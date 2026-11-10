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
    out = compile_prompt(run, state, epoch=0, journal=journal, work="q25")
    assert state.compactions == 1
    assert state.epoch == 1
    assert state.journal == []
    for ln in _idx():
        assert ln in state.index_lines
    assert any("summary" in ln.lower() for ln in state.index_lines)
    assert out.epoch == 1
    assert out.compactions == 1


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
    test_fetch_isolation()
    print("ALL OK")
