from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_meili_tool_load

class Command(BaseCommand):
    help = 'get all articles from meilisearch index'

    def handle(self, *args, **options):
        meili_tools = global_meili_tool_load()
        res = meili_tools.get_all_articles_index()
        for id, title in res.items():
            print(f"- {id}: {title}")