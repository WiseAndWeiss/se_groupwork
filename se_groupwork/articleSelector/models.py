import json
import numpy as np
from django.db import models
from django.conf import settings
from user.models import User, Subscription
from webspider.models import PublicAccount, Article

TAGS_DICT = {
    "文娱活动":     np.array([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
    "学术讲座论坛": np.array([0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
    "赛事招募":     np.array([0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0]),
    "体育赛事":     np.array([0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]),
    "志愿实践":     np.array([0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0]),
    "红色党建活动": np.array([0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0]),
    "组织招募":     np.array([0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0]),
    "其他活动":     np.array([0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0]),
    "重大事项":     np.array([0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0]),
    "校内生活告示": np.array([0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0]),
    "行政通知":     np.array([0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0]),
    "教务通知":     np.array([0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0]),
    "其他通知":     np.array([0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0]),
    "学习资源":     np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0]),
    "就业实习":     np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0]),
    "权益服务":     np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]),
}

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


    def add_user(self, user):
        """
        在偏好表中添加用户
        :param user: 用户
        :return: 用户偏好
        """
        try:
            preferences = self.get(user=user)
        except Preference.DoesNotExist:
            preferences = self.create(user=user, account_preference={}, tag_preference=[0.0625]*16, keyword_preference=[0.01]*100)
        return preferences

    def add_subscription(self, user, account):
        """
        在偏好表中添加用户订阅
        :param user: 用户
        :param account: 公众号
        :return: 用户偏好
        """
        item = self.get_user_preferences(user)
        lenth = len(item.account_preference)  
        # 新赋权重1/(lenth + 1)，保持总权重和为1
        if account.id not in item.account_preference:
            for id in item.account_preference:
                item.account_preference[id] *= (1 - 1/(lenth + 1))
            item.account_preference[account.id] = 1/(lenth + 1)
        item.save()
        return item
    
    def remove_subscription(self, user, account):
        """
        在偏好表中移除用户订阅
        :param user: 用户
        :param account: 公众号
        :return: 用户偏好
        """
        item = self.get_user_preferences(user)
        lenth = len(item.account_preference)
        # 移除权重，保持总权重和为1
        if account.id in item.account_preference:
            if lenth == 1:
                del item.account_preference[account.id]
            else:
                delta = item.account_preference[account.id]/(lenth - 1)
                del item.account_preference[account.id]
                for id in item.account_preference:
                    item.account_preference[id] += delta
            item.save()
        return item

    def update_preference(self, user, article, operation):
        """
        根据用户行为更新用户偏好
        :param user: 用户
        :param article: 文章
        :param operation: 操作("browse", "favorite")
        :return: 用户偏好
        """
        radio = 1 if operation == "browse" else 2
        item = self.get_user_preferences(user)
        # 更新公众号偏好
        account_id = str(article.public_account.id)
        if account_id in item.account_preference:
            for id in item.account_preference:
                item.account_preference[id] *= (1 - (radio * 0.1))
            item.account_preference[account_id] += (radio * 0.1)
        else:
            print("[Error] 未订阅该公众号")
        # 更新标签偏好
        tags_vector = np.array(article.tags_vector)
        tag_preference_vector = np.array(item.tag_preference)
        if tags_vector.shape[0] == 16 and tag_preference_vector.shape[0] == 16:
            tag_preference_vector = (1 - radio * 0.1) * tag_preference_vector + radio * 0.1 * tags_vector
            item.tag_preference = tag_preference_vector.tolist()
        # 更新关键词偏好
        semantic_vector = np.array(article.semantic_vector)
        keyword_preference_vector = np.array(item.keyword_preference)
        if semantic_vector.shape[0] == 100 and keyword_preference_vector.shape[0] == 100:
            keyword_preference_vector = (1 - radio * 0.1) * keyword_preference_vector + radio * 0.1 * semantic_vector
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
        tags_vector = np.array(article.tags_vector)
        tag_preference_vector = np.array(preference.tag_preference)
        if tags_vector.shape[0] == 16 and tag_preference_vector.shape[0] == 16:
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

