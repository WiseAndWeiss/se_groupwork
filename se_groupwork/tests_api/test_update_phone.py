from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class PhoneUpdateTests(TestCase):
    """修改手机号测试用例"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            phone_number='13800138000'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/auth/update/phone/'

    def test_change_phone_success(self):
        """测试成功修改手机号"""
        data = {'new_phone': '13900139000'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '手机号修改成功')
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '13900139000')

    def test_change_phone_duplicate(self):
        """测试手机号重复"""
        # 创建另一个用户占用手机号
        User.objects.create_user(
            username='otheruser',
            password='TestPass123!',
            phone_number='13600136000'
        )
        
        data = {'new_phone': '13600136000'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_phone', response.data)

    def test_change_phone_empty(self):
        """测试手机号为空（应该允许，因为手机号是可选的）"""
        data = {'new_phone': ''}
        response = self.client.post(self.url, data)
        
        # 手机号可以为空
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '')