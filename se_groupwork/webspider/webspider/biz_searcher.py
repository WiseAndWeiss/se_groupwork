import requests
import math
from tqdm import tqdm
import time
import random
import json
from typing import List, Dict, Any
from webspider.webspider.avatar_downloader import AvatarDownloader
from django.conf import settings
import os
from webspider.models import PublicAccount, Cookies


class BizSearcher:
    def __init__(self, query: str = None):
        """
        初始化公众号查找器,用于根据用户搜索的内容找到对应的公众号

        Args:
            query: 用户搜索的内容
        """
        self.url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        self.token, self.cookies = self.load_cookies()
        self.cookies = json.loads(self.cookies)  # 转化为requests可以使用的形式
        self.query = query  # 搜索的内容
        self.avatar_urls = {}  # 存放图片的地址
        self.avatar_downloader = AvatarDownloader(save_dir=os.path.join(settings.MEDIA_ROOT, 'icons'))

        # 初始化参数和headers
        self.params = {
            "token": self.token,
            "query": self.query,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "action": "search_biz",
            "begin": "0",
            "count": "5",
        }

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Mobile Safari/537.36",
        }

    def load_cookies(self) -> tuple[str, str] | tuple[None, None]:
        """
        从数据库加载Cookie并转换为字符串格式
        """
        try:
            cookies = Cookies.objects.latest('created_at')
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

    def get_mp_list(self, count: int = 5, per_page: int = 5) -> List[Dict[str, Any]]:
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

        for i in tqdm(range(page), desc="获取公众号列表"):
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
                    content_list.extend(content_json.get("list", []))
                else:
                    print(f"第{i + 1}页验证失败")

                # 随机延迟，避免请求过于频繁
                time.sleep(random.randint(1, 3))
            except Exception as e:
                print(f"获取第{i + 1}页失败: {e}")
                continue
        
        # print(content_list)
        return content_list

    def process_mp_list(self, json_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将原始的json数据处理为 "nick_name":"fakeid" 这样的字典
        Args:
            json_data:原始的json数据
        """
        mp_dict = {}
        try:
            for account in json_data:
                # 确保每个账号信息是字典类型
                if isinstance(account, dict):
                    nickname = account.get('nickname')
                    fakeid = account.get('fakeid')
                    self.avatar_urls[nickname] = account.get('round_head_img')
                    # 只有当两个字段都存在时才添加
                    if nickname and fakeid:
                        mp_dict[nickname] = fakeid
            return mp_dict
        except Exception as e:
            print(f"公众号查找失败：{e}")
            return {}

    def save_to_database(self, mp_dict: Dict[str, Any]) -> None:
        """
        将公众号数据保存到数据库

        Args:
            mp_dict: 公众号字典 {昵称: fakeid}
        """
        try:
            for nickname, fakeid in mp_dict.items():
                local_icon_path = self.avatar_urls.get(nickname)

                # 检查是否已存在相同fakeid的公众号
                account, created = PublicAccount.objects.get_or_create(
                    fakeid=fakeid,
                    defaults={
                        'name': nickname
                    }
                )

                if created:
                    self._save_icon_to_imagefield(account, local_icon_path)
                    print(f"✅ 已保存公众号: {nickname} (fakeid: {fakeid})")
                else:
                    print(f"⚠️  公众号已存在: {nickname} (fakeid: {fakeid})")
        except Exception as e:
            print(f"保存到数据库失败: {e}")

    def _save_icon_to_imagefield(self, account, image_path):
        """
        将本地图片保存到ImageField
        """
        try:
            # 如果账号已经有头像，先删除旧文件
            if account.icon and account.icon.name:
                account.icon.delete(save=False)

            # 直接设置ImageField的路径，而不是重新保存文件
            if image_path and os.path.exists(image_path):
                # 获取相对于MEDIA_ROOT的路径
                if image_path.startswith(settings.MEDIA_ROOT):
                    relative_path = os.path.relpath(image_path, settings.MEDIA_ROOT)
                else:
                    # 如果图片不在MEDIA_ROOT下，需要移动或复制
                    relative_path = os.path.join('icons', os.path.basename(image_path))
                
                account.icon.name = relative_path
                account.save()
                print(f"✅ 已设置头像: {account.name} -> {relative_path}")
            else:
                print(f"⚠️ 头像文件不存在: {image_path}")
            
        except Exception as e:
            print(f"❌ 保存头像失败 {account.name}: {str(e)}")

    def biz_search(self):
        mp_json = self.get_mp_list()
        mp_dict = self.process_mp_list(mp_json)
        self.avatar_urls = self.avatar_downloader.download(self.avatar_urls)
        self.save_to_database(mp_dict)
        return mp_dict
    

# 使用示例
if __name__ == '__main__':
    # 初始化公众号抓取器
    searcher = BizSearcher(
        query="华侨"
    )
    print(searcher.biz_search())

