import threading
import json
from remoteAI.remoteAI.article_ai_serializer import entry
from webspider.webspider.article_fetcher import ArticleFetcher
from webspider.models import Article, PublicAccount
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

class TaskManager:
    def __init__(self):
        # 最大并发线程数限制为5
        self.semaphore = threading.Semaphore(5)
        self.task_pool = []
        self.result = []

    def print_table_to_json(self, save_path):
        """打印数据表"""
        all_articles = Article.objects.all()
        json_data = {
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "url": article.article_url,
                    "content": article.content,
                    "account": article.public_account.name,
                }
                for article in all_articles
            ]
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)


    def get_all_tasks_fakeid(self) -> bool:
        """获取所有过长时间未爬虫的公众号fakeid"""
        ten_hours_ago = timezone.now() - timedelta(hours=10)

        unprocessed_tasks = PublicAccount.objects.filter(
            Q(last_crawl_time__lt=ten_hours_ago) | Q(last_crawl_time__isnull=True)
        ).values_list('fakeid', flat=True)

        unprocessed_tasks = list(unprocessed_tasks)
        self.task_pool = unprocessed_tasks
        if len(unprocessed_tasks) == 0:
            return False
        else: 
            return True

    def _worker(self, fakeid) -> None:
        """线程工作函数，用于控制并发和调用处理函数"""
        try:
            # 获得信号量许可（控制并发数）
            self.semaphore.acquire()
            article_fetcher = ArticleFetcher(fakeid)
            article_fetcher.fetch_articles(5)
        finally:
            # 释放信号量许可
            self.semaphore.release()

    def startrun(self) -> None:
        """任务管理入口函数"""
        # 1. 获取各个公众号的fakeid
        if not self.get_all_tasks_fakeid():
            return False

        # 2. 逐个处理任务
        threads = []
        for fakeid in self.task_pool:
            # 创建并启动线程（异步执行）
            thread = threading.Thread(target=self._worker, args=(fakeid,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        
        return True


if __name__ == "__main__":
    # 示例用法
    manager = TaskManager()
    manager.startrun()