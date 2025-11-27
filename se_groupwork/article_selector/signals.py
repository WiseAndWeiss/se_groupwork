from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from article_selector.models import Preference
from user.models import User, Favorite, History, Subscription
from webspider.models import PublicAccount
from article_selector.article_selector import get_campus_accounts

@receiver(post_save, sender=User)
def init_user_preferences(sender, instance, created, **kwargs):
    if created:
        if Preference.objects.filter(user=instance).count() != 0:
            Preference.objects.filter(user=instance).delete()
        user = instance
        account_preference = {}
        campus_accounts = get_campus_accounts()
        for account in campus_accounts:
            account_preference[account.id] = 1/(len(campus_accounts))
        tag_preference = [0.0625]*16
        keyword_preference = [0.01]*100
        Preference.objects.create(user=user, account_preference=account_preference, tag_preference=tag_preference, keyword_preference=keyword_preference)


@receiver(post_delete, sender=User)
def delete_user_preferences(sender, instance, **kwargs):
    Preference.objects.filter(user=instance).delete()


@receiver(post_save, sender=History)
def update_preference_by_new_browse(sender, instance, created, **kwargs):
    user = instance.user
    article = instance.article
    Preference.objects.update_preference_by_article(user, article, alpha=0.1)


@receiver(post_save, sender=Favorite)
def update_preference_by_new_favorite(sender, instance, created, **kwargs):
    user = instance.user
    article = instance.article
    Preference.objects.update_preference_by_article(user, article, alpha=0.2)
