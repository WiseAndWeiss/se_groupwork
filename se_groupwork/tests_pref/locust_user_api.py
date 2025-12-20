import json
import os
import time
from locust import HttpUser, task, between, events

USERNAME = os.getenv("LOCUST_USER_USERNAME", "testuser")
PASSWORD = os.getenv("LOCUST_USER_PASSWORD", "Password123!")
# 如果提供了 LOCUST_ACCESS_TOKEN 就跳过登录，直接复用该 token
ACCESS_TOKEN = os.getenv("LOCUST_ACCESS_TOKEN")
API_PREFIX = os.getenv("LOCUST_API_PREFIX", "/api/user")
RESULT_PATH = os.getenv("LOCUST_RESULT_PATH", "locust_user_api_stats.json")


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class UserApiUser(HttpUser):
    wait_time = between(0.2, 1.0)
    token = None

    def on_start(self):
        # 如果外部已经提供 token，则直接使用，避免压测时重复登录
        if ACCESS_TOKEN:
            self.token = ACCESS_TOKEN
            return

        payload = {"username": USERNAME, "password": PASSWORD}
        with self.client.post(f"{API_PREFIX}/auth/login/", json=payload, catch_response=True) as resp:
            if resp.status_code == 200 and "access" in resp.json():
                self.token = resp.json()["access"]
                resp.success()
            else:
                resp.failure(f"login failed: {resp.status_code} {resp.text}")

    @task(3)
    def profile(self):
        if not self.token:
            return
        self.client.get(
            f"{API_PREFIX}/auth/profile/",
            headers=_auth_header(self.token),
            name="GET profile",
        )

    @task(2)
    def subscriptions(self):
        if not self.token:
            return
        self.client.get(
            f"{API_PREFIX}/subscriptions/",
            headers=_auth_header(self.token),
            name="GET subscriptions",
        )

    @task(2)
    def collections_and_favorites(self):
        """获取收藏夹列表，然后通过collection获取收藏"""
        if not self.token:
            return
        headers = _auth_header(self.token)
        # 获取收藏夹列表
        with self.client.get(
            f"{API_PREFIX}/collections/",
            headers=headers,
            name="GET collections",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"list collections failed: {resp.status_code}")
                return
            collections = resp.json()
            if collections:
                collection_id = collections[0].get("id")
                # 获取该收藏夹内的收藏
                self.client.get(
                    f"{API_PREFIX}/collections/{collection_id}/",
                    headers=headers,
                    name="GET collection favorites",
                )

    @task(1)
    def history(self):
        if not self.token:
            return
        self.client.get(
            f"{API_PREFIX}/history/",
            headers=_auth_header(self.token),
            name="GET history",
        )

    @task(1)
    def todos(self):
        if not self.token:
            return
        self.client.get(
            f"{API_PREFIX}/todos/",
            headers=_auth_header(self.token),
            name="GET todos",
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
