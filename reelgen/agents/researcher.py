"""Researcher agent: searches the web and returns structured, sourced notes."""
from __future__ import annotations

from .. import config, llm
from ..models import Research

SYSTEM = """You are the Researcher for a channel of 30-second vertical explainer videos
for beginners. Research the topic on the web and gather what a scriptwriter needs:
a plain-English definition, the everyday problem it solves, how it works in 3-5 steps,
2-3 analogies, common misconceptions, and a few verifiable facts.

Rules:
- Prefer primary and reputable sources (official docs, original papers, well-known
  engineering blogs, reputable news). Avoid content farms.
- Every fact must carry the URL it came from. Do not state anything you could not verify.
- Keep it beginner-friendly but technically accurate.
- Finish with organised notes in plain text, with a "Sources" list of URLs."""

STRUCTURE_SYSTEM = """Convert research notes into the requested JSON structure.
Use only information present in the notes. Keep every fact paired with its source URL."""


def run(topic: str, notes_from_user: str = "") -> tuple[Research, str]:
    prompt = f"Topic: {topic}"
    if notes_from_user:
        prompt += f"\nNotes from the channel owner (follow them): {notes_from_user}"
    raw = llm.research_with_web(SYSTEM, prompt, effort=config.EFFORT_RESEARCH)
    research = llm.structured(STRUCTURE_SYSTEM, f"Topic: {topic}\n\nResearch notes:\n{raw}",
                              Research, effort=config.EFFORT_STRUCTURE)
    return research, raw
