#!/usr/bin/env python3
"""grade_v2.py — additive re-grade of the config-C long-run rows under GRADE-V2.

The rule is pre-registered in longrun/GRADE-V2.md (written before this module).
score_longrun.py is NOT edited: this module imports it read-only to obtain the
ORIGINAL verdicts, then computes its own v2 verdicts side by side.

Usage:
  python3 grade_v2.py --rows measure/rows-longrun-c-2026-10-26.jsonl \
      --fixture longrun/runtime/LR-01.json \
      --out measure/rows-longrun-c-2026-10-26.grade-v2.json
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
# an "anchor" must be code-shaped: snake_case, dotted, ALLCAPS_CODE, or camelCase.
# prose filler ("before", "re-raising", "scope") is never an anchor (GRADE-V2 R2).
CODE_SHAPE = re.compile(r"(_|\.|[a-z][A-Z]|^[A-Z]{3,}$)")
FENCE = re.compile(r"```.*?(?:```|\Z)", re.S)
DETAILS = re.compile(r"<details>.*?(?:</details>|\Z)", re.S | re.I)
PREAMBLE = re.compile(
    r"(?i)(\bI need to read\b|\bI(?:\x27|\u2019)ll read\b|\bI will read\b|"
    r"\blet me read\b|\bLet me read\b|\bI(?:\x27|\u2019)m going to read\b)")
CAVEAT = re.compile(r"(?i)^\s*(?:#+\s*)?(?:caveat|note|nb|caveats)\b")


def load_scorer():
    spec = importlib.util.spec_from_file_location("score_longrun", HERE / "score_longrun.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prose(text):
    """answer with quoted material (fenced code, <details> blocks) removed."""
    text = DETAILS.sub("\n", text or "")
    text = FENCE.sub("\n", text)
    return text


def prose_lines(text):
    return [ln.strip() for ln in prose(text).splitlines() if ln.strip()]


TERMINAL = (".", "!", "?", ")")


def concluding_lines(text):
    """prose lines that end a sentence and are not merely a reading preamble."""
    return [ln for ln in prose_lines(text)
            if ln.rstrip().endswith(TERMINAL) and not PREAMBLE.search(ln)]


def has_conclusion(text, num_token=None):
    lines = prose_lines(text)
    if not lines:
        return False
    if num_token:
        for ln in lines:
            if ln.rstrip().endswith(TERMINAL) and num_token in ln:
                return True
        last = lines[-1].rstrip()
        if last.endswith(TERMINAL) and num_token in prose(text):
            return True
        return False
    return any(ln.rstrip().endswith(TERMINAL) for ln in lines)


def num_token(n):
    return re.compile(r"(?<![0-9.])" + re.escape(str(n)) + r"(?![0-9])")


def v2_numeric(answer, expected):
    tok = num_token(expected)
    if not tok.search(answer or ""):
        return False, "R1a: expected number %s absent as standalone token" % expected
    if not has_conclusion(answer, str(expected)):
        return False, "R1b: no concluding statement carrying %s" % expected
    return True, "R1: number %s as token + conclusion" % expected


def anchors_of(expected):
    return [a for a in dict.fromkeys(IDENT.findall(str(expected)))
            if CODE_SHAPE.search(a)]


def v2_prose(answer, expected):
    anchors = anchors_of(expected)
    if not anchors:
        return None, "R4: no anchors derivable"
    low = (answer or "").lower()
    missing = [a for a in anchors if a.lower() not in low]
    if missing:
        return False, "R2: missing anchors %s of %d" % (missing[:4], len(anchors))
    if not has_conclusion(answer):
        return False, "R2b: no concluding sentence"
    return True, "R2: all %d anchors + conclusion" % len(anchors)


def v2_regex(answer, pattern):
    terms = re.findall(r"\(\?=[^)]*?\.\*([^)]+)\)", str(pattern))
    if not terms:
        return None, "R4: regex without lookahead conjunction"
    flags = re.I if str(pattern).startswith("(?i") else 0
    if "(?is)" in str(pattern):
        flags = re.I | re.S
    low = answer or ""
    missing = [t for t in terms if not re.search(t, low, flags)]
    if missing:
        return False, "R3: missing %s of %d lookahead terms" % (missing[:4], len(terms))
    return True, "R3: %d/%d lookahead terms present" % (len(terms), len(terms))


def classify(expected, mode):
    if mode == "regex":
        return "regex"
    s = str(expected).strip()
    if re.fullmatch(r"\d+", s):
        return "numeric"
    return "prose"


def v2_grade(answer, expected, mode):
    kind = classify(expected, mode)
    if answer is None:
        return False, "R0: no record at the checkpoint turn"
    if not str(answer).strip():
        return False, "R0: empty answer"
    if kind == "numeric":
        return v2_numeric(answer, expected)
    if kind == "regex":
        got, why = v2_regex(answer, expected)
        if got is None:
            return None, why
        return got, why
    got, why = v2_prose(answer, expected)
    if got is None:
        return None, why
    return got, why


def checks_of(fixture):
    """the in-scope fact checks, in fixture order: checkpoints then acceptance facts."""
    out = []
    for i, cp in enumerate(fixture.get("checkpoints") or []):
        out.append({"id": str(cp.get("id") or "cp.t%s" % cp.get("turn")),
                    "turn": cp.get("turn"), "expected": cp.get("expected"),
                    "mode": str(cp.get("match", "exact")), "src": "checkpoints[%d]" % i})
    for raw in (fixture.get("acceptance") or {}).get("checks") or []:
        if not isinstance(raw, dict) or raw.get("kind") != "fact":
            continue
        out.append({"id": str(raw.get("id")), "turn": raw.get("turn"),
                    "expected": raw.get("expected"),
                    "mode": str(raw.get("match", "exact")), "src": "acceptance"})
    return out


def budget_cut(content):
    text = content or ""
    if text.count("```") % 2:
        return True, "unclosed code fence"
    lines = prose_lines(text)
    if lines:
        last = lines[-1].rstrip()
        if not last.endswith(TERMINAL + ("`", ":", "]", "}", '"', "'")):
            return True, "ends mid-sentence: %r" % last[-40:]
    return False, ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(HERE.parent / "measure" / "rows-longrun-c-2026-10-26.jsonl"))
    ap.add_argument("--fixture", default=str(HERE / "runtime" / "LR-01.json"))
    ap.add_argument("--out", default=str(HERE.parent / "measure" /
                                        "rows-longrun-c-2026-10-26.grade-v2.json"))
    args = ap.parse_args(argv)

    fixture_bytes = Path(args.fixture).read_bytes()
    import hashlib
    fsha = hashlib.sha256(fixture_bytes).hexdigest()
    scorer = load_scorer()
    fixture = scorer.normalise_fixture(json.loads(fixture_bytes.decode()), fsha)

    rows = [json.loads(ln) for ln in Path(args.rows).read_text().splitlines() if ln.strip()]
    arms = sorted({r.get("arm") for r in rows}, key=str)
    checks = checks_of(json.loads(fixture_bytes.decode()))

    result = {"schema": "consonance.grade-v2/1", "rows": str(args.rows),
              "fixture": str(args.fixture), "fixture_sha256": fsha,
              "rule": "GRADE-V2 (longrun/GRADE-V2.md), registered before scoring",
              "checks": [c["id"] for c in checks], "per_arm": {}, "turn_notes": {}}

    table = {}
    for arm in arms:
        arm_rows = [r for r in rows if r.get("arm") == arm]
        by_turn = {}
        for r in arm_rows:
            by_turn[int(r.get("turn"))] = r
        # ORIGINAL verdicts, from the untouched scorer
        header = {"fixture_sha256": fsha, "task_id": arm_rows[0].get("task_id"),
                  "arm": arm, "rep": arm_rows[0].get("rep")}
        card = scorer.score(fixture, scorer.index_run(
            [header] + [dict(r) for r in arm_rows], header), fsha)
        orig = {ch["id"]: ch["verdict"] for ch in card["checks"]}
        orig_req = [ch for ch in card["checks"] if ch.get("required")]

        new, skipped, details = {}, [], {}
        for c in checks:
            rec = by_turn.get(int(c["turn"]))
            ans = None if rec is None else rec.get("content")
            verdict, why = v2_grade(ans, c["expected"], c["mode"])
            if verdict is None:
                skipped.append(c["id"])
                details[c["id"]] = "unverifiable: " + why
            else:
                new[c["id"]] = "pass" if verdict else "fail"
                details[c["id"]] = why
        graded = [c["id"] for c in checks if c["id"] in new]
        old_pass = sum(1 for i in graded if orig.get(i) == "pass")
        new_pass = sum(1 for i in graded if new.get(i) == "pass")
        n = len(graded)

        pre = [r for r in arm_rows if PREAMBLE.search(r.get("content") or "")]
        pre_dead = [r for r in pre if not concluding_lines(r.get("content") or "")]
        cuts = [(int(r.get("turn")), budget_cut(r.get("content"))[1]) for r in arm_rows
                if budget_cut(r.get("content"))[0]]
        last = by_turn.get(48)
        last_cut, last_why = budget_cut((last or {}).get("content") or "")

        result["per_arm"][arm] = {
            "old_accuracy": [old_pass, n], "new_accuracy": [new_pass, n],
            "n_graded": n, "skipped_checks": skipped,
            "old_failed_ids": [i for i in graded if orig.get(i) != "pass"],
            "new_failed_ids": [i for i in graded if new.get(i) != "pass"],
            "required_old": [sum(1 for ch in orig_req if ch["verdict"] == "pass"), len(orig_req)],
            "required_failed_old": [ch["id"] for ch in orig_req if ch["verdict"] != "pass"],
            "v2_details": details,
            "preamble_turns": len(pre), "preamble_no_conclusion": len(pre_dead),
            "preamble_no_conclusion_turns": sorted(int(r.get("turn")) for r in pre_dead),
            "budget_cut_turns": len(cuts), "budget_cut_detail": cuts[:6],
            "turn48_truncated": bool(last_cut), "turn48_why": last_why,
            "turns_present": len(by_turn),
        }
        table[arm] = result["per_arm"][arm]

    print("\narm | old acc | new acc | n | old failed | new failed | preamble(no conclusion) | budget-cut | t48 trunc")
    for arm in arms:
        t = table[arm]
        print("%-16s | %2d/%2d | %2d/%2d | %2d | %d | %d | %d (%d) | %d | %s" % (
            arm, t["old_accuracy"][0], t["old_accuracy"][1], t["new_accuracy"][0],
            t["new_accuracy"][1], t["n_graded"], len(t["old_failed_ids"]),
            len(t["new_failed_ids"]), t["preamble_turns"], t["preamble_no_conclusion"],
            t["budget_cut_turns"], t["turn48_truncated"]))
        print("   old failed: %s" % t["old_failed_ids"])
        print("   new failed: %s" % t["new_failed_ids"])
        print("   required(old): %d/%d, failed %s" % (
            t["required_old"][0], t["required_old"][1], t["required_failed_old"]))

    Path(args.out).write_text(json.dumps(result, indent=1) + "\n")
    print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
