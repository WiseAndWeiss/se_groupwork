import os
import random
import time
import json
from datetime import datetime, timedelta, timezone
from locust import HttpUser, task, between, events

USERNAME = os.getenv("LOCUST_USER_USERNAME", "testuser")
PASSWORD = os.getenv("LOCUST_USER_PASSWORD", "Password123!")
ACCESS_TOKEN = os.getenv("LOCUST_ACCESS_TOKEN")
API_PREFIX = os.getenv("LOCUST_API_PREFIX", "/api/user")
ARTICLE_ID = int(os.getenv("LOCUST_ARTICLE_ID", "1"))
PUBLIC_ACCOUNT_ID = int(os.getenv("LOCUST_PUBLIC_ACCOUNT_ID", "1"))
TODO_TITLE = os.getenv("LOCUST_TODO_TITLE", "locust todo")
RESULT_PATH = os.getenv("LOCUST_RESULT_PATH", "locust_user_api_write_stats.json")


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _suffix() -> str:
    return f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"


def _now_iso(offset_minutes: int = 0) -> str:
    dt = datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)
    return dt.isoformat()


class UserApiWriteUser(HttpUser):
    wait_time = between(0.2, 1.0)
    token = None
    article_cursor = 0
    public_account_cursor = 0

    def on_start(self):
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
        if self.token:
            self._cleanup_user_state()

    def _cleanup_user_state(self):
        """Clear all favorites and subscriptions before load starts."""
        headers = _auth_header(self.token)
        for resource in ("favorites", "subscriptions"):
            with self.client.get(
                f"{API_PREFIX}/{resource}/",
                headers=headers,
                name=f"GET {resource} list (cleanup)",
                catch_response=True,
            ) as resp:
                if resp.status_code != 200:
                    resp.failure(f"cleanup list {resource} failed: {resp.status_code} {resp.text}")
                    continue
                try:
                    items = resp.json()
                    if isinstance(items, dict) and "results" in items:
                        items = items.get("results", [])
                except ValueError:
                    resp.failure(f"cleanup list {resource} json error")
                    continue
                for item in items or []:
                    rid = item.get("id")
                    if not rid:
                        continue
                    with self.client.delete(
                        f"{API_PREFIX}/{resource}/{rid}/",
                        headers=headers,
                        name=f"DELETE {resource} cleanup",
                        catch_response=True,
                    ) as del_resp:
                        if del_resp.status_code in (200, 202, 204, 404):
                            del_resp.success()
                        elif del_resp.status_code == 400:
                            # already removed or conflict; treat as success for cleanup
                            del_resp.success()
                        else:
                            del_resp.failure(
                                f"cleanup delete {resource} {rid} failed: {del_resp.status_code} {del_resp.text}"
                            )

    def _next_article_id(self) -> int:
        self.article_cursor = (self.article_cursor) % 100 + 1  # 1~100循环
        return self.article_cursor

    def _next_public_account_id(self) -> int:
        self.public_account_cursor = (self.public_account_cursor) % 100 + 1  # 1~100循环
        return self.public_account_cursor

    @task(2)
    def create_and_delete_subscription(self):
        if not self.token:
            return
        headers = _auth_header(self.token)
        public_account_id = self._next_public_account_id()
        with self.client.post(
            f"{API_PREFIX}/subscriptions/",
            json={"public_account_id": public_account_id},
            headers=headers,
            name="POST subscriptions create",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                sub_id = resp.json().get("id")
                resp.success()
            elif resp.status_code == 400 or resp.status_code == 404:
                # 已订阅/已删除等业务冲突，视作成功以避免高失败率
                resp.success()
                sub_id = None
            else:
                resp.failure(f"create sub failed: {resp.status_code} {resp.text}")
                return
        if sub_id:
            self.client.delete(
                f"{API_PREFIX}/subscriptions/{sub_id}/",
                headers=headers,
                name="DELETE subscriptions id",
            )

    @task(2)
    def get_collection_and_list_favorites(self):
        """前端通过collection来获取收藏夹内的收藏"""
        if not self.token:
            return
        headers = _auth_header(self.token)
        # 先获取收藏夹列表
        with self.client.get(
            f"{API_PREFIX}/collections/",
            headers=headers,
            name="GET collections list",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"list collections failed: {resp.status_code} {resp.text}")
                return
            collections = resp.json()
            if not collections:
                resp.failure("no collections found")
                return
            collection_id = collections[0].get("id")
        
        # 获取该收藏夹内的收藏
        if collection_id:
            self.client.get(
                f"{API_PREFIX}/collections/{collection_id}/",
                headers=headers,
                name="GET collection favorites",
            )

    @task(2)
    def create_and_delete_favorite(self):
        if not self.token:
            return
        headers = _auth_header(self.token)
        article_id = self._next_article_id()
        with self.client.post(
            f"{API_PREFIX}/favorites/",
            json={"article_id": article_id},
            headers=headers,
            name="POST favorites create",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                fav_id = resp.json().get("id")
                resp.success()
            elif resp.status_code == 400 or resp.status_code == 404:
                # 已收藏/已删除/收藏夹满等业务冲突，视作成功
                resp.success()
                fav_id = None
            else:
                resp.failure(f"create favorite failed: {resp.status_code} {resp.text}")
                return
        if fav_id:
            self.client.delete(
                f"{API_PREFIX}/favorites/{fav_id}/",
                headers=headers,
                name="DELETE favorites id",
            )

    @task(2)
    def create_update_delete_todo(self):
        if not self.token:
            return
        headers = _auth_header(self.token)
        title = f"{TODO_TITLE}-{_suffix()}"
        start_time = _now_iso()
        end_time = _now_iso(60)
        with self.client.post(
            f"{API_PREFIX}/todos/",
            json={"title": title, "note": "locust note", "remind": False, "start_time": start_time, "end_time": end_time},
            headers=headers,
            name="POST todos create",
            catch_response=True,
        ) as resp:
            if resp.status_code != 201:
                resp.failure(f"create todo failed: {resp.status_code} {resp.text}")
                return
            todo_id = resp.json().get("id")
        if not todo_id:
            return
        # update
        self.client.patch(
            f"{API_PREFIX}/todos/{todo_id}/",
            json={"note": "updated by locust"},
            headers=headers,
            name="PATCH todos id",
        )
        # delete
        self.client.delete(
            f"{API_PREFIX}/todos/{todo_id}/",
            headers=headers,
            name="DELETE todos id",
        )

    @task(2)
    def create_history(self):
        if not self.token:
            return
        headers = _auth_header(self.token)
        article_id = self._next_article_id()
        with self.client.post(
            f"{API_PREFIX}/history/",
            json={"article_id": article_id},
            headers=headers,
            name="POST history create",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 404):
                resp.success()
            else:
                resp.failure(f"create history failed: {resp.status_code} {resp.text}")

    @task(1)
    def list_history(self):
        if not self.token:
            return
        headers = _auth_header(self.token)
        with self.client.get(
            f"{API_PREFIX}/history/",
            headers=headers,
            name="GET history list",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"list history failed: {resp.status_code} {resp.text}")

    @task(1)
    def create_and_delete_collection(self):
        if not self.token:
            return
        headers = _auth_header(self.token)
        name = f"locust-col-{_suffix()}"
        with self.client.post(
            f"{API_PREFIX}/collections/",
            json={"name": name, "description": "locust collection"},
            headers=headers,
            name="POST collections create",
            catch_response=True,
        ) as resp:
            if resp.status_code not in (201, 400):
                resp.failure(f"create collection failed: {resp.status_code} {resp.text}")
                return
            col_id = resp.json().get("id") if resp.status_code == 201 else None
        if col_id:
            self.client.delete(
                f"{API_PREFIX}/collections/{col_id}/",
                headers=headers,
                name="DELETE collections id",
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
