from django.db.models.signals import post_save
from django.dispatch import receiver
from webspider.models import Article
from se_groupwork.global_tools import global_faiss_tool_load

@receiver(post_save, sender=Article)
def update_faiss_index(sender, instance, created, **kwargs):
    if created:
        article_id = instance.id
        faissTool = global_faiss_tool_load()
        faissTool.update_article(article_id)
        print(f"Faiss index updated for article {article_id}")