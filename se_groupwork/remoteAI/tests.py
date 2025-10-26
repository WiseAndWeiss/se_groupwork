from django.test import TestCase
import json
from remoteAI.remoteAI.task_manager import TaskManager
from webspider.models import Article, PublicAccount

# Create your tests here.
class RemoteAITestCase(TestCase):
    # 测试前的准备工作（如创建测试数据）
    def setUp(self):
        # 创建测试用的PublicAccount数据（仅在测试中生效，不影响真实数据库）
        with open('remoteAI/testdata.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        for account in data['account']:
            PublicAccount.objects.create(**account)
        for article in data['article']:
            Article.objects.create(**article)

    # 测试具体功能（方法名必须以test_开头）
    def test_get_summary_ids(self):
        # 调用你要测试的功能（例如获取summary为Null的id）
        tm = TaskManager()
        result = tm.startrun()
        self.assertTrue(result)
