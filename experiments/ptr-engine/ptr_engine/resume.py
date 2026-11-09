"""Deterministic resume of a partial run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List, Optional


def _item_id(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("id", item.get("ref", repr(item))))
    return str(getattr(item, "id", getattr(item, "ref", repr(item))))


@dataclass
class RunState:
    pending: List[Any] = field(default_factory=list)
    completed: List[str] = field(default_factory=list)
    rows: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pending": self.pending,
            "completed": list(self.completed),
            "rows": list(self.rows),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RunState":
        return cls(
            pending=list(d.get("pending", [])),
            completed=list(d.get("completed", [])),
            rows=list(d.get("rows", [])),
        )


def run_items(
    items: Iterable[Any],
    worker: Callable[[Any], Any],
    state: Optional[RunState] = None,
) -> RunState:
    """Process items in order, recording rows; resumable via state."""
    if state is None:
        state = RunState(pending=list(items))
    else:
        # ensure pending covers not-yet-completed in original order
        done = set(state.completed)
        if not state.pending:
            state.pending = [x for x in items if _item_id(x) not in done]
    for item in list(state.pending):
        iid = _item_id(item)
        if iid in state.completed:
            state.pending.remove(item)
            continue
        row = worker(item)
        state.rows.append(row)
        state.completed.append(iid)
        state.pending.remove(item)
    return state


__all__ = ["RunState", "run_items"]
