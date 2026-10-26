#!/usr/bin/env python3
"""anchor_prereg_check.py - acceptance checker for ANCHOR-PREREG (rule R2).

OFFLINE. Stdlib only. No network, no requests/httpx import, no model call, no
re-grade of any arm. Reads fixtures, engine sources, the v6 row/grade files and
ANCHOR-PREREG.md (all read-only) and re-derives:

  Task 1  the anchor census: for every v4 checkpoint, classify each anchor token
          that grade_v3.py:55-63 derives from `expected` as
              CODE-SYMBOL      the token occurs in the cited source file outside
                               any string literal / comment (kind=A code token)
              NUMBER           the expected value is a numeric literal, with the
                               source line that establishes it
              PROSE-CONNECTOR  every occurrence in the cited file lies inside a
                               string literal or comment, or the token is absent
                               from that file entirely (an English connective
                               introduced by the expected string, e.g. "raising"
                               inside "before re-raising")
          and compares the result cell-for-cell to the table recorded in
          experiments/ptr-engine/longrun/ANCHOR-PREREG.md.

  Task 3  the two-sided probe, judged by a faithful re-implementation of the
          non-numeric branch of grade_v3.judge (marker present; every required
          anchor present; the marker line carries >=1 required anchor):
            correct paraphrase  V6's real cp.2.t46 answer (loaded from the row
                                file, never hand-typed) must be REJECTED under R1
                                and ACCEPTED under R2
            wrong answer        the same sentence with ledger.write_audit(...)
                                replacing ledger.record_refusal(...) must be
                                REJECTED under R2 as well

  Task 4  counts only: per grid on disk, how many arm-checks were rejected
          solely on a PROSE-CONNECTOR anchor (i.e. would flip under R2).

Exit 0 iff the census matches the recorded table AND
  correct paraphrase: R1 rejects, R2 accepts AND wrong answer: R2 rejects.
Exit 1 otherwise, naming the differing cells / violated probe.

    python3 experiments/ptr-engine/tools/anchor_prereg_check.py
    python3 experiments/ptr-engine/tools/anchor_prereg_check.py --print-table

Idempotent: writes nothing, same output on every run.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import tokenize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

FIXTURES = [
    "experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json",
    "experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json",
]
PREREG = "experiments/ptr-engine/longrun/ANCHOR-PREREG.md"
V6_ROWS = "experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl"
V6_GRADE = "experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json"
GRADE_V3 = "experiments/ptr-engine/longrun/grade_v3.py"
GRIDS = [
    "measure/rows-longrun-c-2026-10-26.grade-v3.json",
    "measure/rows-longrun-v3-2026-10-26.grade-v3.json",
    "measure/rows-longrun-v3-2026-10-26.grade-v3-final.json",
    "measure/rows-longrun-v4-2026-10-26.grade-v3.json",
    "measure/rows-longrun-v4-tools-2026-10-26.grade-v3.json",
    "measure/rows-longrun-v5-tools.grade-v3.json",
    "measure/rows-longrun-v6-tools.grade-v3.json",
]

# ---- grade_v3.py:15-24, copied verbatim in behaviour (read-only rule of record)
STOPWORDS = set("""
that this than then them they their there these those with from into over
also both each only when where which while would should could must have
has had been being will shall about above across after before below between
more most some such same just like make makes made used using does doing
then once only also very much many what whom whose here were was are and
for the but not you your our its his her all any can may
""".split())
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
MARKER_RE = re.compile(r"^ANSWER:\s*\S.*$")          # grade_v3.py:26
FENCE_RE = re.compile(r"^\s*(```|~~~)")              # grade_v3.py:25


def anchors(s):
    """grade_v3.py:55-63 - derive the anchor list from an expected string."""
    seen, out = set(), []
    for m in TOKEN_RE.finditer(s):
        for part in m.group(0).split("_"):
            p = part.lower()
            if len(p) >= 4 and p not in STOPWORDS and p not in seen:
                seen.add(p)
                out.append(p)
    return out


def has_anchor(text, anchor):
    """grade_v3.py:66-70."""
    return re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(anchor),
                     text, re.I) is not None


def strip_fences(text):
    out, inside = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def marker_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    if lines and MARKER_RE.match(lines[-1].strip()):
        return lines[-1].strip()
    return None


# ------------------------------------------------------------------ task 1
def prose_lines(path):
    """Line numbers covered by a STRING or COMMENT token in `path`."""
    with open(path, "rb") as fh:
        toks = list(tokenize.tokenize(fh.readline))
    return {t.start[0] for t in toks if t.type in (tokenize.STRING, tokenize.COMMENT)}


def occurrences(path, anchor):
    """[(line, is_prose)] for every word-boundary occurrence of `anchor`."""
    prose = prose_lines(path)
    hits = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if has_anchor(line, anchor):
                hits.append((i, i in prose))
    return hits


def classify(source_ref, anchor):
    """-> (class, evidence). source_ref = 'path#L66-L71'."""
    path, _, lineref = source_ref.partition("#")
    hits = occurrences(os.path.join(ROOT, path), anchor)
    code = [l for l, isprose in hits if not isprose]
    prose = [l for l, isprose in hits if isprose]
    if code:
        return "CODE-SYMBOL", "%s:%d" % (path, code[0])
    if prose:
        return "PROSE-CONNECTOR", "%s:%d (docstring/comment only; no code occurrence)" % (
            path, prose[0])
    return "PROSE-CONNECTOR", "absent from %s (0 occurrences)" % path


def number_evidence(expected, source_ref):
    """Source line that establishes a numeric expected value."""
    path, _, lineref = source_ref.partition("#")
    full = os.path.join(ROOT, path)
    with open(full, encoding="utf-8") as fh:
        ptr = []
        for i, line in enumerate(fh, 1):
            if re.search(r"(?<![\d.])%s(?![\d.])" % re.escape(str(expected)), line):
                return "%s:%d" % (path, i)
            if line.startswith("class Ptr"):
                ptr.append(i)
    # a counted value: the number of `class Ptr*` definitions and where the last
    # one sits is what establishes it (expected 31 -> 31 definitions, last :247)
    if ptr and str(expected) == str(len(ptr)):
        return "%s:%d-%d (%d class-Ptr definitions, last at :%d)" % (
            path, ptr[0], ptr[-1], len(ptr), ptr[-1])
    return "absent from %s" % path


def census(unique=True):
    """[(checkpoint_id, token, class, evidence)] derived from the fixture.

    The two v4 fixtures carry byte-identical checkpoint arrays (tools2 adds only
    tools_channel), so `unique=True` collapses the duplicate cells and the
    equality of the two fixtures is checked separately.
    """
    rows = []
    for fx in FIXTURES:
        d = json.load(open(os.path.join(ROOT, fx)))
        for idx, cp in enumerate(d.get("checkpoints") or []):
            cid = str(cp.get("id") or "cp.%d.t%s" % (idx, cp.get("turn")))
            exp = str(cp.get("expected", cp.get("answer", "")))
            src = cp.get("source", "")
            toks = anchors(exp)
            if re.fullmatch(r"-?\d+(?:\.\d+)?", exp.strip()):
                rows.append((cid, exp.strip(), "NUMBER", number_evidence(exp.strip(), src)))
            for t in toks:
                cls, ev = classify(src, t)
                rows.append((cid, t, cls, ev))
    return list(dict.fromkeys(rows)) if unique else rows


def recorded_census():
    """The census table recorded in ANCHOR-PREREG.md between the sentinels."""
    path = os.path.join(ROOT, PREREG)
    if not os.path.exists(path):
        return None
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"<!-- census:begin -->(.*?)<!-- census:end -->", txt, re.S)
    if not m:
        return None
    out = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] in ("checkpoint id",) or set(cells[0]) <= set("-: "):
            continue
        out.append((cells[0], cells[1], cells[2], cells[3]))
    return out


# ------------------------------------------------------------------ judge
def judge_R1(text, exp, required_marker=True):
    """R1 (§4 as implemented): every anchor derived from expected is required."""
    need = anchors(exp)
    return _judge(text, need, required_marker)


def judge_R2(text, exp, required_marker=True):
    """R2: required = derived anchors classified CODE-SYMBOL or NUMBER only."""
    src = None
    for fx in FIXTURES:
        d = json.load(open(os.path.join(ROOT, fx)))
        for cp in d.get("checkpoints") or []:
            if str(cp.get("expected", cp.get("answer", ""))) == exp:
                src = cp.get("source", "")
                break
        if src:
            break
    need = [a for a in anchors(exp) if classify(src, a)[0] == "CODE-SYMBOL"]
    return _judge(text, need, required_marker)


def _judge(text, need, required_marker):
    stripped = strip_fences(text)
    mline = marker_line(text)
    missing = [a for a in need if not has_anchor(stripped, a)]
    if required_marker and mline is None:
        return {"pass": False, "reason": "marker_missing", "missing": missing,
                "required": need}
    if missing:
        return {"pass": False, "reason": "missing_anchor:%s" % missing[0],
                "missing": missing, "required": need}
    if mline is None or not any(has_anchor(mline, a) for a in need):
        return {"pass": False, "reason": "marker_lacks_anchor", "missing": [],
                "required": need}
    return {"pass": True, "reason": "ok", "missing": [], "required": need}


# ------------------------------------------------------------------ task 4
def task4():
    """Count arm-checks rejected SOLELY on a PROSE-CONNECTOR anchor."""
    out = []
    for g in GRIDS:
        p = os.path.join(ROOT, "experiments/ptr-engine", g)
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        checks = total = flips = 0
        keys = []
        for arm, a in (d.get("arms") or {}).items():
            for c in a.get("checks") or []:
                if c.get("kind") not in (None, "checkpoint", "fact"):
                    continue
                if c.get("pass") is None:
                    continue
                total += 1
                reason = str(c.get("reason") or "")
                detail = str(c.get("detail") or "")
                miss = []
                if reason.startswith("missing_anchor:"):
                    miss = [reason.split(":", 1)[1]]
                elif reason in ("refused_while_knowable", "value_not_in_concluding_position"):
                    m = re.search(r"missing (?:%d/%d anchors: )?([a-z_, ]+)$" % (1, 1), detail)
                    if m:
                        miss = [x.strip() for x in m.group(1).split(",") if x.strip()]
                if miss and all(_is_prose(m) for m in miss):
                    flips += 1
                    keys.append("%s:%s(%s)" % (os.path.basename(g), arm, ",".join(miss)))
                checks += 1
        out.append({"grid": os.path.basename(g), "arm_checks": total,
                    "prose_only_flips": flips, "keys": keys})
    return out


_PROSE = {}


def _is_prose(token):
    if token in _PROSE:
        return _PROSE[token]
    for fx in FIXTURES:
        d = json.load(open(os.path.join(ROOT, fx)))
        for cp in d.get("checkpoints") or []:
            exp = str(cp.get("expected", cp.get("answer", "")))
            if token in anchors(exp):
                _PROSE[token] = classify(cp.get("source", ""), token)[0] == "PROSE-CONNECTOR"
                return _PROSE[token]
    _PROSE[token] = False
    return False


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print-table", action="store_true")
    args = ap.parse_args()

    rows = census()
    if args.print_table:
        print("| checkpoint id | anchor token | class | evidence (file:line or absent) |")
        print("|---|---|---|---|")
        for cid, tok, cls, ev in rows:
            print("| %s | %s | %s | %s |" % (cid, tok, cls, ev))
        return 0

    fails = []

    # ---- task 1: recompute vs recorded
    rec = recorded_census()
    print("== TASK 1 census: %d cells recomputed" % len(rows))
    if rec is None:
        fails.append("ANCHOR-PREREG.md has no <!-- census:begin --> table")
        print("   RECORDED TABLE: MISSING")
    else:
        a = [(r[0], r[1], r[2]) for r in rows]
        b = [(r[0], r[1], r[2]) for r in rec]
        if a != b:
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else None
                y = b[i] if i < len(b) else None
                if x != y:
                    fails.append("census cell %d: computed %r recorded %r" % (i, x, y))
            print("   CENSUS MISMATCH")
        else:
            empty = [r for r in rec if not r[3] or r[3].startswith("absent") and "PROSE" not in r[2]]
            if empty:
                fails.append("recorded rows without evidence: %r" % (empty,))
            print("   CENSUS MATCHES recorded table (%d rows, %d CODE-SYMBOL, %d NUMBER, %d PROSE-CONNECTOR)"
                  % (len(rows), sum(1 for r in rows if r[2] == "CODE-SYMBOL"),
                     sum(1 for r in rows if r[2] == "NUMBER"),
                     sum(1 for r in rows if r[2] == "PROSE-CONNECTOR")))
    for r in rows:
        print("   %-10s %-11s %-16s %s" % r)

    # ---- task 3: two-sided probe
    exp = "ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), before re-raising"
    rows_v6 = [json.loads(l) for l in open(os.path.join(ROOT, V6_ROWS))]
    t46 = [r for r in rows_v6 if r.get("turn") == 46 and (r.get("content") or "").strip()]
    if not t46:
        fails.append("no non-empty turn-46 row in %s" % V6_ROWS)
        good = ""
    else:
        good = t46[0]["content"]
    print("\n== TASK 3 probe A (correct paraphrase, V6 cp.2.t46, shorthash %s)"
          % hashlib.sha256(good.encode()).hexdigest()[:12])
    r1 = judge_R1(good, exp)
    r2 = judge_R2(good, exp)
    print("   R1 -> pass=%s reason=%s missing=%s" % (r1["pass"], r1["reason"], r1["missing"]))
    print("   R2 -> pass=%s reason=%s missing=%s (required=%s)" % (
        r2["pass"], r2["reason"], r2["missing"], r2["required"]))
    if r1["pass"] or not r2["pass"]:
        fails.append("probe A: R1 reject / R2 accept NOT satisfied (R1=%s R2=%s)"
                     % (r1["pass"], r2["pass"]))

    wrong = good.replace("record_refusal", "write_audit")
    print("\n== TASK 3 probe B (plausible wrong answer: ledger.write_audit(...))")
    w1 = judge_R1(wrong, exp)
    w2 = judge_R2(wrong, exp)
    print("   R1 -> pass=%s reason=%s missing=%s" % (w1["pass"], w1["reason"], w1["missing"]))
    print("   R2 -> pass=%s reason=%s missing=%s" % (w2["pass"], w2["reason"], w2["missing"]))
    if w2["pass"]:
        fails.append("probe B: wrong answer ACCEPTED under R2 - R2 is a blanket pass")
    if not w2["missing"]:
        fails.append("probe B: wrong answer rejected for the wrong reason (no missing anchor)")

    wrong2 = good.replace("scope", "grant")
    print("\n== TASK 3 probe C (wrong kwarg variant: scope=... replaced by grant=...)")
    w3 = judge_R2(wrong2, exp)
    print("   R2 -> pass=%s reason=%s missing=%s" % (w3["pass"], w3["reason"], w3["missing"]))
    if w3["pass"]:
        fails.append("probe C: wrong kwarg ACCEPTED under R2")

    # ---- task 4 counts
    print("\n== TASK 4 prose-only rejections (would flip under R2; no re-grade)")
    t4 = task4()
    tot_f = sum(x["prose_only_flips"] for x in t4)
    tot_m = sum(x["arm_checks"] for x in t4)
    for x in t4:
        print("   %-46s flip<=%d of %d  %s" % (x["grid"], x["prose_only_flips"],
                                               x["arm_checks"], ",".join(x["keys"])))
    print("   TOTAL: would flip <=%d of %d checkpoint arm-checks" % (tot_f, tot_m))

    print("\n== RESULT: %s" % ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("   - %s" % f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
