from django.core.management.base import BaseCommand
from article_selector.meilisearch.meili_tools import MeilisearchTool

class Command(BaseCommand):
    help = 'rebuild meilisearch index'

    def handle(self, *args, **options):
        meili_tools = MeilisearchTool()
        meili_tools.rebuild_index()