import requests
import os




class AvatarDownloader:
    def __init__(self, save_dir="avatars"):
        """
        初始化头像下载器

        Args:
            save_dir: 保存目录
        """
        self.save_dir = save_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })

        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)

    def download(self, name_url_dict):
        """
        下载所有头像，并返回 {公众号名称: 本地文件路径} 的字典

        Args:
            name_url_dict: 字典格式 {公众号名称: 头像URL}

        Returns:
            dict: {公众号名称: 本地文件路径}
        """
        print(f"开始下载 {len(name_url_dict)} 个头像...")
        result_dict = {}

        for name, url in name_url_dict.items():
            local_path = self._download_single(name, url)
            if local_path:
                result_dict[name] = local_path

        print(f"\n下载完成! 成功: {len(result_dict)}/{len(name_url_dict)}")
        return result_dict

    def _download_single(self, name, url):
        """
        下载单个头像

        Args:
            name: 公众号名称
            url: 头像URL

        Returns:
            str: 本地文件路径（如果下载成功），否则返回None
        """
        try:
            # 生成安全文件名
            safe_name = self._sanitize_filename(name)
            file_ext = self._get_file_extension(url)
            filename = f"{safe_name}.{file_ext}"
            filepath = os.path.join(self.save_dir, filename)

            # 下载图片
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"✅ {name}")

                # 返回相对路径（相对于当前工作目录）
                relative_path = os.path.relpath(filepath)
                return relative_path
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            return None

    def _sanitize_filename(self, name):
        """清理文件名中的非法字符"""
        # 简单清理，移除Windows文件名中的非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '')
        return name.strip()

    def _get_file_extension(self, url):
        """从URL中获取文件扩展名"""
        # 尝试从wx_fmt参数获取
        if 'wx_fmt=' in url:
            return url.split('wx_fmt=')[1].split('&')[0].split('/')[0]

        # 默认使用png
        return 'png'


# 使用示例
if __name__ == "__main__":
    # 你的数据格式：{公众号名称: 头像URL}
    name_url_dict = {
        '厦门本地宝': 'http://mmbiz.qpic.cn/sz_mmbiz_png/4eGXlI7GKKxmIgpTHjcSFMrSjnbUMtaVC8zakoIgOqShfibZDKWN21UQBjWSPowibYoqaPNibcxEia0uAdBb6kjZFA/0?wx_fmt=png',
        '厦门文旅': 'http://mmbiz.qpic.cn/mmbiz_png/m2htgmbutiallCS9xRc6wpeWFKFMQp6icTJibyOz2GL3ib2yc2fwicRUTXoiccKj3Hzdov6VfxdPFxicwkoXPwF1akIrw/0?wx_fmt=png',
        '厦门市住房保障中心': 'http://mmbiz.qpic.cn/mmbiz_png/JR0b4ICibAQUPrzbowicR2wxHyI0SzCUCFufENVSHOMKUibYdqW97a4hfllFSbGVxNs7DwG9usRMNicnN6zo2giaVTQ/0?wx_fmt=png',
        '厦门日报': 'http://mmbiz.qpic.cn/mmbiz_png/wXVeicJMia0rSDLCX5fQtp4Olvw9Acs490apQic0qhtZ7Tibyg2CaPjPhlTNiaeBcTlVzdQr6I0B29Y9Ves4wQCVDrw/0?wx_fmt=png',
        '厦门大学': 'http://mmbiz.qpic.cn/mmbiz_png/g84wSb3VFX50kia5LicgSDdURS39j74IX30Oic6SBKfBulYSYyJbKJgl1oH5zT7ic3Q2SRmMpJ9tRCLbIOic8V6lEKA/0?wx_fmt=png'
    }

    # 创建下载器并下载
    downloader = AvatarDownloader()
    downloader.download(name_url_dict)