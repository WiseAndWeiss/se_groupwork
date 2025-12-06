from django.core.management.base import BaseCommand
from remoteAI.remoteAI.task_manager import TaskManager
from webspider.models import Article
import json

class Command(BaseCommand):
    help = '处理特定公众号的未摘要的文章'

    def add_arguments(self, parser):
        parser.add_argument('account_names', nargs='+', type=str, help='一个或多个公众号名称')
        parser.add_argument(
            '--max_count',
            type=int,
            default=5,
            help='要获取的文章数量最大值（默认：5）'
        )


    def handle(self, *args, **options):
        account_names = options['account_names']
        count = options['max_count']
        #TODO 分别处理各个公众号的未处理文章
        manager = TaskManager(max_workers=50)
        manager.startrun(target_accounts_name=account_names, max_count=count)

