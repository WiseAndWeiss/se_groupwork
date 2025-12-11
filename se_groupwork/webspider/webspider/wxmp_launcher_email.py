#!/usr/bin/env python3
"""
改进版的微信公众号登录器：支持邮件发送二维码

此版本用于 Docker 容器环境，将二维码发送到指定邮箱，
用户可以在邮件中扫码登录，登录成功后 cookies/token 自动保存到数据库。

使用方式：
  python webspider/webspider/wxmp_launcher_email.py
  
或在 Django shell 中：
  from webspider.webspider.wxmp_launcher_email import WxmpLauncherEmail
  launcher = WxmpLauncherEmail()
  launcher.login()
"""

import os
import sys
import json
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'se_groupwork.settings')
django.setup()

from django.core.mail import EmailMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs
from webspider.webspider.config import PATH_QRCODE, PATH_ERROR_SCREENSHOT
from webspider.models import Cookies


class WxmpLauncherEmail:
    """支持邮件通知的微信公众号登录器"""

    def __init__(self, qrcode_path=PATH_QRCODE, notify_email=None):
        """
        初始化登录器

        :param qrcode_path: 二维码保存路径
        :param notify_email: 接收二维码的邮箱地址（默认从环境变量读取）
        """
        self.qrcode_path = qrcode_path
        self.notify_email = notify_email or os.getenv('WXMP_NOTIFY_EMAIL', 'lu-yt23@mails.tsinghua.edu.cn')
        self.driver = None
        self.token = None
        self.cookies = None

    def send_qrcode_email(self):
        """
        发送二维码图像到邮箱

        :return: 是否发送成功
        """
        try:
            email = EmailMessage(
                subject='[微信公众号登录] 二维码已生成',
                body='您好，\n\n请在60秒内使用微信扫描下方二维码进行登录。\n\n如果无法在邮件中查看，请保存二维码文件后用微信扫码。',
                from_email=os.getenv('DEFAULT_FROM_EMAIL', os.getenv('EMAIL_HOST_USER', 'noreply@example.com')),
                to=[self.notify_email],
            )

            # 附加二维码图像
            if os.path.isfile(self.qrcode_path):
                with open(self.qrcode_path, 'rb') as attachment:
                    email.attach(
                        'qrcode.png',
                        attachment.read(),
                        mimetype='image/png'
                    )
                print(f"[✓] 二维码已附加到邮件")
            else:
                print(f"[⚠] 二维码文件不存在: {self.qrcode_path}")

            email.send()
            print(f"[✓] 二维码已发送到 {self.notify_email}")
            return True

        except Exception as e:
            print(f"[✗] 邮件发送失败: {e}")
            print(f"[!] 请检查邮件配置（EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD）")
            return False

    def login(self):
        """
        执行登录流程：获取二维码 -> 发送邮件 -> 等待用户扫码 -> 保存 cookies
        """
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=600,600")
        options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=options)

        try:
            print("[*] 正在打开微信公众平台页面...")
            self.driver.get("https://mp.weixin.qq.com/")

            print("[*] 等待二维码加载...")
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "login__type__container__scan__qrcode"))
            )

            # 获取并保存二维码
            qr_element = self.driver.find_element(By.CLASS_NAME, "login__type__container__scan__qrcode")
            qr_element.screenshot(self.qrcode_path)
            print(f"[✓] 二维码已保存到 {self.qrcode_path}")

            # 发送邮件通知
            if not self.send_qrcode_email():
                print("[!] 警告：邮件发送失败，但将继续等待扫码...")

            # 等待用户扫码登录（180秒超时）
            print("[*] 等待用户扫码登录（最多180秒）...")
            WebDriverWait(self.driver, 180).until(
                lambda d: "token=" in d.current_url
            )

            # 提取 token 和 cookies
            self.token = self.get_token()
            self.cookies = self.get_all_cookies()

            if self.token and self.cookies:
                self.save_to_database()
                print("[✓] 登录流程完成")
                return True
            else:
                print("[✗] 无法提取 token 或 cookies")
                return False

        except Exception as e:
            print(f"[✗] 登录失败: {e}")
            # 保存错误截图便于调试
            try:
                self.driver.save_screenshot(PATH_ERROR_SCREENSHOT)
                print(f"[i] 错误截图已保存到 {PATH_ERROR_SCREENSHOT}")
            except Exception as screenshot_e:
                print(f"[⚠] 无法保存错误截图: {screenshot_e}")
            return False

        finally:
            self.close()

    def get_token(self):
        """
        从登录后的 URL 中提取 token

        :return: token 字符串或 None
        """
        try:
            current_url = self.driver.current_url
            print(f"[i] 登录后 URL: {current_url}")
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]
            if token:
                print(f"[✓] 成功提取 token: {token[:20]}...")
            return token
        except Exception as e:
            print(f"[✗] 提取 token 失败: {e}")
            return None

    def get_all_cookies(self):
        """
        获取并解析所有浏览器 cookies

        :return: cookies 字典或 None
        """
        try:
            cookies = self.driver.get_cookies()
            print(f"[✓] 获取到 {len(cookies)} 个 Cookie")

            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            return cookies_dict

        except Exception as e:
            print(f"[✗] 获取 Cookie 失败: {e}")
            return None

    def save_to_database(self):
        """
        将 cookies 和 token 保存到数据库
        """
        try:
            cookies_obj = Cookies.objects.create(
                cookies=json.dumps(self.cookies),
                token=self.token
            )
            print(f"[✓] 成功保存 Cookie 到数据库（ID: {cookies_obj.id}）")
            return True

        except Exception as e:
            print(f"[✗] 数据库保存失败: {e}")
            return False

    def close(self):
        """
        关闭浏览器驱动并清理临时文件
        """
        if self.driver:
            try:
                self.driver.quit()
                print("[✓] 浏览器已关闭")
            except Exception as e:
                print(f"[⚠] 关闭浏览器时出错: {e}")

        # 清理二维码和错误截图
        for file_path in [self.qrcode_path, PATH_ERROR_SCREENSHOT]:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"[✓] 临时文件已清理: {file_path}")
                except Exception as e:
                    print(f"[⚠] 无法删除 {file_path}: {e}")


def main():
    """主函数：可从命令行直接调用"""
    print("=" * 60)
    print("微信公众号登录器（邮件通知版）")
    print("=" * 60)

    launcher = WxmpLauncherEmail()
    success = launcher.login()

    if success:
        print("\n[✓] 登录成功！")
        print(f"[i] Token: {launcher.token}")
        print(f"[i] Cookies 数量: {len(launcher.cookies) if launcher.cookies else 0}")
    else:
        print("\n[✗] 登录失败，请检查上述错误信息")

    print("=" * 60)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
