from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User, Subscription, History, Favorite
from webspider.models import Article, PublicAccount
from django.utils import timezone
from remoteAI.remoteAI.vectorize import keywords_vectorize, tags_vectorize

from datetime import datetime, timedelta
import json

class ArticleSelectorTests(TestCase):

    testdata = None
    user = None

    def setUp(self):
        with open('tests_api/testdata_articles_selector.json', 'r', encoding='utf-8') as f:
            self.testdata = json.load(f)
        # 创建测试用的User数据
        self.client = APIClient()
        self.user = User.objects.create_user(**self.testdata['user'])
        self.client.force_authenticate(user=self.user)
        # 创建测试用的PublicAccount数据
        for account_info in self.testdata['public_accounts']:
            PublicAccount.objects.create(**account_info)
        # 创建测试用的Article数据
        for article_info in self.testdata['articles']:
            pa = PublicAccount.objects.get(fakeid=article_info['public_account_fakeid'])
            del article_info['public_account_fakeid']
            article_info['public_account'] = pa
            pt = timezone.now() - timedelta(
                days=article_info['publish_time_delta']['days'],
                hours=article_info['publish_time_delta']['hours']
            )
            del article_info['publish_time_delta']
            article_info['publish_time'] = pt
            if article_info['summary'] != '':
                tags = article_info['tags'].split(',')
                article_info['tags_vector'] = tags_vectorize(tags)
                keywords = article_info['key_info'].split(',')
                article_info['semantic_vector'] = keywords_vectorize(keywords)
            Article.objects.create(**article_info)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(PublicAccount.objects.count(), len(self.testdata['public_accounts']))
        self.assertEqual(Article.objects.count(), len(self.testdata['articles']))

    def test_latest_api(self):
        '''测试latest API'''
        # 仅默认公众号(12篇)
        response = self.client.get(reverse('articles-latest'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 12)
        self.assertEqual(response.data['reach_end'], True)
        # 添加订阅公众号(共25篇，其中一篇是无效状态)
        account_c1 = PublicAccount.objects.get(fakeid='C1')
        account_c2 = PublicAccount.objects.get(fakeid='C2')
        Subscription.objects.create_subscription(self.user, account_c1)
        Subscription.objects.create_subscription(self.user, account_c2)
        response = self.client.get(reverse('articles-latest'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 20)
        self.assertEqual(response.data['reach_end'], False)
        response = self.client.get(reverse('articles-latest'), data={'start_rank': 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 4)
        self.assertEqual(response.data['reach_end'], True)
    
    def test_recommend_api(self):
        '''测试recommend API'''
        # 准备数据
        account_c1 = PublicAccount.objects.get(fakeid='C1')
        account_c2 = PublicAccount.objects.get(fakeid='C2')
        article_t1_1 = Article.objects.get(article_url='1/T1')
        article_t1_2 = Article.objects.get(article_url='2/T1')
        article_t2_1 = Article.objects.get(article_url='1/T1')
        article_t2_2 = Article.objects.get(article_url='2/T1')
        Subscription.objects.create_subscription(self.user, account_c1)
        Subscription.objects.create_subscription(self.user, account_c2)
        History.objects.create_history(self.user, article_t1_1)
        History.objects.create_history(self.user, article_t1_2)
        History.objects.create_history(self.user, article_t2_1)
        History.objects.create_history(self.user, article_t2_2)
        Favorite.objects.create_favorite(self.user, article_t1_1)
        # 测试
        response = self.client.get(reverse('articles-recommended'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 8)
        first_article_url = response.data['articles'][0]['article_url']
        secend_article_url = response.data['articles'][1]['article_url']
        self.assertTrue(("T1" in first_article_url) or ("T2" in first_article_url))
        self.assertTrue(("T1" in secend_article_url) or ("T2" in secend_article_url))

    def test_campus_and_customized_api(self):
        '''测试campus和customized API'''
        # 准备数据
        account_c1 = PublicAccount.objects.get(fakeid='C1')
        account_c2 = PublicAccount.objects.get(fakeid='C2')
        Subscription.objects.create_subscription(self.user, account_c1)
        Subscription.objects.create_subscription(self.user, account_c2)
        # 测试默认公众号
        response = self.client.get(reverse('articles-campus-latest'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 12)
        self.assertEqual(response.data['reach_end'], True)
        for article in response.data['articles']:
            self.assertTrue(('T1' in article['article_url']) or ('T2' in article['article_url']))
        # 测试自定义公众号
        response = self.client.get(reverse('articles-customized-latest'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 12)
        self.assertEqual(response.data['reach_end'], True)
        for article in response.data['articles']:
            self.assertTrue(('C1' in article['article_url']) or ('C2' in article['article_url']))
    
    def test_by_account_api(self):
        '''测试by_account API'''
        # 准备数据
        account_c1 = PublicAccount.objects.get(fakeid='C1')
        c1_id = account_c1.id
        Subscription.objects.create_subscription(self.user, account_c1)
        account_t1 = PublicAccount.objects.get(fakeid='T1')
        t1_id = account_t1.id
        # 测试
        response = self.client.get(reverse('articles-by-account'), data={'account_id': c1_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 6)
        self.assertEqual(response.data['reach_end'], True)
        for article in response.data['articles']:
            self.assertTrue('C1' in article['article_url'])
        response = self.client.get(reverse('articles-by-account'), data={'account_id': t1_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 6)
        self.assertEqual(response.data['reach_end'], True)
        for article in response.data['articles']:
            self.assertTrue('T1' in article['article_url'])

    def test_filter_api(self):
        '''测试filter API'''
        # 准备数据
        account_c1 = PublicAccount.objects.get(fakeid='C1')
        account_c2 = PublicAccount.objects.get(fakeid='C2')
        Subscription.objects.create_subscription(self.user, account_c1)
        Subscription.objects.create_subscription(self.user, account_c2)
        # 测试
        require ={
            'account_id': PublicAccount.objects.get(fakeid='T1').id,
            'tags': ['教务通知'],
            'date_from': (timezone.now() - timedelta(days=1)).date().strftime('%Y-%m-%d'),
            'date_to': (timezone.now() + timedelta(days=1)).date().strftime('%Y-%m-%d')
        }
        date_from = timezone.datetime.strptime(require['date_from'], '%Y-%m-%d')
        date_from = timezone.make_aware(date_from)
        date_to = timezone.datetime.strptime(require['date_to'], '%Y-%m-%d')
        date_to = timezone.make_aware(date_to)
        response = self.client.post(
            reverse('articles-filter'),
            data=json.dumps(require),
            content_type='application/json'
        )
        # 检查
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['articles']), 2)
        for article in response.data['articles']:
            self.assertTrue('T1' in article['article_url'])
            self.assertTrue('教务通知' in article['tags'])
            self.assertTrue(date_from <= timezone.datetime.fromisoformat(article['publish_time']))
            self.assertTrue(date_to >= timezone.datetime.fromisoformat(article['publish_time']))
        