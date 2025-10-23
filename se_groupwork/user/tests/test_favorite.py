# user/tests/test_favorite.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from user.models import Favorite, User
from webspider.models import Article, PublicAccount

User = get_user_model()

class FavoriteTestCase(TestCase):
    """收藏功能测试用例"""
    
    def setUp(self):
        """测试前置设置"""
        self.user = User.objects.create_user(
            username='favoriteuser',
            email='favorite@example.com',
            password='testpass123'
        )
        
        # 创建公众号和文章
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_fakeid',
            icon_url='http://example.com/icon.jpg'
        )
        
        self.article1 = Article.objects.create(
            title='测试文章1',
            content='测试内容1',
            public_account=self.public_account,
            article_url='http://example.com/article1',  # 添加唯一的URL
            publish_time=timezone.now()
        )
        
        self.article2 = Article.objects.create(
            title='测试文章2',
            content='测试内容2',
            public_account=self.public_account,
            article_url='http://example.com/article2',  # 添加唯一的URL
            publish_time=timezone.now()
        )
    
    def test_create_favorite(self):
        """测试创建收藏"""
        favorite = Favorite.objects.create(
            user=self.user,
            article=self.article1,
        )
        
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.article, self.article1)
        self.assertIsNotNone(favorite.favorited_at)
    
    def test_duplicate_favorite_prevention(self):
        """测试防止重复收藏"""
        Favorite.objects.create(user=self.user, article=self.article1)
        
        # 验证唯一约束
        with self.assertRaises(Exception):
            Favorite.objects.create(user=self.user, article=self.article1)
    
    # ... 其他测试方法保持不变 ...


class FavoriteManagerTestCase(TestCase):
    """收藏管理器测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='manageruser',
            email='manager@example.com',
            password='testpass123'
        )
        
        self.public_account = PublicAccount.objects.create(name='测试号', fakeid='test')
        self.article = Article.objects.create(
            title='管理测试文章',
            content='测试内容',
            public_account=self.public_account,
            article_url='http://example.com/manager_article',  # 添加唯一的URL
            publish_time=timezone.now()
        )
    
    # ... 测试方法保持不变 ...


class FavoriteIntegrationTestCase(TestCase):
    """收藏功能集成测试"""
    
    def test_complete_favorite_workflow(self):
        """测试完整的收藏工作流"""
        user = User.objects.create_user(
            username='workflowuser',
            email='workflow@example.com',
            password='testpass123'
        )
        
        # 创建多篇文章
        public_account = PublicAccount.objects.create(name='集成测试号', fakeid='integrate')
        articles = []
        for i in range(1, 4):
            article = Article.objects.create(
                title=f'集成测试文章{i}',
                content=f'内容{i}',
                public_account=public_account,
                article_url=f'http://example.com/integration_article{i}',  # 添加唯一的URL
                publish_time=timezone.now()
            )
            articles.append(article)
        
        # 用户收藏多篇文章
        for article in articles:
            Favorite.objects.create(user=user, article=article)
        
        # 验证收藏数量
        self.assertEqual(user.favorite_set.count(), 3)
        user.refresh_from_db()
        self.assertEqual(user.favorite_count, 3)
        
        # 取消一个收藏
        favorite_to_remove = user.favorite_set.first()
        favorite_to_remove.delete()
        
        # 验证收藏数量减少
        self.assertEqual(user.favorite_set.count(), 2)
        user.refresh_from_db()
        self.assertEqual(user.favorite_count, 2)