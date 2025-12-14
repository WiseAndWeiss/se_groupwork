from django.core.management.base import BaseCommand
from askAI.faiss.faiss_tools import FaissTool

class Command(BaseCommand):
    help = 'update article by id to faiss index'

    def add_arguments(self, parser):
        target_id = parser.add_argument('target_id', type=int, help='target article id')

    def handle(self, *args, **options):
        target_id = options['target_id']
        faiss_tool = FaissTool()
        faiss_tool.update_article(target_id)