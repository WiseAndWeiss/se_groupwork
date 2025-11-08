import os
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import FavoriteSerializer, HistorySerializer, UserEmailChangeSerializer, UserPasswordChangeSerializer, UserPhoneChangeSerializer, UserRegistrationSerializer, UserLoginSerializer , UserProfileSerializer, SubscriptionSerializer
from user.models import User, Subscription, Favorite, History
from webspider.models import PublicAccount, Article


# 认证相关API
class RegisterView(APIView):
    """用户注册API"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """用户登录API"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    """用户资料API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


# 订阅相关API
class SubscriptionListView(APIView):
    """订阅列表API - 处理列表和创建操作"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户的所有订阅"""
        subscriptions = Subscription.objects.get_user_subscriptions(request.user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """创建新的订阅"""
        public_account_id = request.data.get('public_account_id')
        public_account = get_object_or_404(PublicAccount, pk=public_account_id)
        
        if Subscription.objects.is_subscribed(request.user, public_account):
            return Response({'error': '已经订阅过该公众号'}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = Subscription.objects.create_subscription(request.user, public_account)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request):
        """清空当前用户的所有订阅"""
        Subscription.objects.clear_user_subscriptions(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionDetailView(APIView):
    """订阅详情API - 处理单个订阅的操作"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        """删除特定的订阅"""
        subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
        Subscription.objects.delete_subscription(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)


# 收藏相关API
class FavoriteListView(APIView):
    """收藏列表API - 处理列表和创建操作"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户的所有收藏"""
        favorites = Favorite.objects.get_user_favorites(request.user)
        serializer = FavoriteSerializer(favorites, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """创建新的收藏"""
        article_id = request.data.get('article_id')
        article = get_object_or_404(Article, pk=article_id)
        
        if Favorite.objects.is_favorited(request.user, article):
            return Response({'error': '已经收藏过该文章'}, status=status.HTTP_400_BAD_REQUEST)
        
        favorite = Favorite.objects.create_favorite(request.user, article)
        serializer = FavoriteSerializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request):
        """清空当前用户的所有收藏"""
        Favorite.objects.clear_user_favorites(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteDetailView(APIView):
    """收藏详情API - 处理单个收藏的操作"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        """删除特定的收藏"""
        favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
        Favorite.objects.delete_favorite(favorite)
        return Response(status=status.HTTP_204_NO_CONTENT)


# 历史记录相关API
class HistoryListView(APIView):
    """历史记录列表API - 处理列表和创建操作"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户的所有浏览历史"""
        histories = History.objects.get_user_history(request.user)
        serializer = HistorySerializer(histories, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """创建或更新浏览历史记录"""
        article_id = request.data.get('article_id')
        article = get_object_or_404(Article, pk=article_id)
        
        history, created = History.objects.update_or_create(
            user=request.user,
            article=article,
            defaults={'viewed_at': timezone.now()}
        )
        
        serializer = HistorySerializer(history)
        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        """清空当前用户的所有历史记录"""
        History.objects.clear_user_history(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HistoryDetailView(APIView):
    """历史记录详情API - 处理单个历史记录的操作"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        """删除特定的历史记录"""
        history = get_object_or_404(History, pk=pk, user=request.user)
        History.objects.delete_history(history)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# 用户资料更新相关API
class UsernameUpdateView(APIView):
    """修改用户名API"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        """修改用户名"""
        new_username = request.data.get('new_username')
        
        if not new_username:
            return Response({'error': '新用户名不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查用户名是否已存在
        if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
            return Response({'error': '该用户名已被占用'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新用户名
        request.user.username = new_username
        request.user.save()
        
        # 返回更新后的用户信息
        serializer = UserProfileSerializer(request.user)
        return Response({
            'message': '用户名修改成功',
            'user': serializer.data
        })

class AvatarUpdateView(APIView):
    """修改头像API"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        """修改头像"""
        new_avatar = request.FILES.get('avatar')
        
        if not new_avatar:
            return Response({'error': '请选择头像文件'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查文件类型
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if new_avatar.content_type not in allowed_types:
            return Response({'error': '只支持JPEG、JPG、PNG和GIF格式的图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查文件大小（限制为10MB）
        if new_avatar.size > 10 * 1024 * 1024:
            return Response({'error': '头像文件大小不能超过10MB'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存旧头像路径用于后续删除
        old_avatar_path = None
        if request.user.avatar:
            old_avatar_path = request.user.avatar.path

        # 更新头像
        request.user.avatar = new_avatar
        request.user.save()

        # 删除旧头像文件（避免存储空间浪费）
        if old_avatar_path and os.path.exists(old_avatar_path):
            try:
                os.remove(old_avatar_path)
            except OSError:
                pass  # 如果删除失败，忽略错误
        
        # 返回更新后的用户信息
        serializer = UserProfileSerializer(request.user)
        return Response({
            'message': '头像修改成功',
            'user': serializer.data
        })

class PasswordChangeView(APIView):
    """修改密码API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """修改密码"""
        serializer = UserPasswordChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # 更新密码
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            # 更新会话认证哈希，防止用户被登出
            update_session_auth_hash(request, request.user)
            
            # 生成新的token
            refresh = RefreshToken.for_user(request.user)
            
            return Response({
                'message': '密码修改成功',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmailChangeView(APIView):
    """修改邮箱API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """修改邮箱"""
        serializer = UserEmailChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # 更新邮箱
            request.user.email = serializer.validated_data['new_email']
            request.user.save()
            
            # 返回更新后的用户信息
            serializer_response = UserProfileSerializer(request.user)
            return Response({
                'message': '邮箱修改成功',
                'user': serializer_response.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PhoneChangeView(APIView):
    """修改手机号API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """修改手机号"""
        serializer = UserPhoneChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # 更新手机号
            request.user.phone_number = serializer.validated_data['new_phone']
            request.user.save()
            
            # 返回更新后的用户信息
            serializer_response = UserProfileSerializer(request.user)
            return Response({
                'message': '手机号修改成功',
                'user': serializer_response.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
