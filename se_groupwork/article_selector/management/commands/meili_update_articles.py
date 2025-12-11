from django.core.management.base import BaseCommand
from article_selector.meilisearch.meili_tools import MeilisearchTool

class Command(BaseCommand):
    help = 'update articles by id list to meilisearch index'
    
    def add_arguments(self, parser):
        parser.add_argument('articles_id', nargs='+', type=int)

    def handle(self, *args, **options):
        meili = MeilisearchTool()
        meili.update_batch_articles(options['articles_id'])