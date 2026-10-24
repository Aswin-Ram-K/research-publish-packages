#!/usr/bin/env python3
"""U4b corpus — deterministic agent preamble + per-branch deltas.

The unit needs one *shared prefix* ``P`` (≈4,000 tokens) that models a
realistic agent preamble plus accumulated state, and K short deltas that make
the branches genuinely diverge.

Three builders, all byte-deterministic:

``preamble(chars)``
    The shared prefix body.  Same bytes for every branch of every arm that
    wants to share it.

``with_marker(body, branch_id, frac)``
    Arm B's prefix: the *same* text with one early line replaced by a
    branch-specific state line of **exactly the same length** (padded with
    ``.``).  Placing branch state early is the faithful model of an
    edit-based history: the branch-specific bytes rewrite the prefix, so a
    radix match cannot reach past that point.  Equal length is deliberate --
    it denies the incumbent the excuse "your branches were different sizes".

``delta(branch_id, chars)``
    Arm A's tail: a fully branch-specific instruction block.

``shared_tail(chars)`` + ``branch_suffix(branch_id)``
    Arm C's tail: a *common* instruction block with the branch-specific
    marker only at the very end.  This is the honest incumbent's best case.

No I/O, no network, no randomness without a seed.
"""

from __future__ import annotations

import hashlib
import random

SEED = 20261020

_ADJS = (
    "dense", "narrow", "staged", "verified", "bounded", "linear", "cached",
    "pinned", "divergent", "replayed", "salted", "amortised", "cold", "warm",
    "partial", "absolute", "monotone", "residual", "aligned", "queued",
    "serialised", "idempotent", "tolerant", "durable", "compact", "explicit",
)
_NOUNS = (
    "checkpoint", "transcript", "prefill", "prefix", "digest", "artifact",
    "ledger", "window", "segment", "residual", "branch", "pointer", "node",
    "budget", "token", "page", "radix", "session", "handoff", "verdict",
    "probe", "meter", "ratio", "baseline", "ceiling", "floor", "cap",
)
_VERBS = (
    "retains", "replays", "measures", "pins", "discards", "amortises",
    "extends", "splits", "merges", "records", "clamps", "normalises",
    "serialises", "validates", "renders", "reuses", "evicts", "admits",
)


def _sentence(rng: random.Random, words: int) -> str:
    parts = []
    for _ in range(words):
        parts.append(
            f"{rng.choice(_ADJS)} {rng.choice(_NOUNS)} {rng.choice(_VERBS)}"
        )
    return " ".join(parts) + "."


def _line(rng: random.Random, index: int) -> str:
    """One preamble line: ~190-230 characters, so a marker fits inside it."""

    head = f"{index:04d} | step {index * 7:05d} "
    body = _sentence(rng, 7) + " " + _sentence(rng, 6)
    tail = f" token={rng.randrange(1 << 24):06x}"
    return head + body + tail


def preamble(chars: int, seed: int = SEED) -> str:
    """Deterministic shared body of *at least* ``chars`` characters.

    Built line by line until the budget is met, then trimmed at the last
    newline so the caller always sees whole lines.
    """

    rng = random.Random(seed)
    lines: list[str] = []
    total = 0
    index = 0
    while total < chars:
        line = _line(rng, index)
        lines.append(line)
        total += len(line) + 1
        index += 1
    text = "\n".join(lines)
    if len(text) > chars:
        cut = text.rfind("\n", 0, chars)
        if cut > 0:
            text = text[:cut]
    return text


def revision_of(branch_id: str) -> str:
    """A short stable hex tag for a branch, so markers are not just the id."""

    return hashlib.sha256(f"U4b:rev:v1:{branch_id}".encode("utf-8")).hexdigest()[:10]


def with_marker(body: str, branch_id: str, frac: float = 0.08) -> str:
    """Replace one early line with a branch-specific line of equal length.

    ``frac`` is the position in the body.  0.08 is "early in the accumulated
    state" -- about 320 of 4,000 tokens -- rather than the strawman of char 0:
    even a branch that *shares* the first 8% must still pay for the other 92%,
    and the measurement shows how much that partial head is worth.
    """

    lines = body.split("\n")
    if len(lines) < 4:
        raise ValueError("body too short to mark")
    index = max(1, min(len(lines) - 1, int(len(lines) * frac)))
    old = lines[index]
    marker = (
        f"{index:04d} | BRANCH-STATE[{branch_id}] rev={revision_of(branch_id)} "
        f"diverges here; this line is specific to the {branch_id} history"
    )
    if len(marker) > len(old):
        raise ValueError(f"marker ({len(marker)}) longer than target line ({len(old)})")
    lines[index] = marker.ljust(len(old), ".")
    out = "\n".join(lines)
    assert len(out) == len(body), "marker must not change the body length"
    return out


def delta(branch_id: str, chars: int, seed: int = SEED) -> str:
    """Arm A tail: fully branch-specific, distinct bytes for every branch."""

    rng = random.Random(seed ^ int(hashlib.sha256(branch_id.encode()).hexdigest()[:8], 16))
    lines = [f"TASK[{branch_id}]: act only on this slice; shared state is read-only."]
    total = len(lines[0]) + 1
    while total < chars:
        line = _sentence(rng, 6) + " " + _sentence(rng, 5)
        line = f"- {branch_id}/{len(lines):02d} {line}"
        lines.append(line)
        total += len(line) + 1
    text = "\n".join(lines)
    return text if len(text) <= chars else text[:chars]


def shared_tail(chars: int, seed: int = SEED) -> str:
    """Arm C tail: byte-identical across branches (only the suffix differs)."""

    return delta("SHARED-TAIL", chars, seed=seed + 1)


def branch_suffix(branch_id: str) -> str:
    """Arm C's only branch-specific bytes, placed at the very end."""

    return f"\nBRANCH[{branch_id}] rev={revision_of(branch_id)}\n"
