from django.test import TestCase
from articleSelector.models import Preference
from articleSelector.articleSelector import sort_articles_by_preference
from user.models import User, Subscription
from webspider.models import PublicAccount, Article
import json

# Create your tests here.
class ArticleSelectorTestCase(TestCase):

    def setUp(self):
        with open("articleSelector/testdata.json", "r", encoding='utf-8') as f:
            data = json.load(f)
        user_list = [None]
        account_list = [None]
        article_list = [None]
        self.test_article = []
        for user in data['users']:
            u = User.objects.create_user(**user)
            print(f"创建新用户: {u.username}")
            user_list.append(u)
        for account in data['accounts']:
            a = PublicAccount.objects.create(**account)
            print(f"创建新公众号: {a.name}")
            account_list.append(a)
        for article in data['articles']:
            a = Article.objects.create(
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
            print(f"添加新文章: <{a.title}>({a.public_account.name})")
            article_list.append(a)
        for subscription in data['subscriptions']:
            user_id = subscription['user']
            for account_id in subscription['accounts']:
                Subscription.objects.create_subscription(user_list[user_id], account_list[account_id])
                print(f"用户 \"{user_list[user_id].username}\" 订阅公众号\"{account_list[account_id].name}\"")
        for browse in data['browses']:
            user_id = browse['user']
            for article_id in browse['articles']:
                Preference.objects.update_preference(user_list[user_id], article_list[article_id], 'browse')
                print(f"用户 \"{user_list[user_id].username}\" 浏览文章 <{article_list[article_id].title}>")
        for favorite in data['favorites']:
            user_id = favorite['user']
            for article_id in favorite['articles']:
                Preference.objects.update_preference(user_list[user_id], article_list[article_id], 'favorite')
                print(f"用户 \"{user_list[user_id].username}\" 收藏文章 <{article_list[article_id].title}>")
        for test in data['test']:
            self.test_article.append(article_list[test])

    def test_article_selector_creation(self):
        Preference.objects.output('outputfile.txt')
        print("=================================================")
        users = User.objects.all()
        users = reversed(users)
        for user in users:
            print(f"用户 \"{user.username}\" 的文章推荐列表:")
            recommended_articles = sort_articles_by_preference(user, self.test_article)
            recommended_articles_info = [(article.title, article.public_account.name) for article in recommended_articles]
            for i,article_info in enumerate(recommended_articles_info):
                print(f"    {i+1}. <{article_info[0]}> ({article_info[1]})")
    