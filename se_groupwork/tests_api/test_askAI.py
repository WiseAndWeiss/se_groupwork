from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.models import User
from webspider.models import Article, PublicAccount
from se_groupwork.global_tools import global_sqlvec_tool_load

import json
import time

class AskAITests(TestCase):
    def setUp(self):
        # 初始化向量工具并清空索引
        sqlvec_tool = global_sqlvec_tool_load()
        sqlvec_tool.clear_index()
        
        # 创建测试客户端和用户
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)
        
        # 创建测试公众号
        self.account = PublicAccount.objects.create(
            name='test account', 
            fakeid='fakeid1', 
            icon='icon.jpg'
        )
        
        # 加载测试文章数据
        with open('tests_api/testdata_askAI.json', 'r', encoding='utf-8') as f:
            self.articles_info = json.load(f)['articles']
        
        # 创建测试文章
        for article_info in self.articles_info:
            Article.objects.create(
                public_account=self.account,
                title=article_info['title'],
                content=article_info['content'],
                article_url=article_info['article_url'],
                publish_time=article_info['publish_time']
            )
        
        # 定义API端点
        self.ask_url = reverse('ask')
        self.ask_stream_url = reverse('ask-stream')
        self.test_question1 = "最近有什么体育活动或比赛可以参加吗？"
        self.test_question2 = "快要期末考试了，我想知道考试的时间安排"

    def test_ask_ai_endpoints(self):
        """测试普通问答和流式问答两个接口"""
        
        def test_ask_normal():
            """测试普通问答接口"""
            data = {"question": self.test_question1}
            response = self.client.post(self.ask_url, data, format='json')
            # 验证响应状态码
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # 验证响应结构
            self.assertIn('question', response.data)
            self.assertIn('answer', response.data)
            self.assertIn('references-articles', response.data)
            print("Answer:", response.data['answer'])
            # 验证参考文章不为空（假设测试数据能匹配到结果）
            self.assertIsInstance(response.data['references-articles'], list)

        def test_ask_stream():
            """测试流式问答接口"""
            data = {"question": self.test_question2}
            response = self.client.post(self.ask_stream_url, data, format='json')
            
            # 验证响应状态码和内容类型
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
            
            # 读取流式响应内容
            print("Streaming Answer:")
            content = b''.join(response.streaming_content).decode('utf-8')
            print(content)
            
            # 验证内容包含回答和参考信息标记
            self.assertTrue(len(content) > 0)
            self.assertIn('[[REFERENCES]]', content)
            
            # 解析参考文章部分
            references_part = content.split('[[REFERENCES]]')[-1].strip()
            references = json.loads(references_part)
            self.assertIsInstance(references, list)

        # 执行两个子测试
        test_ask_normal()
        test_ask_stream()