from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_faiss_tool_load

class Command(BaseCommand):
    help = 'get all articles id from faiss index'

    def handle(self, *args, **options):
        faissTool = global_faiss_tool_load()
        res = faissTool.get_all_articles_ids_in_index()
        print(f"{len(res)} articles in faiss index totally")
        print(res)