from wxmp_launcher import WxmpLauncher
from biz_searcher import BizSearcher
from article_fetcher import ArticleFetcher
# 添加Django环境设置
import os
import django
import sys
# 定位到项目根目录（manage.py所在目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "se_groupwork.settings")
django.setup()


def main():
    # 步骤1: 通过wxmp_launcher获得登陆的cookies和token
    need_cookie = input("是否需要cookie？").strip()
    if need_cookie != "":
        print("步骤1: 登录微信公众平台获取cookies和token...")
        launcher = WxmpLauncher()
        try:
            if launcher.login():
                print("登录成功!")
            else:
                print("登录失败，请检查网络连接或二维码扫描")
                return
        except Exception as e:
            print(f"登录过程中发生错误: {e}")
            return
        finally:
            launcher.close()

    # 步骤2: 通过cookies和token以及biz_searcher获取fakeid
    print("\n步骤2: 搜索公众号获取fakeid...")
    search_query = input("请输入要搜索的公众号名称: ").strip()
    if not search_query:
        print("公众号名称不能为空!")
        return

    searcher = BizSearcher(
        query=search_query
    )

    try:
        mp_dict = searcher.biz_search()

        if not mp_dict:
            print("未找到相关公众号，请尝试其他关键词")
            return

        # 显示搜索结果并选择第一个
        print("找到以下公众号:")
        for i, (name, fid) in enumerate(mp_dict.items(), 1):
            print(f"{i}. {name} (fakeid: {fid})")

        # 默认选择第一个
        selected_name = list(mp_dict.keys())[0]
        fakeid = mp_dict[selected_name]
        print(f"\n默认选择第一个公众号: {selected_name} (fakeid: {fakeid})")
    except Exception as e:
        print(f"搜索公众号过程中发生错误: {e}")
        return

    # 步骤3: 通过cookies、token和fakeid在article_fetcher中生成data.csv
    print("\n步骤3: 获取文章列表")
    fetcher = ArticleFetcher(
        fakeid=fakeid
    )

    try:
        # 获取文章总数
        total_count = fetcher.get_total_count()
        if total_count <= 0:
            print("获取文章总数失败，请检查Cookie、token和fakeid是否正确")
            return

        print(f"公众号 '{selected_name}' 共有 {total_count} 篇文章")

        # 获取文章列表，并保存
        fetcher.fetch_articles(5)
    except Exception as e:
        print(f"获取文章列表过程中发生错误: {e}")
        return


if __name__ == "__main__":
    main()