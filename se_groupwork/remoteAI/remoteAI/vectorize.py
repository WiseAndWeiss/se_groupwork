from sentence_transformers import SentenceTransformer
from sklearn.random_projection import GaussianRandomProjection
import numpy as np
import json

from remoteAI.remoteAI.tags import TAGS

local_model_path = './remoteAI/all-MiniLM-L6-v2'
model = SentenceTransformer(local_model_path)

def vectorize(text):
    vector = model.encode(text)
    cuted_vector = vector[0:100]
    return cuted_vector


def keywords_vectorize(keywords):
    keywords_vectors = [vectorize(keyword) for keyword in keywords]
    article_vector = np.mean(keywords_vectors, axis=0)
    norm = np.linalg.norm(article_vector)
    if norm != 0:
        article_vector = article_vector / norm
    return article_vector.tolist()


def tags_vectorize(tags):
    tags_vector = np.zeros(len(TAGS))
    for tag in tags:
        if tag in TAGS:
            rank = TAGS.index(tag)
            tags_vector[rank] = 1
    norm = np.linalg.norm(tags_vector)
    if norm != 0:
        tags_vector = tags_vector / norm
    return tags_vector.tolist()


data = [
    {
        "tags": ["就业", "招聘"],
        "keyinfo": "春招,简历优化,2025毕业生,求职攻略"
    },
    {
        "tags": ["就业", "资源"],
        "keyinfo": "毕业生择业,薪资对比,职业发展路径,求职决策"
    },
    {
        "tags": ["教务", "通知"],
        "keyinfo": "春季学期,选课补选,补选时间,教务通知"
    },
    {
        "tags": ["教务", "通知"],
        "keyinfo": "学籍异动,转专业,休学,申请材料,教务信息"
    },
    {
        "tags": ["体育", "比赛"],
        "keyinfo": "校园杯,篮球联赛,报名启动,赛程安排"
    },
    {
        "tags": ["体育", "比赛"],
        "keyinfo": "羽毛球挑战赛,运动装备,校内比赛,运动员"
    },
    {
        "tags": ["就业", "资源"],
        "keyinfo": "春招补录、秋招失利、投递策略、内推渠道、毕业生补招"
    },
    {
        "tags": ["教务", "通知"],
        "keyinfo": "补考报名,重修流程,教务通知"
    },
    {
        "tags": ["体育", "比赛"],
        "keyinfo": "体育比赛奖项,积分规则,团体冠军,个人奖项,校内赛事规则"
    }
]


if __name__ == '__main__':
    # for test
    print("Already loaded model")
    result = []
    for item in data:
        tags = item['tags']
        keyinfo = item['keyinfo'].split(',')
        tags_vector = tags_vectorize(tags)
        keyinfo_vector = keywords_vectorize(keyinfo)
        result.append(item | {"tags_vector": tags_vector, "keyinfo_vector": keyinfo_vector})
    with open('vector.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)