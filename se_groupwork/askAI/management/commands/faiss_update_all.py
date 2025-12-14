from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_faiss_tool_load

class Command(BaseCommand):
    help = 'Update all articles to faiss index'
    
    def handle(self, *args, **options):
        faissTool = global_faiss_tool_load()
        faissTool.update_all_articles()