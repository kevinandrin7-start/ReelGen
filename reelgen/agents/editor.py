"""Editor agent: fits scene lengths to the narration, renders the video, and mixes
the voice on top (speed-up, per-scene placement, -14 LUFS loudness)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .. import audio, config
from ..models import ScenePlan
from ..render import video

TAIL = 0.35  # breathing room after each line
MIN_SCENE = {"hook": 2.4, "problem": 4.0, "define": 3.4, "steps": 9.0, "payoff": 3.6}
EXTRA_WEIGHT = {"hook": 0.5, "problem": 1.0, "define": 1.0, "steps": 2.0, "payoff": 1.5}


class TooLong(Exception):
    """Narration can't fit the target length even at max speed."""


@dataclass
class Timing:
    speed: float
    durations: List[float]
    starts: List[float]


def plan_timing(clip_lengths: List[float], scenes: List[str], total: float = None) -> Timing:
    total = total or config.TOTAL_SECONDS
    speed = config.VOICE_SPEED
    while True:
        need = [l / speed + config.VOICE_LEAD_IN + TAIL for l in clip_lengths]
        need = [max(n, MIN_SCENE.get(s, 2.0)) for n, s in zip(need, scenes)]
        if sum(need) <= total or speed >= config.VOICE_MAX_SPEED:
            break
        speed = min(config.VOICE_MAX_SPEED, speed + 0.01)
    if sum(need) > total + 1e-6:
        raise TooLong(f"narration needs {sum(need):.1f}s at {speed:.2f}x, target is {total:.0f}s")
    spare = total - sum(need)
    wsum = sum(EXTRA_WEIGHT.get(s, 1.0) for s in scenes)
    durations = [n + spare * EXTRA_WEIGHT.get(s, 1.0) / wsum for n, s in zip(need, scenes)]
    # snap to frames, put rounding error on the last scene
    fps = config.FPS
    durations = [round(d * fps) / fps for d in durations]
    durations[-1] = round((total - sum(durations[:-1])) * fps) / fps
    starts, acc = [], 0.0
    for d in durations:
        starts.append(acc)
        acc += d
    return Timing(speed, durations, starts)


def mix_voice(clips: List[Path], timing: Timing, out_wav: Path) -> Path:
    args, filters, labels = [], [], []
    for i, c in enumerate(clips):
        args += ["-i", str(c)]
        delay = int((timing.starts[i] + config.VOICE_LEAD_IN) * 1000)
        filters.append(f"[{i}:a]aresample=48000,atempo={timing.speed:.3f},adelay={delay}|{delay}[a{i}]")
        labels.append(f"[a{i}]")
    total = sum(timing.durations)
    # loudnorm trims a little at the end, so pad/trim to the exact length after it
    filters.append(f"{''.join(labels)}amix=inputs={len(clips)}:normalize=0,apad=pad_dur=1,"
                   f"loudnorm=I={config.LOUDNESS_TARGET}:TP=-1.5:LRA=11,aresample=48000,"
                   f"apad,atrim=0:{total:.3f}[out]")
    audio.run([*args, "-filter_complex", ";".join(filters), "-map", "[out]", "-ac", "1", str(out_wav)])
    return out_wav


def run(plan: ScenePlan, clips: List[Path], scenes: List[str], workdir: Path, out_mp4: Path) -> Timing:
    workdir.mkdir(parents=True, exist_ok=True)
    timing = plan_timing([audio.duration(c) for c in clips], scenes)
    silent = video.render(plan, timing.durations, workdir / "silent.mp4", workdir / "parts")
    voice = mix_voice(clips, timing, workdir / "voice_mix.wav")
    audio.run(["-i", str(silent), "-i", str(voice), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", f"{sum(timing.durations):.3f}", "-movflags", "+faststart",
               str(out_mp4)])
    return timing
