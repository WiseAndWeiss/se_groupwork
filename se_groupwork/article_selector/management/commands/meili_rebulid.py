from django.core.management.base import BaseCommand
from se_groupwork.global_tools import global_meili_tool_load

class Command(BaseCommand):
    help = 'rebuild meilisearch index'

    def handle(self, *args, **options):
        meili_tools = global_meili_tool_load()
        meili_tools.rebuild_index()