"""Render a ScenePlan to a silent 1080x1920 MP4. Scenes render in parallel processes."""
from __future__ import annotations

import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from .. import config
from ..models import ScenePlan
from .canvas import Ctx, chrome, clamp
from .scenes import TEMPLATES

ORDER = ["hook", "problem", "define", "steps", "payoff"]


def timeline(durations: List[float]) -> List[Tuple[str, float, float]]:
    """[(scene, start, duration)]"""
    out, acc = [], 0.0
    for name, d in zip(ORDER, durations):
        out.append((name, acc, d))
        acc += d
    return out


def frame(plan: ScenePlan, durations: List[float], t: float) -> Image.Image:
    total = sum(durations)
    for name, start, D in timeline(durations):
        if t < start + D or name == ORDER[-1]:
            lt = t - start
            c = Ctx()
            chrome(c, t, total)
            TEMPLATES[name](c, lt, D, getattr(plan, name))
            img = c.done()
            fade = clamp((D - lt) / 0.2) if name == "hook" else min(clamp(lt / 0.2), clamp((D - lt) / 0.2))
            if name == ORDER[-1]:
                fade = clamp(lt / 0.2)
            if fade < 1:
                bg = Ctx()
                chrome(bg, t, total)
                img = Image.blend(bg.done(), img, fade)
            return img
    raise ValueError("t outside timeline")


def _render_scene(args) -> str:
    plan_json, durations, idx, outdir = args
    plan = ScenePlan.model_validate_json(plan_json)
    name, start, D = timeline(durations)[idx]
    fps = config.FPS
    nf = int(round(D * fps))
    path = os.path.join(outdir, f"{idx:02d}_{name}.mp4")
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{config.W}x{config.H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "18",
         "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(fps), path],
        stdin=subprocess.PIPE)
    for f in range(nf):
        proc.stdin.write(frame(plan, durations, start + f / fps).convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for scene {name}")
    return path


def render(plan: ScenePlan, durations: List[float], out_path: Path, workdir: Path) -> Path:
    """Durations are rounded to whole frames so the total is exact."""
    fps = config.FPS
    durations = [round(d * fps) / fps for d in durations]
    workdir.mkdir(parents=True, exist_ok=True)
    jobs = [(plan.model_dump_json(), durations, i, str(workdir)) for i in range(len(ORDER))]
    workers = max(1, min(len(ORDER), os.cpu_count() or 1))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        parts = list(ex.map(_render_scene, jobs))
    listfile = workdir / "parts.txt"
    listfile.write_text("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
                    "-c", "copy", str(out_path)], check=True)
    return out_path


def still(plan: ScenePlan, durations: List[float], t: float, path: Path) -> Path:
    frame(plan, durations, t).save(path)
    return path
