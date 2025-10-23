# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from user.models import Subscription


@receiver(post_save, sender=Subscription)
def update_subscription_count_on_save(sender, instance, created, **kwargs):
    """
    当订阅关系创建或更新时，更新用户的订阅计数
    """
    if created and instance.is_active:
        # 新创建且活跃的订阅
        user = instance.user
        user.subscription_count += 1
        user.save(update_fields=['subscription_count'])


@receiver(post_delete, sender=Subscription)
def update_subscription_count_on_delete(sender, instance, **kwargs):
    """
    当订阅关系删除时，更新用户的订阅计数
    """
    user = instance.user
    user.subscription_count -= 1
    user.save(update_fields=['subscription_count'])