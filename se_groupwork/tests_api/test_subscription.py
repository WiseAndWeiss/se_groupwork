from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User

class SubscriptionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        
        # 创建测试公众号 - 根据实际模型定义修改
        from webspider.models import PublicAccount
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_fakeid_123',
        )

    def test_create_subscription(self):
        """测试创建订阅"""
        url = reverse('user:subscription-list')
        data = {'public_account_id': self.public_account.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_duplicate_subscription(self):
        """测试重复订阅"""
        url = reverse('user:subscription-list')
        data = {'public_account_id': self.public_account.id}
        
        # 第一次订阅
        self.client.post(url, data, format='json')
        # 第二次订阅
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_subscriptions(self):
        """测试获取订阅列表"""
        url = reverse('user:subscription-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_subscription(self):
        """测试删除订阅"""
        # 先创建订阅
        from user.models import Subscription
        subscription = Subscription.objects.create(
            user=self.user, 
            public_account=self.public_account
        )
        
        url = reverse('user:subscription-detail', kwargs={'pk': subscription.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)