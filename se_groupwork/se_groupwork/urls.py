"""
URL configuration for se_groupwork project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
import user.views as user_views

urlpatterns = [
    # 认证相关
    path('api/auth/register/', user_views.RegisterView.as_view(), name='register'),
    path('api/auth/login/', user_views.LoginView.as_view(), name='login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', user_views.ProfileView.as_view(), name='profile'),
    
    # 订阅相关 - RESTful风格
    path('api/subscriptions/', user_views.SubscriptionListView.as_view(), name='subscription-list'),
    path('api/subscriptions/<int:pk>/', user_views.SubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # 收藏相关 - RESTful风格
    path('api/favorites/', user_views.FavoriteListView.as_view(), name='favorite-list'),
    path('api/favorites/<int:pk>/', user_views.FavoriteDetailView.as_view(), name='favorite-detail'),
    
    # 历史记录相关 - RESTful风格
    path('api/history/', user_views.HistoryListView.as_view(), name='history-list'),
    path('api/history/<int:pk>/', user_views.HistoryDetailView.as_view(), name='history-detail'),
]
