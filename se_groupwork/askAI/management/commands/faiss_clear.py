from django.core.management.base import BaseCommand
from askAI.faiss.faiss_tools import FaissTool

class Command(BaseCommand):
    help = 'clear faiss index'
    
    def handle(self, *args, **options):
        faiss_tool = FaissTool()
        faiss_tool.clear_index()