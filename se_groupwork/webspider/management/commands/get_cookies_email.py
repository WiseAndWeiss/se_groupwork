from django.core.management.base import BaseCommand
from webspider.webspider.wxmp_launcher_email import WxmpLauncherEmail

class Command(BaseCommand):
    help = '使用邮件发送二维码的方式登录微信公众平台并获取 cookies'

    def add_arguments(self, parser):
        parser.add_argument('--email', dest='email', help='接收二维码的邮箱地址（可选，默认使用 WXMP_NOTIFY_EMAIL 环境变量）')

    def handle(self, *args, **options):
        email = options.get('email')
        launcher = WxmpLauncherEmail(notify_email=email) if email else WxmpLauncherEmail()
        try:
            success = launcher.login()
            if success:
                self.stdout.write(self.style.SUCCESS(f"登录成功，token={launcher.token}"))
            else:
                self.stdout.write(self.style.ERROR("登录失败，请检查日志"))
        finally:
            launcher.close()
