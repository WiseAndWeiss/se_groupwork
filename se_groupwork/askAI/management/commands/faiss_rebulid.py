from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_faiss_tool_load

class Command(BaseCommand):
    help = 'Rebuild faiss index'
    
    def handle(self, *args, **options):
        faissTool = global_faiss_tool_load()
        faissTool.rebuild_index()