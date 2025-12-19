from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_sqlvec_tool_load

class Command(BaseCommand):
    help = 'update articles by ids to sqlvec index'

    def add_arguments(self, parser):
        parser.add_argument('target_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        target_ids = options['target_ids']
        sqlvecTool = global_sqlvec_tool_load()
        sqlvecTool.update_articles(target_ids)