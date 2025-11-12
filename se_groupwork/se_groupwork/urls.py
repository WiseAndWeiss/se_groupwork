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
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
import user.views as user_views
from article_selector.views import ArticleViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    # 用户管理API
    path('api/user/', include('user.urls')),

    # 修改个人资料相关
    path('api/auth/update/username/', user_views.UsernameUpdateView.as_view(), name='update-username'),
    path('api/auth/update/avatar/', user_views.AvatarUpdateView.as_view(), name='update-avatar'),
    path('api/auth/update/password/', user_views.PasswordChangeView.as_view(), name='update-password'),
    path('api/auth/update/email/', user_views.EmailChangeView.as_view(), name='update-email'),
    path('api/auth/update/phone/', user_views.PhoneChangeView.as_view(), name='update-phone'),
	
    # 文章相关
    path('api/articles/latest/', ArticleViewSet.as_view({'get': 'latest'}), name='articles-latest'),
    path('api/articles/recommended/', ArticleViewSet.as_view({'get': 'recommended'}), name='articles-recommended'),
	path('api/articles/campus-latest/', ArticleViewSet.as_view({'get': 'campus_latest'}), name='articles-campus-latest'),
	path('api/articles/customized-latest/', ArticleViewSet.as_view({'get': 'customized_latest'}), name='articles-customized-latest'),
	path('api/articles/by-account/', ArticleViewSet.as_view({'get': 'by_account'}), name='articles-by-account'),
    path('api/articles/filter/', ArticleViewSet.as_view({'post': 'filter'}), name='articles-filter'),
	
    # API文档
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
