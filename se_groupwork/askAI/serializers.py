from rest_framework import serializers
from webspider.models import Article

class ReferenceArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'article_url'
        ]