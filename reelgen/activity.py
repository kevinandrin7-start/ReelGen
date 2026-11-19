"""Each agent's last task, kept under "agents" in backlog/topics.json so the dashboard's
Show Workflow view can show it. Every function here only changes the dict it is given; callers
save it as part of the backlog update they were already making, so no extra commits."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

# Agent ids, shared with docs/app.js.
COLLABORATOR, RESEARCHER, SCRIPTER, DIRECTOR = "collaborator", "researcher", "scripter", "director"
SOUND, EDITOR, TESTER, DRIVE, DRIVE_KEEPER, PUBLISHER = (
    "sound_engineer", "editor", "tester", "drive", "drive_keeper", "publisher")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record(data: dict, agent: str, task: str, ok: bool = True, topic: Optional[str] = None) -> None:
    data.setdefault("agents", {})[agent] = {"task": task[:300], "ok": ok, "topic": topic, "at": _now()}


def production(data: dict, title: str, research, script, report, video_seconds: float, respellings: int = 0,
               test_summary: str = "") -> None:
    """Record every production agent after a video is made and uploaded."""
    record(data, RESEARCHER, f"Researched the topic from {len(research.sources)} sources, "
                             f"with {len(research.key_facts)} key facts and {len(research.analogies)} analogies.",
           topic=title)
    record(data, SCRIPTER, f"Wrote a {script.word_count()}-word, 5-line script and the captions.", topic=title)
    record(data, DIRECTOR, "Planned the 5 scenes: hook, problem, definition, steps and payoff.", topic=title)
    fixes = f", with {respellings} pronunciation fix{'es' if respellings != 1 else ''}" if respellings else ""
    record(data, SOUND, f"Recorded the narration ({len(script.lines)} lines){fixes}.", topic=title)
    record(data, EDITOR, f"Rendered and mixed a {video_seconds:.1f}-second 1080x1920 video.", topic=title)
    wer = f" Word error rate {report.wer:.0%}." if report.wer is not None else ""
    record(data, TESTER, (test_summary or ("All checks passed" if report.passed else "Some checks failed")) + "." + wer,
           ok=report.passed, topic=title)
    record(data, DRIVE, "Stored the video, waiting for your approval.", topic=title)
    record(data, COLLABORATOR, "Finished the run and sent the video for approval.", topic=title)
