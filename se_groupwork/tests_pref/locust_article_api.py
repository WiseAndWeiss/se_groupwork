import json
import os
import time
from locust import HttpUser, task, between, events

# 认证：可直接提供 access token，或提供用户名/密码让脚本登录
USERNAME = os.getenv("LOCUST_USER_USERNAME", "testuser")
PASSWORD = os.getenv("LOCUST_USER_PASSWORD", "Password123!")
ACCESS_TOKEN = os.getenv("LOCUST_ACCESS_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2MjE5ODIwLCJpYXQiOjE3NjYxMzM0MjAsImp0aSI6IjI3MjA5ODM4MGQwODQwOGI5ODZkNDU2YTBjNzdhYWIxIiwidXNlcl9pZCI6IjI3In0.zPAsR9NZBWaAWnKNJr21CqTpODBR6BJZFB_n27Fy8xo")

# 接口前缀与参数
ARTICLES_PREFIX = os.getenv("LOCUST_ARTICLES_PREFIX", "/api/articles")
USER_API_PREFIX = os.getenv("LOCUST_USER_PREFIX", "/api/user")
RESULT_PATH = os.getenv("LOCUST_RESULT_PATH", "locust_article_api_stats.json")

ACCOUNT_ID = os.getenv("LOCUST_ARTICLE_ACCOUNT_ID", "1")
SEARCH_CONTENT = os.getenv("LOCUST_ARTICLE_SEARCH", "清华")
START_RANK = int(os.getenv("LOCUST_ARTICLE_START_RANK", "0"))
FILTER_RANGE = os.getenv("LOCUST_ARTICLE_FILTER_RANGE", "a")
FILTER_LIMIT = int(os.getenv("LOCUST_ARTICLE_FILTER_LIMIT", "20"))


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class ArticleApiUser(HttpUser):
    wait_time = between(0.2, 1.0)
    token = None

    def on_start(self):
        # 复用外部 token，避免压测登录接口
        if ACCESS_TOKEN:
            self.token = ACCESS_TOKEN
            return

        payload = {"username": USERNAME, "password": PASSWORD}
        with self.client.post(f"{USER_API_PREFIX}/auth/login/", json=payload, catch_response=True) as resp:
            if resp.status_code == 200 and "access" in resp.json():
                self.token = resp.json()["access"]
                resp.success()
            else:
                resp.failure(f"login failed: {resp.status_code} {resp.text}")

    @task(3)
    def latest(self):
        if not self.token:
            return
        self.client.get(
            f"{ARTICLES_PREFIX}/latest/?start_rank={START_RANK}",
            headers=_auth_header(self.token),
            name="GET articles latest",
        )

    @task(2)
    def recommended(self):
        if not self.token:
            return
        self.client.get(
            f"{ARTICLES_PREFIX}/recommended/",
            headers=_auth_header(self.token),
            name="GET articles recommended",
        )

    @task(2)
    def campus_latest(self):
        if not self.token:
            return
        self.client.get(
            f"{ARTICLES_PREFIX}/campus-latest/?start_rank={START_RANK}",
            headers=_auth_header(self.token),
            name="GET articles campus_latest",
        )

    @task(2)
    def customized_latest(self):
        if not self.token:
            return
        self.client.get(
            f"{ARTICLES_PREFIX}/customized-latest/?start_rank={START_RANK}",
            headers=_auth_header(self.token),
            name="GET articles customized_latest",
        )

    @task(1)
    def search_customized_latest(self):
        if not self.token:
            return
        self.client.get(
            f"{ARTICLES_PREFIX}/customized-latest/search?start_rank={START_RANK}&search_content={SEARCH_CONTENT}",
            headers=_auth_header(self.token),
            name="GET articles customized_search",
        )

    @task(1)
    def by_account(self):
        if not self.token:
            return
        self.client.get(
            f"{ARTICLES_PREFIX}/by-account/?account_id={ACCOUNT_ID}&start_rank={START_RANK}",
            headers=_auth_header(self.token),
            name="GET articles by_account",
        )

    @task(1)
    def filter_articles(self):
        if not self.token:
            return
        payload = {
            "range": FILTER_RANGE,  # a=all, d=default, c=custom
            "start_rank": START_RANK,
            "limit": FILTER_LIMIT,
        }
        self.client.post(
            f"{ARTICLES_PREFIX}/filter/",
            json=payload,
            headers=_auth_header(self.token),
            name="POST articles filter",
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
