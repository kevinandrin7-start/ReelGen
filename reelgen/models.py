"""Data passed between agents. Every hand-off is one of these pydantic models,
saved as JSON in runs/<slug>/ so a run can be inspected or resumed."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- research --

class Fact(BaseModel):
    fact: str
    source_url: str


class Research(BaseModel):
    topic: str
    one_line_definition: str = Field(description="Plain-English definition a beginner understands")
    why_it_matters: str
    pain_point: str = Field(description="The concrete problem this concept solves, as a viewer would feel it")
    how_it_works: List[str] = Field(description="3-5 ordered steps or parts, each one short sentence")
    key_facts: List[Fact]
    analogies: List[str] = Field(description="2-3 everyday analogies")
    misconceptions: List[str]
    acronym_expansion: Optional[str] = Field(default=None, description="If the topic is an acronym, what it stands for")
    sources: List[str]

# ------------------------------------------------------------------ script --

SceneKind = Literal["hook", "problem", "define", "steps", "payoff"]


class ScriptLine(BaseModel):
    scene: SceneKind
    narration: str = Field(description="Exactly what the voice says, as normal written English")
    spoken: str = Field(description="Same line rewritten for text-to-speech: acronyms spelled the way they "
                                    "should be said (e.g. 'L L M', 'rag'), numbers as words")


class Script(BaseModel):
    title: str
    lines: List[ScriptLine] = Field(description="Exactly 5 lines in order: hook, problem, define, steps, payoff")
    instagram_caption: str = Field(description="2-4 short sentences plus a question to drive comments, no hashtags")
    hashtags: List[str] = Field(description="5-7 hashtags, each starting with #")
    youtube_title: str = Field(description="Under 60 characters, ends with #Shorts")
    youtube_description: str

    def word_count(self) -> int:
        return sum(len(l.narration.split()) for l in self.lines)

# ------------------------------------------------------------- scene plan --

Icon = Literal["chat", "robot", "database", "docs", "check", "cross", "numbers", "search", "gear",
               "bulb", "lock", "chart", "cloud", "code", "user", "globe", "clock", "warning", "brain",
               "layers", "link", "spark"]


class HookScene(BaseModel):
    line1: str = Field(description="First half of the hook question, <= 16 chars")
    line2: str = Field(description="Second half, highlighted in amber, <= 18 chars")
    icon: Icon = "spark"
    subline: str = Field(default="Here's the answer in 30 sec", description="<= 30 chars")


class Pain(BaseModel):
    text: str = Field(description="<= 34 chars")
    icon: Icon = "warning"


class ProblemScene(BaseModel):
    headline: str = Field(description="<= 26 chars")
    pains: List[Pain] = Field(description="2-3 concrete pain cards")
    tags: List[str] = Field(description="2-3 red tags, each <= 10 chars, ALL CAPS")


class DefineScene(BaseModel):
    intro: str = Field(default="The fix:", description="<= 14 chars, e.g. 'The fix:' or 'Meet'")
    term: str = Field(description="The big term, <= 10 chars ideally")
    expansion: Optional[str] = Field(default=None, description="Acronym expansion, e.g. 'Retrieval-Augmented Generation'")
    analogy: str = Field(description="One-line analogy, <= 30 chars")


class Step(BaseModel):
    title: str = Field(description="<= 22 chars")
    sub: str = Field(description="<= 32 chars")
    icon: Icon


class StepsScene(BaseModel):
    label: str = Field(description="e.g. 'HOW RAG WORKS', <= 22 chars")
    steps: List[Step] = Field(description="3-5 steps")
    result: str = Field(description="Result pill text, <= 34 chars")


class Compare(BaseModel):
    title: str = Field(description="<= 22 chars")
    sub: str = Field(description="<= 30 chars")


class PayoffScene(BaseModel):
    line1: str = Field(description="<= 14 chars, e.g. 'RAG ='")
    highlight: str = Field(description="<= 20 chars, teal")
    line3: str = Field(default="", description="<= 14 chars, may be empty")
    bad: Compare
    good: Compare


class ScenePlan(BaseModel):
    hook: HookScene
    problem: ProblemScene
    define: DefineScene
    steps: StepsScene
    payoff: PayoffScene

# ------------------------------------------------------------------ tester --

class Check(BaseModel):
    name: str
    passed: bool
    detail: str


class TestReport(BaseModel):
    passed: bool
    checks: List[Check]
    transcript: str = ""
    wer: Optional[float] = None
    scene_wer: List[float] = []
    misheard_words: List[str] = []
