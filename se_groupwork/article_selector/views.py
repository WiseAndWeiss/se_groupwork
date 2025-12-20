from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Subquery, OuterRef
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

from datetime import timedelta
from django.utils import timezone

from webspider.models import Article, PublicAccount
from user.models import Subscription, Favorite
from article_selector.serializers import ArticleSerializer, ArticlesFilterSerializer
from article_selector.article_selector import *
from se_groupwork.global_tools import global_meili_tool_load

response_format = {
    200: OpenApiResponse(
        description="成功返回文章列表及是否到达末尾",
        examples=[
            OpenApiExample(
                name="返回文章列表",
                value={
                    "articles": [
                        {
                            "id": 1,
                            "title": "测试文章",
                            "summary": "文章摘要",
                            "publish_time": "2025-11-12T10:00:00+08:00",
                            "public_account": {"id": 1, "name": "测试公众号"}
                        }
                    ],
                    "reach_end": False
                }
            )
        ]
    ),
    400: OpenApiResponse(description="参数缺失或格式错误"),
    401: OpenApiResponse(description="未登录或登录失效"),
    404: OpenApiResponse(description="所查询对象不存在"),
}

@extend_schema(
    description="按时间、推荐或其他条件获取推文列表",
    tags=["文章推送"],
)
class ArticleViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _annotate_favorite(self, qs, user):
        favorite_subq = Favorite.objects.filter(user=user, article=OuterRef('pk')).values('id')[:1]
        return qs.annotate(is_favorited_id=Subquery(favorite_subq))

    def _base_queryset(self, accounts, user):
        # 只取列表用得到的字段，避免拉取大文本/向量，减少 I/O
        qs = (
            Article.objects.select_related('public_account')
            .only(
                'id', 'title', 'article_url', 'publish_time', 'cover',
                'summary', 'tags', 'key_info', 'relevant_time',
                'public_account__name', 'public_account_id'
            )
            .filter(public_account__in=accounts)
            .exclude(summary='')
        )
        return self._annotate_favorite(qs, user)

    @extend_schema(
        summary="获取最新文章列表",
        description="按发布时间倒序获取用户关联公众号的最新文章，支持分页加载（每次20条）",
        parameters=[
            OpenApiParameter(
                name="start_rank",
                type=int,
                location=OpenApiParameter.QUERY,
                description="起始偏移量（用于分页，默认0）",
                required=False,
                examples=[OpenApiExample(name="start_rank", value=0), OpenApiExample(name="start_rank", value=20)]
            )
        ],
        responses=response_format
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        获取最新文章列表
        GET /api/articles/latest/?start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        related_accounts = get_accounts_by_user(request.user)
        all_articles = self._base_queryset(related_accounts, request.user).order_by('-publish_time')[start_rank:start_rank+21]
        reached_end = len(all_articles) < 21
        all_articles = all_articles[:20]
        serializer = ArticleSerializer(all_articles, many=True, context={'request': request})
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })
    
    @extend_schema(
        summary="获取推荐文章列表",
        description="基于用户偏好推荐3天内的文章，固定返回最多8条",
        responses=response_format
    )
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """
        获取推荐文章列表（固定）
        GET /api/articles/recommended/
        """
        # 这里可以根据用户的阅读历史、偏好等进行推荐
        # 暂时返回固定的推荐文章
        related_accounts = get_accounts_by_user(request.user)
        recent_articles = (
            self._base_queryset(related_accounts, request.user)
            .filter(publish_time__gte=timezone.now() - timedelta(days=3))
            .order_by('-publish_time')[:200]  # 限制候选集大小，降低排序成本
        )
        recommended_articles = sort_articles_by_preference(request.user, recent_articles)[:8]
        serializer = ArticleSerializer(recommended_articles, many=True, context={'request': request})
        return Response({
            'articles': serializer.data,
            'reach_end': True
        })

    @extend_schema(
        summary="获取最新校内咨询文章",
        description="按发布时间倒序获取默认公众号的最新文章，支持分页加载（每次20条）",
        parameters=[
            OpenApiParameter(
                name="start_rank",
                type=int,
                location=OpenApiParameter.QUERY,
                description="起始偏移量（用于分页，默认0）",
                required=False,
                examples=[OpenApiExample(name="start_rank", value=0), OpenApiExample(name="start_rank", value=20)]
            )
        ],
        responses=response_format
    )
    @action(detail=False, methods=['get'])
    def campus_latest(self, request):
        """
        获取最新校内咨询文章列表
        GET /api/articles/campus-latest/?start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        campus_accounts = get_campus_accounts()
        campus_articles = self._base_queryset(campus_accounts, request.user).order_by('-publish_time')[start_rank:start_rank+21]
        reached_end = len(campus_articles) < 21
        campus_articles = campus_articles[:20]
        serializer = ArticleSerializer(campus_articles, many=True, context={'request': request})
        return Response({
            'start_rank': start_rank,
            'articles': serializer.data,
            'reach_end': reached_end
        })
    
    @extend_schema(
        summary="获取最新自选咨询文章",
        description="按发布时间倒序获取自选公众号的最新文章，支持分页加载（每次20条）",
        parameters=[
            OpenApiParameter(
                name="start_rank",
                type=int,
                location=OpenApiParameter.QUERY,
                description="起始偏移量（用于分页，默认0）",
                required=False,
                examples=[OpenApiExample(name="start_rank", value=0), OpenApiExample(name="start_rank", value=20)]
            )
        ],
        responses=response_format
    )
    @action(detail=False, methods=['get'])
    def customized_latest(self, request):
        """
        获取最新自选咨询文章列表
        GET /api/articles/customized-latest/?start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        # 根据用户的自选偏好获取文章
        customized_accounts = get_customized_accounts(request.user)
        customized_articles = self._base_queryset(customized_accounts, request.user).order_by('-publish_time')[start_rank:start_rank+21]
        reached_end = len(customized_articles) < 21
        customized_articles = customized_articles[:20]
        serializer = ArticleSerializer(customized_articles, many=True, context={'request': request})
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })
    
    @extend_schema(
        summary="搜索最新自选咨询文章",
        description="按发布时间倒序获取自选公众号的最新文章，支持分页加载（每次20条）",
        parameters=[
            OpenApiParameter(
                name="start_rank",
                type=int,
                location=OpenApiParameter.QUERY,
                description="起始偏移量（用于分页，默认0）",
                required=False,
                examples=[OpenApiExample(name="start_rank", value=0), OpenApiExample(name="start_rank", value=20)]
            ),
            OpenApiParameter(
                name="search_content",
                type=str,
                location=OpenApiParameter.QUERY,
                description="搜索内容",
                required=False,
                examples=[OpenApiExample(name="search_content", value="清华")]
            )
        ],
        responses=response_format
    )
    @action(detail=False, methods=['get'])
    def search_customized_latest(self, request):
        """
        获取最新自选咨询文章列表
        GET /api/articles/customized-latest/search/?start_rank=0&name=..
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        search_content = request.query_params.get('search_content', '').strip()

        # 根据用户的自选偏好获取文章
        customized_accounts = get_customized_accounts(request.user)

        # 基础查询：自选公众号且排除空summary
        base_query = self._base_queryset(customized_accounts, request.user)

        # 如果有搜索内容，添加搜索条件（多字段模糊搜索）
        if search_content:
            base_query = base_query.filter(
                Q(summary__icontains=search_content) |
                Q(title__icontains=search_content) |
                Q(content__icontains=search_content)
            )

        customized_articles = base_query.order_by('-publish_time')[start_rank:start_rank+21]
        reached_end = len(customized_articles) < 21
        customized_articles = customized_articles[:20]
        serializer = ArticleSerializer(customized_articles, many=True, context={'request': request})
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })
    
    @extend_schema(
        summary="获取指定公众号的最新文章",
        description="按发布时间倒序获取单个公众号的文章，支持分页加载（每次20条）",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=str,
                location=OpenApiParameter.QUERY,
                description="公众号ID（必填）",
                required=True,
                examples=[OpenApiExample(name="account_id", value="123")]
            ),
            OpenApiParameter(
                name="start_rank",
                type=int,
                location=OpenApiParameter.QUERY,
                description="起始偏移量（用于分页，默认0）",
                required=False,
                examples=[OpenApiExample(name="start_rank", value=0)]
            )
        ],
        responses=response_format
    )
    @action(detail=False, methods=['get'])
    def by_account(self, request):
        """
        获取指定公众号最新文章列表
        GET /api/articles/by-account/?account_id=xxx&start_rank=0
        """
        start_rank = int(request.query_params.get('start_rank', 0))
        account_id = request.query_params.get('account_id')
        try:
            account_articles = self._base_queryset([account_id], request.user).filter(public_account_id=account_id).order_by('-publish_time')[start_rank:start_rank+21]
            reached_end = len(account_articles) < 21
            account_articles = account_articles[:20]
            serializer = ArticleSerializer(account_articles, many=True, context={'request': request})
            return Response({
                'articles': serializer.data,
                'reach_end': reached_end
            })
        except PublicAccount.DoesNotExist:
            return Response(
                {'error': '公众号不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="按条件筛选文章",
        description="支持按公众号、日期范围、标签、内容搜索等条件筛选文章，支持分页加载",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "account_names": {
                        "type": "string",
                        "description": "公众号名称"
                    },
                    "range": {
                        "choices": ["a", "d", "c"],
                        "description": "筛选范围：a-all全部, d-default默认，c-custom自选"
                    },
                    "date_from": {
                        "type": "string",
                        "format": "date-time",
                        "description": "开始日期（包含，格式：YYYY-MM-DD，可选）"
                    },
                    "date_to": {
                        "type": "string",
                        "format": "date-time",
                        "description": "结束日期（不包含，格式：YYYY-MM-DD，可选）"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签列表（可选，匹配包含任一标签的文章）"
                    },
                    "search_content": {
                        "type": "string",
                        "description": "搜索内容（可选）"
                    },
                    "start_rank": {
                        "type": "integer",
                        "description": "起始偏移量（默认0）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "每页条数（默认20）"
                    }
                },
                "examples": [
                    {
                        "date_from": "2025-11-01T00:00:00+08:00",
                        "tags": ["通知", "活动"],
                        "start_rank": 0
                    }
                ]
            }
        },
        responses=response_format
    )
    @action(detail=False, methods=['post'])
    def filter(self, request):
        """
        指定筛选条件获取文章列表
        POST /api/articles/filter/
        """
        serializer = ArticlesFilterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        data = serializer.validated_data
        queryset = None

        range = data.get('range')
        if range == 'a':
            all_accounts = get_accounts_by_user(request.user)
        elif range == 'd':
            all_accounts = get_campus_accounts()
        else:
            all_accounts = get_customized_accounts(request.user)

        account_names = data.get('account_names')
        if account_names:
            account_list = PublicAccount.objects.filter(name__in=account_names)
            if len(account_list) == 0:
                return Response(
                    {'error': '公众号不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            account_list = all_accounts
        queryset = self._base_queryset(account_list, request.user)
        
        date_from = data.get('date_from')
        if date_from:
            queryset = queryset.filter(publish_time__gte=date_from)
            
        date_to = data.get('date_to')
        if date_to:
            date_to_next = date_to + timedelta(days=1)
            queryset = queryset.filter(publish_time__lt=date_to_next.strftime('%Y-%m-%d'))

        
        tags = data.get('tags')
        if tags:
            tag_query = Q()
            for tag in tags:
                tag_query |= Q(tags__contains=tag)
            queryset = queryset.filter(tag_query)

        search_content = data.get('search_content')
        if search_content:  # 筛选逻辑：如果关键词在标题/摘要/内容中出现，则将其返回
            try:
                meilitools = global_meili_tool_load()
                search_result_ids = meilitools.search_articles(search_content)
                queryset = queryset.filter(id__in=search_result_ids)
            except Exception:
                search_query = Q()
                for field in ['title', 'summary', 'content']:
                    search_query |= Q(**{f'{field}__icontains': search_content})
                queryset = queryset.filter(search_query)


        if len(queryset) == 0 or queryset is None:
            return Response(
                {'error': '没有找到符合条件的文章'},
                status=status.HTTP_404_NOT_FOUND
            )

        start_rank = data.get('start_rank', 0)
        limit = data.get('limit', 21)
        queryset = queryset.order_by('-publish_time')[start_rank:start_rank+limit+1]

        reached_end = len(queryset) < limit
        queryset = queryset[:limit]
        serializer = ArticleSerializer(queryset, many=True, context={'request': request})
        return Response({
            'articles': serializer.data,
            'reach_end': reached_end
        })