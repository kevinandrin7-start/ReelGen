"""The topic backlog lives in backlog/topics.json in the repo. The dashboard edits it through
the GitHub API; the pipeline and the publisher edit it with `update()`, which pulls, applies
the change, commits and pushes, retrying if someone else pushed first."""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional

from . import config

log = logging.getLogger(__name__)

# statuses
QUEUED, IN_PROGRESS, READY, APPROVED, POSTING, POSTED, FAILED, REJECTED = (
    "queued", "in_progress", "ready", "approved", "posting", "posted", "failed", "rejected")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "topic"


def load() -> dict:
    if not config.BACKLOG_FILE.exists():
        return {"version": 1, "topics": []}
    return json.loads(config.BACKLOG_FILE.read_text())


def save(data: dict) -> None:
    config.BACKLOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.BACKLOG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def new_topic(title: str, notes: str = "") -> dict:
    return {"id": "t_" + uuid.uuid4().hex[:10], "title": title.strip(), "notes": notes.strip(),
            "status": QUEUED, "order": time.time(), "created_at": now(), "updated_at": now(),
            "attempts": 0, "error": None, "posted": {}}


def find(data: dict, topic_id: str) -> dict:
    for t in data["topics"]:
        if t["id"] == topic_id:
            return t
    raise KeyError(topic_id)


def next_queued(data: dict) -> Optional[dict]:
    q = [t for t in data["topics"] if t.get("status") == QUEUED]
    q.sort(key=lambda t: (t.get("order", 0), t.get("created_at", "")))
    return q[0] if q else None


def set_fields(t: dict, **fields) -> None:
    t.update(fields)
    t["updated_at"] = now()

# ------------------------------------------------------------------- git --


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=config.ROOT, check=check, capture_output=True, text=True)


def git_enabled() -> bool:
    return os.environ.get("REELGEN_GIT_PUSH") == "1"


def update(mutate: Callable[[dict], None], message: str, extra_paths: List[str] = (), tries: int = 5) -> dict:
    """Apply `mutate` to the freshest backlog and push it (when REELGEN_GIT_PUSH=1)."""
    if not git_enabled():
        data = load()
        mutate(data)
        save(data)
        return data
    branch = os.environ.get("REELGEN_GIT_BRANCH", "main")
    for attempt in range(tries):
        _git("pull", "--rebase", "--autostash", "origin", branch)
        data = load()
        mutate(data)
        save(data)
        _git("add", str(config.BACKLOG_FILE), *extra_paths)
        if _git("diff", "--cached", "--quiet", check=False).returncode == 0:
            return data  # nothing changed
        _git("commit", "-m", message)
        push = _git("push", "origin", f"HEAD:{branch}", check=False)
        if push.returncode == 0:
            return data
        log.warning("push rejected (attempt %d): %s", attempt + 1, push.stderr.strip()[:200])
        _git("reset", "--soft", "HEAD~1")
        _git("restore", "--staged", str(config.BACKLOG_FILE))
        _git("checkout", "--", str(config.BACKLOG_FILE))
        time.sleep(2 + attempt * 3)
    raise RuntimeError("could not push backlog update")
