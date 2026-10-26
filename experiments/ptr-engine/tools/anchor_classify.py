#!/usr/bin/env python3
"""anchor_classify.py - the ONE canonical classifier implementing rule R2.1.

OFFLINE. Stdlib only. No network, no model call, no re-grade, writes nothing.

Normative text: ``experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md`` (R2.1).
This module is the operational reading of that text; a caller must never
re-implement the rule. It supersedes the *classification* logic of
``experiments/ptr-engine/tools/anchor_prereg_check.py`` (which stays on disk,
untouched, and still passes -- it remains the checker for the FROZEN R2 doc).
Nothing was copied from it and patched: the only thing reused is the anchor
*derivation* (``grade_v3.anchors()`` semantics: TOKEN_RE, split on "_", drop
len<4 and STOPWORDS), re-implemented here verbatim-by-description and pinned to
grade_v3 by an equality assertion in
``experiments/ptr-engine/tools/tests/test_anchor_classify.py``.

R2.1 in one line: an anchor is CODE-SYMBOL iff it occurs, inside the checkpoint's
cited line range, as (part of) a ``tokenize`` NAME token; occurrences inside a
STRING token (docstring, any continuation line of it), a COMMENT token, or any
part of an f-string (FSTRING_START / FSTRING_MIDDLE / FSTRING_END) do not count.
The decision is per OCCURRENCE, never per line. The answer side is deliberately
mention-only (see METRIC / SEMANTIC below) and is a known, accepted limitation.

Public API::

    classify(anchor, "path/to/file.py#L66-L71")  -> Classification
    required_anchors(expected, "path#L66-L71")   -> [anchor dicts]
    judge(answer_text, required)                 -> {"verdict": "ACCEPT"|"REJECT", ...}
    rule_digest("...ANCHOR-PREREG-V2.md")        -> sha256 of the R2.1 rule body
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import tokenize

CODE_SYMBOL = "CODE-SYMBOL"
NUMBER = "NUMBER"
PROSE_CONNECTOR = "PROSE-CONNECTOR"

#: R2.1 judges WHICH TOKENS MUST APPEAR. It does not judge meaning. Probe E (a
#: sentence that negates every anchor while naming all of them) is ACCEPTED by
#: design; that is a declared limitation, not a bug, and never a semantic pass.
RULE = "R2.1"
METRIC = "mention-only"
SEMANTIC = False

#: Interpretation is pinned to CPython >= 3.12 (measured on 3.14.4, the only
#: interpreter on this host) because below 3.12 an f-string is ONE STRING token
#: and its replacement fields stop being NAME tokens. See ANCHOR-PREREG-V2.md
#: section 1.3 for the exact consequence.
INTERPRETER_PIN = "CPython >= 3.12 (measured on 3.14.4)"

RULE_BEGIN = "<!-- r21-rule:begin -->"
RULE_END = "<!-- r21-rule:end -->"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

# CPython 3.12+ emits these three token types for f-strings; on <= 3.11 they do
# not exist and the whole f-string is a single STRING token instead.
FSTRING_TYPES = tuple(
    getattr(tokenize, name) for name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END")
    if hasattr(tokenize, name)
)
PROSE_TYPES = frozenset({tokenize.STRING, tokenize.COMMENT}) | frozenset(FSTRING_TYPES)

# Copied by description from experiments/ptr-engine/longrun/grade_v3.py:15-22 --
# R2/R2.1 do not change anchor derivation. tests/test_anchor_classify.py asserts
# derive_anchors() == grade_v3.anchors() on every fixture `expected` string.
STOPWORDS = frozenset("""
that this than then them they their there these those with from into over
also both each only when where which while would should could must have
has had been being will shall about above across after before below between
more most some such same just like make makes made used using does doing
then once only also very much many what whom whose here were were was are and
for the but not you your our its his her all any can may
""".split())
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
MARKER_RE = re.compile(r"^ANSWER:\s*\S.*$")

_CITE_TAIL = re.compile(r"^(?P<a>\d+)(?:-L?(?P<b>\d+))?$")
_PART_SPLIT = re.compile(r"[^A-Za-z0-9]+")
_NUM_RE = re.compile(r"^\d+$")


# --------------------------------------------------------------------------
# citations  ("experiments/.../resolve.py#L66-L71")
# --------------------------------------------------------------------------
def parse_source_ref(ref):
    """Split a citation into (path, (start, end) | None).

    ``#L39``            -> single-line range (39, 39)
    ``#L66-L71``/``#L66-71`` -> (66, 71)
    no fragment         -> (path, None), meaning the whole file
    """
    ref = (ref or "").strip()
    if "#L" in ref:
        path, _, tail = ref.partition("#L")
        m = _CITE_TAIL.match(tail)
        if not m:
            raise ValueError("unparseable line-range citation %r" % (ref,))
        start = int(m.group("a"))
        end = int(m.group("b") or start)
        if end < start:
            raise ValueError("inverted line range in %r" % (ref,))
        return path, (start, end)
    return ref, None


def source_path(ref):
    """Resolve a citation's path against the workspace root."""
    path, _ = parse_source_ref(ref)
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


# --------------------------------------------------------------------------
# anchor derivation (R2/R2.1 do not change this; grade_v3.anchors semantics)
# --------------------------------------------------------------------------
def derive_anchors(expected):
    """Derived anchor tokens of an `expected` string, order-preserving."""
    seen, out = set(), []
    for m in TOKEN_RE.finditer(expected or ""):
        for part in m.group(0).split("_"):
            p = part.lower()
            if len(p) >= 4 and p not in STOPWORDS and p not in seen:
                seen.add(p)
                out.append(p)
    return out


# --------------------------------------------------------------------------
# occurrence scan
# --------------------------------------------------------------------------
def _parts(s):
    """Lower-cased alphanumeric parts of a token text.

    One split rule for both sides of the rule: ``record_refusal`` -> {record,
    refusal} (NAME tokens), ``re-raising`` -> {re, raising} and
    ``resolve budget spent: `` -> {resolve, budget, spent} (prose text).
    """
    return [p.lower() for p in _PART_SPLIT.split(s) if p]


def _tokens(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return list(tokenize.tokenize(io.BytesIO(raw).readline))


class Occurrence(object):
    """One place the anchor was seen, with what kind of token it was seen in."""

    __slots__ = ("line", "end_line", "kind", "token", "is_code", "basis")

    def __init__(self, line, end_line, kind, token, is_code, basis=""):
        self.line = line
        self.end_line = end_line
        self.kind = kind            # tokenize token name, e.g. NAME / STRING
        self.token = token          # the token's text (truncated for display)
        self.is_code = is_code      # True only for a NAME token (or a number literal)
        self.basis = basis          # for NUMBER: "literal" / "class-count"

    def as_dict(self):
        d = {"line": self.line, "kind": self.kind, "token": self.token,
             "is_code": self.is_code}
        if self.end_line != self.line:
            d["end_line"] = self.end_line
        if self.basis:
            d["basis"] = self.basis
        return d

    def __repr__(self):
        return "Occurrence(%d, %s, %r)" % (self.line, self.kind, self.token)


class Classification(object):
    """The classifier's verdict for one anchor against one citation."""

    def __init__(self, anchor, cls, cite, code, prose, decided_by):
        self.anchor = anchor
        self.cls = cls
        self.cite = cite
        self.code = code            # [Occurrence] counting (is_code) occurrences
        self.prose = prose          # [Occurrence] non-counting occurrences
        self.decided_by = decided_by  # "tokenize-NAME" | "expected-form"

    # -- convenience ------------------------------------------------------
    @property
    def occurrence_lines(self):
        """Lines the decision was made on: the code lines, else the prose lines."""
        src = self.code or self.prose
        return [o.line for o in src]

    @property
    def evidence(self):
        """First counting code line, or the prose lines that made it prose."""
        if self.code:
            return "%s:%d" % (self.cite, self.code[0].line)
        if self.prose:
            return "%s:%-4s (prose only: %s)" % (
                self.cite, str(self.prose[0].line),
                ", ".join(sorted({o.kind for o in self.prose})),
            )
        return "%s: absent" % (self.cite,)

    def __iter__(self):
        # so `cls, occurrences = classify(...)` works
        return iter((self.cls, self.occurrence_lines))

    def as_dict(self):
        return {
            "anchor": self.anchor,
            "class": self.cls,
            "cite": self.cite,
            "decided_by": self.decided_by,
            "evidence": self.evidence,
            "occurrences": [o.as_dict() for o in (self.code + self.prose)],
        }

    def __repr__(self):
        return "Classification(%r, %s, %s)" % (self.anchor, self.cls, self.evidence)


def _in_range(lo, hi, line):
    if lo is None:
        return True
    return lo <= line <= hi


def _prose_first_line(tok, key, text_lines, lo, hi):
    """First line of a (possibly multi-line) prose token that carries the anchor.

    This is what makes a docstring continuation line reportable: the STRING token
    starts on the line the docstring opens on, but the anchor can sit on any of
    its continuation lines.
    """
    for line in range(tok.start[0], tok.end[0] + 1):
        if not _in_range(lo, hi, line):
            continue
        if line - 1 < len(text_lines) and key in _parts(text_lines[line - 1]):
            return line
    return None


def _display(tok):
    s = tok.string.replace("\n", "\\n")
    return s if len(s) <= 60 else s[:57] + "..."


def classify(anchor, source_path, line_range=None):
    """Classify one anchor against one citation under R2.1.

    Returns a :class:`Classification` (``.cls`` is CODE-SYMBOL / NUMBER /
    PROSE-CONNECTOR, ``.occurrence_lines`` the lines it was decided on). Also
    unpackable: ``cls, lines = classify(...)``.

    ``line_range`` overrides the ``#L..-L..`` fragment when given (for probes
    that scope the rule by hand).
    """
    path, cite_range = parse_source_ref(source_path)
    if line_range is not None:
        cite_range = (int(line_range[0]), int(line_range[1]))
    abs_path = path if os.path.isabs(path) else os.path.join(ROOT, path)
    key = (anchor or "").strip().lower()
    cite = (source_path or "").replace(str(ROOT) + os.sep, "")
    lo, hi = (None, None) if cite_range is None else cite_range

    toks = _tokens(abs_path)
    with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
        text_lines = fh.read().split("\n")

    # ---- NUMBER: decided by the expected string's own form (R2 wording) ----
    # The anchor is a decimal integer literal, so it IS a number anchor; the
    # source is only corroboration. This is why `31` (a count of class
    # definitions, not a literal token) is still NUMBER.
    if _NUM_RE.match(key):
        numbers = [t for t in toks
                   if t.type == tokenize.NUMBER and _in_range(lo, hi, t.start[0])]
        lit = [t for t in numbers if t.string.replace("_", "") == key]
        if lit:
            first = lit[0]
            return Classification(anchor, NUMBER, cite,
                                  [Occurrence(first.start[0], first.start[0],
                                              "NUMBER", first.string, False, "literal")],
                                  [], "expected-form")
        class_lines = [n for n in range(1, len(text_lines) + 1)
                       if _in_range(lo, hi, n) and text_lines[n - 1].startswith("class ")]
        if len(class_lines) == int(key):
            mid = [Occurrence(class_lines[0], class_lines[-1], "class-def", "class ", False,
                              "class-count")]
            return Classification(anchor, NUMBER, cite, mid, [], "expected-form")
        return Classification(anchor, NUMBER, cite,
                              [Occurrence(0, 0, "absent", "(no literal, no class count)",
                                          False, "unestablished")],
                              [], "expected-form")

    # ---- CODE-SYMBOL vs PROSE-CONNECTOR: per OCCURRENCE, not per line ----
    code, prose = [], []
    for tok in toks:
        kind = tokenize.tok_name.get(tok.type, str(tok.type))
        if tok.type in PROSE_TYPES:
            if key not in _parts(tok.string):
                continue
            line = _prose_first_line(tok, key, text_lines, lo, hi)
            if line is None:
                continue
            prose.append(Occurrence(line, tok.end[0], kind, _display(tok), False))
        elif tok.type == tokenize.NAME:
            if key not in [p.lower() for p in tok.string.split("_")]:
                continue
            if not _in_range(lo, hi, tok.start[0]):
                continue
            code.append(Occurrence(tok.start[0], tok.end[0], kind, _display(tok), True))

    cls = CODE_SYMBOL if code else PROSE_CONNECTOR
    return Classification(anchor, cls, cite, code, prose, "tokenize-NAME")


def required_anchors(expected, source_ref):
    """R2.1 required set for one checkpoint: anchors classified CODE-SYMBOL.

    NUMBER anchors are classified but NOT required here -- they are graded by
    ``grade_v3.number_in()``, exactly as under R2 (ANCHOR-PREREG.md section 4).
    """
    out = []
    for anchor in derive_anchors(expected):
        c = classify(anchor, source_ref)
        out.append(c)
    return out


# --------------------------------------------------------------------------
# the answer side: mention-only, by declared limitation
# --------------------------------------------------------------------------
def mentions(anchor, text):
    """True iff `text` mentions the anchor as a whole word ("_" is a boundary).

    This inherits `grade_v3.has_anchor()` (grade_v3.py:51-58) on purpose: R2.1
    governs which tokens must appear, not whether the sentence is right. A
    negated sentence that names every anchor therefore passes -- see METRIC.
    """
    return re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(anchor),
                     text or "", re.I) is not None


def marker_line(answer_text):
    for line in (answer_text or "").splitlines():
        if MARKER_RE.match(line):
            return line
    return None


def judge(answer_text, classifications):
    """Judge one answer under R2.1. Returns a dict with verdict + evidence.

    Mirrors the non-numeric branch of `grade_v3.judge`: the marker must be
    present, every required anchor must be mentioned, and the marker line itself
    must carry at least one required anchor.
    """
    required = [c for c in classifications if c.cls == CODE_SYMBOL]
    marker = marker_line(answer_text)
    missing = [c.anchor for c in required if not mentions(c.anchor, answer_text)]
    reason, verdict = "ok", "ACCEPT"
    if marker is None:
        verdict, reason = "REJECT", "marker_missing"
    elif missing:
        verdict, reason = "REJECT", "missing_anchor:" + ",".join(missing)
    elif not any(mentions(c.anchor, marker) for c in required):
        verdict, reason = "REJECT", "marker_carries_no_required_anchor"
    return {
        "verdict": verdict,
        "reason": reason,
        "missing": missing,
        "required": [c.anchor for c in required],
        "marker_line": marker,
        "metric": METRIC,
        "semantic": SEMANTIC,
        "rule": RULE,
        "evidence": [c.as_dict() for c in classifications],
    }


# --------------------------------------------------------------------------
# attestation: the digest of the rule text itself
# --------------------------------------------------------------------------
def rule_text(doc_path):
    """The R2.1 rule body, delimited by RULE_BEGIN / RULE_END.

    Definition (unambiguous on purpose): the lines strictly between the marker
    lines, joined with "\\n", terminated by one "\\n". Nothing else is stripped
    or normalised, so a third party reads the same bytes.
    """
    path = doc_path if os.path.isabs(doc_path) else os.path.join(ROOT, doc_path)
    with open(path, "r", encoding="utf-8", newline="\n") as fh:
        lines = fh.read().split("\n")
    try:
        i = next(n for n, l in enumerate(lines) if l.strip() == RULE_BEGIN)
        j = next(n for n, l in enumerate(lines) if l.strip() == RULE_END)
    except StopIteration:
        raise ValueError("R2.1 rule markers not found in %r" % (doc_path,))
    if j <= i:
        raise ValueError("RULE_END precedes RULE_BEGIN in %r" % (doc_path,))
    return "\n".join(lines[i + 1:j]) + "\n"


def rule_digest(doc_path):
    """sha256 (hex) of rule_text(doc_path) - the attestation of the frozen text."""
    return hashlib.sha256(rule_text(doc_path).encode("utf-8")).hexdigest()


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="classify anchors under R2.1")
    ap.add_argument("anchor")
    ap.add_argument("source_ref")
    args = ap.parse_args(argv)
    print(classify(args.anchor, args.source_ref).as_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
