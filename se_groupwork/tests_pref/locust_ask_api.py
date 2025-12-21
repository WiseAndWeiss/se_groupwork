import json
import os
import time
from locust import HttpUser, task, between, events

USERNAME = os.getenv("LOCUST_USER_USERNAME", "testuser")
PASSWORD = os.getenv("LOCUST_USER_PASSWORD", "Password123!")
ACCESS_TOKEN = os.getenv("LOCUST_ACCESS_TOKEN")
API_PREFIX = os.getenv("LOCUST_API_PREFIX", "/api")
RESULT_PATH = os.getenv("LOCUST_RESULT_PATH", "locust_ask_api_stats.json")
QUESTION = os.getenv("LOCUST_ASK_QUESTION", "请帮我总结一下近期校园活动")


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class AskApiUser(HttpUser):
    wait_time = between(0.5, 1.5)
    token = None

    def on_start(self):
        # 优先使用外部提供的 access token，避免重复登录
        if ACCESS_TOKEN:
            self.token = ACCESS_TOKEN
            return

        payload = {"username": USERNAME, "password": PASSWORD}
        with self.client.post(f"{API_PREFIX}/user/auth/login/", json=payload, catch_response=True) as resp:
            if resp.status_code == 200 and "access" in resp.json():
                self.token = resp.json()["access"]
                resp.success()
            else:
                resp.failure(f"login failed: {resp.status_code} {resp.text}")

    @task
    def ask(self):
        if not self.token:
            return
        self.client.post(
            f"{API_PREFIX}/ask/",
            headers=_auth_header(self.token),
            json={"question": QUESTION},
            name="POST ask",
        )


@events.quitting.add_listener
def save_stats(environment, **kwargs):
    runner = getattr(environment, "runner", None)
    if not runner:
        return
    stats = runner.stats
    data = {
        "timestamp": int(time.time()),
        "fail_ratio": stats.total.fail_ratio,
        "total_rps": stats.total.total_rps,
        "requests": [],
    }
    for stat in stats.entries.values():
        data["requests"].append(
            {
                "name": stat.name,
                "method": stat.method,
                "num_requests": stat.num_requests,
                "num_failures": stat.num_failures,
                "avg_response_time_ms": stat.avg_response_time,
                "p95_ms": stat.get_response_time_percentile(0.95),
                "p99_ms": stat.get_response_time_percentile(0.99),
                "rps": stat.total_rps,
            }
        )
    try:
        with open(RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass
