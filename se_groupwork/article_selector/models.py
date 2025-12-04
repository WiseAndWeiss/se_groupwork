import json
import numpy as np
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from user.models import User, Subscription
from webspider.models import PublicAccount, Article
from remoteAI.remoteAI.tags import TAGS

# Create your models here.
class PreferenceManager(models.Manager):
    def output(self, outputfile=None, user=None):
        """
        输出数据到文件
        """
        table = []
        if user:
            preferences = self.get_user_preferences(user)
            table.append({
                'user': {
                    'id': preferences.user.id,
                    'username': preferences.user.username,
                },
                'account_preference': preferences.account_preference,
                'tag_preference': preferences.tag_preference,
                'keyword_preference': preferences.keyword_preference,
            })
        else:
            for preference in self.all():
                table.append({
                    'user': {
                        'id': preference.user.id,
                        'username': preference.user.username,
                    },
                    'account_preference': preference.account_preference,
                    'tag_preference': preference.tag_preference,
                    'keyword_preference': preference.keyword_preference,
                    # 'updated_at': preference.updated_at
                })
        if outputfile:
            with open(outputfile, 'w', encoding='utf-8') as f:
                json.dump(table, f, ensure_ascii=False, indent=4)
        else:
            print(json.dumps(table, ensure_ascii=False, indent=4))
        return True
            
    
    def get_user_preferences(self, user):
        """
        获取用户偏好
        :param user: 用户
        :return: 用户偏好
        """
        try:
            preferences = self.get(user=user)
        except Preference.DoesNotExist:
            preferences = self.add_user(user)
        return preferences


    def add_user(self, user, account_preference={}, tag_preference=[1/len(TAGS)]*len(TAGS), keyword_preference=[0.01]*100):
        """
        在偏好表中添加用户
        :param user: 用户
        :return: 用户偏好
        """
        try:
            preferences = self.get(user=user)
        except Preference.DoesNotExist:
            preferences = self.create(user=user, account_preference=account_preference, tag_preference=tag_preference, keyword_preference=keyword_preference)
        return preferences


    def update_preference_by_article(self, user, article, alpha=0.1):
        """
        根据用户行为更新用户偏好
        :param user: 用户
        :param article: 文章
        :param operation: 操作("browse", "favorite")
        :return: 用户偏好
        """
        item = self.get_user_preferences(user)
        # 更新公众号偏好
        account_id = str(article.public_account.id)
        if len(item.account_preference) == 0:
            item.account_preference = {account_id: 1}
        else:
            if account_id in item.account_preference:
                item.account_preference[account_id] *= (1 - alpha)
            else:
                item.account_preference[account_id] = 1/10
            tar = 1 - item.account_preference[account_id]
            cur = 0
            for id in list(item.account_preference.keys()):
                if item.account_preference[id] < 1/20:
                    del item.account_preference[id]
                else:
                    cur += item.account_preference[id]
            for id in list(item.account_preference.keys()):
                item.account_preference[id] = item.account_preference[id]/cur * tar
        # 更新标签偏好
        tags_vector = np.array(article.tags_vector)
        tag_preference_vector = np.array(item.tag_preference)
        if tags_vector.shape[0] == len(TAGS) and tag_preference_vector.shape[0] == len(TAGS):
            tag_preference_vector = (1 - alpha) * tag_preference_vector + alpha * tags_vector
            item.tag_preference = tag_preference_vector.tolist()
        # 更新关键词偏好
        semantic_vector = np.array(article.semantic_vector)
        keyword_preference_vector = np.array(item.keyword_preference)
        if semantic_vector.shape[0] == 100 and keyword_preference_vector.shape[0] == 100:
            keyword_preference_vector = (1 - alpha) * keyword_preference_vector + alpha* semantic_vector
            item.keyword_preference = keyword_preference_vector.tolist()
        item.save()
        return item

    def caculate_preference(self, user, article):
        score = 0
        preference = self.get_user_preferences(user)
        # 计算公众号偏好
        account_id = article.public_account.id
        if account_id in preference.account_preference:
            score += preference.account_preference[account_id]
        # 计算标签偏好
        tags = article.tags
        if "重大" in tags:  score += 0.5
        tags_vector = np.array(article.tags_vector)
        tag_preference_vector = np.array(preference.tag_preference)
        if tags_vector.shape[0] == len(TAGS) and tag_preference_vector.shape[0] == len(TAGS):
            score += np.dot(tags_vector, tag_preference_vector)
        # 计算关键词偏好
        semantic_vector = np.array(article.semantic_vector)
        keyword_preference_vector = np.array(preference.keyword_preference)
        if semantic_vector.shape[0] == 100 and keyword_preference_vector.shape[0] == 100:
            score += np.dot(semantic_vector, keyword_preference_vector)
        return score

class Preference(models.Model):
    """
    用户偏好表：存储用户对公众号、标签、关键词的偏好权重
    与用户是一对一关联（通过ForeignKey+unique实现，模拟OneToOneField）
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
        verbose_name="用户key"
    )
    account_preference = models.JSONField(
        default=dict,
        help_text='{"公众号id": 权重}',
        verbose_name="公众号偏好"
    )
    tag_preference = models.JSONField(
        default=list,
        help_text='16个标签的权重',
        verbose_name="标签偏好"
    )
    keyword_preference = models.JSONField(
        default=list,
        help_text='偏好向量',
        verbose_name="关键词偏好"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    objects = PreferenceManager()

    class Meta:
        verbose_name = "用户偏好"
        verbose_name_plural = "用户偏好"
        ordering = ['-updated_at']

