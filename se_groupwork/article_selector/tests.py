from django.test import TestCase
from article_selector.models import Preference
from article_selector.article_selector import sort_articles_by_preference, get_campus_accounts, get_accounts_by_user, get_customized_accounts
from user.models import User, Subscription, History, Favorite
from webspider.models import PublicAccount, Article
from article_selector.meilisearch.meili_tools import MeilisearchTool
from se_groupwork.global_tools import global_meili_tool_load
import json
import time

# Create your tests here.
class ArticleSelectorTestCase(TestCase):
    users_info = {}
    accounts_info = {}
    articles_info = {}
    subscriptions_info = {}
    browses_info = {}
    favorites_info = {}
    testarticle_ids = []

    def setUp(self):
        with open("article_selector/testdata.json", "r", encoding='utf-8') as f:
            data = json.load(f)
            self.users_info = data['users']
            self.accounts_info = data['accounts']
            self.articles_info = data['articles']
            self.subscriptions_info = data['subscriptions']
            self.browses_info = data['browses']
            self.favorites_info = data['favorites']
        return
    
    def test_article_selector(self):
        def t01_add_account_and_user(self):
            for user in self.users_info:
                User.objects.create_user(**user)
                print(f"*新增用户‘{user['username']}’")
            for account in self.accounts_info:
                print(account['name'])
                PublicAccount.objects.create(**account, is_default=True)
                print(f"*新增公众号‘{account['name']}’")
            for article in self.articles_info:
                account = PublicAccount.objects.get(fakeid=article['public_account'])
                Article.objects.create(
                    public_account=account,
                    title=article['title'],
                    content=article['content'],
                    article_url=article['article_url'],
                    publish_time=article['publish_time'],
                    summary=article['summary'],
                    tags=article['tags'],
                    key_info=article['key_info'],
                    tags_vector=article['tags_vector'],
                    semantic_vector=article['semantic_vector']
                )
                print(f"*新增文章‘{article['title']}’")
            Preference.objects.output(outputfile="article_selector/testresult_01_aaau.json")
            self.assertEqual(User.objects.count(), len(self.users_info))
            self.assertEqual(PublicAccount.objects.count(), len(self.accounts_info))
            self.assertEqual(Article.objects.count(), len(self.articles_info))
            return
        
        def t02_add_subscription(self):
            for subscription in self.subscriptions_info:
                user_id = subscription['user']
                user = User.objects.get(id=user_id)
                for account_id in subscription['accounts']:
                    account = PublicAccount.objects.get(id=account_id)
                    print(f"*用户‘{user.username}’订阅公众号‘{account.name}’")
                    Subscription.objects.create_subscription(user, account)
            Preference.objects.output(outputfile="article_selector/testresult_02_as.json")
            return
    
        def t03_browse_and_favorite(self):
            for browse in self.browses_info:
                user_id = browse['user']
                user = User.objects.get(id=user_id)
                for article_id in browse['articles']:
                    article = Article.objects.get(id=article_id)
                    print(f"*用户‘{user.username}’浏览文章‘{article.title}’")
                    History.objects.create_history(user, article)
            for favorite in self.favorites_info:
                user_id = favorite['user']
                user = User.objects.get(id=user_id)
                for article_id in favorite['articles']:
                    article = Article.objects.get(id=article_id)
                    print(f"*用户‘{user.username}’收藏文章‘{article.title}’")
                    Favorite.objects.create_favorite(user, article)
            Preference.objects.output(outputfile="article_selector/testresult_03_baf.json")
            return
        
        def t_04_accounts_type(self):
            result = {}
            result['campus_accounts'] = [a.name for a in get_campus_accounts()]
            for preference in Preference.objects.all():
                result[preference.user.username] = {
                    'all_accounts': [a.name for a in get_accounts_by_user(preference.user)],
                    'customized_accounts': [a.name for a in get_customized_accounts(preference.user)]
                }
            with open("article_selector/testresult_04_accounts_type.json", "w", encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            return
        
        def t05_recommend_article(self):
            for user in User.objects.all():
                all_accounts = get_accounts_by_user(user)
                origin_articles = Article.objects.filter(public_account__in=all_accounts)
                recommended_articles = sort_articles_by_preference(user, origin_articles)
                print(f"用户‘{user.username}’推荐文章：")
                for article in recommended_articles:
                    print(f"  - {article.title}")
            return

        print("test 01: add account and user")
        t01_add_account_and_user(self)
        print("test 02: add subscription")
        t02_add_subscription(self)
        print("test 03: browse and favorite")
        t03_browse_and_favorite(self)
        print("test 04: accounts type")
        t_04_accounts_type(self)
        print("test 05: recommend article")
        t05_recommend_article(self)

    def test_meili_search(self):
        def t00_setup(self):
            for account in self.accounts_info:
                PublicAccount.objects.create(**account, is_default=True)
            for article in self.articles_info:
                account = PublicAccount.objects.get(fakeid=article['public_account'])
                Article.objects.create(
                    public_account=account,
                    title=article['title'],
                    content=article['content'],
                    article_url=article['article_url'],
                    publish_time=article['publish_time'],
                    summary=article['summary'],
                    tags=article['tags'],
                    key_info=article['key_info'],
                    tags_vector=article['tags_vector'],
                    semantic_vector=article['semantic_vector']
                )

        def t01_meili_init(self):
            meili_tool = global_meili_tool_load()
            meili_tool.clear_index()
            time.sleep(1)
            self.assertTrue(MeilisearchTool.initialized)
            self.assertTrue(meili_tool.valid)
            self.assertTrue(meili_tool.test_mode)
            index_num = meili_tool.get_article_index_count()
            self.assertEqual(index_num, 0)
            return meili_tool

        def t02_meili_update_index(self, meili_tool: MeilisearchTool):
            articles = Article.objects.all()
            articles_id = [article.id for article in articles]
            meili_tool.update_article(articles_id[0])
            time.sleep(1)
            index_num = meili_tool.get_article_index_count()
            checkflag = meili_tool.get_article_index_by_id(articles_id[0]) is not None
            self.assertEqual(index_num, 1)
            self.assertTrue(checkflag)
            meili_tool.delete_article(articles_id[0])
            time.sleep(1)
            index_num = meili_tool.get_article_index_count()
            self.assertEqual(index_num, 0)
            meili_tool.update_batch_articles(articles_id)
            time.sleep(1)
            index_num = meili_tool.get_article_index_count()
            all_articles = meili_tool.get_all_articles_index()
            self.assertEqual(set(articles_id), set(all_articles.keys()))
            self.assertEqual(index_num, len(articles))
            return

        def t03_meili_clear_and_sync(self, meili_tool: MeilisearchTool):
            all_articles = Article.objects.all()
            all_articles_id = [article.id for article in all_articles]
            meili_tool.clear_index()
            time.sleep(1)
            index_num = meili_tool.get_article_index_count()
            self.assertEqual(index_num, 0)
            meili_tool.update_article(all_articles_id[0])
            time.sleep(1)
            meili_tool.sync_articles_index_with_mysql()
            time.sleep(1)
            index_num = meili_tool.get_article_index_count()
            self.assertEqual(index_num, len(all_articles))
            return
        
        def t04_meili_rebuild(self, meili_tool: MeilisearchTool):
            meili_tool.rebuild_index()
            time.sleep(1)
            index_num = meili_tool.get_article_index_count()
            self.assertEqual(index_num, len(Article.objects.all()))
            return
        
        def t05_meili_search(self, meili_tool: MeilisearchTool):
            result = meili_tool.search_articles("学期")
            self.assertGreater(len(result), 0)
            for id in result:
                self.assertTrue(Article.objects.filter(id=id).exists())
            return

        def t06_meili_invalid(self, meili_tool: MeilisearchTool):
            meili_tool.valid = False
            self.assertIsNone(meili_tool.search_articles("学期"))
            self.assertIsNone(meili_tool.get_article_index_by_id(1))
            self.assertIsNone(meili_tool.get_article_index_count())
            self.assertIsNone(meili_tool.get_all_articles_index())
            self.assertIsNone(meili_tool.delete_article(1))
            self.assertIsNone(meili_tool.update_article(1))
            self.assertIsNone(meili_tool.update_batch_articles([1]))
            self.assertIsNone(meili_tool.clear_index())
            self.assertIsNone(meili_tool.sync_articles_index_with_mysql())
            self.assertIsNone(meili_tool.rebuild_index())
            meili_tool.valid = True
            return

        t00_setup(self)
        print("test 01: meili init")
        meili_tool = t01_meili_init(self)
        print("test 02: meili update index")
        t02_meili_update_index(self, meili_tool)
        print("test 03: meili clear and sync")
        t03_meili_clear_and_sync(self, meili_tool)
        print("test 04: meili rebuild")
        t04_meili_rebuild(self, meili_tool)
        print("test 05: meili search")
        t05_meili_search(self, meili_tool)
        print("test 06: meili invalid")
        t06_meili_invalid(self, meili_tool)


