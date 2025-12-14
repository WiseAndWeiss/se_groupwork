from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_faiss_tool_load

class Command(BaseCommand):
    help = 'update article by id to faiss index'

    def add_arguments(self, parser):
        parser.add_argument('target_id', type=int, help='target article id')

    def handle(self, *args, **options):
        target_id = options['target_id']
        faissTool = global_faiss_tool_load()
        faissTool.update_article(target_id)