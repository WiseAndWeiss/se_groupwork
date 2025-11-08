from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class EmailUpdateTests(TestCase):
    """修改邮箱测试用例"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='old@example.com'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/auth/update/email/'

    def test_change_email_success(self):
        """测试成功修改邮箱"""
        data = {'new_email': 'new@example.com'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '邮箱修改成功')
        self.assertEqual(response.data['user']['email'], 'new@example.com')
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')

    def test_change_email_duplicate(self):
        """测试邮箱重复"""
        # 创建另一个用户占用邮箱
        User.objects.create_user(
            username='otheruser',
            password='TestPass123!',
            email='existing@example.com'
        )
        
        data = {'new_email': 'existing@example.com'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_email', response.data)

    def test_change_email_invalid_format(self):
        """测试邮箱格式无效"""
        data = {'new_email': 'invalid-email'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_email', response.data)

    def test_change_email_empty(self):
        """测试邮箱为空"""
        data = {'new_email': ''}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_email', response.data)