#!/usr/bin/env python3
"""G33 step 2-3: parse the reflex-decisions fixture into cases.json + blinded_cases.json
and run the pre-registered mechanical defect checks (PREREGISTRATION.md section 5).

Re-runnable. Never writes outside the sandbox directory.
Usage: python3 parse_fixture.py
"""
import json
import os
import re
import sys
import difflib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, os.pardir, "fixture", "reflex-decisions.ts")  # G41: shipped fixture; was "G51" (not in the ship set)

STR = r'"((?:[^"\\]|\\.)*)"'


def unescape(s: str) -> str:
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def split_records(text: str):
    """Records sit at 2-space indent: lines exactly '  {' ... '  },' (last: '  },')."""
    lines = text.split("\n")
    recs, cur, start = [], None, None
    for i, ln in enumerate(lines, 1):
        if ln == "  {":
            cur, start = [ln], i
        elif cur is not None:
            cur.append(ln)
            if ln in ("  },", "  }"):
                recs.append((start, "\n".join(cur)))
                cur = None
    return recs


def field(body: str, name: str, pattern: str):
    m = re.search(r"^\s*" + name + r":\s*" + pattern, body, re.M | re.S)
    if not m:
        return None
    return m.group(1)


def extract_array(body: str, name: str):
    """Return the text inside `name: [ ... ]`, bracket-matched with string-literal
    awareness. A naive non-greedy `\\[(.*?)\\]` is WRONG here: `N10-014`
    has the option string "the G08] ref list", whose `]` truncates the match.
    (Parser defect D-P1, caught by raw-text verification; see EVIDENCE.md.)"""
    m = re.search(r"^\s*" + re.escape(name) + r":\s*\[", body, re.M)
    if not m:
        return None
    i, depth, instr, esc = m.end(), 1, False, False
    start = i
    while i < len(body):
        ch = body[i]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                break
        i += 1
    return body[start:i]


def parse_list(raw):
    if raw is None:
        return None
    return [unescape(x) for x in re.findall(STR, raw)]


def main():
    with open(SRC, encoding="utf-8") as fh:
        text = fh.read()

    raw_records = split_records(text)
    cases, parse_failures = [], []

    for start_line, body in raw_records:
        cid = field(body, "id", STR)
        kind = field(body, "kind", STR)
        question = field(body, "question", STR)
        options_raw = extract_array(body, "options")
        correct = field(body, "correct", r"(-?\d+)")
        rationale = field(body, "rationale", STR)
        namespaces_raw = extract_array(body, "namespaces")

        missing = [n for n, v in (("id", cid), ("kind", kind), ("question", question),
                                  ("options", options_raw), ("correct", correct),
                                  ("rationale", rationale)) if v is None]
        if missing:
            parse_failures.append({"line": start_line, "missing_fields": missing})
            continue

        cases.append({
            "id": unescape(cid),
            "kind": unescape(kind),
            "question": unescape(question),
            "options": parse_list(options_raw),
            "correct": int(correct),
            "rationale": unescape(rationale),
            "namespaces": parse_list(namespaces_raw) or [],
            "_line": start_line,
        })

    n = len(cases)

    # --- pre-registered defect checks (section 5) -------------------------------
    oob = [{"id": c["id"], "correct": c["correct"], "n_options": len(c["options"]),
            "options": c["options"]} for c in cases
           if not (0 <= c["correct"] < len(c["options"]))]

    id_counts = Counter(c["id"] for c in cases)
    dup_ids = sorted([i for i, k in id_counts.items() if k > 1])

    norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
    qmap = {}
    for c in cases:
        qmap.setdefault(norm(c["question"]), []).append(c["id"])
    dup_q_exact = {k: v for k, v in qmap.items() if len(v) > 1}

    near = []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = norm(cases[i]["question"]), norm(cases[j]["question"])
            if a == b:
                continue
            r = difflib.SequenceMatcher(None, a, b).ratio()
            if r >= 0.90:
                near.append({"a": cases[i]["id"], "b": cases[j]["id"], "ratio": round(r, 4)})

    bad_arity = [{"id": c["id"], "n_options": len(c["options"])} for c in cases
                 if len(c["options"]) < 2 or len(c["options"]) > 8]

    opt_lens = [len(c["options"]) for c in cases]
    dist = Counter(c["options"][c["correct"]] for c in cases if 0 <= c["correct"] < len(c["options"]))
    single = [c["id"] for c in cases if len(c["options"]) == 1]

    summary = {
        "records_found": len(raw_records),
        "cases_parsed": n,
        "parse_failures": parse_failures,
        "options_total": sum(opt_lens),
        "options_per_case": dict(sorted(Counter(opt_lens).items())),
        "distinct_labels": len(dist),
        "label_distribution": dict(dist.most_common()),
        "label_distribution_by_kind": {
            k: dict(Counter(c["options"][c["correct"]] for c in cases
                            if c["kind"] == k and 0 <= c["correct"] < len(c["options"]))
                    .most_common())
            for k in sorted({c["kind"] for c in cases})},
        "single_option_cases": single,
        "duplicate_ids": dup_ids,
        "duplicate_questions_exact": dup_q_exact,
        "near_duplicate_questions": near,
        "answer_outside_option_set": oob,
        "bad_option_arity": bad_arity,
    }

    with open(os.path.join(HERE, "cases.json"), "w", encoding="utf-8") as fh:
        json.dump(cases, fh, indent=1)
    blinded = [{k: c[k] for k in ("id", "kind", "question", "options")} for c in cases]
    with open(os.path.join(HERE, "blinded_cases.json"), "w", encoding="utf-8") as fh:
        json.dump(blinded, fh, indent=1)
    with open(os.path.join(HERE, "parse_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)

    print(json.dumps(summary, indent=1))
    if parse_failures:
        print("PARSE FAILURES PRESENT", file=sys.stderr)


if __name__ == "__main__":
    main()
