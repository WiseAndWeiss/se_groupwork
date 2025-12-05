from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction

from remoteAI.remoteAI.article_ai_serializer import entry
from webspider.models import Article

class ArticleDAO:
    @staticmethod
    def get_pending_article_ids(target_accounts_name = None, max_article_num = None):
        '''获取待处理的文章'''
        queryset = Article.objects.filter(summary="").order_by('-publish_time')
        if target_accounts_name:
            queryset = queryset.filter(public_account__name__in=target_accounts_name)
        if max_article_num:
            queryset = queryset[:max_article_num]
        print(f"计划处理文章{len(queryset)}篇:")
        for article in queryset:
            print(f"  - {article.id} | {article.title}")
        return list(queryset.values_list('id', flat=True))

    @staticmethod
    def get_article_info(article_id):
        '''获取文章信息'''
        try:
            article = Article.objects.get(id=article_id)
            return {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "account": article.public_account.name
            }
        except Article.DoesNotExist:
            # TODO: 日志
            print(f"文章{article_id}不存在")
            return None

    
    @staticmethod
    def batch_update_articles_info(articles_info, batch_size = 10):
        '''批量更新文章信息'''
        if len(articles_info) == 0:
            return
        for i in range(0, len(articles_info), batch_size):
            batch = articles_info[i:i+batch_size]
            update_cases = {}
            for article_info in batch:
                update_cases[article_info["id"]] = {
                    "summary": article_info["summary"],
                    "tags": article_info["tags"],
                    "key_info": article_info["key_info"],
                    "tags_vector": article_info["tags_vector"],
                    "semantic_vector": article_info["semantic_vector"]
                }
            with transaction.atomic():
                for article_id, update_case in update_cases.items():
                    Article.objects.filter(id=article_id).update(**update_case)


class TaskManager:
    def __init__(self, max_workers = 5):
        self.max_workers = max_workers
        self.target_accounts_name = None
        self.max_article_num = None
        self.task_pool = []
        self.result = []

    def update_task_pool(self):
        self.task_pool = ArticleDAO.get_pending_article_ids(
            self.target_accounts_name, 
            self.max_article_num
        )
        return len(self.task_pool) > 0
    
    def set_task_pool(self, task_pool):
        self.task_pool = task_pool

    def _process_article(self, article_info):
        '''线程函数，处理单任务'''
        if not article_info:
            return None
        article_id = article_info["id"]
        print(f"线程开始：{article_info['title']}")
        try:
            resp = entry(article_info)
            if resp is None:
                return {"id": article_id, "summary": "", "keyinfo": [], "tags": [], "semantic_vector": [], "tags_vector": []}
            else:
                return resp | {"id": article_id}
        except Exception as e:
            # TODO: 日志
            print(f"线程出错：{article_info['title']}")
            print(e)
            return None

    def startrun(self, target_accounts_name = None, max_article_num = None):
        self.target_accounts_name = target_accounts_name
        self.max_article_num = max_article_num
        if len(self.task_pool) == 0:
            self.update_task_pool()
        if len(self.task_pool) == 0:
            return False
        self.result = []
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="remoteAIWorker") as executor:
            future_to_article = {
                executor.submit(self._process_article, ArticleDAO.get_article_info(article_id)): article_id
                for article_id in self.task_pool
            }
            for future in as_completed(future_to_article):
                article_id = future_to_article[future]
                try:
                    article_info = future.result()
                    if article_info:
                        self.result.append(article_info)
                except Exception:
                    # TODO: 日志
                    print(f"线程出错：{article_id}")
        if self.result:
            ArticleDAO.batch_update_articles_info(self.result)
        self.result.clear()
        self.task_pool.clear()
        return True
        
if __name__ == "__main__":
    # 实例用法
    task_manager = TaskManager()
    task_manager.startrun()