"""Cell-matrix runner.

A *cell* is one (policy, case, depth) combination with a fixed salt; it is
repeated ``reps`` times so cache reuse across repetitions can be measured.
``send`` is injected -- in tests it is a fake returning the same 7-tuple as
``client.chat``; in the live gate it is ``functools.partial(ChatClient.chat,
max_tokens=...)``.  The runner itself performs no I/O and no network calls.

Eviction instrument (spec): turn 1 must have ``cached_tokens == 0``; if a
later turn drops to 0 after having been non-zero the whole cell is flagged.
The turn immediately following a compaction is exempt, because there the
prefix *is* expected to break -- that break is the thing compaction measures,
not an eviction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence

from resextract.context import (
    CacheMeter,
    CacheRow,
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    canonical_bytes,
    compact,
    default_est_tokens,
    make_salt,
    needs_compaction,
    render,
)

Send = Callable[[list[dict[str, str]]], Any]


def _truncating_summarizer(text: str) -> str:
    """Deterministic offline fallback summariser (no model call)."""

    limit = max(1, len(text) // 2)
    return text[:limit]


@dataclass(frozen=True)
class Turn:
    text: str
    volatile: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    case_id: str
    preamble: str
    turns: tuple[Turn, ...]

    def __post_init__(self) -> None:
        if not self.turns:
            raise ValueError("a case needs at least one turn")


@dataclass(frozen=True)
class Cell:
    cell: str
    arm: str
    policy: str
    case_id: str
    depth: int
    reps: int
    salt: str
    budget_tokens: int = 10**9
    keep_last: int = 2

    def __post_init__(self) -> None:
        RenderPolicy(self.policy)  # validate
        if self.depth < 1 or self.reps < 1:
            raise ValueError("depth and reps must be >= 1")


@dataclass
class CellResult:
    cell: str
    rows: list[CacheRow]
    events: list[dict[str, Any]]
    evicted: bool


def cell_salt(seed: int, policy: str, case_id: str, depth: int) -> str:
    """A distinct salt per cell, stable across repetitions of that cell."""

    key = f"{seed}:{policy}:{case_id}:{depth}"
    return make_salt(int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:12], 16))


def build_cells(
    *,
    policies: Iterable[str],
    cases: Iterable[str],
    depths: Iterable[int],
    reps: int,
    salt_seed: int = 0,
    budget_tokens: int = 10**9,
    keep_last: int = 2,
    arm: str = "main",
) -> list[Cell]:
    cells: list[Cell] = []
    for policy in policies:
        for case_id in cases:
            for depth in depths:
                cells.append(
                    Cell(
                        cell=f"{arm}/{policy}/{case_id}/d{depth}",
                        arm=arm,
                        policy=RenderPolicy(policy).value,
                        case_id=case_id,
                        depth=int(depth),
                        reps=int(reps),
                        salt=cell_salt(salt_seed, policy, case_id, int(depth)),
                        budget_tokens=budget_tokens,
                        keep_last=keep_last,
                    )
                )
    return cells


_POINTER_POLICIES = (RenderPolicy.POINTER, RenderPolicy.POINTER_FORK)


def prefix_sha256(policy: RenderPolicy, messages: Sequence[dict[str, str]]) -> str:
    """Digest of the *invariant prefix* that a radix cache should retain.

    Message 0 is the salted invariant head and every later message is one body
    node, verbatim and in chain order (``render._linear_messages``).  The
    pointing arms digest the head plus the chain's *opening* body
    (``keep = 2``), the message compaction rewrites -- a summary or fork node,
    or a later kept delta under a sliding window -- while ``NAIVE_MUTABLE``
    digests message 0 alone (``keep = 1``), the message its volatile block is
    interpolated into.  Appending a turn only extends the list, so it cannot
    change either digest: a change means the cacheable prefix itself was
    rewritten (salt/preamble edit, volatile value, fork label, compaction) --
    what ``analyze.compaction_effect`` correlates with TTFT.
    """

    keep = 2 if policy in _POINTER_POLICIES else 1
    return hashlib.sha256(canonical_bytes(list(messages)[:keep])).hexdigest()


def _unpack(result: Any) -> tuple[int, int, int, float, float, int | None, str]:
    """Accept the 7-tuple from client.chat or an equivalent mapping."""

    if isinstance(result, Mapping):
        return (
            int(result.get("prompt_tokens") or 0),
            int(result.get("cached_tokens") or 0),
            int(result.get("completion_tokens") or 0),
            float(result.get("ttft_ms") or 0.0),
            float(result.get("wall_ms") or 0.0),
            result.get("status"),
            str(result.get("text") or ""),
        )
    values = tuple(result)
    if len(values) != 7:
        raise ValueError(f"send() must return 7 values, got {len(values)}")
    prompt, cached, completion, ttft, wall, status, text = values
    return (
        int(prompt or 0),
        int(cached or 0),
        int(completion or 0),
        float(ttft or 0.0),
        float(wall or 0.0),
        status,
        str(text or ""),
    )


def run_cell(
    cell: Cell,
    case: Case,
    send: Send,
    meter: CacheMeter | None = None,
    *,
    compaction: CompactionPolicy | str = CompactionPolicy.SUMMARISE_IN_PLACE,
    summarizer: Callable[[str], str] = _truncating_summarizer,
    est_tokens: Callable[[str], int] = default_est_tokens,
) -> CellResult:
    """Execute one cell -- ``reps`` repetitions of ``depth`` turns."""

    if case.case_id != cell.case_id:
        raise ValueError(f"case {case.case_id!r} does not match cell {cell.case_id!r}")
    meter = meter if meter is not None else CacheMeter()
    policy = RenderPolicy(cell.policy)
    rows: list[CacheRow] = []
    events: list[dict[str, Any]] = []
    evicted = False

    for rep in range(1, cell.reps + 1):
        chain: list[StateNode] = [StateNode.create(case.preamble, "invariant")]
        seen_cached = False
        last_compaction_turn = -1
        for turn_no in range(1, cell.depth + 1):
            turn = case.turns[(turn_no - 1) % len(case.turns)]
            chain = chain + [StateNode.create(turn.text, "delta", parent=chain[-1], turn=turn_no)]

            if needs_compaction(
                chain, budget_tokens=cell.budget_tokens, est_tokens=est_tokens
            ):
                chain, event = compact(
                    chain,
                    compaction,
                    keep_last=cell.keep_last,
                    summarizer=summarizer,
                    est_tokens=est_tokens,
                )
                events.append({**event, "cell": cell.cell, "rep": rep, "turn": turn_no})
                last_compaction_turn = turn_no

            kwargs = dict(preamble=case.preamble, volatile=turn.volatile, salt=cell.salt)
            messages = render(policy, chain, **kwargs)
            prefix_sha = prefix_sha256(policy, messages)

            prompt, cached, completion, ttft, wall, status, _text = _unpack(send(messages))
            uncached = max(0, prompt - cached)

            flagged = False
            if turn_no == 1 and rep == 1:
                # Cold-start contract: the very first turn of a cell must miss.
                # Repetitions are *expected* to hit -- that is what reps measure.
                flagged = cached != 0
            elif seen_cached and cached == 0 and last_compaction_turn != turn_no:
                flagged = True
            if flagged:
                evicted = True
            if cached > 0:
                seen_cached = True

            row = CacheRow(
                cell=cell.cell,
                arm=cell.arm,
                policy=policy.value,
                case_id=cell.case_id,
                turn=turn_no,
                rep=rep,
                salt=cell.salt,
                prompt_tokens=prompt,
                cached_tokens=cached,
                uncached=uncached,
                ttft_ms=ttft,
                wall_ms=wall,
                completion_tokens=completion,
                status=None if status is None else int(status),
                evicted=flagged,
                prefix_sha256=prefix_sha,
            )
            rows.append(row)
            meter.record(row)

    if evicted:
        for row in rows:
            row.evicted = True
    return CellResult(cell=cell.cell, rows=rows, events=events, evicted=evicted)


def run_matrix(
    cells: Sequence[Cell],
    cases: Sequence[Case],
    send: Send,
    meter: CacheMeter | None = None,
    **kwargs: Any,
) -> list[CellResult]:
    """Run every cell against the case it names, in order."""

    by_id = {case.case_id: case for case in cases}
    meter = meter if meter is not None else CacheMeter()
    results: list[CellResult] = []
    for cell in cells:
        try:
            case = by_id[cell.case_id]
        except KeyError as exc:
            raise KeyError(f"cell {cell.cell!r} names unknown case {cell.case_id!r}") from exc
        results.append(run_cell(cell, case, send, meter, **kwargs))
    return results


def rows_json(rows: Sequence[CacheRow]) -> str:
    return json.dumps([row.to_dict() for row in rows], sort_keys=True, ensure_ascii=False)
