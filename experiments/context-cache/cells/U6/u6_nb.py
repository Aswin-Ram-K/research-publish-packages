"""The two arms' prompt state over one 60-turn session.

BASELINE -- the incumbent's best case: a **static prefix** (one salted
invariant header, never rewritten), **append-only history** (a turn's text is
stored once, verbatim, and never mutated), **periodic compaction**, and
**volatile state only in the delta** (turn 1's body).  Compaction never
rewrites an emitted message either: every turn text is retained byte for byte
in the chain, and the *view* folds everything but the last ``KEEP_LAST`` turns
into a one-line digest each (id + first ``DIGEST_CHARS`` characters).  A fold is
a deterministic digest, never a model summary, so no caller prompt is rewritten
by a caller -- the same rule the SYSTEM arm obeys.

SYSTEM -- pointer context + fork compaction: ``FORK`` replaces the whole chain
by a fork node (a content-addressed ``[fork] ...`` marker plus the digests of
the folded head) and the kept tail, so the chain stays short and the prefix
breaks at every compaction.

Equal information: both arms carry the same turn texts, in the same order, under
the same header, with the same volatile block.  What differs is how much of the
history a *view* retains -- BASELINE folds to digests (``DIGEST_CHARS`` per
folded turn), SYSTEM keeps the last ``FORK_LINES`` folded turns' digests plus
the kept tail.  Both views are deterministic functions of the same chain.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from resextract.context import default_est_tokens, salted

DIGEST_CHARS = 240
KEEP_LAST = 2
FORK_LINES = 12
BASELINE = "BASELINE"
SYSTEM = "SYSTEM"
ARMS = (BASELINE, SYSTEM)

Node = tuple[str, str, str]  # (role, kind, text); kind in {delta, folded}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_line(index: int, role: str, text: str) -> str:
    """The compact stand-in for a folded turn."""

    head = " ".join(text.split())[:DIGEST_CHARS]
    return f"[folded {index + 1} {role} {_sha(text)[:12]}] {head}"


def _role(index: int) -> str:
    """Fallback role when the caller does not supply the corpus role.

    Roles come from the corpus, not from a node's position in this arm's view:
    position-relative roles let a shrinking view shift every turn's role, so
    the arms disagreed about the same turn and the baseline retained an extra
    turn per fold.
    """

    return "user" if index % 2 == 0 else "assistant"


def _view_marks(messages: list[dict[str, str]]) -> str:
    return "|".join(f"{m['role']}:{_sha(m['content'])[:16]}" for m in messages)


@dataclass
class ArmState:
    arm: str
    preamble: str
    salt: str
    nodes: list[Node]
    events: list[dict[str, Any]]

    @classmethod
    def new(cls, arm: str, *, preamble: str, salt: str) -> "ArmState":
        return cls(arm=arm, preamble=preamble, salt=salt, nodes=[], events=[])

    @property
    def folded_count(self) -> int:
        return sum(1 for n in self.nodes if n[1] == "folded")

    def append(self, index: int, body: str, role: str | None = None) -> None:
        self.nodes.append((role or _role(index), "delta", body))

    def marks(self) -> str:
        return _view_marks(self.view())

    def fold_n(self) -> int:
        """Turns retained verbatim before the fold: KEEP_LAST + 1 (this turn)."""

        return KEEP_LAST + 1

    def other_marks(self) -> str:
        """Marks of the other arm's view, for the per-turn distinctness assertion."""

        return _view_marks(self.view())

    def view(self) -> list[dict[str, str]]:
        head = salted(self.salt, self.preamble)
        deltas = [(i, n) for i, n in enumerate(self.nodes) if n[1] == "delta"]
        fold = deltas[: max(0, len(deltas) - self.fold_n())]
        live = deltas[max(0, len(deltas) - self.fold_n()):]
        bodies: list[dict[str, str]] = []
        if fold:
            if self.arm == BASELINE:
                lines = [
                    digest_line(i, n[0], n[2])
                    for i, n in enumerate(self.nodes)
                    if n[1] == "folded"
                ] + [digest_line(i, n[0], n[2]) for i, n in fold]
                bodies.append({"role": "user", "content": "[compacted history]\n" + "\n".join(lines)})
            else:
                marker = (
                    f"[fork] replaces head through {fold[-1][1]}; "
                    f"forked_from {_sha(''.join(_sha(n[2]) for _, n in fold))[:16]}"
                )
                lines = [digest_line(i, n[0], n[2]) for i, n in fold[-FORK_LINES:]]
                bodies.append({"role": "user", "content": marker + ("\n\n" + "\n".join(lines) if lines else "")})
        for i, (role, _kind, text) in live:
            bodies.append({"role": role, "content": text})
        return [{"role": "system", "content": head}, *bodies]

    def compact(self) -> dict[str, Any] | None:
        deltas = [n for n in self.nodes if n[1] == "delta"]
        cut = len(deltas) - self.fold_n()
        if cut <= 0:
            return None
        if self.arm == BASELINE:
            kept: list[Node] = []
            seen = 0
            for role, kind, text in self.nodes:
                if kind == "delta":
                    seen += 1
                    kept.append((role, "folded" if seen <= cut else "delta", text))
                else:
                    kept.append((role, kind, text))
            self.nodes = kept
            policy = "append_only"
        else:
            self.nodes = deltas[cut:]
            policy = "fork"
        self.events.append({"policy": policy, "folded": cut, "kept": len(deltas) - cut,
                            "at_turn": len(deltas)})
        return self.events[-1]

    def est_tokens(self) -> int:
        return sum(default_est_tokens(n[2]) for n in self.nodes)
