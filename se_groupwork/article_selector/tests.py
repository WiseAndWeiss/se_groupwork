from django.test import TestCase
from article_selector.models import Preference
from article_selector.article_selector import sort_articles_by_preference, get_campus_accounts, get_accounts_by_user, get_customized_accounts
from user.models import User, Subscription, History, Favorite
from webspider.models import PublicAccount, Article
import json

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
    
    def test(self):
        def t01_add_account_and_user(self):
            for user in self.users_info:
                User.objects.create_user(**user)
                print(f"*新增用户‘{user['username']}’")
            for account in self.accounts_info:
                PublicAccount.objects.create(**account)
                print(f"*新增公众号‘{account['name']}’")
            for article in self.articles_info:
                Article.objects.create(
                    public_account_id=article['public_account'],
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

        # for account in data['accounts']:
        #     a = PublicAccount.objects.create(**account)
        #     print(f"创建新公众号: {a.name}")
        #     account_list.append(a)
        # for user in data['users']:
        #     u = User.objects.create_user(**user)
        #     print(f"创建新用户: {u.username}")
        #     user_list.append(u)
        # for article in data['articles']:
        #     a = Article.objects.create(
        #         public_account_id=article['public_account'],
        #         title=article['title'],
        #         content=article['content'],
        #         article_url=article['article_url'],
        #         publish_time=article['publish_time'],
        #         summary=article['summary'],
        #         tags=article['tags'],
        #         key_info=article['key_info'],
        #         tags_vector=article['tags_vector'],
        #         semantic_vector=article['semantic_vector']
        #     )
        #     print(f"添加新文章: <{a.title}>({a.public_account.name})")
        #     article_list.append(a)
        # for subscription in data['subscriptions']:
        #     user_id = subscription['user']
        #     for account_id in subscription['accounts']:
        #         Subscription.objects.create_subscription(user_list[user_id], account_list[account_id])
        #         print(f"用户 \"{user_list[user_id].username}\" 订阅公众号\"{account_list[account_id].name}\"")
        # for browse in data['browses']:
        #     user_id = browse['user']
        #     for article_id in browse['articles']:
        #         History.objects.create_history(user_list[user_id], article_list[article_id])
        #         print(f"用户 \"{user_list[user_id].username}\" 浏览文章 <{article_list[article_id].title}>")
        # for favorite in data['favorites']:
        #     user_id = favorite['user']
        #     for article_id in favorite['articles']:
        #         Favorite.objects.create_favorite(user_list[user_id], article_list[article_id])
        #         print(f"用户 \"{user_list[user_id].username}\" 收藏文章 <{article_list[article_id].title}>")
        # for test in data['test']:
        #     self.test_article.append(article_list[test])

    # def test_article_preference(self):
    #     Preference.objects.output('outputfile.txt')
    #     print("=================================================")
    #     users = User.objects.all()
    #     users = reversed(users)
    #     for user in users:
    #         print(f"用户 \"{user.username}\" 的文章推荐列表:")
    #         recommended_articles = sort_articles_by_preference(user, self.test_article)
    #         recommended_articles_info = [(article.title, article.public_account.name) for article in recommended_articles]
    #         for i,article_info in enumerate(recommended_articles_info):
    #             print(f"    {i+1}. <{article_info[0]}> ({article_info[1]})")
    
    # def test_get_account(self):
    #     campus_accounts = get_campus_accounts()
    #     for account in campus_accounts:
    #         print(f"校园公众号: {account.name}")