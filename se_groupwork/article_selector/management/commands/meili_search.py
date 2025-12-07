from django.core.management.base import BaseCommand
from article_selector.meilisearch.meili_tools import MeilisearchTool
from webspider.models import Article

class Command(BaseCommand):
    help = 'search article id by text with meilisearch'
    
    def add_arguments(self, parser):
        parser.add_argument('text', type=str, help='search text')
    
    def handle(self, *args, **options):
        text = options['text']
        meili = MeilisearchTool()
        ids = meili.search_articles(text)
        print("搜索结果:", ids)
        for id in ids:
            article = Article.objects.get(id=id)
            print(f"- {article.title} ({id})")
        