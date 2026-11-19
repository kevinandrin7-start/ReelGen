"""Collaborator (orchestrator): runs one topic through every agent, passes each agent's
output to the next, retries what can be retried, and saves every hand-off to runs/<slug>/."""
from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, List, Optional

from pydantic import BaseModel

from .. import config, llm
from ..models import Research, ScenePlan, Script, TestReport
from ..render import video
from . import director, editor, researcher, scripter, sound_engineer, tester

log = logging.getLogger(__name__)


class Respelling(BaseModel):
    word: str
    say_as: str


class Respellings(BaseModel):
    respellings: List[Respelling]


@dataclass
class Result:
    run_dir: Path
    video: Path
    script: Script
    report: TestReport
    files: List[str] = field(default_factory=list)


@dataclass
class Hooks:
    """Swap points for tests and offline runs."""
    research: Optional[Callable[[str, str], tuple]] = None
    script: Optional[Callable[..., Script]] = None
    direct: Optional[Callable[[Script, Research], ScenePlan]] = None
    synth: Optional[Callable] = None
    transcribe: object = None  # None = Google STT, False = skip speech checks
    respell: Optional[Callable[[List[str], Script], dict]] = None


def run_dir_for(title: str) -> Path:
    from ..backlog import slugify
    return config.RUNS_DIR / f"{date.today().isoformat()}-{slugify(title)}"


def _save(path: Path, obj) -> None:
    path.write_text(obj.model_dump_json(indent=2) if hasattr(obj, "model_dump_json") else obj)


def produce(title: str, notes: str = "", hooks: Hooks = Hooks()) -> Result:
    rd = run_dir_for(title)
    rd.mkdir(parents=True, exist_ok=True)
    work = config.WORK_DIR / rd.name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    lex = sound_engineer.load_pronunciations()

    # 1. Researcher
    log.info("researcher: %s", title)
    research, notes_md = (hooks.research or researcher.run)(title, notes)
    _save(rd / "research.json", research)
    _save(rd / "research_notes.md", notes_md)

    # 2-3. Scripter -> Director, 4. Sound engineer, 5. Editor (with a re-write if it runs long)
    feedback = None
    for attempt in range(3):
        log.info("scripter (attempt %d)", attempt + 1)
        script = (hooks.script or scripter.run)(research, lex, feedback)
        _save(rd / "script.json", script)
        log.info("director")
        plan = (hooks.direct or director.run)(script, research)
        _save(rd / "scene_plan.json", plan)
        log.info("sound engineer")
        clips = sound_engineer.run(script, work / "voice", lex, synth=hooks.synth)
        scenes = [l.scene for l in script.lines]
        try:
            log.info("editor")
            out = work / "final.mp4"
            timing = editor.run(plan, clips, scenes, work / "edit", out)
            break
        except editor.TooLong as e:
            feedback = (f"The narration is too long: {e}. It has {script.word_count()} words. "
                        "Cut it to about 70 words without losing accuracy.")
            log.warning(feedback)
    else:
        raise RuntimeError("script still too long after 3 attempts")

    # 6. Tester, with up to MAX_VOICE_RETRIES re-recordings of lines it heard wrong
    run_lex = dict(lex)
    for attempt in range(config.MAX_VOICE_RETRIES + 1):
        log.info("tester (attempt %d)", attempt + 1)
        report = tester.run(out, script, timing, run_lex, transcribe=hooks.transcribe)
        _save(rd / "test_report.json", report)
        if report.passed or attempt == config.MAX_VOICE_RETRIES:
            break
        bad = tester.failed_scene_indexes(report)
        if not bad or not report.misheard_words:
            break  # not a pronunciation problem; re-recording won't help
        fixes = (hooks.respell or _respell)(report.misheard_words, script)
        if not fixes:
            break
        run_lex.update(fixes)
        log.info("re-recording scenes %s with respellings %s", bad, fixes)
        clips = sound_engineer.run(script, work / "voice", run_lex, synth=hooks.synth, only=bad, previous=clips)
        timing = editor.run(plan, clips, scenes, work / "edit", out)

    # thumbnail for the dashboard
    thumb = rd / "thumbnail.jpg"
    t_mid = timing.starts[2] + timing.durations[2] * 0.8
    video.frame(plan, timing.durations, t_mid).convert("RGB").resize((360, 640)).save(thumb, quality=82)
    (rd / "caption.txt").write_text(scripter.full_caption(script) + "\n")
    if run_lex != lex:
        (rd / "pronunciation_fixes.json").write_text(json.dumps(
            {k: v for k, v in run_lex.items() if lex.get(k) != v}, indent=2))
    return Result(rd, out, script, report, [str(p.relative_to(config.ROOT)) for p in rd.iterdir()])


def _respell(words: List[str], script: Script) -> dict:
    prompt = ("Text-to-speech mispronounced or slurred these words in a narration (the speech checker "
              f"heard them wrong): {words}.\nNarration: " + " ".join(l.narration for l in script.lines)
              + "\nFor each word that is likely mispronounced (technical terms, acronyms, names), give a "
                "respelling a TTS voice will say correctly, e.g. 'LLM' -> 'L L M', 'GPT' -> 'G P T', "
                "'Kubernetes' -> 'koo-ber-net-eez'. Skip ordinary words.")
    out = llm.structured("You fix text-to-speech pronunciation.", prompt, Respellings,
                         effort=config.EFFORT_STRUCTURE, max_tokens=4000)
    return {r.word: r.say_as for r in out.respellings if r.word and r.say_as and r.word != r.say_as}
