from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_meili_tool_load

class Command(BaseCommand):
    help = 'update articles by id list to meilisearch index'
    
    def add_arguments(self, parser):
        parser.add_argument('articles_id', nargs='+', type=int)

    def handle(self, *args, **options):
        meili = global_meili_tool_load()
        meili.update_batch_articles(options['articles_id'])