import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE_ROOT = os.path.dirname(LONGRUN)
if ENGINE_ROOT not in sys.path:
    sys.path.insert(0, ENGINE_ROOT)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

from ptr_engine import compile_prompt, CompactionState, PtrPrefixDrift, COMPACT_EVERY  # noqa: E402


def _run(system="system text", model="m1", fixture="f1", generation="gen-7"):
    class R:
        pass
    o = R()
    o.system = system
    o.tool_schema = {"b": 2, "a": 1}
    o.answer_grammar = None
    o.model = model
    o.fixture = fixture
    o.generation = generation
    o.run_id = "run-1"
    return o


def _idx():
    return ["@doc:key@r1~312 scope=default", "@artifact:plan@3~12 scope=default"]


def test_determinism():
    run = _run()
    state = CompactionState(index_lines=_idx())
    journal = ["T1|user|hello"]
    work = "question?"
    a = compile_prompt(run, state, epoch=0, journal=journal, work=work)
    state2 = CompactionState(index_lines=_idx())
    b = compile_prompt(run, state2, epoch=0, journal=journal, work=work)
    assert str(a) == str(b)
    assert a.prefix_sha256 == b.prefix_sha256
    assert a.encode() == b.encode()


def test_drift():
    run = _run()
    state = CompactionState(index_lines=_idx())
    journal = ["T1|user|hello"]
    compile_prompt(run, state, epoch=0, journal=journal, work="q")
    run.system = run.system + "X"
    try:
        compile_prompt(run, state, epoch=state.epoch, journal=journal, work="q2")
    except PtrPrefixDrift:
        return
    raise AssertionError("expected PtrPrefixDrift")


def test_prefix_stability():
    run = _run()
    state = CompactionState(index_lines=_idx())
    journal = []
    prefixes = []
    l3_sizes = []
    fetch_turns = {5, 12, 19}
    work_base = "base question"
    for t in range(1, 25):
        if t in fetch_turns:
            work = work_base + "\n<fetched body turn %d>" % t
        else:
            work = work_base
        out = compile_prompt(run, state, epoch=state.epoch, journal=journal, work=work)
        prefixes.append(out.prefix_sha256)
        l3_sizes.append(out.layer_tokens["L3"])
    assert len(set(prefixes)) == 1, "prefix_sha256 changed across turns"
    grows = sum(1 for i in range(1, len(l3_sizes)) if l3_sizes[i] > l3_sizes[i - 1])
    assert grows == 3, "L3 grew %d times, expected 3" % grows


def test_compaction():
    run = _run()
    state = CompactionState(index_lines=_idx())
    journal = ["T%d|user|c%d" % (i, i) for i in range(1, 25)]
    before = list(state.index_lines)
    out = compile_prompt(run, state, epoch=0, journal=journal, work="q25")
    assert state.compactions == 1
    assert state.epoch == 1
    assert state.journal == []
    for ln in _idx():
        assert ln in state.index_lines
    # The fold record is a PIN, not an L1 line: it must persist on every later
    # turn, and PINS is append-only, so the record extends the cached prefix
    # instead of rewriting L1 (which would re-prefill everything after it).
    assert state.index_lines == before, "the fold rewrote L1: %r" % (state.index_lines,)
    assert len(state.pins) == 1, "expected exactly one fold pin, got %r" % (state.pins,)
    pin = state.pins[0]
    assert pin == "P1|fold|T24|24 turns dropped at epoch 1", pin
    # Honesty property: the fold drops turns, it does not summarise them.
    assert "summary" not in pin.lower(), "pin claims a summary: %r" % pin
    # The record names how many turns were dropped and the epoch it opened.
    assert str(len(journal)) in pin, (
        "pin does not name the %d dropped turns: %r" % (len(journal), pin))
    assert out.epoch == 1
    assert out.compactions == 1
    # PINS is rendered and counted once it carries a pin.
    assert out.layer_tokens["PINS"] > 0, out.layer_tokens


def test_fold_pin_persists_and_extends_the_prefix():
    """The fold record survives every later turn and never rewrites the prefix."""
    run = _run()
    state = CompactionState(index_lines=_idx())
    journal = ["T%d|user|c%d" % (i, i) for i in range(1, 25)]
    out25 = compile_prompt(run, state, epoch=0, journal=journal, work="q25")
    prefix25 = out25.prefix_sha256
    # Turns 26-28: the record is still in PINS, and the prefix does not move.
    for t in range(26, 29):
        out = compile_prompt(run, state, epoch=state.epoch,
                             journal=["T%d|user|c%d" % (t, t)], work="q%d" % t)
        assert out.prefix_sha256 == prefix25, "prefix moved after the fold at T%d" % t
        assert "P1|fold|T24|24 turns dropped at epoch 1" in str(out), (
            "the fold record vanished at T%d" % t)
        assert out.layer_tokens["PINS"] > 0


def test_no_pins_means_no_pins_block():
    """An arm that never pins renders no PINS block and no PINS key."""
    run = _run()
    state = CompactionState(index_lines=_idx())
    out = compile_prompt(run, state, epoch=0, journal=[], work="q")
    assert "PINS" not in out.layer_tokens, out.layer_tokens
    assert set(out.layer_tokens) == {"L0", "L1", "L2", "L3", "L4"}
    # ... and the prefix is exactly the pre-PINS L0+L1 hash: the first two
    # blocks of the prompt, with no empty PINS block inserted between them.
    import hashlib
    parts = str(out).split("\n\n")
    assert parts[1].startswith("@artifact:"), parts[1]
    assert out.prefix_sha256 == hashlib.sha256(
        ("\n\n".join(parts[:2])).encode("utf-8")).hexdigest()


def test_fetch_isolation():
    run = _run()
    state = CompactionState(index_lines=_idx())
    journal = []
    out12 = compile_prompt(run, state, epoch=0, journal=journal, work="turn12 question")
    prefix12 = out12.prefix_sha256
    out13 = compile_prompt(run, state, epoch=state.epoch, journal=journal, work="turn13 question\n<fetched body>")
    assert out13.prefix_sha256 == prefix12, "fetch changed L0+L1+L2"


if __name__ == "__main__":
    test_determinism()
    test_drift()
    test_prefix_stability()
    test_compaction()
    test_fold_pin_persists_and_extends_the_prefix()
    test_no_pins_means_no_pins_block()
    test_fetch_isolation()
    print("ALL OK")
