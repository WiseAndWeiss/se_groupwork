from django.core.management.base import BaseCommand
from article_selector.meilisearch.meili_tools import MeilisearchTool

class Command(BaseCommand):
    help = 'sync articles to meilisearch index with mysql'
    
        
    def handle(self, *args, **options):
        meilisearch_tool = MeilisearchTool()
        meilisearch_tool.sync_articles_index_with_mysql()