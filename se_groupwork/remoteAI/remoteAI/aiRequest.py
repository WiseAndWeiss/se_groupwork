import json
import requests
import configparser

llm = "deepseek"
config = configparser.ConfigParser()
config.read('api.config')
url = config.get(llm, 'url')
key = config.get(llm, 'key')
model = config.get(llm, 'model')

setting = {
    "model": model,
    "temperature": 0.7,
    "stream": True
}
stream_output = False

def get_response(msg):
    data = setting | {"messages": msg}
    headers = {
    "Content-Type": "application/json",
    'authorization': f'Bearer {key}'
    }
    full_response = ''
    try:
        with requests.post(
            url=url,
            headers=headers,
            json=data,
            stream=True
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        chunk = decoded_line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(chunk)
                            content = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                if stream_output:
                                    print(content, end="", flush=True)
                                full_response += content
                        except json.JSONDecodeError:
                            print(f"解析错误: {chunk}")
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
    finally:
        return str(full_response)
    

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Why is the sky blue?"}
    ]
    response = get_response(messages)
    print("\nFull Response:", response)
