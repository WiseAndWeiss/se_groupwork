from django.db.models.signals import post_save
from django.dispatch import receiver
from webspider.models import Article
from se_groupwork.global_tools import global_sqlvec_tool_load

@receiver(post_save, sender=Article)
def update_sqlvec_index(sender, instance, created, **kwargs):
    if created:
        article_id = instance.id
        sqlvecTool = global_sqlvec_tool_load()
        sqlvecTool.update_article(article_id)