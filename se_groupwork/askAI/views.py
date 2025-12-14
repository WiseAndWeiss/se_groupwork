
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from askAI.serializers import ReferenceArticleSerializer

from askAI.askAI.ai_ask import ask_ai, get_reference_articles

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
        400: OpenApiResponse(description='参数错误')
    }
)
class AskView(APIView):
    def post(self, request):
        question = request.data.get('question')
        if not question:
            return Response({'error': '请输入问题'}, status=status.HTTP_400_BAD_REQUEST)
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
        