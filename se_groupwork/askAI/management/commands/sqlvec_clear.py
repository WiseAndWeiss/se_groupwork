from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_sqlvec_tool_load

class Command(BaseCommand):
    help = 'clear faiss index'
    
    def handle(self, *args, **options):
        sqlvec_tool = global_sqlvec_tool_load()
        sqlvec_tool.clear_index()