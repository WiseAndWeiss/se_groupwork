from django.test import TestCase
from webspider.models import Article, PublicAccount
from remoteAI.remoteAI.task_manager import TaskManager
import json
import time
import csv

class RemoteAITests(TestCase):
    def setUp(self):
        account = PublicAccount.objects.create(
            name= "学生清华",
            icon= "icon1.jpg",
            fakeid= "fakeid1"
        )
        with open('tests_pref/testdata_remoteAI.json', 'r', encoding='utf-8') as f:
            self.testdata = json.load(f)
            for article in self.testdata:
                Article.objects.create(
                    **article,
                    public_account=account
                )
    
    def test_parallel_remoteAI(self):
        # 热身
        warm_up_tasks_pool = [1]
        TaskManager(max_workers=1).startrun_fortest(warm_up_tasks_pool)
        # 参数准备
        tasks_pool = [1,2,3,4,5,6,7,8,9,10] * 50
        max_workers_range = [5, 10, 15, 20, 25, 50, 75, 100]
        csv_data = [
            ["max_workers", "tasks_num", "time", "time/articles", "time/(articles * workers))"]
        ]
        # 测试
        for max_workers in max_workers_range:
            print("============start test for max_workers = {}==============".format(max_workers))
            test_length = max_workers * 4
            start = time.time()
            TaskManager(max_workers=max_workers).startrun_fortest(tasks_pool[0:test_length])
            end = time.time()
            # 记录与打印
            csv_data.append([max_workers, test_length, end - start, (end - start) / test_length, ((end - start) / test_length) / max_workers])
            print("max_workers = {}, tasks_num = {}, time = {}".format(max_workers, test_length, end - start))
            print("average time per article = {}".format((end - start) / test_length))
            print("average time per article per worker = {}".format(((end - start) / test_length) / max_workers))
            print("===================================")
        with open('tests_pref/testresult_remoteAI.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)