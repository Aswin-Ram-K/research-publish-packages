"""Compaction honesty: the marker must state what happened, and epoch must not regress.

Two defects measured against the real ``ptr_engine.layers`` module:

D1  ``compile_prompt`` emptied ``state.journal`` and appended
    ``[summary: N turns folded into epoch E]`` -- a marker asserting a summary
    that does not exist.  A fact written at turn 1 is present at turns 1-23 and
    gone from turn 24 on, so the marker must say "dropped", not "summary".

D2  ``st.epoch = epoch`` at the end of ``compile_prompt`` overwrote the state
    with the caller's argument, so a caller passing ``epoch=0`` every turn made
    the epoch go 0 ... 0, 1 at the compaction, then back to 0.  The state is
    authoritative: epoch must be non-decreasing across turns.

The tests drive the real module with ``epoch=0`` on every turn, exactly the
stale-caller shape that exposed D2.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE_ROOT = os.path.dirname(LONGRUN)
if ENGINE_ROOT not in sys.path:
    sys.path.insert(0, ENGINE_ROOT)

from ptr_engine.layers import (  # noqa: E402
    COMPACT_EVERY,
    CompactionState,
    compile_prompt,
    format_journal_line,
)

TURNS = 28
FACT = "doc-fact-01 value 3001"


class _Run:
    def __init__(self):
        self.system = "system text"
        self.tool_schema = None
        self.answer_grammar = None
        self.model = "offline-model"
        self.fixture = "u-spcc-32"
        self.generation = "gen-7"
        self.run_id = "u-spcc-32"


def _drive(turns=TURNS):
    """Compile ``turns`` prompts, always passing the stale ``epoch=0``."""
    st = CompactionState()
    run = _Run()
    prompts = []
    for t in range(1, turns + 1):
        content = FACT if t == 1 else "turn %d" % t
        line = format_journal_line(t, "user", content)
        prompts.append(
            compile_prompt(run, st, epoch=0, journal=[line], work="work %d" % t)
        )
    return st, run, prompts


def test_fact_evicted_at_compaction_boundary():
    """The eviction is real: present 1-23, absent 24+ (now stated honestly)."""
    _st, _run, prompts = _drive()
    assert COMPACT_EVERY == 24
    for i in range(0, 23):  # turns 1..23
        assert FACT in prompts[i], "fact missing at turn %d" % (i + 1)
    for i in range(23, TURNS):  # turns 24..28
        assert FACT not in prompts[i], "fact unexpectedly retained at turn %d" % (i + 1)


def test_marker_states_dropped_not_summary():
    """Turn 26 carries the honest marker and never claims a summary."""
    _st, _run, prompts = _drive()
    p26 = prompts[25]
    assert "[compacted: 24 turns dropped at epoch 1]" in p26
    assert "summary" not in p26.lower()


def test_epoch_monotonic_and_agrees_everywhere():
    """st.epoch, _Prompt.epoch and run.epoch agree and never decrease."""
    st, run, prompts = _drive()
    seen = [p.epoch for p in prompts]
    assert seen == sorted(seen), "epoch regressed: %r" % (seen,)
    assert seen[23] == 1, "compaction at turn 24 must advance epoch to 1"
    assert seen[24] == 1, "turn 25 must not regress epoch to 0"
    assert st.epoch == 1
    assert run.epoch == 1
    for p in prompts:
        assert p.epoch == st.epoch or p.epoch <= st.epoch
    assert prompts[-1].epoch == st.epoch == run.epoch == 1


def test_compactions_increments_exactly_once():
    st, run, prompts = _drive()
    assert st.compactions == 1
    assert run.compactions == 1
    assert prompts[-1].compactions == 1
