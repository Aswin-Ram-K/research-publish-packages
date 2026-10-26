"""Faithful copy of res/extract meter.normalise_cache (meter.py:96-124).

The batch's cold-isolation and hit-rate evidence depends on this coercion:
49 of U2's 97 usage records and 23 of U4's 438 carry
``"prompt_tokens_details": null``.  The copy exists so CX-V2 can break it and
restore it without editing ``src/`` or any unit's script (write contract).

Do not import this from the units -- it is a verifier artefact.
"""
from __future__ import annotations

from typing import Any, Mapping


def normalise_cache(usage: Mapping[str, Any] | None) -> tuple[int, int]:
    if not isinstance(usage, Mapping):
        return (0, 0)
    prompt = max(0, int(usage.get("prompt_tokens") or 0))
    cached = 0
    details = usage.get("prompt_tokens_details")
    if isinstance(details, Mapping):
        cached = int(details.get("cached_tokens") or 0)
    else:
        # Some OpenAI-compatible servers put cached_tokens at the top level.
        cached = int(usage.get("cached_tokens") or 0)
    cached = max(0, cached)
    if cached > prompt:
        cached = prompt
    return (prompt, cached)
