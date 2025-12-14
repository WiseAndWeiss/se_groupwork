from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_meili_tool_load

class Command(BaseCommand):
    help = 'delete article by id to meilisearch index'
    
    def add_arguments(self, parser):
        parser.add_argument('article_id', type=int, help='article id to update')
        
    def handle(self, *args, **options):
        article_id = options['article_id']
        meili_tools = global_meili_tool_load()
        meili_tools.delete_article(article_id)