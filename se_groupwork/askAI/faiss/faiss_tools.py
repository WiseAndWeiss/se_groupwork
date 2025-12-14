from webspider.models import Article
from django.conf import settings
from se_groupwork.global_tools import global_embedding_load

import os
import json
import faiss
import numpy as np
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

text_splitter = RecursiveCharacterTextSplitter(
	chunk_size=CHUNK_SIZE, 
	chunk_overlap=CHUNK_OVERLAP,
	separators = ["\n\n", "\n", "。", "！", "？", "，", "、", ""]
)

class FaissTool:
	_instance = None
	initialized = False

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self, test_mode=False):
		if FaissTool.initialized:
			return
		FaissTool.initialized = True
		self.test_mode = test_mode
		self.embedding = global_embedding_load()
		if not self.test_mode:
			self.faiss_index_path = settings.FAISS_INDEX_PATH
			self.chunk_to_article_id_json_path = settings.CHUNK_TO_ARTICLE_ID_JSON_PATH
			self.index = self._load_index()
			self.chunk_article_map = self._load_chunk_article_map()
		else:
			self.faiss_index_path = settings.TMP_FAISS_INDEX_PATH_FOR_TEST
			self.chunk_to_article_id_json_path = settings.TMP_CHUNK_TO_ARTICLE_ID_JSON_PATH_FOR_TEST
			self.index = faiss.IndexFlatL2(settings.EMBEDDING_DIM)
			self.chunk_article_map = {}
			faiss.write_index(self.index, self.faiss_index_path)
			f = open(self.chunk_to_article_id_json_path, "w", encoding="utf-8")
			f.write("{}")
			f.close()


	def _load_index(self) -> faiss.Index:
		if os.path.exists(self.faiss_index_path):
			index = faiss.read_index(self.faiss_index_path)
		else:
			index = faiss.IndexFlatL2(settings.EMBEDDING_DIM)
			faiss.write_index(index, self.faiss_index_path)
			f = open(self.chunk_to_article_id_json_path, "w")
			f.write("{}")
			f.close()
		return index

	def _save_index(self):
		faiss.write_index(self.index, self.faiss_index_path)

	def _load_chunk_article_map(self) -> Dict[int, int]:
		if os.path.exists(self.chunk_to_article_id_json_path):
			with open(self.chunk_to_article_id_json_path, "r") as f:
				jsondata = json.load(f)
				return {int(k): int(v) for k, v in jsondata.items()}
		f = open(self.chunk_to_article_id_json_path, "w", encoding="utf-8")
		f.write("{}")
		f.close()
		return {}
	
	def _save_chunk_article_map(self):
		jsondata = {str(k): str(v) for k, v in self.chunk_article_map.items()}
		with open(self.chunk_to_article_id_json_path, "w", encoding="utf-8") as f:
			json.dump(jsondata, f, ensure_ascii=False, indent=4)
	
	def _embed_texts(self, texts: List[str]) -> np.ndarray:
		
		return np.array(self.embedding.embed_documents(texts)).astype(np.float32)
	
	def _add_content_to_index(self, content: str, id: int):
		if not content:
			return np.array([])
		chunks = text_splitter.split_text(content)
		chunks = [chunk for chunk in chunks if chunk.strip()]
		if not chunks:
			return np.array([])
		chunk_embeddings = self._embed_texts(chunks)
		start_idx = self.index.ntotal
		delta_chunk_map = {start_idx + i: id for i in range(len(chunks))}
		self.index.add(chunk_embeddings)
		self.chunk_article_map.update(delta_chunk_map)

	def update_article(self, article_id: int):
		try:
			article = Article.objects.get(id=article_id)
			self._add_content_to_index(article.content, article_id)
			self._save_index()
			self._save_chunk_article_map()
		except Article.DoesNotExist:
			print(f"[Error at faiss_tools.py::update_article] article_id {article_id} does not exist")
		except Exception as e:
			print(f"[Error at faiss_tools.py::update_article] {e}")

	def update_articles(self, article_ids: List[int]):
		try:
			queryset = Article.objects.filter(id__in=article_ids)
			for article in queryset:
				self._add_content_to_index(article.content, article.id)
			self._save_index()
			self._save_chunk_article_map()
		except Exception as e:
			print(f"[Error at faiss_tools.py::update_articles] {e}")

	def update_all_articles(self, batch_size: int = 100):
		try:
			total = Article.objects.count()
			for offset in range(0, total, batch_size):
				queryset = Article.objects.all()[offset:offset+batch_size]
				for article in queryset:
					self._add_content_to_index(article.content, article.id)
				self._save_index()
				self._save_chunk_article_map()
		except Exception as e:
			print(f"[Error at faiss_tools.py::update_all_articles] {e}")


	def clear_index(self):
		try:
			self.index = faiss.IndexFlatL2(settings.EMBEDDING_DIM)
			self.chunk_article_map = {}
			self._save_index()
			self._save_chunk_article_map()
		except Exception as e:
			print(f"[Error at faiss_tools.py::clear_index] {e}")

	def rebuild_index(self):
		self.clear_index()
		self.update_all_articles()

	def search(self, query, top_k: int = 8):
		if not query.strip():
			print("[Error at faiss_tools.py::search] query is empty")
			return []
		try:
			query_embedding = self._embed_texts([query])
			DIST, IDX = self.index.search(query_embedding, top_k*2)
			article_results = {}
			for dist, idx in zip(DIST[0], IDX[0]):
				article_id = self.chunk_article_map[idx]
				if article_id not in article_results or dist < article_results[article_id]:
					article_results[article_id] = dist
			result_list = [(article_id, dist) for article_id, dist in article_results.items()]
			result_list.sort(key=lambda x: x[1])
			result_list = result_list[:top_k]
			return result_list
		except Exception as e:
			print(f"[Error at faiss_tools.py::search] {e}")
			return []
		
	def get_all_articles_ids_in_index(self):
		ids = list(self.chunk_article_map.values())
		ids = list(set(ids))
		ids.sort()
		return ids