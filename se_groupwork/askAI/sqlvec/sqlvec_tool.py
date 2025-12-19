from webspider.models import Article
from django.conf import settings
from se_groupwork.global_tools import global_embedding_load
import sqlite3
import sqlite_vec
import numpy as np
import struct
import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, 
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", "。", "！", "？", "，", "、", ""]
)

# 适配示例的向量序列化函数
def serialize_f32(vector: List[float]) -> bytes:
    """将浮点向量序列化为bytes（sqlite-vec原生要求）"""
    return struct.pack("%sf" % len(vector), *vector)

def deserialize_f32(data: bytes) -> List[float]:
    """将bytes反序列化为浮点向量（可选，搜索时无需）"""
    return list(struct.unpack("%sf" % (len(data) // 4), data))

class SqliteVectorTool:
    _instance = None
    initialized = False
    _conn = None  # 进程内单例连接

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, test_mode=False):
        if SqliteVectorTool.initialized:
            return
        SqliteVectorTool.initialized = True
        self.test_mode = test_mode
        self.embedding = global_embedding_load()
        self.embedding_dim = settings.EMBEDDING_DIM  # 比如768
        
        # 数据库路径设置
        if not self.test_mode:
            self.db_path = settings.SQLITEVECTOR_DB_PATH
        else:
            self.db_path = settings.TMP_SQLITEVECTOR_DB_PATH_FOR_TEST
        
        self._init_db()
        if self.test_mode:
            self._clear_index()

    def _check_connection(self, conn):
        """检查连接是否健康"""
        if conn is None:
            return False
        try:
            conn.execute("SELECT 1")
            return True
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            return False

    def _update_connection(self):
        """原生sqlite3连接 + 手动加载扩展（适配示例代码）"""
        # 复用健康连接
        if self._check_connection(self._conn):
            return self._conn
        
        # 原生sqlite3连接（核心修改）
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=10 
        )
        self._conn.enable_load_extension(True)
        sqlite_vec.load(self._conn)
        self._conn.enable_load_extension(False)
        
        return self._conn

    def _init_db(self):
        """初始化vec0虚拟表"""
        conn = self._update_connection()
        try:
            # 创建vec0虚拟表
            conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings 
                USING vec0(embedding float[{self.embedding_dim}])
            """)
            # 创建普通表存储article_id映射
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_article_mapping (
                    chunk_rowid INTEGER PRIMARY KEY,
                    article_id INTEGER NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """生成文本嵌入"""
        return np.array(self.embedding.embed_documents(texts), dtype=np.float32)

    def _add_content_to_index(self, content: str, article_id: int):
        """添加文章chunk到向量库（适配序列化）"""
        if not content:
            return
        chunks = text_splitter.split_text(content)
        chunks = [c.strip() for c in chunks if c.strip()]
        if not chunks:
            return
        embeddings = self._embed_texts(chunks)
        conn = self._update_connection()
        try:
            # 批量插入（先插vec0表，再插映射表）
            for emb in embeddings:
                emb_bytes = serialize_f32(emb.tolist())
                cursor = conn.execute(
                    "INSERT INTO chunk_embeddings(embedding) VALUES (?)",
                    [emb_bytes]
                )
                chunk_rowid = cursor.lastrowid
                conn.execute(
                    "INSERT INTO chunk_article_mapping(chunk_rowid, article_id) VALUES (?, ?)",
                    [chunk_rowid, article_id]
                )
            conn.commit()
            print(f"[Success] 文章{article_id}添加到向量库")
        except Exception as e:
            conn.rollback()
            print(f"[Error in _add_content_to_index] {e}")
            raise e
        finally:
            pass

    def _delete_article_chunks(self, article_id: int):
        """删除文章对应的所有chunk向量"""
        conn = self._update_connection()
        try:
            # 先查该文章的所有chunk_rowid
            cursor = conn.execute(
                "SELECT chunk_rowid FROM chunk_article_mapping WHERE article_id = ?",
                [article_id]
            )
            chunk_rowids = [row[0] for row in cursor.fetchall()]
            if not chunk_rowids:
                return
            conn.execute(
                f"DELETE FROM chunk_embeddings WHERE rowid IN ({','.join(['?']*len(chunk_rowids))})",
                chunk_rowids
            )
            conn.execute(
                "DELETE FROM chunk_article_mapping WHERE article_id = ?",
                [article_id]
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[Error in _delete_article_chunks] {e}")
        finally:
            pass

    def update_article(self, article_id: int):
        """更新单篇文章的向量"""
        try:
            article = Article.objects.get(id=article_id)
            self._add_content_to_index(article.content, article_id)
        except Article.DoesNotExist:
            print(f"[Error] 文章{article_id}不存在")
        except Exception as e:
            print(f"[Error in update_article] {e}")

    def search(self, query, top_k: int = 8):
        """相似搜索（完全适配示例代码的语法）"""
        if not query.strip():
            print("[Error] 查询为空")
            return []
        
        try:
            # 生成查询向量并序列化
            query_emb = self._embed_texts([query])[0]
            query_emb_bytes = serialize_f32(query_emb.tolist())
            
            conn = self._update_connection()
            cursor = conn.cursor()

            # 核心搜索SQL（适配示例的MATCH语法）
            cursor.execute("""
                SELECT 
                    cam.article_id,
                    cev.distance
                FROM (
                    SELECT 
                        rowid,
                        distance
                    FROM chunk_embeddings
                    WHERE embedding MATCH ?
                    ORDER BY distance
                    LIMIT ?
                ) AS cev
                LEFT JOIN chunk_article_mapping AS cam ON cev.rowid = cam.chunk_rowid
                WHERE cam.article_id IS NOT NULL 
                GROUP BY cam.article_id
                ORDER BY MIN(cev.distance)
                LIMIT ?
            """, (query_emb_bytes, top_k * 2, top_k))
            
            results = cursor.fetchall()
            return [(row[0], row[1]) for row in results]
        except Exception as e:
            print(f"[Error in search] {e}")
            return []

    def update_articles(self, article_ids: List[int]):
        try:
            queryset = Article.objects.filter(id__in=article_ids)
            for article in queryset:
                self._add_content_to_index(article.content, article.id)
        except Exception as e:
            print(f"[Error in update_articles] {e}")

    def update_all_articles(self, batch_size: int = 100):
        try:
            total = Article.objects.count()
            for offset in range(0, total, batch_size):
                queryset = Article.objects.all()[offset:offset+batch_size]
                for article in queryset:
                    self._add_content_to_index(article.content, article.id)
        except Exception as e:
            print(f"[Error in update_all_articles] {e}")

    def clear_index(self):
        """清空向量库"""
        conn = self._update_connection()
        try:
            conn.execute("DELETE FROM chunk_embeddings")
            conn.execute("DELETE FROM chunk_article_mapping")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[Error in clear_index] {e}")

    def rebuild_index(self):
        """重建向量库"""
        self.clear_index()
        self.update_all_articles()

    def get_all_articles_ids(self):
        conn = self._update_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT article_id FROM chunk_article_mapping ORDER BY article_id")
        return [row[0] for row in cursor.fetchall()]

    def get_all_articles_ids_in_index(self):
        """Compatibility wrapper kept for older FAISS-style callers."""
        return self.get_all_articles_ids()