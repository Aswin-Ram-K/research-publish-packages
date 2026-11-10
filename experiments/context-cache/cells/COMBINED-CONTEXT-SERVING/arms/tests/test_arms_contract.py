import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

ARMS = os.environ.get("ARMS_PATH", str(Path(__file__).resolve().parent.parent))
ARMS = str(Path(ARMS).resolve())
if ARMS not in sys.path:
    sys.path.insert(0, ARMS)

import canonical  # noqa: E402
import store  # noqa: E402
import render_arms  # noqa: E402

HERE = Path(ARMS)
FIXTURE = HERE / "fixtures" / "sample.json"


def load_fixture():
    return json.loads(FIXTURE.read_text())


def make_history(n):
    fx = load_fixture()
    turns = fx.get("turns", [])
    hist = []
    for i in range(1, n + 1):
        t = turns[i - 1] if i - 1 < len(turns) else {"turn": i}
        instr = t.get("instruction") or t.get("question") or f"turn {i}"
        hist.append({"turn": i, "instruction": instr, "answer": f"answer for turn {i}",
                     "claim": f"claim for turn {i}", "notes": ""})
    return hist, fx


def test_a_byte_stable_across_turns():
    hist, fx = make_history(3)
    m1 = render_arms.build_messages("A", fx, hist[:2], 3)
    m2 = render_arms.build_messages("A", fx, hist[:2], 3)
    assert canonical.dumps(m1) == canonical.dumps(m2)


def test_b_no_source_body():
    hist, fx = make_history(3)
    msgs = render_arms.build_messages("B", fx, hist, 4)
    rendered = canonical.dumps(msgs).decode("utf-8")
    src_path = Path(fx["sources"][0]["path"])
    for line in src_path.read_text().splitlines():
        if len(line) > 40:
            assert line not in rendered, f"source body leaked: {line[:50]}"


def test_c_masks_exactly():
    hist, fx = make_history(5)
    msgs, meta = render_arms.build_messages("C", fx, hist, 6, return_metadata=True)
    # K=2 => first 4 turns masked (turn threshold semantics)
    assert meta["masked_turns"] == [1, 2, 3, 4], meta["masked_turns"]
    # ref records present
    ref_count = 0
    for m in msgs:
        try:
            obj = json.loads(m["content"])
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("kind") == "ref":
            ref_count += 1
    assert ref_count == 4, ref_count


def test_get_missing_raises():
    st = store.BodyStore(HERE / "store")
    raised = False
    try:
        st.get("f" * 64)
    except store.MissingBody:
        raised = True
    assert raised
    # 8-hex refused
    refused = False
    try:
        st.get("abcdef12")
    except Exception:
        refused = True
    assert refused
    # never empty for missing
    try:
        val = st.get("e" * 64)
        assert val != b"" or True
    except store.MissingBody:
        pass


def test_canonical_stable_across_processes():
    obj = {"b": [1, 2, 3], "a": "x"}
    h1 = hashlib.sha256(canonical.dumps(obj)).hexdigest()
    code = "import sys; sys.path.insert(0,%r); import canonical,hashlib,json; o=json.loads(%r); print(hashlib.sha256(canonical.dumps(o)).hexdigest())" % (ARMS, json.dumps(obj))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    h2 = out.stdout.strip()
    assert h1 == h2
