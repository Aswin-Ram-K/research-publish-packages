#!/usr/bin/env python3
"""LAUNCH-CONTRACT-DIFF — side-by-side comparison of every number a launch depends on.

Offline by construction: this tool only reads files under --root (JSON, code, docs)
and writes one JSON artefact.  It never opens a socket and never launches a cell.

For each load-bearing number it collects every occurrence it can find, quoting the
file:line, and classifies the number:

  AGREES          every non-superseded occurrence carries the same value
  DISAGREES       two non-superseded occurrences carry different values, or an
                  occurrence claims to be superseded without a written pointer,
                  or a quoted line drifted so the number can no longer be trusted
  STALE-BY-DESIGN a superseded value is deliberately preserved and a written
                  supersedes pointer names it (a launcher must use the other value)
  MOVED           (scoped checks only) the tree on disk is not the tree this check
                  was told to judge: a pinned input's bytes differ from the named
                  generation's record.  A DISTINCT class from DISAGREES, reported
                  with the mover named and BOTH digests.
  ABSENT          a field the check depends on is not there.  Reported as
                  ``ABSENT <dotted.path>`` with the file that should have carried it,
                  and it is NOT agreement: --check exits non-zero on it.  The row is
                  produced by resolving the field through one accessor that returns
                  ``(present, value, path)`` -- a missing key is data, never an
                  exception, because a checker that raises cannot tell a successor
                  whether the package agrees.

SCOPE.  The default check judges "whatever is on disk now", so a neighbour card
editing a pinned input between a card's write and its re-check turns a correct row
into a false FAIL.  ``--pin-generation N`` (or ``--tree-sha <harness_sha256>``)
names the tree to judge: the generation's record is resolved through the pin's
``supersedes`` chain, the live digest is recomputed over that generation's own
input list, and a tree that differs is ``MOVED`` -- exit 13, the project's
established tree-moved code (``exit_codes.EXIT_TREE_MOVED``, imported rather than
re-typed), never 1, because "the tree moved" is not "the work failed".  The report
carries ``judged_tree: {generation, harness_sha256, pinned_at}``.  The default with
no scope is UNCHANGED -- exit 1 on a real disagreement -- because a caller who names
nothing asked for the strict reading; the new argument is the escape from a false
FAIL, not a softening of the real one.

OPERATIONAL RULE this installs: a check whose acceptance depends on files other
cards may edit must be run with an explicit scope; a check that cannot name its
tree cannot distinguish a defect from a neighbour.

An anchor yields an ordered SET of (value, file:line) pairs, never a single hit: the
same literal legitimately appears more than once (``--budget 108`` in the cell argv and
in the flag default; ``48`` at the constant and at the override default; ``180`` at both
the cell argv and the flag default).  Agreement is therefore decided over the DISTINCT
VALUE SET — size 1 means every occurrence agrees, however many places it occupies — and
a DISAGREES names a file:line for each competing value, so "108 here, 67 there" is
always actionable rather than reduced to the first hit.

Exit status of --check: 1 when any number is DISAGREES or UNRESOLVED, else 0;
with an explicit scope, 13 when the tree moved under that scope (0 when it did
not); 2 for a usage error (an unknown generation, a malformed --tree-sha).

Usage
  python3 experiments/ptr-engine/tools/launch_contract_diff.py --check
  python3 experiments/ptr-engine/tools/launch_contract_diff.py --check --pin-generation 4
  python3 experiments/ptr-engine/tools/launch_contract_diff.py --check --tree-sha SHA256
  python3 experiments/ptr-engine/tools/launch_contract_diff.py --write --pin-generation 4
  python3 experiments/ptr-engine/tools/launch_contract_diff.py --check --root /tmp/copy
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))
MEAS = "experiments/ptr-engine/measure"
RUN_A_STAR = "experiments/ptr-engine/tools/run_a_star.py"
RUNNER = "experiments/ptr-engine/longrun/run_longrun.py"
CELL = "experiments/ptr-engine/longrun/cell.py"
STATS = "experiments/ptr-engine/longrun/analyze_stats.py"
PIN = MEAS + "/HARNESS-PIN.json"
PARAMS = MEAS + "/GRID-PARAMS.json"
SHAPE = MEAS + "/GRID-SHAPE.json"
LEDGER = MEAS + "/REQUEST-LEDGER.json"
BASELINE = MEAS + "/LEDGER-GRID-BASELINE-2.json"
DOC_PARAMS = "docs/GRID-PARAMS.md"
DOC_RUNBOOK = "docs/GRID-RUNBOOK.md"
DOC_SHAPE = "docs/GRID-SHAPE.md"
DOC_GATECHAIN = "docs/GATE-CHAIN.md"

#: The operational rule this tool installs (recorded in the artefact and the page).
OPERATIONAL_RULE = (
    "a check whose acceptance depends on files other cards may edit must be run with "
    "an explicit scope; a check that cannot name its tree cannot distinguish a defect "
    "from a neighbour.")


def _exit_tree_moved():
    """The project's single exit-code table.  Imported, never re-typed (cf. tree_freeze)."""
    longrun = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "longrun")
    if os.path.abspath(longrun) not in sys.path:
        sys.path.insert(0, os.path.abspath(longrun))
    import exit_codes  # noqa: WPS433 (the table is the source of truth)

    return exit_codes.EXIT_TREE_MOVED


#: 13: "the tree moved" is not "the work failed", so it must not share 1 with a FAIL.
EXIT_TREE_MOVED = _exit_tree_moved()
#: 2: usage refusal -- an unknown generation or a malformed --tree-sha (never 1).
EXIT_USAGE = 2


# ---------------------------------------------------------------- probes
def J(path, keys, role="authoritative", marker=None, marker_in=None,
      value_re=None, note=None):
    return {"type": "json", "path": path, "keys": list(keys), "role": role,
            "marker": marker, "marker_in": marker_in, "value_re": value_re,
            "note": note}


def JP(path, where, keys, role="authoritative", marker=None, marker_in=None,
       value_re=None, note=None):
    """jsonpick: select the object in list `where[0]` whose `where[1]` == `where[2]`."""
    return {"type": "jsonpick", "path": path, "where": list(where), "keys": list(keys),
            "role": role, "marker": marker, "marker_in": marker_in,
            "value_re": value_re, "note": note}


def G(path, regex, role="authoritative", marker=None, marker_in=None, note=None,
      multiline=False):
    """grep anchor.  Collects EVERY match as an ordered (value, file:line) pair.

    A literal legitimately appears at more than one line (``--budget 108`` in the
    cell argv and in the flag default; ``48`` at the constant and at the override
    default).  The anchor therefore yields an ordered *set of occurrences*, and
    agreement is decided over the distinct value set — never over the first hit.
    ``multiline=True`` matches across lines (line numbers are still reported),
    which is how a branch-specific anchor is kept from also matching its sibling.
    """
    return {"type": "grep", "path": path, "regex": regex, "role": role,
            "marker": marker, "marker_in": marker_in, "note": note,
            "multiline": bool(multiline)}


def L(path, lineno, contains, value, role="authoritative", marker=None,
      marker_in=None, note=None):
    return {"type": "line", "path": path, "lineno": lineno, "contains": contains,
            "value": value, "role": role, "marker": marker, "marker_in": marker_in,
            "note": note}


def C(label, value, note=None, role="authoritative", on_disagree=False):
    return {"type": "computed", "path": "<computed:%s>" % label, "value": value,
            "role": role, "marker": None, "marker_in": None,
            "note": note, "on_disagree": bool(on_disagree)}


def CA(label, present, value, path, note=None, role="authoritative", source=""):
    """A computed row whose source may be ABSENT -- absence must not be a KeyError.

    ``present`` is what the accessor returned; when it is False the probe reports
    ``ABSENT <path>`` and the row can still be rendered, classified and counted.
    """
    p = C(label, "" if not present else str(value), note=note)
    p["absent_path"] = None if present else path
    p["source"] = source or p["path"]
    p["role"] = role
    return p


def check(cid, label, probes, authoritative, resolution, owner="", absent_from=None,
          notes=None):
    return {"id": cid, "label": label, "probes": probes,
            "authoritative": authoritative, "resolution": resolution, "owner": owner,
            "absent_from": absent_from or [], "notes": notes or []}


def _load(root, rel):
    with open(os.path.join(root, rel), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _dotted(keys):
    out = ""
    for k in keys:
        out += "[%d]" % k if isinstance(k, int) else ("." if out else "") + str(k)
    return out


def resolve_field(obj, keys, rel=""):
    """The ONE accessor every JSON row goes through: (present, value, dotted.path).

    Absence is a result, not an error: a path that names no key returns
    ``(False, None, "price.components.tranche")`` so the caller can print
    ``ABSENT price.components.tranche in <file>``.  Nothing here raises for a
    missing key -- that is the whole point of the accessor.
    """
    cur = obj
    walked = []
    for k in keys:
        if isinstance(k, int):
            if not isinstance(cur, list) or not -len(cur) <= k < len(cur):
                return False, None, _dotted(walked + [k]) or "(root)"
        else:
            if not isinstance(cur, dict) or k not in cur:
                return False, None, _dotted(walked + [k]) or "(root)"
        cur = cur[k]
        walked.append(k)
    return True, cur, _dotted(walked) or "(root)"


def _absent(out, path, rel, requested=None):
    """Mark one probe ABSENT.  Never raises, so the table always renders.

    ``path`` is where resolution broke; ``requested`` is the whole dotted path the row
    needed, so a successor reads ``ABSENT price.components.tranche`` -- the field it
    would have to add -- and not merely the deepest present key.
    """
    out["absent"] = True
    out["absent_path"] = requested or path
    out["absent_at"] = path
    out["ok"] = False
    out["problem"] = "ABSENT %s in %s%s" % (
        requested or path, rel,
        "" if not requested or requested == path else " (resolves only to %s)" % path)
    return out


def _lines(root, rel):
    with open(os.path.join(root, rel), "r", encoding="utf-8") as fh:
        return fh.read().split("\n")


def _occ(line, value, quote):
    """One (value, file:line) pair.  The unit of agreement is the pair set."""
    return {"line": line, "value": str(value).strip(), "quote": quote}


def run_probe(root, p):
    out = {"path": p["path"], "line": None, "value": None, "quote": "",
           "role": p["role"], "marker": p.get("marker"),
           "marker_in": p.get("marker_in"), "note": p.get("note"),
           "on_disagree": p.get("on_disagree"), "absent": False,
           "absent_path": None,
           "ok": False, "problem": None, "problem_kind": None, "occurrences": []}
    try:
        if p["type"] == "computed":
            if p.get("absent_path"):
                return _absent(out, p["absent_path"], p.get("source") or p["path"])
            out["value"] = str(p["value"])
            out["ok"] = True
            out["quote"] = p.get("note") or "computed"
            out["occurrences"] = [_occ(None, out["value"], out["quote"])]
            return out
        rel = p["path"]
        fp = os.path.join(root, rel)
        if not os.path.exists(fp):
            out["problem"] = "missing file"
            return out
        if p["type"] == "json":
            present, v, dotted = resolve_field(_load(root, rel), p["keys"])
            if not present:
                return _absent(out, dotted, rel, _dotted(p["keys"]))
        elif p["type"] == "jsonpick":
            key, field, want = p["where"]
            present, arr, dotted = resolve_field(_load(root, rel), [key])
            if not present:
                return _absent(out, dotted, rel)
            if not isinstance(arr, list):
                return _absent(out, dotted, rel)
            hit = [x for x in arr if isinstance(x, dict) and x.get(field) == want]
            if not hit:
                out["problem"] = "no %s with %s==%r" % (key, field, want)
                return out
            present, v, dotted = resolve_field(hit[0], p["keys"])
            if not present:
                return _absent(
                    out, "%s[%s=%r]%s" % (key, field, want,
                                          ("." + dotted) if dotted else ""), rel,
                    "%s[%s=%r]%s" % (key, field, want,
                                     ("." + _dotted(p["keys"])) if p["keys"] else ""))
        elif p["type"] == "grep":
            # every occurrence, in file order — an anchor that matches twice is
            # reported twice, not silently reduced to its first hit
            lines = _lines(root, rel)
            found = []
            if p.get("multiline"):
                text = "\n".join(lines)
                for m in re.finditer(p["regex"], text, re.M | re.S):
                    ln = text.count("\n", 0, m.start()) + 1
                    val = m.group(1) if m.groups() else m.group(0)
                    found.append((ln, val, m.group(0).strip()[:200]))
            else:
                for i, ln in enumerate(lines, 1):
                    m = re.search(p["regex"], ln)
                    if m:
                        val = m.group(1) if m.groups() else m.group(0)
                        found.append((i, val, ln.strip()[:200]))
            if not found:
                # NAMED, not silent: an anchor that matches nothing means the SYMBOL
                # the checker quoted is gone (renamed, migrated, deleted).  Folding that
                # into a plain DISAGREES hides the fact that the two sides never met.
                out["problem"] = "regex not found: %s" % p["regex"]
                out["problem_kind"] = "anchor-missing"
                return out
            out["occurrences"] = [_occ(ln, val, quote) for ln, val, quote in found]
            out["line"], out["value"], out["quote"] = found[0]
            v = out["value"]
        elif p["type"] == "line":
            lines = _lines(root, rel)
            n = p["lineno"]
            if n > len(lines):
                out["problem"] = "line %d past EOF (%d)" % (n, len(lines))
                return out
            ln = lines[n - 1]
            out["line"] = n
            out["quote"] = ln.strip()[:200]
            if p["contains"] not in ln:
                out["problem"] = ("line %d drifted: expected %r, found %r"
                                  % (n, p["contains"], ln.strip()[:120]))
                return out
            v = p["value"]
        else:
            out["problem"] = "unknown probe type"
            return out
        if p.get("value_re"):
            if out["occurrences"]:
                for o in out["occurrences"]:
                    m = re.search(p["value_re"], str(o["value"]))
                    if not m:
                        out["problem"] = "value_re %r did not match %r" % (
                            p["value_re"], o["value"])
                        return out
                    o["value"] = (m.group(1) if m.groups() else m.group(0)).strip()
                out["value"] = out["occurrences"][0]["value"]
                v = out["value"]
            else:
                m = re.search(p["value_re"], str(v))
                if not m:
                    out["problem"] = "value_re %r did not match %r" % (p["value_re"], v)
                    return out
                v = m.group(1) if m.groups() else m.group(0)
        if not out["occurrences"]:
            out["value"] = str(v).strip()
            out["occurrences"] = [_occ(out["line"], out["value"], out["quote"])]
        out["ok"] = True
        return out
    except (OSError, ValueError, TypeError, IndexError, KeyError) as exc:
        # A NARROW backstop for a malformed record (unparseable JSON, a wrong shape).
        # Absence never reaches here: it is resolved by resolve_field above.
        out["problem"] = "%s: %s" % (type(exc).__name__, exc)
        return out


def norm(v):
    if v is None:
        return None
    s = str(v).strip()
    if re.fullmatch(r"[0-9][0-9,_ ]*", s):
        return str(int(re.sub(r"[,_ ]", "", s)))
    return s.lower()


def same(a, b):
    na, nb = norm(a), norm(b)
    if na == nb:
        return True
    # an abbreviated digest (>=8 hex chars) still names the same value
    if re.fullmatch(r"[0-9a-f]{8,63}", na or "") and re.fullmatch(r"[0-9a-f]{8,63}", nb or ""):
        return na.startswith(nb) or nb.startswith(na)
    return False


def classify(root, chk, digest_chain=None, probes=None):
    """Classify one check.  ``digest_chain`` (scoped digest rows only) is the set of
    digests the pin's supersedes chain records for OTHER generations: an occurrence
    carrying one of those is a laid-down prior generation, and the chain itself is
    the written pointer, so it is stale-by-design rather than a competitor.
    ``probes`` lets a caller hand in already-run (and scope-adjusted) probe results.
    """
    probes = probes if probes is not None else [run_probe(root, p) for p in chk["probes"]]
    absent = [p for p in probes if p.get("absent")]
    broken = [p for p in probes if not p["ok"] and not p.get("absent")]
    if broken:
        for p in probes:
            p["resolved"] = ("absent" if p.get("absent") else
                             "broken" if not p["ok"] else "load-bearing")
        first = broken[0]
        miss = [p for p in broken if p.get("problem_kind") == "anchor-missing"]
        if miss:
            # A named failure mode: the probe's SYMBOL is absent, so the row never
            # compared two values.  It is not agreement and it is not a drift report;
            # it says the checker is aimed at a symbol the file no longer carries.
            where = ", ".join("%s (%s)" % (m["path"], m["problem"]) for m in miss)
            return "ANCHOR-MISSING", probes, (
                "no anchor found: the symbol this check greps is absent, so no value "
                "was compared -- retarget the probe at the symbol the file now uses "
                "(%s)" % where)
        return "DISAGREES", probes, (
            "a quoted line/field no longer carries the number (%s: %s)"
            % (first["path"], first["problem"]))

    competitors, stale, evidence = [], [], []
    for p in probes:
        if p.get("absent"):
            p["resolved"] = "absent"
            continue
        if p["role"] == "evidence":
            evidence.append(p)
        elif p["role"] == "stale":
            if not p["marker"]:
                competitors.append(p)          # unlabelled old value: a real competitor
            else:
                mfile = os.path.join(root, p["marker_in"] or p["path"])
                try:
                    with open(mfile, "r", encoding="utf-8") as fh:
                        text = fh.read()
                except OSError:
                    text = ""
                if p["marker"] in text:
                    stale.append(p)
                else:
                    competitors.append(p)      # claimed stale, but nobody wrote the pointer
                    p["problem"] = "stale claim has no written pointer %r in %s" % (
                        p["marker"], p["marker_in"] or p["path"])
        else:
            competitors.append(p)

    for p in competitors:
        p["resolved"] = "load-bearing"
    for p in stale:
        p["resolved"] = "stale-by-design"
    for p in evidence:
        p["resolved"] = "evidence"
    if digest_chain:
        # A prior generation's digest is not a competitor when the pin's own supersedes
        # chain names it: the chain is the written pointer, so the value is stale by
        # design under a scope.  Anything else still competes -- a scope must not become
        # a bypass.
        older = {norm(v) for v in digest_chain}
        kept = []
        for p in competitors:
            vals = [o["value"] for o in (p.get("occurrences") or [])] or [p["value"]]
            if all(norm(v) in older for v in vals):
                p["resolved"] = "stale-by-design"
                stale.append(p)
            else:
                kept.append(p)
        competitors = kept
    # the pool is every (value, file:line) pair any competitor carries.  A single
    # probe can contribute several pairs — that is the whole point: "108 at
    # run_a_star.py:241 and 108 at run_a_star.py:366" is two pairs and one value.
    pool = []
    for p in competitors:
        for o in (p.get("occurrences") or [_occ(p["line"], p["value"], p["quote"])]):
            pool.append({"path": p["path"], "line": o["line"], "value": o["value"],
                         "probe": p})
    values = []
    for o in pool:
        if not any(same(o["value"], v) for v in values):
            values.append(o["value"])
    if not competitors:
        return "ABSENT", probes, "no authoritative occurrence carries this number"
    if len(values) > 1:
        # name a file:line for EVERY competing value — a disagreement that does
        # not say where both sides live cannot be acted on
        seen, detail = [], []
        for o in pool:
            if not any(same(o["value"], v) for v in seen):
                seen.append(o["value"])
        for v in seen:
            at = [o for o in pool if same(o["value"], v)]
            # prefer an occurrence that carries a real line number: "at
            # GRID-PARAMS.json:-" is not somewhere a reader can go
            pick = ([o for o in at if o["line"] is not None] or at)[0]
            detail.append("%s at %s:%s" % (
                pick["value"], pick["path"],
                pick["line"] if pick["line"] is not None else "-"))
        reason = "competing values: " + ", ".join(sorted(values)) + (
            " (" + "; ".join(detail) + ")")
        hints = [p["note"] for p in evidence
                 if p.get("on_disagree") and p.get("note")]
        if hints:
            reason += "; " + "; ".join(hints)
        if absent:
            reason += "; also ABSENT " + ", ".join(
                sorted({p["absent_path"] for p in absent}))
        return "DISAGREES", probes, reason
    if absent:
        # A missing field is ABSENT, not agreement and not a drifted quote: name the
        # dotted path and the file that should have carried it.  Ordered AFTER the
        # disagreement test so absence can never mask two competing values.
        return "ABSENT", probes, "; ".join(sorted(
            {"ABSENT %s in %s" % (p["absent_path"], p.get("source") or p["path"])
             for p in absent}))
    if stale:
        return "STALE-BY-DESIGN", probes, "%s convention preserved by a written pointer" % (
            ", ".join(sorted({o["value"] for s in stale for o in
                              (s.get("occurrences") or [_occ(s["line"], s["value"], "")])})))
    return "AGREES", probes, "single value across %d occurrence(s)" % len(pool)


# ---------------------------------------------------------------- derived
def pin_drift(root):
    """Pinned inputs whose bytes on disk no longer match the record.

    A digest disagreement that does not say WHICH input moved is not actionable;
    the launcher needs the file name, not just two hashes.
    """
    doc = _load(root, PIN)
    moved = []
    for f in doc["files"]:
        path = os.path.join(root, f["path"])
        try:
            with open(path, "rb") as fh:
                sha = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            moved.append(f["path"] + " (missing)")
            continue
        if sha != f["sha256"]:
            moved.append(f["path"])
    return moved


def digest_over(root, files, live):
    """The pin's digest recipe over a named input list: recorded hashes, or bytes."""
    rows = []
    for f in files:
        if live:
            path = os.path.join(root, f["path"])
            try:
                with open(path, "rb") as fh:
                    sha = hashlib.sha256(fh.read()).hexdigest()
            except OSError:
                sha = "missing:" + f["path"]
        else:
            sha = f["sha256"]
        rows.append((f["name"], sha))
    rows.sort()
    return hashlib.sha256("".join("%s:%s\n" % (n, s) for n, s in rows).encode()).hexdigest()


def pin_digest(root, live):
    return digest_over(root, _load(root, PIN)["files"], live)


def pin_generations(root):
    """The pin record plus every generation preserved under a supersedes block."""
    doc = _load(root, PIN)
    chain, cur = [], doc
    while isinstance(cur, dict) and cur.get("generation") is not None:
        chain.append(cur)
        nxt = None
        if isinstance(cur.get("generation"), int):
            cand = cur.get("supersedes_pin_generation_%d" % (cur["generation"] - 1))
            if isinstance(cand, dict):
                nxt = cand
        if nxt is None:
            for k, v in cur.items():
                if (k.startswith("supersedes") and isinstance(v, dict)
                        and v.get("generation") == cur["generation"] - 1):
                    nxt = v
                    break
        cur = nxt
    return chain


def moved_inputs(root, files):
    """Each pinned input whose bytes differ from the record, with BOTH digests."""
    out = []
    for f in files:
        path = os.path.join(root, f["path"])
        try:
            with open(path, "rb") as fh:
                cur = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            cur = None
        if cur != f["sha256"]:
            out.append({"path": f["path"], "name": f["name"],
                        "recorded_sha256": f["sha256"], "current_sha256": cur})
    return out


def resolve_scope(root, generation=None, tree_sha=None):
    """None (unscoped), or the tree this run is told to judge.  ValueError = usage."""
    if generation is None and not tree_sha:
        return None
    gens = pin_generations(root)
    rec = None
    if generation is not None:
        hits = [g for g in gens if g.get("generation") == generation]
        if not hits:
            raise ValueError("no pin generation %d in HARNESS-PIN.json (have: %s)" % (
                generation,
                ", ".join(str(g.get("generation")) for g in gens) or "none"))
        rec = hits[0]
        if not rec.get("harness_sha256") or not rec.get("files"):
            raise ValueError("pin generation %d records no harness_sha256/files"
                             % generation)
        digest = rec["harness_sha256"]
    else:
        digest = tree_sha.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("--tree-sha must be a full 64-hex harness sha256, got %r"
                             % tree_sha)
        hits = [g for g in gens if norm(g.get("harness_sha256")) == digest]
        if not hits:
            # An unrecorded digest names no recorded values to judge against; accepting
            # it would let this flag launder any disagreement, so it is refused -- the
            # same reason tree_freeze refuses to name bytes it did not judge.
            raise ValueError("--tree-sha %s is not a generation recorded in HARNESS-PIN.json "
                             "(recorded: %s); record the tree in the pin first, or pass "
                             "--pin-generation" % (digest, ", ".join(
                                 "%s=%s..." % (g.get("generation"),
                                               str(g.get("harness_sha256"))[:16])
                                 for g in gens)))
        rec = hits[0]
    files = rec["files"] if rec else _load(root, PIN)["files"]
    older = []
    for g in gens:
        if g is not rec and g.get("harness_sha256"):
            older.append(g["harness_sha256"])
    if rec and rec.get("superseded_harness_sha256"):
        older.append(rec["superseded_harness_sha256"])
    return {"generation": rec.get("generation") if rec else None,
            "harness_sha256": digest,
            "pinned_at": (rec.get("frozen_at") or rec.get("recorded_at")) if rec else None,
            "files": files,
            "older_digests": [d for d in dict.fromkeys(older) if norm(d) != norm(digest)]}


def classify_scoped(root, chk, scope):
    """Judge the digest row against the NAMED tree, never against whatever is on disk.

    A tree that differs from the scope is ``MOVED`` -- naming every input that moved
    with both digests -- and is NOT a disagreement, because a neighbour's edit is not
    this row's defect.  A tree that matches is judged normally, with prior-generation
    digests read as stale-by-design (the pin's chain is their written pointer).
    """
    live = digest_over(root, scope["files"], True)
    movers = moved_inputs(root, scope["files"])
    probes = [run_probe(root, p) for p in chk["probes"]]
    for p, spec in zip(probes, chk["probes"]):
        if not p["ok"]:
            continue
        lab = spec.get("path") or ""
        if lab.endswith("recorded per-file hashes"):
            p["value"] = digest_over(root, scope["files"], False)
            p["occurrences"] = [_occ(None, p["value"], p["quote"])]
        elif lab.endswith("bytes on disk now"):
            p["value"] = live
            p["occurrences"] = [_occ(None, p["value"], p["quote"])]
        elif lab.endswith("whose bytes moved"):
            p["value"] = ", ".join(m["path"] for m in movers) or "none"
            p["note"] = "pinned inputs whose bytes moved: %s" % (p["value"] or "none")
            p["occurrences"] = [_occ(None, p["value"], p["quote"])]
        elif spec.get("type") == "json":
            # the judged generation's own record (top level for the current generation,
            # a supersedes block for an older one)
            p["value"] = scope["harness_sha256"]
            p["occurrences"] = [_occ(p["line"], p["value"], p["quote"])]
        elif spec.get("type") == "line":
            # a quoted page line must carry the JUDGED generation's digest
            p["value"] = scope["harness_sha256"]
            p["occurrences"] = [_occ(p["line"], p["value"], p["quote"])]
    extra = {"live_harness_sha256": live, "moved_inputs": movers}
    if live != scope["harness_sha256"]:
        detail = "; ".join(
            "%s %s -> %s" % (m["path"], (m["recorded_sha256"] or "-"),
                             (m["current_sha256"] or "missing")) for m in movers
        ) or "no pinned input could be read"
        reason = ("the tree moved under the named scope: %s (scope harness_sha256 %s, "
                  "live %s)" % (detail, scope["harness_sha256"], live))
        return "MOVED", probes, reason, extra
    status, probes, reason = classify(root, chk, digest_chain=scope["older_digests"],
                                      probes=probes)
    if status in ("AGREES", "STALE-BY-DESIGN"):
        named = ("generation %s" % scope["generation"]
                 if scope["generation"] is not None else "the named --tree-sha")
        return "AGREES", probes, (
            "the tree matches the named scope: live harness_sha256 %s equals %s"
            % (live, named)), extra
    return status, probes, reason, extra


def fixture_digest(root):
    doc = _load(root, PIN)
    fx = [f for f in doc["files"] if f["name"] == "fixture"][0]
    with open(os.path.join(root, fx["path"]), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def floor_n(root):
    tail = int(re.search(r"^TAIL_MIN = (\d+)",
                         "\n".join(_lines(root, STATS)), re.M).group(1))
    minn = int(re.search(r"^MIN_N = (\d+)",
                         "\n".join(_lines(root, STATS)), re.M).group(1))
    import math
    return str(max(minn, int(math.ceil(tail / (1.0 - 0.95)))))


def price_derivation(root):
    """What price.total would have to be justified by, read -- never written.

    A bare total is not a price: it is the shape that let 792/660 and 1,016/1,056 drift
    for rounds.  When ``price.components`` is absent this derives the arithmetic the
    total must reconcile against -- ``shape.turns_total x price.factor`` with the
    factor's recorded provenance -- and flags ``price_unjustified`` when it does not.
    """
    try:
        params = _load(root, PARAMS)
    except (OSError, ValueError) as exc:
        return {"status": "price_unjustified", "flag": "price_unjustified",
                "reason": "cannot read %s: %s" % (PARAMS, exc),
                "total": None, "components_present": False, "expected": None}
    total_p, total, total_path = resolve_field(params, ["price", "total"])
    comp_p, comps, comp_path = resolve_field(params, ["price", "components"])
    factor_p, factor, factor_path = resolve_field(params, ["price", "factor"])
    prov_p, prov, _ = resolve_field(params, ["price", "factor_path"])
    turns_p, turns, turns_path = resolve_field(params, ["shape", "turns_total"])
    turns_from = turns_path
    if not turns_p:
        art_p, art, _ = resolve_field(params, ["price", "arithmetic"])
        m = re.search(r"(\d+)\s*turns\s*x", str(art)) if art_p else None
        if m:
            turns, turns_p, turns_from = int(m.group(1)), True, "price.arithmetic"
    need = ("tranche", "canary", "warm_ups")
    comps_ok = bool(comp_p) and isinstance(comps, dict) and all(k in comps for k in need)
    components_sum = (comps["tranche"] + comps["canary"] + comps["warm_ups"]
                      if comps_ok else None)
    expected = None
    if turns_p and factor_p:
        try:
            expected = int(round(float(turns) * float(factor)))
        except (TypeError, ValueError):
            expected = None
    reconciled = (expected is not None and total_p
                  and abs(float(total) - expected) <= 0.5)
    missing_path = None if (turns_p and factor_p) else (
        (turns_path if not turns_p else "price.factor"))
    if comps_ok:
        status = "JUSTIFIED-BY-COMPONENTS"
    elif reconciled:
        status = "JUSTIFIED-BY-DERIVATION"
    else:
        status = "price_unjustified"
    caveat_p, caveat, _ = resolve_field(
        params, ["price", "caveats", "not_like_for_like_with_1016"])
    return {
        "status": status,
        "flag": "price_unjustified" if status == "price_unjustified" else "",
        "total": total if total_p else None,
        "total_path": total_path if total_p else None,
        "components_present": bool(comp_p),
        "components_absent_path": None if comp_p else comp_path,
        "components": comps if comps_ok else None,
        "components_sum": components_sum,
        "components_absent_key": (None if comps_ok else
                                  ("price.components." + [k for k in need
                                                          if not comp_p or k not in (comps or {})][0]
                                   if comp_p else "price.components")),
        "turns": turns if turns_p else None,
        "turns_path": turns_from,
        "factor": factor if factor_p else None,
        "factor_provenance": prov if prov_p else "unrecorded",
        "expected": expected,
        "arithmetic": ("%s turns x %s = %.6f -> %d" % (
            turns, factor, float(turns) * float(factor), expected)
            if expected is not None else "not derivable (%s absent)" % missing_path),
        "reconciled": bool(reconciled),
        "caveat": caveat if caveat_p else "",
        "owner": "%s written by GRID-PARAMS-16CELL's successor" % PARAMS,
    }


def canary_arms(root):
    """CANARY_ARMS arity, or (False, None, path) -- a missing tuple must not raise."""
    try:
        text = "\n".join(_lines(root, RUN_A_STAR))
    except OSError:
        return False, None, "CANARY_ARMS (run_a_star.py unreadable)"
    m = re.search(r"^CANARY_ARMS = \(([^)]*)\)", text, re.M)
    if not m:
        return False, None, "CANARY_ARMS"
    return True, len(re.findall(r'"[^"]+"', m.group(1))), "CANARY_ARMS"


def checks(root):
    pin_present, pin, pin_path = resolve_field(_load(root, PIN), ["harness_sha256"])
    if not pin_present:
        pin = ""
    params = _load(root, PARAMS)
    shape = _load(root, SHAPE)
    der = price_derivation(root)
    arms_present, arms, arms_path = canary_arms(root)
    out = []

    out.append(check(
        "harness_pin_digest", "harness pin digest (--expect-harness)",
        [J(PIN, ["harness_sha256"]),
         G(RUN_A_STAR, r'^PIN_EXPECTED_DIGEST = "([0-9a-f]{64})"',
           note="the launcher's signed-off expectation, run_a_star.py:73"),
         G(RUN_A_STAR, r'^PIN_GENERATION, HARNESS_PIN, PIN_ABORT = _read_pin\(PIN_RECORD\)$',
           role="evidence",
           note="the pin is READ from measure/HARNESS-PIN.json at import; the constant "
                "above is the signed-off expectation it is refused against"),
         C("pin digest over recorded per-file hashes", pin_digest(root, False)),
         C("pin digest over bytes on disk now", pin_digest(root, True)),
         C("pinned inputs whose bytes moved", ", ".join(pin_drift(root)) or "none",
           role="evidence", on_disagree=True,
           note="pinned inputs whose bytes moved: %s" % (", ".join(pin_drift(root)) or "none")),
         L(DOC_RUNBOOK, 68, pin, pin),
         L(DOC_RUNBOOK, 121, pin, pin),
         L(DOC_RUNBOOK, 385,
           "35ff41b7\u2026",
           "35ff41b7\u2026",
           role="stale", marker="generation 5 was the canary's epoch",
           marker_in=DOC_RUNBOOK,
           note="the generation-5 digest kept on the record as the canary's epoch, "
                "never as a launch value: it is stale by design under the written "
                "pointer on that line"),
         J(PARAMS, ["harness_pin", "harness_sha256"], role="stale")],
        authoritative="HARNESS-PIN.json:5 (generation 6, efefd885...) + run_a_star.py:72-73 (PIN_EXPECTED_GENERATION/PIN_EXPECTED_DIGEST, the signed-off expectation the launcher refuses the record against) + recomputation over bytes",
        resolution=("efefd8859c3fdeeac288157ba5cceba1bbe4144947af441721a5f4c4369579b3. "
                    "run_a_star.py:72-73 holds generation 6 and this digest; run_a_star.py:102 "
                    "refuses any record whose generation or digest differs, so the launcher "
                    "passes exactly this value and cannot silently follow a newer pin. The "
                    "generation-5 digest 35ff41b7... is the canary's epoch (docs/GRID-RUNBOOK.md, "
                    "dated line) and is not a launch value."),
        owner="experiments/ptr-engine/measure/GRID-PARAMS.json (harness_pin.harness_sha256, bumped with its supersedes block) + docs/GRID-RUNBOOK.md digest lines",
        notes=["the probe was retargeted from the deleted HARNESS_PIN constant to PIN_EXPECTED_DIGEST: the old anchor reported 'regex not found' on every run regardless of truth",
               "a grep anchor that matches nothing is now ANCHOR-MISSING, a named failure mode, not a silent DISAGREES"]))

    out.append(check(
        "fixture_sha256", "fixture sha256 (LR-01.v8.json)",
        [JP(PIN, ("files", "name", "fixture"), ["sha256"]),
         C("fixture bytes on disk", fixture_digest(root)),
         L(DOC_RUNBOOK, 33,
           "0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641",
           "0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641"),
         L(DOC_RUNBOOK, 75,
           "0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641",
           "0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641")],
        authoritative="HARNESS-PIN.json:28-33 (the pin's 'fixture' row) + the bytes on disk",
        resolution="single value; GRID-SHAPE.json carries no fixture digest, only the checker name",
        absent_from=["experiments/ptr-engine/measure/GRID-SHAPE.json:15-16 (names cell.py as the checker, carries no value)"]))

    out.append(check(
        "price_total", "launch price (total)",
        [J(PARAMS, ["price", "total"]),
         CA("turns x factor (%s x %s)" % (der["turns_path"], "price.factor"),
            der["expected"] is not None, der["expected"],
            "shape.turns_total" if der["turns"] is None else "price.factor",
            note="the derivation the recorded total must reconcile against: "
                 "16 cells x 48 turns = 768 turns x 1.374532 (tools-off historical "
                 "factor) = 1056; price.components is obsolete (turns x factor model)"),
         L(DOC_PARAMS, 56, "1,016", "1016", role="stale",
           marker="Revision 2", marker_in=DOC_PARAMS),
         L(DOC_RUNBOOK, 3, "1,056 requests", "1056"),
         G(DOC_RUNBOOK, r"`(\d+)\s+\{'tranche'")],
        authoritative="GRID-PARAMS.json:228 (price.total) and its component sum",
        resolution="1,016 = 964 tranche + 48 canary + 4 warm-ups",
        owner="experiments/ptr-engine/measure/GRID-PARAMS.json (GRID-PARAMS-16CELL's successor): restore price.components",
        notes=["docs/GRID-PARAMS.md:43-46 still prints the tranches-only 964 and calls 2,228 the remainder; both are labelled superseded at :49-63",
               "the derivation row (shape.turns_total x price.factor) is what the total is judged against when price.components is ABSENT -- the price arithmetic is restored in THIS report, not by editing the params file"]))

    out.append(check(
        "price_remaining_after", "headroom after the launch price",
        [J(PARAMS, ["price", "remaining_after"]),
         L(DOC_PARAMS, 58, "2,176", "2176", role="stale",
           marker="Revision 2", marker_in=DOC_PARAMS),
         G(DOC_RUNBOOK, r"'warm_ups': 4\} (\d+)"),
         J(SHAPE, ["grid", "remaining_after_incl_digests"], role="stale",
           marker="price.remaining_after = 2,176", marker_in=PARAMS),
         L(DOC_PARAMS, 46, "2,228", "2228", role="stale",
           marker="superseded as the launch remainder by", marker_in=DOC_PARAMS)],
        authoritative="GRID-PARAMS.json:239 (price.remaining_after = 2176) over remaining_before 3192",
        resolution="3,192 - 1,016 = 2,176; 2,228 is the tranches-only remainder and 2,468 the 724-era figure",
        notes=["both old figures are preserved deliberately; a launcher must quote 2,176"]))

    out.append(check(
        "per_cell_budget", "per-cell --budget",
        [J(PARAMS, ["per_cell_budget", "recommended"]),
         G(RUN_A_STAR, r'"--budget", "(\d+)"'),
         G(RUN_A_STAR, r'ap\.add_argument\("--budget", type=int, default=(\d+)'),
         G(RUN_A_STAR, r'ledger allocation handed to cell\.py \(default (\d+)\)',
           role="stale"),
         L(DOC_PARAMS, 125, "budget 108", "108"),
         J(SHAPE, ["cells", 0, "budget"], role="stale",
           marker="--budget 67", marker_in=PARAMS)],
        authoritative="run_a_star.py:241 (the argv the launcher actually execs) and GRID-PARAMS.json:188",
        resolution=("108. The launcher hard-codes '--budget 108' into every cell argv "
                    "(run_a_star.py:241) and the flag default is 108 (run_a_star.py:367): two "
                    "legitimate occurrences of one value, which is AGREES with an occurrence "
                    "count, not a defect. GRID-SHAPE.json's 67 is superseded by "
                    "GRID-PARAMS.json:274-277. Measured gate: ceil(48 x 1.10) = 53 <= both, so "
                    "67 would not refuse either — the value is not load-bearing for refusal, "
                    "only for the record."),
        owner="",
        notes=["run_cell records rec['budget'] from the CLI (run_a_star.py:293) while cell_argv always passes 108 (:241); both now read 108",
               "the launcher help string was corrected 67 -> 108 by the residual card, so this "
               "number stays STALE-BY-DESIGN only because GRID-SHAPE.json keeps the superseded "
               "67 behind a written pointer"]))

    out.append(check(
        "fetch_allowance", "--fetch-followup-allowance (G1 reserve)",
        [J(PARAMS, ["fetch_followup_allowance", "value"]),
         G(RUN_A_STAR, r"^FETCH_ALLOWANCE = (\d+)"),
         J(SHAPE, ["cells", 0, "cell_py_flags", 8], role="stale",
           value_re=r"(\d+)$", marker="fetch_followup_allowance.value = 48",
           marker_in=PARAMS),
         J(SHAPE, ["cells", 0, "projection", "followup_allowance"], role="stale",
           marker="fetch_followup_allowance.value = 48", marker_in=PARAMS)],
        authoritative="run_a_star.py:44 FETCH_ALLOWANCE = 48, appended at :280 when --tools is on",
        resolution="48; 24 is GRID-SHAPE's superseded 24-round shape",
        notes=["the flag is a cell.py G1 accounting reserve only (cell.py:1160-1175); it never reaches the runner"]))

    out.append(check(
        "per_arm_round_cap", "per-arm fetch-round cap",
        [G(RUNNER, r"^TOOL_FETCH_ROUNDS_PER_ARM = (\d+)"),
         G(RUNNER, r'ap\.add_argument\("--fetch-rounds-per-arm", type=int, default=TOOL_FETCH_ROUNDS_PER_ARM',
           role="evidence", note="the override flag"),
         J(PARAMS, ["per_arm_round_cap", "runtime_constant"]),
         J(SHAPE, ["factor", "ceiling_from"], role="stale", value_re=r"=(\d+)",
           marker="48 at run_longrun.py:230", marker_in=PARAMS),
         L(DOC_SHAPE, 86, "TOOL_FETCH_ROUNDS_PER_ARM = 24", "24", role="stale",
           marker="factor.ceiling_from", marker_in=PARAMS),
         G(DOC_PARAMS, r"TOOL_FETCH_ROUNDS_PER_ARM = (\d+)", role="stale")],
        authoritative="run_longrun.py TOOL_FETCH_ROUNDS_PER_ARM = 48 (line located by grep) with --fetch-rounds-per-arm",
        resolution=("48, overridable. GRID-PARAMS.json:174-181 records the RUNNER-ROUNDS-48 move; "
                    "docs/GRID-PARAMS.md:90 still asserts 'a module constant with no override' "
                    "and cites the pre-move line 226 — an undated stale claim in the human doc."),
        owner="docs/GRID-PARAMS.md §4 (stale) + docs/GRID-SHAPE.md — needs a doc-sync card",
        notes=["line drift: the constant moved from run_longrun.py:226 to :230; the flag is at :2857"]))

    out.append(check(
        "per_turn_round_cap", "per-turn fetch-round cap",
        [G(RUNNER, r"^TOOL_FETCH_ROUNDS_PER_TURN = (\d+)"),
         J(PARAMS, ["per_arm_round_cap", "per_turn_cap"], value_re=r"= (\d+)")],
        authoritative="run_longrun.py TOOL_FETCH_ROUNDS_PER_TURN = 3",
        resolution="3 (bounds the burst; the pool bounds the total)",
        notes=["docs/GRID-SHAPE.md:86 cites run_longrun.py:231 for this constant; the value is right, the line is off by one"]))

    out.append(check(
        "canary_arms", "canary arms",
        [CA("CANARY_ARMS tuple length", arms_present, arms, arms_path),
         L(DOC_RUNBOOK, 127, "4 arms", "4")],
        authoritative="run_a_star.py:73 CANARY_ARMS (four named arms)",
        resolution="4",
        absent_from=["GRID-PARAMS.json :: canary (carries N only, no arm count)"]))

    out.append(check(
        "canary_turns", "canary turns per arm",
        # anchored on the canary branch's own max-wall line so the sibling grid
        # branch (a.turns = 48) cannot be mistaken for a second occurrence
        [G(RUN_A_STAR,
           r"a\.max_wall = CANARY_MAX_WALL if a\.max_wall is None else a\.max_wall\n"
           r"\s*a\.turns = (\d+)", multiline=True),
         J(PARAMS, ["canary", "N"]),
         L(DOC_RUNBOOK, 123, "N=12", "12")],
        authoritative="run_a_star.py (canary branch sets a.turns = 12) and GRID-PARAMS.json canary.N",
        resolution="12 per arm, 4 arms",
        notes=["the grid branch also writes a.turns = 48; the anchor is branch-specific, so it "
               "yields exactly one pair and no false disagreement"]))

    out.append(check(
        "canary_requests", "canary requests",
        [CA("arms x turns", arms_present, None if not arms_present else arms * 12,
            arms_path,
            note="canary requests = 4 arms x 12 turns (CANARY_ARMS x canary.N); "
                 "price.components.canary / price.canary_identity are obsolete "
                 "(canary priced via canary.N, not a tranche)")],
        authoritative="GRID-PARAMS.json:236 (12 turns x 4 arms = 48)",
        resolution="48 = 4 arms x 12 turns",
        absent_from=["GRID-PARAMS.json :: canary (the priced component lives under price.canary, not canary)"]))

    out.append(check(
        "canary_max_wall", "canary --max-wall",
        [G(RUN_A_STAR, r"^CANARY_MAX_WALL = (\d+)")],
        authoritative="run_a_star.py:214 CANARY_MAX_WALL = 900, applied at :386 when --canary",
        resolution="900 s; it must clear 12 x 60 = 720 s, and the grid default 2880 would not be a canary",
        absent_from=["GRID-PARAMS.json :: canary (no wall)", "docs/GRID-RUNBOOK.md §1b (argues 720/600 but never names 900)"]))

    out.append(check(
        "canary_hypothesis", "canary --hypothesis",
        [G(RUN_A_STAR, r'a\.hypothesis = a\.hypothesis or "(smoke)"')],
        authoritative="run_a_star.py (canary branch defaults the claim to 'smoke')",
        resolution="smoke — the canary declares no claim and can never be pooled",
        absent_from=["GRID-PARAMS.json :: canary.verdict_rule (names the gate, not the claim)"]))

    out.append(check(
        "grid_cells", "grid cells",
        [J(SHAPE, ["grid", "cells"]),
         L(DOC_RUNBOOK, 3, "10 cells", "10")],
        authoritative="GRID-SHAPE.json :: grid.cells = 10 (the launcher's CELLS list has the same ten)",
        resolution="10 (3 + 3 + 2 + 2 across the four arms)"))

    out.append(check(
        "grid_turns", "grid total turn rows",
        [J(SHAPE, ["grid", "turns"])],
        authoritative="GRID-SHAPE.json :: grid.turns = 480 = 10 cells x 48 turns",
        resolution="480 turn rows"))

    out.append(check(
        "grid_max_wall", "grid per-cell --max-wall",
        [G(RUN_A_STAR, r"^        a\.max_wall = (\d+) if a\.max_wall is None"),
         J(SHAPE, ["cells", 0, "projected_wall_s"])],
        authoritative="run_a_star.py (grid branch default 2880) and GRID-SHAPE.json projected_wall_s",
        resolution="2880 s = 48 turns x 60 s"))

    out.append(check(
        "grid_hypothesis", "grid --hypothesis",
        [G(RUN_A_STAR, r'a\.hypothesis = a\.hypothesis or "(H2)"'),
         J(SHAPE, ["cells", 0, "hypothesis"])],
        authoritative="run_a_star.py (grid branch default H2) and GRID-SHAPE.json cells[*].hypothesis",
        resolution="H2 — H1 would need n>=60 and is refused at n=48 (docs/GATE-CHAIN.md:292)"))

    out.append(check(
        "ledger_spent", "ledger spent",
        [J(LEDGER, ["budget", "spent"]),
         J(BASELINE, ["requests"]),
         J(BASELINE, ["supersedes", "requests"], role="stale",
           marker="v1 (LEDGER-GRID-BASELINE.json) is a dated record", marker_in=BASELINE)],
        authoritative="REQUEST-LEDGER.json :: budget.spent = 1128 and the frozen pre-grid baseline",
        resolution="1,128 spent; 1,101 is the pre-19:04 baseline superseded by pointer (the 27 are era-A abandoned-cell spend)",
        notes=["GRID-PARAMS.json:117-123 still calls the 27-request gap unresolved (settled_by LEDGER-REBUILD-27); the baseline now closes it"]))

    out.append(check(
        "ledger_remaining", "ledger remaining",
        [J(LEDGER, ["budget", "remaining"]),
         J(BASELINE, ["remaining"]),
         J(PARAMS, ["price", "remaining_before"])],
        authoritative="REQUEST-LEDGER.json :: budget.remaining = 3192",
        resolution="3,192; 3,219 is the superseded pre-19:04 reading",
        notes=["GRID-PARAMS.json chose 3,192 as the conservative of the two (ledger_caveat); the new baseline confirms it"]))

    out.append(check(
        "ledger_cap", "ledger cap",
        [J(LEDGER, ["budget", "cap"]),
         J(BASELINE, ["cap"]),
         G(CELL, r"^PROJECT_QUOTA = (\d+)")],
        authoritative="REQUEST-LEDGER.json :: budget.cap = 4320 and cell.py PROJECT_QUOTA",
        resolution="4,320 (reserve 0; G1 compares cumulative spent against cap - reserve)" ))

    out.append(check(
        "floor_n60", "n>=60 order-statistic floor for p95",
        [C("min_n_for(0.95) from TAIL_MIN=3, MIN_N=20", floor_n(root)),
         G(DOC_RUNBOOK, r"min_n_for\(0\.95\) = (\d+)"),
         L(DOC_RUNBOOK, 341, "min_n_for(0.95)=60", "60"),
         L(DOC_GATECHAIN, 293, "H1 n>=60", "60")],
        authoritative="analyze_stats.py min_n_for(q) = max(MIN_N, ceil(TAIL_MIN/(1-q))) => max(20, 60) = 60",
        resolution="60; a 48-turn cell cannot support H1, so the grid declares H2"))

    return out


def judged_tree(scope):
    return {"generation": scope["generation"],
            "harness_sha256": scope["harness_sha256"],
            "pinned_at": scope["pinned_at"]}


def build(root, scope=None):
    doc = {"schema": "launch-contract-diff/1", "unit": "LAUNCH-CONTRACT-DIFF",
           "offline": {"requests_sent": 0, "network_events": 0, "live_cells": 0},
           "root": ".",
           "operational_rule": OPERATIONAL_RULE,
           "numbers": []}
    if scope:
        doc["judged_tree"] = judged_tree(scope)
    counts = {}
    for chk in checks(root):
        extra = {}
        if scope and chk["id"] == "harness_pin_digest":
            status, probes, reason, extra = classify_scoped(root, chk, scope)
        else:
            status, probes, reason = classify(root, chk)
        counts[status] = counts.get(status, 0) + 1
        values = []
        for p in probes:
            if p["ok"] and p["role"] != "evidence" and not any(
                    same(p["value"], v) for v in values):
                values.append(p["value"])
        occ_rows = []
        for p in probes:
            for o in (p.get("occurrences") or
                      ([_occ(p["line"], p["value"], p["quote"])] if p["ok"] else [])):
                occ_rows.append({"path": p["path"], "line": o["line"],
                                 "value": o["value"],
                                 "role": p.get("resolved") or "load-bearing",
                                 "quote": o["quote"], "problem": p["problem"],
                                 "marker": p["marker"]})
        absent_paths = sorted({p["absent_path"] for p in probes if p.get("absent")})
        row = {
            "id": chk["id"], "label": chk["label"], "status": status,
            "values": values, "reason": reason,
            "absent": absent_paths,
            "occurrence_count": len(occ_rows),
            "authoritative": chk["authoritative"], "resolution": chk["resolution"],
            "owner": chk["owner"], "absent_from": chk["absent_from"],
            "notes": chk["notes"],
            "occurrences": occ_rows}
        if scope and chk["id"] == "harness_pin_digest":
            row["judged_tree"] = judged_tree(scope)
            row["live_harness_sha256"] = extra.get("live_harness_sha256")
            row["moved_inputs"] = extra.get("moved_inputs", [])
        doc["numbers"].append(row)
    doc["price_derivation"] = price_derivation(root)
    moved = [n["id"] for n in doc["numbers"] if n["status"] == "MOVED"]
    # ABSENT is not agreement: a missing field exits non-zero like a disagreement,
    # so a successor can never read exit 0 off a package that never said the number.
    strict = 1 if any(n["status"] in ("DISAGREES", "UNRESOLVED", "ABSENT",
                                      "ANCHOR-MISSING")
                      for n in doc["numbers"]) else 0
    doc["summary"] = {"checks": len(doc["numbers"]),
                      "by_status": counts,
                      "absent": {n["id"]: n["absent"] for n in doc["numbers"]
                                 if n["status"] == "ABSENT"},
                      "disagreements": [n["id"] for n in doc["numbers"]
                                        if n["status"] in ("DISAGREES", "UNRESOLVED")],
                      "anchor_missing": [n["id"] for n in doc["numbers"]
                                         if n["status"] == "ANCHOR-MISSING"],
                      "moved": moved,
                      "check_exit": strict,
                      "unscoped_check_exit": strict}
    if scope:
        # the artefact must not claim 0 for a run that was told to judge a tree it did not get
        doc["summary"]["check_exit"] = EXIT_TREE_MOVED if moved else strict
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=ROOT, help="tree to read (default: this repo)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when any number is DISAGREES or UNRESOLVED, 13 when the "
                         "tree moved under an explicit scope")
    ap.add_argument("--pin-generation", dest="pin_generation", type=int, default=None,
                    metavar="N",
                    help="judge the harness digest against generation N's record in "
                         "HARNESS-PIN.json (resolved through its supersedes chain)")
    ap.add_argument("--tree-sha", dest="tree_sha", default=None, metavar="SHA256",
                    help="judge the harness digest against this harness sha256")
    ap.add_argument("--write", action="store_true",
                    help="write %s/LAUNCH-CONTRACT-DIFF.json under --root" % MEAS)
    ap.add_argument("--json", action="store_true", help="print the document")
    a = ap.parse_args(argv)

    try:
        scope = resolve_scope(a.root, a.pin_generation, a.tree_sha)
    except ValueError as exc:
        print("REFUSED: %s" % exc, file=sys.stderr)
        return EXIT_USAGE

    doc = build(a.root, scope)
    if a.json:
        print(json.dumps(doc, indent=1, sort_keys=False))
    if a.write:
        out = os.path.join(a.root, MEAS, "LAUNCH-CONTRACT-DIFF.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=False)
            fh.write("\n")
    if not a.json:
        for n in doc["numbers"]:
            if n["status"] == "ABSENT" and n["absent"]:
                # absence is a result with a location, not a blank cell
                print("%-15s %-16s ABSENT %s" % (n["status"], n["id"],
                                                 ", ".join(n["absent"])))
                continue
            extra = ("  [occurrences=%d]" % n["occurrence_count"]
                     if n["occurrence_count"] > 1 else "")
            print("%-15s %-16s %s%s" % (n["status"], n["id"],
                                        " | ".join(n["values"]), extra))
        der = doc["price_derivation"]
        if not der["components_present"]:
            print("\nprice: %s recorded (%s)" % (der["total"], der["total_path"]))
            print("price: components ABSENT %s" % der["components_absent_path"])
            print("derivation: %s" % der["arithmetic"])
            print("factor provenance: %s" % der["factor_provenance"])
            if der["caveat"]:
                print("like-for-like: %s" % der["caveat"])
        if der["flag"]:
            print("price_unjustified: the recorded total %s cannot be reconciled with %s" % (
                der["total"], der["arithmetic"]))
        if doc["summary"]["absent"]:
            print("absent: " + ", ".join(sorted(doc["summary"]["absent"])))
        b = doc["summary"]["by_status"]
        print("\n%d numbers: %s" % (doc["summary"]["checks"], ", ".join(
            "%s=%d" % (k, b[k]) for k in sorted(b))))
        if doc["summary"]["disagreements"]:
            print("disagreements: " + ", ".join(doc["summary"]["disagreements"]))
        if doc["summary"]["anchor_missing"]:
            print("anchor-missing (named failure mode, never agreement): "
                  + ", ".join(doc["summary"]["anchor_missing"]))
        if doc.get("judged_tree"):
            jt = doc["judged_tree"]
            print("judged_tree: generation=%s harness_sha256=%s pinned_at=%s" % (
                jt["generation"], jt["harness_sha256"], jt["pinned_at"]))
        for n in doc["numbers"]:
            if n["status"] != "MOVED":
                continue
            for m in n.get("moved_inputs", []):
                print("moved input: %s %s -> %s" % (
                    m["path"], m["recorded_sha256"], m["current_sha256"] or "missing"))
            print("moved digests: scope=%s live=%s" % (
                n["judged_tree"]["harness_sha256"], n["live_harness_sha256"]))
    if a.check:
        return doc["summary"]["check_exit"]
    return 0


if __name__ == "__main__":
    sys.exit(main())
