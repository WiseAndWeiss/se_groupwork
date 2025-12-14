from django.test import TestCase
from se_groupwork.global_tools import global_faiss_tool_load

# Create your tests here.
class Test(TestCase):
	def setUp(self):
		self.faissTool = global_faiss_tool_load()

	def test1(self):
		self.assertTrue(self.faissTool.test_mode)
		self.assertEqual(self.faissTool.get_all_articles_ids_in_index(), [])