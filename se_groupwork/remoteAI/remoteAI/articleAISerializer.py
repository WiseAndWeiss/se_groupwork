import re
import json
from aiRequest import get_response


def load_basic_info(content):
	pattern = r"""
    标题:?(.*?)\n    # 匹配标题（非贪婪匹配到换行）
    时间：?(.*?)\n    # 匹配时间（包含日期和时间，非贪婪匹配到换行）
    URL:?(.*?)\n    # 匹配URL（非贪婪匹配到换行）
	"""
	match = re.search(pattern, content, re.VERBOSE | re.DOTALL)
	result = {}
	if match:
		datetime_str = match.group(2).strip()
		date_time = datetime_str.split(' ', 1) if ' ' in datetime_str else (datetime_str, '')
		url = match.group(3).strip()
		url = url.split("&chksm=")[0] if "&chksm=" in url else url
		result = {
			"title": match.group(1).strip(),
			"date": date_time[0] if len(date_time) > 0 else "",
			"time": date_time[1] if len(date_time) > 1 else "",
			"from": "",
			"url": url
		}
		return result
	else:
		raise ValueError("内容格式异常")


def extract_json(content):
	pattern = r'```json(.*?)```'
	match = re.search(pattern, content, re.DOTALL)
	if match:
		json_str = match.group(1).strip()
		return json.loads(json_str)
	else:
		raise ValueError("内容格式异常")


def ai_summarize_article(content):
	prompt = """
	你将作为一个校园公众号推送文章整合、摘要和分类的AI助手。用户将会提供一篇由某校园公众号推送的文章内容。你需要根据文章内容：
	- 提取数个关键词，用于检索
	- 生成一个简洁的摘要(100字左右)
	- 并为文章分配一个或多个合适的分类标签
	请确保摘要准确反映文章的主要内容，且分类标签简洁明了。
	你可以任意思考和输出，但最终的结论输出内容请组织为以下json格式，记得用```json和```包裹：
	```json
	{
		"keywords": ["关键词1", "关键词2", "..."],
		"summary": "这里是文章的简洁摘要。",
		"categories": ["分类标签1", "分类标签2", "..."],
		"relevant_time": "MM-DD HH:MM",   # 可选，例如活动的时间，通知的截止时间等，如无相关时间信息则留空字符串
	}
	```
	所有标签和其使用场景，请参考以下信息：
	一、活动类（用户可参与）
		1.1. 文娱活动：括团建活动、学生节、校园歌手比赛、演出、电影放映、社团文化节、毕业晚会”等，覆盖所有非竞技类的文化娱乐活动。
		1.2. 学术讲座论坛：与学术、科研相关的“学科论坛、校友分享会、学术研讨会等。
		1.3. 赛事招募：特指学术、科研比赛，例如创业大赛、学科竞赛（如数学建模、英语竞赛）、大创、挑战杯等。
		1.4. 体育赛事：例如运动会，院系球类赛（篮球 / 足球赛）、校际对抗赛等，覆盖所有竞技类体育活动。
		1.5. 志愿实践：新增分类，包含 “校内志愿（图书馆义工、活动协助）、校外实践（社区服务、支教招募）、公益活动报名”等
		1.6. 红色党建活动：聚焦思想建设与红色教育的活动，包含 “主题党日活动、党史学习教育、红色基地参观、党建知识竞赛” 等，突出政治性和组织性。
		1.7. 组织招募：针对较长期的学生组织的成员吸纳，包含 “学生会 / 团委招新、社团纳新、系队（体育/文艺）选拔、志愿者团队招募”。
		1.8. 其他活动：覆盖学生可参与，但未归入文娱、志愿、赛事等类别的单次活动，参与属性明确，但类型特殊”，例如校园联名打卡活动（如书店 / 咖啡馆打卡）、公益义卖等。
	二、通知类（用户阅读信息）
		2.1. 重大事项： 突发性、关键性、非日常的重要新闻，紧急或特殊且无其他类别可归属”，例如校内重要人物讣告、突发安全事件通报（如极端天气、校内事故）、学校重大荣誉获得（如入选国家级项目）的紧急播报（使用此类别请谨慎，确保信息确实重大）。
		2.2. 校内生活告示： “宿舍调整、设施维修、食堂 / 超市营业时间变更，供暖时间” 等均属于此类，聚焦 “影响日常生活” 的通知。
		2.3. 行政通知：新增分类，区别于生活类，例如奖学金评定、助学金申请、评奖评优通知等，侧重学校行政事务相关信息。
		2.4. 教务通知：针对教学信息，包括招生保研、选课时间、大学生体测、期中期末考试时间、四六级计算机考试报名、补考缓考通知等
		2.5. 其他通知：与学生在校生活直接相关，但未归入‘校内生活告示’‘行政通知’的临时性、事务性通知”
	三、资源类（用户获取资源）
		3.1. 学习资源：聚焦学习相关的辅助资源，如 “复习资料共享、选课指南、考研 / 考公经验帖、学术数据库使用教程”
		3.2. 就业实习：新增分类，包含 “校内招聘会信息、企业实习推送、就业指导讲座（区别于学术讲座）、简历修改服务通知”，覆盖学生职业发展需求。
		3.3. 权益服务：新增分类，包含 “医保报销指南、心理咨询预约、校园卡挂失 / 补办流程、投诉建议渠道”，聚焦学生权益保障相关的服务信息。
	四、其他类
		4.1. 其他内容：非服务性、偏向宣传/记录性质，与学生日常生活关联度较低”的内容，无明确参与或告知的需求，例如校内人物专访（如优秀教师、学生代表）、学生组织/支队实践成果回顾（非招募类）、学校品牌形象宣传文章（如校园风景、历史故事）等
	"""
	messages = [
		{"role": "system", "content": prompt},
		{"role": "user", "content": f"{content}"}
	]
	response = get_response(messages)
	print("AI返回内容：", response)
	json_data = extract_json(response)
	return json_data


def entry(content):
	basic_info = load_basic_info(content)
	ai_info = ai_summarize_article(content)
	result = {**basic_info, **ai_info}
	# print(json.dumps(result, ensure_ascii=False, indent=4))
	return result


if __name__ == "__main__":
	filenames = ["1.content", "2.content", "3.content", "4.content", "5.content"]
	for filename in filenames:
		with open(filename, "r", encoding="utf-8") as f:
			content = f.read()
			entry(content)