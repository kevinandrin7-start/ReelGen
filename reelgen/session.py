"""Commands for running the pipeline from a scheduled Claude Code session (your Claude plan),
instead of calling the Claude API. The session itself acts as the Researcher, Scripter and
Director and writes their JSON files; these commands do everything else. See ROUTINE.md.

Exit codes: 0 ok, 2 Drive full, 3 script too long, 4 narration check failed, 5 queue empty.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from . import backlog as B
from . import config, retention
from .models import Research, ScenePlan, Script

FILES = {"research": ("research.json", Research), "script": ("script.json", Script),
         "plan": ("scene_plan.json", ScenePlan)}


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def brief(step: str) -> int:
    """Print an agent's instructions and the JSON schema its file must follow."""
    from .agents import director, researcher, scripter
    system = {"research": researcher.SYSTEM, "script": scripter.SYSTEM, "plan": director.SYSTEM}[step]
    name, model = FILES[step]
    print(f"# {step}: write {name}\n\n## Instructions\n{system}\n\n## JSON schema\n"
          + json.dumps(model.model_json_schema(), indent=1))
    if step == "script":
        print("\n## Pronunciation dictionary (use these in `spoken`)\n"
              + json.dumps(json.loads(config.PRONUNCIATIONS_FILE.read_text()), indent=1))
    return 0


def start(topic_id: str | None) -> int:
    from .gcloud import drive
    if not retention.apply(drive.delete, room_for=1):
        _out({"status": "drive_full", "message": f"Drive already holds {config.DRIVE_MAX_VIDEOS} videos waiting "
              "for approval or posting. Nothing to do until Kevin approves or rejects one."})
        return 2
    data = B.load()
    topic = B.find(data, topic_id) if topic_id else B.next_queued(data)
    if not topic:
        _out({"status": "queue_empty"})
        return 5
    tid, title = topic["id"], topic["title"]
    rd = config.RUNS_DIR / f"{date.today().isoformat()}-{B.slugify(title)}"
    rel = str(rd.relative_to(config.ROOT))
    B.update(lambda d: B.set_fields(B.find(d, tid), status=B.IN_PROGRESS, started_at=B.now(), run_dir=rel,
                                    attempts=B.find(d, tid).get("attempts", 0) + 1, error=None),
             f"Start: {title}")
    rd.mkdir(parents=True, exist_ok=True)
    _out({"status": "started", "topic_id": tid, "title": title, "notes": topic.get("notes", ""),
          "run_dir": rel, "write": [f"{rel}/{f}" for f, _ in FILES.values()] + [f"{rel}/research_notes.md"]})
    return 0


def validate(run_dir: str) -> int:
    from .agents import scripter
    rd = config.ROOT / run_dir
    problems, warnings = [], []
    loaded = {}
    for step, (name, model) in FILES.items():
        p = rd / name
        if not p.exists():
            problems.append(f"{name} is missing")
            continue
        try:
            loaded[step] = model.model_validate_json(p.read_text())
        except ValidationError as e:
            problems.append(f"{name}: {e}")
    if "script" in loaded:
        s = loaded["script"]
        try:
            scripter._validate(s)
            (rd / "script.json").write_text(s.model_dump_json(indent=2))  # store the tidied title/hashtags
        except ValueError as e:
            problems.append(str(e))
        wc = s.word_count()
        if not 55 <= wc <= 90:
            warnings.append(f"script has {wc} words; aim for 65-80")
    if "plan" in loaded:
        warnings += _plan_length_warnings(loaded["plan"])
    _out({"ok": not problems, "problems": problems, "warnings": warnings})
    return 0 if not problems else 1


def _plan_length_warnings(plan: ScenePlan) -> list[str]:
    out = []
    for scene_name in ("hook", "problem", "define", "steps", "payoff"):
        scene = getattr(plan, scene_name)
        for field, info in type(scene).model_fields.items():
            desc = info.description or ""
            if "<=" in desc:
                limit = int(desc.split("<=")[1].split()[0])
                val = getattr(scene, field)
                if isinstance(val, str) and len(val) > limit:
                    out.append(f"{scene_name}.{field} is {len(val)} chars (limit {limit}): {val!r}")
    for i, st in enumerate(plan.steps.steps):
        if len(st.title) > 22 or len(st.sub) > 32:
            out.append(f"steps.steps[{i}] text is long and will be shrunk: {st.title!r} / {st.sub!r}")
    return out


def preview(run_dir: str) -> int:
    """Render one still per scene into <run_dir>/preview.png to check the layout before finishing."""
    from PIL import Image

    from .render import video
    rd = config.ROOT / run_dir
    plan = ScenePlan.model_validate_json((rd / "scene_plan.json").read_text())
    durations = [3.0, 5.0, 4.0, 13.5, 4.5]
    times = [2.6, 7.6, 11.6, 25.0, 29.6]  # late in each scene, when everything is on screen
    tiles = [video.frame(plan, durations, t).convert("RGB").resize((360, 640)) for t in times]
    sheet = Image.new("RGB", (360 * 5, 640))
    for i, im in enumerate(tiles):
        sheet.paste(im, (i * 360, 0))
    path = rd / "preview.png"
    sheet.save(path)
    _out({"preview": str(path.relative_to(config.ROOT))})
    return 0


def finish(topic_id: str, accept: bool = False) -> int:
    from .__main__ import _summary
    from .agents import collaborator, editor, scripter, sound_engineer
    from .gcloud import drive

    data = B.load()
    topic = B.find(data, topic_id)
    rel = topic.get("run_dir")
    if not rel:
        print("topic has no run_dir; run `start` first", file=sys.stderr)
        return 1
    if validate(rel) != 0:
        return 1
    rd = config.ROOT / rel
    research = Research.model_validate_json((rd / "research.json").read_text())  # noqa: F841 (validated)
    script = Script.model_validate_json((rd / "script.json").read_text())
    plan = ScenePlan.model_validate_json((rd / "scene_plan.json").read_text())
    lex = sound_engineer.load_pronunciations()
    extra = rd / "respellings.json"
    if extra.exists():
        lex.update(json.loads(extra.read_text()))
    work = config.WORK_DIR / rd.name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    try:
        out, report = collaborator.make_video(rd, work, script, plan, lex, respell=None, max_retries=0)
    except editor.TooLong as e:
        _out({"status": "too_long", "message": str(e), "words": script.word_count(),
              "fix": "Shorten script.json (keep it accurate, about 70 words), validate, and run finish again."})
        return 3
    summary = _summary(report)
    speech_failed = any(not c.passed for c in report.checks
                        if c.name in ("narration matches script", "each scene's line is right"))
    if not report.passed and speech_failed and not accept:
        _out({"status": "narration_check_failed", "summary": summary, "misheard_words": report.misheard_words,
              "transcript": report.transcript, "scene_wer": report.scene_wer,
              "fix": f"Write {rel}/respellings.json mapping each mispronounced word as written in the script to "
                     "a spelling the voice will say correctly (e.g. {\"Kubernetes\": \"koo-ber-net-eez\"}), then "
                     "run finish again. After 2 tries, run finish with --accept."})
        return 4

    name = f"{date.today().isoformat()} {topic['title']}.mp4"
    up = drive.upload(out, name, description=scripter.full_caption(script))

    def done(d):
        B.set_fields(B.find(d, topic_id), status=B.READY, finished_at=B.now(), drive_file_id=up["id"],
                     drive_link=up.get("webViewLink"), caption=scripter.full_caption(script),
                     youtube_title=script.youtube_title, youtube_description=script.youtube_description,
                     test_passed=report.passed, test_summary=summary, thumbnail=f"{rel}/thumbnail.jpg")
    B.update(done, f"Ready for approval: {topic['title']}", extra_paths=[rel])
    _out({"status": "ready", "drive_link": up.get("webViewLink"), "test_passed": report.passed, "summary": summary})
    return 0


def fail(topic_id: str, message: str) -> int:
    def m(d):
        t = B.find(d, topic_id)
        give_up = t.get("attempts", 1) >= config.MAX_ATTEMPTS
        B.set_fields(t, status=B.FAILED if give_up else B.QUEUED, error=message[:500])
    title = B.find(B.load(), topic_id)["title"]
    B.update(m, f"Failed: {title}")
    return 0
