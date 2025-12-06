from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from webspider.models import Cookies, Article, PublicAccount

@receiver(post_save, sender=Cookies)
def limit_cookies_count(sender, instance, created, **kwargs):
    """
    信号：保存后检查cookies的记录数量，保持最多5条（因为cookies具有时效性）
    """
    if created:
        max_count = 5
        current_count = Cookies.objects.count()

        if current_count > max_count:
            # 获取需要删除的最旧记录的主键
            excess_count = current_count - max_count
            oldest_record_ids = Cookies.objects.order_by('created_at').values_list('id', flat=True)[:excess_count]

            # 使用主键列表进行删除
            deleted_count = Cookies.objects.filter(id__in=list(oldest_record_ids)).delete()[0]
            print(f"自动删除 {deleted_count} 条最旧记录，保持总数不超过 {max_count} 条")


@receiver(post_save, sender=Article)
def update_account_crawl_time(sender, instance, created, **kwargs):
    """
    当文章保存时，自动更新对应公众号的最后爬取时间
    """
    # 更新公众号的最后爬取时间
    instance.public_account.last_crawl_time = timezone.localtime(timezone.now())
    instance.public_account.save(update_fields=['last_crawl_time'])
    instance.public_account.article_count += 1 
    instance.public_account.save(update_fields=['article_count'])

@receiver(pre_save, sender=PublicAccount)
def auto_set_default_status(sender, instance, **kwargs):
    """
    信号：在保存公众号前，自动设置是否为默认公众号
    避免使用post_save防止递归调用
    """
    # 检查公众号名称是否在默认名单中
    default_accounts = getattr(settings, 'DEFAULT_PUBLIC_ACCOUNTS', [])
    instance.is_default = instance.name in default_accounts