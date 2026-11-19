from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from reelgen import backlog as B
from reelgen import config, retention, textnorm
from reelgen.agents import editor, sound_engineer, tester
from reelgen.models import Script

FX = Path(__file__).resolve().parent.parent / "fixtures"


def test_normalize_acronyms_and_numbers():
    acr = {"llm", "rag"}
    assert textnorm.normalize("LLMs use 30% of RAG", acr, {"rag"}) == \
        ["l", "l", "m", "use", "thirty", "percent", "of", "rag"]
    assert textnorm.normalize("L L M", acr) == ["l", "l", "m"]


def test_wer_and_misheard():
    ref = "the fix is rag".split()
    hyp = "the fix is rack".split()
    assert textnorm.wer(ref, hyp) == 0.25
    _, ops = textnorm.align(ref, hyp)
    assert ("sub", "rag", "rack") in ops


def test_pronunciations_whole_words_only():
    lex = {"RAG": "rag", "AI": "A I"}
    assert sound_engineer.apply_pronunciations("RAG for AI, not RAGE or SAID", lex) == "rag for A I, not RAGE or SAID"


def test_timing_fits_30s_and_speeds_up():
    scenes = ["hook", "problem", "define", "steps", "payoff"]
    t = editor.plan_timing([2.5, 4.5, 3.5, 12.0, 3.8], scenes)
    assert abs(sum(t.durations) - 30) < 1e-6
    assert all(abs(d * 30 - round(d * 30)) < 1e-6 for d in t.durations)
    t2 = editor.plan_timing([3, 5.5, 4, 13.5, 4.3], scenes)
    assert t2.speed > config.VOICE_SPEED
    with pytest.raises(editor.TooLong):
        editor.plan_timing([5, 9, 6, 20, 6], scenes)


def _topic(**kw):
    t = B.new_topic("x")
    t.update(kw)
    return t


def test_retention_rules():
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)
    iso = lambda d: (now - timedelta(days=d)).isoformat().replace("+00:00", "Z")
    old = _topic(status="posted", drive_file_id="a", posted={"instagram": iso(4), "youtube": iso(3.5)})
    fresh = _topic(status="posted", drive_file_id="b", posted={"instagram": iso(1), "youtube": iso(1)})
    half = _topic(status="posting", drive_file_id="c", posted={"instagram": iso(5)})
    rej = _topic(status="rejected", drive_file_id="d")
    gone = _topic(status="posted", drive_file_id="e", drive_deleted_at=iso(1), posted={"instagram": iso(9), "youtube": iso(9)})
    data = {"topics": [old, fresh, half, rej, gone]}
    dels, room = retention.plan_deletions(data, now)
    assert {t["drive_file_id"] for t in dels} == {"a", "d"}
    assert room


def test_retention_full_deletes_oldest_posted_then_pauses():
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)
    iso = lambda d: (now - timedelta(days=d)).isoformat().replace("+00:00", "Z")
    posted = [_topic(status="posted", drive_file_id=f"p{i}", posted={"instagram": iso(i / 10 + .1), "youtube": iso(i / 10 + .1)})
              for i in range(2)]
    waiting = [_topic(status="ready", drive_file_id=f"w{i}") for i in range(3)]
    dels, room = retention.plan_deletions({"topics": posted + waiting}, now)
    assert [t["drive_file_id"] for t in dels] == ["p1"]  # oldest posted
    assert room
    waiting5 = [_topic(status="ready", drive_file_id=f"w{i}") for i in range(5)]
    dels, room = retention.plan_deletions({"topics": waiting5}, now)
    assert dels == [] and not room  # never deletes unapproved videos


def test_next_queued_respects_order():
    a, b, c = B.new_topic("a"), B.new_topic("b"), B.new_topic("c")
    a["order"], b["order"], c["order"] = 3, 1, 2
    c["status"] = "ready"
    assert B.next_queued({"topics": [a, b, c]})["title"] == "b"


def test_tester_speech_checks_with_fake_transcript(tmp_path):
    script = Script.model_validate_json((FX / "rag_script.json").read_text())
    timing = editor.Timing(1.06, [3.0, 5.4, 4.2, 13.0, 4.4], [0, 3.0, 8.4, 12.6, 25.6])
    # fake words: spread each line's words through its scene window at ~170 wpm
    words, text = [], []
    for line, s, d in zip(script.lines, timing.starts, timing.durations):
        toks = line.narration.replace("RAG", "rag").replace("AI", "A I").split()
        step = 60 / 170
        for i, w in enumerate(toks):
            st = s + 0.2 + i * step
            words.append((w, st, st + step * 0.8))
        text += toks
    report = tester.TestReport(passed=False, checks=[])
    lex = {"RAG": "rag", "AI": "A I"}
    import reelgen.audio as A
    orig = A.run
    A.run = lambda args: None
    try:
        tester._speech_checks(tmp_path / "v.mp4", script, timing, lex, lambda p, h: (" ".join(text), words), report)
    finally:
        A.run = orig
    by = {c.name: c for c in report.checks}
    assert report.wer == 0
    assert by["narration matches script"].passed
    assert by["each scene's line is right"].passed


def test_session_validate_and_length_warnings(tmp_path, monkeypatch, capsys):
    import shutil
    from reelgen import session
    from reelgen.models import ScenePlan
    rd = tmp_path / "runs" / "x"
    rd.mkdir(parents=True)
    for src, dst in [("rag_research.json", "research.json"), ("rag_script.json", "script.json"),
                     ("rag_plan.json", "scene_plan.json")]:
        shutil.copy(FX / src, rd / dst)
    monkeypatch.setattr(config, "ROOT", tmp_path)
    assert session.validate("runs/x") == 0
    plan = ScenePlan.model_validate_json((FX / "rag_plan.json").read_text())
    plan.hook.line1 = "A very long first line of the hook question"
    assert any("hook.line1" in w for w in session._plan_length_warnings(plan))
    (rd / "script.json").write_text('{"title": "x"}')
    assert session.validate("runs/x") == 1


def test_activity_records_each_agent():
    import json
    from reelgen import activity as A
    from reelgen.models import Research, Script, TestReport
    fx = Path(__file__).resolve().parent.parent / "fixtures"
    research = Research.model_validate_json((fx / "rag_research.json").read_text())
    script = Script.model_validate_json((fx / "rag_script.json").read_text())
    report = TestReport(passed=True, checks=[], wer=0.04)
    data = {"version": 1, "topics": []}
    A.production(data, "RAG", research, script, report, 30.0, respellings=1, test_summary="All checks passed")
    ag = data["agents"]
    for k in (A.RESEARCHER, A.SCRIPTER, A.DIRECTOR, A.SOUND, A.EDITOR, A.TESTER, A.DRIVE, A.COLLABORATOR):
        assert ag[k]["topic"] == "RAG" and ag[k]["ok"] and ag[k]["at"].endswith("Z")
    assert "with 1 pronunciation fix." in ag[A.SOUND]["task"]
    assert "30.0-second" in ag[A.EDITOR]["task"]
    assert "4%" in ag[A.TESTER]["task"]
    json.dumps(data)  # stays plain JSON for the dashboard


def test_rushed_line_is_slowed_but_others_keep_speed():
    scenes = ["hook", "problem", "define", "steps", "payoff"]
    # hook: 9 words in 2.6s (208 wpm natural) -> slowed; the rest are normal
    t = editor.plan_timing([2.6, 4.4, 4.9, 11.0, 4.6], scenes, words=[9, 13, 10, 33, 12])
    assert t.speeds[0] < 1.0 and 9 / (2.6 / t.speeds[0]) * 60 <= config.MAX_LINE_WPM + 1
    assert t.speeds[3] == t.speed
    assert abs(sum(t.durations) - 30) < 1e-6


def test_voiced_span_ignores_silence_at_edges():
    quiet = [(0.0, 0.3), (2.1, 2.9)]
    assert abs(tester._voiced_span(quiet, 0.0, 2.6) - 1.8) < 1e-9
