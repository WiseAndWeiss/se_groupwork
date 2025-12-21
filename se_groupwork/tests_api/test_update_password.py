from django.test import TestCase
from django.contrib.auth import get_user_model, authenticate
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class PasswordUpdateTests(TestCase):
    """修改密码测试用例"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='OldPass123!'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/user/update/password/'

    def test_change_password_success(self):
        """测试成功修改密码"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewStrongPass1!',
            'confirm_password': 'NewStrongPass1!'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('密码修改成功', response.data['message'])
        
        # 验证新密码可以登录
        self.user.refresh_from_db()
        user = authenticate(username='testuser', password='NewStrongPass1!')
        self.assertIsNotNone(user)

    def test_change_password_wrong_old_password(self):
        """测试旧密码错误"""
        data = {
            'old_password': 'WrongOldPass!',
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_change_password_mismatch(self):
        """测试新密码和确认密码不匹配"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'confirm_password': 'DifferentPass123!'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_change_password_weak(self):
        """测试密码强度不足"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'weak',
            'confirm_password': 'weak'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_change_password_same_as_old(self):
        """测试新密码与旧密码相同"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'OldPass123!',
            'confirm_password': 'OldPass123!'
        }
        response = self.client.post(self.url, data)
        
        # 这个应该成功，因为系统允许使用旧密码
        self.assertEqual(response.status_code, status.HTTP_200_OK)