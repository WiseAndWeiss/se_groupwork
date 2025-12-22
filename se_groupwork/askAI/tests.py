from django.test import TestCase
from webspider.models import PublicAccount, Article
from askAI.askAI.ai_ask import ask_ai, get_reference_articles
from askAI.sqlvec.sqlvec_tool import SqliteVectorTool
from se_groupwork.global_tools import global_sqlvec_tool_load
import json
import time


class AskAITestCase(TestCase):
    def setUp(self):
        sqlvecTool = global_sqlvec_tool_load()
        sqlvecTool.clear_index()
        with open('askAI/testdata.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        account_info = data['account']
        account = PublicAccount.objects.create(**account_info)
        for article in data['articles']:
            Article.objects.create(
                public_account = account,
                title=article['title'],
                content=article['content'],
                article_url=article['article_url'],
                publish_time=article['publish_time']
            )

    def test_askAI(self):
        question1 = "最近食堂有什么上新的好吃的吗？"
        articles = get_reference_articles(question1)
        self.assertGreaterEqual(len(articles), 1)
        content = [article.content for article in articles]
        full_response = ""
        for chunk in ask_ai(question1, content):
            full_response += chunk
            print(chunk, end='')
        time.sleep(1)
    
    def test_sqlvec_tool(self):
        def t01_sqlvec_init(self):
            sqlvec_tool = global_sqlvec_tool_load()
            sqlvec_tool.clear_index()
            self.assertTrue(SqliteVectorTool.initialized)
            self.assertTrue(sqlvec_tool.test_mode)
            self.assertIsNotNone(sqlvec_tool._conn)
            index_num = len(sqlvec_tool.get_all_articles_ids_in_index())
            self.assertEqual(index_num, 0)
            return sqlvec_tool

        def t02_sqlvec_update(self, sqlvec_tool: SqliteVectorTool):
            articles = Article.objects.all()
            articles_ids = [article.id for article in articles]
            sqlvec_tool.update_article(articles_ids[0])
            index_num = len(sqlvec_tool.get_all_articles_ids_in_index())
            self.assertEqual(index_num, 1)
            sqlvec_tool.update_articles(articles_ids[1:3])
            index_num = len(sqlvec_tool.get_all_articles_ids_in_index())
            self.assertEqual(index_num, 3)
            sqlvec_tool.clear_index()
            sqlvec_tool.update_all_articles()
            index_num = len(sqlvec_tool.get_all_articles_ids_in_index())
            self.assertEqual(index_num, len(articles))

        def t03_sqlvec_rebuild(self, sqlvec_tool: SqliteVectorTool):
            sqlvec_tool.rebuild_index()
            index_num = len(sqlvec_tool.get_all_articles_ids_in_index())
            self.assertEqual(index_num, len(Article.objects.all()))

        def t04_sqlvec_search(self, sqlvec_tool: SqliteVectorTool):
            results = sqlvec_tool.search("", top_k=5)
            self.assertEqual(len(results), 0)
            question = "马上要期末考试了，我想了解考试时间安排"
            results = sqlvec_tool.search(question, top_k=5)
            print(f"\nSearch {question} results:")
            for result in results:
                id, score = result
                article = Article.objects.get(id=id)
                print(f"- {id}({score}) {article.title}")
            self.assertGreater(len(results), 0)
    
        sqlvec_tool = t01_sqlvec_init(self)
        t02_sqlvec_update(self, sqlvec_tool)
        t03_sqlvec_rebuild(self, sqlvec_tool)
        t04_sqlvec_search(self, sqlvec_tool)