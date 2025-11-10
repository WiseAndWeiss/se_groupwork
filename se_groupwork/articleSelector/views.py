from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from datetime import timedelta
from django.utils import timezone

from webspider.models import Article, PublicAccount
from user.models import Subscription
from articleSelector.serializers import ArticleSerializer, ArticlesFilterSerializer
from articleSelector.articleSelector import *

class ArticleViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        获取最新文章列表
        GET /api/articles/latest/?start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        related_accounts = get_accounts_by_user(request.user)
        all_articles = Article.objects.filter(
            public_account__in = related_accounts,
            summary__ne = ''
        ).order_by('-publish_date')[start_rank:start_rank+21]
        reached_end = len(all_articles) < 21
        all_articles = all_articles[:20]
        serializer = ArticleSerializer(all_articles, many=True)
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """
        获取推荐文章列表（固定）
        GET /api/articles/recommended/
        """
        # 这里可以根据用户的阅读历史、偏好等进行推荐
        # 暂时返回固定的推荐文章
        related_accounts = get_accounts_by_user(request.user)
        recent_articles = Article.objects.filter(
            public_account__in=related_accounts,
            summary__ne = '',
            publish_time__gte=timezone.now() - timedelta(days=3)
        )
        recommended_articles = sort_articles_by_preference(request.user, recent_articles)[:8]
        serializer = ArticleSerializer(recommended_articles, many=True)
        return Response({
            'articles': serializer.data,
            'reach_end': True
        })
    
    @action(detail=False, methods=['get'])
    def campus_latest(self, request):
        """
        获取最新校内咨询文章列表
        GET /api/articles/campus-latest/?start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        campus_accounts = get_campus_accounts()
        campus_articles = Article.objects.filter(
            public_account__in=campus_accounts,
            summary__ne = ''
        ).order_by('-publish_date')[start_rank:start_rank+21]
        reached_end = len(campus_articles) < 21
        campus_articles = campus_articles[:20]
        serializer = ArticleSerializer(campus_articles, many=True)
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })
    
    @action(detail=False, methods=['get'])
    def customized_latest(self, request):
        """
        获取最新自选咨询文章列表
        GET /api/articles/customized-latest/?start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        # 根据用户的自选偏好获取文章
        customized_accounts = get_customized_accounts(request.user)
        customized_articles = Article.objects.filter(
            public_account__in=customized_accounts,
            summary__ne = ''
        ).order_by('-publish_date')[start_rank:start_rank+21]
        reached_end = len(customized_articles) < 21
        customized_articles = customized_articles[:20]
        serializer = ArticleSerializer(customized_articles, many=True)
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })
    
    @action(detail=False, methods=['get'])
    def by_account(self, request):
        """
        获取指定公众号最新文章列表
        GET /api/articles/by-account/?account_id=xxx&start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        account_id = request.query_params.get('account_id')
        try:
            account_articles = Article.objects.filter(
                public_account_id=account_id,
                summary__ne = ''
            ).order_by('-publish_date')[start_rank:start_rank+21]
            reached_end = len(account_articles) < 21
            account_articles = account_articles[:20]
            serializer = ArticleSerializer(account_articles, many=True)
            return Response({
                'articles': serializer.data,
                'reach_end': reached_end
            })
        except PublicAccount.DoesNotExist:
            return Response(
                {'error': '公众号不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def filtered(self, request):
        """
        指定筛选条件获取文章列表
        POST /api/articles/filtered/
        """
        serializer = ArticlesFilterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        data = serializer.validated_data
        queryset = None
        
        accounts_id = data.get('accounts_id')
        if accounts_id:
            account_list = PublicAccount.objects.filter(id__in=accounts_id)
        else:
            account_list = get_accounts_by_user(request.user)
        queryset = Article.objects.filter(
            public_account__in=account_list,
            summary__ne = ''
        )
        
        date_from = data.get('date_from')
        if date_from:
            queryset = queryset.filter(publish_date__gte=date_from)
        date_to = data.get('date_to')
        if date_to:
            queryset = queryset.filter(publish_date__lte=date_to)
        
        tags = data.get('tags')
        if tags:
            tag_query = Q()
            for tag in tags:
                tag_query |= Q(tags__contains=tag)
            queryset = queryset.filter(tag_query)

        search_content = data.get('search_content')
        if search_content:
            # TODO: 实现搜索功能
            pass

        start_rank = data.get('start_rank', 0)
        limit = data.get('limit', 21)
        queryset = queryset.order_by('-publish_date')[start_rank:start_rank+limit+1]

        reached_end = len(queryset) < limit
        queryset = queryset[:limit]
        serializer = ArticleSerializer(queryset, many=True)
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })