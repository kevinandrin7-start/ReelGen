"""Scripter agent: turns research into a 5-line, ~30-second narration plus captions."""
from __future__ import annotations

import json
from typing import Optional

from .. import config, llm
from ..models import Research, Script

SYSTEM = """You are the Scripter for "AI in 30 Seconds", vertical explainer videos for beginners.
Write a voiceover of 65-80 words total that takes about 28 seconds to say, as exactly 5 lines
in this order:
1. hook (~3s): a question about a pain point the viewer feels. 5-9 words.
2. problem (~5s): a concrete example of what goes wrong. 12-16 words.
3. define (~4s): name the concept (and what the acronym stands for, if any). 6-10 words.
4. steps (~13s): how it works, 3-5 short steps in order. 30-38 words.
5. payoff (~4s): a one-line analogy, then "Follow for more!". 8-12 words.

Style: short spoken sentences, friendly, confident, no jargon without a quick explanation,
technically accurate. Never invent facts that are not in the research.

For every line also give `spoken`: the same words prepared for text-to-speech. Spell out
acronyms the way people say them (e.g. "L L M", "A P I", but "rag" for RAG, "jason" for JSON),
write numbers as words, and avoid symbols. `spoken` must say the same words as `narration`
apart from those respellings.

Also write the Instagram caption (no hashtags in it), 5-7 hashtags, a YouTube Shorts title
under 60 characters ending in #Shorts, and a 2-3 sentence YouTube description."""


def run(research: Research, pronunciations: dict[str, str], feedback: Optional[str] = None) -> Script:
    prompt = (
        "Research (JSON):\n" + research.model_dump_json(indent=1)
        + "\n\nKnown pronunciations (word -> how to say it): " + json.dumps(pronunciations)
    )
    if feedback:
        prompt += "\n\nYour previous draft had problems. Fix them:\n" + feedback
    script = llm.structured(SYSTEM, prompt, Script, effort=config.EFFORT_WRITING)
    _validate(script)
    return script


def _validate(script: Script) -> None:
    kinds = [l.scene for l in script.lines]
    if kinds != ["hook", "problem", "define", "steps", "payoff"]:
        raise ValueError(f"script lines must be hook, problem, define, steps, payoff; got {kinds}")
    if len(script.youtube_title) > 60:
        script.youtube_title = script.youtube_title[:52].rstrip() + " #Shorts"
    if not script.youtube_title.endswith("#Shorts"):
        script.youtube_title = (script.youtube_title[:51].rstrip() + " #Shorts")
    script.hashtags = [h if h.startswith("#") else "#" + h for h in script.hashtags][:7]


def full_caption(script: Script) -> str:
    return script.instagram_caption.strip() + "\n\n" + " ".join(script.hashtags)
