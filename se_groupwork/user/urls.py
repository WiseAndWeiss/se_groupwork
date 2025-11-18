from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'user'  # 命名空间，方便反向解析

urlpatterns = [
    # 认证相关
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 订阅管理
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # 收藏管理
    path('favorites/', views.FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/<int:pk>/', views.FavoriteDetailView.as_view(), name='favorite-detail'),
    
    # 浏览历史
    path('history/', views.HistoryListView.as_view(), name='history-list'),
    path('history/<int:pk>/', views.HistoryDetailView.as_view(), name='history-detail'),
    
    # 个人资料更新
    path('update/username/', views.UsernameUpdateView.as_view(), name='update-username'),
    path('update/avatar/', views.AvatarUpdateView.as_view(), name='update-avatar'),
    path('update/password/', views.PasswordChangeView.as_view(), name='update-password'),
    path('update/email/', views.EmailChangeView.as_view(), name='update-email'),
    path('update/phone/', views.PhoneChangeView.as_view(), name='update-phone'),
]