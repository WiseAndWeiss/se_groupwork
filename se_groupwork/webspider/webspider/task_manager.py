import json
from remoteAI.remoteAI.article_ai_serializer import entry
from webspider.webspider.article_fetcher import ArticleFetcher
from webspider.models import Article, PublicAccount
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

class TaskManager:
    def __init__(self):
        self.task_pool = []
        self.task_data = [] 
        self.result = []
        self.names = [] 

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

        # 先获取默认公众号
        default_tasks = PublicAccount.objects.filter(
            Q(last_crawl_time__lte=ten_hours_ago) | Q(last_crawl_time__isnull=True),
            is_default=True
        )
        
        # 再获取非默认但有订阅的公众号
        non_default_tasks = PublicAccount.objects.filter(
            Q(last_crawl_time__lte=ten_hours_ago) | Q(last_crawl_time__isnull=True),
            is_default=False,
            subscription_count__gt=0
        )
        
        # 合并：默认公众号在前
        all_tasks = list(default_tasks.values_list('fakeid', 'name')) + \
                    list(non_default_tasks.values_list('fakeid', 'name'))

        self.task_data = all_tasks

        fakeids = [task[0] for task in self.task_data]
        self.names = [task[1] for task in self.task_data]
        print(f"待处理的公众号：{self.names}")

        self.task_pool = fakeids
        if len(fakeids) == 0:
            return False
        else: 
            return True

    def _process_task(self, fakeid) -> None:
        """单线程处理"""
        try:
            article_fetcher = ArticleFetcher(fakeid)
            article_fetcher.fetch_articles(5)
        except Exception as e:
            print(f"处理公众号 {fakeid} 时出错: {e}")
        finally:
            # 获取公众号名称并打印
            account = PublicAccount.objects.filter(fakeid=fakeid).first()
            if account:
                print(f"已完成处理公众号: {account.name}")
            else:
                print(f"找不到fakeid为 {fakeid} 的公众号")

    def startrun(self) -> None:
        """任务管理入口函数"""
        # 1. 获取各个公众号的fakeid
        if not self.get_all_tasks_fakeid():
            return False

        # 2. 顺序处理任务
        for fakeid, name in self.task_data:
            print(f"正在处理公众号: {name}")
            self._process_task(fakeid)
        
        return True

if __name__ == "__main__":
    # 示例用法
    manager = TaskManager()
    manager.startrun()