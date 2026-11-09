#!/usr/bin/env python3
"""fixture_coverage.py - the gate a checkpoint fixture must pass before it is run.

WHY THIS EXISTS. `orchestration/handoffs/EVAL-PRACTICE-SURVEY.json` measured that the
v5 fixture carries 3 decidable checkpoints, which caps an arm comparison at b+c=3
discordant pairs and exact McNemar two-sided p=0.25 - no ranking at any number of
repeats. Expanding to 12 checkpoints only helps if each of the 12 is DECIDABLE: a
checkpoint whose answer lies outside the pinned range, whose truth is hand-typed, or
whose truth value also sits somewhere else in the pinned range is a checkpoint that
a wrong answer can pass. That defect class already cost this project three rounds
(`resolve.py` pinned L66-110 while `DEFAULT_MAX_REFS` lives at L39).

WHAT IT CHECKS, per checkpoint, all four measured from the pinned tree (never from
the fixture's own `expected` string, which is documentation):

  answerable_from_pinned_range
      the AST node(s) that establish the truth fall inside the source range the
      checkpoint declares (`checkpoints[].source` = `<path>#L<a>-L<b>`), AND the
      evidence text is present in the pinned body the model is shown
      (`items[].body`). A truth outside the range is the historical defect.

  truth (AST-derived)
      via `experiments/ptr-engine/tools/det_verify.py` - the same extraction
      `grade_v5.py` uses - plus two rules grade_v5 does not yet dispatch:
        constant_value                  module-level `NAME = <int>`      -> NUM
        count_classes                   len of `class <regex>:`          -> NUM
        call_inside_function            callee + kwargs of one call      -> CALL
        call_at_line                    callee + kwargs at one line      -> CALL
        no_attr_call_inside_function    absence of `x.<attr>(` in fn      -> NONE
      The fixture's documented `expected` is compared with the derivation and a
      divergence is a failure (never graded against stale prose).

  expected_tokens
      tiktoken cl100k_base tokens of the contracted answer line
      `ANSWER: <KIND> <expected>` (whitespace count when tiktoken is absent).
      >40 tokens is a failure: the contract is one short line, and a long CALL
      turns a knowledge checkpoint into a transcription test.

  collision
      does the truth value also appear elsewhere in the checkpoint's pinned range,
      so that a wrong answer would pass?
        NUM  - the numeral occurs more than once as a standalone token in the range
               (a model can lift a numeral it read instead of deriving it).
        CALL - the same callee appears in the range with two DIFFERENT keyword
               sets (a neighbour's argument list would look right). Repeated
               identical sites are reported as `sites` but are not a collision:
               every one of them yields the same answer, so no wrong answer passes.
        NONE - the absent attribute call DOES occur in the range (the absence does
               not hold where the question is asked).
      Two checkpoints deriving the same truth are also a collision: 12 items that
      decide 9 facts buy 9 discordant pairs, not 12.

EXIT CODE
  0  every checkpoint passed; the fixture may be run.
  1  at least one checkpoint failed one of the four checks, or a kind/rules is not
     one this gate can derive, or a `TEXT` item is present (grade_v5 refuses TEXT).

    python3 experiments/ptr-engine/tools/fixture_coverage.py \
        --fixture experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json

Offline. Stdlib only (+ det_verify). Reads the fixture and the pinned sources;
writes nothing.
"""
import argparse
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))          # .../experiments/ptr-engine -> repo
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import det_verify as dv                                 # noqa: E402  (canonical AST helpers)

MAX_EXPECTED_TOKENS = 40
PIN_RE = re.compile(r"^#L(\d+)(?:-L?(\d+))?$")
KINDS = ("NUM", "CALL", "NONE")
RULES = ("constant_value", "count_classes", "call_inside_function",
         "call_at_line", "no_attr_call_inside_function")


# --------------------------------------------------------------------- helpers
def _resolve(path, engine_root):
    """Fixture paths are repo-relative; fall back to engine-root-relative."""
    if os.path.isabs(path):
        return path
    cand = os.path.join(dv.ROOT, path)
    if os.path.exists(cand):
        return cand
    return os.path.join(engine_root, path)


def _pointer_range(pointer):
    m = PIN_RE.match(pointer or "")
    if not m:
        return None
    lo = int(m.group(1))
    hi = int(m.group(2) or m.group(1))
    return (lo, hi)


def _read_lines(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8").splitlines(True)


def _range_text(lines, rng):
    if rng is None:
        return "".join(lines)
    lo, hi = rng
    return "".join(lines[lo - 1:hi])


def _tokens(text):
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return len(text.split())


def _answer_line(kind, expected):
    return "ANSWER: %s %s" % (kind, expected)


def _call_sig(node):
    return " ".join(ast.unparse(node).split())


def _fmt_call(callee, kwargs):
    """`callee(kw=value, ...)` with kwargs in alphabetical order."""
    inner = ", ".join("%s=%s" % (k, " ".join(str(v).split())) for k, v in sorted(kwargs.items()))
    return "%s(%s)" % (callee, inner)


def _doc_call(text):
    """(callee, {kwarg: value}) from a documented CALL string - grade_v5's rule.

    `...` as a value is a DECLARED elision (v5 precedent: `scope=...`): the exact
    source text is not part of the question, so it is not compared.
    """
    text = str(text)
    start, end = text.find("("), text.rfind(")")
    if start < 0 or end < start:
        return None, None
    callee = text[:start].strip().split()[-1]
    kwargs, depth, cur = {}, 0, []
    parts = []
    for ch in text[start + 1:end]:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    for item in parts:
        name, sep, value = item.partition("=")
        if not sep:
            return callee, None
        kwargs[name.strip()] = " ".join(value.split())
    return callee, kwargs


def documented_matches_call(documented, truth):
    """Is the fixture's documented CALL the AST truth, allowing `...` elisions?"""
    callee, kwargs = _doc_call(documented)
    if kwargs is None:
        return False
    t_callee, t_kwargs = _doc_call(truth)
    if _norm(callee) != _norm(t_callee):
        return False
    if set(kwargs) != set(t_kwargs):
        return False
    for name, value in kwargs.items():
        if value == "...":
            continue
        if _norm(value) != _norm(t_kwargs[name]):
            return False
    return True


def _norm(text):
    return " ".join(str(text or "").split())


# ------------------------------------------------------------------- derivation
def derive(spec, trees, fixture, engine_root):
    """(truth, kind, lines, evidence_hint) from one checkpoint's `answer_spec`."""
    kind = (spec or {}).get("kind")
    d = (spec or {}).get("derive") or {}
    rule = d.get("rule")
    if kind == "TEXT":
        return None, "TEXT", [], "TEXT is refused by grade_v5"
    if rule not in RULES:
        return None, kind, [], "unknown derive rule %r" % (rule,)
    path = _resolve(d.get("file") or "", engine_root)
    tree = trees.get(path)
    if tree is None:
        tree, _sha = dv.parse_module(path)
        trees[path] = tree
    if rule == "constant_value":
        value, lineno = dv.constant_value(tree, d["symbol"])
        return value, "NUM", [lineno], "%s = %s" % (d["symbol"], value)
    if rule == "count_classes":
        names = dv.count_classes(tree, d["pattern"])
        lines = [ln for _, ln in names]
        return len(names), "NUM", sorted(lines), "class <regex %s> count" % d["pattern"]
    if rule == "call_inside_function":
        call = dv.call_inside_function(tree, d["function"], d["attr"])
        return call["unparsed"], "CALL", [call["lineno"]], call["unparsed"]
    if rule == "call_at_line":
        lineno = int(d["line"])
        hits = [s for s in ast.walk(tree) if isinstance(s, ast.Call)
                and isinstance(s.func, ast.Attribute) and s.lineno == lineno]
        if len(hits) != 1:
            raise SystemExit("call_at_line: expected exactly one attribute call at %s:%d, found %d"
                             % (d["file"], lineno, len(hits)))
        return _call_sig(hits[0]), "CALL", [lineno], _call_sig(hits[0])
    # no_attr_call_inside_function
    fn = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == d["function"]:
            fn = node
    if fn is None:
        raise SystemExit("function %r not found in %s" % (d["function"], d["file"]))
    found = [s for s in ast.walk(fn) if isinstance(s, ast.Call)
             and isinstance(s.func, ast.Attribute) and s.func.attr == d["attr"]]
    if len(found) != 0:
        return "NONE", "NONE", [s.lineno for s in found], "absence does not hold"
    return "NONE", "NONE", [], "no `.%s(` call inside `%s`" % (d["attr"], d["function"])


# ----------------------------------------------------------------------- checks
def check_fixture(fixture_path, engine_root=None, quiet=False):
    """Rows + failures for one fixture. Never writes, never runs a model."""
    engine_root = engine_root or os.path.join(dv.ROOT, "experiments", "ptr-engine")
    with open(fixture_path) as fh:
        fixture = json.load(fh)
    items = {it.get("id"): it for it in fixture.get("items") or []}
    src_by_id = {}
    for s in fixture.get("sources") or []:
        sid = s.get("id") or os.path.basename(s.get("path") or "")
        src_by_id[sid] = s
    file_cache, trees = {}, {}
    rows, failures = [], []

    for idx, cp in enumerate(fixture.get("checkpoints") or []):
        cid = str(cp.get("id") or "cp.%d" % idx)
        turn = int(cp.get("turn", -1))
        spec = cp.get("answer_spec") or {}
        declared = cp.get("source") or ""
        path_part, _, ptr = declared.partition("#")
        ptr = "#" + ptr if ptr else ""
        path_abs = _resolve(path_part, engine_root) if path_part else ""
        rng = _pointer_range(ptr)
        lines = None
        if path_abs and os.path.exists(path_abs):
            if path_abs not in file_cache:
                file_cache[path_abs] = _read_lines(path_abs)
            lines = file_cache[path_abs]
        pinned_body = ""
        item = items.get(os.path.basename(path_part))
        if item is not None and item.get("body"):
            pinned_body = item["body"]

        row = {"id": cid, "turn": turn, "kind": spec.get("kind"), "source": declared,
               "answerable": False, "truth": None, "tokens": None,
               "tokens_ws": None, "collision": False, "reason": "", "sites": None}

        # --- truth (AST-derived; the fixture's `expected` is documentation) ---
        try:
            truth, kind, node_lines, hint = derive(spec, trees, fixture, engine_root)
        except SystemExit as exc:
            row["reason"] = "derive: %s" % exc
            failures.append((cid, row["reason"]))
            rows.append(row)
            continue
        row["truth"] = truth
        row["kind"] = kind
        documented = cp.get("expected")
        if kind == "TEXT":
            row["reason"] = "kind TEXT is refused by grade_v5"
            failures.append((cid, row["reason"]))
            rows.append(row)
            continue
        if kind not in KINDS:
            row["reason"] = "kind %r is not one of %s" % (kind, ", ".join(KINDS))
            failures.append((cid, row["reason"]))
            rows.append(row)
            continue
        row["expected_documented"] = documented
        answer_form = truth
        if documented is not None:
            if kind == "CALL":
                ok_doc = documented_matches_call(documented, truth)
            else:
                ok_doc = str(documented).strip() == str(truth).strip()
            if ok_doc:
                # the documented form is the one the fixture declares gradeable
                # (a `...` value is a declared elision, not part of the answer)
                answer_form = documented
            if not ok_doc:
                row["reason"] = "documented expected %r != AST truth %r" % (documented, truth)
                failures.append((cid, row["reason"]))
                rows.append(row)
                continue

        # --- answerable from the pinned range -------------------------------
        # the derivation must come from the file the checkpoint cites, and its AST
        # node(s) must sit inside the declared range (a truth outside the range is
        # the resolve.py L39 defect that already cost this project three rounds).
        derive_file = _resolve((spec.get("derive") or {}).get("file") or path_part, engine_root)
        same_file = os.path.abspath(derive_file) == os.path.abspath(path_abs) if path_abs else False
        ok_range = bool(rng and node_lines and all(rng[0] <= ln <= rng[1] for ln in node_lines))
        if not same_file:
            ok_range = False
        if kind == "NONE":
            ok_range = bool(rng) and bool(node_lines == []) or (
                bool(rng) and node_lines and all(rng[0] <= ln <= rng[1] for ln in node_lines))
        evidence_in_body = True
        if pinned_body:
            if kind == "NUM" and isinstance(truth, int):
                evidence_in_body = bool(re.search(r'(?<![\w.])%d(?![\w.])' % truth, pinned_body)) or \
                    hint.startswith("class ")
            elif kind == "CALL":
                evidence_in_body = truth.split("(")[0] in pinned_body
            else:
                fn = (spec.get("derive") or {}).get("function")
                evidence_in_body = quote_present(pinned_body, fn)
        row["answerable"] = bool(rng) and same_file and ok_range and evidence_in_body
        if not row["answerable"]:
            if not same_file:
                row["reason"] = ("derived from %s but the checkpoint cites %s"
                                 % (os.path.basename(derive_file), declared))
            elif not ok_range:
                row["reason"] = ("truth at %s falls outside the declared pinned range %s"
                                 % (node_lines or "?", ptr or "?"))
            else:
                row["reason"] = "evidence for the truth is absent from the pinned body"
            failures.append((cid, row["reason"]))

        # --- expected token count ------------------------------------------
        line = _answer_line(kind, answer_form)
        row["tokens"] = _tokens(line)
        row["tokens_ws"] = len(line.split())
        if row["tokens"] > MAX_EXPECTED_TOKENS:
            row["reason"] = (row["reason"] + "; " if row["reason"] else "") + \
                "expected answer is %d tokens (> %d)" % (row["tokens"], MAX_EXPECTED_TOKENS)
            failures.append((cid, "tokens %d > %d" % (row["tokens"], MAX_EXPECTED_TOKENS)))

        # --- collision inside the checkpoint's own pinned range -------------
        rg_text = _range_text(lines, rng) if lines is not None else pinned_body
        if kind == "NUM":
            n = len(re.findall(r'(?<![\w.])%s(?![\w.])' % re.escape(str(truth)), rg_text))
            row["sites"] = n
            row["collision"] = n > 1
        elif kind == "CALL":
            callee = truth.split("(")[0]
            row["sites"] = len(re.findall(re.escape(callee) + r"\s*\(", rg_text))
            sigs = set()
            for node in ast.walk(trees[path_abs]):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                        and ast.unparse(node.func) == callee:
                    sigs.add(_call_sig(node))
            row["collision"] = len(sigs) > 1
        else:
            attr = (spec.get("derive") or {}).get("attr") or ""
            n = len(re.findall(r'\.' + re.escape(attr) + r'\s*\(', rg_text))
            row["sites"] = n
            row["collision"] = n > 0
        if row["collision"]:
            row["reason"] = (row["reason"] + "; " if row["reason"] else "") + \
                "truth collides with another occurrence in the pinned range (sites=%s)" % row["sites"]
            failures.append((cid, "collision (sites=%s)" % row["sites"]))
        rows.append(row)

    # --- cross-checkpoint duplicate truths ---------------------------------
    seen = {}
    for row in rows:
        if row["truth"] is None:
            continue
        d = {}
        for cp in fixture.get("checkpoints") or []:
            if str(cp.get("id")) == row["id"]:
                d = (cp.get("answer_spec") or {}).get("derive") or {}
        key = ("NONE", d.get("function"), d.get("attr")) if row["kind"] == "NONE" \
            else (row["kind"], str(row["truth"]))
        if key in seen:
            first = seen[key]
            row["collision"] = True
            row["reason"] = (row["reason"] + "; " if row["reason"] else "") + \
                "duplicate truth of %s" % first["id"]
            failures.append((row["id"], "duplicate truth of %s" % first["id"]))
            # both items are non-discriminating, so both are flagged
            first["collision"] = True
            first["reason"] = (first["reason"] + "; " if first["reason"] else "") + \
                "duplicate truth of %s" % row["id"]
            failures.append((first["id"], "duplicate truth of %s" % row["id"]))
        else:
            seen[key] = row

    if not rows:
        failures.append(("-", "fixture declares no checkpoints"))

    if not quiet:
        print("fixture: %s" % fixture_path)
        print("engine root: %s" % engine_root)
        print("checkpoints: %d   kinds: %s" % (
            len(rows), ", ".join("%s=%d" % (k, sum(1 for r in rows if r["kind"] == k)) for k in KINDS)))
        print("")
        hdr = ("id", "turn", "kind", "answerable", "truth", "tokens", "collision", "sites")
        print("%-11s %4s %-4s %-10s %-46s %6s %-8s %5s" % hdr)
        for r in rows:
            print("%-11s %4s %-4s %-10s %-46s %6s %-8s %5s" % (
                r["id"], r["turn"], r["kind"], "YES" if r["answerable"] else "NO",
                str(r["truth"])[:46], r["tokens"], "YES" if r["collision"] else "no",
                r["sites"] if r["sites"] is not None else "-"))
        print("")
        if failures:
            print("FAIL: %d finding(s)" % len(failures))
            for cid, why in failures:
                print("  - %s: %s" % (cid, why))
        else:
            print("PASS: %d/%d checkpoints decidable, none colliding, all <= %d tokens"
                  % (len(rows), len(rows), MAX_EXPECTED_TOKENS))
    return rows, failures


def quote_present(body, fn):
    """Does the pinned body contain the function the NONE truth is about?"""
    if not fn:
        return False
    return re.search(r'def\s+%s\s*\(' % re.escape(fn), body) is not None


def main(argv=None):
    ap = argparse.ArgumentParser(description="gate a checkpoint fixture's coverage")
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--engine-root", default=None)
    ap.add_argument("--json", action="store_true", help="print rows as JSON")
    args = ap.parse_args(argv)
    rows, failures = check_fixture(args.fixture, args.engine_root, quiet=args.json)
    if args.json:
        print(json.dumps({"rows": rows, "failures": failures}, indent=1, default=str))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
