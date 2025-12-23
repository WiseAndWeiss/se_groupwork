from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count

from .models import User, Subscription, Collection, Favorite, History, Todo


# ==================== 内联模型配置 ====================

class SubscriptionInline(admin.TabularInline):
    """用户订阅的内联显示"""
    model = Subscription
    extra = 0
    readonly_fields = ('subscribed_at', 'order')
    fields = ('public_account', 'subscribed_at', 'order', 'is_active')
    raw_id_fields = ('public_account',)
    show_change_link = True


class CollectionInline(admin.TabularInline):
    """用户收藏夹的内联显示"""
    model = Collection
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'get_favorite_count_display')
    fields = ('name', 'is_default', 'get_favorite_count_display', 'created_at')
    show_change_link = True
    
    def get_favorite_count_display(self, obj):
        return obj.favorites.count()
    get_favorite_count_display.short_description = _('收藏文章数')


class FavoriteInline(admin.TabularInline):
    """收藏记录的内联显示"""
    model = Favorite
    extra = 0
    readonly_fields = ('favorited_at',)
    fields = ('article', 'collection', 'favorited_at')
    raw_id_fields = ('article',)
    show_change_link = True


class HistoryInline(admin.TabularInline):
    """浏览历史的内联显示"""
    model = History
    extra = 0
    readonly_fields = ('viewed_at',)
    fields = ('article', 'viewed_at')
    raw_id_fields = ('article',)
    show_change_link = True


class TodoInline(admin.TabularInline):
    """用户待办的内联显示"""
    model = Todo
    extra = 0
    readonly_fields = ('start_time', 'end_time', 'remind')
    fields = ('title', 'start_time', 'end_time', 'remind')
    raw_id_fields = ('article',)
    show_change_link = True


# ==================== Admin类配置 ====================

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """自定义用户管理界面"""
    
    # 列表页配置
    list_display = (
        'username', 'email', 'phone_number', 'is_active', 
        'is_staff', 'date_joined', 'subscription_count', 
        'favorite_count', 'get_avatar_preview'
    )
    list_display_links = ('username', 'email')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'phone_number')
    readonly_fields = ('date_joined', 'last_login', 'get_avatar_preview')
    ordering = ('-date_joined',)
    list_per_page = 20
    
    # 详情页字段分组
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': (
            'avatar', 'get_avatar_preview', 'email', 'phone_number', 'bio'
        )}),
        (_('权限状态'), {'fields': (
            'is_active', 'is_staff', 'is_superuser', 
            'groups', 'user_permissions'
        )}),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
        (_('统计信息'), {'fields': (
            'subscription_count', 'collection_count', 
            'favorite_count', 'history_count'
        )}),
    )
    
    # 添加用户表单配置
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    # 内联显示相关数据
    inlines = [SubscriptionInline, CollectionInline, FavoriteInline, HistoryInline, TodoInline]
    
    # 自定义方法
    def get_avatar_preview(self, obj):
        if obj.avatar:
            return format_html('', obj.avatar.url)
        return "无头像"
    get_avatar_preview.short_description = _('头像预览')
    
    # 批量操作
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        """激活用户"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {updated} 个用户')
    activate_users.short_description = _('激活选中的用户')
    
    def deactivate_users(self, request, queryset):
        """禁用用户"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功禁用 {updated} 个用户')
    deactivate_users.short_description = _('禁用选中的用户')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """订阅关系管理界面"""
    
    list_display = ('user', 'public_account', 'subscribed_at', 'order', 'is_active')
    list_display_links = ('user', 'public_account')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('user__username', 'public_account__name')
    readonly_fields = ('subscribed_at',)
    raw_id_fields = ('user', 'public_account')
    list_editable = ('order', 'is_active')
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('user', 'public_account')}),
        (_('订阅信息'), {'fields': ('subscribed_at', 'order', 'is_active')}),
    )


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """收藏夹管理界面"""
    
    list_display = ('name', 'user', 'is_default', 'get_favorite_count', 'created_at')
    list_display_links = ('name', 'user')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'user__username', 'description')
    readonly_fields = ('created_at', 'updated_at', 'get_favorite_count_display')
    raw_id_fields = ('user',)
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'is_default')}),
        (_('描述信息'), {'fields': ('description',)}),
        (_('统计信息'), {'fields': ('get_favorite_count_display',)}),
        (_('时间信息'), {'fields': ('created_at', 'updated_at')}),
    )
    
    inlines = [FavoriteInline]
    
    # 修复：使用自定义方法而不是注解
    def get_favorite_count(self, obj):
        return obj.favorites.count()
    get_favorite_count.short_description = _('收藏文章数')
    
    def get_favorite_count_display(self, obj):
        return obj.favorites.count()
    get_favorite_count_display.short_description = _('收藏文章数')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """收藏记录管理界面"""
    
    list_display = ('user', 'article', 'collection', 'favorited_at')
    list_display_links = ('user', 'article')
    list_filter = ('favorited_at', 'collection')
    search_fields = ('user__username', 'article__title', 'collection__name')
    readonly_fields = ('favorited_at',)
    raw_id_fields = ('user', 'article', 'collection')
    date_hierarchy = 'favorited_at'
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('user', 'article', 'collection')}),
        (_('时间信息'), {'fields': ('favorited_at',)}),
    )


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    """浏览历史管理界面"""
    
    list_display = ('user', 'article', 'viewed_at')
    list_display_links = ('user', 'article')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'article__title')
    readonly_fields = ('viewed_at',)
    raw_id_fields = ('user', 'article')
    date_hierarchy = 'viewed_at'
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('user', 'article')}),
        (_('时间信息'), {'fields': ('viewed_at',)}),
    )


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    """待办事项管理界面"""

    list_display = ('title', 'user', 'start_time', 'end_time', 'remind', 'article', 'created_at')
    list_display_links = ('title', 'user')
    list_filter = ('remind', 'start_time', 'end_time')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'article')
    date_hierarchy = 'start_time'
    ordering = ('start_time',)

    fieldsets = (
        (None, {'fields': ('user', 'title', 'note', 'article')}),
        (_('时间信息'), {'fields': ('start_time', 'end_time', 'remind')}),
        (_('记录信息'), {'fields': ('created_at', 'updated_at')}),
    )