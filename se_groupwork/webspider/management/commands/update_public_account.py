from django.core.management.base import BaseCommand
from webspider.webspider.task_manager import TaskManager

class Command(BaseCommand):
    help = '更新所有公众号的文章列表'

    def handle(self, *args, **options):
        manager = TaskManager()
        result = manager.startrun()
        if result:
            self.stdout.write(self.style.SUCCESS('任务执行成功！'))
        else:
            self.stdout.write('没有需要处理的任务')