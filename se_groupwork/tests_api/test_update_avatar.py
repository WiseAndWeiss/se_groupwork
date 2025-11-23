import os
from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AvatarUpdateTests(TestCase):
    """修改头像测试用例"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/user/update/avatar/'

    def create_test_image(self, format='JPEG', size=(100, 100), filename='test.jpg'):
        """创建测试图片"""
        image = Image.new('RGB', size, color='red')
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return SimpleUploadedFile(
            filename,
            buffer.getvalue(),
            content_type=f'image/{format.lower()}'
        )

    def test_update_avatar_success(self):
        """测试成功修改头像"""
        image_file = self.create_test_image()
        
        data = {'avatar': image_file}
        response = self.client.patch(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '头像修改成功')
        self.assertIn('avatar', response.data['user'])
        
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar)

    def test_update_avatar_no_file(self):
        """测试未提供头像文件"""
        response = self.client.patch(self.url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('请选择头像文件', response.data['error'])

    def test_update_avatar_invalid_format(self):
        """测试无效的文件格式"""
        # 创建文本文件
        text_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )
        
        data = {'avatar': text_file}
        response = self.client.patch(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('只支持JPEG、JPG、PNG和GIF格式的图片', response.data['error'])

    def test_update_avatar_png_format(self):
        """测试PNG格式图片"""
        image_file = self.create_test_image('PNG', filename='test.png')
        
        data = {'avatar': image_file}
        response = self.client.patch(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar)