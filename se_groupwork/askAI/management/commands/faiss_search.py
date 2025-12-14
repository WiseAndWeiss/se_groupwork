from django.core.management.base import BaseCommand
from askAI.faiss.faiss_tools import FaissTool
from webspider.models import Article

class Command(BaseCommand):
    help = 'search articles by question'

    def add_arguments(self, parser):
        parser.add_argument('query', type=str, help='search query')

    def handle(self, *args, **options):
        query = options['query']
        faiss_tool = FaissTool()
        res = faiss_tool.search(query)
        for id, score in res:
            article = Article.objects.get(id=id)
            print(f"- {id}({score}) {article.title}")