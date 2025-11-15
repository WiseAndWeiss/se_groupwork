from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Subscription, Favorite, History
from webspider.models import PublicAccount, Article
from .param_validate import validate_credentials, check_password_strength, check_phone_number

class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器
    - 处理用户注册时的数据验证和用户创建
    - 包含密码确认字段，确保两次输入一致
    """
    password = serializers.CharField(write_only=True)  # 密码字段，只用于写入不返回
    password_confirm = serializers.CharField(write_only=True)  # 密码确认字段，只用于写入

    class Meta:
        model = User  # 指定关联的Django模型
        fields = ['username', 'email', 'password', 'password_confirm', 'avatar', 'bio']  # 序列化器包含的字段

    def validate(self, data):
        # 1. 检查密码一致性
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("两次密码不一致")
        
        # 2. 调用检验函数
        validation_result = validate_credentials(data['username'], data['password'])
        
        if not validation_result['is_valid']:
            errors = []
            errors.extend(validation_result['username_errors'])
            errors.extend(validation_result['password_errors'])
            raise serializers.ValidationError("；".join(errors))
        
        return data

    def create(self, validated_data):
        """创建用户实例
        - 移除密码确认字段（模型中没有此字段）
        - 使用UserManager的create_user方法创建用户
        - 返回新创建的用户对象
        """
        validated_data.pop('password_confirm')  # 移除密码确认字段，避免保存到数据库时报错
        # 创建新用户，记录用户名、密码
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user  # 返回新创建的用户对象

class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器
    - 处理用户登录认证
    - 验证用户名和密码是否正确
    """
    username = serializers.CharField()  # 用户名字段
    password = serializers.CharField()  # 密码字段

    def validate(self, data):
        """登录验证方法
        - 检查用户名和密码是否提供
        - 使用Django的authenticate方法验证用户凭证
        - 检查用户账户是否活跃
        """
        username = data.get('username')  # 获取用户名
        password = data.get('password')  # 获取密码
        
        if username and password:  
            # 使用Django认证系统验证用户
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('用户名或密码错误')  # 认证失败
            if not user.is_active:
                raise serializers.ValidationError('用户账户已禁用')  # 账户被禁用
        else:
            raise serializers.ValidationError('必须提供用户名和密码')  # 缺少必要字段
        
        data['user'] = user  # 将用户对象添加到验证数据中
        return data  # 返回包含用户对象的验证数据

class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器
    - 用于序列化用户个人信息
    - 包含用户的基本信息和统计信息
    """
    class Meta:
        model = User  # 关联用户模型
        fields = ['id', 'username', 'email', 'phone_number', 'avatar', 'bio', 
                 'subscription_count', 'favorite_count', 'history_count',
                 'date_joined']  # 包含的用户信息字段

class PublicAccountSerializer(serializers.ModelSerializer):
    """公众号序列化器
    - 用于序列化公众号信息
    - 包含公众号的所有字段
    """
    class Meta:
        model = PublicAccount  # 关联公众号模型
        fields = '__all__'  # 包含所有字段

class ArticleSerializer(serializers.ModelSerializer):
    """文章序列化器
    - 用于序列化文章信息
    - 包含文章的所有字段
    """
    class Meta:
        model = Article  # 关联文章模型
        fields = ['id', 'title', 'author', 'article_url', 'publish_time', 'cover_url', 'summary']   # 包含的字段

class SubscriptionSerializer(serializers.ModelSerializer):
    """订阅关系序列化器
    - 用于序列化用户订阅公众号的关系
    - 包含订阅信息和关联的公众号详情
    """
    public_account = PublicAccountSerializer(read_only=True)  # 嵌套序列化公众号信息，只读
    
    class Meta:
        model = Subscription  # 关联订阅模型
        fields = ['id', 'public_account', 'subscribe_at', 'is_active']  # 包含的订阅信息字段

class FavoriteSerializer(serializers.ModelSerializer):
    """收藏序列化器
    - 用于序列化用户收藏文章的关系
    - 包含收藏信息和关联的文章详情
    """
    article = ArticleSerializer(read_only=True)  # 嵌套序列化文章信息，只读
    
    class Meta:
        model = Favorite  # 关联收藏模型
        fields = ['id', 'article', 'favorited_at']  # 包含的收藏信息字段

class HistorySerializer(serializers.ModelSerializer):
    """浏览历史序列化器
    - 用于序列化用户浏览文章的历史记录
    - 包含浏览历史和关联的文章详情
    """
    article = ArticleSerializer(read_only=True)  # 嵌套序列化文章信息，只读
    
    class Meta:
        model = History  # 关联历史模型
        fields = ['id', 'article', 'viewed_at']  # 包含的历史信息字段

# 修改个人资料相关的序列化器
class UserPasswordChangeSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        """验证旧密码是否正确"""
        user = self.context['request'].user
        if not authenticate(username=user.username, password=value):
            raise serializers.ValidationError("旧密码不正确")
        return value
    
    def validate(self, data):
        """验证新密码和确认密码是否一致"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("两次输入的新密码不一致")
        return data
    
    def validate_new_password(self, value):
        """验证新密码强度"""
        result = check_password_strength(value)
        if result['strength'] == 'weak':
            raise serializers.ValidationError(result['suggestion'])
        return value
    
class UserEmailChangeSerializer(serializers.Serializer):
    """修改邮箱序列化器"""
    new_email = serializers.EmailField()
    
    def validate_new_email(self, value):
        """这里不需要验证邮箱格式，因为django内置了检验"""
        """验证新邮箱是否已被使用"""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("该邮箱已被使用")
        return value

class UserPhoneChangeSerializer(serializers.Serializer):
    """修改手机号序列化器"""
    new_phone = serializers.CharField()
    
    def validate_new_phone(self, value):
        """验证新手机号格式是否正确"""
        validated, reason = check_phone_number(value)
        if not validated:
            raise serializers.ValidationError(reason)
        
        """验证新手机是否已被使用"""
        user = self.context['request'].user
        if User.objects.filter(phone_number=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("该手机号已被使用")
        return value