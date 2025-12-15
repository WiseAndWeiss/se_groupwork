from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from webspider.models import PublicAccount
from webspider.webspider.article_fetcher import ArticleFetcher


class Command(BaseCommand):
    help = '按最近抓取时间筛选并更新公众号文章'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='要获取的文章数量（默认：5）')
        parser.add_argument('--sleep', type=int, default=None, help='抓取请求间隔秒数，未设置则在15-20秒内随机')
        parser.add_argument('--hours', type=float, default=10.0, help='距上次抓取超过多少小时才更新（默认：10小时）')
        parser.add_argument('--defaults-only', action='store_true', help='仅更新默认公众号')
        parser.add_argument('--nondefaults-only', action='store_true', help='仅更新非默认公众号')
        parser.add_argument('--only-subscribed', action='store_true', help='仅更新已被订阅的非默认公众号（subscription_count>0）')

    def handle(self, *args, **options):
        count = options['count']
        sleep_seconds = options['sleep']
        hours = options['hours']
        defaults_only = options['defaults_only']
        nondefaults_only = options['nondefaults_only']
        only_subscribed = options['only_subscribed']

        # 处理互斥选项
        if defaults_only and nondefaults_only:
            self.stdout.write(self.style.ERROR('不能同时指定 --defaults-only 和 --nondefaults-only'))
            return

        cutoff = timezone.now() - timedelta(hours=hours)

        qs = PublicAccount.objects.all()
        if defaults_only:
            qs = qs.filter(is_default=True)
        elif nondefaults_only:
            qs = qs.filter(is_default=False)

        # 仅限距今超过阈值或从未抓取过的账号
        qs = qs.filter(last_crawl_time__lte=cutoff) | qs.filter(last_crawl_time__isnull=True)

        # 订阅过滤仅作用于非默认
        if only_subscribed:
            qs = qs.filter(is_default=False, subscription_count__gt=0)

        qs = qs.distinct()

        if not qs.exists():
            self.stdout.write('没有符合条件的公众号需要更新')
            return

        for account in qs:
            name = account.name or '(未命名)'
            self.stdout.write(f'正在处理公众号: {name}')

            if not account.fakeid:
                self.stdout.write(self.style.ERROR(f'跳过: 公众号"{name}"的fakeid为空'))
                continue

            try:
                fetcher = ArticleFetcher(account.fakeid, sleep_seconds=sleep_seconds)
                fetcher.fetch_articles(count)
                self.stdout.write(self.style.SUCCESS(f'成功更新公众号"{name}"的文章！'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'处理公众号"{name}"时出错: {exc}'))
