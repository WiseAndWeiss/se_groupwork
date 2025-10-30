# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from user.models import Subscription, Favorite, History


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

@receiver(post_save, sender=Favorite)
def update_favorite_count_on_save(sender, instance, created, **kwargs):
    """
    当收藏关系创建时，更新用户的收藏计数
    """
    if created:
        user = instance.user
        user.favorite_count += 1
        user.save(update_fields=['favorite_count'])

@receiver(post_delete, sender=Favorite)
def update_favorite_count_on_delete(sender, instance, **kwargs):
    """
    当收藏关系删除时，更新用户的收藏计数
    """
    user = instance.user
    user.favorite_count -= 1
    user.save(update_fields=['favorite_count'])

@receiver(post_save, sender=History)
def update_history_count_on_save(sender, instance, created, **kwargs):
    """
    当浏览历史创建时，更新用户的浏览历史计数
    """
    if created:
        user = instance.user
        user.history_count += 1
        user.save(update_fields=['history_count'])

@receiver(post_delete, sender=History)
def update_history_count_on_delete(sender, instance, **kwargs):
    """
    当浏览历史删除时，更新用户的浏览历史计数
    """
    user = instance.user
    user.history_count -= 1
    user.save(update_fields=['history_count'])