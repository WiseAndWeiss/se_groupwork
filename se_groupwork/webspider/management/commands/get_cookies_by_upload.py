# webspider/management/commands/get_cookies_by_upload.py

from django.core.management.base import BaseCommand, CommandError
from webspider.models import Cookies
import json
import ast

class Command(BaseCommand):
    help = '手动上传cookies和token到数据库'
    
    def add_arguments(self, parser):
        # 改为可选参数
        parser.add_argument(
            '--cookies', 
            type=str,
            nargs='?',
            help='cookies JSON字符串'
        )
        parser.add_argument(
            '--token', 
            type=str,
            nargs='?',
            help='token字符串'
        )

    def handle(self, *args, **options):
        cookies_str = options.get('cookies')
        token = options.get('token')
        
        # 交互式输入
        if not cookies_str:
            self.stdout.write('请粘贴cookies JSON字符串（输入完后按回车键）：')
            cookies_str = input()
        
        if not token:
            self.stdout.write('请输入token：')
            token = input()

        self.stdout.write('开始处理cookies和token上传...')

        try:
            # 尝试解析cookies字符串
            try:
                cookies_dict = json.loads(cookies_str)
            except json.JSONDecodeError:
                try:
                    cookies_dict = ast.literal_eval(cookies_str)
                except (ValueError, SyntaxError) as e:
                    raise CommandError(f'cookies格式解析失败: {e}')

            if not isinstance(cookies_dict, dict):
                raise CommandError('cookies必须是字典格式')

            if not token or not token.strip():
                raise CommandError('token不能为空')

            # 保存到数据库
            cookies_obj = Cookies.objects.create(
                cookies=json.dumps(cookies_dict, ensure_ascii=False),
                token=token.strip()
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'成功保存Cookie到数据库！ID: {cookies_obj.id}'
                )
            )

        except Exception as e:
            raise CommandError(f'保存到数据库时发生错误: {e}')