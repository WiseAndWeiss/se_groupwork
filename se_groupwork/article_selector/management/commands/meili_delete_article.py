from django.core.management.base import BaseCommand
from article_selector.meilisearch.meili_tools import MeilisearchTool

class Command(BaseCommand):
    help = 'delete article by id to meilisearch index'
    
    def add_arguments(self, parser):
        parser.add_argument('article_id', type=int, help='article id to update')
        
    def handle(self, *args, **options):
        article_id = options['article_id']
        meilisearch_tool = MeilisearchTool()
        meilisearch_tool.delete_article(article_id)