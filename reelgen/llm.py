"""Thin wrapper around the Anthropic SDK used by every agent."""
from __future__ import annotations

import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from . import config

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

_client = None  # anthropic.Anthropic, created on first use
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def client():
    global _client
    if _client is None:
        import anthropic  # only needed in API mode
        _client = anthropic.Anthropic(max_retries=4, timeout=600)
    return _client


class LLMError(RuntimeError):
    pass


def _check(resp) -> None:
    if resp.stop_reason == "refusal":
        cat = getattr(resp.stop_details, "category", None) if resp.stop_details else None
        raise LLMError(f"model declined the request (category={cat})")
    if resp.stop_reason == "max_tokens":
        raise LLMError("response hit max_tokens")


def structured(system: str, prompt: str, schema: Type[T], effort: str = "medium",
               max_tokens: int = 16000) -> T:
    """One call that returns a validated pydantic object."""
    resp = client().beta.messages.parse(
        model=config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
        output_config={"effort": effort},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )
    _check(resp)
    log.info("llm %s usage in=%s out=%s", schema.__name__, resp.usage.input_tokens, resp.usage.output_tokens)
    if resp.parsed_output is None:
        raise LLMError(f"no parsed output for {schema.__name__}")
    return resp.parsed_output


def research_with_web(system: str, prompt: str, effort: str = "medium",
                      max_continuations: int = 5) -> str:
    """Let Claude search and read the web with Anthropic's server-side tools.
    Returns the final text (notes with source URLs)."""
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": config.MAX_WEB_SEARCHES},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": config.MAX_WEB_FETCHES},
    ]
    messages = [{"role": "user", "content": prompt}]
    so_far: list = []
    for _ in range(max_continuations + 1):
        resp = client().beta.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=16000,
            system=system,
            messages=messages,
            tools=tools,
            output_config={"effort": effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
        log.info("research usage in=%s out=%s stop=%s", resp.usage.input_tokens,
                 resp.usage.output_tokens, resp.stop_reason)
        if resp.stop_reason == "pause_turn":
            # Server-side tool loop paused; resend so it resumes where it left off.
            so_far = so_far + list(resp.content)
            messages = [messages[0], {"role": "assistant", "content": so_far}]
            continue
        _check(resp)
        blocks = so_far + list(resp.content)
        text = "\n".join(b.text for b in blocks if b.type == "text").strip()
        if not text:
            raise LLMError("researcher returned no text")
        return text
    raise LLMError("research did not finish after continuations")
