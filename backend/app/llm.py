"""LLM provider wrapper.

Design rule: every coach feature has a deterministic fallback, so the app works with
no API key (mock mode). The LLM upgrades parsing accuracy and coaching voice.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from .config import get_settings

log = logging.getLogger(__name__)


class AnthropicLLM:
    def __init__(self, api_key: str | None) -> None:
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        s = get_settings()
        self.models = {"parse": s.parse_model, "coach": s.coach_model}

    def json(
        self,
        *,
        system: str,
        prompt: str,
        schema: dict[str, Any],
        images: list[tuple[bytes, str]] | None = None,
        role: str = "parse",
        max_tokens: int = 1500,
    ) -> dict[str, Any]:
        """Force a structured answer by making the model call a single tool."""
        content: list[dict[str, Any]] = []
        for data, media_type in images or []:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type,
                           "data": base64.b64encode(data).decode()},
            })
        content.append({"type": "text", "text": prompt})
        resp = self.client.messages.create(
            model=self.models[role],
            max_tokens=max_tokens,
            system=system,
            tools=[{"name": "respond", "description": "Return the answer.", "input_schema": schema}],
            tool_choice={"type": "tool", "name": "respond"},
            messages=[{"role": "user", "content": content}],
        )
        for block in resp.content:
            if block.type == "tool_use":
                return dict(block.input)
        raise RuntimeError("model did not return structured output")

    def text(
        self, *, system: str, messages: list[dict[str, str]], role: str = "coach", max_tokens: int = 700
    ) -> str:
        resp = self.client.messages.create(
            model=self.models[role], max_tokens=max_tokens, system=system, messages=messages
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()


_llm: AnthropicLLM | None = None
_resolved = False


def get_llm() -> AnthropicLLM | None:
    """Return the configured LLM, or None in mock mode."""
    global _llm, _resolved
    if _resolved:
        return _llm
    s = get_settings()
    provider = s.llm_provider
    if provider == "auto":
        import os

        provider = "anthropic" if (s.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")) else "mock"
    if provider == "anthropic":
        try:
            _llm = AnthropicLLM(s.anthropic_api_key)
        except Exception as e:  # pragma: no cover
            log.warning("Anthropic client unavailable (%s); falling back to mock mode", e)
            _llm = None
    _resolved = True
    return _llm


def set_llm_for_tests(llm: Any) -> None:
    global _llm, _resolved
    _llm, _resolved = llm, True
