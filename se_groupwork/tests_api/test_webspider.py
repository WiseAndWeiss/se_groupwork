from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User
from webspider.models import PublicAccount, Article, Cookies
from webspider.webspider.wxmp_launcher import WxmpLauncher
from webspider.webspider.article_fetcher import ArticleFetcher
import json

# Create your tests here.
class WebspiderTestCase(TestCase):
    PREPARED_COOKIE = True

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example')
        self.client.force_authenticate(user=self.user)
        self.launcher = WxmpLauncher()
        if self.PREPARED_COOKIE:
            # 预先准备好cookie，此处经常失效，需要手动更新
            cookie = json.dumps({'xid': '616cc19f15704254e537901594b44e3c', 'data_bizuin': '3864870658', 'slave_user': 'gh_57eec1711514', 'slave_sid': 'Sk5JN1REc1ZzcndobzJzeTE1V2Fwajc1eHplelFKbGJFVlB0bHczRnpraXRZNXVraU1SVFBERFQzT0wwRllIeFI2SWpxaTFLYWlENkU1UjM3aklpRWVmUDJxcUxia0NMM2pPdWdKcmFfTWNOa3ExcnU3N3lEVHBJRk9vWUNiT3RPcW04YTBRMkk2dzloSUZ0', 'rand_info': 'CAESIF4MLCEZF12JL6W838jEqbkvn7Tiqy2ENsg/mLPWjkMh', 'data_ticket': 'HkJFd8T2TU0rrgCCbZUmuVE3MR2Lj4aEBqzJ7rfph9E4Z+RCmN3CMlHLzEYzNEeE', 'bizuin': '3864870658', 'mm_lang': 'zh_CN', 'slave_bizuin': '3864870658', 'uuid': '67be5ea061c49e990c51535c9500cf88', 'ua_id': 'JoqllqENjU1n3OEaAAAAAJkyTqSUiREGCf-GX_akcNk=', 'wxuin': '66419653903259', '_clck': '9qduem|1|g22|0'})
            token = "1458425898"
            Cookies.objects.create(cookies=cookie, token=token)
        else:
            try:
                self.launcher.login()
                print(self.launcher.token)
                print(self.launcher.cookies)
            finally:
                self.launcher.close()
            
    def test_webspider(self):
        '''
        path('public-accounts/campus/', views.CampusPublicAccountListView.as_view(), name='campus-public-accounts'),
        path('public-accounts/search/', views.SearchPublicAccountListView.as_view(), name='search-public-accounts'),
        path('new-accounts/search/', views.SearchNewAccountListView.as_view(), name='search-new-accounts'),
        path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
        '''
        def test_01_search_new_accounts(self):
            self.assertEqual(len(PublicAccount.objects.all()), 0)
            # 搜索新公众号
            response = self.client.get(reverse('webspider:search-new-accounts'), data={'name': '清华大学'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(len(response.data) > 0)
            print(response.data)
            print("Search Results for New Accounts:")
            for account in response.data:
                print(f"- {account['name']} ({account['fakeid']})")
            # 重复搜索新公众号
            response = self.client.get(reverse('webspider:search-new-accounts'), data={'name': '清华大学'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['count'] > 0)
            # 空参数
            response = self.client.get(reverse('webspider:search-new-accounts'))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            # 更新文章
            fakeid = PublicAccount.objects.get(name='清华大学').fakeid
            article_fetcher = ArticleFetcher(fakeid=fakeid, sleep_seconds=5)
            article_fetcher.fetch_articles(5)

        def test_02_search_accounts(self):
            # 搜索库内公众号
            response = self.client.get(reverse('webspider:search-public-accounts'), data={'name': '清华大学'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['count'] > 0)
            print("Search Results for Existing Accounts:")
            for account in response.data['public_accounts']:
                print(f"- {account['name']} ({account['fakeid']})")
            # 空参数
            response = self.client.get(reverse('webspider:search-public-accounts'))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        
        def test_03_campus_accounts(self):
            # 搜索校园公众号
            response = self.client.get(reverse('webspider:campus-public-accounts'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(len(response.data) > 0)
            print("Campus Accounts:")
            for account in response.data:
                print(f"- {account['name']} ({account['fakeid']})")

        def test_04_article_detail(self):
            # 搜索文章详情
            article_id = Article.objects.first().id
            response = self.client.get(reverse('webspider:article-detail', kwargs={'pk': article_id}))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['id'], article_id)
            # 非法文章id
            response = self.client.get(reverse('webspider:article-detail', kwargs={'pk': 999999}))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        print("Test 01: Search New Accounts")
        test_01_search_new_accounts(self)
        print("Test 02: Search Existing Accounts")
        test_02_search_accounts(self)
        print("Test 03: Campus Accounts")
        test_03_campus_accounts(self)
        print("Test 04: Article Detail")
        test_04_article_detail(self)
