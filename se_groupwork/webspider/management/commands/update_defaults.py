from django.core.management.base import BaseCommand
from webspider.models import PublicAccount
from webspider.webspider.article_fetcher import ArticleFetcher


class Command(BaseCommand):
    help = '更新所有默认公众号的文章列表'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='要获取的文章数量（默认：5）'
        )
        parser.add_argument(
            '--sleep',
            type=int,
            default=None,
            help='抓取请求间隔秒数，未设置则在15-20秒内随机'
        )

    def handle(self, *args, **options):
        count = options['count']
        sleep_seconds = options['sleep']

        accounts = PublicAccount.objects.filter(is_default=True)
        if not accounts.exists():
            self.stdout.write('没有默认公众号需要更新')
            return

        for account in accounts:
            name = account.name or '(未命名)'
            self.stdout.write(f'正在处理默认公众号: {name}')

            if not account.fakeid:
                self.stdout.write(self.style.ERROR(f'跳过: 公众号"{name}"的fakeid为空'))
                continue

            try:
                fetcher = ArticleFetcher(account.fakeid, sleep_seconds=sleep_seconds)
                fetcher.fetch_articles(count)
                self.stdout.write(self.style.SUCCESS(f'成功更新默认公众号"{name}"的文章！'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'处理默认公众号"{name}"时出错: {exc}'))
