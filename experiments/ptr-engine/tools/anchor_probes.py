#!/usr/bin/env python3
"""anchor_probes.py - the R2.1 probe corpus, honest about what it measures.

    python3 experiments/ptr-engine/tools/anchor_probes.py            # check corpus
    python3 experiments/ptr-engine/tools/anchor_probes.py --json     # machine-readable

OFFLINE. Stdlib only. No network, no model call, no re-grade, no accuracy number,
no arm comparison. Reads (all read-only): the v6 row/grade files, one v4 fixture,
and the engine sources cited by the checkpoint. Writes nothing. Exits 0 iff every
probe returns the verdict R2.1 must return; exits 1 and names each mismatch.

Each result carries the classifier's per-anchor occurrence evidence, and the
declared metric (`mention-only`, `semantic: false`), so that an ACCEPT here can
never be quoted as a semantic verdict on the arm. See
`experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md` section 1.2.

Probes and their honest verdicts:

  A          real V6 cp.2.t46 answer          -> ACCEPT   (R1 rejected it on `raising`)
  B          record_refusal -> write_audit    -> REJECT   (missing record, refusal)
  C-minimal  `scope=` -> `grant=` only        -> ACCEPT   (label says ACCEPT: the
                                                            author's reported rejection
                                                            came from a GLOBAL
                                                            substitution, not this edit)
  C-global   every `scope` -> `grant`         -> REJECT   (missing scope)
  E          verifier negation probe          -> ACCEPT, metric mention-only,
                                                            semantic false
  F          (this card) every anchor kept, guard inverted and arguments swapped
                                              -> ACCEPT, and that acceptance is the
                                                            declared limitation
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anchor_classify as ac  # noqa: E402

ROOT = ac.ROOT
GRADE = "experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json"
ROWS = "experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl"
CP2_ID = "cp.2.t46"
CP2_SOURCE = "experiments/ptr-engine/ptr_engine/resolve.py#L66-L71"
CP2_EXPECTED = ("ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), "
                "before re-raising")

#: sha256 of the V6 cp.2.t46 answer text as the verifier pinned it
#: (`V-ANCHOR-PREREG.json`, short `ecdb3fc9d9f0`). The row text is identified by
#: this digest, never by position or hand-copying.
V6_ANSWER_SHA_PREFIX = "ecdb3fc9d9f0"


def _abs(rel):
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


# ---------------------------------------------------------------------------
# probe A's input: the REAL row, found by its digest
# ---------------------------------------------------------------------------
def find_v6_answer(rows_path=ROWS, prefix=V6_ANSWER_SHA_PREFIX):
    """The V6 cp.2.t46 answer text, located by its sha256 prefix."""
    hits = []

    def walk(node):
        if isinstance(node, str):
            if hashlib.sha256(node.encode("utf-8")).hexdigest().startswith(prefix):
                hits.append(node)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    with open(_abs(rows_path), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                walk(json.loads(line))
    uniq = sorted(set(hits))
    if len(uniq) != 1:
        raise SystemExit("expected exactly 1 row text with sha256 prefix %s, found %d"
                         % (prefix, len(uniq)))
    return uniq[0]


def grade_note():
    """The v6 grade file's own recorded verdict for cp.2.t46 / pointer-stable."""
    with open(_abs(GRADE), encoding="utf-8") as fh:
        grade = json.load(fh)
    for arm in grade.get("arms", {}).values():
        for check in arm.get("checks", []):
            if check.get("id") == CP2_ID:
                return check
    raise SystemExit("grade file carries no %s check" % (CP2_ID,))


# ---------------------------------------------------------------------------
# judging: R2.1 (mention-only) and the R1 baseline the flips are measured against
# ---------------------------------------------------------------------------
def judge_all(answer, anchors):
    """R1-style judge: EVERY derived anchor required (the pre-R2 baseline)."""
    marker = ac.marker_line(answer)
    missing = [a for a in anchors if not ac.mentions(a, answer)]
    if marker is None:
        return "REJECT", "marker_missing", missing
    if missing:
        return "REJECT", "missing_anchor:" + ",".join(missing), missing
    return "ACCEPT", "ok", []


def probe_results():
    answer_a = find_v6_answer()
    cells = ac.required_anchors(CP2_EXPECTED, CP2_SOURCE)
    evidence = [c.as_dict() for c in cells]
    required = [c.anchor for c in cells if c.cls == ac.CODE_SYMBOL]
    all_anchors = ac.derive_anchors(CP2_EXPECTED)

    def result(pid, answer, expect, note, extra=None):
        judged = ac.judge(answer, cells)
        row = {
            "id": pid,
            "expect": expect,
            "observed": judged["verdict"],
            "ok": judged["verdict"] == expect,
            "reason": judged["reason"],
            "missing": judged["missing"],
            "required": required,
            "answer": answer,
            "metric": ac.METRIC,
            "semantic": ac.SEMANTIC,
            "rule": ac.RULE,
            "note": note,
            "evidence": evidence,
        }
        row.update(extra or {})
        return row

    probes = []

    # -- A: the real V6 answer, never hand-typed -----------------------------
    a_r1, a_r1_reason, a_r1_missing = judge_all(answer_a, all_anchors)
    note = ("real V6 cp.2.t46 row text, located by sha256 %s; R2.1 accepts because "
            "every required token is present. R1 (all 9 anchors) rejected it as %s "
            "-- the only difference is the prose connector `raising`."
            % (V6_ANSWER_SHA_PREFIX, a_r1_reason))
    probes.append(result("A", answer_a, "ACCEPT", note, {
        "answer_sha256": hashlib.sha256(answer_a.encode()).hexdigest(),
        "r1": {"verdict": a_r1, "reason": a_r1_reason, "missing": a_r1_missing},
    }))

    # -- B: wrong method ----------------------------------------------------
    b = answer_a.replace("record_refusal", "write_audit")
    probes.append(result(
        "B", b, "REJECT",
        "`record_refusal` -> `write_audit`: the call no longer exists on Ledger, and "
        "the anchors `record`/`refusal` disappear with it."))

    # -- C-minimal: the ONE edit the author's table described ---------------
    c_min = answer_a.replace("scope=", "grant=", 1)
    probes.append(result(
        "C-minimal", c_min, "ACCEPT",
        "CORRECTION to ANCHOR-PREREG.md section 5 probe C: the minimal edit "
        "`scope=` -> `grant=` is ACCEPTED, because `scope` survives inside "
        "`scope_name`. The rejection the author reported came from the checker's "
        "GLOBAL `scope` -> `grant` substitution (see C-global / probe C-global), "
        "not from this edit. The verdict here is ACCEPT and it is labelled ACCEPT.",
        {"label": "ACCEPT", "correction": "author's table overstated probe C",
         "replaces": "ANCHOR-PREREG.md section 5 probe C"}))

    # -- C-global: the stronger edit that actually rejects ------------------
    c_glob = answer_a.replace("scope", "grant")
    probes.append(result(
        "C-global", c_glob, "REJECT",
        "every `scope` -> `grant` (so `scope_name` -> `grant_name`): the anchor "
        "`scope` is genuinely gone. This is the edit the author's checker performed "
        "and described as the one-kwarg edit."))

    # -- E: the verifier's negation probe ----------------------------------
    e = ("ANSWER: do NOT call ledger.record_refusal; ignore scope, serialized_ref, "
         "text, code and error entirely.")
    probes.append(result(
        "E", e, "ACCEPT",
        "verifier's added probe (V-ANCHOR-PREREG overstated[1]): every required token "
        "is named and the meaning is inverted. ACCEPTED by design -- this is the "
        "mention-only limitation, NOT a semantic pass on the arm and NOT a failure "
        "of the answer rule as specified.",
        {"metric": "mention-only", "semantic": False,
         "quote_as": "mention-only acceptance, not a semantic verdict"}))

    # -- F: this card's added probe — same tokens, inverted guard, swapped args
    f = ("ANSWER: ledger.record_refusal(scope=text, serialized_ref=scope_name, "
         "code=error.code) -- but only when ledger is None, so no refusal is ever "
         "recorded.")
    probes.append(result(
        "F", f, "ACCEPT",
        "ADDED by this card: keeps all 8 anchors but swaps `scope`/`serialized_ref` "
        "arguments and inverts the guard (`if ledger is not None` -> `when ledger is "
        "None`), so it records nothing. R2.1 must ACCEPT it: a mention-based metric "
        "cannot detect this, and pretending otherwise would be the silent upgrade "
        "the rule forbids.",

        {"why_accept_is_honest":
         "every required token is present; R2.1 judges presence only (section 1.2)"}))

    return probes, cells, answer_a


def main(argv=None):
    ap = argparse.ArgumentParser(description="check the R2.1 probe corpus")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of lines")
    args = ap.parse_args(argv)

    probes, cells, answer_a = probe_results()

    # honesty guards on the corpus itself ----------------------------------
    problems = []
    if "```" in answer_a:
        problems.append("probe A text is fenced: judge() would need strip_fences")
    note = grade_note()
    if "raising" not in (note.get("detail") or ""):
        problems.append("grade file detail does not name `raising`: the R1->R2 flip "
                        "premise is not reproduced")
    if not answer_a.startswith((note.get("found_excerpt") or "\0")[:60]):
        problems.append("row text does not start with the grade file's found_excerpt")

    failed = [p for p in probes if not p["ok"]]

    if args.json:
        print(json.dumps({"probes": probes, "problems": problems,
                          "metric": ac.METRIC, "semantic": ac.SEMANTIC,
                          "rule": ac.RULE,
                          "classifier_sha256": hashlib.sha256(
                              open(os.path.join(HERE, "anchor_classify.py"), "rb").read()
                          ).hexdigest()}, indent=1))
    else:
        print("R2.1 probe corpus  (metric=%s, semantic=%s, rule=%s)"
              % (ac.METRIC, ac.SEMANTIC, ac.RULE))
        print("required anchors: %s" % (", ".join(
            "%s=%s" % (c.anchor, c.cls) for c in cells),))
        for p in probes:
            print("%-10s %-6s expected %-6s  %s  missing=%s"
                  % (p["id"], p["observed"], p["expect"],
                     "OK" if p["ok"] else "MISMATCH", p["missing"] or "-"))
            print("           %s" % (p["note"],))
            for c in p["evidence"]:
                print("           evidence %-11s %-16s %s"
                      % (c["anchor"], c["class"], c["evidence"]))
        for msg in problems:
            print("PROBLEM: %s" % (msg,))
        print("RESULT: %s" % ("PASS" if not failed and not problems else "FAIL",))

    return 0 if not failed and not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
