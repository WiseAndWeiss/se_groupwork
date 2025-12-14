from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_meili_tool_load

class Command(BaseCommand):
    help = 'get count of meilisearch index'

    def handle(self, *args, **options):
        meili_tools = global_meili_tool_load()
        count = meili_tools.get_article_index_count()
        print(count)