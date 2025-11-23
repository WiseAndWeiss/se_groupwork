from django.core.management.base import BaseCommand
from webspider.webspider.article_fetcher import ArticleFetcher
from webspider.models import PublicAccount

class Command(BaseCommand):
    help = '更新特定公众号的文章列表'
    
    def add_arguments(self, parser):
        parser.add_argument('account_names', nargs='+', type=str, help='一个或多个公众号名称')
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='要获取的文章数量（默认：5）'
        )

    def handle(self, *args, **options):
        account_names = options['account_names']
        count = options['count']

        # 批量获取所有指定公众号的fakeid
        accounts_info = PublicAccount.objects.filter(
            name__in=account_names
        ).values_list('name', 'fakeid')

        # 转换为字典方便查找 {name: fakeid}
        fakeid_map = {name: fakeid for name, fakeid in accounts_info}
        
        for account_name in account_names:
            self.stdout.write(f'正在处理公众号: {account_name}')

            # 检查公众号是否存在
            if account_name not in fakeid_map:
                self.stdout.write(self.style.ERROR(f'错误: 公众号"{account_name}"不存在于数据库中'))
                continue

            fakeid = fakeid_map[account_name]
            if not fakeid:
                self.stdout.write(self.style.ERROR(f'错误: 公众号"{account_name}"的fakeid为空'))
                continue

            try:
                article_fetcher = ArticleFetcher(fakeid)
                article_fetcher.fetch_articles(count)
                
                self.stdout.write(self.style.SUCCESS(f'成功更新公众号"{account_name}"的文章！'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'处理公众号"{account_name}"时出错: {str(e)}'))
