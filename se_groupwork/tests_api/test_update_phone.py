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
        self.url = '/api/user/update/phone/'

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
    
    def test_change_phone_invalid_format(self):
        """测试手机号格式不正确"""
        # 测试各种无效的手机号格式
        invalid_phones = [
            '1234567890',      # 位数不够
            '123456789012',    # 位数过多
            '1380013800a',     # 包含字母
            '12345678901',     # 无效的号段
            '01234567890',     # 以0开头
            '1380013800 ',     # 包含空格
            '138-0013-8000',   # 包含特殊字符
            'abc12345678',     # 字母开头
            '12345abcde',      # 数字字母混合
        ]
        
        for invalid_phone in invalid_phones:
            with self.subTest(invalid_phone=invalid_phone):
                data = {'new_phone': invalid_phone}
                response = self.client.post(self.url, data)
                
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('new_phone', response.data)
                # 检查错误消息是否包含格式验证的提示
                error_message = str(response.data['new_phone'][0])
                self.assertIn('手机号', error_message.lower())

    def test_change_phone_valid_formats(self):
        """测试各种有效的手机号格式"""
        # 测试各种有效的手机号格式
        valid_phones = [
            '13800138000',  # 138号段
            '13900139000',  # 139号段
            '15000150000',  # 150号段
            '15100151000',  # 151号段
            '15200152000',  # 152号段
            '15700157000',  # 157号段
            '15800158000',  # 158号段
            '15900159000',  # 159号段
            '13000130000',  # 130号段
            '13100131000',  # 131号段
            '13200132000',  # 132号段
            '15500155000',  # 155号段
            '15600156000',  # 156号段
            '13300133000',  # 133号段
            '15300153000',  # 153号段
            '18000180000',  # 180号段
            '18900189000',  # 189号段
            '18100181000',  # 181号段
            '17700177000',  # 177号段
            '17300173000',  # 173号段
            '17600176000',  # 176号段
            '14700147000',  # 147号段
            '14500145000',  # 145号段
            '14900149000',  # 149号段
            '16600166000',  # 166号段
            '19800198000',  # 198号段
            '19900199000',  # 199号段
        ]
        
        for valid_phone in valid_phones:
            with self.subTest(valid_phone=valid_phone):
                data = {'new_phone': valid_phone}
                response = self.client.post(self.url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['message'], '手机号修改成功')
                
                # 验证手机号确实被更新了
                self.user.refresh_from_db()
                self.assertEqual(self.user.phone_number, valid_phone)
                
                # 重置为原始手机号，以便下一个测试
                self.user.phone_number = '13800138000'
                self.user.save()

    def test_change_phone_edge_cases(self):
        """测试边界情况"""
        # 测试边界情况的手机号
        edge_cases = [
            ('13800138000', status.HTTP_200_OK),  # 与原手机号相同（应该允许）
            ('1380013800', status.HTTP_400_BAD_REQUEST),  # 少一位
            ('138001380000', status.HTTP_400_BAD_REQUEST),  # 多一位
            ('+8613800138000', status.HTTP_400_BAD_REQUEST),  # 包含国际区号
            ('013800138000', status.HTTP_400_BAD_REQUEST),  # 以0开头
            ('138 0013 8000', status.HTTP_400_BAD_REQUEST),  # 包含空格
            ('', status.HTTP_400_BAD_REQUEST)  # 空手机号
        ]
        
        for phone, expected_status in edge_cases:
            with self.subTest(phone=phone, expected_status=expected_status):
                data = {'new_phone': phone}
                response = self.client.post(self.url, data)
                
                self.assertEqual(response.status_code, expected_status)
                
                if expected_status == status.HTTP_200_OK:
                    self.user.refresh_from_db()
                    self.assertEqual(self.user.phone_number, phone)
                    # 重置
                    self.user.phone_number = '13800138000'
                    self.user.save()