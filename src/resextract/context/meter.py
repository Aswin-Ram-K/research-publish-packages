"""Cache metering rows.

The one subtlety: SGLang omits ``prompt_tokens_details`` entirely (JSON
``null``) on a cold request rather than reporting ``{"cached_tokens": 0}``.
:func:`normalise_cache` treats ``None``, missing and empty as zero so the
analysis never has to special-case the cold path.

Impossible values are clamped, counted and reported -- never silently passed
through.  ``cached_tokens`` above ``prompt_tokens`` cannot happen on a correct
server, so for batch robustness it is clamped to ``prompt_tokens``; the clamp
is counted in :func:`clamp_stats` (``clamped``) and its worst case reported as
``max_overrun``.  Negative ``cached_tokens`` clamp to 0 and a negative
``prompt_tokens`` clamps to 0; neither is an overrun.  Callers that record
``uncached = max(0, prompt - cached)`` are unaffected by the upper clamp,
because they already floored at 0.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Mapping, Sequence

_clamp_count = 0
_clamp_max_overrun = 0


def clamp_stats() -> dict[str, int]:
    """Counters for :func:`normalise_cache` clamps, since process start."""

    return {"clamped": _clamp_count, "max_overrun": _clamp_max_overrun}


def reset_clamp_stats() -> None:
    """Zero the clamp counters (tests and per-cell batch reporting)."""

    global _clamp_count, _clamp_max_overrun
    _clamp_count = 0
    _clamp_max_overrun = 0


@dataclass
class CacheRow:
    """One metered model turn.  Field names are part of the public contract."""

    cell: str
    arm: str
    policy: str
    case_id: str
    turn: int
    rep: int
    salt: str
    prompt_tokens: int
    cached_tokens: int
    uncached: int
    ttft_ms: float
    wall_ms: float
    completion_tokens: int
    status: int | None
    evicted: bool
    prefix_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CacheRow":
        known = {f.name for f in fields(cls)}
        missing = known - set(data)
        if missing:
            raise ValueError(f"CacheRow missing fields: {sorted(missing)}")
        return cls(
            cell=str(data["cell"]),
            arm=str(data["arm"]),
            policy=str(data["policy"]),
            case_id=str(data["case_id"]),
            turn=int(data["turn"]),
            rep=int(data["rep"]),
            salt=str(data["salt"]),
            prompt_tokens=int(data["prompt_tokens"]),
            cached_tokens=int(data["cached_tokens"]),
            uncached=int(data["uncached"]),
            ttft_ms=float(data["ttft_ms"]),
            wall_ms=float(data["wall_ms"]),
            completion_tokens=int(data["completion_tokens"]),
            status=None if data["status"] is None else int(data["status"]),
            evicted=bool(data["evicted"]),
            prefix_sha256=str(data["prefix_sha256"]),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)


def normalise_cache(usage: Mapping[str, Any] | None) -> tuple[int, int]:
    """Return ``(prompt_tokens, cached_tokens)`` from a raw usage dict.

    ``None`` / missing / ``{}`` / ``{"prompt_tokens_details": None}`` all map
    to zero cached tokens.  A missing ``prompt_tokens`` is also zero.  The
    returned pair always satisfies ``0 <= cached_tokens <= prompt_tokens``:
    ``cached_tokens > prompt_tokens`` is clamped down to the prompt, counted
    in :func:`clamp_stats` and reported as ``max_overrun``, never dropped
    silently.
    """

    global _clamp_count, _clamp_max_overrun

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
        _clamp_count += 1
        _clamp_max_overrun = max(_clamp_max_overrun, cached - prompt)
        cached = prompt
    return (prompt, cached)


class CacheMeter:
    """In-memory row sink; ``to_jsonl`` is the only file I/O."""

    def __init__(self) -> None:
        self._rows: list[CacheRow] = []

    def record(self, row: CacheRow) -> None:
        if not isinstance(row, CacheRow):
            raise TypeError("record() takes a CacheRow")
        self._rows.append(row)

    def rows(self) -> list[CacheRow]:
        return list(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    def to_jsonl(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for row in self._rows:
                handle.write(row.to_json() + "\n")
        return target


def rows_from_jsonl(path: str | Path) -> list[CacheRow]:
    """Read back a jsonl file written by :meth:`CacheMeter.to_jsonl`."""

    rows: list[CacheRow] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(CacheRow.from_dict(json.loads(line)))
    return rows


def rows_to_json(rows: Sequence[CacheRow]) -> str:
    return json.dumps([row.to_dict() for row in rows], sort_keys=True, ensure_ascii=False)
