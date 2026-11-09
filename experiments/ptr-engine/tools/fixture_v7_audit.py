#!/usr/bin/env python3
"""fixture_v7_audit.py -- INDEPENDENT re-derivation of LR-01.v7.json's 12 truths.

Written for unit V-FIXTURE-V7 by the verifier, from the source files only. It does
NOT import `grade_v5`, `det_verify`, `fixture_coverage`, or any code written by
`CHECKPOINT-ITEMS-V2` / `GRADE-V6-DERIVE`. Every number below is computed here, by
walking `ast` and reading the module constants directly, and the *question -> source
fact* map is the verifier's own reading of each `question` string against the source
-- never the fixture's `answer_spec.derive`, which this tool deliberately ignores.

Exit 0 iff every id agrees (or is a declared ambiguity). Any `disagree` exits 1.
Nothing is written anywhere.

Usage:
    python3 experiments/ptr-engine/tools/fixture_v7_audit.py
    python3 experiments/ptr-engine/tools/fixture_v7_audit.py --fixture /tmp/mutated.json
    python3 experiments/ptr-engine/tools/fixture_v7_audit.py --json
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC_RESOLVE = os.path.join(ROOT, "experiments", "ptr-engine", "ptr_engine", "resolve.py")
SRC_ERRORS = os.path.join(ROOT, "experiments", "ptr-engine", "ptr_engine", "errors.py")
SRC_LEDGER = os.path.join(ROOT, "experiments", "ptr-engine", "ptr_engine", "ledger.py")
DEFAULT_FIXTURE = os.path.join(ROOT, "experiments", "ptr-engine", "longrun", "tasks-v6",
                              "LR-01.v7.json")


# ------------------------------------------------------------------ small helpers
def sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _squash(text):
    return " ".join(str(text).split())


def parse_source(path):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    return ast.parse(text), text


def function_node(tree, name):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def attr_calls(tree, function, attr):
    """Every `*.attr(...)` Call lexically inside `function` (no nesting descent into defs)."""
    fn = function_node(tree, function)
    if fn is None:
        raise SystemExit("audit_error: function %r not found" % function)
    hits = []
    for sub in ast.walk(fn):
        if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                and sub.func.attr == attr):
            hits.append(sub)
    return sorted(hits, key=lambda n: (getattr(n, "lineno", 0), getattr(n, "col_offset", 0)))


def name_calls(tree, function, name):
    """Every bare `name(...)` Call inside `function` (the `_refuse(...)` shape)."""
    fn = function_node(tree, function)
    if fn is None:
        raise SystemExit("audit_error: function %r not found" % function)
    return sorted([sub for sub in ast.walk(fn)
                   if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                   and sub.func.id == name],
                  key=lambda n: n.lineno)


def call_render(node):
    """(callee, {kwarg: value_text}, [kwarg in source order]) straight off the AST."""
    callee = ast.unparse(node.func)
    kwargs, order = {}, []
    for kw in node.keywords:
        if kw.arg is None:
            raise SystemExit("audit_error: **kwargs splat at L%d" % node.lineno)
        kwargs[kw.arg] = _squash(ast.unparse(kw.value))
        order.append(kw.arg)
    return callee, kwargs, order


def module_constant(tree, symbol):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == symbol:
                    return ast.literal_eval(node.value), node.lineno
    raise SystemExit("audit_error: constant %r not found" % symbol)


def class_names(tree):
    return [(n.name, n.lineno) for n in tree.body if isinstance(n, ast.ClassDef)]


# ------------------------------------------------- documented-expected -> structure
def split_args(argtext):
    """Split on top-level commas, honouring quotes and bracket depth."""
    parts, cur, depth, quote, esc = [], [], 0, None, False
    for ch in argtext:
        if esc:
            cur.append(ch)
            esc = False
            continue
        if quote:
            if ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            cur.append(ch)
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
    return [p for p in parts if p]


KWARG_RE = re.compile(r"^([A-Za-z_]\w*)\s*=\s*(.*)$", re.S)


def documented_call(expected):
    """(callee, {kw: value}, trailing_text) from the fixture's human `expected`.

    Written as its own balanced-paren scan so that a documentation string carrying
    prose *after* the call (cp.11.t46 does) is reported as `trailing_text` rather
    than silently swallowing it.
    """
    text = str(expected)
    start = text.find("(")
    if start < 0:
        raise SystemExit("audit_error: documented CALL has no '(' : %r" % text)
    depth, end, quote, esc = 0, None, None, False
    for i in range(start, len(text)):
        ch = text[i]
        if esc:
            esc = False
            continue
        if quote:
            if ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise SystemExit("audit_error: documented CALL unbalanced: %r" % text)
    callee = _squash(text[:start])
    if " " in callee:
        callee = callee.split()[-1]
    kwargs = {}
    for item in split_args(text[start + 1:end]):
        m = KWARG_RE.match(item)
        if not m:
            raise SystemExit("audit_error: documented arg not a kwarg: %r" % item)
        kwargs[m.group(1)] = _squash(m.group(2))
    return callee, kwargs, text[end + 1:].strip()


# ------------------------------------------------------- the 12 independent truths
def derive_all():
    """{id: {kind, value|present, evidence, source, line}} -- the verifier's own map.

    The id -> source-fact binding is read off each `question` and the source; the
    fixture's `answer_spec` is never consulted.
    """
    rt, _ = parse_source(SRC_RESOLVE)
    et, _ = parse_source(SRC_ERRORS)
    out = {}

    # T6  "What does resolve() call when it records a successful resolution, and
    #      which keyword arguments does it pass?"  -> the recording call in resolve()
    hits = attr_calls(rt, "resolve", "record_resolution")
    if len(hits) != 1:
        raise SystemExit("audit_error: resolve() has %d record_resolution calls" % len(hits))
    callee, kwargs, order = call_render(hits[0])
    out["cp.0.t06"] = {
        "kind": "CALL", "callee": callee, "kwargs": kwargs, "source_order": order,
        "evidence": "resolve.py:%d ast.Call inside resolve() -> %s"
                    % (hits[0].lineno, ast.unparse(hits[0])),
        "source": "resolve.py", "line": hits[0].lineno,
    }

    # T8  "Which scope method does resolve() call to read the cache block size for
    #      the ledger row?" -> scope.<method>() inside resolve()
    hits = attr_calls(rt, "resolve", "block")
    if len(hits) != 1:
        raise SystemExit("audit_error: resolve() has %d block() calls" % len(hits))
    callee, kwargs, order = call_render(hits[0])
    out["cp.1.t08"] = {
        "kind": "CALL", "callee": callee, "kwargs": kwargs, "source_order": order,
        "evidence": "resolve.py:%d ast.Call inside resolve() -> %s"
                    % (hits[0].lineno, ast.unparse(hits[0])),
        "source": "resolve.py", "line": hits[0].lineno,
    }

    # T12 "What is the default per-turn resolve budget in refs?" -> DEFAULT_MAX_REFS
    value, line = module_constant(rt, "DEFAULT_MAX_REFS")
    out["cp.2.t12"] = {
        "kind": "NUM", "value": int(value),
        "evidence": "resolve.py:%d ast.Assign DEFAULT_MAX_REFS = %d" % (line, int(value)),
        "source": "resolve.py", "line": line,
    }

    # T14 "Does resolve() itself call ledger.record_refusal()?" -> absence inside resolve()
    hits = attr_calls(rt, "resolve", "record_refusal")
    out["cp.3.t14"] = {
        "kind": "NONE", "absent": not hits,
        "evidence": ("resolve.py: resolve() calls no *.record_refusal; its only "
                     "ledger-touching calls are the bare _refuse(...) at L%d and "
                     "ledger.record_resolution at L%d (indirect, via _refuse)"
                     % (name_calls(rt, "resolve", "_refuse")[0].lineno,
                        attr_calls(rt, "resolve", "record_resolution")[0].lineno))
        if not hits else "resolve.py:%d record_refusal IS called inside resolve()" % hits[0].lineno,
        "source": "resolve.py", "line": 74,
    }

    # T18 "How many Ptr* error classes ... starting PtrLedger?"
    names = class_names(et)
    led = [n for n, _ in names if re.match(r"^PtrLedger\w*$", n)]
    out["cp.4.t18"] = {
        "kind": "NUM", "value": len(led), "evidence": "errors.py ClassDef %s" % led,
        "source": "errors.py", "line": min(l for n, l in names if n in led),
    }

    # T20 "Does _refuse() call ledger.resolved_count()?" -> absence inside _refuse()
    hits = attr_calls(rt, "_refuse", "resolved_count")
    out["cp.5.t20"] = {
        "kind": "NONE", "absent": not hits,
        "evidence": ("resolve.py: _refuse() calls only ledger.record_refusal; no "
                     "*.resolved_count") if not hits else
                    "resolve.py:%d resolved_count IS called inside _refuse()" % hits[0].lineno,
        "source": "resolve.py", "line": 66,
    }

    # T24 "How many Ptr* error classes does errors.py define?"
    ptr = [n for n, _ in names if re.match(r"^Ptr\w*$", n)]
    out["cp.6.t24"] = {
        "kind": "NUM", "value": len(ptr),
        "evidence": "errors.py: %d top-level ClassDef, %d matching ^Ptr\\w*$"
                    % (len(names), len(ptr)),
        "source": "errors.py", "line": min(l for n, l in names),
    }

    # T26 "... starting PtrLaw?"
    law = [n for n, _ in names if re.match(r"^PtrLaw\w*$", n)]
    out["cp.7.t26"] = {
        "kind": "NUM", "value": len(law), "evidence": "errors.py ClassDef %s" % law,
        "source": "errors.py", "line": min(l for n, l in names if n in law),
    }

    # T32 "... starting PtrUnknown?"
    unk = [n for n, _ in names if re.match(r"^PtrUnknown\w*$", n)]
    out["cp.8.t32"] = {
        "kind": "NUM", "value": len(unk), "evidence": "errors.py ClassDef %s" % unk,
        "source": "errors.py", "line": min(l for n, l in names if n in unk),
    }

    # T36 "Which ledger method does resolve() call to count refs already resolved, at
    #      the first of its three call sites?" -> first resolved_count() in resolve()
    hits = attr_calls(rt, "resolve", "resolved_count")
    callee, kwargs, order = call_render(hits[0])
    out["cp.9.t36"] = {
        "kind": "CALL", "callee": callee, "kwargs": kwargs, "source_order": order,
        "call_sites": [h.lineno for h in hits],
        "evidence": "resolve.py:%d first of %d resolved_count() calls at lines %s -> %s"
                    % (hits[0].lineno, len(hits), [h.lineno for h in hits],
                       ast.unparse(hits[0])),
        "source": "resolve.py", "line": hits[0].lineno,
    }

    # T42 "Does _refuse() call scope.block()?" -> absence inside _refuse()
    hits = attr_calls(rt, "_refuse", "block")
    out["cp.10.t42"] = {
        "kind": "NONE", "absent": not hits,
        "evidence": ("resolve.py: _refuse() calls nothing but ledger.record_refusal; no "
                     "scope.block()") if not hits else
                    "resolve.py:%d block() IS called inside _refuse()" % hits[0].lineno,
        "source": "resolve.py", "line": 66,
    }

    # T46 "What does _refuse call, and what does it pass?"
    hits = attr_calls(rt, "_refuse", "record_refusal")
    if len(hits) != 1:
        raise SystemExit("audit_error: _refuse() has %d record_refusal calls" % len(hits))
    callee, kwargs, order = call_render(hits[0])
    out["cp.11.t46"] = {
        "kind": "CALL", "callee": callee, "kwargs": kwargs, "source_order": order,
        "evidence": "resolve.py:%d ast.Call inside _refuse() -> %s"
                    % (hits[0].lineno, ast.unparse(hits[0])),
        "source": "resolve.py", "line": hits[0].lineno,
    }
    return out


# ------------------------------------------------------------------------ judgement
def judge(cid, mine, cp):
    """agree / disagree / ambiguous, with both values quoted."""
    documented = cp.get("expected")
    kind = mine["kind"]
    fx_kind = (cp.get("answer_spec") or {}).get("kind")
    row = {"id": cid, "turn": cp.get("turn"), "kind": kind, "fixture_kind": fx_kind,
           "fixture_expected": documented, "our_value": None, "evidence": mine["evidence"],
           "source": "%s:L%s" % (mine["source"], mine["line"]), "notes": []}

    if fx_kind != kind:
        row.update(verdict="disagree",
                   notes=["fixture declares kind %r; source fact is %r" % (fx_kind, kind)])
        return row

    if kind == "NUM":
        row["our_value"] = str(mine["value"])
        ok = str(documented).strip() == str(mine["value"])
        row["verdict"] = "agree" if ok else "disagree"
        if not ok:
            row["notes"].append("fixture %r != derived %r"
                                % (documented, mine["value"]))
        return row

    if kind == "NONE":
        row["our_value"] = "NONE"
        if not mine["absent"]:
            row.update(verdict="disagree",
                       notes=["the call IS present in the source; NONE is wrong"])
        elif str(documented).strip().upper() != "NONE":
            row.update(verdict="disagree",
                       notes=["fixture expected %r is not the constant NONE" % documented])
        else:
            row["verdict"] = "agree"
            row["notes"].append(
                "absence is decidable (grade_v5 flags none_contradicted_by_source when "
                "the call exists), but the graded truth is the CONSTANT 'NONE' -> a "
                "constant-NONE policy passes this id for free")
        return row

    # CALL
    callee, fx_kwargs, trailing = documented_call(documented)
    row["our_value"] = {"callee": mine["callee"], "kwargs": mine["kwargs"]}
    row["fixture_parse"] = {"callee": callee, "kwargs": fx_kwargs,
                            "trailing_text": trailing}
    verdict = "agree"
    if callee != mine["callee"]:
        verdict = "disagree"
        row["notes"].append("callee: fixture %r vs derived %r" % (callee, mine["callee"]))

    fx_set, my_set = set(fx_kwargs), set(mine["kwargs"])
    if fx_set == my_set:
        row["name_set"] = "exact (%d kwargs)" % len(my_set)
    elif fx_set < my_set:
        row["name_set"] = "SUBSET: fixture omits %s" % sorted(my_set - fx_set)
        verdict = "disagree"
    elif my_set < fx_set:
        row["name_set"] = "SUPERSET: fixture invents %s" % sorted(fx_set - my_set)
        verdict = "disagree"
    else:
        row["name_set"] = ("NEITHER: fixture-only %s / derived-only %s"
                           % (sorted(fx_set - my_set), sorted(my_set - fx_set)))
        verdict = "disagree"

    elided, mismatched = [], []
    for name in sorted(my_set & fx_set):
        have, want = _squash(fx_kwargs[name]), _squash(mine["kwargs"][name])
        if have in ("...", "\u2026"):
            elided.append({"kwarg": name, "source_value": want})
            continue
        if have != want:
            mismatched.append({"kwarg": name, "fixture": have, "derived": want})
            verdict = "disagree"
    row["elided_kwargs"] = elided
    row["value_mismatches"] = mismatched
    if elided:
        row["notes"].append(
            "FALSE-POSITIVE SURFACE: %d/%d kwarg values are elided as '...' in the "
            "fixture; grade_v5.grade_cell accepts a literal '...' for any elided kwarg "
            "(elided_kwargs branch), so a partially-correct answer passes this id"
            % (len(elided), len(my_set)))
    if trailing:
        row["notes"].append(
            "documentation defect (not graded): the expected string carries trailing "
            "prose after the call: %r" % trailing)
    # Source order vs the answer contract's alphabetical rule (order is NOT graded).
    if mine["source_order"] != sorted(mine["source_order"]):
        row["notes"].append(
            "contract/ordering: source passes kwargs as %s; the answer contract requires "
            "alphabetical %s -- grade_v5 does not grade order (kwargs_as_written is "
            "reported only), so this is documentation drift, not a truth error"
            % (mine["source_order"], sorted(mine["source_order"])))
    row["verdict"] = verdict
    return row


# ------------------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description="independent audit of LR-01.v7 truths")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    with open(args.fixture, "r", encoding="utf-8") as fh:
        raw = fh.read()
    fixture = json.loads(raw)          # the ONLY decode path: \uXXXX -> real chars
    cps = fixture.get("checkpoints") or []
    if len(cps) != 12:
        raise SystemExit("audit_error: fixture declares %d checkpoints, expected 12" % len(cps))

    mine = derive_all()
    rows = []
    for cp in cps:
        cid = cp.get("id")
        if cid not in mine:
            rows.append({"id": cid, "verdict": "disagree",
                         "notes": ["no independent derivation for this id"]})
            continue
        rows.append(judge(cid, mine[cid], cp))

    # the double-encoding trap, measured rather than assumed
    encoding = {
        "fixture_path": args.fixture,
        "fixture_sha256": sha256_of(args.fixture),
        "raw_contains_u003d_escape": "\\u003d" in raw,
        "raw_equals_chars": raw.count("="),
        "escaped_sequences_in_raw": sorted(set(re.findall(r"\\u[0-9a-fA-F]{4}", raw))),
        "decode_roundtrip": json.loads('"a\\u003db"') == "a=b",
        "compares": "json.loads(raw) values (decoded strings); raw JSON text is never "
                    "compared",
    }
    counts = {"agree": 0, "disagree": 0, "ambiguous": 0}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    report = {
        "unit": "V-FIXTURE-V7",
        "fixture": args.fixture,
        "fixture_sha256": encoding["fixture_sha256"],
        "source_sha256": {
            "resolve.py": sha256_of(SRC_RESOLVE),
            "errors.py": sha256_of(SRC_ERRORS),
            "ledger.py": sha256_of(SRC_LEDGER),
        },
        "counts": counts,
        "encoding": encoding,
        "rows": rows,
    }
    if args.json:
        print(json.dumps(report, indent=1, ensure_ascii=False))
    else:
        print("V-FIXTURE-V7 independent audit of %s" % args.fixture)
        print("fixture sha256 %s" % report["fixture_sha256"])
        for name, sha in sorted(report["source_sha256"].items()):
            print("  source %-12s %s" % (name, sha))
        print("")
        for r in rows:
            print("[%-8s] %-11s t%-2s %-4s ours=%s"
                  % (r["verdict"], r["id"], r["turn"], r["kind"],
                     json.dumps(r.get("our_value"), ensure_ascii=False)))
            print("           fixture: %s"
                  % json.dumps(r.get("fixture_expected"), ensure_ascii=False))
            if r.get("name_set"):
                print("           kwarg name set: %s" % r["name_set"])
            for note in r.get("notes") or []:
                print("           note: %s" % note)
        print("")
        print("encoding: raw has \\u003d escape = %s; decode roundtrip = %s"
              % (encoding["raw_contains_u003d_escape"], encoding["decode_roundtrip"]))
        print("counts: %s" % json.dumps(counts))
    return 0 if counts.get("disagree", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
