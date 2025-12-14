from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User, Todo
from webspider.models import Article, PublicAccount
from django.utils import timezone
import datetime


class TodoTests(TestCase):
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
        
        # 创建测试待办事项
        self.todo_without_end = Todo.objects.create(
            user=self.user,
            title='无结束时间待办',
            note='这是一个测试待办',
            start_time=timezone.now() + datetime.timedelta(hours=1),
            remind=False
        )
        
        self.todo_with_end = Todo.objects.create(
            user=self.user,
            title='有结束时间待办',
            note='这是一个跨天待办',
            start_time=timezone.now() + datetime.timedelta(hours=2),
            end_time=timezone.now() + datetime.timedelta(days=1),
            remind=True,
            article=self.article
        )

    def test_create_todo(self):
        """测试创建待办事项"""
        url = reverse('user:todo-list')
        data = {
            'title': '新建待办',
            'note': '新建待办描述',
            'start_time': (timezone.now() + datetime.timedelta(hours=3)).isoformat(),
            'remind': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Todo.objects.count(), 3)
        self.assertEqual(response.data['title'], '新建待办')

    def test_create_todo_with_article(self):
        """测试创建带有关联文章的待办"""
        url = reverse('user:todo-list')
        data = {
            'title': '文章相关待办',
            'start_time': (timezone.now() + datetime.timedelta(hours=4)).isoformat(),
            'article': self.article.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['article'], self.article.id)

    def test_create_todo_invalid_time(self):
        """测试创建时间无效的待办（结束时间早于开始时间）"""
        url = reverse('user:todo-list')
        data = {
            'title': '无效时间待办',
            'start_time': (timezone.now() + datetime.timedelta(hours=5)).isoformat(),
            'end_time': (timezone.now() + datetime.timedelta(hours=4)).isoformat()  # 结束时间早于开始时间
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_todo_list(self):
        """测试获取待办列表"""
        url = reverse('user:todo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # 验证按开始时间和id排序
        titles = [todo['title'] for todo in response.data]
        self.assertEqual(titles, ['无结束时间待办', '有结束时间待办'])

    def test_get_todo_list_with_date_filter(self):
        """测试按日期筛选待办列表"""
        # 测试当天的待办
        today = timezone.now().date()
        url = reverse('user:todo-list') + f'?date={today}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 测试未来日期的待办（包含跨天任务）
        future_date = (timezone.now() + datetime.timedelta(days=1)).date()
        url = reverse('user:todo-list') + f'?date={future_date}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 应该包含跨天的待办事项
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], '有结束时间待办')

    def test_get_todo_list_invalid_date_format(self):
        """测试日期格式无效的情况"""
        url = reverse('user:todo-list') + '?date=2024-13-45'  # 无效日期
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_todo_detail(self):
        """测试获取单个待办详情"""
        url = reverse('user:todo-detail', kwargs={'pk': self.todo_without_end.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '无结束时间待办')
        self.assertEqual(response.data['note'], '这是一个测试待办')

    def test_update_todo_full(self):
        """测试全量更新待办事项"""
        url = reverse('user:todo-detail', kwargs={'pk': self.todo_without_end.id})
        new_time = timezone.now() + datetime.timedelta(hours=6)
        data = {
            'title': '更新后的待办',
            'note': '更新后的描述',
            'start_time': new_time.isoformat(),
            'remind': True
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证更新
        self.todo_without_end.refresh_from_db()
        self.assertEqual(self.todo_without_end.title, '更新后的待办')
        self.assertEqual(self.todo_without_end.note, '更新后的描述')
        self.assertTrue(self.todo_without_end.remind)

    def test_update_todo_partial(self):
        """测试部分更新待办事项"""
        url = reverse('user:todo-detail', kwargs={'pk': self.todo_without_end.id})
        data = {
            'title': '部分更新后的标题'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证部分更新
        self.todo_without_end.refresh_from_db()
        self.assertEqual(self.todo_without_end.title, '部分更新后的标题')
        # 其他字段应保持不变
        self.assertEqual(self.todo_without_end.note, '这是一个测试待办')

    def test_update_todo_invalid_data(self):
        """测试更新待办时数据无效的情况"""
        url = reverse('user:todo-detail', kwargs={'pk': self.todo_with_end.id})
        data = {
            'end_time': (timezone.now() - datetime.timedelta(days=1)).isoformat()  # 结束时间早于开始时间
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_todo(self):
        """测试删除待办事项"""
        initial_count = Todo.objects.count()
        url = reverse('user:todo-detail', kwargs={'pk': self.todo_without_end.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Todo.objects.count(), initial_count - 1)
        self.assertFalse(Todo.objects.filter(id=self.todo_without_end.id).exists())

    def test_get_nonexistent_todo(self):
        """测试获取不存在的待办"""
        url = reverse('user:todo-detail', kwargs={'pk': 9999})  # 不存在的ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_nonexistent_todo(self):
        """测试更新不存在的待办"""
        url = reverse('user:todo-detail', kwargs={'pk': 9999})
        data = {'title': '不存在的待办'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_todo(self):
        """测试删除不存在的待办"""
        url = reverse('user:todo-detail', kwargs={'pk': 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_todo_ordering(self):
        """测试待办事项排序"""
        # 创建更多待办事项测试排序
        todo_early = Todo.objects.create(
            user=self.user,
            title='最早的待办',
            start_time=timezone.now(),
        )
        
        todo_late = Todo.objects.create(
            user=self.user,
            title='最晚的待办',
            start_time=timezone.now() + datetime.timedelta(hours=50),
        )
        
        url = reverse('user:todo-list')
        response = self.client.get(url)
        
        # 验证按开始时间和id排序
        todos = response.data
        titles = [todo['title'] for todo in todos]
        expected_titles = ['最早的待办', '无结束时间待办', '有结束时间待办', '最晚的待办']
        self.assertEqual(titles, expected_titles)

    def test_todo_cross_day_filtering(self):
        """测试跨天待办事项的日期筛选"""
        # 先清空所有待办
        Todo.objects.filter(user=self.user).delete()
        
        # 使用简单的日期，避免时区问题
        today = timezone.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        day_after_tomorrow = today + datetime.timedelta(days=2)
        
        # 创建明确的datetime对象，使用当前时区
        start_time = timezone.make_aware(datetime.datetime.combine(
            today, datetime.time(10, 0)
        ))
        end_time = timezone.make_aware(datetime.datetime.combine(
            day_after_tomorrow, datetime.time(18, 0)
        ))
        
        todo = Todo.objects.create(
            user=self.user,
            title='跨天待办',
            start_time=start_time,
            end_time=end_time
        )
        
        # 测试今天应该包含这个待办
        url = reverse('user:todo-list') + f'?date={today}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 测试明天应该包含这个待办
        url = reverse('user:todo-list') + f'?date={tomorrow}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 测试后天应该包含这个待办
        url = reverse('user:todo-list') + f'?date={day_after_tomorrow}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 测试大后天不应该包含这个待办
        day_after_day_after_tomorrow = day_after_tomorrow + datetime.timedelta(days=1)
        url = reverse('user:todo-list') + f'?date={day_after_day_after_tomorrow}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class TodoPermissionTests(TestCase):
    """测试待办事项的权限控制"""
    
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        # user1创建待办
        self.client.force_authenticate(user=self.user1)
        self.todo = Todo.objects.create(
            user=self.user1,
            title='用户1的待办',
            start_time=timezone.now() + datetime.timedelta(hours=1)
        )
    
    def test_user_cannot_access_others_todo(self):
        """测试用户不能访问其他用户的待办"""
        # 切换到user2
        self.client.force_authenticate(user=self.user2)
        
        # 尝试获取user1的待办
        url = reverse('user:todo-detail', kwargs={'pk': self.todo.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # 尝试更新user1的待办
        data = {'title': '尝试修改'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # 尝试删除user1的待办
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_only_see_own_todos(self):
        """测试用户只能看到自己的待办列表"""
        # user2创建自己的待办
        self.client.force_authenticate(user=self.user2)
        Todo.objects.create(
            user=self.user2,
            title='用户2的待办',
            start_time=timezone.now() + datetime.timedelta(hours=1)
        )
        
        url = reverse('user:todo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], '用户2的待办')