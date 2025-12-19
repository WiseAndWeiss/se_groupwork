from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_sqlvec_tool_load

class Command(BaseCommand):
    help = 'get all articles id from sqlvec index'

    def handle(self, *args, **options):
        sqlvecTool = global_sqlvec_tool_load()
        res = sqlvecTool.get_all_articles_ids()
        print(f"{len(res)} articles in sqlvec index totally")
        print(res)