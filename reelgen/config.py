"""Central settings. Every value can be overridden with an environment variable."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# --- Paths -----------------------------------------------------------------
BACKLOG_FILE = ROOT / "backlog" / "topics.json"
RUNS_DIR = ROOT / "runs"
WORK_DIR = Path(_env("REELGEN_WORK_DIR", str(ROOT / ".work")))
FONTS_DIR = ROOT / "assets" / "fonts"
PRONUNCIATIONS_FILE = ROOT / "config" / "pronunciations.json"

# --- Channel / brand -------------------------------------------------------
CHANNEL_LABEL = _env("REELGEN_CHANNEL_LABEL", "AI IN 30 SECONDS")
CTA_TEXT = _env("REELGEN_CTA", "Follow for more AI in 30s")

# --- Claude ----------------------------------------------------------------
# One setting switches every agent. Cheaper option: claude-sonnet-5-5.
CLAUDE_MODEL = _env("REELGEN_MODEL", "claude-opus-5-5")
# effort per agent: low | medium | high
EFFORT_RESEARCH = _env("REELGEN_EFFORT_RESEARCH", "medium")
EFFORT_WRITING = _env("REELGEN_EFFORT_WRITING", "medium")
EFFORT_STRUCTURE = _env("REELGEN_EFFORT_STRUCTURE", "low")
MAX_WEB_SEARCHES = int(_env("REELGEN_MAX_WEB_SEARCHES", "6"))
MAX_WEB_FETCHES = int(_env("REELGEN_MAX_WEB_FETCHES", "4"))

# --- Production schedule ---------------------------------------------------
TOPICS_PER_RUN = int(_env("REELGEN_TOPICS_PER_RUN", "1"))  # the workflow runs once a day
MAX_ATTEMPTS = int(_env("REELGEN_MAX_ATTEMPTS", "2"))

# --- Video -----------------------------------------------------------------
W, H, FPS = 1080, 1920, 30
TOTAL_SECONDS = float(_env("REELGEN_TOTAL_SECONDS", "30"))
SUPERSAMPLE = int(_env("REELGEN_SUPERSAMPLE", "2"))

# --- Voice (Google Cloud Text-to-Speech) -----------------------------------
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
TTS_VOICE = _env("REELGEN_TTS_VOICE", "en-US-Chirp3-HD-Charon")
TTS_LANGUAGE = _env("REELGEN_TTS_LANGUAGE", "en-US")
TTS_SAMPLE_RATE = 24000
VOICE_SPEED = float(_env("REELGEN_VOICE_SPEED", "1.06"))  # atempo; editor may raise to 1.15 to fit
VOICE_MAX_SPEED = 1.15
VOICE_LEAD_IN = 0.2  # seconds of silence before each scene's line

# --- Tester thresholds -----------------------------------------------------
MAX_WER = float(_env("REELGEN_MAX_WER", "0.12"))          # whole-video word error rate
MAX_SCENE_WER = float(_env("REELGEN_MAX_SCENE_WER", "0.25"))
WPM_RANGE = (125.0, 205.0)
MAX_GAP_SECONDS = 1.4  # longest silence allowed inside a scene's speech
LOUDNESS_TARGET = -14.0
LOUDNESS_TOLERANCE = 1.5
MAX_VOICE_RETRIES = 2

# --- Google Drive ----------------------------------------------------------
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
DRIVE_FOLDER_NAME = _env("REELGEN_DRIVE_FOLDER", "ReelGen")
DRIVE_MAX_VIDEOS = int(_env("REELGEN_DRIVE_MAX_VIDEOS", "5"))
DRIVE_KEEP_DAYS_AFTER_POST = float(_env("REELGEN_DRIVE_KEEP_DAYS", "3"))
