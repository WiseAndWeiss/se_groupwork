"""
WSGI config for se_groupwork project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from se_groupwork.global_tools import global_embedding_load, global_faiss_tool_load, global_meili_tool_load

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'se_groupwork.settings')

# Initialize Django before loading tools that depend on apps/models.
application = get_wsgi_application()

global_embedding_load()
global_faiss_tool_load()
global_meili_tool_load()

