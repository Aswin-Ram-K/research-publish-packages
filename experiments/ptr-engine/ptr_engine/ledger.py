"""Append-only JSONL ledger: one row per request.

The row shape is fixed by SPEC.md:

    {ledger_id, scope, refs_resolved, refs_refused, bytes_appended, block_size,
     append_remainder, prompt_tokens?, cached_tokens?, uncached_tokens?,
     token_source?, ref?}

``refs_resolved``/``refs_refused`` are counts, not booleans, so a host that
batches several fetches into one request can record them in one row.

THE TOKEN RULE, stated here because it is the one field group that can quietly
lie: the token fields are **optional** and are filled by a host that has them.
When a host does not have them, the row carries ``null`` and ``token_source:
null``. It never carries ``0``. A zero that means "unknown" has already been read
as "free" once in this project, and a measurement that cannot tell those two apart
is not a measurement. Supplying counts without saying where they came from is
refused with ``PTR_TOKEN_SOURCE_REQUIRED``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

from .errors import (
    PtrLawBoundInvalidError,
    PtrLawObservedInvalidError,
    PtrLawSeriesLengthError,
    PtrLawUnknownServerError,
    PtrLedgerBlockSizeError,
    PtrLedgerCountError,
    PtrLedgerIdError,
    PtrLedgerRefusalCodeError,
    PtrLedgerScopeError,
    PtrTokenSourceRequiredError,
)
from .annotate import ledger_id as make_ledger_id

# The codes a ledger failure can carry. Additive to the seven resolve controls:
# these five are reachable only by calling the ledger directly.
LEDGER_CODES: tuple[str, ...] = (
    "PTR_LEDGER_COUNT",
    "PTR_LEDGER_BLOCK_SIZE",
    "PTR_LEDGER_ID",
    "PTR_LEDGER_SCOPE",
    "PTR_LEDGER_REFUSAL_CODE",
)

# The codes a *billing-law* failure can carry. Deliberately a separate tuple:
# LEDGER_CODES is the row contract's five, and `tests/test_negative_controls.py`
# asserts that count. Additive, never a replacement.
LEDGER_LAW_CODES: tuple[str, ...] = (
    "PTR_LAW_UNKNOWN_SERVER",
    "PTR_LAW_BOUND_INVALID",
    "PTR_LAW_SERIES_LENGTH",
    "PTR_LAW_OBSERVED_INVALID",
)

TOKEN_FIELDS: tuple[str, ...] = ("prompt_tokens", "cached_tokens", "uncached_tokens")

ROW_KEYS: tuple[str, ...] = (
    "ledger_id",
    "scope",
    "refs_resolved",
    "refs_refused",
    "bytes_appended",
    "block_size",
    "append_remainder",
    "prompt_tokens",
    "cached_tokens",
    "uncached_tokens",
    "token_source",
    "ref",
    "ref_index",
)


def _count(name: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PtrLedgerCountError(
            f"{name} must be a non-negative int, got {value!r}", field=name, value=repr(value)
        )
    return value


class Ledger:
    """A JSONL ledger. One process, one file, append-only."""

    def __init__(self, path: Union[str, Path], *, block_size: int = 64) -> None:
        if not isinstance(block_size, int) or isinstance(block_size, bool) or block_size <= 0:
            raise PtrLedgerBlockSizeError(
                f"block_size must be a positive int, got {block_size!r}", block_size=repr(block_size)
            )
        self.path = Path(path).expanduser()
        self.block_size = block_size
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self._rows: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        self._rows = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    self._rows.append(json.loads(line))

    # -- counters ---------------------------------------------------------
    @property
    def rows(self) -> tuple[Mapping[str, Any], ...]:
        """Every row written so far, in append order."""
        return tuple(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    def next_seq(self) -> int:
        return len(self._rows)

    def resolved_count(self) -> int:
        """Total refs successfully resolved in this ledger (= the turn budget spend)."""
        return sum(int(row.get("refs_resolved") or 0) for row in self._rows)

    def refused_count(self) -> int:
        return sum(int(row.get("refs_refused") or 0) for row in self._rows)

    def was_resolved(self, *serialized_refs: str) -> bool:
        """True when some row records a *successful* resolve of any given text.

        Two texts can name the same entry -- the ref as the caller wrote it and the
        line as the index spells it -- so a row records both and both are matched.
        """
        wanted = {text for text in serialized_refs if isinstance(text, str) and text}
        if not wanted:
            return False
        for row in self._rows:
            if int(row.get("refs_resolved") or 0) <= 0:
                continue
            if row.get("ref") in wanted or row.get("ref_index") in wanted:
                return True
        return False

    def last(self) -> Optional[Mapping[str, Any]]:
        return self._rows[-1] if self._rows else None

    def iter_rows(self) -> Iterator[Mapping[str, Any]]:
        return iter(self._rows)

    # -- writing -----------------------------------------------------------
    def record(
        self,
        *,
        ledger_id: str,
        scope: str,
        refs_resolved: int = 0,
        refs_refused: int = 0,
        bytes_appended: int = 0,
        block_size: Optional[int] = None,
        token_source: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None,
        uncached_tokens: Optional[int] = None,
        ref: Optional[str] = None,
        ref_index: Optional[str] = None,
    ) -> dict[str, Any]:
        """Append one row and return it as written."""
        if not isinstance(ledger_id, str) or not ledger_id:
            raise PtrLedgerIdError("ledger_id must be a non-empty string", ledger_id=repr(ledger_id))
        if not isinstance(scope, str) or not scope:
            raise PtrLedgerScopeError("scope must be a non-empty string", scope=repr(scope))
        block = self.block_size if block_size is None else block_size
        if not isinstance(block, int) or isinstance(block, bool) or block <= 0:
            raise PtrLedgerBlockSizeError(
                f"block_size must be a positive int, got {block!r}", block_size=repr(block)
            )

        tokens = {
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached_tokens,
            "uncached_tokens": uncached_tokens,
        }
        supplied = {k: v for k, v in tokens.items() if v is not None}
        if supplied and not (isinstance(token_source, str) and token_source.strip()):
            raise PtrTokenSourceRequiredError(
                "token counts supplied without token_source; say where they came from",
                counts=sorted(supplied),
            )
        for name, value in tokens.items():
            if value is not None:
                _count(name, value)

        appended = _count("bytes_appended", bytes_appended)
        row: dict[str, Any] = {
            "ledger_id": ledger_id,
            "scope": scope,
            "refs_resolved": _count("refs_resolved", refs_resolved),
            "refs_refused": _count("refs_refused", refs_refused),
            "bytes_appended": appended,
            "block_size": block,
            "append_remainder": appended % block,
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached_tokens,
            "uncached_tokens": uncached_tokens,
            "token_source": token_source if supplied else None,
            "ref": ref,
            "ref_index": ref_index,
        }
        line = json.dumps(row, ensure_ascii=False, sort_keys=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
        self._rows.append(row)
        return row

    def record_resolution(
        self,
        *,
        scope: str,
        serialized_ref: str,
        bytes_appended: int,
        block_size: Optional[int] = None,
        entry_text: Optional[str] = None,
    ) -> dict[str, Any]:
        """One successful resolve: resolves 1, refuses 0, id derived from position."""
        block = self.block_size if block_size is None else block_size
        return self.record(
            ledger_id=make_ledger_id(scope, serialized_ref, self.next_seq()),
            scope=scope,
            refs_resolved=1,
            refs_refused=0,
            bytes_appended=bytes_appended,
            block_size=block,
            ref=serialized_ref,
            ref_index=entry_text,
        )

    def record_refusal(
        self,
        *,
        scope: str,
        serialized_ref: str,
        code: str,
        block_size: Optional[int] = None,
    ) -> dict[str, Any]:
        """One refused resolve: resolves 0, refuses 1, nothing appended."""
        if not isinstance(code, str) or not code.startswith("PTR_"):
            raise PtrLedgerRefusalCodeError(
                f"refusal needs a named error code, got {code!r}", code=repr(code)
            )
        return self.record(
            ledger_id=make_ledger_id(
                scope or "unknown-scope", serialized_ref or "@invalid", self.next_seq()
            ),
            scope=scope or "unknown-scope",
            refs_resolved=0,
            refs_refused=1,
            bytes_appended=0,
            block_size=block_size,
            ref=serialized_ref,
        )

    def read_rows(self) -> list[dict[str, Any]]:
        """Re-read the file from disk (a test asserts it matches memory)."""
        out: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out


def read_ledger(path: Union[str, Path]) -> Sequence[Mapping[str, Any]]:
    """Read a JSONL ledger without opening it for writing."""
    rows: list[Mapping[str, Any]] = []
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# The billing law, carried by the ledger
# ---------------------------------------------------------------------------
#
# One append onto an already-primed prefix of ``P1`` tokens, appending ``L``
# tokens, re-bills (``experiments/miss-law/LAW.md``, measured on 774 raw rows):
#
#     SGLang / occamy-1.0, B = 64:    uncached = (P1 mod B) + L
#     vLLM   / qwen3.5-9b, B = 1056:  uncached = (P1 mod B) + B + L
#
# and, at ``P1 mod B in {0, 1}`` on SGLang, an outcome that is not a tail cost at
# all: the server reports no cache and bills the whole prefix, ``uncached = P1 + L``
# (~8,013 billed tokens where the tail formula predicts 13). That is modelled
# below as its own stored outcome, ``avalanche`` -- not as a warning string and not
# as a footnote, because a host that budgets with the tail formula alone is wrong
# by four orders of magnitude at those two residues.
#
# ``L`` is the measured appended length and INCLUDES the request template's
# framing tokens (12 in the measured shape) -- never the raw payload count ``n``.
# ``law_L`` is that conversion and the only place the constant lives.

FRAMING_TOKENS: int = 12
"""Framing tokens the measured request shape adds to the payload on every append."""


def _bound(name: str, value: Any) -> int:
    """A non-negative int, or ``PTR_LAW_BOUND_INVALID``."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PtrLawBoundInvalidError(
            f"{name} must be a non-negative int, got {value!r}", field=name, value=repr(value)
        )
    return value


@dataclass(frozen=True)
class ServerProfile:
    """One measured server: its cache block grid and what its cache does at the edge.

    ``boundary_blocks`` is the number of *whole* blocks the server re-bills on top of
    the unaligned tail (0 on SGLang, 1 on vLLM). ``avalanche_measured`` says whether
    the residue-0/1 grid was actually swept on this server: on vLLM it was not (27
    residues present in the sweep, none of them 0 or 1), so an avalanche prediction
    there is an extrapolation and is reported as one.
    """

    name: str
    block_size: int
    boundary_blocks: int
    avalanche_residues: frozenset[int]
    avalanche_measured: bool
    note: str

    def boundary_tokens(self, P1: int) -> int:
        """The whole blocks re-billed *in addition* to the unaligned tail.

        ``boundary_blocks`` is capped by the complete blocks the prefix actually
        holds (``P1 // B``): a server that re-bills "one whole cached block" has no
        block to re-bill when ``P1 < B``, and the replay of the measured rows shows
        exactly that (vLLM, P1 = 453 < 1056, bills the whole prefix ``P1 + L``, not
        ``P1 + B + L``). With ``P1 >= B`` the cap is inert and the law is unchanged.
        """
        return min(self.boundary_blocks, P1 // self.block_size) * self.block_size

    def tail(self, P1: int, L: int) -> int:
        """The bill if the cache behaves: ``(P1 mod B) + boundary blocks + L``."""
        return (P1 % self.block_size) + self.boundary_tokens(P1) + L

    def predict(self, P1: int, L: int) -> tuple[int, bool]:
        """``(uncached, avalanche)`` -- the law for one append on this server."""
        if (P1 % self.block_size) in self.avalanche_residues:
            return P1 + L, True
        return self.tail(P1, L), False


SGLANG_PROFILE = ServerProfile(
    name="sglang",
    block_size=64,
    boundary_blocks=0,
    avalanche_residues=frozenset({0, 1}),
    avalanche_measured=True,
    note="occamy-1.0: 83 null-cache measure rows, all at residue 0/1 and nowhere else",
)

VLLM_PROFILE = ServerProfile(
    name="vllm",
    block_size=1056,
    boundary_blocks=1,
    avalanche_residues=frozenset({0, 1}),
    avalanche_measured=False,
    note=(
        "qwen3.5-9b: one whole boundary block re-bills once P1 >= B, none when "
        "P1 < B (measured at P1 = 453); residue 0/1 never sampled"
    ),
)

SERVER_PROFILES: Mapping[str, ServerProfile] = {
    SGLANG_PROFILE.name: SGLANG_PROFILE,
    VLLM_PROFILE.name: VLLM_PROFILE,
}


def server_profile(server: str) -> ServerProfile:
    """The measured profile for ``server``, or ``PTR_LAW_UNKNOWN_SERVER``.

    There is no default: an unmeasured server has no block grid, and inventing one
    would turn a measurement into a guess.
    """
    if not isinstance(server, str) or not server:
        raise PtrLawUnknownServerError(
            f"server must be a non-empty string, got {server!r}", server=repr(server)
        )
    try:
        return SERVER_PROFILES[server]
    except KeyError:
        raise PtrLawUnknownServerError(
            f"no measured cache profile for server {server!r}; known: {sorted(SERVER_PROFILES)}",
            server=server,
            known=sorted(SERVER_PROFILES),
        ) from None


def predict_uncached(server: str, P1: int, L: int) -> tuple[int, bool]:
    """The law for one append: ``(uncached, avalanche)``."""
    return server_profile(server).predict(_bound("P1", P1), _bound("L", L))


def law_L(payload_tokens: int) -> int:
    """``L`` from a payload count: the append carries the template's framing tokens too."""
    return _bound("payload_tokens", payload_tokens) + FRAMING_TOKENS


@dataclass(frozen=True)
class HitEntry:
    """One turn's billing, with what the law concluded stored, not recomputed.

    ``residue`` and ``avalanche`` are stored at record time on purpose: a later
    reader (or a changed profile) must not be able to silently redraw the outcome a
    turn was billed under. ``tail_uncached`` is what the same append would have cost
    had the cache behaved, so ``predicted_uncached - tail_uncached`` is exactly what
    the avalanche added.
    """

    turn: int
    server: str
    cell: str
    P1: int
    L: int
    B: int
    residue: int
    avalanche: bool
    predicted_uncached: int
    tail_uncached: int
    observed_uncached: Optional[int]
    avalanche_extrapolated: bool

    @property
    def delta(self) -> Optional[int]:
        """``observed - predicted``, or ``None`` when the observation is unknown."""
        if self.observed_uncached is None:
            return None
        return self.observed_uncached - self.predicted_uncached

    @property
    def avalanche_tokens(self) -> int:
        """What the avalanche added over the tail formula (0 for a normal miss)."""
        return self.predicted_uncached - self.tail_uncached

    def as_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "server": self.server,
            "cell": self.cell,
            "P1": self.P1,
            "L": self.L,
            "B": self.B,
            "residue": self.residue,
            "avalanche": self.avalanche,
            "predicted_uncached": self.predicted_uncached,
            "tail_uncached": self.tail_uncached,
            "observed_uncached": self.observed_uncached,
            "avalanche_extrapolated": self.avalanche_extrapolated,
        }


@dataclass(frozen=True)
class TurnCheck:
    """One reconciled turn: predicted, observed, and the delta between them."""

    turn: int
    server: str
    cell: str
    residue: int
    avalanche: bool
    predicted_uncached: int
    observed_uncached: Optional[int]
    delta: Optional[int]
    status: str  # "exact" | "mismatch" | "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "server": self.server,
            "cell": self.cell,
            "residue": self.residue,
            "avalanche": self.avalanche,
            "predicted_uncached": self.predicted_uncached,
            "observed_uncached": self.observed_uncached,
            "delta": self.delta,
            "status": self.status,
        }


@dataclass(frozen=True)
class Reconciliation:
    """The per-turn verdict of the law against a series of observations.

    Three outcomes, and they are not interchangeable:

    * ``exact``    -- ``delta == 0``; the law explained the bill.
    * ``mismatch`` -- ``delta != 0``; the law did *not* explain it, and the turn is
      named here with its server and cell. A silent mismatch is a bug in the host,
      not a rounding difference.
    * ``unknown``  -- no observation (``None``). It is not zero and it is not a
      match; it is counted separately and excluded from the explained fraction.
    """

    checks: tuple[TurnCheck, ...]

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def exact(self) -> tuple[TurnCheck, ...]:
        return tuple(c for c in self.checks if c.status == "exact")

    @property
    def mismatched(self) -> tuple[TurnCheck, ...]:
        return tuple(c for c in self.checks if c.status == "mismatch")

    @property
    def unknown(self) -> tuple[TurnCheck, ...]:
        return tuple(c for c in self.checks if c.status == "unknown")

    @property
    def explained_fraction(self) -> float:
        """Turns the law accounted for exactly, over *all* turns (unknowns included).

        A turn with no observation is not evidence, so it is not in the numerator;
        it stays in the denominator because "I never looked" must not read as 100 %.
        """
        if not self.checks:
            return 0.0
        return len(self.exact) / len(self.checks)

    def unexplained(self) -> tuple[str, ...]:
        """One line per turn the law could not account for -- mismatches, then unknowns."""
        lines: list[str] = []
        for check in self.mismatched:
            lines.append(
                f"turn {check.turn} ({check.server} cell={check.cell}): could not explain -- "
                f"observed {check.observed_uncached} vs predicted {check.predicted_uncached} "
                f"(delta {check.delta:+d})"
            )
        for check in self.unknown:
            lines.append(
                f"turn {check.turn} ({check.server} cell={check.cell}): could not explain -- "
                f"observed_uncached is unknown (None), which is not zero"
            )
        return tuple(lines)

    def as_dict(self) -> dict[str, Any]:
        return {
            "turns": self.total,
            "explained": len(self.exact),
            "mismatched": [c.as_dict() for c in self.mismatched],
            "unknown": [c.as_dict() for c in self.unknown],
            "explained_fraction": self.explained_fraction,
            "unexplained": list(self.unexplained()),
            "checks": [c.as_dict() for c in self.checks],
        }


@dataclass(frozen=True)
class LedgerSummary:
    """The totals a host budgets with. Every number here is derivable, none is a guess."""

    turns: int
    billed_tokens: int
    observed_billed_tokens: Optional[int]
    observed_unknown_turns: int
    avalanche_count: int
    avalanche_tokens: int
    avalanche_extra_tokens: int
    avalanche_extrapolated_turns: int
    exact: int
    mismatched: int
    unknown: int
    explained_fraction: float
    servers: tuple[str, ...]
    residues: tuple[tuple[int, int], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "turns": self.turns,
            "billed_tokens": self.billed_tokens,
            "observed_billed_tokens": self.observed_billed_tokens,
            "observed_unknown_turns": self.observed_unknown_turns,
            "avalanche_count": self.avalanche_count,
            "avalanche_tokens": self.avalanche_tokens,
            "avalanche_extra_tokens": self.avalanche_extra_tokens,
            "avalanche_extrapolated_turns": self.avalanche_extrapolated_turns,
            "exact": self.exact,
            "mismatched": self.mismatched,
            "unknown": self.unknown,
            "explained_fraction": self.explained_fraction,
            "servers": list(self.servers),
            "residues": [[residue, count] for residue, count in self.residues],
        }


class HitLedger:
    """One entry per turn, carrying the law's prediction and the server's observation.

    Pure and in-memory: no file, no clock, no randomness, nothing at import time. A
    host points it at the ``server``/``cell`` it is measuring; ``record`` refuses a
    server it has no measured profile for rather than guessing a block size.
    """

    def __init__(self, server: str = "sglang", *, cell: str = "") -> None:
        self._profile = server_profile(server)
        if not isinstance(cell, str):
            raise PtrLawObservedInvalidError(
                f"cell must be a string, got {cell!r}", cell=repr(cell)
            )
        self._cell = cell
        self._entries: list[HitEntry] = []

    # -- identity ----------------------------------------------------------
    @property
    def server(self) -> str:
        return self._profile.name

    @property
    def block_size(self) -> int:
        return self._profile.block_size

    @property
    def entries(self) -> tuple[HitEntry, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def _profile_for(self, server: Optional[str]) -> ServerProfile:
        if server is None:
            return self._profile
        return server_profile(server)

    # -- the law -----------------------------------------------------------
    def predict(self, P1: int, L: int, *, server: Optional[str] = None) -> tuple[int, bool]:
        """``(uncached, avalanche)`` for one append of ``L`` tokens onto ``P1``."""
        profile = self._profile_for(server)
        return profile.predict(_bound("P1", P1), _bound("L", L))

    # -- recording ---------------------------------------------------------
    def record(
        self,
        *,
        P1: int,
        L: Optional[int] = None,
        payload_tokens: Optional[int] = None,
        observed_uncached: Optional[int] = None,
        server: Optional[str] = None,
        cell: Optional[str] = None,
    ) -> HitEntry:
        """Record one turn and return it as stored.

        ``L`` is the measured appended length. ``payload_tokens`` is the raw payload
        count ``n``: it is converted with ``law_L`` (``n + FRAMING_TOKENS``) and is
        refused if both are supplied, because two different answers to "how much was
        appended" is exactly the confusion this law exists to remove.
        """
        profile = self._profile_for(server)
        prime = _bound("P1", P1)
        if L is not None and payload_tokens is not None:
            raise PtrLawBoundInvalidError(
                "supply L or payload_tokens, not both", fields=["L", "payload_tokens"]
            )
        if L is None and payload_tokens is None:
            raise PtrLawBoundInvalidError(
                "one of L or payload_tokens is required", fields=["L", "payload_tokens"]
            )
        appended = _bound("L", L) if L is not None else law_L(payload_tokens)  # type: ignore[arg-type]
        observed = None if observed_uncached is None else _bound(
            "observed_uncached", observed_uncached
        )
        label = self._cell if cell is None else cell
        if not isinstance(label, str):
            raise PtrLawObservedInvalidError(f"cell must be a string, got {label!r}", cell=repr(label))

        residue = prime % profile.block_size
        predicted, avalanche = profile.predict(prime, appended)
        entry = HitEntry(
            turn=len(self._entries),
            server=profile.name,
            cell=label,
            P1=prime,
            L=appended,
            B=profile.block_size,
            residue=residue,
            avalanche=avalanche,
            predicted_uncached=predicted,
            tail_uncached=profile.tail(prime, appended),
            observed_uncached=observed,
            avalanche_extrapolated=bool(avalanche and not profile.avalanche_measured),
        )
        self._entries.append(entry)
        return entry

    # -- reconciliation ----------------------------------------------------
    def _series(self, observed: Optional[Sequence[Any]]) -> list[tuple[Any, str, str]]:
        if observed is None:
            return [(e.observed_uncached, e.server, e.cell) for e in self._entries]
        items = list(observed)
        if len(items) != len(self._entries):
            raise PtrLawSeriesLengthError(
                f"observed series has {len(items)} entries for {len(self._entries)} recorded turns",
                turns=len(self._entries),
                series=len(items),
            )
        out: list[tuple[Any, str, str]] = []
        for index, (entry, item) in enumerate(zip(self._entries, items)):
            if isinstance(item, Mapping):
                if "observed_uncached" not in item:
                    raise PtrLawObservedInvalidError(
                        f"series entry {index} is a mapping with no observed_uncached key",
                        index=index,
                        keys=sorted(str(k) for k in item),
                    )
                server = item.get("server", entry.server)
                if server != entry.server:
                    raise PtrLawObservedInvalidError(
                        f"series entry {index} names server {server!r} but turn {entry.turn} "
                        f"was recorded on {entry.server!r}",
                        index=index,
                        recorded=entry.server,
                        supplied=server,
                    )
                cell = item.get("cell", entry.cell)
                if not isinstance(cell, str):
                    raise PtrLawObservedInvalidError(
                        f"series entry {index} has a non-string cell {cell!r}",
                        index=index,
                        cell=repr(cell),
                    )
                out.append((item.get("observed_uncached"), entry.server, cell))
            else:
                out.append((item, entry.server, entry.cell))
        return out

    def reconcile(self, observed: Optional[Sequence[Any]] = None) -> Reconciliation:
        """Check the law against observations, naming every turn it cannot explain.

        ``observed`` is either ``None`` (use what ``record`` stored per turn) or a
        series aligned one-to-one with the recorded turns: ``None``, an int, or a
        mapping ``{"observed_uncached": int|None, "server"?: str, "cell"?: str}``.
        """
        checks: list[TurnCheck] = []
        for (value, server, cell), entry in zip(self._series(observed), self._entries):
            if value is None:
                checks.append(
                    TurnCheck(
                        turn=entry.turn,
                        server=server,
                        cell=cell,
                        residue=entry.residue,
                        avalanche=entry.avalanche,
                        predicted_uncached=entry.predicted_uncached,
                        observed_uncached=None,
                        delta=None,
                        status="unknown",
                    )
                )
                continue
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise PtrLawObservedInvalidError(
                    f"series entry for turn {entry.turn} is not a non-negative int or None: {value!r}",
                    turn=entry.turn,
                    value=repr(value),
                )
            count = value
            delta = count - entry.predicted_uncached
            checks.append(
                TurnCheck(
                    turn=entry.turn,
                    server=server,
                    cell=cell,
                    residue=entry.residue,
                    avalanche=entry.avalanche,
                    predicted_uncached=entry.predicted_uncached,
                    observed_uncached=count,
                    delta=delta,
                    status="exact" if delta == 0 else "mismatch",
                )
            )
        return Reconciliation(tuple(checks))

    # -- totals ------------------------------------------------------------
    def summarise(self) -> LedgerSummary:
        """Billed tokens, what the avalanches cost, and how much of the bill the law explained."""
        reconciliation = self.reconcile()
        known = [e.observed_uncached for e in self._entries if e.observed_uncached is not None]
        residues: dict[int, int] = {}
        for entry in self._entries:
            residues[entry.residue] = residues.get(entry.residue, 0) + 1
        avalanches = [e for e in self._entries if e.avalanche]
        return LedgerSummary(
            turns=len(self._entries),
            billed_tokens=sum(e.predicted_uncached for e in self._entries),
            observed_billed_tokens=sum(known) if known else None,
            observed_unknown_turns=len(self._entries) - len(known),
            avalanche_count=len(avalanches),
            avalanche_tokens=sum(e.predicted_uncached for e in avalanches),
            avalanche_extra_tokens=sum(e.avalanche_tokens for e in avalanches),
            avalanche_extrapolated_turns=sum(1 for e in self._entries if e.avalanche_extrapolated),
            exact=len(reconciliation.exact),
            mismatched=len(reconciliation.mismatched),
            unknown=len(reconciliation.unknown),
            explained_fraction=reconciliation.explained_fraction,
            servers=tuple(sorted({e.server for e in self._entries})),
            residues=tuple(sorted(residues.items())),
        )


__all__ = [
    "Ledger",
    "read_ledger",
    "ROW_KEYS",
    "TOKEN_FIELDS",
    "LEDGER_CODES",
    "LEDGER_LAW_CODES",
    "FRAMING_TOKENS",
    "ServerProfile",
    "SERVER_PROFILES",
    "SGLANG_PROFILE",
    "VLLM_PROFILE",
    "server_profile",
    "predict_uncached",
    "law_L",
    "HitEntry",
    "TurnCheck",
    "Reconciliation",
    "LedgerSummary",
    "HitLedger",
]
