"""AGENTIC-CONTRACT: the one definition of a stage-2 episode's arms and its rows.

The TASK schema is not here.  ``consonance.longrun-fixture/2`` won the ruling
(2026-11-11) and is read by ``run_longrun.load_fixture``; the bespoke ``agentic-contract``
task shape was deleted with its loader, because a second task schema is a second
convention for the same measurement.

What remains is what more than one module needs:

* :data:`ARMS` — the five arms, in report order.  ``agentic_cell`` imports it for its
  ``--arms`` validation and ``analyze_agentic`` declares the same tuple for its report.
* :data:`TOOL_NAMES` — the tool surface an episode may declare.
* :data:`REQUIRED_ROW_KEYS` + :func:`validate_row` — the per-request row.  The cell
  validates every row it writes with this function and the analyser reads the same keys,
  so the writer and the reader cannot disagree about what a row is.
* :class:`ContractError` — the one error a row defect raises.
"""

from __future__ import annotations

ARMS = ("none", "masking-no-fetch", "pinned", "bounded-context-fetch", "compact")

#: The tool surface an episode may declare.  ``grep`` is bounded by the executor's own
#: constants (``run_longrun.GREP_MAX_HITS`` and friends), not by a copy here.
TOOL_NAMES = ("read_file", "grep")

#: Every key a per-request row must carry.  ``fetch_rounds``, ``compactions``, ``evicted``,
#: ``prompt_tokens_max`` and ``tools_schema_sent`` are the stage-2 additions: the first
#: three let a reader see the fold land on the row where it happened, and the last two are
#: measured from the request that was actually sent.
REQUIRED_ROW_KEYS = ("run_id", "harness_sha256", "arm", "task_id", "rep", "step", "kind",
                     "prompt_tokens", "tool_calls", "fetch_rounds", "fold_event",
                     "fold_kind", "compactions", "evicted", "prompt_tokens_max",
                     "tools_schema_sent", "answer", "expected", "verified",
                     "expected_present", "ts")


class ContractError(ValueError):
    """A row that does not satisfy this contract."""


def validate_row(row: dict) -> dict:
    """Return the row unchanged, or raise ContractError naming the first defect."""
    if not isinstance(row, dict):
        raise ContractError("row is not an object: %r" % (type(row).__name__,))
    for key in REQUIRED_ROW_KEYS:
        if key not in row:
            raise ContractError("row for %r step %r is missing required key %r"
                                % (row.get("task_id"), row.get("step"), key))
    if row["arm"] not in ARMS:
        raise ContractError("row arm %r is not one of %r" % (row["arm"], ARMS))
    if row["kind"] not in ("work", "final", "summary"):
        raise ContractError("row kind %r is not work/final/summary" % (row["kind"],))
    if not isinstance(row["tool_calls"], list):
        raise ContractError("row tool_calls must be a list, got %r"
                            % (type(row["tool_calls"]).__name__,))
    return row
