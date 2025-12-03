from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User, Collection, Favorite
from webspider.models import Article, PublicAccount
from django.utils import timezone


class CollectionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='Testpass123')
        self.client.force_authenticate(user=self.user)
        
        # 创建测试数据
        self.public_account = PublicAccount.objects.create(
            name='测试公众号',
            fakeid='test_fakeid_123',
        )
        
        self.article = Article.objects.create(
            public_account=self.public_account,
            title='测试文章标题',
            content='测试文章内容',
            article_url='http://example.com/article/1',
            publish_time=timezone.now()
        )
        
        # 创建默认收藏夹（应该由信号自动创建）
        self.default_collection = Collection.objects.filter(user=self.user, is_default=True).first()
        if not self.default_collection:
            self.default_collection = Collection.objects.create(
                user=self.user,
                name="默认收藏夹",
                is_default=True,
                order=0
            )
        
        # 创建测试收藏夹
        self.test_collection = Collection.objects.create(
            user=self.user,
            name="测试收藏夹",
            description="测试描述",
            is_default=False,
            order=1
        )

    def test_create_collection(self):
        """测试创建收藏夹"""
        url = reverse('user:collection-list')
        data = {
            'name': '新建收藏夹',
            'description': '新建收藏夹描述'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects.count(), 3)  # 默认 + 测试 + 新建

    def test_create_duplicate_collection_name(self):
        """测试创建同名收藏夹"""
        url = reverse('user:collection-list')
        data = {
            'name': '测试收藏夹',  # 与已有收藏夹同名
            'description': '重复名称'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_collections(self):
        """测试获取收藏夹列表"""
        url = reverse('user:collection-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 默认收藏夹和测试收藏夹

    def test_get_collection_detail(self):
        """测试获取收藏夹详情（包含收藏内容）"""
        # 先添加一些收藏
        Favorite.objects.create(
            user=self.user,
            collection=self.test_collection,
            article=self.article
        )
        
        url = reverse('user:collection-detail', kwargs={'pk': self.test_collection.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 应该返回收藏夹中的收藏列表

    def test_update_collection(self):
        """测试更新收藏夹信息"""
        url = reverse('user:collection-detail', kwargs={'pk': self.test_collection.id})
        data = {
            'name': '更新后的收藏夹',
            'description': '更新后的描述'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证更新
        self.test_collection.refresh_from_db()
        self.assertEqual(self.test_collection.name, '更新后的收藏夹')
        self.assertEqual(self.test_collection.description, '更新后的描述')

    def test_delete_collection(self):
        """测试删除收藏夹"""
        url = reverse('user:collection-detail', kwargs={'pk': self.test_collection.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Collection.objects.filter(user=self.user).count(), 1)  # 只剩默认收藏夹

    def test_delete_default_collection(self):
        """测试删除默认收藏夹（应该失败）"""
        url = reverse('user:collection-detail', kwargs={'pk': self.default_collection.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 验证默认收藏夹仍然存在
        self.assertTrue(Collection.objects.filter(id=self.default_collection.id).exists())

    def test_collection_count_updates(self):
        """测试收藏夹计数更新"""
        # 初始计数
        initial_count = self.user.collection_count
        
        # 创建新收藏夹
        url = reverse('user:collection-list')
        data = {'name': '计数测试收藏夹'}
        response = self.client.post(url, data, format='json')
        
        # 验证用户收藏夹计数更新
        self.user.refresh_from_db()
        self.assertEqual(self.user.collection_count, initial_count + 1)
        
        # 删除收藏夹
        new_collection_id = response.data['id']
        url = reverse('user:collection-detail', kwargs={'pk': new_collection_id})
        self.client.delete(url)
        
        # 验证计数恢复
        self.user.refresh_from_db()
        self.assertEqual(self.user.collection_count, initial_count)

    def test_collection_ordering(self):
        """测试收藏夹排序"""
        # 创建多个收藏夹测试排序
        Collection.objects.create(user=self.user, name="收藏夹A", order=2)
        Collection.objects.create(user=self.user, name="收藏夹B", order=3)
        
        url = reverse('user:collection-list')
        response = self.client.get(url)
        
        # 验证按order字段排序
        collections = response.data
        orders = [coll['order'] for coll in collections]
        self.assertEqual(orders, sorted(orders))


class CollectionSignalTests(TestCase):
    """测试与Collection相关的信号"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
    
    def test_default_collection_creation_on_user_creation(self):
        """测试用户注册时自动创建默认收藏夹"""
        # 创建新用户，应该触发信号创建默认收藏夹
        new_user = User.objects.create_user(username='newuser', password='testpass123')
        
        # 验证默认收藏夹已创建
        default_collection = Collection.objects.filter(user=new_user, is_default=True).first()
        self.assertIsNotNone(default_collection)
        self.assertEqual(default_collection.name, "默认收藏夹")
        self.assertEqual(default_collection.order, 0)
        
        # 验证用户收藏夹计数已更新
        new_user.refresh_from_db()
        self.assertEqual(new_user.collection_count, 1)