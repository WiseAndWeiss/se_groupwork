# signals.py
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from user.models import Subscription, Favorite, History, Collection, User

HISTORY_MAX_RECORDS = getattr(settings, 'HISTORY_MAX_RECORDS', 100)

@receiver(post_save, sender=User)
def create_default_collection(sender, instance, created, **kwargs):
    """
    当新用户注册时，自动创建默认收藏夹
    """
    if created:
        Collection.objects.create(
            user=instance,
            name="默认收藏夹",
            is_default=True,
            order=0
        )

@receiver(post_save, sender=Subscription)
def update_subscription_count_on_save(sender, instance, created, **kwargs):
    """
    当订阅关系创建或更新时，更新用户和公众号的订阅计数
    """
    if created and instance.is_active:
        # 使用原子操作更新计数
        from user.models import User, PublicAccount
        
        User.objects.filter(id=instance.user_id).update(
            subscription_count=F('subscription_count') + 1
        )
        PublicAccount.objects.filter(id=instance.public_account_id).update(
            subscription_count=F('subscription_count') + 1
        )

@receiver(post_delete, sender=Subscription)
def update_subscription_count_on_delete(sender, instance, **kwargs):
    """
    当订阅关系删除时，更新用户和公众号的订阅计数
    """
    # 使用原子操作更新计数
    from user.models import User, PublicAccount
    
    User.objects.filter(id=instance.user_id).update(
        subscription_count=F('subscription_count') - 1
    )
    PublicAccount.objects.filter(id=instance.public_account_id).update(
        subscription_count=F('subscription_count') - 1
    )

@receiver(post_save, sender=Collection)
def update_collection_count_on_save(sender, instance, created, **kwargs):
    """
    当收藏夹创建时，更新用户的收藏夹计数
    """
    if created:
        User.objects.filter(id=instance.user_id).update(
            collection_count=F('collection_count') + 1
        )

@receiver(post_delete, sender=Collection)
def update_collection_count_on_delete(sender, instance, **kwargs):
    """
    当收藏夹删除时，更新用户的收藏夹计数
    """
    User.objects.filter(id=instance.user_id).update(
        collection_count=F('collection_count') - 1
    )

@receiver(post_save, sender=Favorite)
def update_favorite_count_on_save(sender, instance, created, **kwargs):
    """
    当收藏关系创建时，更新用户的收藏计数，以及收藏夹计数
    """
    if created:
        # 原子更新用户收藏计数
        User.objects.filter(id=instance.user_id).update(
            favorite_count=F('favorite_count') + 1
        )
        
        # 原子更新收藏夹计数
        if instance.collection_id:
            from user.models import Collection
            Collection.objects.filter(id=instance.collection_id).update(
                favorite_count=F('favorite_count') + 1
            )

@receiver(post_delete, sender=Favorite)
def update_favorite_count_on_delete(sender, instance, **kwargs):
    """
    当收藏关系删除时，更新用户的收藏计数，以及收藏夹计数
    """
    # 原子更新用户收藏计数
    User.objects.filter(id=instance.user_id).update(
        favorite_count=F('favorite_count') - 1
    )
    
    # 原子更新收藏夹计数
    if instance.collection_id:
        from user.models import Collection
        Collection.objects.filter(id=instance.collection_id).update(
            favorite_count=F('favorite_count') - 1
        )

@receiver(post_save, sender=History)
def update_history_count_on_save(sender, instance, created, **kwargs):
    """
    当浏览历史创建时，更新用户的浏览历史计数
    """
    if created:
        User.objects.filter(id=instance.user_id).update(
            history_count=F('history_count') + 1
        )

@receiver(post_save, sender=History)
def enforce_history_cap(sender, instance, **kwargs):
    """确保每个用户的历史记录不超过HISTORY_MAX_RECORDS（保留最新的）"""
    if not HISTORY_MAX_RECORDS or HISTORY_MAX_RECORDS <= 0:
        return

    # 获取用户的历史记录，按时间倒序排列
    qs = (
        History.objects
        .filter(user=instance.user)
        .order_by('-viewed_at', '-id')
    )
    
    # 找出需要删除的旧记录ID
    stale_ids = list(qs.values_list('id', flat=True)[HISTORY_MAX_RECORDS:])
    
    if stale_ids:
        # 批量删除旧记录，这会自动触发post_delete信号
        History.objects.filter(id__in=stale_ids).delete()


@receiver(post_save, sender=History)
def enforce_history_cap(sender, instance, **kwargs):
    """Ensure per-user history does not exceed HISTORY_MAX_RECORDS (keep latest)."""
    if not HISTORY_MAX_RECORDS or HISTORY_MAX_RECORDS <= 0:
        return

    qs = (
        History.objects
        .filter(user=instance.user)
        .order_by('-viewed_at', '-id')
    )
    stale_ids = list(qs.values_list('id', flat=True)[HISTORY_MAX_RECORDS:])
    if stale_ids:
        History.objects.filter(id__in=stale_ids).delete()

@receiver(post_delete, sender=History)
def update_history_count_on_delete(sender, instance, **kwargs):
    """
    当浏览历史删除时，更新用户的浏览历史计数
    """
    User.objects.filter(id=instance.user_id).update(
        history_count=F('history_count') - 1
    )