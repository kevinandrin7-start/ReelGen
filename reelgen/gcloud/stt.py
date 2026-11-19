"""Google Cloud Speech-to-Text v1 (REST, API key) with word timestamps."""
from __future__ import annotations

import base64
import subprocess
import time
from pathlib import Path
from typing import List, Tuple

import requests

from .. import config

URL = "https://speech.googleapis.com/v1/speech:recognize"


def _to_flac_16k(src: Path, dst: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "16000",
                    "-c:a", "flac", str(dst)], check=True)
    return dst


def transcribe(audio: Path, phrase_hints: List[str]) -> Tuple[str, List[Tuple[str, float, float]]]:
    """Returns (transcript, [(word, start, end)]). Audio must be under 60 s (sync API limit)."""
    if not config.GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    flac = _to_flac_16k(audio, audio.with_suffix(".stt.flac"))
    body = {
        "config": {
            "encoding": "FLAC",
            "sampleRateHertz": 16000,
            "languageCode": config.TTS_LANGUAGE,
            "enableWordTimeOffsets": True,
            "enableAutomaticPunctuation": False,
            "model": "latest_long",
            # Hints help with technical terms, but we keep them modest so the
            # check still catches genuinely mispronounced words.
            "speechContexts": [{"phrases": phrase_hints[:100], "boost": 5}],
        },
        "audio": {"content": base64.b64encode(flac.read_bytes()).decode()},
    }
    for attempt in range(4):
        r = requests.post(URL, json=body, headers={"X-Goog-Api-Key": config.GOOGLE_API_KEY}, timeout=120)
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt * 2)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Speech-to-Text failed {r.status_code}: {r.text[:300]}")
        words, parts = [], []
        for res in r.json().get("results", []):
            alt = res["alternatives"][0]
            parts.append(alt.get("transcript", ""))
            for w in alt.get("words", []):
                words.append((w["word"], _secs(w["startTime"]), _secs(w["endTime"])))
        return " ".join(p.strip() for p in parts), words
    raise RuntimeError("Speech-to-Text kept failing after retries")


def _secs(s: str) -> float:
    return float(s.rstrip("s"))
