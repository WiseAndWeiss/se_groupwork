import os
import time
import random
import json
from urllib.parse import urlencode
from locust import HttpUser, task, between, events

# Comma-separated paths, e.g. "/static/admin/css/base.css,/media/avatars/demo.png"
RAW_URLS = os.getenv("LOCUST_STATIC_URLS", "/media/icons/%E6%B8%85%E5%8D%8E%E5%A4%A7%E5%AD%A6.png").split(",")
CACHE_BUST = False
RESULT_PATH = os.getenv("LOCUST_RESULT_PATH", "locust_static_assets_stats.json")
WAIT_MIN = float(os.getenv("LOCUST_WAIT_MIN", "0.1"))
WAIT_MAX = float(os.getenv("LOCUST_WAIT_MAX", "0.3"))


class StaticAssetsUser(HttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    @task(1)
    def fetch_asset(self):
        path = random.choice(RAW_URLS).strip()
        if not path:
            return
        url = path
        if CACHE_BUST:
            suffix = urlencode({"_": int(time.time() * 1000)})
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{suffix}"
        self.client.get(url, name="GET static asset")


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
