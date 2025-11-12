from rest_framework import serializers
from webspider.models import Article

class ArticleSerializer(serializers.ModelSerializer):
    account_name = serializers.ReadOnlyField(source='public_account.name')
    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'account_name',
            'article_url',
            'publish_time',
            'cover_url',
            'summary',
            'tags',
            'key_info'
        ]


class ArticlesFilterSerializer(serializers.Serializer):
    start_rank = serializers.IntegerField(default=0, min_value=0)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=50)
    # 可以根据需要添加更多筛选字段
    accounts_id = serializers.ListField(child=serializers.IntegerField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    date_from = serializers.DateField(required=False, format="%Y-%m-%dT%H:%M:%S.%f%z")
    date_to = serializers.DateField(required=False, format="%Y-%m-%dT%H:%M:%S.%f%z")
    search_content = serializers.CharField(required=False)