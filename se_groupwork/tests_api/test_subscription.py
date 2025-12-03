from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User
from webspider.models import PublicAccount
from user.models import Subscription

class SubscriptionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
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
        
        subscription = Subscription.objects.create(
            user=self.user, 
            public_account=self.public_account
        )
        
        url = reverse('user:subscription-detail', kwargs={'pk': subscription.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SubscriptionSortTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='Testpass123')
        self.client.force_authenticate(user=self.user)
        
        # 创建测试公众号
        self.public_account1 = PublicAccount.objects.create(
            name='测试公众号1',
            fakeid='test_fakeid_1',
        )
        self.public_account2 = PublicAccount.objects.create(
            name='测试公众号2',
            fakeid='test_fakeid_2',
        )
        self.public_account3 = PublicAccount.objects.create(
            name='测试公众号3',
            fakeid='test_fakeid_3',
        )
        
        # 创建测试订阅
        self.subscription1 = Subscription.objects.create(
            user=self.user, 
            public_account=self.public_account1,
            order=1
        )
        self.subscription2 = Subscription.objects.create(
            user=self.user, 
            public_account=self.public_account2,
            order=2
        )
        self.subscription3 = Subscription.objects.create(
            user=self.user, 
            public_account=self.public_account3,
            order=3
        )

    def test_sort_subscriptions_success(self):
        """测试成功排序订阅"""
        url = reverse('user:subscription-sort')  
        data = {
            'orders': [
                {'subscription_id': self.subscription2.id, 'order': 1},
                {'subscription_id': self.subscription1.id, 'order': 2},
                {'subscription_id': self.subscription3.id, 'order': 3}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '订阅排序更新成功')
        
        # 验证排序是否正确更新
        self.subscription1.refresh_from_db()
        self.subscription2.refresh_from_db()
        self.subscription3.refresh_from_db()
        
        self.assertEqual(self.subscription1.order, 2)
        self.assertEqual(self.subscription2.order, 1)
        self.assertEqual(self.subscription3.order, 3)

    def test_sort_subscriptions_empty_orders(self):
        """测试空排序列表"""
        url = reverse('user:subscription-sort')
        data = {'orders': []}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'orders 不能为空')

    def test_sort_subscriptions_invalid_format(self):
        """测试无效的数据格式"""
        url = reverse('user:subscription-sort')
        data = {'orders': 'invalid_format'}  # 应该是列表，不是字符串
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'orders 必须是数组格式')

    def test_sort_subscriptions_invalid_subscription_id(self):
        """测试无效的订阅ID"""
        url = reverse('user:subscription-sort')
        data = {
            'orders': [
                {'subscription_id': 9999, 'order': 1},  # 不存在的订阅ID
                {'subscription_id': self.subscription1.id, 'order': 2}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('以下订阅ID不存在或不属于当前用户', response.data['error'])

    def test_sort_other_user_subscription(self):
        """测试排序其他用户的订阅（应该失败）"""
        # 创建另一个用户和他的订阅
        other_user = User.objects.create_user(username='otheruser', password='otherpass123')
        other_subscription = Subscription.objects.create(
            user=other_user, 
            public_account=self.public_account1,
            order=1
        )
        
        url = reverse('user:subscription-sort')
        data = {
            'orders': [
                {'subscription_id': other_subscription.id, 'order': 1},  # 其他用户的订阅
                {'subscription_id': self.subscription1.id, 'order': 2}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_sort_subscriptions_partial_update(self):
        """测试部分订阅排序（不传入所有订阅）"""
        url = reverse('user:subscription-sort')
        data = {
            'orders': [
                {'subscription_id': self.subscription3.id, 'order': 1},  # 只更新第三个订阅
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证只有第三个订阅的排序被更新
        self.subscription1.refresh_from_db()
        self.subscription2.refresh_from_db()
        self.subscription3.refresh_from_db()
        
        self.assertEqual(self.subscription1.order, 1)  # 保持不变
        self.assertEqual(self.subscription2.order, 2)  # 保持不变
        self.assertEqual(self.subscription3.order, 1)  # 更新为1

    def test_sort_subscriptions_duplicate_order_values(self):
        """测试重复的排序值（应该允许）"""
        url = reverse('user:subscription-sort')
        data = {
            'orders': [
                {'subscription_id': self.subscription1.id, 'order': 1},
                {'subscription_id': self.subscription2.id, 'order': 1},  # 相同的排序值
                {'subscription_id': self.subscription3.id, 'order': 2}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证排序值已更新
        self.subscription1.refresh_from_db()
        self.subscription2.refresh_from_db()
        self.subscription3.refresh_from_db()
        
        self.assertEqual(self.subscription1.order, 1)
        self.assertEqual(self.subscription2.order, 1)
        self.assertEqual(self.subscription3.order, 2)

    def test_sort_subscriptions_negative_order(self):
        """测试负数的排序值（应该失败）"""
        url = reverse('user:subscription-sort')
        data = {
            'orders': [
                {'subscription_id': self.subscription1.id, 'order': -1},  # 负数
                {'subscription_id': self.subscription2.id, 'order': 2}
            ]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def test_sort_subscriptions_unauthorized(self):
        """测试未认证用户访问"""
        self.client.logout()  # 登出用户
        
        url = reverse('user:subscription-sort')
        data = {
            'orders': [
                {'subscription_id': self.subscription1.id, 'order': 1}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_subscriptions_after_sort(self):
        """测试排序后获取订阅列表的顺序"""
        # 先排序
        url_sort = reverse('user:subscription-sort')
        sort_data = {
            'orders': [
                {'subscription_id': self.subscription3.id, 'order': 1},
                {'subscription_id': self.subscription1.id, 'order': 2},
                {'subscription_id': self.subscription2.id, 'order': 3}
            ]
        }
        self.client.post(url_sort, sort_data, format='json')
        
        # 然后获取订阅列表
        url_list = reverse('user:subscription-list')
        response = self.client.get(url_list)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证返回的顺序是否正确
        subscriptions = response.data
        self.assertEqual(len(subscriptions), 3)
        self.assertEqual(subscriptions[0]['id'], self.subscription3.id)  # 排序第一
        self.assertEqual(subscriptions[1]['id'], self.subscription1.id)  # 排序第二
        self.assertEqual(subscriptions[2]['id'], self.subscription2.id)  # 排序第三