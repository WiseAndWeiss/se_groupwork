from django.core.management.base import BaseCommand
from askAI.faiss.faiss_tools import FaissTool

class Command(BaseCommand):
    help = 'Update all articles to faiss index'
    
    def handle(self, *args, **options):
        faiss_tool = FaissTool()
        faiss_tool.update_all_articles()