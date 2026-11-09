"""Deterministic batching of ``fetch(ref, range?)`` calls by body tokens."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Sequence, Union

from .quantise import token_len


@dataclass
class FetchRequest:
    ref: str
    body: Union[str, bytes] = ""
    tokens: Optional[int] = None
    range: Optional[str] = None

    def body_tokens(self, tokenizer: Any = None) -> int:
        if self.tokens is not None:
            return int(self.tokens)
        if isinstance(self.body, (str, bytes, bytearray)):
            text = self.body.decode("utf-8", errors="replace") if isinstance(self.body, (bytes, bytearray)) else self.body
            return token_len(text, tokenizer)
        return 0

    def sort_key(self) -> str:
        return str(self.ref) + (self.range or "")


def _normalise(item: Any) -> FetchRequest:
    if isinstance(item, FetchRequest):
        return item
    if isinstance(item, dict):
        return FetchRequest(
            ref=str(item.get("ref", item.get("id", ""))),
            body=item.get("body", item.get("text", "")),
            tokens=item.get("tokens"),
            range=item.get("range"),
        )
    if isinstance(item, (tuple, list)):
        ref = item[0] if len(item) > 0 else ""
        body = item[1] if len(item) > 1 else ""
        tokens = item[2] if len(item) > 2 else None
        rng = item[3] if len(item) > 3 else None
        return FetchRequest(ref=str(ref), body=body, tokens=tokens, range=rng)
    # object with attributes
    ref = getattr(item, "ref", getattr(item, "id", str(item)))
    body = getattr(item, "body", getattr(item, "text", ""))
    tokens = getattr(item, "tokens", None)
    rng = getattr(item, "range", None)
    return FetchRequest(ref=str(ref), body=body, tokens=tokens, range=rng)


def batch_fetches(
    fetches: Iterable[Any],
    budget_tokens: int,
    tokenizer: Any = None,
) -> List[List[FetchRequest]]:
    """Return batches of fetch requests whose total body tokens <= budget.

    Ordering is stable and independent of input/dict iteration order (sorted by
    ref). A request larger than the budget is never silently dropped: it becomes
    its own (oversized) batch.
    """
    if budget_tokens <= 0:
        raise ValueError("budget_tokens must be positive")
    ordered = sorted((_normalise(f) for f in fetches), key=lambda f: f.sort_key())
    batches: List[List[FetchRequest]] = []
    current: List[FetchRequest] = []
    current_tokens = 0
    for req in ordered:
        rt = req.body_tokens(tokenizer)
        if current and current_tokens + rt > budget_tokens:
            batches.append(current)
            current = []
            current_tokens = 0
        current.append(req)
        current_tokens += rt
        # oversized single request: close batch so it is not dropped
        if current_tokens > budget_tokens:
            batches.append(current)
            current = []
            current_tokens = 0
    if current:
        batches.append(current)
    return batches


__all__ = ["FetchRequest", "batch_fetches"]
