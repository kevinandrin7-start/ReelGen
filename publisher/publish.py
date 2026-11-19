"""ReelGen publisher. Runs on your laptop, posts approved videos from Google Drive to
YouTube Shorts and Instagram Reels through a Chrome profile that is signed in to the
channel accounts.

  python publish.py login              # one time: opens Chrome so you can sign in to both sites
  python publish.py run                # post every approved video (oldest first)
  python publish.py run --dry-run      # fill everything in but stop before Publish/Share
  python publish.py run --max 1        # post at most one video this run
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # so `reelgen` (Drive client) imports from the repo


def load_env() -> None:
    env = HERE / ".env"
    if not env.exists():
        sys.exit(f"Missing {env}. Copy .env.example to .env and fill it in.")
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


load_env()

from playwright.sync_api import sync_playwright  # noqa: E402

from github_backlog import Backlog, now  # noqa: E402
from reelgen.gcloud import drive  # noqa: E402
import sites  # noqa: E402

log = logging.getLogger("publisher")
PROFILE = Path(os.environ.get("REELGEN_CHROME_PROFILE", HERE / "chrome-profile"))
DOWNLOADS = HERE / "downloads"


def browser(p):
    # A separate Chrome profile just for the channel accounts, never your personal profile.
    return p.chromium.launch_persistent_context(
        str(PROFILE), channel="chrome", headless=False, viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"])


def cmd_login(args) -> None:
    with sync_playwright() as p:
        ctx = browser(p)
        ctx.pages[0].goto("https://www.instagram.com/accounts/login/")
        ctx.new_page().goto("https://studio.youtube.com/")
        input("Sign in to the channel's Instagram and YouTube accounts in the Chrome window, "
              "then press Enter here to save the session... ")
        ctx.close()


def cmd_run(args) -> int:
    bl = Backlog(os.environ["GITHUB_REPO"], os.environ["GITHUB_TOKEN"])
    data, _ = bl.load()
    todo = [t for t in data["topics"] if t.get("status") in ("approved", "posting") and t.get("drive_file_id")
            and not t.get("drive_deleted_at")]
    todo.sort(key=lambda t: t.get("approved_at") or t.get("updated_at") or "")
    todo = todo[: args.max]
    if not todo:
        log.info("nothing approved to post")
        return 0
    DOWNLOADS.mkdir(exist_ok=True)
    failures = 0
    with sync_playwright() as p:
        ctx = browser(p)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for t in todo:
            tid, title = t["id"], t["title"]
            posted = dict(t.get("posted") or {})
            log.info("posting %s", title)
            if not args.dry_run:
                bl.set(tid, f"Posting: {title}", status="posting", error=None)
            video = DOWNLOADS / f"{tid}.mp4"
            if not video.exists():
                drive.download(t["drive_file_id"], video)
            try:
                if not posted.get("youtube"):
                    url = sites.post_youtube(page, video, t.get("youtube_title") or title,
                                             t.get("youtube_description") or "", args.dry_run)
                    if not args.dry_run:
                        posted.update(youtube=now(), youtube_url=url)
                        bl.set(tid, f"Posted to YouTube: {title}", posted={"youtube": now(), "youtube_url": url})
                if not posted.get("instagram"):
                    sites.post_instagram(page, video, t.get("caption") or title, args.dry_run)
                    if not args.dry_run:
                        posted.update(instagram=now())
                        bl.set(tid, f"Posted to Instagram: {title}", posted={"instagram": now()})
                if not args.dry_run:
                    bl.set(tid, f"Posted: {title}", status="posted",
                           agent_task="Posted the video to YouTube Shorts and Instagram Reels.")
                    video.unlink(missing_ok=True)
                log.info("done: %s%s", title, " (dry run, nothing published)" if args.dry_run else "")
            except sites.PostError as e:
                failures += 1
                log.error("%s", e)
                if not args.dry_run:
                    bl.set(tid, f"Posting failed: {title}", status="approved", error=str(e)[:400],
                           agent_task=f"Posting failed: {e}", agent_ok=False)
            sites.pause(20, 40)  # space posts out
        ctx.close()
    return 1 if failures else 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(HERE / "publisher.log")])
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login").set_defaults(fn=cmd_login)
    r = sub.add_parser("run")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--max", type=int, default=2)
    r.set_defaults(fn=cmd_run)
    args = ap.parse_args()
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
