from sentence_transformers import SentenceTransformer
from sklearn.random_projection import GaussianRandomProjection
import numpy as np
import json

local_model_path = 'remoteAI/all-MiniLM-L6-v2'
model = SentenceTransformer(local_model_path)

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
    tags_vector = np.zeros(16)
    for tag in tags:
        if tag in TAGS_DICT:
            tags_vector += TAGS_DICT[tag]
    norm = np.linalg.norm(tags_vector)
    if norm != 0:
        tags_vector = tags_vector / norm
    return tags_vector.tolist()


data = [
    {
        "tags": "就业实习,权益服务",
        "keyinfo": "春招,简历优化,2025毕业生,求职攻略"
    },
    {
        "tags": "就业实习",
        "keyinfo": "毕业生择业,薪资对比,职业发展路径,求职决策"
    },
    {
        "tags": "教务通知",
        "keyinfo": "春季学期,选课补选,补选时间,教务通知"
    },
    {
        "tags": "行政通知,教务通知",
        "keyinfo": "学籍异动,转专业,休学,申请材料,教务信息"
    },
    {
        "tags": "赛事招募",
        "keyinfo": "校园杯,篮球联赛,报名启动,赛程安排"
    },
    {
        "tags": "体育赛事",
        "keyinfo": "羽毛球挑战赛,运动装备,校内比赛,运动员"
    },
    {
        "tags": "就业实习,权益服务",
        "keyinfo": "春招补录、秋招失利、投递策略、内推渠道、毕业生补招"
    },
    {
        "tags": "教务通知",
        "keyinfo": "补考报名,重修流程,教务通知"
    },
    {
        "tags": "体育赛事",
        "keyinfo": "体育比赛奖项,积分规则,团体冠军,个人奖项,校内赛事规则"
    }
]


if __name__ == '__main__':
    # for test
    print("Already loaded model")
    result = []
    for item in data:
        tags = item['tags'].split(',')
        keyinfo = item['keyinfo'].split(',')
        tags_vector = tags_vectorize(tags)
        keyinfo_vector = keywords_vectorize(keyinfo)
        result.append(item | {"tags_vector": tags_vector, "keyinfo_vector": keyinfo_vector})
    with open('vector.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)