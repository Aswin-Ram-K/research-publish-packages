#!/usr/bin/env python3
"""PROSE-VALUE-METRIC: read an asserted answer out of a turn's text, prose or contract.

OFFLINE. Zero inference requests, zero network, no grid re-run, no edit to any
grade document, fixture, grader or PARM-1 file. Reads rows files and grade
documents for reading only.

WHY THIS EXISTS
---------------
`grade_v5` reads one channel: the `^ANSWER:` contract line. Every turn that
states an answer in prose is filed `prose_only` -> `never_answered`, so
`checkpoint_accuracy` is a *format-compliance* number wherever the model wrote
prose instead of the marker. `NEVER-ANSWERED-ROOT` proved the size of that in
this corpus: 4 of the 63 never-answered cells state a value (3 wrong, 1 right),
plus 1 `cap_hit` cell that states a wrong value -- 5 stated answers, 4 wrong,
1 right, 0 of 63 ever containing the true `64`.

`asserted_value(text)` is the widened, deliberately conservative extractor. It
returns `(value, form, span)` for an asserted answer -- in a contract line OR in
prose -- and `None` when the text asserts no value. Its output is a SECOND
metric (`asserted_value_accuracy`), never a replacement for
`checkpoint_accuracy`: no frozen number is recomputed or overwritten here.

FORMS (`tuples[1]`), highest precedence first
---------------------------------------------
answer_num      `^ANSWER: NUM 64`            (the frozen grader's own channel)
answer_call     `^ANSWER: CALL f(a=b)`       (the frozen grader's own channel)
answer_bare     `^ANSWER: 64`                (marker, no tag)
is              `the budget is 64` / `is set to 64` / `is exactly `64``
equals          `= 64` / `equals 64` / `equal to 64`
default_of      `the default of 64` / `defaults to 64` / `default is 64`
leading_line    the first non-blank line is a bare numeral: `7` (then "Evidence: ...")
leading_bare    the whole turn is a numeral: `2000`
trailing_bare   a bare integer ending the last prose line: `... total: 64`
backtick        an integer in backticks, in an asserting sentence: `` `64` ``
calls           prose names a qualified callee: `_refuse calls `ledger.record_refusal``
prose_call      the whole turn is one call expression: `ledger.record_refusal(scope=...)`

REJECTION RULES (each one is a rule the grader_v4 era got wrong)
----------------------------------------------------------------
R1 code citation      a numeral inside `resolve.py:39`, `#L39`, `L39`, `lines 15-142`
                      is a location, never an answer (grade_v4 read `#L39` as 39).
R2 range endpoint     a numeral adjacent to `-`, an en/em dash or `to`/`through`
                      is one end of a span (`15-142`, `L15–L142`).
R3 unit suffix        a numeral followed by a size/unit (`1680 B`, `200 bytes`,
                      `4096 tokens`, `128 chars`, `12 ms`, `3%`) is a measurement.
R4 identifier glue    a numeral touching `[A-Za-z_.@]` is part of a version, a
                      hash, a path component or an identifier (`v5`, `p95`, `2.1`).
R5 count-of-other     the low-precedence forms (`backtick`, `trailing_bare`) are
                      accepted only when the sentence also carries a value cue
                      (`is`/`=`/`equals`/`default`/`:`); without one, `passes four
                      arguments` and `seven distinct Ptr* error classes` are
                      counts of something else, not the answer.
R6 non-prose zone     anything inside `<tool_call>...</tool_call>`, a fenced code
                      block, or a `@knowledge:...@N` pointer handle is markup or
                      retrieved code, not the model's assertion (grade_v4 read
                      `64` out of a pasted `resolve()` body). These zones are
                      masked with spaces before matching, so no `ANSWER:` line
                      and no citation can be smuggled in from a code block.
R7 non-integer prose  prose forms accept integers only; a decimal (`0.9` PPL,
                      `2.1`) is a score, not a checkpoint answer. Contract lines
                      are exempt because the grader itself accepted them.
R8 unqualified call   the `calls` form needs a QUALIFIED name (`obj.method`). A bare
                      identifier is usually a tool or a local (`read_file`, `_refuse`),
                      and "I'll call read_file" is a plan, not an answer.

All numerals are matched with named groups (`(?P<num>...)`) so the span can be
quoted verbatim, and the span always indexes the ORIGINAL text.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
OUT = os.path.join(MEASURE, "PROSE-VALUE-METRIC.json")

T3_BOUNDARY = "2026-10-26T15:56"
POPULATION_RULE = ("grade_v5 documents generated at/after 2026-10-26T15:56Z, "
                   "rows-longrun-*.jsonl grids only")

NUM = r"-?\d+(?:\.\d+)?"
INT = r"-?\d+"

# --- zone masks (R6) ------------------------------------------------------
# Linear scanners, not regexes: `grid policy / arm transcript-grow` emits
# `<tool_call>open` every ~25 chars for 85,100 chars (~3400 opens), and a
# non-greedy DOTALL regex to `(?:</tool_call>|$)` rescans to EOF at every open --
# O(n^2) and it did not finish in 60 s. The scanners below are O(n).
POINTER = re.compile(r"@knowledge:[^@\s]+@\d+")
TOOL_OPEN, TOOL_CLOSE, FENCE_MARK = "<tool_call>", "</tool_call>", "```"


def _mask_blocks(text, opener, closer):
    """Mask every `opener ... closer` (or opener..EOF when unterminated)."""
    out, i = [], 0
    while True:
        j = text.find(opener, i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        k = text.find(closer, j + len(opener))
        end = len(text) if k < 0 else k + len(closer)
        out.append(" " * (end - j))
        i = end
    return "".join(out)

# --- citation / unit / glue masks (R1-R4) --------------------------------
CITE = re.compile(r"[A-Za-z0-9_./-]*\.(?:py|json|jsonl|md|txt|sh|yaml|yml|toml|js|ts)"
                  r":\d+(?:-\d+)?")
HASH_LINE = re.compile(r"#?L\d+(?:\s*[-\u2013\u2014]\s*L?\d+)?")
LINE_WORD = re.compile(r"\blines?\s+\d+(?:\s*[-\u2013\u2014]\s*\d+)?", re.I)
UNIT_WORD = r"(?:B|bytes?|KiB|MiB|GiB|KB|MB|GB|tokens?|chars?|characters?|ms|us|seconds?|%)"
# scan form: anchored right after a numeral, so `\s*` costs one attempt only
UNIT_SUFFIX = re.compile(r"\s*" + UNIT_WORD + r"(?![\w])", re.I)
# mask form: numeral AND unit in one anchored pass. Masking with a LEADING `\s*`
# over the whole text is O(n^2) on a whitespace-heavy zone -- the tool-spam turn
# is 85,100 chars of mostly masked spaces, and it never finished.
UNIT_PAIR = re.compile(r"(?P<num>-?\d+(?:\.\d+)?)(?P<unit>\s*" + UNIT_WORD +
                       r"(?![\w]))", re.I)
RANGE_GLUE = re.compile(r"(?:[-\u2013\u2014]|\bto\b|\bthrough\b|\buntil\b)\s*$", re.I)
RANGE_HEAD = re.compile(r"\s*(?:[-\u2013\u2014]|\bto\b|\bthrough\b)", re.I)
IDENT_LEFT = re.compile(r"[A-Za-z_.@]$")
IDENT_RIGHT = re.compile(r"^[A-Za-z_@]")

# --- contract channel -----------------------------------------------------
ANSWER_LINE = re.compile(
    r"^ANSWER:[ \t]*(?:(?P<tag>NUM|NUMBER|INT|INTEGER|CALL|CALLS)[ \t]+)?"
    r"(?P<val>[^\n]*\S)[ \t]*$", re.M)
CALL_FORM = re.compile(r"^(?P<callee>[A-Za-z_][\w.]*)\s*\((?P<args>.*)\)\s*$", re.S)

# --- prose cue channel (named groups on every numeral) -------------------
NUMG = r"(?P<num>" + NUM + r")"
# bold / italic / backtick emphasis around a value is formatting, not content:
# `is **1 ref**` must read as 1, which is how grade_v4 read it.
OPEN = r"(?:\*\*|__|`|\*)?"
CLOSE = r"(?:\*\*|__|`|\*)?"
NUME = OPEN + NUMG + CLOSE
CUE_PATTERNS = [
    # `the default of 64`, `defaults to 64`, `default is 64`
    ("default_of", re.compile(r"\bdefaults?\b[^.;\n]{0,40}?\b(?:of|to|is|=)\s*" + NUME,
                              re.I)),
    # `is 64`, `is set to 64`, `is exactly **64**`
    ("is", re.compile(r"\bis\s+(?:(?:set|equal|exactly|now|still)\s+(?:to\s+)?)?" + NUME,
                      re.I)),
    # `= 64`
    ("equals", re.compile(r"=\s*" + NUME)),
    # `equals 64`, `equal to 64`
    ("equals", re.compile(r"\bequals?\s+(?:to\s+)?`?" + NUMG, re.I)),
]
# R8: a prose callee must be qualified -- bare identifiers are tools or locals.
CALLS = re.compile(r"\bcalls?\s+(?:the\s+)?`?(?P<callee>[A-Za-z_]\w*\.[A-Za-z_]\w*)`?")
CALL_LINE = re.compile(r"^\s*(?P<callee>[A-Za-z_]\w*\.[A-Za-z_]\w*)\s*\((?P<args>[^()]*)\)\s*$")
LEADING_LINE = re.compile(r"\A\s*(?P<num>" + INT + r")\s*$", re.M)
BACKTICK = re.compile(r"`(?P<num>" + INT + r")`")
TRAILING = re.compile(r"(?P<num>" + INT + r")\s*[.)]?\s*$")
LEADING = re.compile(r"^\s*(?P<num>" + NUM + r")\s*$")
CUE_WORD = re.compile(r"(\bis\b|\bare\b|=|\bequals?\b|\bdefaults?\b|\bdefault\b|"
                      r"\byields?\b|\bgives?\b|:)", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def sentences(zone):
    """Yield `(start, end)` spans of sentences -- offsets stay global."""
    pos = 0
    for m in SENT_SPLIT.finditer(zone):
        if m.start() > pos:
            yield (pos, m.start())
        pos = m.end()
    if pos < len(zone):
        yield (pos, len(zone))


def mask(text, patterns):
    """Replace each match with spaces, preserving length and every offset."""
    for rx in patterns:
        text = rx.sub(lambda m: " " * (m.end() - m.start()), text)
    return text


def prose_zone(text):
    """R6: mask tool calls, fenced code and pointer handles."""
    z = _mask_blocks(text, TOOL_OPEN, TOOL_CLOSE)
    z = _mask_blocks(z, FENCE_MARK, FENCE_MARK)
    return POINTER.sub(lambda m: " " * (m.end() - m.start()), z)


def masked_for_numerals(text):
    """R1-R4: mask citations, line references, unit suffixes and identifier glue.

    Only the *rejectable* spans are masked; the numerals they carry can then not
    be matched at all, which is the conservative direction (a missed value
    becomes `no_value`, never a fabricated match).
    """
    z = mask(text, (CITE, HASH_LINE, LINE_WORD))
    z = UNIT_PAIR.sub(lambda m: " " * (m.end() - m.start()), z)
    return z


def rejects(zone, start, end, sentence=None, cue_forms_ok=False):
    """Return the rejection rule id for a candidate span, or '' if accepted."""
    left = zone[max(0, start - 6):start]
    right = zone[end:end + 12]
    if IDENT_LEFT.search(left) or IDENT_RIGHT.search(right):
        return "R4_identifier_glue"
    if RANGE_GLUE.search(left) or RANGE_HEAD.match(right):
        return "R2_range_endpoint"
    if UNIT_SUFFIX.match(right):
        return "R3_unit_suffix"
    body = zone[start:end]
    if "." in body:
        return "R7_non_integer_prose"
    if not cue_forms_ok:
        if sentence is None or not CUE_WORD.search(sentence):
            return "R5_count_of_other"
    return ""


def _accept(zone, sentence, m, form, cue_forms_ok=True, base=0):
    """`(value, form, (start,end))` in GLOBAL offsets, or `(None, rule)`."""
    start, end = base + m.start("num"), base + m.end("num")
    rule = rejects(zone, start, end, sentence, cue_forms_ok)
    if rule:
        return None, rule
    return (m.group("num"), form, (start, end)), ""


def asserted_value(text):
    """Return `(value, form, span)` for an asserted answer, or `None`.

    Contract line first (the frozen grader's channel), then prose cues in
    document order, then the two low-precedence sentence forms. Ties are broken
    by precedence, never by preference for a "nicer" answer.
    """
    if not text or not str(text).strip():
        return None
    text = str(text)

    # 1. contract channel -- evaluated on the RAW text: a marker inside a code
    #    block is a code sample, so the search runs on the masked zone instead.
    raw_zone = prose_zone(text)
    for m in ANSWER_LINE.finditer(raw_zone):
        val = m.group("val").strip()
        tag = (m.group("tag") or "").upper()
        cm = CALL_FORM.match(val)
        if tag in ("CALL", "CALLS") or (cm and not re.fullmatch(NUM, val)):
            if cm:
                return (cm.group("callee"), "answer_call",
                        (m.start("val"), m.start("val") + len(cm.group("callee"))))
        num = re.fullmatch(NUM, val.strip("` "))
        if num:
            form = "answer_num" if tag in ("NUM", "NUMBER", "INT", "INTEGER") else "answer_bare"
            s = raw_zone.find(num.group(0), m.start("val"))
            return (num.group(0), form, (s, s + len(num.group(0))))

    zone = masked_for_numerals(raw_zone)
    stripped = zone.strip()

    # 2a. the whole turn is a numeral (`2000`) -- checked before any line rule
    m = re.fullmatch(NUM, stripped)
    if m:
        s0 = zone.find(stripped)
        return (stripped, "leading_bare", (s0, s0 + len(stripped)))

    # 2b. the first non-blank line is a bare numeral (`7\n\nEvidence: ...`)
    first = next((ln.strip() for ln in raw_zone.splitlines() if ln.strip()), "")
    m = re.fullmatch(INT, first)
    if m:
        s = raw_zone.find(first)
        return (first, "leading_line", (s, s + len(first)))

    # 3. the whole turn is one call expression (`ledger.record_refusal(...)`)
    m = CALL_LINE.match(zone)
    if m:
        return (m.group(0).strip(), "prose_call", (m.start("callee"), m.end("callee")))

    # 4. prose cue channel, in document order over sentence boundaries
    for s0, s1 in list(sentences(zone)):
        sentence = zone[s0:s1]
        if not sentence.strip():
            continue
        cm = CALLS.search(sentence)
        for form, rx in CUE_PATTERNS:
            m = rx.search(sentence)
            if not m:
                continue
            if cm and cm.start() < m.start():
                return (cm.group("callee"), "calls", (s0 + cm.start("callee"),
                                                      s0 + cm.end("callee")))
            got, _rule = _accept(zone, sentence, m, form, base=s0)
            if got:
                return (got[0], form, got[2])
        if cm:
            return (cm.group("callee"), "calls", (s0 + cm.start("callee"),
                                                  s0 + cm.end("callee")))
        # backtick integer inside an asserting sentence
        cue = CUE_WORD.search(sentence)
        for m in BACKTICK.finditer(sentence):
            got, _rule = _accept(zone, sentence, m, "backtick",
                                 cue_forms_ok=bool(cue), base=s0)
            if got:
                return (got[0], "backtick", got[2])
        # a sentence that ends on a bare integer
        m = TRAILING.search(sentence.rstrip())
        if m:
            got, _rule = _accept(zone, sentence, m, "trailing_bare",
                                 cue_forms_ok=bool(cue), base=s0)
            if got:
                return (got[0], "trailing_bare", got[2])

    # 3. the whole turn is a bare numeral (the `c/lease-reopen/cp.0.t12` shape)
    m = LEADING.match(zone)
    if m:
        return (m.group("num"), "leading_bare", (m.start("num"), m.end("num")))
    return None


def explain(text):
    """Every candidate the extractor saw and why it was rejected (tests/audit)."""
    out = []
    if not text:
        return out
    zone = masked_for_numerals(prose_zone(str(text)))
    for s0, s1 in sentences(zone):
        sentence = zone[s0:s1]
        for form, rx in CUE_PATTERNS:
            for m in rx.finditer(sentence):
                rule = rejects(zone, m.start("num"), m.end("num"), sentence, True)
                out.append({"form": form, "text": m.group("num"), "rule": rule})
        for m in BACKTICK.finditer(sentence):
            rule = rejects(zone, m.start("num"), m.end("num"), sentence,
                           bool(CUE_WORD.search(sentence)))
            out.append({"form": "backtick", "text": m.group("num"), "rule": rule})
    return out


# ---------------------------------------------------------------------------
# measure: recompute the 66-cell population as a SECOND column
# ---------------------------------------------------------------------------
def load_rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def rows_path_for(doc):
    rel = doc.get("rows_file") or ""
    for cand in (os.path.join(ROOT, rel), os.path.join(MEASURE, os.path.basename(rel)),
                 os.path.join(ROOT, "experiments", "ptr-engine", rel)):
        if os.path.isfile(cand):
            return cand
    return None


def sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def compare(value, form, kind, expected):
    """match / mismatch / no_value, against the frozen checkpoint truth."""
    if value is None:
        return "no_value"
    kind = (kind or "").upper()
    if kind == "CALL":
        callee = (expected or {}).get("callee") if isinstance(expected, dict) else None
        if not callee:
            return "no_value"
        return "match" if callee in str(value) else "mismatch"
    try:
        exp = float(expected)
    except (TypeError, ValueError):
        return "no_value"
    try:
        return "match" if abs(float(value) - exp) < 1e-9 else "mismatch"
    except (TypeError, ValueError):
        return "mismatch"


def cell_text(rows, arm, turn):
    """`per_turn[-1]` -- the same last-row-wins rule grade_v5.grade_rows uses."""
    per = [r for r in rows if r.get("arm") == arm and int(r.get("turn", -1)) == turn]
    if not per:
        return None
    return per[-1].get("content") or ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=OUT)
    args = ap.parse_args(argv)

    docs = sorted(glob.glob(os.path.join(MEASURE, "cell-longrun-*20261026T1556Z.grade-v5.json")))
    documents, cells = OrderedDict(), []
    for path in docs:
        doc = json.load(open(path, encoding="utf-8"))
        if str(doc.get("generated_at") or "") < T3_BOUNDARY:
            continue
        rp = rows_path_for(doc)
        if not rp or "rows-longrun-" not in os.path.basename(rp):
            continue
        rows = load_rows(rp)
        base = os.path.basename(path)
        documents[base] = OrderedDict([
            ("grid", os.path.basename(rp)),
            ("rows_file", os.path.relpath(rp, ROOT)),
            ("doc_sha256", sha256_of(path)),
            ("rows_sha256", sha256_of(rp)),
            ("grader", doc.get("grader")),
            ("generated_at", doc.get("generated_at")),
            ("fixture_version", doc.get("fixture_version")),
            ("n_cells", len(doc.get("cells") or [])),
        ])
        truth = {t.get("id"): t for t in doc.get("truth") or []}
        for cell in doc.get("cells") or []:
            cid, arm = cell.get("id"), cell.get("arm")
            text = cell_text(rows, arm, int(cell.get("turn", -1)))
            got = asserted_value(text)
            t = truth.get(cid) or {}
            expected = t.get("expected", cell.get("expected"))
            kind = t.get("kind", cell.get("expected_kind"))
            value, form, span = got if got else (None, None, None)
            verdict = compare(value, form, kind, expected)
            quote = ""
            if got and text:
                s, e = span
                quote = text[max(0, s - 60):min(len(text), e + 60)]
            cells.append(OrderedDict([
                ("grid", os.path.basename(rp)),
                ("arm", arm),
                ("checkpoint", cid),
                ("turn", cell.get("turn")),
                ("source", base),
                ("source_sha256", sha256_of(path)),
                ("rows_sha256", sha256_of(rp)),
                ("truth_source_sha256", t.get("source_sha256")),
                ("frozen_verdict", cell.get("verdict")),
                ("frozen_reason", cell.get("reason")),
                ("frozen_pass", cell.get("verdict") == "pass"),
                ("checkpoint_kind", kind),
                ("checkpoint_truth", expected),
                ("text_chars", len(text or "")),
                ("asserted_value", value),
                ("asserted_form", form),
                ("asserted_span", list(span) if span else None),
                ("asserted_quote", quote),
                ("asserted_verdict", verdict),
            ]))

    def tally(rows_sub):
        c = Counter()
        for r in rows_sub:
            c["cells"] += 1
            c["frozen_pass"] += 1 if r["frozen_pass"] else 0
            c["widened_match"] += 1 if r["asserted_verdict"] == "match" else 0
            c["widened_mismatch"] += 1 if r["asserted_verdict"] == "mismatch" else 0
            c["no_value"] += 1 if r["asserted_verdict"] == "no_value" else 0
            if (not r["frozen_pass"]) and r["asserted_verdict"] != "no_value":
                c["frozen_nonpass_asserts"] += 1
                if r["asserted_verdict"] == "mismatch":
                    c["frozen_nonpass_wrong"] += 1
                else:
                    c["frozen_nonpass_right"] += 1
        return c

    non = [r for r in cells if not r["frozen_pass"]]
    overall = tally(cells)
    per_arm = OrderedDict()
    for arm in sorted({r["arm"] for r in cells}):
        per_arm[arm] = OrderedDict((k, v) for k, v in
                                  sorted(tally([r for r in cells if r["arm"] == arm]).items()))
    per_grid = OrderedDict()
    for g in sorted({r["grid"] for r in cells}):
        per_grid[g] = OrderedDict((k, v) for k, v in
                                  sorted(tally([r for r in cells if r["grid"] == g]).items()))

    changed = [r for r in non if r["asserted_verdict"] != "no_value"]
    doc = OrderedDict([
        ("unit", "PROSE-VALUE-METRIC"),
        ("live_requests", 0),
        ("network", False),
        ("population", OrderedDict([
            ("rule", POPULATION_RULE),
            ("n_cells", len(cells)),
            ("n_frozen_pass", overall["frozen_pass"]),
            ("n_frozen_non_pass", len(non)),
            ("n_documents", len(documents)),
            ("documents", documents),
        ])),
        ("metric", "asserted_value -- read from the turn text, prose or contract line"),
        ("note", ("second column only: checkpoint_accuracy is NOT recomputed or "
                  "overwritten; frozen_verdict is copied verbatim from the grade document")),
        ("overall", OrderedDict((k, v) for k, v in sorted(overall.items()))),
        ("per_arm", per_arm),
        ("per_grid", per_grid),
        ("cells", cells),
        ("delta", OrderedDict([
            ("of_frozen_non_passes", len(non)),
            ("assert_a_value", len(changed)),
            ("wrong", overall["frozen_nonpass_wrong"]),
            ("right", overall["frozen_nonpass_right"]),
            ("changed_cells", [OrderedDict([("grid", r["grid"]), ("arm", r["arm"]),
                                            ("checkpoint", r["checkpoint"]),
                                            ("asserted_value", r["asserted_value"]),
                                            ("asserted_form", r["asserted_form"]),
                                            ("asserted_verdict", r["asserted_verdict"]),
                                            ("frozen_reason", r["frozen_reason"]),
                                            ("text_chars", r["text_chars"]),
                                            ("asserted_quote", r["asserted_quote"])])
                               for r in changed]),
        ])),
    ])
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(json.dumps({"cells": len(cells), "frozen_pass": overall["frozen_pass"],
                      "non_pass": len(non), "asserts": len(changed),
                      "wrong": overall["frozen_nonpass_wrong"],
                      "right": overall["frozen_nonpass_right"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
