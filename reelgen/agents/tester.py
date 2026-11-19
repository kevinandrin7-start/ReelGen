"""Tester agent: checks the finished video before it goes anywhere.

- format: 1080x1920, 30 fps, target length, AAC audio
- loudness: -14 LUFS +/- tolerance, true peak below -1 dBTP
- narration matches the script: Google Speech-to-Text transcript vs script (word error rate),
  overall and per scene, plus the list of words it heard differently (likely mispronounced)
- pacing: words per minute per scene, no long gaps inside a line, each line inside its scene
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .. import audio, config, textnorm
from ..models import Check, Script, TestReport
from .editor import Timing

Transcriber = Callable[[Path, List[str]], Tuple[str, List[Tuple[str, float, float]]]]


def run(video_path: Path, script: Script, timing: Timing, lex: Dict[str, str],
        transcribe: Optional[Transcriber] = None) -> TestReport:
    checks: List[Check] = []
    checks += _format_checks(video_path)
    checks += _loudness_checks(video_path)

    report = TestReport(passed=False, checks=checks)
    if transcribe is None:
        from ..gcloud import stt
        transcribe = stt.transcribe
    if transcribe is not False:  # False = offline test run, skip speech checks
        _speech_checks(video_path, script, timing, lex, transcribe, report)
    report.passed = all(c.passed for c in report.checks)
    return report


def _format_checks(path: Path) -> List[Check]:
    info = audio.probe(path)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    out = []
    ok = v is not None and v["width"] == config.W and v["height"] == config.H
    out.append(Check(name="resolution", passed=ok, detail=f"{v and v['width']}x{v and v['height']}"))
    fps = float(Fraction(v["r_frame_rate"])) if v else 0.0  # "30/1"
    out.append(Check(name="frame rate", passed=abs(fps - config.FPS) < 0.01, detail=f"{fps:.2f} fps"))
    out.append(Check(name="length", passed=abs(dur - config.TOTAL_SECONDS) <= 0.15, detail=f"{dur:.2f}s"))
    out.append(Check(name="audio track", passed=a is not None and a["codec_name"] == "aac",
                     detail=a["codec_name"] if a else "missing"))
    return out


def _loudness_checks(path: Path) -> List[Check]:
    m = audio.loudness(path)
    ok = abs(m["lufs"] - config.LOUDNESS_TARGET) <= config.LOUDNESS_TOLERANCE
    return [Check(name="loudness", passed=ok, detail=f"{m['lufs']:.1f} LUFS (target {config.LOUDNESS_TARGET})"),
            Check(name="true peak", passed=m["true_peak"] <= -0.5, detail=f"{m['true_peak']:.1f} dBTP")]


def _speech_checks(path: Path, script: Script, timing: Timing, lex: Dict[str, str],
                   transcribe: Transcriber, report: TestReport) -> None:
    wav = path.with_suffix(".check.wav")
    audio.run(["-i", str(path), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    narr = [l.narration for l in script.lines]
    acr = textnorm.acronyms_in(narr) | {k.lower() for k in lex if k.isupper()}
    as_word = {k.lower() for k, v in lex.items() if " " not in v.strip()}
    hints = sorted({w for w in " ".join(narr).replace(",", " ").split() if any(ch.isupper() for ch in w[1:])
                    or w.isupper()} | set(lex))
    transcript, words = transcribe(wav, hints)
    report.transcript = transcript

    ref_all = textnorm.normalize(" ".join(narr), acr, as_word)
    hyp_all = textnorm.normalize(transcript, acr, as_word)
    edits, ops = textnorm.align(ref_all, hyp_all)
    report.wer = edits / max(1, len(ref_all))
    report.misheard_words = sorted({r for op, r, h in ops if op in ("sub", "del") and r})
    report.checks.append(Check(name="narration matches script", passed=report.wer <= config.MAX_WER,
                               detail=f"word error rate {report.wer:.0%}"
                                      + (f"; differs at: {', '.join(report.misheard_words[:12])}"
                                         if report.misheard_words else "")))

    # per-scene: bucket recognised words by the scene window they fall in
    windows = [(s, s + d) for s, d in zip(timing.starts, timing.durations)]
    pacing_problems, gap_problems, scene_bad = [], [], []
    for i, (line, (ws, we)) in enumerate(zip(script.lines, windows)):
        sw = [(w, s, e) for (w, s, e) in words if ws - 0.05 <= (s + e) / 2 < we]
        ref = textnorm.normalize(line.narration, acr, as_word)
        hyp = textnorm.normalize(" ".join(w for w, _, _ in sw), acr, as_word)
        sw_wer = textnorm.wer(ref, hyp)
        report.scene_wer.append(round(sw_wer, 3))
        if sw_wer > config.MAX_SCENE_WER:
            scene_bad.append(f"{line.scene} {sw_wer:.0%}")
        if len(sw) >= 3:
            span = sw[-1][2] - sw[0][1]
            wpm = len(ref) / span * 60 if span > 0 else 0
            lo, hi = config.WPM_RANGE
            if not lo <= wpm <= hi:
                pacing_problems.append(f"{line.scene} {wpm:.0f} wpm")
            gaps = [b[1] - a[2] for a, b in zip(sw, sw[1:])]
            if gaps and max(gaps) > config.MAX_GAP_SECONDS:
                gap_problems.append(f"{line.scene} {max(gaps):.1f}s pause")
            if sw[-1][2] > we + 0.15:
                pacing_problems.append(f"{line.scene} runs past its scene")
    report.checks.append(Check(name="each scene's line is right", passed=not scene_bad,
                               detail="ok" if not scene_bad else "; ".join(scene_bad)))
    report.checks.append(Check(name="pacing", passed=not pacing_problems,
                               detail="ok" if not pacing_problems else "; ".join(pacing_problems)))
    report.checks.append(Check(name="no awkward pauses", passed=not gap_problems,
                               detail="ok" if not gap_problems else "; ".join(gap_problems)))


def failed_scene_indexes(report: TestReport) -> List[int]:
    return [i for i, w in enumerate(report.scene_wer) if w > config.MAX_SCENE_WER]
