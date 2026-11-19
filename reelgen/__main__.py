"""ReelGen command line.

  python -m reelgen produce              # make videos for the next queued topic(s)
  python -m reelgen produce --topic ID   # a specific topic
  python -m reelgen cleanup              # apply the Google Drive rules only
  python -m reelgen add "Topic" --notes "..."
  python -m reelgen demo                 # offline: render the RAG sample with a placeholder voice
"""
from __future__ import annotations

import argparse
import logging
import sys
import traceback
from datetime import date
from pathlib import Path

from . import backlog as B
from . import config, retention

log = logging.getLogger("reelgen")


def cmd_add(args) -> int:
    t = B.new_topic(args.title, args.notes or "")
    B.update(lambda d: d["topics"].append(t), f"Add topic: {t['title']}")
    print(t["id"])
    return 0


def cmd_cleanup(args) -> int:
    from .gcloud import drive
    room = retention.apply(drive.delete, room_for=0)
    print("drive has room" if room else "drive is full")
    return 0


def _summary(report) -> str:
    bad = [f"{c.name}: {c.detail}" for c in report.checks if not c.passed]
    return "All checks passed" if not bad else "Failed: " + " | ".join(bad)


def produce_one(topic_id: str | None) -> bool:
    from .agents import collaborator
    from .agents.scripter import full_caption
    from .gcloud import drive

    if not retention.apply(drive.delete, room_for=1):
        log.warning("Google Drive already holds %d videos waiting to be approved or posted; "
                    "skipping production until there is room.", config.DRIVE_MAX_VIDEOS)
        return False

    data = B.load()
    topic = B.find(data, topic_id) if topic_id else B.next_queued(data)
    if not topic:
        log.info("backlog is empty")
        return False
    tid, title = topic["id"], topic["title"]
    B.update(lambda d: B.set_fields(B.find(d, tid), status=B.IN_PROGRESS, started_at=B.now(),
                                    attempts=B.find(d, tid).get("attempts", 0) + 1, error=None),
             f"Start: {title}")
    try:
        res = collaborator.produce(title, topic.get("notes", ""))
        name = f"{date.today().isoformat()} {title}.mp4"
        up = drive.upload(res.video, name, description=full_caption(res.script))
        rel_dir = str(res.run_dir.relative_to(config.ROOT))

        def done(d):
            B.set_fields(B.find(d, tid), status=B.READY, finished_at=B.now(), run_dir=rel_dir,
                         drive_file_id=up["id"], drive_link=up.get("webViewLink"),
                         caption=full_caption(res.script), youtube_title=res.script.youtube_title,
                         youtube_description=res.script.youtube_description,
                         test_passed=res.report.passed, test_summary=_summary(res.report),
                         thumbnail=f"{rel_dir}/thumbnail.jpg")
        B.update(done, f"Ready for approval: {title}", extra_paths=[rel_dir])
        log.info("done: %s -> %s", title, up.get("webViewLink"))
        return True
    except Exception as e:  # record the failure on the topic so the dashboard shows it
        log.error("failed: %s\n%s", e, traceback.format_exc())
        msg = f"{type(e).__name__}: {e}"[:500]

        def fail(d):
            t = B.find(d, tid)
            give_up = t.get("attempts", 1) >= config.MAX_ATTEMPTS
            B.set_fields(t, status=B.FAILED if give_up else B.QUEUED, error=msg)
        B.update(fail, f"Failed: {title}")
        raise


def cmd_produce(args) -> int:
    ok = True
    for i in range(1 if args.topic else config.TOPICS_PER_RUN):
        try:
            if not produce_one(args.topic):
                break
        except Exception:
            ok = False
    return 0 if ok else 1


def cmd_demo(args) -> int:
    """Offline end-to-end run using the RAG fixtures and a placeholder tone voice."""
    import json
    import subprocess

    from .agents import collaborator
    from .models import Research, ScenePlan, Script

    fx = config.ROOT / "fixtures"
    research = Research.model_validate_json((fx / "rag_research.json").read_text())
    script = Script.model_validate_json((fx / "rag_script.json").read_text())
    plan = ScenePlan.model_validate_json((fx / "rag_plan.json").read_text())

    def fake_synth(text: str, out: Path) -> Path:
        secs = max(1.0, len(text.split()) * 0.36)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"sine=frequency=220:sample_rate=24000:duration={secs:.2f}", "-af", "volume=0.3",
                        str(out)], check=True)
        return out

    hooks = collaborator.Hooks(research=lambda t, n: (research, "(fixture)"),
                               script=lambda r, lex, fb=None: script,
                               direct=lambda s, r: plan, synth=fake_synth, transcribe=False)
    res = collaborator.produce("RAG demo", hooks=hooks)
    print(json.dumps({"video": str(res.video), "run_dir": str(res.run_dir),
                      "passed": res.report.passed,
                      "checks": [c.model_dump() for c in res.report.checks]}, indent=2))
    return 0


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(prog="reelgen")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("produce"); p.add_argument("--topic"); p.set_defaults(fn=cmd_produce)
    p = sub.add_parser("cleanup"); p.set_defaults(fn=cmd_cleanup)
    p = sub.add_parser("add"); p.add_argument("title"); p.add_argument("--notes"); p.set_defaults(fn=cmd_add)
    p = sub.add_parser("demo"); p.set_defaults(fn=cmd_demo)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
