from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from webspider.models import PublicAccount
from user.models import Subscription

User = get_user_model()

# Create your tests here.
class SubscriptionTestCase(TestCase):
    """订阅功能测试用例"""

    def setUp(self):
        """测试前置设置"""
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        # 创建测试公众号
        self.account1 = PublicAccount.objects.create(
            name='测试公众号1',
            fakeid='fakeid123',
            icon_url='http://example.com/icon1.jpg'
        )
        self.account2 = PublicAccount.objects.create(
            name='测试公众号2',
            fakeid='fakeid456',
            icon_url='http://example.com/icon2.jpg'
        )
        self.account3 = PublicAccount.objects.create(
            name='测试公众号3',
            fakeid='fakeid789',
            icon_url='http://example.com/icon3.jpg'
        )

    def test_create_subscription(self):
        """测试创建订阅关系"""
        # 用户1订阅公众号1
        subscription = Subscription.objects.create(
            user=self.user1,
            public_account=self.account1
        )

        # 验证订阅关系
        self.assertEqual(subscription.user, self.user1)
        self.assertEqual(subscription.public_account, self.account1)
        self.assertTrue(subscription.is_active)
        self.assertIsNotNone(subscription.subscribe_at)

        # 验证唯一约束
        with self.assertRaises(Exception):  # 具体异常类型取决于数据库
            Subscription.objects.create(
                user=self.user1,
                public_account=self.account1
            )

    def test_user_subscription_relationships(self):
        """测试用户与订阅的关系"""
        # 创建多个订阅
        Subscription.objects.create(user=self.user1, public_account=self.account1)
        Subscription.objects.create(user=self.user1, public_account=self.account2)
        Subscription.objects.create(user=self.user2, public_account=self.account1)

        # 测试正向查询：用户订阅的公众号
        user1_subscriptions = self.user1.subscription_set.all()
        self.assertEqual(user1_subscriptions.count(), 2)
        self.assertIn(self.account1, [sub.public_account for sub in user1_subscriptions])

        # 测试反向查询：公众号被哪些用户订阅
        account1_subscribers = self.account1.subscription_set.all()
        self.assertEqual(account1_subscribers.count(), 2)

    def test_subscription_activation(self):
        """测试订阅激活/取消功能"""
        subscription = Subscription.objects.create(
            user=self.user1,
            public_account=self.account1
        )

        # 取消订阅
        subscription.is_active = False
        subscription.save()

        # 验证取消订阅
        updated_subscription = Subscription.objects.get(
            user=self.user1,
            public_account=self.account1
        )
        self.assertFalse(updated_subscription.is_active)

        # 重新激活订阅
        subscription.is_active = True
        subscription.save()
        self.assertTrue(subscription.is_active)

    def test_cascade_deletion(self):
        """测试级联删除"""
        # 创建订阅关系
        Subscription.objects.create(user=self.user1, public_account=self.account1)

        # 删除用户，订阅关系应该被级联删除
        user_id = self.user1.id
        self.user1.delete()

        # 验证订阅关系也被删除
        with self.assertRaises(Subscription.DoesNotExist):
            Subscription.objects.get(user_id=user_id, public_account=self.account1)

        # 重新创建用户和订阅
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        Subscription.objects.create(user=new_user, public_account=self.account2)

        # 删除公众号，订阅关系应该被级联删除
        account_id = self.account2.id
        self.account2.delete()

        with self.assertRaises(Subscription.DoesNotExist):
            Subscription.objects.get(user=new_user, public_account_id=account_id)

    def test_subscription_ordering(self):
        """测试订阅时间排序"""
        # 创建不同时间的订阅
        subscription1 = Subscription.objects.create(user=self.user1, public_account=self.account1)

        # 模拟时间间隔
        subscription1.subscribe_at = timezone.now() - timezone.timedelta(hours=1)
        subscription1.save()

        subscription2 = Subscription.objects.create(user=self.user1, public_account=self.account2)

        # 获取用户的订阅，应该按订阅时间排序（后订阅的在前）
        subscriptions = Subscription.objects.filter(user=self.user1)
        self.assertEqual(subscriptions.first(), subscription2)
        self.assertEqual(subscriptions.last(), subscription1)

    def test_subscription_str_representation(self):
        """测试订阅对象的字符串表示"""
        subscription = Subscription.objects.create(
            user=self.user1,
            public_account=self.account1
        )

        expected_str = f"{self.user1} -> {self.account1}"
        self.assertEqual(str(subscription), expected_str)

        # 测试非活跃状态的显示
        subscription.is_active = False
        subscription.save()
        expected_str_inactive = f"{self.user1} -> {self.account1}"
        self.assertEqual(str(subscription), expected_str_inactive)


class SubscriptionManagerTestCase(TestCase):
    """订阅管理器相关测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='manageruser',
            email='manager@example.com',
            password='testpass123'
        )
        self.account = PublicAccount.objects.create(
            name='管理测试公众号',
            fakeid='manager_fakeid'
        )

    def test_active_subscriptions(self):
        """测试活跃订阅查询"""
        # 创建活跃和非活跃订阅
        active_sub = Subscription.objects.create(user=self.user, public_account=self.account)
        inactive_sub = Subscription.objects.create(
            user=self.user,
            public_account=PublicAccount.objects.create(name='其他公众号', fakeid='other'),
            is_active=False
        )

        # 查询活跃订阅
        active_subs = Subscription.objects.filter(is_active=True)
        self.assertEqual(active_subs.count(), 1)
        self.assertEqual(active_subs.first(), active_sub)


class SubscriptionIntegrationTestCase(TestCase):
    """订阅功能集成测试"""

    def test_complete_subscription_workflow(self):
        """测试完整的订阅工作流"""
        # 创建用户和公众号
        user = User.objects.create_user(
            username='workflowuser',
            email='workflow@example.com',
            password='testpass123'
        )

        accounts = [
            PublicAccount.objects.create(name=f'公众号{i}', fakeid=f'fakeid{i}')
            for i in range(1, 4)
        ]

        # 用户订阅多个公众号
        for account in accounts:
            Subscription.objects.create(user=user, public_account=account)

        # 验证订阅数量
        self.assertEqual(user.subscription_set.count(), 3)

        # 取消其中一个订阅
        subscription_to_cancel = user.subscription_set.first()
        subscription_to_cancel.is_active = False
        subscription_to_cancel.save()

        # 验证活跃订阅数量
        active_subscriptions = user.subscription_set.filter(is_active=True)
        self.assertEqual(active_subscriptions.count(), 2)

        # 重新激活订阅
        subscription_to_cancel.is_active = True
        subscription_to_cancel.save()
        self.assertEqual(user.subscription_set.filter(is_active=True).count(), 3)


class SubscriptionCountTestCase(TestCase):
    """用户订阅数目管理测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='countuser',
            email='count@example.com',
            password='testpass123'
        )
        self.accounts = [
            PublicAccount.objects.create(name=f'计数公众号{i}', fakeid=f'count_fakeid{i}')
            for i in range(1, 4)
        ]

    def test_subscription_count_on_create(self):
        """测试创建订阅时计数自动更新"""
        # 初始计数应为0
        self.assertEqual(self.user.subscription_count, 0)

        # 创建第一个订阅
        Subscription.objects.create(user=self.user, public_account=self.accounts[0])
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 1)

        # 创建第二个订阅
        Subscription.objects.create(user=self.user, public_account=self.accounts[1])
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 2)

    def test_subscription_count_on_delete(self):
        """测试删除订阅时计数自动更新"""
        # 先创建两个订阅
        sub1 = Subscription.objects.create(user=self.user, public_account=self.accounts[0])
        sub2 = Subscription.objects.create(user=self.user, public_account=self.accounts[1])
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 2)

        # 删除一个订阅
        sub1.delete()
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 1)

        # 删除另一个订阅
        sub2.delete()
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 0)

    def test_subscription_count_inactive_creation(self):
        """测试创建非活跃订阅时不增加计数"""
        # 创建非活跃订阅
        Subscription.objects.create(
            user=self.user,
            public_account=self.accounts[0],
            is_active=False
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 0)

    def test_subscription_count_activation_changes(self):
        """测试订阅激活状态变化对计数的影响"""
        # 创建非活跃订阅
        subscription = Subscription.objects.create(
            user=self.user,
            public_account=self.accounts[0],
            is_active=False
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 0)

        # 激活订阅（不影响订阅数目）
        subscription.is_active = True
        subscription.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 0)

        # 再次取消激活（不影响订阅数目）
        subscription.is_active = False
        subscription.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 0)

    def test_multiple_users_subscription_counts(self):
        """测试多个用户的订阅计数独立"""
        user2 = User.objects.create_user(
            username='countuser2',
            email='count2@example.com',
            password='testpass123'
        )

        # 用户1订阅2个公众号
        Subscription.objects.create(user=self.user, public_account=self.accounts[0])
        Subscription.objects.create(user=self.user, public_account=self.accounts[1])

        # 用户2订阅1个公众号
        Subscription.objects.create(user=user2, public_account=self.accounts[0])

        # 验证计数独立
        self.user.refresh_from_db()
        user2.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 2)
        self.assertEqual(user2.subscription_count, 1)

    def test_subscription_count_after_user_deletion(self):
        """测试用户删除后相关订阅计数清理"""
        user2 = User.objects.create_user(
            username='tobedeleted',
            email='delete@example.com',
            password='testpass123'
        )

        # 创建订阅
        Subscription.objects.create(user=user2, public_account=self.accounts[0])
        user2.refresh_from_db()
        self.assertEqual(user2.subscription_count, 1)

        # 删除用户（应该不影响其他用户的计数）
        user2.delete()
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_count, 0)  # 当前用户计数不变

    def test_subscription_count_consistency(self):
        """测试订阅计数与实际订阅数量的一致性"""
        # 创建多个订阅
        for account in self.accounts:
            Subscription.objects.create(user=self.user, public_account=account)

        self.user.refresh_from_db()

        # 验证计数与实际活跃订阅数量一致
        actual_count = Subscription.objects.filter(user=self.user, is_active=True).count()
        self.assertEqual(self.user.subscription_count, actual_count)
        self.assertEqual(self.user.subscription_count, 3)