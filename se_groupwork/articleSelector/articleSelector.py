import numpy as np
from articleSelector.models import Preference
from webspider.models import Article, PublicAccount
from user.models import User
# 多处定义，请勿修改

def sort_articles_by_preference(user, articles):
    unsorted_articles = []
    for article in articles:
        unsorted_articles.append({
            "title": article.title,
            "article": article,
            "score": Preference.objects.caculate_preference(user, article)
        })
    sorted_articles = sorted(unsorted_articles, key=lambda x: x["score"], reverse=True)
    sorted_articles = [article["article"] for article in sorted_articles]
    return sorted_articles

