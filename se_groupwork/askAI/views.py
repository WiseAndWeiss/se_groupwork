
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import StreamingHttpResponse
import json
import threading

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from askAI.serializers import ReferenceArticleSerializer

from askAI.askAI.ai_ask import ask_ai, get_reference_articles

# 限制并发：最多同时处理3个AI问答请求（每个进程）
ASK_CONCURRENCY_SEMAPHORE = threading.Semaphore(3)

# Create your views here.
@extend_schema(
    tags=['智能体'],
    summary='询问',
    description='向AI智能体提问，基于推送知识库回答问题',
    methods=['POST'],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "问题"
                }
            }
        }
    },
    responses={
        200: OpenApiResponse(description='成功', examples={
            "application/json": {
                "question": "今天天气怎么样？",
                "answer": "今天天气晴朗，温度适宜。",
                "references-articles":[
                    {
                        "id": 1,
                        "title": "今日天气预报",
                        "article_url": "https://example.com/article/1"
                    }
                ]
            }
        }),
        400: OpenApiResponse(description='参数错误'),
        503: OpenApiResponse(description='接口繁忙')
    }
)
class AskView(APIView):
    def post(self, request):
        # 并发保护：超过并发上限时直接拒绝
        acquired = ASK_CONCURRENCY_SEMAPHORE.acquire(blocking=False)
        if not acquired:
            return Response({'error': '接口繁忙，请稍后再试'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        question = request.data.get('question')
        if not question:
            ASK_CONCURRENCY_SEMAPHORE.release()
            return Response({'error': '请输入问题'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reference_articles = get_reference_articles(question)
            if not reference_articles:
                return Response({
                    "question": question,
                    "answer": "抱歉，没有找到与该问题相关的文章",
                    "references-articles": []
                })
            contents = [article.content for article in reference_articles]
            full_response = ''
            for chunk in ask_ai(question, contents):
                full_response += chunk
            reference = ReferenceArticleSerializer(reference_articles, many=True).data
            return Response({
                "question": question,
                "answer": full_response,
                "references-articles": reference
            })
        finally:
            ASK_CONCURRENCY_SEMAPHORE.release()


@extend_schema(
    tags=['智能体'],
    summary='询问（流式）',
    description='流式返回回答内容，末尾附带参考文章元数据（[[REFERENCES]] JSON）',
    methods=['POST'],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "问题"
                }
            }
        }
    },
    responses={
        200: OpenApiResponse(description='成功（流式文本）'),
        400: OpenApiResponse(description='参数错误'),
        503: OpenApiResponse(description='接口繁忙')
    }
)
class AskStreamView(APIView):
    def post(self, request):
        acquired = ASK_CONCURRENCY_SEMAPHORE.acquire(blocking=False)
        if not acquired:
            return Response({'error': '接口繁忙，请稍后再试'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        question = request.data.get('question')
        if not question:
            ASK_CONCURRENCY_SEMAPHORE.release()
            return Response({'error': '请输入问题'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reference_articles = get_reference_articles(question)
            references_data = ReferenceArticleSerializer(reference_articles, many=True).data if reference_articles else []

            def stream():
                try:
                    contents = [article.content for article in reference_articles] if reference_articles else []
                    if not contents:
                        yield "抱歉，没有找到与该问题相关的文章\n"
                    else:
                        for chunk in ask_ai(question, contents):
                            yield chunk
                    # 附带参考文章元数据，前端可解析
                    if references_data:
                        yield "\n[[REFERENCES]] " + json.dumps(references_data, ensure_ascii=False)
                finally:
                    ASK_CONCURRENCY_SEMAPHORE.release()

            return StreamingHttpResponse(stream(), content_type="text/plain; charset=utf-8")
        except Exception:
            ASK_CONCURRENCY_SEMAPHORE.release()
            raise
        