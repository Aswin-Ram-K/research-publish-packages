#!/usr/bin/env python3
"""U4 deterministic compaction corpus.

``experiments/context-cache/corpora/compaction.json`` does not exist (only
``build_corpora.py`` is on disk, and running a sibling unit's builder would
write outside this unit's declared write paths), so U4 generates its own
session text here, under ``cells/U4/``, exactly as the unit card instructs.

Determinism contract
--------------------
* no wall clock, no ``os.urandom``, no ``random`` module, no dict-order
  dependence, no filesystem-order dependence;
* all randomness comes from :class:`Lcg`, a 64-bit LCG seeded from a constant,
  so the output is a pure function of ``SEED`` and is identical on every
  Python version;
* ``u4_sessions.json`` records the sha256 of its own payload so a re-run can be
  compared byte for byte.

Sizing contract
---------------
Each turn is ~``TURN_CHARS`` characters, i.e. ~``TURN_CHARS/4`` estimated
tokens under :func:`resextract.context.default_est_tokens` (the estimator the
budget check uses).  ``TURNS_PER_SESSION * TURN_CHARS / 4`` is therefore the
session's total estimated content, and the driver's budget is set well below
it so that several compaction events are forced.

``volatile`` is deliberately EMPTY on every turn.  ``render(NAIVE_APPEND)``
interpolates volatile values into the *newest* message only, so a non-empty
volatile map rewrites the previous turn's message on every subsequent turn and
puts a small prefix break at the end of every prompt.  U4 measures the
compaction break, so the only thing allowed to change the rendered prefix is
the compaction itself.  (Volatile-mutation cost is a different experiment.)

Usage::

    python3 u4_corpus.py                # writes u4_sessions.json next to this file
    python3 u4_corpus.py --check        # re-derive and verify the digest only
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SEED = 20261020
TURNS_PER_SESSION = 44
TURN_CHARS = 2800
SESSIONS = ("u4-s1", "u4-s2", "u4-s3")

#: Budget handed to ``needs_compaction`` (estimated tokens).
BUDGET_TOKENS = 8000
#: Nodes retained verbatim by ``compact(keep_last=...)``.
KEEP_LAST = 2

HERE = Path(__file__).resolve().parent
OUT = HERE / "u4_sessions.json"


class Lcg:
    """64-bit linear congruential generator; identical on every Python."""

    A = 6364136223846793005
    C = 1442695040888963407
    M = 1 << 64

    def __init__(self, seed: int) -> None:
        self.state = (seed ^ 0x9E3779B97F4A7C15) & (self.M - 1)

    def next_u64(self) -> int:
        self.state = (self.A * self.state + self.C) % self.M
        return self.state

    def below(self, n: int) -> int:
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.next_u64() % n

    def choice(self, seq: list[str]) -> str:
        return seq[self.below(len(seq))]


# A fixed vocabulary.  Ordered lists (not sets/dicts) so iteration is stable.
VERBS = [
    "inspect", "trace", "reconcile", "verify", "diff", "annotate", "measure",
    "index", "resolve", "audit", "replay", "prune", "recompute", "snapshot",
]
NOUNS = [
    "the resolver cache", "the pointer table", "the token estimator",
    "the docket manifest", "the radix node", "the compaction boundary",
    "the scheduler queue", "the ledger entry", "the provenance record",
    "the cache meter", "the budget guard", "the chain digest",
]
ADJS = [
    "stale", "truncated", "duplicated", "misaligned", "unshadowed", "warm",
    "cold", "ambiguous", "monotone", "bounded", "pinned", "idempotent",
]
FILES = [
    "src/resextract/context/render.py",
    "src/resextract/context/budget.py",
    "experiments/context-cache/runner.py",
    "experiments/context-cache/analyze.py",
    "orchestration/handoffs/U4.json",
    "cells/U4/u4_cell.py",
]
TESTS = [
    "tests/test_context_render.py",
    "tests/test_context_runner.py",
    "tests/test_context_meter.py",
    "tests/test_orchestration_handoffs.py",
]


def _hex16(rng: Lcg) -> str:
    return f"{rng.next_u64():016x}"


def _turn_text(rng: Lcg, session: str, turn: int) -> str:
    """One deterministic, self-dissimilar agent-session turn (~TURN_CHARS)."""

    head = (
        f"[{session} step {turn:03d}] "
        f"{rng.choice(VERBS).capitalize()} {rng.choice(NOUNS)}. "
        f"Observed state is {rng.choice(ADJS)}; the prior step left a "
        f"{rng.choice(ADJS)} boundary at offset {rng.below(9000)}."
    )
    body: list[str] = [head]
    target = TURN_CHARS
    while sum(len(line) + 1 for line in body) < target:
        kind = rng.below(4)
        if kind == 0:
            body.append(
                f"- {rng.choice(VERBS)} {rng.choice(NOUNS)}: "
                f"{rng.choice(ADJS)} at {_hex16(rng)}:"
                f"{_hex16(rng)}:{rng.below(4096)}"
            )
        elif kind == 1:
            body.append(
                f"- {rng.choice(FILES)} line {rng.below(600) + 1} reports "
                f"{rng.choice(ADJS)} {rng.choice(NOUNS)} "
                f"(count={rng.below(64) + 1}, drift={rng.below(17) - 8})"
            )
        elif kind == 2:
            body.append(
                f"- {rng.choice(TESTS)} :: "
                f"{rng.choice(VERBS)}_{rng.choice(VERBS)} "
                f"expected {rng.below(9999)} got {rng.below(9999)} "
                f"delta {rng.below(501) - 250}"
            )
        else:
            body.append(
                f"- note: {rng.choice(NOUNS)} stays {rng.choice(ADJS)} because "
                f"{rng.choice(NOUNS)} was {rng.choice(ADJS)} first "
                f"(digest {_hex16(rng)})"
            )
    text = "\n".join(body)
    return text[:target]


def build() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "corpus": "u4-compaction",
        "seed": SEED,
        "turns_per_session": TURNS_PER_SESSION,
        "turn_chars": TURN_CHARS,
        "budget_tokens": BUDGET_TOKENS,
        "keep_last": KEEP_LAST,
        "volatile": "empty on every turn (see module docstring)",
        "sessions": [],
    }
    for sidx, session in enumerate(SESSIONS):
        rng = Lcg(SEED + 101 * (sidx + 1))
        preamble = (
            "You are a careful cache-reuse analyst working inside a sandboxed "
            "repository. Every turn appends one investigation step; the "
            f"session identifier is {session}. Report nothing except progress."
        )
        turns = [
            {"turn": turn, "text": _turn_text(rng, session, turn), "volatile": {}}
            for turn in range(1, TURNS_PER_SESSION + 1)
        ]
        payload["sessions"].append(
            {
                "case_id": session,
                "preamble": preamble,
                "turns": turns,
                "est_tokens_total": sum((len(t["text"]) + 3) // 4 for t in turns),
                "chars_total": sum(len(t["text"]) for t in turns),
            }
        )
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=1)
    payload["payload_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only")
    args = parser.parse_args(argv)

    payload = build()
    if args.check:
        if not OUT.exists():
            print(f"MISSING {OUT}")
            return 1
        disk = json.loads(OUT.read_text(encoding="utf-8"))
        same = disk.get("payload_sha256") == payload["payload_sha256"]
        print(f"{'OK' if same else 'MISMATCH'} payload_sha256={payload['payload_sha256']}")
        return 0 if same else 1

    OUT.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "path": str(OUT),
                "payload_sha256": payload["payload_sha256"],
                "sessions": {
                    s["case_id"]: {
                        "turns": len(s["turns"]),
                        "est_tokens_total": s["est_tokens_total"],
                        "mean_turn_est_tokens": round(
                            s["est_tokens_total"] / len(s["turns"]), 1
                        ),
                        "min_turn_chars": min(len(t["text"]) for t in s["turns"]),
                        "max_turn_chars": max(len(t["text"]) for t in s["turns"]),
                    }
                    for s in payload["sessions"]
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
