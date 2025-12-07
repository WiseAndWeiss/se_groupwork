from django.core.management.base import BaseCommand
from article_selector.meilisearch.meili_tools import MeilisearchTool

class Command(BaseCommand):
    help = 'get count of meilisearch index'

    def handle(self, *args, **options):
        meili_tools = MeilisearchTool()
        count = meili_tools.get_article_index_count()
        print(count)