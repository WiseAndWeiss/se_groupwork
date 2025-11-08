from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'email': 'test@example.com'
        }

    def test_user_registration_success(self):
        """测试用户注册成功"""
        url = reverse('register')
        response = self.client.post(url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('access' in response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_user_registration_password_mismatch(self):
        """测试密码不匹配"""
        data = self.user_data.copy()
        data['password_confirm'] = 'wrongpassword'
        url = reverse('register')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """测试用户登录成功"""
        User.objects.create_user(username='testuser', password='testpass123')
        url = reverse('login')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)

    def test_user_login_invalid_credentials(self):
        """测试无效登录凭证"""
        url = reverse('login')
        data = {'username': 'wronguser', 'password': 'wrongpass'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)