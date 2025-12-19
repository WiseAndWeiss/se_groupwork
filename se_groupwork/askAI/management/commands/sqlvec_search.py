from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_sqlvec_tool_load
from webspider.models import Article

class Command(BaseCommand):
    help = 'search articles by question'

    def add_arguments(self, parser):
        parser.add_argument('query', type=str, help='search query')

    def handle(self, *args, **options):
        query = options['query']
        sqlvecTool = global_sqlvec_tool_load()
        res = sqlvecTool.search(query)
        for id, score in res:
            article = Article.objects.get(id=id)
            print(f"- {id}({score}) {article.title}")