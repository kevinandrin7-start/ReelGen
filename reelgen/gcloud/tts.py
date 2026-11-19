"""Google Cloud Text-to-Speech (REST, API key)."""
from __future__ import annotations

import base64
import time
import wave
from pathlib import Path

import requests

from .. import config

URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


def synthesize(text: str, out_wav: Path) -> Path:
    if not config.GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    body = {
        "input": {"text": text},
        "voice": {"languageCode": config.TTS_LANGUAGE, "name": config.TTS_VOICE},
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": config.TTS_SAMPLE_RATE},
    }
    for attempt in range(4):
        r = requests.post(URL, json=body, headers={"X-Goog-Api-Key": config.GOOGLE_API_KEY}, timeout=60)
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt * 2)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"TTS failed {r.status_code}: {r.text[:300]}")
        audio = base64.b64decode(r.json()["audioContent"])
        out_wav.write_bytes(audio)  # LINEAR16 responses include a WAV header
        with wave.open(str(out_wav)) as w:  # sanity check
            w.getnframes()
        return out_wav
    raise RuntimeError("TTS kept failing after retries")
