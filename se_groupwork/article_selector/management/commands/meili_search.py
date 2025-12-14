from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_meili_tool_load
from webspider.models import Article

class Command(BaseCommand):
    help = 'search article id by text with meilisearch'
    
    def add_arguments(self, parser):
        parser.add_argument('text', type=str, help='search text')
    
    def handle(self, *args, **options):
        text = options['text']
        meili_tools = global_meili_tool_load()
        ids = meili_tools.search_articles(text)
        print("搜索结果:", ids)
        for id in ids:
            article = Article.objects.get(id=id)
            print(f"- {article.title} ({id})")
        