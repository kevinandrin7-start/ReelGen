"""Sound engineer agent: makes one narration clip per scene with Google Text-to-Speech,
applying the pronunciation dictionary, and trims the silence around each clip."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .. import audio, config
from ..models import Script

Synth = Callable[[str, Path], Path]


def load_pronunciations() -> Dict[str, str]:
    if config.PRONUNCIATIONS_FILE.exists():
        return json.loads(config.PRONUNCIATIONS_FILE.read_text())
    return {}


def apply_pronunciations(text: str, lex: Dict[str, str]) -> str:
    # longest keys first so "GPT-4" wins over "GPT"
    for word in sorted(lex, key=len, reverse=True):
        text = re.sub(rf"(?<![\w-]){re.escape(word)}(?![\w-])", lex[word], text)
    return text


def run(script: Script, workdir: Path, lex: Dict[str, str], synth: Optional[Synth] = None,
        only: Optional[List[int]] = None, previous: Optional[List[Path]] = None) -> List[Path]:
    """Returns trimmed WAV clips, one per script line. `only` re-records just those lines."""
    if synth is None:
        from ..gcloud import tts
        synth = tts.synthesize
    workdir.mkdir(parents=True, exist_ok=True)
    clips: List[Path] = list(previous) if previous else [Path()] * len(script.lines)
    for i, line in enumerate(script.lines):
        if only is not None and i not in only and previous:
            continue
        text = apply_pronunciations(line.spoken, lex)
        raw = workdir / f"{i:02d}_{line.scene}.raw.wav"
        synth(text, raw)
        clips[i] = audio.trim_silence(raw, workdir / f"{i:02d}_{line.scene}.wav")
    return clips
