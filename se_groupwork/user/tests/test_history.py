import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from webspider.models import Article, PublicAccount
from django.utils import timezone
from user.models import History, User

User = get_user_model()


class HistoryModelTest(TestCase):
    """History模型基础测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123', 
            email='test@example.com'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', 
            password='testpass123', 
            email='other@example.com'
        )
        
        # 创建测试公众号和文章
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_account'
        )
        self.article = Article.objects.create(
            title='测试文章',
            content='测试内容',
            publish_time=timezone.now(),
            article_url='http://example.com/article1',  # 添加唯一的URL
            public_account=self.public_account
        )
        time.sleep(0.1)
        self.article2 = Article.objects.create(
            title='测试文章2',
            content='测试内容2',
            publish_time=timezone.now(),
            article_url='http://example.com/article2',  # 添加唯一的URL
            public_account=self.public_account
        )

    def test_history_creation(self):
        """测试历史记录创建"""
        history = History.objects.create_history(self.user, self.article)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.article, self.article)
        self.assertIsNotNone(history.viewed_at)

    def test_history_str_representation(self):
        """测试字符串表示"""
        history = History.objects.create_history(self.user, self.article)
        expected_str = f"{self.user} viewed {self.article}"
        self.assertEqual(str(history), expected_str)

    def test_history_ordering(self):
        """测试历史记录排序"""
        # 创建多个历史记录
        history1 = History.objects.create_history(self.user, self.article)
        history2 = History.objects.create_history(self.user, self.article2)
        
        histories = History.objects.all()
        self.assertEqual(histories[0], history2)  # 最新创建的应该在前面
        self.assertEqual(histories[1], history1)

    def test_unique_constraint(self):
        """测试同一用户对同一文章可以创建多条记录（无唯一约束）"""
        history1 = History.objects.create_history(self.user, self.article)
        history2 = History.objects.create_history(self.user, self.article)
        
        # 应该能创建两条记录
        self.assertEqual(History.objects.filter(user=self.user, article=self.article).count(), 2)
        self.assertNotEqual(history1.id, history2.id)


class HistoryManagerTest(TestCase):
    """History管理器方法测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123', 
            email='test@example.com'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', 
            password='testpass123', 
            email='other@example.com'
        )
        
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_account'
        )
        self.article = Article.objects.create(
            title='测试文章',
            content='测试内容',
            public_account=self.public_account,
            publish_time=timezone.now(),
            article_url='http://example.com/article1',  # 添加唯一的URL
        )
        time.sleep(0.01)
        self.article2 = Article.objects.create(
            title='测试文章2',
            content='测试内容2',
            publish_time=timezone.now(),
            article_url='http://example.com/article2',  # 添加唯一的URL
            public_account=self.public_account
        )

    def test_get_user_history(self):
        """测试获取用户历史记录"""
        # 创建测试数据
        history1 = History.objects.create_history(self.user, self.article)
        history2 = History.objects.create_history(self.user, self.article2)
        History.objects.create_history(self.other_user, self.article)
        
        user_histories = History.objects.get_user_history(self.user)
        
        self.assertEqual(user_histories.count(), 2)
        self.assertIn(history1, user_histories)
        self.assertIn(history2, user_histories)

    def test_is_viewed(self):
        """测试检查用户是否浏览过文章"""
        # 用户未浏览过
        self.assertFalse(History.objects.is_viewed(self.user, self.article))
        
        # 用户浏览过
        History.objects.create_history(self.user, self.article)
        self.assertTrue(History.objects.is_viewed(self.user, self.article))
        
        # 其他用户浏览过，但当前用户未浏览
        self.assertFalse(History.objects.is_viewed(self.other_user, self.article))

    def test_create_history(self):
        """测试创建历史记录"""
        history = History.objects.create_history(self.user, self.article)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.article, self.article)
        self.assertTrue(History.objects.filter(user=self.user, article=self.article).exists())

    def test_clear_user_history(self):
        """测试清除用户历史记录"""
        # 创建多条记录
        History.objects.create_history(self.user, self.article)
        History.objects.create_history(self.user, self.article2)
        History.objects.create_history(self.other_user, self.article)
        
        # 清除指定用户的历史记录
        History.objects.clear_user_history(self.user)
        
        self.assertEqual(History.objects.filter(user=self.user).count(), 0)
        self.assertEqual(History.objects.filter(user=self.other_user).count(), 1)

    def test_delete_history(self):
        """测试删除单条历史记录"""
        history = History.objects.create_history(self.user, self.article)
        History.objects.create_history(self.user, self.article2)
        
        # 删除单条记录
        History.objects.delete_history(history)
        
        self.assertFalse(History.objects.filter(id=history.id).exists())
        self.assertTrue(History.objects.filter(user=self.user, article=self.article2).exists())

    def test_history_capped_at_max_records(self):
        """历史记录应限制为最新N条"""
        max_records = getattr(settings, 'HISTORY_MAX_RECORDS', 100)
        articles = []
        for i in range(max_records + 5):
            time.sleep(0.001)
            article = Article.objects.create(
                title=f'测试文章cap{i}',
                content=f'内容cap{i}',
                public_account=self.public_account,
                publish_time=timezone.now(),
                article_url=f'http://example.com/article-cap-{i}',
            )
            articles.append(article)
            History.objects.create_history(self.user, article)

        histories = History.objects.filter(user=self.user)
        self.assertEqual(histories.count(), max_records)
        # 最早的几条应被清理
        self.assertFalse(History.objects.filter(user=self.user, article=articles[0]).exists())
        self.assertTrue(History.objects.filter(user=self.user, article=articles[-1]).exists())


class HistoryRelationshipTest(TestCase):
    """历史记录关联关系测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123', 
            email='test@example.com'
        )
        
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_account'
        )
        self.article = Article.objects.create(
            title='测试文章',
            content='测试内容',
            publish_time=timezone.now(),
            article_url='http://example.com/article1',  # 添加唯一的URL
            public_account=self.public_account
        )

    def test_user_deletion_cascades(self):
        """测试用户删除时级联删除历史记录"""
        History.objects.create_history(self.user, self.article)
        
        # 删除用户
        self.user.delete()
        
        # 历史记录应该被级联删除
        self.assertEqual(History.objects.count(), 0)

    def test_article_deletion_cascades(self):
        """测试文章删除时级联删除历史记录"""
        History.objects.create_history(self.user, self.article)
        
        # 删除文章
        self.article.delete()
        
        # 历史记录应该被级联删除
        self.assertEqual(History.objects.count(), 0)


class HistoryEdgeCasesTest(TestCase):
    """边界情况测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123', 
            email='test@example.com'
        )
        
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_account'
        )
        self.article = Article.objects.create(
            title='测试文章',
            content='测试内容',
            publish_time=timezone.now(),
            article_url='http://example.com/article1',  # 添加唯一的URL
            public_account=self.public_account
        )

    def test_multiple_views_same_article(self):
        """测试同一用户多次浏览同一文章"""
        for i in range(5):
            History.objects.create_history(self.user, self.article)
        
        histories = History.objects.filter(user=self.user, article=self.article)
        self.assertEqual(histories.count(), 5)
        
        # 验证时间顺序（最新的在前面）
        viewed_times = [h.viewed_at for h in histories]
        self.assertEqual(viewed_times, sorted(viewed_times, reverse=True))

    def test_empty_user_history(self):
        """测试空用户历史记录"""
        histories = History.objects.get_user_history(self.user)
        self.assertEqual(histories.count(), 0)


class HistoryIntegrationTest(TestCase):
    """集成测试：与其他模型交互"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123', 
            email='test@example.com'
        )
        
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_account'
        )
        self.article = Article.objects.create(
            title='测试文章',
            content='测试内容',
            publish_time=timezone.now(),
            article_url='http://example.com/article1',  # 添加唯一的URL
            public_account=self.public_account
        )

    def test_history_with_user_statistics(self):
        """测试历史记录与用户统计信息的集成"""
        # 初始计数为0
        self.assertEqual(self.user.history_count, 0)
        
        # 创建历史记录（注意：这里不会自动更新history_count，需要手动更新或使用信号）
        History.objects.create_history(self.user, self.article)
        
        # 手动更新用户统计（实际项目中可能需要信号或重写save方法）
        self.user.history_count = History.objects.filter(user=self.user).count()
        self.user.save()
        
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.history_count, 1)

    def test_bulk_operations(self):
        """测试批量操作"""
        # 批量创建历史记录
        articles = []
        for i in range(10):
            time.sleep(0.01)
            article = Article.objects.create(
                title=f'测试文章{i}',
                content=f'内容{i}',
                public_account=self.public_account,
                publish_time=timezone.now(),
                article_url=f'http://example.com/article10{i}',  # 添加唯一的URL
            )
            articles.append(article)
        
        # 批量创建历史记录
        for article in articles:
            History.objects.create_history(self.user, article)
        
        self.assertEqual(History.objects.filter(user=self.user).count(), 10)
        
        # 批量删除
        History.objects.filter(user=self.user).delete()
        self.assertEqual(History.objects.filter(user=self.user).count(), 0)