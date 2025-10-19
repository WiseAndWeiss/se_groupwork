from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """自定义用户管理器"""

    def create_user(self, username, email, password=None, **extra_fields):
        """创建普通用户"""
        if not email:
            raise ValueError('用户必须提供邮箱地址')
        if not username:
            raise ValueError('用户必须提供用户名')

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        user.set_password(password)  # 加密密码
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')

        return self.create_user(username, email, password, **extra_fields)


class User(models.Model):
    """
    自定义用户模型
    - 储存用户的基本信息
    - 不直接存储订阅号信息（通过外键关系关联）
    """

    # 基本身份信息
    username = models.CharField(
        _('用户名'),
        max_length=150,
        unique=True,
        help_text=_('必填。150个字符或更少。只能包含字母、数字和 @/./+/-/_ 字符。'),
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

    # 个人信息
    nickname = models.CharField(
        _('昵称'),
        max_length=50,
        blank=True,
        help_text=_('用户的显示名称')
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

    # 状态标志
    is_active = models.BooleanField(
        _('活跃状态'),
        default=True,
        help_text=_('标记用户是否活跃。取消选中此项而不是删除用户。')
    )
    is_staff = models.BooleanField(
        _('员工状态'),
        default=False,
        help_text=_('标记用户是否可以登录到管理员站点。')
    )

    # 时间信息
    date_joined = models.DateTimeField(_('注册时间'), default=timezone.now)
    last_login = models.DateTimeField(_('最后登录'), blank=True, null=True)
    last_activity = models.DateTimeField(_('最后活动'), auto_now=True)

    # 统计信息
    article_read_count = models.IntegerField(_('阅读文章数'), default=0)
    subscription_count = models.IntegerField(_('订阅公众号数'), default=0)

    # 设置字段
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'  # 用作唯一标识的字段
    REQUIRED_FIELDS = ['email']  # 创建超级用户时需要提供的字段

    objects = UserManager()

    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-date_joined']

    def __str__(self):
        return self.nickname or self.username

    def get_full_name(self):
        """返回用户的完整名称（昵称或用户名）"""
        return self.nickname or self.username

    def get_short_name(self):
        """返回用户的简短名称"""
        return self.nickname or self.username

    def email_user(self, subject, message, from_email=None, **kwargs):
        """发送邮件给用户"""
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email], **kwargs)
