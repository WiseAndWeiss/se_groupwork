from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User
from django.utils import timezone

class FavoriteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        
        # 创建测试公众号和文章 - 根据实际模型定义修改
        from webspider.models import Article, PublicAccount
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_fakeid_123',
            icon_url='http://example.com/icon.jpg'
        )
        
        self.article = Article.objects.create(
            public_account=self.public_account,
            title='测试文章标题',
            content='测试文章内容',
            article_url='http://example.com/article/1',
            publish_time=timezone.now()
        )

    def test_create_favorite(self):
        """测试创建收藏"""
        url = reverse('favorite-list')
        data = {'article_id': self.article.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_favorites(self):
        """测试获取收藏列表"""
        url = reverse('favorite-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_clear_favorites(self):
        """测试清空收藏"""
        url = reverse('favorite-list')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_duplicate_favorite(self):
        """测试重复收藏"""
        url = reverse('favorite-list')
        data = {'article_id': self.article.id}
        
        # 第一次收藏
        self.client.post(url, data, format='json')
        # 第二次收藏
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)