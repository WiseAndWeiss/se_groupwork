"""
文章信息获取器：通过公众号的fakeid获取文章的url，再通过url获取文章的content
"""
import requests
import math
from tqdm import tqdm
import time
import random
import json
from typing import List, Dict, Any, Tuple
from django.utils import timezone
import cloudscraper
import bs4
# 添加Django环境设置
import os
import django
import sys
from avatar_downloader import AvatarDownloader
# 定位到项目根目录（manage.py所在目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "se_groupwork.settings")
django.setup()
# 导入Django模型
from webspider.models import Article, Cookies, PublicAccount


class ArticleFetcher:
    def __init__(self, fakeid: str = None):
        """
        初始化文章抓取器

        Args:
            fakeid: 公众号的biz号
        """
        self.token, self.cookies = self.load_cookies()
        self.cookies = json.loads(self.cookies)  # 转化为requests可以使用的形式
        self.fakeid = fakeid
        self.public_account, _ = PublicAccount.objects.get_or_create(fakeid=fakeid)
        self.url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
        self.scraper = cloudscraper.create_scraper()
        self.avatar_downloader = AvatarDownloader(save_dir="article_covers")

        # 初始化参数和headers
        self.params = {
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "action": "list_ex",
            "begin": "0",
            "count": "5",
            "query": "",
            "fakeid": self.fakeid,
            "type": "9",
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Mobile Safari/537.36",
        }

    def load_cookies(self) -> tuple[str, str] | tuple[None, None]:
        """
        从数据库加载Cookie并转换为字符串格式
        """
        try:
            cookies = Cookies.objects.latest('created_at')  # 选取最新的cookies
            if cookies:
                return cookies.token, cookies.cookies
            else:
                print("未找到Cookie记录")
                return None, None
        except Exception as e:
            print(f"加载Cookie失败: {e}")
            return None, None

    def is_validated(self, resp_json: Dict[str, Any]) -> bool:
        """
        判断响应是否验证成功
        """
        return resp_json.get('base_resp', {}).get('err_msg') == 'ok'

    def get_total_count(self) -> int:
        """
        获取文章总数

        Returns:
            文章总数，如果获取失败返回-1
        """
        try:
            response = requests.get(
                self.url,
                headers=self.headers,
                params=self.params,
                cookies=self.cookies,
                timeout=30
            )
            content_json = response.json()

            if self.is_validated(content_json):
                count = int(content_json["app_msg_cnt"])
                return count
            else:
                print(f"验证失败: {content_json.get('base_resp', {}).get('err_msg')}")
                return -1
        except Exception as e:
            print(f"获取文章总数失败: {e}")
            return -1

    def get_content_list(self, count: int, per_page: int = 5) -> List[Dict[str, Any]]:
        """
        获取文章列表

        Args:
            count: 文章总数
            per_page: 每页获取的文章数

        Returns:
            文章列表
        """
        page = math.ceil(count / per_page)
        content_list = []

        for i in tqdm(range(page), desc="获取文章列表"):
            self.params["begin"] = str(i * per_page)

            try:
                response = requests.get(
                    self.url,
                    headers=self.headers,
                    params=self.params,
                    cookies=self.cookies,
                    timeout=30
                )
                content_json = response.json()

                if self.is_validated(content_json):
                    content_list.extend(content_json.get("app_msg_list", []))
                else:
                    print(f"第{i + 1}页验证失败")

                # 随机延迟，避免请求过于频繁
                time.sleep(random.randint(1, 3))

            except Exception as e:
                print(f"获取第{i + 1}页失败: {e}")
                continue

        return content_list

    def get_article_content(self, article_url: str) -> Dict[str, str]:
        """
        通过文章的url，获取文章的短链接、标题、内容、封面、作者等
        提取短链接是因为：短链接不会改变，长链接会改变

        Return:
            [文章内容，封面]
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090819) XWEB/8519 Flu',
            'Referer': 'https://mp.weixin.qq.com/'
        }
        try:
            response = self.scraper.get(article_url, headers=headers)
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            # 提取信息
            result = {}
            title = soup.find(attrs={'property':'og:title'})['content']
            author = soup.find(attrs={'property':'og:article:author'})['content']
            link = soup.find(attrs={'property':'og:url'})['content']
            content = soup.find('div', class_='rich_media_content').get_text()
            remote_cover_url = soup.find(attrs={'property':'og:image'})['content']
            # 提取文章封面
            local_cover_url = self.get_cover(remote_cover_url, title)
            result.update({
                'link': link, 
                'author': author, 
                'content': content, 
                'title': title,
                'cover_url': local_cover_url
            })
            
            return result
        except Exception as e:
            print(f"获取文章内容失败: {e}")
            return "获取文章内容失败", ""


    def get_cover(self, img_url: str, article_title: str) -> str:
        """
        通过img_url下载对应的文章封面图
        
        Args:
            img_url: 封面图URL
            article_title: 文章标题（用于生成文件名）
            
        Returns:
            本地文件路径
        """
        if not img_url:
            return "获取封面失败"
            
        try:
            # 使用文章标题作为文件名，下载封面图
            name_url_dict = {article_title: img_url}
            result_dict = self.avatar_downloader.download(name_url_dict)
            
            # 返回下载的本地路径
            return result_dict.get(article_title, "")
        except Exception as e:
            print(f"下载文章封面图失败: {e}")
            return ""

    def save_to_database(self, content_list: List[Dict[str, Any]]) -> None:
        """
        将文章数据保存到数据库。

        Args:
            content_list：包含title、link、publish_time、cover_url等信息
        """
        try:
            for item in content_list:
                article_url = item.get("link", "")
                title = item.get("title", "")
                publish_time = timezone.datetime.fromtimestamp(item.get("create_time", 0))

                # 由于公众号发布文章后很少会修改（正文部分支持修改最多20个字），因此如果数据库已有文章，就不需要爬取其它内容了（降低被封风险）
                if Article.objects.filter(title=title, publish_time=publish_time).exists():
                    print(f"文章 {title} 已存在，停止爬取")
                    continue
                
                result = self.get_article_content(article_url)

                article, created = Article.objects.get_or_create(
                    article_url=result['link'],
                    defaults={
                        'public_account': self.public_account,
                        'title': title,
                        'publish_time': publish_time,
                        'content': result['content'],
                        'cover_url': result['cover_url'],
                        'author': result['author']
                    }
                )
                if created:
                    print(f"✅ 已保存文章链接: {title}")
                else:
                    print(f"⚠️ 文章链接已存在: {title}")
        except Exception as e:
            print(f"保存到数据库失败: {e}")

    def fetch_articles(self, n: int):
        """
        完整流程：获取文章总数 -> 获取文章url等信息（不包含内容） -> 利用ArticleScraper和url获取文章内容 -> 保存到数据库
        """
        # 获取文章总数
        total_count = self.get_total_count()
        if total_count <= 0:
            print("获取文章总数失败，请检查Cookie、token和fakeid是否正确")
            return
        print(f"共有 {total_count} 篇文章")
        n = min(total_count, n)
        # 获取文章列表
        content_list = self.get_content_list(n)
        if not content_list:
            print("获取文章列表失败")
            return
        # 保存到数据库
        self.save_to_database(content_list)


# 使用示例
if __name__ == '__main__':

    # 初始化文章抓取器
    fetcher = ArticleFetcher(
        fakeid='MzA4OTIyMzgxMw=='
    )

    print(fetcher.cookies)
    print(fetcher.token)
    print(fetcher.fakeid)

    # 获取文章
    fetcher.fetch_articles(5)
