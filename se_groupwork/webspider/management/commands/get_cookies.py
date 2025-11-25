from django.core.management.base import BaseCommand
from webspider.webspider.wxmp_launcher import WxmpLauncher

class Command(BaseCommand):
    help = '登录微信公众平台获取cookies，用于爬虫'

    def handle(self, *args, **options):
        launcher = WxmpLauncher()
        try:
            launcher.login()
            print(launcher.token)
            print(launcher.cookies)
        finally:
            launcher.close()