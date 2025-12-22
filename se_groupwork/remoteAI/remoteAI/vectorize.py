from se_groupwork.global_tools import global_embedding_load
import numpy as np
import json

from remoteAI.remoteAI.tags import TAGS


def vectorize(text):
    embedding = global_embedding_load()
    vector = embedding.embed_documents([text])
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
    return tags_vector.tolist()