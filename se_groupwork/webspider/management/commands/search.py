from django.core.management.base import BaseCommand
from webspider.webspider.biz_searcher import BizSearcher


class Command(BaseCommand):
    help = '搜索公众号'

    def add_arguments(self, parser):
        parser.add_argument('account_name', type=str, help='公众号名称')

    def handle(self, *args, **options):
        account_name = options['account_name']

        try:
            biz_searcher = BizSearcher(account_name)
            biz_searcher.biz_search()  
            self.stdout.write(self.style.SUCCESS(f'成功搜索到公众号"{account_name}"有关信息！'))
        except Exception as e:
            self.strdout.write(self.style.ERROR(f'搜索公众号"{account_name}"时出错: {str(e)}'))