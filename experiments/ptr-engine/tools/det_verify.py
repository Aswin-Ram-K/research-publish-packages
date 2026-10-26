#!/usr/bin/env python3
"""det_verify.py - a deterministic verifier for the machine-decidable checkpoints.

Ground truth is derived by AST from the cited source file, not from the fixture's
expected string and not from token presence. A correct answer is one that asserts
the source fact; prose, punctuation and surrounding words do not decide.

    python3 experiments/ptr-engine/tools/det_verify.py \
        [--out experiments/ptr-engine/measure/det-verify-matrix.json]

Checks implemented (the machine-decidable subset), each with the checkpoints whose
fixture entry asserts the SAME source-derived fact:

    cp.0.t12     value of `DEFAULT_MAX_REFS` in resolve.py           (numeric)
    cp.1.t24     count of `class Ptr*` definitions in errors.py      (numeric)
    cp.2.t46     callee + keyword names of the call inside `_refuse` (structural)
    acc.cp1      mirror of cp.0.t12 (same DERIVED value, own probes)
    acc.cp2      mirror of cp.1.t24
    acc.cp3      mirror of cp.2.t46
    acc.1        DEFAULT_MAX_REFS == 64, the same AST fact as acc.cp1
    acc.4        count of `def test_*` in tests/test_scope.py        (ast.FunctionDef)

NUMERAL RULE (what counts as the asserted value). The asserted value is the numeral
the answer presents AS ITS ANSWER. A numeral that is part of a CITATION is not a
candidate: `<path>:<n>`, `#L<n>`, `L<n>`, `line <n>`, `<n> of <m>`, or any numeral
inside a parenthetical that names a file. A numeral the answer retracts
("64 is wrong") is not a candidate either. Among the survivors the preference is,
in order: (1) the first candidate in the answer slot - the leading clause of the
text after the last `ANSWER:` marker; (2) failing that, the first candidate
anywhere in that segment. The rule is about citation FORM, not about any one probe
string: no answer is special-cased.

NEGATION RULE (what counts as denying the call). A call mention is negated when a
negative cue from the NEGATION lexicon (explicit `not`, contractions, `never`,
`without calling`, `instead of calling`, `fails to call`, `skips the call`,
`avoid calling`) governs it in the same clause, before or just after the mention.
The lexicon is clause-local on purpose: an `avoid` in an unrelated clause next to a
correct call description does NOT make that description a denial.

COVERAGE is computed in code from CHECK_HANDLERS over the matrix's full entry list;
`decidable / total` is `COVERAGE_SUMMARY`, not prose. Everything else is declared
undecidable with its reason and is EXCLUDED from the FN/FP gate by name.

Exit status: 0 when the gate FN=0/FP=0 holds, 2 when it does not.

Offline, stdlib only, deterministic. Reads the graders' probe corpus read-only by
importing PROBES from grader_fitness.py; never edits it, never edits a fixture.
"""
import argparse
import ast
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")
FIXTURE = os.path.join(LONGRUN, "fixtures", "LR-01.json")
FITNESS_JSON = os.path.join(ROOT, "experiments", "ptr-engine", "measure",
                            "grader-fitness.json")
DEFAULT_OUT = os.path.join(ROOT, "experiments", "ptr-engine", "measure",
                           "det-verify-matrix.json")

# Checkpoints this verifier can actually decide in code (see CHECK_HANDLERS and
# COVERAGE_SUMMARY). acc.cp1/acc.cp2/acc.cp3/acc.1 are NOT copies of the cp.* answers:
# each is verified against the same AST-derived value by its own probes.
DECIDABLE = ("cp.0.t12", "cp.1.t24", "cp.2.t46",
             "acc.cp1", "acc.cp2", "acc.cp3", "acc.1", "acc.4")

# Every matrix entry, in fixture order; COVERAGE is built from this and
# CHECK_HANDLERS, so "decidable" is a property of code, not of a prose claim.
CHECK_ORDER = ("cp.0.t12", "cp.1.t24", "cp.2.t46", "acc.cp1", "acc.cp2", "acc.cp3",
               "acc.1", "acc.2", "acc.3", "acc.4", "acc.n2b", "acc.n3b..acc.n3e",
               "repair.t30")

# --------------------------------------------------------------------------- #
# answer text: the claim an arm actually made
# --------------------------------------------------------------------------- #
ANSWER_MARKER = re.compile(r"ANSWER\s*:", re.I)
# An integer, not embedded in a word and not the integer part of a float.
INT_RE = re.compile(r"(?<![\w.])\d+(?![\w])")


def answer_segment(text):
    """The text after the last `ANSWER:` marker; the whole answer if there is none.

    Rationale (GRADER-FITNESS.md section 5): a conclusion-position rule, so that a
    numeral merely present earlier in the prose cannot be read as the asserted value.
    """
    hits = list(ANSWER_MARKER.finditer(text))
    if not hits:
        return text
    return text[hits[-1].end():]


# An integer the answer explicitly marks as NOT its claim ("64 is wrong", "31 is
# stale"). Narrow by construction: only an `is/was` copula plus a falsity word.
RETRACT_AFTER = re.compile(
    r"^\s*(?:is|was|are|were)\s+(?:wrong|stale|incorrect|outdated|false|obsolete|"
    r"no\s+longer)\b", re.I)


# A CITATION is a file position, not a value: `<path>:<n>`, `#L<n>`, `L<n>`,
# `line <n>`, `<n> of <m>`, or any numeral inside a parenthetical naming a file.
# A numeral lying inside one of these spans is disqualified as a candidate.
CITATION_SPANS = (
    # resolve.py:39 / experiments/ptr-engine/ptr_engine/resolve.py:66-71
    re.compile(r"[A-Za-z0-9_./-]*[A-Za-z_][\w-]*\.\w+:\d+(?:\s*[-\u2013]\s*\d+)?"),
    # #L39 / #L15-L142 / L39 / L15-142
    re.compile(r"#L\d+(?:\s*[-\u2013]\s*L?\d+)?"
               r"|(?<!\w)L\d+(?:\s*[-\u2013]\s*L?\d+)?"),
    # line 39 / lines 15-142
    re.compile(r"\blines?\s+\d+(?:\s*[-\u2013]\s*\d+)?"),
    # 1 of 3 files
    re.compile(r"\b\d+\s+of\s+\d+\b"),
    # a parenthetical naming a file: (resolve.py:39), (see ledger.py:12)
    re.compile(r"\([^()]*[A-Za-z_][\w-]*\.\w{1,5}[^()]*\)"),
    re.compile(r"\([^()]*#?L\d+[^()]*\)"),
)


def citation_spans(segment):
    """[(start, end)] of citation text inside the answer segment."""
    spans = []
    for rx in CITATION_SPANS:
        spans.extend((m.start(), m.end()) for m in rx.finditer(segment))
    return spans


def _in_citation(pos, spans):
    return any(s <= pos < e for s, e in spans)


def answer_slot_end(segment):
    """End of the leading clause after the marker: up to `;` or a sentence period."""
    lead = len(segment) - len(segment.lstrip())
    end = len(segment)
    semi = segment.find(";", lead)
    if semi >= 0:
        end = min(end, semi)
    dot = re.search(r"\.(?=\s|$)", segment[lead:])
    if dot:
        end = min(end, lead + dot.start())
    return end


def asserted_number(segment):
    """The numeral the answer presents as ITS answer (rule: module docstring).

    Candidates are integers in the marker segment that are neither citation
    numerals nor retracted. Preference: (1) the first candidate in the answer slot
    (the leading clause); (2) failing that, the first candidate anywhere in the
    segment. Taking the FIRST survivor - not the last - is what stops a trailing
    `(resolve.py:39)` from being read as the asserted value.
    """
    spans = citation_spans(segment)
    kept, dropped = [], []
    for m in INT_RE.finditer(segment):
        if _in_citation(m.start(), spans):
            dropped.append({"value": int(m.group()), "cited_at": m.start()})
            continue
        tail = segment[m.end():m.end() + 48]
        if RETRACT_AFTER.match(tail):
            dropped.append({"value": int(m.group()), "retracted_by": tail[:32].strip()})
            continue
        kept.append({"value": int(m.group()), "at": m.start()})
    if not kept:
        return None, {"numeral_found": False, "dropped": dropped,
                      "citation_spans": spans}
    slot_end = answer_slot_end(segment)
    in_slot = [c for c in kept if c["at"] < slot_end]
    chosen = in_slot[0] if in_slot else kept[0]
    return chosen["value"], {
        "numeral_found": True, "numeral_at": chosen["at"],
        "selection": "answer_slot" if in_slot else "first_candidate",
        "candidates": kept, "dropped": dropped, "citation_spans": spans}


# --------------------------------------------------------------------------- #
# negation: narrow, stated, and local to the clause governing the call mention
# --------------------------------------------------------------------------- #
NEGATION = re.compile(
    # explicit negative auxiliaries: do not / does not / did not / must not /
    # should not / can not / could not / will not / would not / shouldn't / won't
    r"(?:\b(?:do|does|did|must|should|can|could|will|would)\s+not\b"
    r"|n't\b"
    r"|\bnever\b"
    # not call / not calling / not to call / never calls
    r"|\bnot\s+(?:to\s+)?(?:call|calling|invoke|invoking|record|recording|write|"
    r"writing|persist|persisting|perform|create|use|using)\b"
    # no record_refusal call / no invocation / no ledger write
    r"|\bno\s+(?:[\w.]+\s+){0,3}(?:call|invocation|write|recording)\b"
    # without calling / without ever recording
    r"|\bwithout\s+(?:ever\s+)?(?:calling|recording|writing|invoking|persisting)\b"
    # instead of calling / instead of recording
    r"|\binstead\s+of\s+(?:[\w.]+\s+){0,2}(?:calling|invoking|recording|writing|"
    r"persisting)\b"
    # fails to call / failed to record
    r"|\bfail(?:s|ed|ing)?\s+to\s+(?:call|invoke|record|write|persist)\b"
    # skips the call / skipped the ledger write / skipping recording
    r"|\bskip(?:s|ped|pped|ping|pping)?\s+(?:[\w.]+\s+){0,3}?(?:call|calling|"
    r"invocation|invoking|recording|writing|write|persisting)\b"
    r"|\bno\s+longer\b)", re.I)

# `avoid` is its own entry because it is the one cue that also appears in correct
# prose ("avoid the retry loop"). It negates only when it governs a call-ish verb
# object - avoid calling / avoid the call / avoid recording - never when its
# object is something else.
AVOID_VERB_RX = re.compile(
    r"\bavoid(?:s|ed|ing)?\s+"
    r"(?:(?:the|a|an|any|all|this|that|further|repeated|direct)\s+)?"
    r"(?:calling|call|invoking|invoke|recording|record|writing|write|persisting|"
    r"persist)\b", re.I)


def negation_in(clause, callee=None):
    """Return the negative cue governing a call mention in this clause, or None.

    The rule is a LEXICON, clause-local: a negative auxiliary/imperative, a
    contraction, a bare `never`, `not (to) call(ing)`, `no ... call/write`,
    `without calling`, `instead of calling`, `fails to call`, `skips the call`, or
    `avoid calling` - inside the same clause (back to the nearest `.`/`;`/newline,
    at most 100 characters). A denial elsewhere in the answer does not license
    rejecting an otherwise correct call description, and an `avoid` whose object is
    not the call does not count as a denial.
    """
    if not clause:
        return None
    m = NEGATION.search(clause)
    if m:
        return m.group(0)
    m = AVOID_VERB_RX.search(clause)
    if m:
        return m.group(0)
    if callee:
        attr = re.escape(callee.split(".")[-1])
        m = re.search(r"\bavoid(?:s|ed|ing)?\s+(?:(?:using|any)\s+)?"
                      r"(?:[\w]+\.)*%s\b" % attr, clause, re.I)
        if m:
            return m.group(0)
    return None


def clause_before(text, pos, window=100):
    start = max(0, pos - window)
    head = text[start:pos]
    cut = max(head.rfind(c) for c in ".;\n") if any(c in head for c in ".;\n") else -1
    return head[cut + 1:]


# --------------------------------------------------------------------------- #
# source-derived ground truth
# --------------------------------------------------------------------------- #
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_module(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return ast.parse(raw.decode("utf-8"), filename=path), sha256_file(path)


def constant_value(tree, name):
    """Literal value of a module-level `name = <literal>` assignment."""
    for node in tree.body:
        targets, value = [], None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        for t in targets:
            if isinstance(t, ast.Name) and t.id == name:
                return ast.literal_eval(value), node.lineno
    raise SystemExit("constant %r not found in %s" % (name, getattr(tree, "filename", "?")))


def count_classes(tree, pattern_regex):
    rx = re.compile(pattern_regex)
    names = [(n.name, n.lineno) for n in tree.body
             if isinstance(n, ast.ClassDef) and rx.search(n.name)]
    return names


def call_inside_function(tree, func_name, attr):
    """(callee, keyword names, lineno) of `*.attr(...)` inside function func_name."""
    found = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                        and sub.func.attr == attr):
                    found.append({
                        "callee": ast.unparse(sub.func),
                        "keywords": [k.arg for k in sub.keywords],
                        "lineno": sub.lineno,
                        "unparsed": ast.unparse(sub),
                    })
    if len(found) != 1:
        raise SystemExit("expected exactly one %s() call in %s, found %d"
                         % (attr, func_name, len(found)))
    return found[0]


def source_paths(fixture):
    base = os.path.join(ROOT, "experiments", "ptr-engine", "ptr_engine")
    out = {}
    for s in fixture["sources"]:
        out[s["id"]] = os.path.join(ROOT, s["path"]) if s["path"].startswith("experiments") \
            else os.path.join(base, os.path.basename(s["path"]))
    return out


class Truth(object):
    """Everything det_verify is allowed to treat as fact, each with its evidence."""

    def __init__(self, fixture_path=FIXTURE):
        with open(fixture_path) as fh:
            self.fixture = json.load(fh)
        paths = source_paths(self.fixture)
        self.resolve_path = paths["resolve.py"]
        self.errors_path = paths["errors.py"]

        tree, digest = parse_module(self.resolve_path)
        self.resolve_digest = digest
        self.default_max_refs, self.default_lineno = constant_value(tree, "DEFAULT_MAX_REFS")
        self.refuse_call = call_inside_function(tree, "_refuse", "record_refusal")

        tree_e, digest_e = parse_module(self.errors_path)
        self.errors_digest = digest_e
        cp1 = self.checkpoint("cp.1.t24")
        m = re.search(r"([A-Za-z_][\w]*)\*", cp1["question"])
        self.class_prefix = m.group(1) if m else "Ptr"
        self.ptr_classes = count_classes(tree_e, r"^%s\w*$" % re.escape(self.class_prefix))

        # acc.4: the `grep -c '^def test_'` check, decided by ast.FunctionDef over
        # the pinned path the fixture itself names in acc.n3d (not a hard-coded copy).
        acc4 = next(c for c in self.fixture["acceptance"]["checks"]
                    if c["id"] == "acc.n3d")
        self.test_module_path = os.path.join(ROOT, acc4["no_write"])
        tree_t, digest_t = parse_module(self.test_module_path)
        self.test_module_digest = digest_t
        self.test_functions = [(n.name, n.lineno) for n in tree_t.body
                               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                               and n.name.startswith("test_")]

        declared = {s["id"]: s.get("sha256", "").replace("sha256:", "")
                    for s in self.fixture["sources"]}
        self.digest_matches = {
            "resolve.py": declared.get("resolve.py") == self.resolve_digest,
            "errors.py": declared.get("errors.py") == self.errors_digest,
        }

    def checkpoint(self, cp_id):
        """Fixture checkpoint whose citation the id `cp.<index>.t<turn>` names."""
        m = re.match(r"cp\.(\d+)\.", cp_id)
        if not m:
            raise KeyError(cp_id)
        idx = int(m.group(1))
        return self.fixture["checkpoints"][idx]

    def evidence(self):
        return {
            "resolve.py": {"path": rel(self.resolve_path), "sha256": self.resolve_digest,
                           "sha256_matches_fixture": self.digest_matches["resolve.py"],
                           "DEFAULT_MAX_REFS": {"value": self.default_max_refs,
                                                "line": self.default_lineno},
                           "_refuse.record_refusal": self.refuse_call},
            "errors.py": {"path": rel(self.errors_path), "sha256": self.errors_digest,
                          "sha256_matches_fixture": self.digest_matches["errors.py"],
                          "class_pattern": r"^%s\w*$" % self.class_prefix,
                          "class_count": len(self.ptr_classes),
                          "class_names": [n for n, _ in self.ptr_classes]},
            "tests/test_scope.py": {
                "path": rel(self.test_module_path), "sha256": self.test_module_digest,
                "test_function_count": len(self.test_functions),
                "test_function_names": [n for n, _ in self.test_functions]},
        }


def rel(path):
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path


# --------------------------------------------------------------------------- #
# call-claim extraction (structural, not a mention test)
# --------------------------------------------------------------------------- #
CALLEE_RX = re.compile(r"(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*")
CALL_PARENS_RX = re.compile(r"((?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)\s*\(([^()]*)\)")
CALL_WITH_RX = re.compile(
    r"(?:call(?:s|ed)?|invoke[sd]?|record(?:s|ed)?|writ(?:e|es|ten)|via)\s+"
    r"((?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)\s+(?:with|carrying|taking)\s+([^.;\n]+)", re.I)
ARG_LIST_RX = re.compile(
    r"\b(?:with|carrying|taking|passing)\s+(.+?)(?=\b(?:before|then|so|while|after)\b|\.(?=\s|$)|[;\n]|$)",
    re.I)
ITEM_CUT = re.compile(r"\s*(?:,?\s*(?:then|before|so that|so|while|after|and then)\b.*)$", re.I)
KW_RX = re.compile(r"([A-Za-z_]\w*)\s*=")


def _keywords_from_items(items):
    """Keyword names named by a `with a, b=x and c=y` list."""
    names = set()
    for raw in items:
        item = ITEM_CUT.sub("", raw).strip().strip(",")
        item = re.sub(r"^(?:the|a|an)\s+", "", item, flags=re.I)
        if not item:
            continue
        if " as " in item:
            toks = CALLEE_RX.findall(item.split(" as ")[-1].strip())
            if toks:
                names.add(toks[0].split(".")[-1])
            continue
        m = KW_RX.search(item)
        if m:
            names.add(m.group(1))
            continue
        toks = CALLEE_RX.findall(item)
        dotted = [t for t in toks if "." in t]
        if dotted:
            names.add(dotted[-1].split(".")[-1])
        elif toks:
            names.add(toks[-1].split(".")[-1])
    return names


def split_items(blob):
    blob = re.sub(r"\s+and\s+", ", ", blob)
    return [p for p in (x.strip() for x in blob.split(",")) if p]


def call_claim(answer, gt_callee):
    """Extract {callee, keywords, negated} from the answer, or None if the call is
    never named. Look in the ANSWER segment first, then the full answer body, so a
    correct paraphrase that names the call in its reasoning still counts."""
    attr = gt_callee.split(".")[-1]
    mention_rx = re.compile(r"(?:[A-Za-z_]\w*\.)*%s\b" % re.escape(attr))
    segment = answer_segment(answer)
    for scope_name, scope in (("answer_segment", segment), ("answer_body", answer)):
        m = mention_rx.search(scope)
        if not m:
            continue
        neg = negation_in(clause_before(scope, m.start()), gt_callee)
        if neg is None:
            # a negative predicate may also follow the mention in the same clause
            tail = re.split(r"[.;\n]", scope[m.end():m.end() + 90])[0]
            neg = negation_in(tail, gt_callee)
        if neg is not None:
            return {"callee": m.group(0), "keywords": set(), "negated": neg,
                    "scope": scope_name, "raw": scope[max(0, m.start() - 40):m.end() + 60]}
        window = scope[m.end():m.end() + 220]
        pw = re.match(r"\s*\(([^()]*)\)", window)
        if pw:
            kws = set(x.group(1) for x in KW_RX.finditer(pw.group(1)))
            return {"callee": m.group(0), "keywords": kws, "negated": None,
                    "scope": scope_name, "raw": pw.group(0)}
        # "a ledger.record_refusal entry carrying the scope, ..." - the argument list
        # is the first `with/carrying/taking/passing` phrase after the mention.
        mw = ARG_LIST_RX.search(window)
        if not mw:
            return {"callee": m.group(0), "keywords": set(), "negated": None,
                    "scope": scope_name, "raw": window[:80]}
        return {"callee": m.group(0),
                "keywords": _keywords_from_items(split_items(mw.group(1))),
                "negated": None, "scope": scope_name,
                "raw": m.group(0) + " " + mw.group(0)}
    return None


# --------------------------------------------------------------------------- #
# the three checks
# --------------------------------------------------------------------------- #
def check_numeric(answer, truth_value, label):
    segment = answer_segment(answer)
    value, ev = asserted_number(segment)
    if value is None:
        return False, "no_asserted_value", {"answer_segment": segment.strip()}
    ok = value == truth_value
    return ok, ("asserted_value_matches" if ok else "asserted_value_mismatch"), {
        "asserted": value, "truth": truth_value, "answer_segment": segment.strip(),
        "numeric_rule": ev}


def check_call(answer, truth_call):
    claim = call_claim(answer, truth_call["callee"])
    if claim is None:
        return False, "call_not_named", {"truth_callee": truth_call["callee"]}
    if claim["negated"]:
        return False, "call_negated", {"negative_cue": claim["negated"],
                                       "claim": claim["raw"]}
    want_callee = truth_call["callee"]
    got = claim["callee"]
    if got != want_callee and got.split(".")[-1] != want_callee.split(".")[-1]:
        return False, "wrong_callee", {"claimed": got, "truth": want_callee}
    want = set(truth_call["keywords"])
    if claim["keywords"] != want:
        return False, "keyword_mismatch", {
            "claimed": sorted(claim["keywords"]), "truth": sorted(want),
            "missing": sorted(want - claim["keywords"]),
            "extra": sorted(claim["keywords"] - want)}
    return True, "call_shape_matches", {"callee": want_callee, "keywords": sorted(want),
                                        "claim": claim["raw"]}


# Which check decides each checkpoint. A checkpoint appears here only if the code
# below derives its expected value from the source AST; `via` names the mirrored
# cp.* checkpoint when the fixture entry asserts the same derived fact.
CHECK_HANDLERS = {
    "cp.0.t12": {"kind": "constant", "via": "cp.0.t12"},
    "cp.1.t24": {"kind": "class_count", "via": "cp.1.t24"},
    "cp.2.t46": {"kind": "call_shape", "via": "cp.2.t46"},
    "acc.cp1": {"kind": "constant", "via": "cp.0.t12"},
    "acc.cp2": {"kind": "class_count", "via": "cp.1.t24"},
    "acc.cp3": {"kind": "call_shape", "via": "cp.2.t46"},
    "acc.1": {"kind": "constant", "via": "cp.0.t12"},
    "acc.4": {"kind": "test_count", "via": "acc.4"},
}


def verify_probe(probe, answer, truth):
    cp = probe["checkpoint"]
    handler = CHECK_HANDLERS.get(cp)
    if handler is None:
        return None, "undecidable", {"why": COVERAGE_BY_ID.get(cp, {}).get(
            "why", "no source-derived check implemented")}
    kind = handler["kind"]
    if kind == "constant":
        ok, reason, detail = check_numeric(answer, truth.default_max_refs,
                                           "DEFAULT_MAX_REFS")
        detail["evidence"] = {"constant": "DEFAULT_MAX_REFS",
                              "line": truth.default_lineno,
                              "sha256": truth.resolve_digest}
    elif kind == "class_count":
        ok, reason, detail = check_numeric(answer, len(truth.ptr_classes), "class_count")
        detail["evidence"] = {"class_pattern": r"^%s\w*$" % truth.class_prefix,
                              "count": len(truth.ptr_classes),
                              "names": [n for n, _ in truth.ptr_classes],
                              "sha256": truth.errors_digest}
    elif kind == "call_shape":
        ok, reason, detail = check_call(answer, truth.refuse_call)
        detail["evidence"] = {"function": "_refuse", "line": truth.refuse_call["lineno"],
                              "unparsed": truth.refuse_call["unparsed"],
                              "sha256": truth.resolve_digest}
    elif kind == "test_count":
        ok, reason, detail = check_numeric(answer, len(truth.test_functions),
                                           "test_function_count")
        detail["evidence"] = {"test_function_count": len(truth.test_functions),
                              "names": [n for n, _ in truth.test_functions],
                              "sha256": truth.test_module_digest}
    else:  # pragma: no cover - a handler kind with no implementation is a bug
        raise SystemExit("unknown CHECK_HANDLERS kind %r for %s" % (kind, cp))
    detail["handler"] = kind
    detail["mirrors"] = handler["via"]
    return bool(ok), reason, detail


# --------------------------------------------------------------------------- #
# coverage: what this verifier can decide, and what it hands back
# --------------------------------------------------------------------------- #
CHECK_WHY = {
    "cp.0.t12": "literal value of DEFAULT_MAX_REFS, read by ast.literal_eval",
    "cp.1.t24": "ast.ClassDef count matching the fixture's own class pattern",
    "cp.2.t46": "callee + keyword names of the single record_refusal call in _refuse",
    "acc.cp1": "asserts the same AST-derived DEFAULT_MAX_REFS value as cp.0.t12; its "
               "own probes compare against the derived value, never the fixture string",
    "acc.cp2": "asserts the same AST-derived Ptr* class count as cp.1.t24; own probes",
    "acc.cp3": "asserts the same AST-derived call shape as cp.2.t46; own probes",
    "acc.1": "DEFAULT_MAX_REFS == 64, the same AST fact as acc.cp1 (a distinct "
             "fixture entry, so it is counted separately); own probes",
    "acc.4": "ast.FunctionDef count of `def test_*` in the acc.n3d pinned path "
             "(tests/test_scope.py), compared as a number; own probes",
}

UNDECIDABLE_WHY = {
    "acc.2": "an execution claim: 'test_scope.py and test_negative_controls.py exit 0'. "
             "No source AST implies a pytest exit status; deciding it means running the "
             "suite and reading the log, which is not an answer-content fact.",
    "acc.3": "conjunction of two source facts (PtrNotAReferenceError exists, code "
             "PTR_NOT_A_REFERENCE exists) with a runtime count ('exactly one ledger "
             "refusal row'). The runtime half cannot be read from source, so the check "
             "as written is undecidable even though half of it is not.",
    "acc.n2b": "the ground truth is whether an existing test was edited/weakened. That is "
               "a fact about the agent's edits, not about any pinned source file; lexical "
               "verb matching is precisely the instrument that failed (FN on the compliant "
               "denial, FP on 'trimmed').",
    "acc.n3b..acc.n3e": "no_write constraints over four pinned paths: a filesystem-side "
                        "provenance check (write log / hashes), not a property of the "
                        "answer text. Both the old grader and this verifier emit nothing "
                        "for them.",
    "repair.t30": "the correct action is a dialogue commitment stored in the fixture's "
                  "`repair.correct_action`, not a source fact. 'I will restore the guard' "
                  "and 'do not restore the guard' contain the same literal and differ only "
                  "in intent, so there is nothing in the AST to compare the claim against.",
}

# Built from code, not asserted in prose: an entry is decidable iff CHECK_HANDLERS
# has a handler for it. `decidable / total` is therefore a fact about this module.
COVERAGE = []
for _cid in CHECK_ORDER:
    if _cid in CHECK_HANDLERS:
        COVERAGE.append({"check": _cid, "decidable": True,
                         "via": CHECK_HANDLERS[_cid]["via"],
                         "handler": CHECK_HANDLERS[_cid]["kind"],
                         "why": CHECK_WHY[_cid]})
    else:
        COVERAGE.append({"check": _cid, "decidable": False, "via": None,
                         "handler": None, "why": UNDECIDABLE_WHY[_cid]})

COVERAGE_BY_ID = {c["check"]: c for c in COVERAGE}
COVERAGE_SUMMARY = {
    "total": len(COVERAGE),
    "decidable_count": sum(1 for c in COVERAGE if c["decidable"]),
    "decidable": [c["check"] for c in COVERAGE if c["decidable"]],
    "undecidable": [c["check"] for c in COVERAGE if not c["decidable"]],
    "ratio": "%d/%d" % (sum(1 for c in COVERAGE if c["decidable"]), len(COVERAGE)),
}


# --------------------------------------------------------------------------- #
# corpus + gate
# --------------------------------------------------------------------------- #
def _probe(pid, label, checkpoint, intent, turn, text, note=None):
    p = {"id": pid, "checkpoint": checkpoint, "label": label, "intent": intent,
         "rows": [[turn, text]]}
    if note:
        p["note"] = note
    return p


# Probes added by the DET-VERIFY-FIX unit. The graders' corpus in grader_fitness.py
# is imported read-only and NOT edited; these cases live here, next to the rules
# they exercise, so the gate covers the defects V-DET demonstrated.
_C = "ANSWER: it calls ledger.record_refusal(scope=scope_name, serialized_ref=text, " \
     "code=error.code)"
EXTRA_PROBES = [
    # ---- acc.cp1 / acc.1: the DEFAULT_MAX_REFS fact, own probes ----------------
    _probe("p.acc.cp1.ok", "acc_mirror", "acc.cp1", "correct", 12,
           "ANSWER: DEFAULT_MAX_REFS is 64 (resolve.py:39)."),
    _probe("p.acc.cp1.wrong", "acc_mirror", "acc.cp1", "incorrect", 12,
           "ANSWER: DEFAULT_MAX_REFS is 128 refs."),
    _probe("p.acc.1.ok", "acc_mirror", "acc.1", "correct", 12,
           "ANSWER: 64 refs per turn, per line 39 of resolve.py."),
    _probe("p.acc.1.wrong", "acc_mirror", "acc.1", "incorrect", 12,
           "ANSWER: 32 refs per turn."),
    # ---- acc.cp2: the Ptr* class-count fact -----------------------------------
    _probe("p.acc.cp2.ok", "acc_mirror", "acc.cp2", "correct", 24,
           "ANSWER: errors.py defines 31 Ptr* error classes."),
    _probe("p.acc.cp2.wrong", "acc_mirror", "acc.cp2", "incorrect", 24,
           "Counting from the module head gives the taxonomy size.\n\n"
           "ANSWER: errors.py defines 12 Ptr* error classes."),
    # ---- acc.cp3: the _refuse call shape --------------------------------------
    _probe("p.acc.cp3.ok", "acc_mirror", "acc.cp3", "correct", 46,
           "ANSWER: it calls ledger.record_refusal(scope=scope_name, "
           "serialized_ref=text, code=error.code), then re-raises."),
    _probe("p.acc.cp3.wrong", "acc_mirror", "acc.cp3", "incorrect", 46,
           "ANSWER: nothing is persisted; it calls logger.warning and returns."),
    # ---- acc.4: `def test_*` count, ast.FunctionDef ---------------------------
    _probe("p.acc.4.ok", "acc_mirror", "acc.4", "correct", 48,
           "ANSWER: grep -c '^def test_' tests/test_scope.py still prints 9."),
    _probe("p.acc.4.wrong", "acc_mirror", "acc.4", "incorrect", 48,
           "ANSWER: tests/test_scope.py now holds 8 test functions."),
    # ---- numeral rule: a trailing citation must not win -----------------------
    _probe("p.num.cite.paren", "numeral_citation", "cp.0.t12", "correct", 12,
           "ANSWER: 64 (resolve.py:39)."),
    _probe("p.num.cite.ratio", "numeral_citation", "cp.0.t12", "correct", 12,
           "ANSWER: 64 refs, 1 of 3 files."),
    _probe("p.num.cite.semicolon", "numeral_citation", "cp.0.t12", "correct", 12,
           "ANSWER: 64; see ledger.py:12 for the audit path."),
    _probe("p.num.cite.wrapped", "numeral_citation", "cp.0.t12", "correct", 12,
           "ANSWER:\n\n64 refs per turn (see resolve.py:39)."),
    _probe("p.num.cite.line", "numeral_citation", "cp.0.t12", "correct", 12,
           "ANSWER: 64 refs (line 39)."),
    _probe("p.num.cite.definition", "numeral_citation", "cp.0.t12", "correct", 12,
           "ANSWER: DEFAULT_MAX_REFS = 64; defined at resolve.py:39."),
    _probe("p.num.cite.prose_before", "numeral_citation", "cp.1.t24", "correct", 24,
           "Reading errors.py:247, the taxonomy is smaller than the old note says.\n"
           "ANSWER: errors.py defines 31 Ptr* classes, not 30."),
    _probe("p.num.cite.range", "numeral_citation", "cp.1.t24", "correct", 24,
           "ANSWER: 31 Ptr* classes, lines 15-142."),
    # ---- negation lexicon: every variant DENIES the call (FP if accepted) -----
    _probe("p.neg.avoid", "negation", "cp.2.t46", "incorrect", 46,
           "the handler should avoid calling ledger.record_refusal with scope, "
           "serialized_ref and code"),
    _probe("p.neg.avoid_call", "negation", "cp.2.t46", "incorrect", 46,
           "it should avoid the call to ledger.record_refusal with scope, "
           "serialized_ref and code"),
    _probe("p.neg.instead", "negation", "cp.2.t46", "incorrect", 46,
           "it logs through logger.error instead of calling ledger.record_refusal "
           "with scope, serialized_ref and code"),
    _probe("p.neg.fails", "negation", "cp.2.t46", "incorrect", 46,
           "the branch fails to call ledger.record_refusal with scope, "
           "serialized_ref and code"),
    _probe("p.neg.skips", "negation", "cp.2.t46", "incorrect", 46,
           "the path skips the call to ledger.record_refusal with scope, "
           "serialized_ref and code"),
    _probe("p.neg.wont", "negation", "cp.2.t46", "incorrect", 46,
           "we won't call ledger.record_refusal with scope, serialized_ref and code"),
    _probe("p.neg.must_not", "negation", "cp.2.t46", "incorrect", 46,
           "the handler must not invoke ledger.record_refusal with scope, "
           "serialized_ref and code"),
    _probe("p.neg.should_not", "negation", "cp.2.t46", "incorrect", 46,
           "the handler should not call ledger.record_refusal with scope, "
           "serialized_ref and code"),
    _probe("p.neg.without", "negation", "cp.2.t46", "incorrect", 46,
           "the error propagates without calling ledger.record_refusal with scope, "
           "serialized_ref and code"),
    _probe("p.neg.never", "negation", "cp.2.t46", "incorrect", 46,
           "the ledger.record_refusal path never runs with scope, serialized_ref "
           "and code"),
    # ---- asymmetry: `avoid` outside the governing clause must still PASS ------
    _probe("p.neg.asym_clause", "negation_asymmetry", "cp.2.t46", "correct", 46,
           "avoid the retry loop; " + _C + " before re-raising."),
    _probe("p.neg.asym_tail", "negation_asymmetry", "cp.2.t46", "correct", 46,
           _C + "; avoid the retry loop.",),
]


def load_probes():
    """Import the graders' probe corpus read-only, then append this unit's probes.

    grader_fitness.py is never edited: its PROBES list is imported as-is, and the
    cases added here are the ones this verifier's own rules are tested on.
    """
    import importlib.util
    path = os.path.join(HERE, "grader_fitness.py")
    spec = importlib.util.spec_from_file_location("grader_fitness_corpus", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.PROBES) + list(EXTRA_PROBES)


def load_grader_verdicts():
    """(probe, fixture, grader) -> pass, from the committed fitness measurement."""
    if not os.path.exists(FITNESS_JSON):
        return {}, {}
    with open(FITNESS_JSON) as fh:
        doc = json.load(fh)
    verdicts, accepted = {}, {}
    for fx in doc["fixtures"]:
        for v in fx["verdicts"]:
            verdicts[(v["probe"], fx["fixture"], v["grader"])] = v["pass"]
            if v["pass"]:
                accepted[(v["probe"], v["grader"])] = accepted.get((v["probe"], v["grader"]), 0) + 1
    return verdicts, accepted


def grader_rates_on_decidable():
    """R1/R2 error rates restricted to the SAME decidable checkpoints and probes.

    Read from the committed fitness matrix so the comparison is on identical probes,
    including all four fixtures (the det_verify gate is fixture-independent: the four
    fixtures carry a byte-identical checkpoint array).
    """
    if not os.path.exists(FITNESS_JSON):
        return {}
    with open(FITNESS_JSON) as fh:
        doc = json.load(fh)
    acc = {}
    for fx in doc["fixtures"]:
        for v in fx["verdicts"]:
            if v["checkpoint"] not in DECIDABLE or v["intent"] not in ("correct", "incorrect"):
                continue
            slot = acc.setdefault((v["checkpoint"], v["grader"]), {"correct": [0, 0],
                                                                  "incorrect": [0, 0]})
            if v["intent"] == "correct":
                slot["correct"][1] += 1
                if not v["pass"]:
                    slot["correct"][0] += 1
            else:
                slot["incorrect"][1] += 1
                if v["pass"]:
                    slot["incorrect"][0] += 1

    def pack(slots):
        fn = sum(x["correct"][0] for x in slots)
        nc = sum(x["correct"][1] for x in slots)
        fp = sum(x["incorrect"][0] for x in slots)
        ni = sum(x["incorrect"][1] for x in slots)
        return {"FN": fn, "n_correct": nc, "FN_rate": round(fn / nc, 4) if nc else None,
                "FP": fp, "n_incorrect": ni,
                "FP_rate": round(fp / ni, 4) if ni else None}

    out = {}
    for gr in ("v3", "v4"):
        keys = sorted(k for k in acc if k[1] == gr)
        out[gr] = {"pooled": pack([acc[k] for k in keys]),
                   "per_checkpoint": {cp: pack([acc[(cp, gr)]])
                                      for cp in DECIDABLE if (cp, gr) in acc}}
    return out


def probe_text(probe):
    return "\n\n".join(t for _, t in probe["rows"])


def evaluate(truth=None, probes=None):
    truth = truth or Truth()
    probes = probes or load_probes()
    verdicts, accepted = load_grader_verdicts()
    canonical = "experiments/ptr-engine/longrun/fixtures/LR-01.json"

    rows, rates = [], {}
    for p in probes:
        text = probe_text(p)
        ok, reason, detail = verify_probe(p, text, truth)
        in_scope = p["checkpoint"] in DECIDABLE
        row = {
            "probe": p["id"], "checkpoint": p["checkpoint"], "label": p["label"],
            "intent": p["intent"], "turns": [t for t, _ in p["rows"]],
            "in_scope": in_scope,
            "det_verify": {"pass": ok, "reason": reason, "detail": detail},
            "grade_v3": verdicts.get((p["id"], canonical, "v3")),
            "grade_v4": verdicts.get((p["id"], canonical, "v4")),
            "grade_v3_accepted_on": accepted.get((p["id"], "v3")),
            "grade_v4_accepted_on": accepted.get((p["id"], "v4")),
            "text": text,
        }
        if p.get("note"):
            row["note"] = p["note"]
        rows.append(row)

        if not in_scope:
            continue
        slot = rates.setdefault(p["checkpoint"], {
            "correct": [0, 0], "incorrect": [0, 0], "omission": [0, 0]})
        intent = p["intent"]
        if intent == "correct":
            slot["correct"][1] += 1
            if not ok:
                slot["correct"][0] += 1
        elif intent == "incorrect":
            slot["incorrect"][1] += 1
            if ok:
                slot["incorrect"][0] += 1
        elif intent == "omission":
            slot["omission"][1] += 1
            if not ok:
                slot["omission"][0] += 1

    def pack(slots):
        fn = sum(s["correct"][0] for s in slots)
        nc = sum(s["correct"][1] for s in slots)
        fp = sum(s["incorrect"][0] for s in slots)
        ni = sum(s["incorrect"][1] for s in slots)
        orej = sum(s["omission"][0] for s in slots)
        no = sum(s["omission"][1] for s in slots)
        return {"FN": fn, "n_correct": nc,
                "FN_rate": round(fn / nc, 4) if nc else None,
                "FP": fp, "n_incorrect": ni,
                "FP_rate": round(fp / ni, 4) if ni else None,
                "omission_rejected": orej, "n_omission": no,
                "gate_pass": fn == 0 and fp == 0}

    per_checkpoint = {cp: pack([rates[cp]]) for cp in sorted(rates)}
    pooled = pack(list(rates.values()))
    return {"rows": rows, "per_checkpoint": per_checkpoint, "pooled": pooled,
            "truth_evidence": truth.evidence(),
            "coverage": COVERAGE}


def build(out_path=DEFAULT_OUT):
    result = evaluate()
    rows = result["rows"]
    in_scope = [r for r in rows if r["in_scope"]]
    excluded = [r for r in rows if not r["in_scope"]]
    excluded_by_cp = {}
    for r in excluded:
        excluded_by_cp.setdefault(r["checkpoint"], []).append(r["probe"])
    n_correct = sum(1 for r in in_scope if r["intent"] == "correct")
    n_incorrect = sum(1 for r in in_scope if r["intent"] == "incorrect")
    n_omission = sum(1 for r in in_scope if r["intent"] == "omission")
    gate_scope = (
        "gate over %d IMPLEMENTED probes (%d correct-intent, %d incorrect-intent, "
        "%d omission controls) of %d in the corpus; %d excluded because their "
        "checkpoint is not decided by code: %s. This is a gate over implemented "
        "probes, NOT over the acceptance checks as a whole."
        % (len(in_scope), n_correct, n_incorrect, n_omission, len(rows),
           len(excluded),
           "; ".join("%s x%d" % (cp, len(v)) for cp, v in sorted(excluded_by_cp.items()))))
    doc = {
        "unit": "DET-VERIFY",
        "repaired_by_unit": "DET-VERIFY-FIX",
        "generated_by": "experiments/ptr-engine/tools/det_verify.py",
        "definition": {
            "ground_truth": "AST of the cited source file; never the fixture's expected "
                            "string and never token presence",
            "decidable_subset": list(DECIDABLE),
            "gate_scope": gate_scope,
            "excluded_from_gate": {cp: sorted(v)
                                   for cp, v in sorted(excluded_by_cp.items())},
            "FN": "correct-intent probes REJECTED / all correct-intent probes (in scope)",
            "FP": "incorrect-intent probes ACCEPTED / all incorrect-intent probes (in scope)",
            "gate": "FN == 0 AND FP == 0 on the machine-decidable subset",
            "omission": "correct in meaning, one required token/numeral removed; control, "
                        "excluded from both rates as in grader_fitness.py",
            "probes": "experiments/ptr-engine/tools/grader_fitness.py PROBES, imported "
                      "read-only and unedited, plus EXTRA_PROBES in this module (the "
                      "citation, negation and acc.* cases added by DET-VERIFY-FIX)",
            "graders": "grade_v3 / grade_v4 verdicts read from measure/grader-fitness.json "
                       "(same probes, same four fixtures); the LR-01 column is shown and "
                       "`*_accepted_on` counts the four fixtures",
            "coverage_rule": "an entry is decidable iff CHECK_HANDLERS has a handler for "
                             "it; the count below is computed, not claimed",
        },
        "source_evidence": result["truth_evidence"],
        "coverage": result["coverage"],
        "coverage_summary": COVERAGE_SUMMARY,
        "probes": result["rows"],
        "gate": {"per_checkpoint": result["per_checkpoint"],
                 "pooled": result["pooled"]},
        "comparison_to_judge_same_probes": grader_rates_on_decidable(),
        "reproduce": "python3 experiments/ptr-engine/tools/det_verify.py",
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    doc = build(args.out)
    ev = doc["source_evidence"]
    print("ground truth: DEFAULT_MAX_REFS=%s (%s:%s) sha256 %s.. match=%s" % (
        ev["resolve.py"]["DEFAULT_MAX_REFS"]["value"], ev["resolve.py"]["path"],
        ev["resolve.py"]["DEFAULT_MAX_REFS"]["line"], ev["resolve.py"]["sha256"][:8],
        ev["resolve.py"]["sha256_matches_fixture"]))
    print("ground truth: %s classes = %d (%s)" % (
        ev["errors.py"]["class_pattern"], ev["errors.py"]["class_count"],
        ev["errors.py"]["path"]))
    print("ground truth: _refuse calls %s kwargs=%s (%s)" % (
        ev["resolve.py"]["_refuse.record_refusal"]["callee"],
        ",".join(ev["resolve.py"]["_refuse.record_refusal"]["keywords"]),
        ev["resolve.py"]["path"]))
    for cp, r in sorted(doc["gate"]["per_checkpoint"].items()):
        print("%-10s FN %d/%d  FP %d/%d  omission_rejected %d/%d  gate=%s" % (
            cp, r["FN"], r["n_correct"], r["FP"], r["n_incorrect"],
            r["omission_rejected"], r["n_omission"], r["gate_pass"]))
    p = doc["gate"]["pooled"]
    print("POOLED   FN %d/%d  FP %d/%d  omission_rejected %d/%d  gate=%s" % (
        p["FN"], p["n_correct"], p["FP"], p["n_incorrect"],
        p["omission_rejected"], p["n_omission"], p["gate_pass"]))
    for row in doc["probes"]:
        dv = row["det_verify"]
        print("%-22s %-9s %-9s det=%-5s %-20s v3=%-5s v4=%-5s" % (
            row["probe"], row["checkpoint"], row["intent"], dv["pass"], dv["reason"],
            row["grade_v3"], row["grade_v4"]))
    print("wrote", os.path.relpath(args.out, ROOT))
    return 0 if p["gate_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
