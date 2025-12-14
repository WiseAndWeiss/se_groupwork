from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_meili_tool_load

class Command(BaseCommand):
    help = 'sync articles to meilisearch index with mysql'
    
        
    def handle(self, *args, **options):
        meili_tools = global_meili_tool_load()
        meili_tools.sync_articles_index_with_mysql()