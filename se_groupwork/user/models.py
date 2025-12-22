from django.db import models, transaction
from django.db.models import F, Q
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.conf import settings


from webspider.models import PublicAccount,Article

def user_avatar_path(instance, filename):
    # 文件将上传到 MEDIA_ROOT/avatars/user_<id>
    return f'avatars/{instance.id}/{filename}'

class UserManager(BaseUserManager):
    """自定义用户管理器"""

    def create_user(self, username,  password, email=None, **extra_fields):
        """创建普通用户"""
        if not username:
            raise ValueError('用户必须提供用户名')
        if not password:
            raise ValueError('用户必须提供密码')
        
        if email:
            email = self.normalize_email(email)
        else:
            email = None  # 不能是空字符串！否则违背了唯一性原则

        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )

        user.set_password(password)  # 加密密码
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, email=None, **extra_fields):
        """创建超级用户"""
        if not email:
            raise ValueError('超级用户必须提供邮箱')
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')

        return self.create_user(username, password, email, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    自定义用户模型
    - 储存用户的基本信息
    - 不直接存储订阅号信息（通过外键关系关联）
    """

    # 基本身份信息
    username = models.CharField(
        _('用户名'),
        max_length=20,
        unique=True,
        help_text=_('必填，不超过20个字符。只能包含字母、数字和 @/./+/-/_ 字符。'),
        error_messages={
            'unique': _("该用户名已被占用。"),
        },
    )
    email = models.EmailField(
        _('邮箱地址'),
        blank=True,
        null=True,  # 添加这一行
        unique=True,
        error_messages={
            'unique': _("该邮箱地址已被占用。"),
        },
    )
    phone_number = models.CharField(
        _('手机号'),
        max_length=11,
        blank=True,
        null=True,  # 添加这一行
        unique=True,
        error_messages={
            'unique': _("该手机号已被占用。"),
        },
    )
    avatar = models.ImageField(
        _('头像'),
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        help_text=_('用户头像图片')
    )
    bio = models.TextField(
        _('个人简介'),
        blank=True,
        max_length=500,
        help_text=_('简短的个人介绍，最多500字')
    )
    is_staff = models.BooleanField(
        _('员工状态'),
        default=False,
        help_text=_('标记用户是否可以登录到管理员站点。')
    )
    is_active = models.BooleanField(
        _('活跃状态'),
        default=True,
        help_text=_('标记用户是否被视为活跃用户。取消选中而不是删除账户。')
    )

    # 时间信息
    date_joined = models.DateTimeField(_('注册时间'), default=timezone.now)

    # 统计信息
    subscription_count = models.IntegerField(_('订阅公众号数'), default=0)
    collection_count = models.IntegerField(_('收藏夹数'), default=0)
    favorite_count = models.IntegerField(_('收藏文章数'), default=0)
    history_count = models.IntegerField(_('活跃浏览历史数'), default=0)

    # 设置字段
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'  # 用作唯一标识的字段
    REQUIRED_FIELDS = ['email']  # 创建超级用户时需要提供的字段

    # 自定义用户管理器
    objects = UserManager()

    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_name(self):
        """返回用户的完整名称（昵称或用户名）"""
        return self.username

class SubscriptionManager(models.Manager):
    """自定义订阅管理器"""

    # 获取用户的所有订阅公众号
    def get_user_subscriptions(self, user):
        return self.filter(user=user).select_related('public_account')
    
    # 检测用户是否订阅了某个公众号
    def is_subscribed(self, user, public_account): 
        return self.filter(user=user, public_account=public_account).exists()
    
    # 创建订阅，更新其排序值
    def create_subscription(self, user, public_account):
        # 获取当前最大排序值
        max_order = self.filter(user=user).aggregate(models.Max('order'))['order__max'] or 0
        subscription = self.create(user=user, public_account=public_account, order=max_order + 1)
        return subscription
    
    # 删除用户的所有订阅
    def clear_user_subscriptions(self, user):
        self.filter(user=user).delete()

    # 删除订阅并更新用户的订阅计数
    def delete_subscription(self, subscription):
        subscription.delete()
    
    # 批量更新订阅排序顺序
    def update_order(self, user, subscription_orders):
        subscriptions = self.filter(user=user, id__in=subscription_orders.keys())
        
        with transaction.atomic():
            for subscription in subscriptions:
                new_order = subscription_orders.get(str(subscription.id))
                if new_order is not None:
                    subscription.order = new_order
                    subscription.save(update_fields=['order'])


class Subscription(models.Model):
    """
    订阅关系：连接一个用户-一个公众号的中间表，此外还记录一些其它订阅信息
    图例：用户A-订阅-公众号A
    当用户/公众号删除时，订阅记录自动删除
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    public_account = models.ForeignKey(
        PublicAccount, 
        on_delete=models.CASCADE
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('排序顺序')
    )
    is_active = models.BooleanField(default=True)
    
    objects = SubscriptionManager()

    class Meta:
        unique_together = [('user', 'public_account')]  # 防止重复订阅
        ordering = ['order','-subscribed_at']  # 先按排序顺序，再按订阅时间排序
        indexes = [
            models.Index(fields=['user', 'order']),
            models.Index(fields=['user', '-subscribed_at']),
            # models.Index(fields=['user', 'public_account']),  # unique_together已自动创建
        ]
    def __str__(self):
        return f"{self.user} -> {self.public_account}"
    

class CollectionManager(models.Manager):
    """自定义收藏夹管理器"""

    # 获取用户的所有收藏夹
    def get_user_collections(self, user):
        return self.filter(user=user).prefetch_related('favorites')
    
    # 获取用户特定的收藏夹
    def get_user_collection(self, user, collection_id):
        return self.get(user=user, id=collection_id)

    # 创建新的收藏夹
    def create_collection(self, user, name, description=''):
        # 获取当前最大排序值
        max_order = self.filter(user=user).aggregate(models.Max('order'))['order__max'] or 0 
        collection = self.create(
            user=user, 
            name=name,
            description=description,
            order=max_order + 1,
        )
        return collection

    # 删除收藏夹,以及其中的所有收藏
    def delete_collection(self, collection):
        collection.favorites.all().delete()
        collection.delete()

    # 检查用户是否已有同名收藏夹
    def collection_exists(self, user, name):
        return self.filter(user=user, name=name).exists()

class Collection(models.Model):
    """
    用户的收藏夹
    图例：用户A-收藏夹-收藏A,收藏B,...
    当用户删除时，收藏夹自动删除
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name=_('所属用户')
    )
    name = models.CharField(
        _('收藏夹名称'),
        max_length=50,
        help_text=_('收藏夹名称，不超过50个字符')
    )
    description = models.TextField(
        _('收藏夹描述'),
        blank=True,
        max_length=100,
        help_text=_('收藏夹描述，最多100字')
    )
    created_at = models.DateTimeField(
        _('创建时间'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('更新时间'),
        auto_now=True
    )
    is_default = models.BooleanField(
        _('是否为默认收藏夹'),
        default=False
    )
    order = models.PositiveIntegerField(
        _('排序顺序'),
        default=0
    )
    favorite_count = models.IntegerField(_('收藏文章数'), default=0)

    objects = CollectionManager()

    class Meta:
        verbose_name = _('收藏夹')
        verbose_name_plural = _('收藏夹')
        unique_together = [('user', 'name')]  # 同一用户下收藏夹名称唯一
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),  # 获取默认收藏夹
            # models.Index(fields=['user', 'name']),  # unique_together已自动创建
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_favorite_count(self):
        """获取收藏夹中的文章数量"""
        return self.favorites.count()
    
    def delete(self, *args, **kwargs):
        """防止删除默认收藏夹"""
        if self.is_default:
            raise ValueError("默认收藏夹不可删除")
        super().delete(*args, **kwargs)


class FavoriteManager(models.Manager):
    """自定义收藏管理器"""

    # 获取用户的所有收藏
    def get_user_favorites(self, user):
        return self.filter(user=user).select_related('article')
    
    # 检测用户是否收藏了某篇文章
    def is_favorited(self, user, article): 
        return self.filter(user=user, article=article).exists()
    
    # 创建收藏并更新用户的收藏计数
    def create_favorite(self, user, article, collection):
        # 如果没有指定收藏夹，则使用默认收藏夹（如果没有，则会自动创建）
        if not collection:
           collection, created = Collection.objects.get_or_create(
                user=user,
                is_default=True,
                defaults={
                    'name': "默认收藏夹",
                    'order': 0
                }
            )
            
        favorite = self.create(user=user, article=article, collection=collection)
        return favorite
    
    # 删除用户的所有收藏
    def clear_user_favorites(self, user):
        self.filter(user=user).delete()
    
    # 删除收藏并更新用户的收藏计数
    def delete_favorite(self, favorite):
        favorite.delete()

    # 获取收藏夹中的所有收藏
    def get_collection_favorites(self, collection):
        return self.filter(collection=collection)

    # 移动收藏到其他收藏夹，并手动更新计数
    def move_favorite(self, favorite, new_collection):
        old_collection = favorite.collection 

        favorite.collection = new_collection
        favorite.save(update_fields=['collection'])

        if old_collection:
            old_collection.favorite_count = max(0, old_collection.favorite_count - 1)
            old_collection.save(update_fields=['favorite_count'])
        
        new_collection.favorite_count += 1
        new_collection.save(update_fields=['favorite_count'])

        return favorite

    # 删除收藏夹的所有收藏
    def clear_collection_favorites(self, collection):
        self.filter(collection=collection).delete()

class Favorite(models.Model):
    """
    用户收藏的文章
    图例：用户A-收藏-文章A
    当用户/文章/收藏夹删除时，收藏记录自动删除
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('所属收藏夹'),
        null=True,
        blank=True
    )
    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE
    )
    favorited_at = models.DateTimeField(
        auto_now_add=True
    )

    objects = FavoriteManager()

    class Meta:
        unique_together = [('user', 'article')]  # 防止重复收藏
        ordering = ['-favorited_at']  # 按照收藏时间排列，最新收藏的在前面
        indexes = [
            models.Index(fields=['user', '-favorited_at']),
            models.Index(fields=['collection', '-favorited_at']),
            # models.Index(fields=['user', 'article']),  # unique_together已自动创建
        ]
        verbose_name = _('收藏记录')
        verbose_name_plural = _('收藏记录')

    def __str__(self):
        return f"{self.user} favorited {self.article} in {self.collection}"
    
    def save(self, *args, **kwargs):
        # 自动设置user为collection的user
        if not self.user_id:
            self.user = self.collection.user
        super().save(*args, **kwargs)


class HistoryManager(models.Manager):
    """自定义浏览历史管理器"""

    # 获取用户的所有浏览历史
    def get_user_history(self, user):
        return self.filter(user=user).select_related('article')

    # 检测用户是否浏览过某篇文章
    def is_viewed(self, user, article): 
        return self.filter(user=user, article=article).exists()

    # 创建一条浏览历史记录（唯一性约束：同一用户同一文章只保留一条，若已存在则更新时间）
    def create_history(self, user, article):
        obj, created = self.get_or_create(user=user, article=article)
        if not created:
            # 已存在则更新时间
            obj.viewed_at = timezone.now()
            obj.save(update_fields=["viewed_at"])
        return obj

    # 删除某个用户的所有浏览历史记录
    def clear_user_history(self, user):
        self.filter(user=user).delete()

    # 删除某条浏览历史记录
    def delete_history(self, history):
        history.delete()


class History(models.Model):
    """
    用户浏览历史
    图例：用户A-浏览-文章A
    当用户/文章删除时，浏览记录自动删除
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True
    )   

    objects = HistoryManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "article"], name="unique_user_article_history")
        ]
        ordering = ['-viewed_at']  # 按照浏览时间排列，最新浏览的在前面
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
        ]
    def __str__(self):
        return f"{self.user} viewed {self.article}"


class Todo(models.Model):
    """用户待办事项，用于日历标记和提醒"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='todos'
    )
    title = models.CharField(_('标题'), max_length=100)
    note = models.TextField(_('备注'), blank=True)
    start_time = models.DateTimeField(_('开始时间'))
    end_time = models.DateTimeField(_('结束时间'), null=True, blank=True)
    remind = models.BooleanField(_('是否提醒'), default=False)
    article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('相关文章')
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('待办')
        verbose_name_plural = _('待办')
        ordering = ['start_time', 'id']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['user', 'end_time']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gte=F('start_time')) | Q(end_time__isnull=True),
                name='todo_end_after_start'
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.user})"