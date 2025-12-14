from django.core.management.base import BaseCommand
from askAI.faiss.faiss_tools import FaissTool

class Command(BaseCommand):
    help = 'update articles by ids to faiss index'

    def add_arguments(self, parser):
        target_ids = parser.add_argument('target_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        target_ids = options['target_ids']
        faiss_tool = FaissTool()
        faiss_tool.update_articles(target_ids)