from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'webspider'  # 命名空间，方便反向解析

urlpatterns = [
     # 公众号相关
    path('public-accounts/campus/', views.CampusPublicAccountListView.as_view(), name='campus-public-accounts'),
    path('public-accounts/search/', views.SearchPublicAccountListView.as_view(), name='search-public-accounts'),
]
