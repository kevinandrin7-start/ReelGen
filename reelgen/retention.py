"""Google Drive housekeeping.

Rules:
- A video posted to both Instagram and YouTube is deleted from Drive 3 days after the later post.
- Rejected videos are deleted right away.
- Drive never holds more than 5 videos. If it is full, the oldest posted video goes first.
- If it is still full (nothing has been posted yet), production pauses until you approve or
  reject something, so unapproved videos are never deleted.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Tuple

from . import activity as A
from . import backlog as B
from . import config

log = logging.getLogger(__name__)


def in_drive(t: dict) -> bool:
    return bool(t.get("drive_file_id")) and not t.get("drive_deleted_at")


def fully_posted(t: dict) -> bool:
    p = t.get("posted") or {}
    return bool(p.get("instagram")) and bool(p.get("youtube"))


def posted_at(t: dict) -> datetime:
    p = t.get("posted") or {}
    times = [B.parse_time(p.get(k)) for k in ("instagram", "youtube") if p.get(k)]
    return max(times) if times else datetime.max.replace(tzinfo=timezone.utc)


def plan_deletions(data: dict, now: datetime, room_for: int = 1) -> Tuple[List[dict], bool]:
    """Returns (topics whose Drive file should be deleted, whether there's room for new videos)."""
    live = [t for t in data["topics"] if in_drive(t)]
    keep_for = timedelta(days=config.DRIVE_KEEP_DAYS_AFTER_POST)
    delete = [t for t in live if t.get("status") == B.REJECTED
              or (fully_posted(t) and now - posted_at(t) >= keep_for)]
    remaining = [t for t in live if t not in delete]
    posted_left = sorted([t for t in remaining if fully_posted(t)], key=posted_at)
    while len(remaining) + room_for > config.DRIVE_MAX_VIDEOS and posted_left:
        t = posted_left.pop(0)
        delete.append(t)
        remaining.remove(t)
    return delete, len(remaining) + room_for <= config.DRIVE_MAX_VIDEOS


def apply(delete_file: Callable[[str], None], room_for: int = 1) -> bool:
    """Deletes what the rules say and records it in the backlog. Returns True if there's room."""
    now = datetime.now(timezone.utc)
    to_delete, has_room = plan_deletions(B.load(), now, room_for)
    ids = []
    for t in to_delete:
        log.info("deleting %s (%s) from Drive", t["drive_file_id"], t["title"])
        delete_file(t["drive_file_id"])
        ids.append(t["id"])
    if ids:
        def mark(data):
            for tid in ids:
                B.set_fields(B.find(data, tid), drive_deleted_at=B.now())
            A.record(data, A.DRIVE_KEEPER, f"Removed {len(ids)} video(s) from Drive (posted 3+ days ago, "
                                           "rejected, or to make room).")
        B.update(mark, f"Drive cleanup: removed {len(ids)} video(s)")
    return has_room
