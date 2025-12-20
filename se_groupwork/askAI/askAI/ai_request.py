import json
import requests
import configparser as confp
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

cfg = confp.ConfigParser()
cfg.read('./askAI/askAI/askAI.ini')
llm = "deepseek"
url = cfg.get(llm, "url")
key = cfg.get(llm, "key")
model = cfg.get(llm, "model")

setting = {
    "model": model,
    "temperature": 0.7,
    "stream": False
}

# 读取配置
cfg = confp.ConfigParser()
cfg.read('./askAI/askAI/askAI.ini')
llm = "deepseek"
url = cfg.get(llm, "url")
key = cfg.get(llm, "key")
model = cfg.get(llm, "model")

# 基础配置（开启流式）
setting = {
    "model": model,
    "temperature": 0.7,
    "stream": True  # 核心：开启流式输出
}

def get_stream_response(msg):
    '''
    流式获取AI响应（生成器函数，逐段返回内容）
    '''
    data = {**setting, "messages": msg}
    headers = {
        "Content-Type": "application/json",
        'authorization': f'Bearer {key}'
    }
    session = requests.Session()
    
    # 重试策略（复用原有配置）
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    try:
        # 发送流式请求（stream=True）
        response = session.post(
            url=url,
            headers=headers,
            json=data,
            timeout=(10, 300),  # 流式响应超时时间可适当延长
            stream=True  # 核心：开启流式接收
        )
        response.raise_for_status()

        # 逐行解析流式数据
        for line in response.iter_lines(chunk_size=1024):
            if not line:
                continue
            
            # 处理SSE格式：去除前缀 "data: "，兼容空行/结束符
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                line = line[6:]  # 去掉 "data: " 前缀
            
            # 处理结束信号（如OpenAI/DeepSeek的 "[DONE]"）
            if line == "[DONE]" or line == "":
                break
            
            # 解析单条流式数据
            try:
                chunk = json.loads(line)
                # 提取内容（适配DeepSeek/OpenAI格式）
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:  # 仅返回非空内容
                    yield content.replace('\r\n', '\n').replace('\r', '\n')  # 生成器逐段返回
            except json.JSONDecodeError:
                # 忽略解析失败的行（如心跳包/非标准格式）
                continue

    except requests.exceptions.RequestException as e:
        print(f"[Error at ai_request.py::get_stream_response] 请求出错: {e}")
        yield f"[错误] 请求AI服务失败：{str(e)[:50]}..."  # 流式返回错误信息
    except requests.exceptions.ConnectTimeout:
        print("[Error at ai_request.py::get_stream_response] 网络连接超时")
        yield "[错误] 网络连接超时，请稍后重试"
    except requests.exceptions.ReadTimeout:
        print("[Error at ai_request.py::get_stream_response] 等待返回超时")
        yield "[错误] AI响应超时，请稍后重试"
    except requests.exceptions.HTTPError as e:
        print(f"[Error at ai_request.py::get_stream_response] HTTP状态码: {e}")
        yield f"[错误] AI服务返回异常状态码：{e}"
    except Exception as e:
        print(f"[Error at ai_request.py::get_stream_response] 未知错误: {e}")
        yield f"[错误] 未知错误：{str(e)[:50]}..."
    finally:
        session.close()

    
    

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Why is the sky blue?"}
    ]
    full_response = ""
    for chunk in get_stream_response(messages):
        print(chunk, end="")
        full_response += chunk
    print("\n\nFull response:", full_response)
