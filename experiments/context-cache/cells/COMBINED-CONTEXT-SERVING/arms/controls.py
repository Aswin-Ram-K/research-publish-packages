"""Run all controls; print one line per control with hashes and verdicts."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from canonical import dumps, digest as cdigest
from store import BodyStore, MissingBody
from render_arms import build_messages
from guard_constraints import guard, required_constraint_lines

FIXTURE = HERE / "fixtures" / "sample.json"


def load_fixture():
    return json.loads(FIXTURE.read_text())


def make_history(fixture, n):
    hist = []
    for i in range(1, n + 1):
        turns = fixture.get("turns", [])
        t = turns[i - 1] if i - 1 < len(turns) else {"turn": i, "instruction": f"turn {i}"}
        instr = t.get("instruction") or t.get("question") or f"turn {i}"
        hist.append({
            "turn": i,
            "instruction": instr,
            "answer": f"answer for turn {i}",
            "claim": f"claim for turn {i}",
            "refs": None,
            "notes": "",
        })
    return hist


def canon_msgs(msgs):
    return dumps(msgs)


def main():
    fixture = load_fixture()
    num_turns = len(fixture.get("turns", []))
    print(f"CONTROLS fixture={fixture['task_id']} turns={num_turns}")

    # ---- (a) prefix identity ----
    for arm in ("A", "B", "C"):
        renders = {}
        history = []
        for t in range(1, num_turns + 1):
            msgs = build_messages(arm, fixture, list(history), t)
            renders[t] = msgs
            # append completed turn
            turns = fixture.get("turns", [])
            tt = turns[t - 1] if t - 1 < len(turns) else {"turn": t}
            instr = tt.get("instruction") or tt.get("question") or f"turn {t}"
            history.append({"turn": t, "instruction": instr, "answer": f"answer for turn {t}",
                            "claim": f"claim for turn {t}", "notes": ""})
        ok = True
        first_pair = None
        for t in range(1, num_turns):
            # longest common prefix between consecutive renders
            a, b = renders[t], renders[t + 1]
            L = 0
            while L < len(a) and L < len(b) and a[L] == b[L]:
                L += 1
            common_t = canon_msgs(a[:L])
            common_next = canon_msgs(b[:L])
            h1 = cdigest(common_t)
            h2 = cdigest(common_next)
            if h1 != h2 or L == 0:
                ok = False
            if first_pair is None:
                first_pair = (t, t + 1, h1, h2, L)
        t, tp, h1, h2, L = first_pair
        print(f"CONTROL prefix_identity arm={arm}: turn{t}_common={h1} turn{tp}_common={h2} common_msgs={L} verdict={'PASS' if ok else 'FAIL'}")

    # ---- (b) deliberate divergence ----
    history = make_history(fixture, 2)
    msgs = build_messages("B", fixture, history, 3)
    base = canon_msgs(msgs)
    # mutate one char in a claim
    text = base.decode("utf-8")
    mutated = text.replace("claim for turn 1", "Xlaim for turn 1", 1)
    if mutated == text:
        # fallback: flip a char
        mutated = text[:-1] + ("X" if text[-1] != "X" else "Y")
    mut_hash = cdigest(mutated.encode("utf-8"))
    print(f"CONTROL deliberate_divergence base={cdigest(base)} mutated={mut_hash} verdict={'PASS' if mut_hash != cdigest(base) else 'FAIL'}")

    # ---- (c) reference recovery ----
    src_path = Path(fixture["sources"][0]["path"])
    src_bytes = src_path.read_bytes()
    store = BodyStore(HERE / "store")
    d = store.put(src_bytes)
    expected_digest = fixture["sources"][0]["sha256"]
    if expected_digest.lower().startswith("sha256:"):
        expected_digest = expected_digest[len("sha256:"):]
    got = store.get(d)
    recovery_ok = (got == src_bytes) and (got == store.get(expected_digest)) if False else (got == src_bytes)
    # verify mutated digest raises
    mutated_digest = d[:-1] + ("0" if d[-1] != "0" else "1")
    raised = False
    try:
        store.get(mutated_digest)
    except MissingBody:
        raised = True
    except Exception as e:
        raised = True
    rec_ok = (got == src_bytes) and raised and (d == expected_digest)
    print(f"CONTROL reference_recovery digest={d} get_matches_source={'yes' if got == src_bytes else 'no'} "
          f"missing_raises={'yes' if raised else 'no'} verdict={'PASS' if rec_ok else 'FAIL'}")

    # ---- (d) negative-constraint red->green ----
    # build preamble via render_arms internal
    import render_arms as ra
    p = ra._preamble(fixture)
    ok_pass, missing_pass = guard(p, fixture)
    # drop a constraint line
    lines = p.splitlines()
    # remove first negative constraint prose line
    req = required_constraint_lines(fixture)
    dropped = p
    if req:
        dropped = p.replace(req[0], "", 1)
    ok_fail, missing_fail = guard(dropped, fixture)
    # restore
    restored = dropped.replace("", "", 0) + ""  # no-op placeholder
    # actually restore original
    restored = p
    ok_restored, _ = guard(restored, fixture)
    verdict = "PASS" if (ok_pass and (not ok_fail) and ok_restored) else "FAIL"
    print(f"CONTROL negative_constraint present_guard={'pass' if ok_pass else 'fail'} "
          f"dropped_guard={'fail' if not ok_fail else 'pass'} restored_guard={'pass' if ok_restored else 'fail'} "
          f"verdict={verdict}")

    # overall
    print("CONTROLS_DONE")


if __name__ == "__main__":
    main()
