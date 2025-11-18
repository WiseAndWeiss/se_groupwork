import numpy as np
from article_selector.models import Preference
from webspider.models import Article, PublicAccount
from user.models import User, Subscription

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


def get_campus_accounts():
    accounts = PublicAccount.objects.filter(
        is_default=True
    )
    return list(accounts)

def get_customized_accounts(user):
    accounts = PublicAccount.objects.filter(
        subscription__user=user
    )
    return list(accounts)


def get_accounts_by_user(user):
    customized_accounts = get_customized_accounts(user)
    campus_accounts = get_campus_accounts()
    accounts = customized_accounts + campus_accounts
    accounts = list(set(accounts))
    return accounts


