#!/usr/bin/env python3
"""grade_v5.py - the ANSWER CONTRACT (v5): a checkpoint answer is a typed value.

WHY THIS EXISTS (docs/HARNESS-MAP.md §3; measure/GRADER-FITNESS.md): grade_v3 and
grade_v4 grade PROSE. Their tokens are anchors, their numerals are candidates, and
the instrument therefore scores FN 30.8 % / FP 45.5 % (v3) and 26.9 % / 50.0 % (v4)
on the same answers. `docs/EXTERNAL-EVAL-PRACTICE.md` §2 states the field's rule:
an established suite grades an EFFECT (a test, a typed value, a DB state), never
prose tokens. v5 is our effect: a forced single line, parsed into a VALUE, compared
to truth DERIVED FROM THE SOURCE (AST).

THE CONTRACT (one line, exact; the fixture carries it verbatim in system_prompt):
    ANSWER: NUM <integer>
    ANSWER: CALL <callee>(<kw>=<value>, <kw>=<value>, ...)   # kwargs alphabetical
    ANSWER: NONE
    ANSWER: TEXT <one line of prose>                          # never auto-passed

A bare numeral that the line PRESENTS as its answer (`ANSWER: 64 (resolve.py:39)`)
is also NUM: the citation is not the value. The citation rule is NOT re-implemented
here - `det_verify.asserted_number` / `det_verify.citation_spans` are imported and
called (the card forbids a weaker second rule).

TRUTH IS NOT STORED IN THE FIXTURE. Each checkpoint declares an `answer_spec`
naming an AST derivation (`constant_value`, `count_classes`, `call_inside_function`
- all canonical implementations in `experiments/ptr-engine/tools/det_verify.py`).
The fixture's human `expected` string is kept as DOCUMENTATION and is cross-checked
against the derivation: a divergence aborts the grading run (fixture_truth_mismatch)
instead of silently grading against stale prose.

PER-CELL OUTPUT carries exactly what the card requires: `verdict`, `reason`,
`asserted`, `expected`, `derivation` (file:line + AST node), plus the raw contract
line and the parse error.

    python3 experiments/ptr-engine/longrun/grade_v5.py \
        --rows R.jsonl --fixture .../LR-01.v5.json --out O.grade-v5.json

Offline. Stdlib only. Reads rows + the pinned source tree; writes only --out.
"""
import argparse
import ast
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
for _p in (HERE, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import det_verify as dv          # canonical citation rule + AST truth helpers
import grader_identity as gi     # the ONE sha256 implementation (writer + reader)

RULE = "ANSWER-CONTRACT v1 (forced one-line answer, value graded against AST truth)"
# abstention: an arm that reports a missing fact and does not fabricate is scoreable as a correct abstention;
# retrieval_miss is scored per row using RETRIEVAL_OUTCOMES above (abstain path).

# The grader's own version. Together with the two shas stamped below it makes every
# document this writer emits self-dating: a later reader never has to re-derive an
# era (orchestration/handoffs/QUALITY-ERA-TABLE.json: 11 of 11 stored grade files
# recorded no grader sha, so era was datable only by re-running the grader).
GRADER_VERSION = "5.1"

# Retrieval-outcome vocabulary (shared with score_longrun / ptr_engine.outcomes).
OK = "OK"
NOT_FOUND = "NOT_FOUND"
STALE_OR_REVOKED = "STALE_OR_REVOKED"
SCOPE_UNGRANTED = "SCOPE_UNGRANTED"
RETRIEVAL_OUTCOMES = (OK, NOT_FOUND, STALE_OR_REVOKED, SCOPE_UNGRANTED)
MISS_OUTCOMES = (NOT_FOUND, STALE_OR_REVOKED, SCOPE_UNGRANTED)


def retrieval_miss(outcomes):
    """Boolean: did any retrieval outcome miss? (abstention/retrieval scoring)."""
    if not outcomes:
        return False
    return any(str(o) in MISS_OUTCOMES for o in outcomes)


def is_abstention(parsed):
    """True when a parsed answer is an explicit abstention (NONE)."""
    if not isinstance(parsed, dict):
        return False
    return parsed.get("answer_kind") == "NONE"


class StampError(RuntimeError):
    """A document could not be made self-dating -- the writer refuses to write it."""

CALL_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*\((.*)\)\s*$", re.S)
ANSWER_LINE_RE = re.compile(r"^ANSWER:[ \t]*(.*)$")
KWARG_RE = re.compile(r"^([A-Za-z_]\w*)\s*=\s*(.+)$", re.S)
NUM_HEAD_RE = re.compile(r"^\d+\b")

# --- GRADE-V5-REPAIR: the assertion must BE the value it claims -----------------
NON_ANSWER_ERRORS = frozenset({
    # no value was expressed at all -> `undecidable`, never `fail`
    "no_answer_line", "prose_only", "empty_answer", "empty_text", "empty_num",
    "unparseable", "text_call",
})
ROW_FIELD_KEYS = ("answer_kind", "answer_value", "answer_parse_error", "answer_raw")


class RowFieldDisagreement(ValueError):
    """A row's convenience fields contradict its own `content` (a hard error).

    grade_v5 derives every verdict from `content`. The runner ALSO stores its own
    parse (answer_kind/answer_value/...); that copy may never decide a verdict.
    When the two disagree the row is not silently trusted and not silently
    overridden: the conflict is raised here, and inside grade_rows surfaced as a
    `fail` cell naming both sides, so an artefact cannot grade itself.
    """

    def __init__(self, message, row_fields, content_parse):
        ValueError.__init__(self, message)
        self.row_fields = row_fields
        self.content_parse = content_parse


def _integral_numeral(text):
    """(int, None) when `text` asserts an INTEGER, else (None, value_seen).

    Repair T1: `64.99` was truncated to 64 by int() coercion and so PASSED a truth
    of 64 - a wrong answer graded as verified success. Only an exact decimal
    integer is an integer assertion: a fractional part, a radix prefix (`0x40`) or
    a unit suffix (`64px`) is rejected and REPORTED with the numeral that was seen.
    A sentence-final period (`64.`) is punctuation, not a fraction.
    """
    stripped = (text or "").strip()
    m = re.match(r"^(\d+)(.*)$", stripped, re.S)
    if not m:
        return None, stripped[:60]
    digits, tail = m.group(1), m.group(2)
    if re.match(r"^\.\d", tail):
        return None, stripped[:60]                  # 64.99 / 64.0 -> not integral
    if tail[:1].isalnum() or tail[:1] == "_":
        return None, stripped[:60]                  # 0x40 / 64px / 640kg
    return int(digits), None


# --------------------------------------------------------------------------- parse
def _split_top_level(text):
    """Split on commas that are not inside (), [] or a quoted string."""
    parts, cur = [], []
    depth = 0
    quote = None
    esc = False
    for ch in text:
        if quote:
            cur.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            cur.append(ch)
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_call(text):
    """(value, None) for `callee(kw=value, ...)` or (None, reason)."""
    m = CALL_RE.match((text or "").strip())
    if not m:
        return None, "call_not_parsable"
    callee, argtext = m.group(1), m.group(2).strip()
    kwargs, order = {}, []
    if argtext:
        for item in _split_top_level(argtext):
            km = KWARG_RE.match(item)
            if not km:
                return None, "call_arg_not_kwarg:%s" % item[:40]
            name = km.group(1)
            value = " ".join(km.group(2).split())
            if name in kwargs:
                return None, "call_duplicate_kwarg:%s" % name
            kwargs[name] = value
            order.append(name)
    return {"callee": callee,
            "kwargs": dict(sorted(kwargs.items())),
            "kwargs_as_written": order}, None


# ------------------------------------------------------------------ decoration
# Repair T4 (this unit; measure/ERA-B-GRADE-REHEARSAL.json): an arm was punished for
# CITING where it read a value. Three shapes carry the SAME answer value and differ
# only in decoration, and each was a parse error or a fake kwarg:
#   CALL f(...) .                  -> call_not_parsable        (`\.\s*$` in CALL_RE)
#   CALL f(...) (resolve.py:163)   -> call_arg_not_kwarg / kwarg_value_mismatch
#   NONE -- <justification>        -> trailing_after_none
# NUM already tolerated a sentence-final period (`_integral_numeral`: the '.' is
# punctuation, not a fraction), so the SAME punctuation was a pass on one kind and a
# rejection on the other two. The relaxation below is DECORATION-ONLY: it runs once,
# before any kind branch, and only ever REMOVES a suffix while the remainder is still
# a complete answer of the same kind. Every stripped fragment is recorded so a reader
# sees that the grader discarded something. Wrong values in the same shapes still fail
# (tests/test_grade_v5_decoration.py: red cases).
NONE_TAIL_OPENERS = ("\u2014", "-", ";", "(")

# What makes a NONE justification carry a VALUE rather than a reason: a dotted name
# (`ledger.record_refusal`), a callable (`foo(`), a snake_case code token, or any
# numeral. Citations (`resolve.py:163`, `#L39`) are removed first - they are
# provenance, not value - so a NONE that cites its evidence is still a denial.
CODE_TOKEN_RE = re.compile(
    r"(?<![\w.])(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*"      # ledger.record_refusal
    r"|[A-Za-z_]\w*\s*\("                             # record_refusal(
    r"|[A-Za-z]\w*_\w+"                               # snake_case code identifier
    r"|\d")                                           # any numeral asserts a value


def _trailing_balanced_paren(text):
    """(remainder, fragment) when `text` ends in a balanced parenthetical, else None.

    The group must be SEPARATED from what precedes it by whitespace: in `f(a=g(x))`
    the final `)` closes the CALL itself, and stripping from its matching `(` would
    destroy the answer. A parenthetical citation is always `answer (cite)`.
    """
    s = text.rstrip()
    if not s.endswith(")"):
        return None
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        ch = s[i]
        if ch == ")":
            depth += 1
        elif ch == "(":
            depth -= 1
            if depth == 0:
                if i == 0 or not s[i - 1].isspace():
                    return None
                remainder = s[:i].rstrip()
                return (remainder, s[i:]) if remainder else None
    return None


def _trailing_citation(text):
    """(remainder, fragment) when `text` ends in det_verify's citation grammar, else None.

    The grammar is IMPORTED, not re-invented: `dv.citation_spans` owns `<path>:<n>`,
    `#L<n>`, `L<n>`, `N of M` and file-naming parentheticals. Only a span that ends
    the segment, is preceded by whitespace and leaves a non-empty remainder is
    decoration; a segment that IS a citation has no answer in it and is left alone.
    """
    s = text.rstrip()
    for start, end in sorted(dv.citation_spans(s)):
        if end != len(s) or start == 0 or not s[start - 1].isspace():
            continue
        remainder = s[:start].rstrip()
        if remainder:
            return remainder, s[start:]
    return None


def _complete_prefix(body, head):
    """Is `body` still a complete answer of kind `head`? (decoration never re-kinds)"""
    parts = body.split(None, 1)
    if not parts:
        return False
    h = parts[0].upper()
    rest = parts[1].strip() if len(parts) > 1 else ""
    if h != head:
        return False
    if head == "NONE":
        return not rest
    if head == "TEXT":
        return bool(rest)
    if head == "CALL":
        return _parse_call(rest)[1] is None
    if head == "NUM":
        return bool(rest) and dv.asserted_number(rest)[0] is not None
    return dv.asserted_number(body)[0] is not None          # bare leading numeral


def _without_citations(text):
    out = text
    for start, end in sorted(dv.citation_spans(out), reverse=True):
        out = out[:start] + " " + out[end:]
    return out


def _carries_value(fragment):
    """Does a stripped suffix assert something (a name, a call, a number)?"""
    return bool(CODE_TOKEN_RE.search(_without_citations(fragment)))


def _none_tail(text):
    """(payload) when `text` is `NONE <opener> ...` with a listed opener, else None."""
    parts = text.split(None, 1)
    if len(parts) < 2 or parts[0].upper() != "NONE":
        return None
    rest = parts[1]
    if not rest or rest[0] not in NONE_TAIL_OPENERS:
        return None
    payload = rest[1:] if rest[0] in ("\u2014", "-", ";") else rest
    return payload.rstrip().rstrip(")")


def _strip_decoration(body, detail):
    """Rules (a)/(b)/(c): remove a decorated SUFFIX, never the answer. Returns body.

    (a) one trailing sentence-final `.` (not `..`; `?!` never matched), every kind.
    (b) a balanced trailing `(...)` or trailing citation, on a non-NONE kind, and only
        while the remainder is still a complete answer of the SAME kind.
    (c) a NONE justification after `\u2014` / `-` / `;` / `(`, kept as a denial, UNLESS
        its payload carries a value - `NONE - actually ledger.record_refusal` is a
        contradicted denial and must stay `trailing_after_none`.
    """
    stripped = []
    text = (body or "").strip()
    if text.endswith(".") and not text.endswith(".."):
        stripped.append(".")
        text = text[:-1].rstrip()                           # (a)
    head = text.split(None, 1)[0].upper() if text.split() else ""
    if head == "NONE":
        payload = _none_tail(text)
        if payload is not None and not _carries_value(payload):   # (c)
            stripped.append(text.split(None, 1)[1].strip())
            text = "NONE"
    else:
        for _ in range(4):                                  # (b), bounded
            found = _trailing_balanced_paren(text) or _trailing_citation(text)
            if not found:
                break
            remainder, fragment = found
            if not _complete_prefix(remainder, head):
                break
            text = remainder
            stripped.append(fragment.strip())
    detail["decoration_stripped"] = stripped
    if stripped:
        detail["body_after_decoration"] = text
    return text


def parse_answer_contract(text):
    """Parse one model reply into the contracted value. Never grades truth.

    Returns answer_kind / answer_value / answer_raw / answer_parse_error / detail.
    `answer_kind is None` with a parse error is THE failure this contract exists to
    make machine-decidable: the checkpoint then grades `fail/answer_not_contract`.

    Robustness decision (stated, tested): prose BEFORE or AFTER the single ANSWER
    line is tolerated but NEVER read - the contract line is the only evidence. Two
    or more ANSWER lines, an empty body, or a body in none of the four forms is a
    parse error. This keeps a reasoning preamble from destroying an otherwise
    well-formed answer (the 82 % -> 18 % compliance failure is a formatting
    problem, not a knowledge problem) without letting prose become the value.
    """
    out = {"answer_kind": None, "answer_value": None, "answer_raw": None,
           "answer_parse_error": None, "answer_invalid": None,
           "answer_turn": False, "detail": {}}
    text = text or ""
    hits = [ln for ln in text.splitlines() if ANSWER_LINE_RE.match(ln)]
    out["detail"]["answer_line_count"] = len(hits)
    if not hits:
        # Repair T3: an absent answer is not a wrong answer. An empty turn has no
        # value to grade (`no_answer_line`); prose with no contract line at all has
        # nothing the contract may read (`prose_only`). Both are `undecidable`.
        out["answer_parse_error"] = "prose_only" if text.strip() else "no_answer_line"
        return out
    if len(hits) > 1:
        out["answer_raw"] = hits[-1].strip()
        out["answer_parse_error"] = "multiple_answer_lines"
        return out
    out["answer_raw"] = hits[0].strip()
    body = ANSWER_LINE_RE.match(hits[0]).group(1).strip()
    if not body:
        out["answer_parse_error"] = "empty_answer"
        return out

    # Repair T4: decoration-only relaxation (trailing period / trailing citation or
    # parenthetical / a NONE justification), applied ONCE here, before any kind
    # branch. It removes a suffix only; the value, the kind and every verdict rule
    # below are untouched, and `detail["decoration_stripped"]` records what was cut.
    body = _strip_decoration(body, out["detail"])

    # Text-form fetch request (transport variant): an ANSWER: line wrapping a
    # fetch call.  Only when the callee is exactly the fetch tool and the
    # request parses to one or more refs; otherwise it stays ungradeable.
    _tc_refs = []
    if re.search(r"CALL\s*\(?\s*fetch\b", body, re.IGNORECASE):
        for _m in re.finditer(r"fetch\s*\(\s*ref\s*=\s*[\"']?([^\"',)]+)", body, re.IGNORECASE):
            _tc_refs.append(_m.group(1).strip("\"'"))
    if _tc_refs:
        out["answer_kind"] = None
        out["answer_parse_error"] = "text_call"
        out["detail"]["rule"] = "text-form fetch request (transport variant)"
        out["detail"]["refs"] = _tc_refs
        return out

    head = body.split(None, 1)[0].upper()
    rest = body.split(None, 1)[1].strip() if len(body.split(None, 1)) > 1 else ""

    if head == "NONE":
        if rest:
            out["answer_parse_error"] = "trailing_after_none"
            return out
        out["answer_kind"] = "NONE"
        out["detail"]["rule"] = "absence of the derived call"
        return out

    # Out-of-vocabulary kind token: an explicit ungradeable outcome, NOT a refusal.
    known = ("NUM", "CALL", "NONE", "TEXT")
    # Slash-delimited enumerations (e.g. the misread "NUM/CALL/NONE/TEXT"
    # contract) are not a bare numeral citation and must be ungradeable.
    if head not in known and (not NUM_HEAD_RE.match(body) or "/" in body):
        out["answer_kind"] = "OOV"
        out["answer_parse_error"] = "out_of_vocabulary"
        out["answer_raw"] = out["answer_raw"] or ("ANSWER: " + body)
        out["detail"]["offending_token"] = head
        out["detail"]["rule"] = "out-of-vocabulary kind token (not NUM/CALL/NONE/TEXT)"
        return out

    if head == "TEXT":
        if not rest:
            out["answer_parse_error"] = "empty_text"
            return out
        out["answer_kind"] = "TEXT"
        out["answer_value"] = rest
        out["detail"]["rule"] = "structural only; never auto-passed"
        return out

    if head == "CALL":
        value, err = _parse_call(rest)
        if err:
            out["answer_parse_error"] = err
            return out
        out["answer_kind"] = "CALL"
        out["answer_value"] = value
        out["detail"]["rule"] = "callee + kwarg name set + kwarg value text"
        return out

    # NUM: either `NUM <integer>` or a bare leading numeral with an optional citation.
    numeral_text = rest if head == "NUM" else body
    if head == "NUM" and not numeral_text:
        out["answer_parse_error"] = "empty_num"
        return out
    if head != "NUM" and not NUM_HEAD_RE.match(numeral_text):
        # `ANSWER: six` / `ANSWER: sixty-four` / `ANSWER: The default is 64.`
        out["answer_parse_error"] = "unparseable"
        out["detail"]["rejected_body"] = body[:60]
        return out
    # det_verify's rule, imported not re-implemented: citation numerals never win.
    value, detail = dv.asserted_number(numeral_text)
    out["detail"].update(detail)
    out["detail"]["numeral_from"] = numeral_text
    if value is None:
        out["answer_parse_error"] = "unparseable"
        out["detail"]["rejected_body"] = body[:60]
        return out
    exact, seen = _integral_numeral(numeral_text)
    out["answer_kind"] = "NUM"
    out["answer_value"] = exact        # None when the assertion is not integral
    out["detail"]["numeral_asserted"] = value
    if exact is None:
        # A well-formed numeric assertion of a NON-INTEGER value is a decidable
        # WRONG answer (`fail`), not a parse error: the turn did assert a value.
        out["answer_invalid"] = "num_not_integer"
        out["detail"]["rejected_numeral"] = seen
        out["detail"]["rule"] = "integer equality only (repair T1: never rounds)"
        return out
    out["detail"]["rule"] = "det_verify.asserted_number (citations dropped), integer only"
    return out


# --------------------------------------------------------------------------- truth
def _rel(path):
    try:
        return os.path.relpath(path, dv.ROOT)
    except ValueError:                                    # pragma: no cover
        return path


def _source_map(fixture):
    base = os.path.join(dv.ROOT, "experiments", "ptr-engine", "ptr_engine")
    out = {}
    for s in fixture.get("sources") or []:
        path = s.get("path") or ""
        if not path:
            continue
        out[s.get("id") or os.path.basename(path)] = (
            os.path.join(dv.ROOT, path) if os.sep in path or path.startswith("experiments")
            else os.path.join(base, os.path.basename(path)))
    out.setdefault("resolve.py", os.path.join(base, "resolve.py"))
    out.setdefault("errors.py", os.path.join(base, "errors.py"))
    return out


def _documented_call(expected):
    """(callee, {name: value}) from the fixture's human `expected` string."""
    text = str(expected)
    start = text.find("(")
    end = text.rfind(")")
    if start < 0 or end < start:
        raise SystemExit("fixture_truth_mismatch: documented CALL has no argument list: %r"
                         % text)
    callee = text[:start].strip().split()[-1]
    kwargs = {}
    for item in _split_top_level(text[start + 1:end]):
        km = KWARG_RE.match(item)
        if not km:
            raise SystemExit("fixture_truth_mismatch: documented CALL argument %r is not a "
                             "kwarg" % item)
        kwargs[km.group(1)] = " ".join(km.group(2).split())
    return callee, kwargs


def _show(path):
    """Repo-relative display path (accepted specs use either absolute or relative)."""
    return _rel(path) if os.path.isabs(path) else str(path)


def _spec_error(cid, spec, detail, default_file):
    """ONE actionable line: item id, answer_spec kind, and the file to fix.

    An answer_spec this grader cannot derive must never surface as a bare KeyError
    or a context-free SystemExit: the reader needs to know WHICH item, WHICH kind,
    and WHERE the spec (and its cited source) lives.
    """
    derive = spec.get("derive") or {}
    src = derive.get("file") or default_file
    raise SystemExit(
        "fixture_truth_mismatch: item %s: answer_spec kind %r, rule %r: %s "
        "(fix the answer_spec at %s)" % (cid, spec.get("kind"), derive.get("rule"),
                                         detail, _show(src)))


def _attr_calls_in_function(tree, func_name, attr):
    """Every call inside `func_name` whose callee RESOLVES to `attr`.

    "Resolves to the attribute" covers the three shapes the contract names:
      * a direct/aliased bare call  `attr(...)`        -> ast.Name.id == attr
      * `self.attr(...)`, `module.attr(...)`, `ledger.attr(...)`
      * a call reached through any attribute chain ending in `.attr`
    The last two are ONE AST shape (ast.Attribute with .attr == attr), which is how
    both the `self` and the module-attribute spellings appear after parsing.
    Returns None when the named function does not exist (caller reports it).
    """
    funcs = [n for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name]
    if not funcs:
        return None
    hits = []
    for fn in funcs:
        for sub in ast.walk(fn):
            if not isinstance(sub, ast.Call):
                continue
            callee = sub.func
            if isinstance(callee, ast.Attribute) and callee.attr == attr:
                hits.append({"callee": ast.unparse(callee), "lineno": sub.lineno,
                             "unparsed": ast.unparse(sub)})
            elif isinstance(callee, ast.Name) and callee.id == attr:
                hits.append({"callee": callee.id, "lineno": sub.lineno,
                             "unparsed": ast.unparse(sub)})
    hits.sort(key=lambda h: (h["lineno"], h["callee"]))
    return hits


def _calls_at_line(tree, lineno, name=None):
    """Every ast.Call starting on `lineno`, optionally only one whose callee is `name`.

    `name` is matched on the full dotted callee and, failing that, on its last
    component (so a documented `resolved_count()` still binds to
    `ledger.resolved_count()`), but never by substring: `fn()` must not match
    `other_fn()`.
    """
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or node.lineno != lineno:
            continue
        callee = ast.unparse(node.func)
        if name is not None and callee != name and callee.split(".")[-1] != name:
            continue
        hits.append({"callee": callee, "lineno": node.lineno,
                     "unparsed": ast.unparse(node)})
    return hits


def _tree_for(path, cache):
    if path not in cache:
        cache[path] = dv.parse_module(path)
    return cache[path]


def derive_truth(fixture):
    """Per-checkpoint truth, each with the AST derivation that establishes it."""
    paths = _source_map(fixture)
    resolve_path, errors_path = paths["resolve.py"], paths["errors.py"]
    rt, rsha = dv.parse_module(resolve_path)
    et, esha = dv.parse_module(errors_path)
    cache = {resolve_path: (rt, rsha), errors_path: (et, esha)}
    out = []
    for idx, cp in enumerate(fixture.get("checkpoints") or []):
        spec = cp.get("answer_spec") or {}
        kind = spec.get("kind")
        derive = spec.get("derive") or {}
        cid = str(cp.get("id") or ("cp.%d.t%s" % (idx, cp.get("turn"))))
        documented = cp.get("expected")
        cell = {"id": cid, "turn": int(cp.get("turn", -1)), "kind": kind,
                "documented_expected": documented, "elided_kwargs": []}
        try:
            _derive_one(cell, spec, kind, derive, cid, documented, paths, cache)
        except KeyError as exc:                       # never a bare KeyError
            _spec_error(cid, spec, "missing derive key %s" % exc,
                        derive.get("file") or resolve_path)
        shas = {"resolve.py": rsha, "errors.py": esha}
        for p, (_, sha) in sorted(cache.items()):
            base = os.path.basename(p)
            if base not in shas:
                shas[base] = sha
        cell["source_sha256"] = shas
        out.append(cell)
    if not out:
        raise SystemExit("fixture_truth_mismatch: fixture declares no checkpoints")
    return out


def _check_documented_call(cid, spec, documented, value, cell, src_path):
    """The fixture's human `expected` string cross-checks the derived call."""
    documented_callee, documented_kwargs = _documented_call(documented)
    if documented_callee != value["callee"]:
        _spec_error(cid, spec, "documents callee %r, AST says %r"
                    % (documented_callee, value["callee"]), src_path)
    if set(documented_kwargs) != set(value["kwargs"]):
        _spec_error(cid, spec, "documents kwargs %r, AST says %r"
                    % (sorted(documented_kwargs), sorted(value["kwargs"])), src_path)
    # `...` in the documented expected string is a declared elision of a value
    # whose exact source text is not part of the question (scope=... in v4).
    cell["elided_kwargs"] = sorted(k for k, v in documented_kwargs.items() if v == "...")


def _derive_one(cell, spec, kind, derive, cid, documented, paths, cache):
    """Fill `cell` for one checkpoint. Every undeductible spec raises _spec_error."""
    resolve_path, errors_path = paths["resolve.py"], paths["errors.py"]
    rt, _ = _tree_for(resolve_path, cache)
    et, _ = _tree_for(errors_path, cache)

    if kind == "NUM":
        rule = derive.get("rule")
        if rule == "constant_value":
            symbol = derive.get("symbol")
            if not symbol:
                _spec_error(cid, spec, "NUM/constant_value needs 'symbol'", resolve_path)
            src_path = derive.get("file") or resolve_path
            if not os.path.isabs(src_path) and src_path.startswith("experiments"):
                src_path = os.path.join(dv.ROOT, src_path)
            tree, _ = _tree_for(src_path, cache)
            value, lineno = dv.constant_value(tree, symbol)
            cell.update(expected=int(value),
                        derivation={"file": _show(src_path), "line": lineno,
                                    "ast": "ast.Assign", "symbol": symbol,
                                    "text": "%s:%d ast.Assign %s = %r"
                                            % (_show(src_path), lineno,
                                               symbol, value)})
        elif rule == "count_classes":
            pattern = derive.get("pattern")
            if not pattern:
                _spec_error(cid, spec, "NUM/count_classes needs 'pattern'", errors_path)
            names = dv.count_classes(et, pattern)
            lines = [ln for _, ln in names]
            cell.update(expected=len(names),
                        derivation={"file": _rel(errors_path),
                                    "lines": [min(lines), max(lines)],
                                    "ast": "ast.ClassDef", "pattern": pattern,
                                    "count": len(names),
                                    "text": "%s:%d-%d ast.ClassDef count(%s) = %d"
                                            % (_rel(errors_path), min(lines), max(lines),
                                               pattern, len(names))})
            cell["class_names"] = [n for n, _ in names]
        else:
            _spec_error(cid, spec, "no derivation branch for this NUM rule", resolve_path)
        if str(documented).strip() != str(cell["expected"]):
            _spec_error(cid, spec, "documents %r but the AST derives %r"
                        % (documented, cell["expected"]), resolve_path)

    elif kind == "CALL":
        rule = derive.get("rule")
        if rule == "call_inside_function":
            func, attr = derive.get("function"), derive.get("attr")
            if not func or not attr:
                _spec_error(cid, spec,
                            "call_inside_function needs 'function' and 'attr'",
                            resolve_path)
            call = dv.call_inside_function(rt, func, attr)
            src_path = resolve_path
            value, err = _parse_call(call["unparsed"])
            if err:
                _spec_error(cid, spec, "AST call not parsable (%s)" % err, src_path)
            cell.update(expected=value, call_present=True,
                        derivation={"file": _rel(src_path), "line": call["lineno"],
                                    "ast": "ast.Call inside %s" % func,
                                    "callee": call["callee"],
                                    "text": "%s:%d ast.Call inside %s -> %s"
                                            % (_rel(src_path), call["lineno"],
                                               func, call["unparsed"])})
            _check_documented_call(cid, spec, documented, value, cell, src_path)
        elif rule == "call_at_line":
            lineno = derive.get("line")
            if not isinstance(lineno, int):
                _spec_error(cid, spec, "call_at_line needs an integer 'line'",
                            resolve_path)
            src_path = derive.get("file") or resolve_path
            tree, _ = _tree_for(src_path, cache)
            documented_callee = None
            try:
                documented_callee, _ = _documented_call(documented)
            except SystemExit:
                documented_callee = None
            # `callee` may be declared on the spec; otherwise the documented
            # expected string names the call that must occur at that line.
            name = derive.get("callee") or documented_callee
            hits = _calls_at_line(tree, lineno, name)
            if not hits:
                raise SystemExit(
                    "fixture_truth_mismatch: item %s: answer_spec kind 'CALL', rule "
                    "'call_at_line' finds no call named %r at %s:%d; fix the "
                    "answer_spec line or the cited source %s"
                    % (cid, name, _show(src_path), lineno, _show(src_path)))
            call = hits[0]
            value, err = _parse_call(call["unparsed"])
            if err:
                _spec_error(cid, spec, "AST call at %s:%d not parsable (%s)"
                            % (_show(src_path), lineno, err), src_path)
            cell.update(expected=value, call_present=True,
                        derivation={"file": _show(src_path), "line": call["lineno"],
                                    "ast": "ast.Call at line %d" % lineno,
                                    "callee": call["callee"],
                                    "call_sites_at_line": len(hits),
                                    "text": "%s:%d ast.Call (line-pinned) -> %s"
                                            % (_show(src_path), call["lineno"],
                                               call["unparsed"])})
            _check_documented_call(cid, spec, documented, value, cell, src_path)
        else:
            _spec_error(cid, spec, "no derivation branch for this CALL rule", resolve_path)

    elif kind == "NONE":
        rule = derive.get("rule")
        if rule != "no_attr_call_inside_function":
            _spec_error(cid, spec, "no derivation branch for this NONE rule", resolve_path)
        func, attr = derive.get("function"), derive.get("attr")
        if not func or not attr:
            _spec_error(cid, spec,
                        "NONE/no_attr_call_inside_function needs 'function' and 'attr'",
                        resolve_path)
        src_path = derive.get("file") or resolve_path
        tree, _ = _tree_for(src_path, cache)
        hits = _attr_calls_in_function(tree, func, attr)
        if hits is None:
            _spec_error(cid, spec, "function %r not found in the cited source" % func,
                        src_path)
        # THE derived truth is the boolean absence - and when the attribute IS
        # called there, the truth SAYS SO (call_present=True) so the item grades
        # `fail` instead of aborting. The documented string never overrides this.
        cell.update(expected="NONE", call_present=bool(hits),
                    forbidden_attr=attr, forbidden_function=func,
                    derivation={
                        "file": _show(src_path),
                        "line": hits[0]["lineno"] if hits else 0,
                        "ast": "ast.Call *.%s inside %s" % (attr, func),
                        "attr": attr, "function": func,
                        "call_lines": [h["lineno"] for h in hits],
                        "callees": [h["callee"] for h in hits],
                        "text": "%s ast.Call *.%s inside %s -> %s"
                                % (_show(src_path), attr, func,
                                   ("CALLED at %s" % ", ".join(
                                       "%s:L%d" % (h["callee"], h["lineno"]) for h in hits))
                                   if hits else "absent")})
        cell["documented_agrees"] = ((str(documented).strip().upper() == "NONE")
                                     == (not hits))

    elif kind == "TEXT":
        rule = derive.get("rule")
        if rule == "constant_value":
            symbol = derive.get("symbol")
            if not symbol:
                _spec_error(cid, spec, "TEXT/constant_value needs 'symbol'", resolve_path)
            src_path = derive.get("file") or resolve_path
            if not os.path.isabs(src_path) and src_path.startswith("experiments"):
                src_path = os.path.join(dv.ROOT, src_path)
            tree, _ = _tree_for(src_path, cache)
            value, lineno = dv.constant_value(tree, symbol)
            cell.update(expected=value,
                        derivation={"file": _show(src_path), "line": lineno,
                                    "ast": "ast.Assign", "symbol": symbol,
                                    "text": "%s:%d ast.Assign %s = %r"
                                            % (_show(src_path), lineno,
                                               symbol, value)})
        else:
            _spec_error(cid, spec, "no derivation branch for this TEXT rule", resolve_path)
        if str(documented).strip() != str(cell["expected"]).strip():
            _spec_error(cid, spec, "documents %r but the AST derives %r"
                        % (documented, cell["expected"]), resolve_path)

    else:
        _spec_error(cid, spec, "no derivation branch for this answer_spec kind", resolve_path)


# ------------------------------------------------------------------------ grading
def _normalize(text):
    return " ".join(str(text).split())


def grade_cell(truth, parsed):
    """One machine-decidable verdict. No prose heuristics, no token counting."""
    expected = truth["expected"]
    asserted = parsed["answer_value"]
    cell = {"verdict": "fail", "reason": "", "asserted": asserted,
            "expected": expected, "answer_kind": parsed["answer_kind"],
            "answer_raw": parsed["answer_raw"],
            "answer_parse_error": parsed["answer_parse_error"],
            "decoration_stripped": (parsed.get("detail") or {}).get(
                "decoration_stripped") or [],
            "derivation": truth["derivation"]}

    if parsed["answer_kind"] is None:
        err = parsed.get("answer_parse_error") or "unparseable"
        if err in NON_ANSWER_ERRORS:
            # Repair T3: a non-answer is `undecidable`, NOT `fail`. `pass` and
            # `fail` are the only members of the decidable denominator, so an
            # absent answer can no longer inflate it.
            cell["verdict"] = "undecidable"
            cell["reason"] = err
            cell["undecidable"] = True
        else:
            cell["reason"] = "answer_not_contract:%s" % err
        return cell

    kind = parsed["answer_kind"]

    if kind == "OOV":
        cell["verdict"] = "undecidable"
        cell["reason"] = parsed.get("answer_parse_error") or "out_of_vocabulary"
        cell["undecidable"] = True
        cell["ungradeable"] = True
        cell["offending_token"] = (parsed.get("detail") or {}).get(
            "offending_token")
        return cell

    if kind == "TEXT":
        if truth.get("kind") == "TEXT":
            if _normalize(asserted) == _normalize(expected):
                cell["verdict"] = "pass"
                cell["reason"] = "text_equal"
            else:
                cell["verdict"] = "fail"
                cell["reason"] = "text_mismatch"
        else:
            cell["verdict"] = "text"
            cell["reason"] = "text_not_auto_passed"
        return cell

    if kind == "NONE":
        # NONE-truth checkpoint: the derived truth is the boolean ABSENCE of the
        # named attribute call inside the named function. When the source DOES call
        # it there, answering NONE is contradicted by the source -> `fail` with a
        # reason naming the attribute and the call site (never an abort).
        if truth["kind"] == "NONE":
            if truth.get("call_present"):
                d = truth.get("derivation") or {}
                cell["verdict"] = "fail"
                cell["reason"] = ("none_contradicted_by_source: %s() IS called inside %s "
                                  "at %s" % (truth.get("forbidden_attr"),
                                             truth.get("forbidden_function"),
                                             ", ".join("%s:L%d" % (c, ln) for c, ln in
                                                       zip(d.get("callees") or ["?"],
                                                           d.get("call_lines") or [0]))
                                             or d.get("file")))
                cell["forbidden_attr"] = truth.get("forbidden_attr")
                cell["forbidden_function"] = truth.get("forbidden_function")
                cell["call_lines"] = d.get("call_lines") or []
            else:
                cell["verdict"] = "pass"
                cell["reason"] = "none_confirmed_absent_in_source"
            return cell
        if truth.get("call_present") or truth["kind"] == "CALL":
            cell["reason"] = "none_but_call_exists"
        elif truth["kind"] == "NUM":
            cell["reason"] = "none_contradicted_by_source"
        else:
            cell["verdict"] = "pass"
            cell["reason"] = "none_confirmed_absent_in_source"
        return cell

    if kind != truth["kind"]:
        cell["reason"] = "kind_mismatch:%s_expected" % truth["kind"]
        return cell

    if kind == "NUM":
        if parsed.get("answer_invalid"):
            cell["verdict"] = "fail"
            cell["reason"] = "num_not_integer:%s" % (
                (parsed.get("detail") or {}).get("rejected_numeral"))
            cell["expected_integer"] = int(expected)
            return cell
        if asserted == int(expected):
            cell["verdict"] = "pass"
            cell["reason"] = "num_equal"
        else:
            cell["reason"] = "num_mismatch"
        return cell

    # CALL: exact callee, exact kwarg NAME SET, exact value text (order is a
    # formatting rule, not a truth rule -> kwargs_as_written is reported, not graded).
    got = asserted or {}
    if _normalize(got.get("callee")) != _normalize(expected["callee"]):
        cell["reason"] = "callee_mismatch"
        return cell
    got_kwargs = got.get("kwargs") or {}
    if set(got_kwargs) != set(expected["kwargs"]):
        cell["reason"] = "kwarg_set_mismatch"
        cell["missing_kwargs"] = sorted(set(expected["kwargs"]) - set(got_kwargs))
        cell["extra_kwargs"] = sorted(set(got_kwargs) - set(expected["kwargs"]))
        return cell
    for name, want in sorted(expected["kwargs"].items()):
        have = _normalize(got_kwargs.get(name))
        if have == _normalize(want):
            continue
        if name in truth.get("elided_kwargs", []) and have in ("...", "\u2026"):
            continue          # the fixture itself elides this value; the name is graded
        cell["reason"] = "kwarg_value_mismatch:%s" % name
        cell["kwarg_expected"] = want
        cell["kwarg_asserted"] = got_kwargs.get(name)
        return cell
    cell["verdict"] = "pass"
    cell["reason"] = "call_equal"
    cell["kwargs_as_written"] = got.get("kwargs_as_written")
    return cell


def _norm_value(v):
    """Comparable form of a parsed value (ints stay ints, text is normalized)."""
    if isinstance(v, dict):
        return {k: _norm_value(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_norm_value(x) for x in v]
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, (int, float)):
        return v
    text = _normalize(v)
    if re.match(r"^-?\d+$", text):
        return int(text)
    return text


def _same_answer(content_parse, row_parse):
    """Does the row's own parse say exactly what its content says?"""
    ck = content_parse.get("answer_kind") or None
    rk = row_parse.get("answer_kind") or None
    if ck != rk:
        return False
    if ck is None:
        return ((content_parse.get("answer_parse_error") or None)
                == (row_parse.get("answer_parse_error") or None))
    return _norm_value(content_parse.get("answer_value")) == _norm_value(
        row_parse.get("answer_value"))


def _parsed_from_row(row, strict=True):
    """Parse the row's `content` - ALWAYS - and cross-check the row's own fields.

    Repair T2: the runner writes convenience fields (answer_kind/answer_value/...)
    beside the reply text. Those fields used to be preferred, so a row whose content
    was `ANSWER: TEXT ...` graded `pass/num_equal` when its fields claimed NUM 64 -
    the artefact graded itself. Content is now the only source of truth; a
    disagreeing field set raises RowFieldDisagreement naming BOTH sides.
    """
    parsed = parse_answer_contract(row.get("content") or "")
    parsed["detail"]["source"] = "content"
    fields = {k: row.get(k) for k in ROW_FIELD_KEYS}
    if fields["answer_kind"] is None and not fields["answer_parse_error"]:
        return parsed
    row_parse = {"answer_kind": fields["answer_kind"],
                 "answer_value": fields["answer_value"],
                 "answer_raw": fields["answer_raw"],
                 "answer_parse_error": fields["answer_parse_error"]}
    if _same_answer(parsed, row_parse):
        return parsed
    msg = ('row_fields_disagree_with_content: row claims kind=%r value=%r '
           'parse_error=%r, but content %r parses to kind=%r value=%r '
           'parse_error=%r' % (row_parse["answer_kind"], row_parse["answer_value"],
                               row_parse["answer_parse_error"],
                               (row.get("content") or "")[:80],
                               parsed.get("answer_kind"),
                               parsed.get("answer_value"),
                               parsed.get("answer_parse_error")))
    if strict:
        raise RowFieldDisagreement(msg, row_parse,
                                   {k: parsed.get(k) for k in
                                    ("answer_kind", "answer_value",
                                     "answer_parse_error")})
    return parsed


DECIDABLE_SOURCE = "grade_v5.decidable_population"


def decidable_population(cells):
    """THE single owner of the accuracy populations over graded checkpoint cells.

    Every consumer — this module's `arms` block and
    `analyze_stats.accuracy_from_grade` — MUST call this function instead of
    recomputing passes and fails. Two agreeing copies are the drift bug, and the
    copies HAD drifted: the analyser dropped `turn_missing` cells out of
    `failed`, so an arm with 11 unanswered checkpoints printed 5/8 while this
    grader printed 5/19 for the very same cells (`measure/MATRIX-*.json`).

    The rule (Repair T3, contracted by `tests/test_grade_v5_repair.py` and
    recorded in `measure/ATTACK-GRADE-V5-2.json`):

      pass        verdict == "pass"
      fail        verdict == "fail", INCLUDING reason == "turn_missing": the
                  grader emitted a verdict for every truth checkpoint, so an
                  unanswered checkpoint is a decided loss, not an absence
      text        verdict == "text" — never a pass, never decidable
      undecidable verdict == "undecidable" (a non-answer: no_answer_line,
                  prose_only, empty_answer, empty_text, empty_num, unparseable)
                  PLUS any cell carrying no verdict at all (`pass: null`). An
                  ungraded cell decides nothing, so an implementation that
                  counted `len(cells)` would inflate the denominator.
      decidable   pass + fail. `text` and `undecidable` are outside; `missing`
                  is a SUBSET of `fail`, printed beside it, never added again.
    """
    cells = [c for c in (cells or ()) if isinstance(c, dict)]
    passed = sum(1 for c in cells if c.get("verdict") == "pass")
    failed = sum(1 for c in cells if c.get("verdict") == "fail")
    missing = sum(1 for c in cells
                  if c.get("verdict") == "fail" and c.get("reason") == "turn_missing")
    text = sum(1 for c in cells if c.get("verdict") == "text")
    undecided = sum(1 for c in cells if c.get("verdict") == "undecidable")
    ungraded = len(cells) - passed - failed - text - undecided
    return {"source": DECIDABLE_SOURCE, "cells": len(cells),
            "passed": passed, "failed": failed, "missing": missing, "text": text,
            "undecidable": undecided + ungraded,
            "decidable": passed + failed}


def grade_rows(fixture, rows, truth=None):
    """Grade a list of row dicts (no file I/O) -> the contracted output document."""
    truth = truth if truth is not None else derive_truth(fixture)
    by_arm = {}
    for row in rows:
        by_arm.setdefault(row.get("arm") or "default", []).append(row)
    cells, arms = [], {}
    for arm, arows in sorted(by_arm.items()):
        # interim rows (fetch follow-ups / non-final attempts) are excluded.
        def _interim(r):
            if r.get("interim") is True:
                return True
            if r.get("kind") in ("turn-initial", "tool-followup"):
                return True
            return False
        _non_interim = [r for r in arows if not _interim(r)]
        # fail loudly if more than one non-interim answer for the same turn
        _seen = {}
        for r in _non_interim:
            _seen.setdefault(int(r.get("turn", -1)), []).append(r)
        _dups = [t for t, rs in _seen.items() if len(rs) > 1]
        if _dups:
            raise ValueError("duplicate non-interim checkpoint answers at turns: %s"
                             % ", ".join(str(t) for t in sorted(_dups)))
        by_turn = {int(r.get("turn", -1)): r for r in _non_interim}
        arm_cells = []
        for tr in truth:
            row = by_turn.get(tr["turn"])
            base = {"arm": arm, "id": tr["id"], "turn": tr["turn"],
                    "expected_kind": tr["kind"]}
            if row is None:
                base.update(verdict="fail", reason="turn_missing", asserted=None,
                            expected=tr["expected"], answer_kind=None, answer_raw=None,
                            answer_parse_error=None, derivation=tr["derivation"])
                arm_cells.append(base)
                continue
            try:
                parsed = _parsed_from_row(row)
            except RowFieldDisagreement as exc:
                # A hard, attributed error - never a silent preference for either
                # side. The cell fails and carries both claims.
                base.update(verdict="fail",
                            reason="row_fields_disagree_with_content",
                            asserted=(exc.row_fields or {}).get("answer_value"),
                            expected=tr["expected"],
                            answer_kind=(exc.row_fields or {}).get("answer_kind"),
                            answer_raw=row.get("answer_raw"),
                            answer_parse_error=(exc.row_fields or {}).get(
                                "answer_parse_error"),
                            derivation=tr["derivation"],
                            row_field_conflict={"row": exc.row_fields,
                                                "content": exc.content_parse,
                                                "error": str(exc)})
                arm_cells.append(base)
                continue
            cell = dict(base)
            cell.update(grade_cell(tr, parsed))
            cell["answer_turn"] = parsed.get("answer_turn")
            cell["answer_parse_detail"] = parsed.get("detail") or {}
            arm_cells.append(cell)
        cells.extend(arm_cells)
        failed = [c for c in arm_cells if c["verdict"] == "fail"]
        undecided = [c for c in arm_cells if c["verdict"] == "undecidable"]
        # The population rule lives in ONE function. A second copy here is the
        # drift that `analyze_stats` had already accumulated (see the docstring).
        pop = decidable_population(arm_cells)
        passed, decidable, text_cells = pop["passed"], pop["decidable"], pop["text"]
        arms[arm] = {
            "decidable": decidable,
            "decidable_source": pop["source"],
            "cells": pop["cells"],
            "passed": passed,
            "failed": pop["failed"],
            "undecidable": pop["undecidable"],
            "undecidable_reasons": sorted({c["reason"] for c in undecided}),
            "missing": pop["missing"],
            "checkpoint_accuracy": "%d/%d" % (passed, decidable),
            "checkpoint_accuracy_pct": (round(100.0 * passed / decidable, 1)
                                        if decidable else None),
            "decidable_note": "decidable = pass + fail; undecidable/missing beside it",
            "text_reported": text_cells,
            "text_note": "TEXT is structurally accepted, reported here, never a pass",
            "verified_success": bool(not failed and not text_cells and not undecided),
            "failing_reasons": [{"id": c["id"], "reason": c["reason"]} for c in failed],
        }
    return {"grader": "grade_v5", "rule": RULE,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fixture_task_id": fixture.get("task_id"),
            "fixture_version": fixture.get("fixture_version"),
            "contract": {
                "forms": ["ANSWER: NUM <integer>",
                          "ANSWER: CALL <callee>(<kw>=<value>, ...)",
                          "ANSWER: NONE",
                          "ANSWER: TEXT <one line>"],
                "parse": "parse_answer_contract (this module)",
                "citation_rule": "experiments/ptr-engine/tools/det_verify.py:"
                                 "asserted_number/citation_spans",
            },
            "truth": [{k: v for k, v in t.items() if k != "class_names"} for t in truth],
            "rows": len(rows), "cells": cells, "arms": arms}


# ------------------------------------------------------------------------ stamp
def stamp_document(doc, rows_path, grader_path=None):
    """Make `doc` self-dating: grader_sha256 + grader_version + rows_sha256.

    Raises StampError when any of the three cannot be computed. The caller must
    then NOT write the document: an unstamped grade file is the defect
    (orchestration/handoffs/QUALITY-ERA-TABLE.json, census: 11 stored grade-v5
    files record no grader sha, so their era was datable only by re-derivation).
    Forward-only: historical grade files are never restamped.
    """
    grader_path = os.path.abspath(grader_path or __file__)
    try:
        grader_sha = gi.file_sha256(grader_path)
        rows_sha = gi.file_sha256(rows_path)
    except (OSError, TypeError) as exc:
        raise StampError("stamp_uncomputable: %s (grader=%r rows=%r)"
                         % (exc, grader_path, rows_path))
    version = GRADER_VERSION
    if not grader_sha or not rows_sha or not str(version or "").strip():
        raise StampError("stamp_uncomputable: grader_sha256=%r grader_version=%r "
                         "rows_sha256=%r" % (grader_sha, version, rows_sha))
    doc["grader_sha256"] = grader_sha
    doc["grader_version"] = version
    doc["rows_sha256"] = rows_sha
    return doc


# ---------------------------------------------------------------------------- cli
def load_fixture(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="ANSWER-CONTRACT v5 grader (offline)")
    ap.add_argument("--rows", required=True)
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    fixture = load_fixture(args.fixture)
    rows = [json.loads(line) for line in open(args.rows, encoding="utf-8") if line.strip()]
    doc = grade_rows(fixture, rows)
    doc["rows_file"] = args.rows
    doc["fixture_file"] = args.fixture
    # Stamp BEFORE the file is opened. If the stamp cannot be computed the run
    # refuses (exit 3) instead of emitting a document nobody can date.
    try:
        stamp_document(doc, args.rows)
    except StampError as exc:
        sys.stderr.write("grade_v5: refusing to write an unstamped document: %s\n" % exc)
        return 3
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
    for arm, a in doc["arms"].items():
        print("%-20s acc=%s decidable=%d(pass %d, fail %d) undecidable=%d "
              "missing=%d text=%d verified=%s reasons=%s" % (
            arm, a["checkpoint_accuracy"], a["decidable"], a["passed"], a["failed"],
            a["undecidable"], a["missing"], a["text_reported"], a["verified_success"],
            ",".join(x["reason"] for x in a["failing_reasons"]) or "-"))
    for c in doc["cells"]:
        print("  %-12s T%-3d %-6s %-24s asserted=%r expected=%r  [%s]" % (
            c["id"], c["turn"], c["verdict"], c["reason"], c["asserted"], c["expected"],
            (c["derivation"].get("text") if isinstance(c["derivation"], dict) else "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
