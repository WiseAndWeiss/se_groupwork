from django.shortcuts import render
from rest_framework.views import APIView
import threading
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from webspider.models import PublicAccount, Article
from user.models import Subscription
from user.serializers import PublicAccountSerializer, SubscriptionSerializer
from article_selector.article_selector import get_customized_accounts
from article_selector.serializers import ArticleSerializer
from webspider.webspider.biz_searcher import BizSearcher

# 限制爬虫搜索并发，防止被封：每进程最多 3 个并发
BIZ_SEARCH_SEMAPHORE = threading.Semaphore(3)
# Create your views here.

# 公众号相关API
@extend_schema(
    tags=['公众号相关'],
    summary='获取校内公众号列表',
    description='',
    methods=['GET']
)
class CampusPublicAccountListView(APIView):
    """
    校内公众号获取API
    GET /api/public-accounts/campus/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取所有校内公众号"""
        campus_accounts = PublicAccount.objects.filter(is_default=True)
        serializer = PublicAccountSerializer(campus_accounts, many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema(
    tags=['公众号相关'],
    summary='在数据库里查询特定name的公众号',
    description='',
    methods=['GET'],
    parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                location=OpenApiParameter.QUERY,
                description="公众号名称",
                required=True,
                examples=[OpenApiExample(name="name", value="清华大学")]
            )
        ],
)
class SearchPublicAccountListView(APIView):
    """
    在数据库中查询符合query的公众号
    GET /api/public-accounts/search/?name=xxx
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取特定的公众号"""
        name = request.query_params.get('name', '').strip()

        if not name:
            return Response(
                {'error': '请提供公众号名称参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        accounts = PublicAccount.objects.filter(name__icontains=name)
        serializer = PublicAccountSerializer(accounts, many=True, context={'request': request})

        return Response({
            'count': accounts.count(),
            'public_accounts': serializer.data
        })
    

@extend_schema(
    tags=['公众号相关'],
    summary='利用爬虫寻找符合query的公众号',
    description='',
    methods=['GET'],
    parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                location=OpenApiParameter.QUERY,
                description="公众号名称",
                required=True,
                examples=[OpenApiExample(name="name", value="清华大学")]
            )
        ],
)
class SearchNewAccountListView(APIView):
    """
    通过爬虫获取符合query的公众号
    GET /api/new-accounts/search/?name=xxx
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取特定的公众号"""
        name = request.query_params.get('name', '').strip()

        if not name:
            return Response(
                {'error': '请提供公众号名称参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        acquired = BIZ_SEARCH_SEMAPHORE.acquire(blocking=False)
        if not acquired:
            return Response({'error': '接口繁忙，请稍后再试'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 安全性：确保数据库中没有该公众号再去爬取，减少爬虫负担
        try:
            if PublicAccount.objects.filter(name=name).exists():
                accounts = PublicAccount.objects.filter(name__icontains=name)
                serializer = PublicAccountSerializer(accounts, many=True, context={'request': request})
                return Response({
                    'count': accounts.count(),
                    'public_accounts': serializer.data
                })

            # 调用 BizSearcher 爬取公众号信息
            biz_searcher = BizSearcher(name)
            mp_dict = biz_searcher.biz_search()

            # 如果爬虫没有返回结果，返回空列表
            if not mp_dict:
                return Response([])

            # 从数据库中获取公众号信息
            accounts = PublicAccount.objects.filter(name__in=mp_dict.keys())
            serializer = PublicAccountSerializer(accounts, many=True, context={'request': request})

            return Response(serializer.data)
        finally:
            BIZ_SEARCH_SEMAPHORE.release()


@extend_schema(
    tags=['文章相关'],
    summary='根据文章ID获取文章详情',
    description='根据文章ID返回文章详情，包括正文内容',
    methods=['GET'],
    responses={
        200: ArticleSerializer,
        401: OpenApiResponse(description='未登录或登录失效'),
        404: OpenApiResponse(description='文章不存在')
    }
)
class ArticleDetailView(APIView):
    """根据文章ID返回文章详情"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        try:
            article = Article.objects.get(id=pk)
        except Article.DoesNotExist:
            return Response({'error': '文章不存在'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleSerializer(article, context={'request': request})
        return Response(serializer.data)