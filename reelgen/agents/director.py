"""Director agent: designs the on-screen infographic for each scene of the script.

The director fills a fixed set of scene templates (see reelgen/render/scenes.py) so every
video keeps the channel's visual style. It chooses the words on screen and the icons."""
from __future__ import annotations

from .. import config, llm
from ..models import Research, ScenePlan, Script

SYSTEM = """You are the Director of "AI in 30 Seconds", 9:16 infographic explainer videos.
Given the narration script, design what appears on screen for each of the 5 scenes using the
provided templates. Respect every character limit in the schema: text that is too long will
be shrunk and look bad. On-screen text should reinforce the narration with fewer words, never
contradict it.

Templates:
- hook: a two-part question (line1 white, line2 amber) and one icon.
- problem: a headline, 2-3 pain cards each with an icon, and 2-3 short red tags in caps.
- define: an intro word, the big term, the acronym expansion if any, and an analogy pill.
- steps: a label in caps, 3-5 numbered step cards (title, subtitle, icon) matching the order
  of the narration, and a result pill.
- payoff: "<term> =" style first line, a teal highlight phrase, optional third line, and a
  before/after comparison (bad = without it, good = with it).

Icons available: chat, robot, database, docs, check, cross, numbers, search, gear, bulb, lock,
chart, cloud, code, user, globe, clock, warning, brain, layers, link, spark.
Pick the icon that best matches each idea. No emoji."""


def run(script: Script, research: Research) -> ScenePlan:
    prompt = (
        "Script (JSON):\n" + script.model_dump_json(indent=1, include={"title", "lines"})
        + "\n\nResearch summary: " + research.one_line_definition
        + "\nAcronym expansion: " + (research.acronym_expansion or "none")
    )
    return llm.structured(SYSTEM, prompt, ScenePlan, effort=config.EFFORT_WRITING)
