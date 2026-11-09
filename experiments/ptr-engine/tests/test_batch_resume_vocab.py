from __future__ import annotations

from ptr_engine import batch_fetches, FetchRequest, RunState, run_items
from ptr_engine.outcomes import RETRIEVAL_OUTCOMES, OK, NOT_FOUND, STALE_OR_REVOKED, SCOPE_UNGRANTED


def test_batch_deterministic():
    reqs = [FetchRequest(ref=f"r{i}", body="x" * (i * 5 + 1), tokens=(i * 5 + 1)) for i in range(5)]
    a = batch_fetches(reqs, 12)
    b = batch_fetches(list(reversed(reqs)), 12)
    assert [ [r.ref for r in batch] for batch in a] == [ [r.ref for r in batch] for batch in b]


def test_batch_no_silent_drop_small_budget():
    reqs = [FetchRequest(ref=f"r{i}", tokens=10) for i in range(3)]
    batches = batch_fetches(reqs, 5)  # budget too small for any
    flat = [r.ref for b in batches for r in b]
    assert sorted(flat) == ["r0", "r1", "r2"]
    assert len(batches) == 3


def test_vocabulary_exhaustive():
    import ptr_engine.resolve as R
    src = open(R.__file__).read()
    # no bare outcome string literals outside outcomes module
    for lit in ("\"OK\"", "\"NOT_FOUND\"", "\"STALE_OR_REVOKED\"", "\"SCOPE_UNGRANTED\""):
        assert src.count(lit) == 0, lit
    assert set(RETRIEVAL_OUTCOMES) == {OK, NOT_FOUND, STALE_OR_REVOKED, SCOPE_UNGRANTED}
    assert len(RETRIEVAL_OUTCOMES) == 4


def test_resume_deterministic():
    items = [{"id": f"t{i}"} for i in range(6)]
    def worker(x):
        return ("row", x["id"])

    # uninterrupted
    st_full = run_items(items, worker)
    full_rows = list(st_full.rows)

    # interrupted mid-run
    st1 = RunState(pending=list(items))
    # process first 3 manually by slicing
    st1.pending = items[:3]
    st1 = run_items(items[:3], worker, state=st1)
    # resume with remaining
    st2 = run_items(items, worker, state=st1)
    assert st2.rows == full_rows
