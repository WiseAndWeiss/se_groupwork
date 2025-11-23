from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from webspider.models import PublicAccount
from user.models import Subscription
from user.serializers import PublicAccountSerializer, SubscriptionSerializer
from article_selector.article_selector import get_customized_accounts
from webspider.webspider.biz_searcher import BizSearcher
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
        
        # 安全性：确保数据库中没有该公众号再去爬取，减少爬虫负担
        if PublicAccount.objects.filter(name=name).exists():
            return Response(
                {'error': '该公众号已存在'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

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