from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_sqlvec_tool_load

class Command(BaseCommand):
    help = 'Rebuild sqlvec index'
    
    def handle(self, *args, **options):
        sqlvecTool = global_sqlvec_tool_load()
        sqlvecTool.rebuild_index()