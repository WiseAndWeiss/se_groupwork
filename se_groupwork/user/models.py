from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.conf import settings

from webspider.models import PublicAccount,Article


class UserManager(BaseUserManager):
    """自定义用户管理器"""

    def create_user(self, username,  password, email=None, **extra_fields):
        """创建普通用户"""
        if not username:
            raise ValueError('用户必须提供用户名')
        if not password:
            raise ValueError('用户必须提供密码')

        email = self.normalize_email(email)
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
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')

        return self.create_user(username, password, email, **extra_fields)


class User(AbstractBaseUser):
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
        unique=True,
        error_messages={
            'unique': _("该邮箱地址已被占用。"),
        },
    )
    avatar = models.ImageField(
        _('头像'),
        upload_to='avatars/',
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
    favorite_count = models.IntegerField(_('收藏文章数'), default=0)

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

    # 获取用户的所有订阅
    def get_user_subscriptions(self, user):
        return self.filter(user=user).select_related('public_account')
    
    # 检测用户是否订阅了某个公众号
    def is_subscribed(self, user, public_account): 
        return self.filter(user=user, public_account=public_account).exists()
    
    # 创建订阅并更新用户的订阅计数
    def create_subscription(self, user, public_account):
        subscription = self.create(user=user, public_account=public_account)
        return subscription
    
    # 删除订阅并更新用户的订阅计数
    def delete_subscription(self, subscription):
        subscription.delete()


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
    subscribe_at = models.DateTimeField(
        auto_now_add=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('user', 'public_account')]  # 防止重复订阅
        ordering = ['-subscribe_at']  # 按照订阅创建顺序排列，最新创建的订阅在前面

    def __str__(self):
        return f"{self.user} -> {self.public_account}"
    

class FavoriteManager(models.Manager):
    """自定义收藏管理器"""

    # 获取用户的所有收藏
    def get_user_favorites(self, user):
        return self.filter(user=user).select_related('article')
    
    # 检测用户是否收藏了某篇文章
    def is_favorited(self, user, article): 
        return self.filter(user=user, article=article).exists()
    
    # 创建收藏并更新用户的收藏计数
    def create_favorite(self, user, article):
        favorite = self.create(user=user, article=article)
        return favorite
    
    # 删除收藏并更新用户的收藏计数
    def delete_favorite(self, favorite):
        favorite.delete()

class Favorite(models.Model):
    """
    用户收藏的文章
    图例：用户A-收藏-文章A
    当用户/文章删除时，收藏记录自动删除
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
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

    def __str__(self):
        return f"{self.user} favorited {self.article}"