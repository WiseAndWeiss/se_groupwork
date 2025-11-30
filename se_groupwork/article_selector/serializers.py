from rest_framework import serializers
from webspider.models import Article
from user.models import Favorite

class ArticleSerializer(serializers.ModelSerializer):
    account_name = serializers.ReadOnlyField(source='public_account.name')
    is_favorited = serializers.SerializerMethodField()  
    publish_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'account_name',
            'article_url',
            'publish_time',
            'cover',
            'summary',
            'tags',
            'key_info',
            'is_favorited'
        ]

    def get_is_favorited(self, obj):
        """判断当前用户是否收藏了该文章"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            favorite = Favorite.objects.filter(
                user=request.user, 
                article=obj
            ).first()  # 使用first()获取第一个匹配的记录
            return favorite.id if favorite else 0
        return 0


class ArticlesFilterSerializer(serializers.Serializer):
    start_rank = serializers.IntegerField(default=0, min_value=0)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=50)
    range = serializers.ChoiceField(choices=['a','d','c'], default='a', help_text='公众号范围:a-all、d-default、c-custom')
    accounts_id = serializers.ListField(child=serializers.IntegerField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    date_from = serializers.DateField(required=False, format="%Y-%m-%dT%H:%M:%S.%f%z")
    date_to = serializers.DateField(required=False, format="%Y-%m-%dT%H:%M:%S.%f%z")
    search_content = serializers.CharField(required=False)