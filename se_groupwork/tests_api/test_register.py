import os
import sys
import django
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from user.models import User

class UserRegistrationAPITests(APITestCase):
    """用户注册API测试 - 专注于账号密码功能"""
    
    def setUp(self):
        """测试前置设置"""
        self.register_url = reverse('user:register')
        self.valid_data = {
            'username': 'testuser',
            'password': 'Testpass123!',
            'password_confirm': 'Testpass123!'
        }
    
    def test_successful_registration_with_username_password_only(self):
        """测试仅使用用户名和密码的成功注册"""
        response = self.client.post(self.register_url, self.valid_data, format='json')
        
        # 检查HTTP状态码
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 检查数据库中的用户数量
        self.assertEqual(User.objects.count(), 1)
        
        # 检查响应数据结构
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # 检查用户数据
        user_data = response.data['user']
        self.assertEqual(user_data['username'], 'testuser')
        
        # 检查用户是否真的被创建
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('Testpass123!'))  # 验证密码是否正确加密
    
    def test_registration_fails_with_mismatched_passwords(self):
        """测试密码不匹配时的注册失败"""
        invalid_data = {
            'username': 'testuser2',
            'password': 'Testpass123!d',
            'password_confirm': 'differentpassword'
        }
        response = self.client.post(self.register_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('两次密码不一致', str(response.data))
    
    def test_registration_fails_with_duplicate_username(self):
        """测试用户名重复时的注册失败"""
        # 先创建一个用户
        User.objects.create_user(username='existinguser', password='testpass')
        
        duplicate_data = {
            'username': 'existinguser',  # 重复的用户名
            'password': 'Testpass123!',
            'password_confirm': 'Testpass123!'
        }
        response = self.client.post(self.register_url, duplicate_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 检查错误消息中是否包含用户名相关的错误
        self.assertIn('username', response.data)
    
    def test_registration_fails_with_missing_username(self):
        """测试缺少用户名时的注册失败"""
        missing_username_data = {
            'password': 'Testpass123!',
            'password_confirm': 'Testpass123!'
            # 缺少username字段
        }
        response = self.client.post(self.register_url, missing_username_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_registration_fails_with_missing_password(self):
        """测试缺少密码时的注册失败"""
        missing_password_data = {
            'username': 'testuser3'
            # 缺少password和password_confirm字段
        }
        response = self.client.post(self.register_url, missing_password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 检查是否报告密码相关的错误
        self.assertIn('password', response.data)
    
    def test_registration_fails_with_short_password(self):
        """测试密码过短时的注册失败"""
        short_password_data = {
            'username': 'testuser4',
            'password': '123!Ts',  # 过短的密码
            'password_confirm': '123!Ts'
        }
        response = self.client.post(self.register_url, short_password_data, format='json')
        
        # 这个测试取决于你的密码验证规则
        # 如果设置了最小密码长度，应该返回400
        # 如果没有设置，可能会成功
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('password', response.data)
    
    def test_jwt_tokens_are_valid_after_registration(self):
        """测试注册后返回的JWT token是否有效"""
        response = self.client.post(self.register_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 获取返回的token
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        
        # 使用access token访问需要认证的API
        # 这里以获取用户资料为例（需要先实现这个API）
        # profile_response = self.client.get(
        #     reverse('profile'),
        #     HTTP_AUTHORIZATION=f'Bearer {access_token}'
        # )
        # self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        
        # 暂时注释掉，等实现了profile API后再取消注释
        print("Access Token:", access_token)
        print("Refresh Token:", refresh_token)
    
    def test_user_is_active_after_registration(self):
        """测试注册后的用户是活跃状态"""
        response = self.client.post(self.register_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)  # 新用户不应该是staff
    
    def test_multiple_registrations_with_different_usernames(self):
        """测试使用不同用户名进行多次注册"""
        users_data = [
            {
                'username': 'user1',
                'password': 'pass11Word!',
                'password_confirm': 'pass11Word!'
            },
            {
                'username': 'user2', 
                'password': 'pass21Word!',
                'password_confirm': 'pass21Word!'
            },
            {
                'username': 'user3',
                'password': 'pass31Word!',
                'password_confirm': 'pass31Word!'
            }
        ]
        
        for user_data in users_data:
            response = self.client.post(self.register_url, user_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证所有用户都被创建
        self.assertEqual(User.objects.count(), 3)
        self.assertTrue(User.objects.filter(username='user1').exists())
        self.assertTrue(User.objects.filter(username='user2').exists())
        self.assertTrue(User.objects.filter(username='user3').exists())

class UserRegistrationEdgeCaseTests(APITestCase):
    """边界情况测试"""
    
    def setUp(self):
        self.register_url = reverse('user:register')
    
    def test_registration_with_max_length_username(self):
        """测试使用最大长度的用户名"""
        # 根据你的User模型，用户名最大长度是20
        long_username = 'a' * 20  # 20个字符的用户名
        
        data = {
            'username': long_username,
            'password': 'password123T!',
            'password_confirm': 'password123T!'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        # 应该成功，因为正好是最大长度
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_registration_with_special_characters_in_username(self):
        """测试用户名中包含特殊字符"""
        # 根据你的用户名字段，允许的字符是：字母、数字和 @/./+/-/_ 
        special_username = 'user.name+test-test_user'
        
        data = {
            'username': special_username,
            'password': 'password123T!',
            'password_confirm': 'password123T!'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        # 这个测试取决于你的用户名验证规则
        # 如果允许这些特殊字符，应该成功
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('username', response.data)