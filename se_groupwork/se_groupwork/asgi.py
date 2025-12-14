"""
ASGI config for se_groupwork project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from se_groupwork.global_tools import global_embedding_load, global_faiss_tool_load, global_meili_tool_load

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'se_groupwork.settings')

global_embedding_load()
global_faiss_tool_load()
global_meili_tool_load()

application = get_asgi_application()



