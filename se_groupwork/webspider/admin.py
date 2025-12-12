from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import PublicAccount, Article, Cookies


# ==================== 内联模型配置 ====================

class ArticleInline(admin.TabularInline):
    """公众号文章的内联显示"""
    model = Article
    extra = 0
    readonly_fields = ('publish_time', 'get_title_preview')
    fields = ('title', 'publish_time', 'article_url', 'get_title_preview')
    show_change_link = True
    
    def get_title_preview(self, obj):
        """文章标题预览"""
        if len(obj.title) > 30:
            return f"{obj.title[:30]}..."
        return obj.title
    get_title_preview.short_description = _('标题预览')


# ==================== Admin类配置 ====================

@admin.register(PublicAccount)
class PublicAccountAdmin(admin.ModelAdmin):
    """公众号管理界面"""
    
    list_display = (
        'name', 'fakeid', 'is_default', 'get_article_count', 
        'get_subscription_count', 'last_crawl_time', 'created_at', 'get_icon_preview'
    )
    list_display_links = ('name', 'fakeid')
    list_filter = ('is_default', 'last_crawl_time', 'created_at')
    search_fields = ('name', 'fakeid')
    readonly_fields = ('created_at', 'last_crawl_time', 'get_icon_preview', 
                      'get_article_count_display', 'get_subscription_count_display')
    list_editable = ('is_default',)
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('name', 'fakeid', 'is_default')}),
        (_('媒体文件'), {'fields': ('icon', 'get_icon_preview')}),
        (_('统计信息'), {'fields': ('get_article_count_display', 'get_subscription_count_display')}),
        (_('时间信息'), {'fields': ('last_crawl_time', 'created_at')}),
    )
    
    inlines = [ArticleInline]
    
    # 自定义方法
    def get_icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '',
                obj.icon.url
            )
        return "无图标"
    get_icon_preview.short_description = _('图标预览')
    
    # 修复：使用自定义方法而不是直接使用字段
    def get_article_count(self, obj):
        return obj.articles.count()
    get_article_count.short_description = _('文章数')
    
    def get_subscription_count(self, obj):
        return obj.subscription_set.count()
    get_subscription_count.short_description = _('被订阅数')
    
    def get_article_count_display(self, obj):
        return obj.articles.count()
    get_article_count_display.short_description = _('文章数')
    
    def get_subscription_count_display(self, obj):
        return obj.subscription_set.count()
    get_subscription_count_display.short_description = _('被订阅数')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """文章管理界面"""
    
    list_display = (
        'title', 'public_account', 'author', 'publish_time', 
        'get_tags_count', 'has_summary', 'has_cover'
    )
    list_display_links = ('title', 'public_account')
    list_filter = ('public_account', 'publish_time', 'public_account__is_default')
    search_fields = ('title', 'content', 'author', 'public_account__name')
    readonly_fields = ('publish_time', 'get_cover_preview')
    raw_id_fields = ('public_account',)
    date_hierarchy = 'publish_time'
    list_per_page = 20
    
    fieldsets = (
        (_('基本信息'), {'fields': (
            'public_account', 'title', 'author', 'article_url', 'publish_time'
        )}),
        (_('内容'), {'fields': ('content', 'cover', 'get_cover_preview')}),
        (_('AI处理结果'), {'fields': (
            'summary', 'key_info', 'tags', 'tags_vector', 'semantic_vector'
        )}),
    )
    
    # 自定义列表显示方法
    def get_tags_count(self, obj):
        return len(obj.tags) if obj.tags else 0
    get_tags_count.short_description = _('标签数量')
    
    def has_summary(self, obj):
        return bool(obj.summary and obj.summary.strip())
    has_summary.boolean = True
    has_summary.short_description = _('有总结')
    
    def has_cover(self, obj):
        return bool(obj.cover)
    has_cover.boolean = True
    has_cover.short_description = _('有封面')
    
    def get_cover_preview(self, obj):
        if obj.cover:
            return format_html(
                '',
                obj.cover.url
            )
        return "无封面"
    get_cover_preview.short_description = _('封面预览')


@admin.register(Cookies)
class CookiesAdmin(admin.ModelAdmin):
    """Cookies管理界面"""
    
    list_display = ('token', 'created_at', 'get_cookies_length', 'get_cookies_preview')
    list_display_links = ('token',)
    list_filter = ('created_at',)
    search_fields = ('token', 'cookies')
    readonly_fields = ('created_at', 'get_cookies_preview')
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('token', 'cookies', 'get_cookies_preview')}),
        (_('时间信息'), {'fields': ('created_at',)}),
    )
    
    def get_cookies_length(self, obj):
        return len(obj.cookies) if obj.cookies else 0
    get_cookies_length.short_description = _('Cookies长度')
    
    def get_cookies_preview(self, obj):
        if obj.cookies and len(obj.cookies) > 100:
            return f"{obj.cookies[:100]}..."
        return obj.cookies or "无内容"
    get_cookies_preview.short_description = _('Cookies预览')