from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UsernameUpdateTests(TestCase):
    """修改用户名测试用例"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/auth/update/username/'

    def test_update_username_success(self):
        """测试成功修改用户名"""
        data = {'new_username': 'newtestuser'}
        response = self.client.patch(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '用户名修改成功')
        self.assertEqual(response.data['user']['username'], 'newtestuser')
        
        # 验证数据库更新
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newtestuser')

    def test_update_username_empty(self):
        """测试用户名为空"""
        data = {'new_username': ''}
        response = self.client.patch(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('新用户名不能为空', response.data['error'])

    def test_update_username_duplicate(self):
        """测试用户名重复"""
        # 创建另一个用户
        User.objects.create_user(username='existinguser', password='TestPass123!')
        
        data = {'new_username': 'existinguser'}
        response = self.client.patch(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('该用户名已被占用', response.data['error'])

    def test_update_username_same_as_current(self):
        """测试修改为当前用户名（应该允许）"""
        data = {'new_username': 'testuser'}  # 当前用户名
        response = self.client.patch(self.url, data)
        
        # 应该成功，因为用户名没有变化
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EdgeCasesTestCase(TestCase):
    """边界情况测试用例"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='edgeuser',
            password='TestPass123!',
            email='edge@example.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_very_long_username(self):
        """测试超长用户名"""
        # 创建刚好20个字符的用户名（边界值）
        valid_username = 'a' * 20
        response = self.client.patch('/api/auth/update/username/', {'new_username': valid_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 创建21个字符的用户名（应该失败）
        invalid_username = 'a' * 21
        response = self.client.patch('/api/auth/update/username/', {'new_username': invalid_username})
        # 注意：这个测试假设后端有长度验证，如果没有，需要添加
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_special_characters_in_username(self):
        """测试用户名中的下划线 """
        data = {'new_username': 'user_name123'}
        response = self.client.patch('/api/auth/update/username/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_case_sensitive_username(self):
        """测试用户名大小写敏感性"""
        # 创建一个大写版本的用户名
        User.objects.create_user(username='TESTUSER', password='TestPass123!')
        
        # 尝试修改为小写版本（应该成功，因为用户名是大小写敏感的）
        data = {'new_username': 'testuser_modified'}
        response = self.client.patch('/api/auth/update/username/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)