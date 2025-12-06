import re
import json
from remoteAI.remoteAI.ai_request import get_response
from remoteAI.remoteAI.vectorize import keywords_vectorize, tags_vectorize

def extract_json(content):
	pattern = r'```json(.*?)```'
	try:
		match = re.search(pattern, content, re.DOTALL)
		if match:
			json_str = match.group(1).strip()
			return json.loads(json_str)
		else:
			return None
	except json.JSONDecodeError:
		return None


def ai_summarize_article(content):
	prompt = """
	你将作为一个校园公众号推送文章整合、摘要和分类的AI助手。用户将会提供一篇由某校园公众号推送的文章内容(由于文章获取方式的限制，又是会出现标点分段缺失、图片无法显示等问题，请你自适应）。你需要根据文章内容：
	- 提取数个关键词，用于检索
	- 生成一个简洁的摘要(150字左右)
	- 并为文章分配2-3个合适的分类标签
	请确保摘要准确反映文章的主要内容，且分类标签简洁明了。
	你可以任意思考和输出，但最终的结论输出内容请组织为以下json格式，记得用```json和```包裹：
	```json
	{
		"key_info": ["关键词1", "关键词2", "..."],
		"summary": "这里是文章的简洁摘要。",
		"tags": ["分类标签1", "分类标签2", "..."],
		"relevant_time": "MM-DD HH:MM",   # 可选，例如活动的时间，通知的截止时间等，如无相关时间信息则留空字符串
	}
	```
	关键词应该有一定的概括性和泛用性，例如“挑战者杯”而不是“第十三届挑战者杯一等奖”。
	所有标签和其使用场景，请参考以下信息：
	一、文章类型（必选 1 个）
		[活动]：可参与的各类场景，含演出、讲座、参观、论坛、打卡等具备参与属性的事项。
		[比赛]：具备竞赛属性的正式活动，如科研、体育、校园歌手等竞赛，排除权威度极低的小型线上赛事。
		[通知]：官方发布的正式信息，含教务（选课）、行政（奖学金、假期）、生活（食堂营业）及各类公示。
		[指南]：教程类内容，用于指导具体操作，如就医、报销、校园卡补办等流程。
		[资源]：提供实用资料或渠道，包括学习资料、经验帖、保研数据、求职内推、招聘信息、二手物品等。
		[招募]：校内主体的人员招募，如学生组织、社团、临时性岗位等招募信息。、
		[招聘]：校外主体发起的就业相关，如企业招聘、实习、招聘会、兼职等。
		[整合]: 整合性质的推送，如生权公众号的一周校园信息汇总、学生组织的活动信息汇总等。
		[其他类型]：非服务、非参与性的宣传类内容，如人物专访、学生组织 / 社团成果回顾等。
	二、内容领域（必选 1 个）
		[学术]：与学术研究、学业相关的内容，如科研、OI 竞赛、考研等。
		[教务]：学校学业事务安排，如期中考试、开课信息、体测、保研、四六级等。
		[行政]：学校行政事务安排，如假期、奖学金助学金评定等。
		[体育]：各类体育相关活动及信息。
		[党建]：与党建活动、理论学习、红色教育等相关的信息。
		[文娱]：涵盖音乐、文艺、美术、娱乐等领域的活动及内容。
		[医疗]：涉及就医、身体健康（含心理健康）的相关内容。
		[生活]：与校内日常生活密切相关的信息，如宿舍调整、供暖、设施维修、超市营业等。
		[留学]：与留学申请、准备、相关政策等有关的内容。
		[就业]：与就业、实习、职业规划、招聘等相关的内容。
		[实践]: 与社会实践、支队、创新创业等相关的信息。
		[公益]：各类公益相关活动，如志愿活动、献血、义卖、书信帮扶、二手书回收发放等。
		[其他内容]：无法归入上述领域的内容。
	三、重要标签（可选）
		[重大]：涉及重大、突发、关键且非日常的重要新闻，如校内重要人物讣告、极端天气通知等。确保事项重大，该标签请谨慎使用。
	"""
	messages = [
		{"role": "system", "content": prompt},
		{"role": "user", "content": f"{content}"}
	]
	response = get_response(messages)
	json_data = extract_json(response)
	return json_data


def entry(article_msg):
	for retry in range(3):
		ai_resp = ai_summarize_article(json.dumps(article_msg, ensure_ascii=False, indent=4))
		success_flag = True
		success_flag &= (ai_resp is not None)
		success_flag &= ("summary" in ai_resp)
		success_flag &= ("key_info" in ai_resp)
		success_flag &= ("tags" in ai_resp)
		if not success_flag:
			print(f"[Retry {retry}] For {article_msg['title']}")
			continue
		print(ai_resp)
		ai_resp["semantic_vector"] = keywords_vectorize(ai_resp["key_info"])
		ai_resp["tags_vector"] = tags_vectorize(ai_resp["tags"])
		return ai_resp
	return None