import json
import requests
import configparser as confp
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

cfg = confp.ConfigParser()
cfg.read('./remoteAI/remoteAI/remoteAI.ini')
llm = "deepseek"
url = cfg.get(llm, "url")
key = cfg.get(llm, "key")
model = cfg.get(llm, "model")

setting = {
    "model": model,
    "temperature": 0.7,
    "stream": False
}

def get_response(msg):
    '''
    非流式获取AI响应
    '''
    data = {**setting, "messages": msg}
    headers = {
        "Content-Type": "application/json",
        'authorization': f'Bearer {key}'
    }
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    result = ""
    try:
        response = session.post(
            url=url,
            headers=headers,
            json=data,
            timeout=(10, 100)
        )
        response.raise_for_status()
        response_json = response.json()
        result = response_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except requests.exceptions.RequestException as e:
        # TODO: 日志
        print(f"[Error at ai_request.py::get_response] 请求出错: {e}")
    except requests.exceptions.ConnectTimeout:
        # TODO: 日志
        print("[Error at ai_request.py::get_response] 网络连接超时")
    except requests.exceptions.ReadTimeout:
        # TODO: 日志
        print("[Error at ai_request.py::get_response] 等待返回超时")
    except requests.exceptions.HTTPError as e:
        # TODO: 日志
        print(f"[Error at ai_request.py::get_response] HTTP状态码: {e}")
    except json.JSONDecodeError:
        # TODO: 日志
        print("[Error at ai_request.py::get_response] JSON解析错误")
    except Exception as e:
        # TODO: 日志
        print(f"[Error at ai_request.py::get_response] 未知错误: {e}")
    finally:
        session.close()
        return str(result)
    
    

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Why is the sky blue?"}
    ]
    response = get_response(messages)
    print("\nFull Response:", response)
