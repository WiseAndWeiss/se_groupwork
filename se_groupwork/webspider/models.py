"""
models.py:用于规定爬虫数据库中数据表的格式
"""

from django.db import models



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
        upload_to='icons/',  # 图片将保存在 media/account_avatars/ 目录下
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

    article_count = models.IntegerField(
        verbose_name='文章数', 
        default=0
    )
    subscription_count = models.IntegerField(
        verbose_name='被订阅数', 
        default=0
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
            models.Index(fields=['is_default']),  # 筛选默认公众号会用到
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
        max_length=50,
        verbose_name='文章标题'
    )
    content = models.TextField(
        blank=True,
        verbose_name='文章内容'
    )
    author = models.CharField(
        max_length=20,
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
    tags = models.JSONField(
        default=list,
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
        upload_to='covers/',
        blank=True,
        verbose_name='封面URL',
    )
    
    class Meta:
        verbose_name = '微信文章'
        verbose_name_plural = '微信文章'
        ordering = ['-publish_time']
        unique_together = ['public_account', 'article_url']
        indexes = [
            models.Index(fields=['-publish_time']),  # 获取最新文章会用到
            models.Index(fields=['public_account','-publish_time']),  # 获取公众号的最新文章会用到
        ]


class Cookies(models.Model):
    """
    储存爬虫用的cookies和tokens
    """
    cookies = models.TextField(
        verbose_name="Cookies"
    )
    token = models.CharField(
        max_length=20,
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


