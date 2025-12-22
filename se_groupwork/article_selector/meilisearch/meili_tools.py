from meilisearch import Client
from django.conf import settings
from webspider.models import Article
import json
import time

'''
mysql.webspider_articles -> meilisearch
{
	id -> id
	title -> title
	content -> content
	summary -> summary
	key_info -> key_info
}
'''

class MeilisearchTool:
	_instance = None
	initialized = False

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self, test_mode=False):
		if MeilisearchTool.initialized:
			return
		MeilisearchTool.initialized = True
		self.valid = False
		self.test_mode = test_mode
		print("[Info at meili_tools.py::__init__] MeilisearchTool 初始化", "testmode" if test_mode else "")
		self.client = Client(settings.MEILISEARCH_HOST, settings.MEILISEARCH_API_KEY)
		self.index_name = settings.MEILISEARCH_INDEX_NAME if not test_mode else settings.TMP_MEILISEARCH_INDEX_NAME_FOR_TEST
		self.index = self.check_and_create_index()
		self.valid = self.index is not None
		if test_mode:
			self.clear_index()

	def check_and_create_index(self):
		'''
		检查并创建索引
		'''
		try:
			indexes = self.client.get_indexes()
			uids = [index.uid for index in indexes['results']]
			if self.index_name not in uids:
				self.client.create_index(uid = self.index_name, options={"primaryKey": "id"})
				time.sleep(0.1)
				print("[Info at meili_tools.py::check_and_create_index] 索引创建成功")
			return self.client.get_index(self.index_name)
		except Exception as e:
			print("[Error at meili_tools.py::check_and_create_index] 索引不存在且创建失败", e)
			return None

	def search_articles(self, search_query, max_results=1000):
		'''
		根据搜索查询返回文章id列表
		'''
		if not self.valid:
			print("[Error at meili_tools.py::search_articles] 索引无效")
			return None
		try:
			result = self.index.search(
				search_query,
				{
					"limit": max_results,
					"attributesToRetrieve": ["id"]
				}
			)
			id_list = [hit['id'] for hit in result['hits']]
			return id_list
		except Exception as e:
			print("[Error at meili_tools.py::search_articles] 搜索失败", e)
			return []
		
	def get_article_index_by_id(self, article_id):
		'''
		根据文章id获取文章索引
		'''
		if not self.valid:
			print("[Error at meili_tools.py::get_article_index_by_id] 索引无效")
			return None
		try:
			return self.index.get_document(article_id)
		except Exception as e:
			print("[Error at meili_tools.py::get_article_index_by_id] 获取文章索引失败", e)
			return None
		
	def get_article_index_count(self):
		'''
		获取文章索引数量
		'''
		if not self.valid:
			print("[Error at meili_tools.py::get_article_index_count] 索引无效")
			return None
		try:
			return self.index.get_stats().number_of_documents
		except Exception as e:
			print("[Error at meili_tools.py::get_article_index_count] 获取文章索引数量失败", e)
			return None
		
	def get_all_articles_index(self):
		'''
		获取所有文章索引
		'''
		if not self.valid:
			print("[Error at meili_tools.py::get_all_articles_index] 索引无效")
			return None
		try:
			documents = self.index.get_documents(
				parameters={
					"limit": 100,
					"offset": 0,
					"fields": ["id", "title"]
				}
			).results
			return {doc.id : doc.title for doc in documents}
		except Exception as e:
			print("[Error at meili_tools.py::get_all_articles_index] 获取文章索引失败", e)
			return None
		
	def update_article(self, article_id):
		'''
		根据文章id更新文章
		'''
		if not self.valid:
			print("[Error at meili_tools.py::update_article] 索引无效")
			return None
		try:
			article = Article.objects.get(id=article_id)
			article_index_info = {
				"id": article_id,
				"title": article.title,
				"content": article.content,
				"summary": article.summary,
				"key_info": article.key_info
			}
			task = self.index.add_documents([article_index_info])
		except Article.DoesNotExist:
			print("[Error at meili_tools.py::update_article] 数据库中不存在该文章")
		except Exception as e:
			print("[Error at meili_tools.py::update_article] 文章更新失败", e)
			return None
		
	def update_batch_articles(self, articles_id):
		'''
		根据文章id列表批量更新文章
		'''
		if not self.valid:
			print("[Error at meili_tools.py::update_batch_articles] 索引无效")
			return None
		try:
			articles_info = []
			queryset = Article.objects.filter(id__in=articles_id).order_by('-id')
			for article in queryset:
				article_info = {
					"id": article.id,
					"title": article.title,
					"content": article.content,
					"summary": article.summary,
					"key_info": article.key_info
				}
				articles_info.append(article_info)
			batch_size = 500
			for i in range(0, len(articles_info), batch_size):
				batch = articles_info[i:i+batch_size]
				task = self.index.add_documents(batch)
			return True
		except Article.DoesNotExist:
			print("[Error at meili_tools.py::update_batch_articles] 数据库中不存在该文章")
		except Exception as e:
			print("[Error at meili_tools.py::update_batch_articles] 文章更新失败", e)
			return None
		
	def delete_article(self, article_id):
		'''
		根据文章id删除文章
		'''
		if not self.valid:
			print("[Error at meili_tools.py::delete_article] 索引无效")
			return None
		try:
			task = self.index.delete_documents([article_id])
			return True
		except Exception as e:
			print("[Error at meili_tools.py::delete_article] 文章删除失败", e)
			return None
	
	def sync_articles_index_with_mysql(self):
		'''
		将mysql中的新增文章同步到meilisearch
		'''
		if not self.valid:
			print("[Error at meili_tools.py::sync_articles_index_with_mysql] 索引无效")
			return None
		try:
			# 获取mysql中的id列表
			queryset = Article.objects.exclude(summary="").order_by('-id')
			mysql_ids = set(queryset.values_list('id', flat=True))
			# 去除meilisearch中已有的id
			offset = 0
			batch_size = 1000
			while True:
				resp = self.index.get_documents(
					parameters={
						"offset": offset,
						"limit": batch_size,
						"fields": ["id"],
					}
				)
				for hit in resp.results:
					id = hit.id
					mysql_ids.discard(id)
				if len(resp.results) < batch_size:
					break
				offset += batch_size
			if not mysql_ids:
				print("暂无需要同步到索引的文章")
				return True
			# 分批同步
			articles_info = []
			queryset = queryset.filter(id__in=mysql_ids)
			for article in queryset:
				article_info = {
					"id": article.id,
					"title": article.title,
					"content": article.content,
					"summary": article.summary,
					"key_info": article.key_info
				}
				articles_info.append(article_info)
			batch_size = 500
			for i in range(0, len(articles_info), batch_size):
				batch = articles_info[i:i+batch_size]
				task = self.index.add_documents(batch)
			print(f"成功同步{len(mysql_ids)}篇文章到索引")
			return True
		except Exception as e:
			print("[Error at meili_tools.py::sync_articles_index_with_mysql] 索引同步失败", e)
			return None
		
	def clear_index(self):
		'''
		清空索引
		'''
		if not self.valid:
			print("[Error at meili_tools.py::clear_index] 索引无效")
			return None
		try:
			task = self.index.delete_all_documents()
			return True
		except Exception as e:
			print("[Error at meili_tools.py::clear_index] 索引清空失败", e)
			return None
		
	def rebuild_index(self):
		'''
		重建索引
		'''
		if not self.valid:
			print("[Error at meili_tools.py::rebuild_index] 索引无效")
			return None
		try:
			delete_task = self.index.delete_all_documents()
			print("[Info at meili_tools.py::rebuild_index] 索引删除成功")
			time.sleep(1)
			queryset = Article.objects.exclude(summary="").order_by('-id')
			articles_info = []
			for article in queryset:
				article_info = {
					"id": article.id,
					"title": article.title,
					"content": article.content,
					"summary": article.summary,
					"key_info": article.key_info
				}
				articles_info.append(article_info)
			batch_size = 500
			for i in range(0, len(articles_info), batch_size):
				batch = articles_info[i:i+batch_size]
				task = self.index.add_documents(batch)
			print(f"成功重建{len(queryset)}篇文章到索引")
			return True
		except Exception as e:
			print("[Error at meili_tools.py::rebuild_index] 索引重建失败", e)
			return None