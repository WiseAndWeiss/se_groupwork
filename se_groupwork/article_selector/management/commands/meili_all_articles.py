from django.core.management.base import BaseCommand
from article_selector.meilisearch.meili_tools import MeilisearchTool

class Command(BaseCommand):
    help = 'get all articles from meilisearch index'

    def handle(self, *args, **options):
        meili_tools = MeilisearchTool()
        res = meili_tools.get_all_articles_index()
        for id, title in res.items():
            print(f"- {id}: {title}")