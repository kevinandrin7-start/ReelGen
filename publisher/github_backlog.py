"""Read and update backlog/topics.json through the GitHub API (no local git needed)."""
from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from typing import Callable

import requests

FILE = "backlog/topics.json"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Backlog:
    def __init__(self, repo: str, token: str, branch: str = "main"):
        self.repo, self.branch = repo, branch
        self.h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    def _url(self) -> str:
        return f"https://api.github.com/repos/{self.repo}/contents/{FILE}"

    def load(self) -> tuple[dict, str]:
        r = requests.get(self._url(), headers=self.h, params={"ref": self.branch}, timeout=30)
        r.raise_for_status()
        j = r.json()
        return json.loads(base64.b64decode(j["content"]).decode()), j["sha"]

    def update(self, mutate: Callable[[dict], None], message: str) -> dict:
        for attempt in range(5):
            data, sha = self.load()
            mutate(data)
            body = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
            r = requests.put(self._url(), headers=self.h, timeout=30, json={
                "message": message, "branch": self.branch, "sha": sha,
                "content": base64.b64encode(body.encode()).decode()})
            if r.ok:
                return data
            if r.status_code not in (409, 422):
                r.raise_for_status()
            time.sleep(2 + attempt * 2)
        raise RuntimeError("could not save backlog (kept conflicting)")

    def set(self, topic_id: str, message: str, **fields) -> dict:
        def m(d):
            t = next(t for t in d["topics"] if t["id"] == topic_id)
            for k, v in fields.items():
                if k == "posted":
                    t.setdefault("posted", {}).update(v)
                else:
                    t[k] = v
            t["updated_at"] = now()
        return self.update(m, message)
