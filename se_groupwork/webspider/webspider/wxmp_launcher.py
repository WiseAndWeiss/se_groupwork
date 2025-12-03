from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs
from PIL import Image
from webspider.webspider.config import PATH_QRCODE, PATH_ERROR_SCREENSHOT
import json
import os
from webspider.models import Cookies


class WxmpLauncher:
    def __init__(self, qrcode_path=PATH_QRCODE):
        """
        初始化微信公众平台登录器

        :param qrcode_path: 二维码保存路径
        """
        self.qrcode_path = qrcode_path
        self.driver = None
        self.token = None
        self.cookies = None

    def get_token(self):
        """
        登陆后，页面会跳转，格式如https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=[Token]
        从url中提取Token

        :return: 返回token
        """
        # 获取当前URL
        current_url = self.driver.current_url
        print("登录成功后的URL:", current_url)

        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        token = query_params.get('token', [None])[0]
        return token

    def get_all_cookies(self):
        """
        获取当前页面的所有Cookie

        :return: 返回cookies列表
        """
        try:
            # 获取所有Cookie
            cookies = self.driver.get_cookies()
            print(f"获取到 {len(cookies)} 个Cookie")

            cookies_dict = {}
            for cookie in cookies:
                cookies_dict[cookie['name']] = cookie['value']

            self.cookies = cookies_dict
            return cookies_dict
        except Exception as e:
            print(f"获取Cookie失败: {e}")
            return None

    def show_qrcode_with_pillow(self, file_path=None):
        """
        使用Pillow打开并显示二维码图片

        :param file_path: 二维码图片路径，默认为None使用初始化路径
        """
        if file_path is None:
            file_path = self.qrcode_path
        try:
            img = Image.open(file_path)
            img.show()
            print(f"已使用系统默认图片查看器打开 {file_path}")
        except Exception as e:
            print(f"打开图片失败: {e}")

    def login(self):
        """
        登录函数，让用户登录微信公众平台后，获取登录的cookie和token并保存
        """
        # 设置浏览器选项
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=600,600")
        options.add_experimental_option('detach', True)
        # 无头模式
        options.add_argument("--headless")

        # 初始化浏览器
        self.driver = webdriver.Chrome(options=options)

        try:
            # 打开微信公众平台登录页
            print("正在打开微信公众平台页面...")
            self.driver.get("https://mp.weixin.qq.com/")

            # 等待二维码加载完成
            print("等待二维码加载...")
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "login__type__container__scan__qrcode"))
            )

            # 获取二维码元素
            qr_element = self.driver.find_element(By.CLASS_NAME, "login__type__container__scan__qrcode")

            # 截图方式获取二维码
            qr_element.screenshot(self.qrcode_path)

            # 显示二维码
            self.show_qrcode_with_pillow()

            # 等待url中出现"token="，表明浏览器已跳转
            WebDriverWait(self.driver, 60).until(
                lambda d: "token=" in d.current_url
            )

            # 提取token和cookies
            self.token = self.get_token()
            self.cookies = self.get_all_cookies()
            # 储存到数据库
            self.save_to_database()
            return True

        except Exception as e:
            print(f"获取二维码时出错: {e}")
            # 保存页面截图以便调试
            self.driver.save_screenshot(PATH_ERROR_SCREENSHOT)
            print(f"已保存页面截图到 {PATH_ERROR_SCREENSHOT}")
            return False

    def close(self):
        """
        关闭浏览器驱动，删除临时文件
        """
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")

        # 删除qrcode.png
        if os.path.isfile(PATH_QRCODE):
            os.remove(PATH_QRCODE)
        if os.path.isfile(PATH_ERROR_SCREENSHOT):
            os.remove(PATH_ERROR_SCREENSHOT)

    def save_to_database(self) -> None:
        """
        将公众号数据保存到数据库
        """
        try:
            cookies = Cookies.objects.create(
                cookies=json.dumps(self.cookies),
                token=self.token
            )
            print(f"成功保存Cookie到数据库，ID: {cookies.id}")
        except Exception as e:
            print(f"保存到数据库失败: {e}")


# 执行函数
if __name__ == "__main__":
    launcher = WxmpLauncher()
    try:
        launcher.login()
        print(launcher.token)
        print(launcher.cookies)
    finally:
        launcher.close()