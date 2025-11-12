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


@receiver(post_save, sender=PublicAccount)
def update_preference_by_new_default_account(sender, instance, created, **kwargs):
    if created:
        account = instance
        # TODO: 等待默认字段完善
        # if account.is_default:
        if "清华大学" in account.name:
            for pref in Preference.objects.all():
                if account.id not in pref.account_preference:
                    lenth = len(pref.account_preference)
                    for id in pref.account_preference:
                        pref.account_preference[id] *= (1 - 1/(lenth + 1))
                    pref.account_preference[account.id] = 1/(lenth + 1)
                    pref.save()


@receiver(post_delete, sender=PublicAccount)
def update_preference_by_delete_default_account(sender, instance, **kwargs):
    account = instance
    # TODO: 等待默认字段完善
    # if account.is_default:
    if "清华大学" in account.name:
        for pref in Preference.objects.all():
            if account.id in pref.account_preference:
                cur_aprefer_value = pref.account_preference[account.id]
                for id in pref.account_preference:
                    pref.account_preference[id] *= (1 + cur_aprefer_value/(1 - cur_aprefer_value))
                del pref.account_preference[account.id]
                pref.save()


@receiver(post_save, sender=Subscription)
def update_preference_by_new_subscription(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        account = instance.public_account
        preference = Preference.objects.get(user=user)
        account_preference = preference.account_preference
        if account.id not in account_preference:
            lenth = len(account_preference)
            for id in account_preference:
                account_preference[id] *= (1 - 1/(lenth + 1))
            account_preference[account.id] = 1/(lenth + 1)
            preference.account_preference = account_preference
            preference.save()
        else:
            # TODO: 日志警告
            print("Error: Already have such subscription in preference but create")
            pass


@receiver(post_delete, sender=Subscription)
def update_preference_by_delete_subscription(sender, instance, **kwargs):
    user = instance.user
    account = instance.public_account
    preference = Preference.objects.get(user=user)
    account_preference = preference.account_preference
    if account.id in account_preference:
        cur_aprefer_value = account_preference[account.id]
        for id in account_preference:
            account_preference[id] *= (1 + cur_aprefer_value/(1 - cur_aprefer_value))
        del account_preference[account.id]
        preference.account_preference = account_preference
        preference.save()
    else:
        # TODO: 日志警告
        print('Error: No such subscription in preference but delete')
        pass


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
