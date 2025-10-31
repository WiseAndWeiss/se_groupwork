import threading
import json
from remoteAI.remoteAI.article_ai_serializer import entry
from webspider.models import Article, PublicAccount

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
                    "account": PublicAccount.objects.get(id=article.account_id).name,
                    "summary": article.summary,
                    "keyinfo": article.key_info,
                    "tags": article.tags
                }
                for article in all_articles
            ]
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)



    def get_all_tasks_id(self) -> bool:
        """获取所有未处理任务的ID"""
        unprocessed_tasks = Article.objects.filter(summary="").values_list('id', flat=True)
        unprocessed_tasks = list(unprocessed_tasks)
        self.task_pool = unprocessed_tasks
        if len(unprocessed_tasks) == 0:
            return False
        else: 
            return True

    def get_msg_by_id(self, task_id):
        """根据任务ID获取任务详情"""
        item = Article.objects.get(id=task_id)
        article_msg = {
            "id": task_id,
            "title": item.title,
            "content": item.content,
            "account": PublicAccount.objects.get(id=item.account_id).name
        }
        return article_msg

    def _worker(self, article_msg) -> None:
        """线程工作函数，用于控制并发和调用处理函数"""
        try:
            # 获得信号量许可（控制并发数）
            self.semaphore.acquire()
            resp = entry(article_msg)
            if resp is None:
                resp = entry(article_msg)
                if resp is None:
                    return
            # 更新数据库
            print(f"开始任务：{article_msg['title']}")
            self.result.append(resp | {"id": article_msg["id"]})
        finally:
            # 释放信号量许可
            self.semaphore.release()

    def startrun(self) -> None:
        """任务管理入口函数"""
        self.print_table_to_json("origin.json")
        if not self.get_all_tasks_id():
            return False

        # 2. 逐个处理任务
        threads = []
        for task_id in self.task_pool:
            # 获取任务详情
            task_msg = self.get_msg_by_id(task_id)
            # 创建并启动线程（异步执行）
            thread = threading.Thread(target=self._worker, args=(task_msg,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        
        # 3. 更新数据库
        for item in self.result:
            Article.objects.filter(id=item["id"]).update(summary=item["summary"], key_info=",".join(item["keyinfo"]), tags=",".join(item["tags"]))
        self.result = []
        self.print_table_to_json("result.json")
        return True


if __name__ == "__main__":
    # 示例用法
    manager = TaskManager()
    manager.startrun()