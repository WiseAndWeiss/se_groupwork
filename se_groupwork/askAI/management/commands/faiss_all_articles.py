from django.core.management.base import BaseCommand
from askAI.faiss.faiss_tools import FaissTool

class Command(BaseCommand):
    help = 'get all articles id from faiss index'

    def handle(self, *args, **options):
        faissTool = FaissTool()
        res = faissTool.get_all_articles_ids_in_index()
        print(f"{len(res)} articles in faiss index totally")
        print(res)