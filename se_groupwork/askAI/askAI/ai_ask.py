from se_groupwork.global_tools import global_faiss_tool_load
from askAI.askAI.ai_request import get_stream_response
from webspider.models import Article
from copy import copy

base_prompt = """
你是一个面向校园生活领域的信息整合和总结专家，你需要根据用户的提问，从参考知识库中进行回答，我会提供你参考知识库中最可能相关的最多5篇文章。
回答规则：
	1. 优先使用参考知识库中的内容，用自然语言回答；
	2. 若知识库无相关信息，直接说「未查询到相关内容」，不要编造；
	3. 回答简洁明了，贴合用户问题，不要冗余。
下面是参考知识库中最可能相关的文章：

"""

def get_reference_articles(question):
    articles = []
    faissTool = global_faiss_tool_load()
    for id, score in faissTool.search(question, top_k=5):
        article = Article.objects.get(id=id)
        articles.append(article)
    return articles


def ask_ai(question, reference_articles_content):
    prmopt = copy(base_prompt)
    for i, article in enumerate(reference_articles_content):
        prmopt += f'============[第{i}篇]==============\n' + article + '\n\n\n'
    message = [
		{"role": "system", "content": prmopt},
		{"role": "user", "content": question}
	]
    for chunk in get_stream_response(message):
        yield chunk
