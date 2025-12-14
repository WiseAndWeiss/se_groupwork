from django.db.models.signals import post_save
from django.dispatch import receiver
from webspider.models import Article
from askAI.faiss.faiss_tools import FaissTool

@receiver(post_save, sender=Article)
def update_faiss_index(sender, instance, created, **kwargs):
    if created:
        article_id = instance.id
        faiss_tool = FaissTool()
        faiss_tool.update_article(article_id)
        print(f"Faiss index updated for article {article_id}")