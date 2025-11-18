"""
models.py:用于规定爬虫数据库中数据表的格式
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


# Create your models here
class PublicAccount(models.Model):
    """
    微信公众号
    - 储存公众号的名字、图标地址（实际图片存储不在mysql中）、fakeid（用于爬虫）、公众号的所有已爬取文章
    """
    name = models.CharField(
        max_length=30,
        verbose_name='公众号名称',
    )
    icon = models.ImageField(
        upload_to='account_avatars/',  # 图片将保存在 media/account_avatars/ 目录下
        blank=True,
        verbose_name='图标',
    )
    fakeid = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Biz标识',
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='是否默认公众号',
    )
    last_crawl_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后爬取时间',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    def __str__(self):
        return f"{self.name} ({self.fakeid or '无微信号'})"

    class Meta:
        verbose_name = '微信公众号'
        verbose_name_plural = '微信公众号'
        ordering = ['-created_at']  # 按照表出现的先后顺序排列
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['fakeid']),
        ]


class Article(models.Model):
    """
    公众号文章
    - 储存文章的标题、上传时间、所属的公众号、url链接、ai总结后的内容、ai提取的关键信息、ai提供的标签
    """
    public_account = models.ForeignKey(
        PublicAccount,
        on_delete=models.CASCADE,  # 公众号删除时文章也删除
        related_name='articles',
        verbose_name='所属公众号'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='文章标题'
    )
    content = models.TextField(
        blank=True,
        verbose_name='文章内容'
    )
    author = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='作者'
    )
    article_url = models.URLField(
        unique=True,
        verbose_name='文章链接'
    )
    publish_time = models.DateTimeField(
        blank=True,
        verbose_name='发布时间'
    )
    summary = models.TextField(
        blank=True,
        verbose_name='文章总结'
    )
    key_info = models.TextField(
        blank=True,
        verbose_name='关键信息'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='标签'
    )
    tags_vector = models.JSONField(
        default=list,
        verbose_name="标签向量"
    )
    semantic_vector = models.JSONField(
        default=list,
        verbose_name="语义向量"
    )
    cover = models.ImageField(
        upload_to='article_covers/',
        blank=True,
        verbose_name='封面URL',
    )
    
    class Meta:
        verbose_name = '微信文章'
        verbose_name_plural = '微信文章'
        ordering = ['-publish_time']
        unique_together = ['public_account', 'publish_time']


class Cookies(models.Model):
    """
    储存爬虫用的cookies和tokens
    """
    cookies = models.TextField(
        verbose_name="Cookies"
    )
    token = models.CharField(
        max_length=100,
        verbose_name="Token"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        verbose_name = 'Cookies'
        verbose_name_plural = 'Cookies'
        ordering = ['-created_at']


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

@receiver(pre_save, sender=PublicAccount)
def auto_set_default_status(sender, instance, **kwargs):
    """
    信号：在保存公众号前，自动设置是否为默认公众号
    避免使用post_save防止递归调用
    """
    # 检查公众号名称是否在默认名单中
    default_accounts = getattr(settings, 'DEFAULT_PUBLIC_ACCOUNTS', [])
    instance.is_default = instance.name in default_accounts
