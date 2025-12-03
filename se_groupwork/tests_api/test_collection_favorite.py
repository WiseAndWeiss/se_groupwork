from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User, Collection, Favorite
from webspider.models import Article, PublicAccount
from django.utils import timezone


class FavoriteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
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
        
        self.article2 = Article.objects.create(
            public_account=self.public_account,
            title='测试文章标题2',
            content='测试文章内容2',
            article_url='http://example.com/article/2',
            publish_time=timezone.now()
        )
        
        # 创建收藏夹
        self.default_collection, created = Collection.objects.get_or_create(
            user=self.user,
            name="默认收藏夹",
            is_default=True,
            order=0,
            defaults={'description': '默认收藏夹'}
        )
        
        self.test_collection = Collection.objects.create(
            user=self.user,
            name="测试收藏夹",
            is_default=False,
            order=1
        )
        
        # 创建测试收藏
        self.favorite = Favorite.objects.create(
            user=self.user,
            collection=self.default_collection,
            article=self.article
        )

    def test_create_favorite(self):
        """测试创建收藏"""
        url = reverse('user:favorite-list')
        data = {'article_id': self.article2.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favorite.objects.count(), 2)

    def test_create_favorite_with_specific_collection(self):
        """测试创建收藏并指定收藏夹"""
        url = reverse('user:favorite-list')
        data = {
            'article_id': self.article2.id,
            'collection_id': self.test_collection.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证收藏确实在指定的收藏夹中
        favorite = Favorite.objects.get(article=self.article2)
        self.assertEqual(favorite.collection.id, self.test_collection.id)

    def test_create_duplicate_favorite(self):
        """测试重复收藏"""
        url = reverse('user:favorite-list')
        data = {'article_id': self.article.id}  # 已经收藏过的文章
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_favorites(self):
        """测试获取收藏列表"""
        url = reverse('user:favorite-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 应该返回1个收藏

    def test_clear_favorites(self):
        """测试清空收藏"""
        # 先添加另一个收藏
        Favorite.objects.create(
            user=self.user,
            collection=self.default_collection,
            article=self.article2
        )
        
        self.assertEqual(Favorite.objects.count(), 2)
        
        url = reverse('user:favorite-list')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_delete_single_favorite(self):
        """测试删除单个收藏"""
        url = reverse('user:favorite-detail', kwargs={'pk': self.favorite.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_move_favorite(self):
        """测试移动收藏到其他收藏夹"""
        url = reverse('user:favorite-move', kwargs={'pk': self.favorite.id})
        data = {'collection_id': self.test_collection.id}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证收藏已移动
        self.favorite.refresh_from_db()
        self.assertEqual(self.favorite.collection.id, self.test_collection.id)
        
        # 验证原收藏夹计数更新
        self.default_collection.refresh_from_db()
        self.test_collection.refresh_from_db()
        self.assertEqual(self.default_collection.favorite_count, 0)
        self.assertEqual(self.test_collection.favorite_count, 1)

    def test_move_favorite_invalid_collection(self):
        """测试移动到不存在的收藏夹"""
        url = reverse('user:favorite-move', kwargs={'pk': self.favorite.id})
        data = {'collection_id': 999}  # 不存在的收藏夹ID
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_favorites(self):
        """测试搜索收藏"""
        # 先添加一些测试收藏
        Favorite.objects.create(
            user=self.user,
            collection=self.default_collection,
            article=self.article2
        )
        
        # 搜索包含"标题"的文章
        url = reverse('user:favorite-search')
        response = self.client.get(url, {'title': '标题'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 两篇文章标题都包含"标题"

    def test_search_favorites_empty_query(self):
        """测试空搜索查询（应该返回所有收藏）"""
        url = reverse('user:favorite-search')
        response = self.client.get(url, {'title': ''})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 返回所有收藏

    def test_favorite_count_updates(self):
        """测试收藏计数更新"""
        # 初始计数
        initial_user_count = self.user.favorite_count
        initial_collection_count = self.default_collection.favorite_count
        
        # 创建新收藏
        url = reverse('user:favorite-list')
        data = {'article_id': self.article2.id}
        response = self.client.post(url, data, format='json')
        
        # 验证用户和收藏夹计数更新
        self.user.refresh_from_db()
        self.default_collection.refresh_from_db()
        self.assertEqual(self.user.favorite_count, initial_user_count + 1)
        self.assertEqual(self.default_collection.favorite_count, initial_collection_count + 1)
        
        # 删除收藏
        new_favorite_id = response.data['id']
        url = reverse('user:favorite-detail', kwargs={'pk': new_favorite_id})
        self.client.delete(url)
        
        # 验证计数恢复
        self.user.refresh_from_db()
        self.default_collection.refresh_from_db()
        self.assertEqual(self.user.favorite_count, initial_user_count)
        self.assertEqual(self.default_collection.favorite_count, initial_collection_count)

    def test_favorite_ordering(self):
        """测试收藏按时间排序（最新的在前）"""
        # 创建较新的收藏
        new_favorite = Favorite.objects.create(
            user=self.user,
            collection=self.default_collection,
            article=self.article2
        )
        
        url = reverse('user:favorite-list')
        response = self.client.get(url)
        
        # 验证按时间倒序排列
        favorites = response.data
        self.assertEqual(len(favorites), 2)
        # 新创建的收藏应该在第一个
        self.assertEqual(favorites[0]['id'], new_favorite.id)


class FavoriteSignalTests(TestCase):
    """测试与Favorite相关的信号"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
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
        
        self.collection = Collection.objects.create(
            user=self.user,
            name="测试收藏夹",
            is_default=True,
            order=0,
        )
    
    def test_favorite_count_on_creation(self):
        """测试创建收藏时计数更新"""
        initial_user_count = self.user.favorite_count
        initial_collection_count = self.collection.favorite_count
        
        # 创建收藏
        favorite = Favorite.objects.create(
            user=self.user,
            collection=self.collection,
            article=self.article
        )
        
        # 验证计数已更新
        self.user.refresh_from_db()
        self.collection.refresh_from_db()
        self.assertEqual(self.user.favorite_count, initial_user_count + 1)
        self.assertEqual(self.collection.favorite_count, initial_collection_count + 1)
    
    def test_favorite_count_on_deletion(self):
        """测试删除收藏时计数更新"""
        # 先创建收藏
        favorite = Favorite.objects.create(
            user=self.user,
            collection=self.collection,
            article=self.article
        )
        
        # 获取删除前的计数
        self.user.refresh_from_db()
        self.collection.refresh_from_db()
        count_before_delete_user = self.user.favorite_count
        count_before_delete_collection = self.collection.favorite_count
        
        # 删除收藏
        favorite.delete()
        
        # 验证计数已更新
        self.user.refresh_from_db()
        self.collection.refresh_from_db()
        self.assertEqual(self.user.favorite_count, count_before_delete_user - 1)
        self.assertEqual(self.collection.favorite_count, count_before_delete_collection - 1)