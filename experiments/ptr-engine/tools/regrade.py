#!/usr/bin/env python3
"""regrade.py - one command that re-derives every published grade from rows.

WHY THIS EXISTS (docs/HARNESS-MAP-V2.md, open item 13): the corpus grades rows
with `grade_v5`, but there was no command that re-derives a published grade. The
loop lived in prose (`measure/REGRADE-DET.md`), `TVS-REGRADE` graded eight files
by hand, and `LATENCY-REPORT-2`/`OPERATOR-BRIEF-2` had to trust whatever grade
file sat beside a rows file. This tool is that loop, made executable.

WHAT IT GUARANTEES
  * A fresh grade is written to a NEW path (`measure/regrade/<rows-stem>.grade-v5.json`);
    an existing file is NEVER overwritten (exit 4).
  * The grader's sha256 is recorded in the output AND on stdout, so a grade carries
    its own provenance. `--sha256` pins the expected digest; a mismatch is exit 3.
  * `--check` regrades in memory and compares against an existing grade file
    dict-wise. Only `generated_at` is ignored (the documented provenance keys that
    legacy v5 grade files simply do not carry are accepted when ABSENT in the old
    document, and a differing recorded sha IS a difference).
  * `--report` prints one row per rows file: pairs, graded, ungraded, grader sha,
    its grade file, and identical|differs|absent.
  * `--as-of` pins `generated_at`, so two runs are byte-identical.

WHAT IT DOES NOT DO: it reproduces the GRADER's output, so a defect in the grader
is reproduced faithfully. It is a reproducibility tool, not a validator. It
performs zero inference requests and reads only the rows, the fixture, the pinned
source tree and the grader.

Exit codes: 0 ok / 1 --check mismatch / 2 unreadable input / 3 grader import or
sha failure / 4 refused overwrite. See docs/REGRADE.md.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)                      # experiments/ptr-engine
MEASURE = os.path.join(ENGINE, "measure")
DEFAULT_GRADER = os.path.join(ENGINE, "longrun", "grade_v5.py")
DEFAULT_FIXTURE = os.path.join(ENGINE, "longrun", "tasks-v5", "runtime-v5",
                               "LR-01.v5.json")
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import grader_identity as gi                       # noqa: E402 - after sys.path

# THE PIN IS AN EXPECTATION, NOT THE IDENTITY (REGRADE-STAMP-WIRE / F1).
# This digest is what this tool was written against. It is NEVER the source of the
# grader's identity: `resolve_grader_identity` reads the grader's bytes at run time
# through the resolver GRADER-STAMP created, and compares them to this value. When
# grade_v5.py changes, regrade reports the drift and keeps working; pass `--sha256`
# to REQUIRE a digest (that is the strict mode, and a mismatch there is exit 3).
EXPECTED_GRADER_SHA = ("056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec5"
                       "5a917a52d9f26772")

# Keys this tool adds to a grade document. They are listed on stdout and accepted
# as "provenance only" when an older grade file predates them. All three stamp keys
# have the same meaning as grade_v5.py's stamp (F2): a regrade output and a fresh
# grade are indistinguishable in provenance.
PROVENANCE_KEYS = ("grader_sha256", "grader_version", "rows_sha256",
                   "grader_path")


class Failure(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def resolve_grader_identity(grader_path, expected=None):
    """Resolve WHO the grader is by hashing it NOW; `expected` is only compared.

    F1: the old DEFAULT_GRADER_SHA was the only source of identity, so when
    GRADER-STAMP changed grade_v5.py's bytes the tool either reported drift that
    was not drift or refused a grade it should reproduce. The sha is derived here
    through `grader_identity.file_sha256` -- the same implementation the writer
    uses -- so a future grader edit cannot silently invalidate the tool: it shows
    up as `drift` (reported) and in every stamp it writes, and `--sha256` can
    still demand an exact digest when reproducibility is the point.
    """
    if not os.path.isfile(grader_path):
        raise Failure(3, "grader not found: %s" % grader_path)
    actual = gi.file_sha256(grader_path)
    pin = expected if expected is not None else EXPECTED_GRADER_SHA
    return {"sha256": actual, "path": os.path.abspath(grader_path),
            "expected": pin, "drift": bool(pin) and actual != pin,
            "source": "resolved"}


def load_grader(path):
    """Import the grader module by path. Its own path setup is preserved."""
    if not os.path.isfile(path):
        raise Failure(3, "grader not found: %s" % path)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location("regrade_grader", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                          # noqa: BLE001 - contract
        raise Failure(3, "grader import failed: %s: %s" % (type(exc).__name__, exc))
    for attr in ("grade_rows", "load_fixture"):
        if not hasattr(mod, attr):
            raise Failure(3, "grader %s lacks %s()" % (path, attr))
    return mod


def load_rows(path):
    if not os.path.isfile(path):
        raise Failure(2, "rows file not found: %s" % path)
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError as exc:
                    raise Failure(2, "rows %s:%d is not JSON: %s"
                                  % (path, lineno, exc))
    except OSError as exc:
        raise Failure(2, "rows unreadable %s: %s" % (path, exc))
    return rows


def load_fixture(grader, path):
    if not os.path.isfile(path):
        raise Failure(2, "fixture not found: %s" % path)
    try:
        return grader.load_fixture(path)
    except Exception as exc:                          # noqa: BLE001 - input
        raise Failure(2, "fixture unreadable %s: %s" % (path, exc))


def label_path(path, like=None):
    """A stable label for the document. In --check mode adopt the old label."""
    if like:
        return like
    p = os.path.abspath(path)
    engine = os.path.abspath(ENGINE)
    if p.startswith(engine + os.sep):
        return os.path.relpath(p, engine)
    return p


def regrade(grader, rows_path, fixture_path, grader_path, as_of=None, like=None,
            identity=None):
    rows = load_rows(rows_path)
    fixture = load_fixture(grader, fixture_path)
    try:
        doc = grader.grade_rows(fixture, rows)
    except Exception as exc:                          # noqa: BLE001 - grader
        raise Failure(2, "grader failed on %s: %s: %s"
                      % (rows_path, type(exc).__name__, exc))
    doc["rows_file"] = label_path(rows_path, (like or {}).get("rows_file"))
    doc["fixture_file"] = label_path(fixture_path, (like or {}).get("fixture_file"))
    doc["grader_path"] = os.path.abspath(grader_path)
    # F2: all three stamp keys, with grade_v5.py's meaning, resolved at run time.
    # `grader_version` comes from the loaded grader module; both shas come from
    # grader_identity's one implementation. A stamp that cannot be built is a
    # refused grade (exit 3), never an unstamped document (GRADER-STAMP's rule).
    ident = identity or resolve_grader_identity(grader_path)
    doc["grader_sha256"] = ident["sha256"]
    doc["grader_version"] = getattr(grader, "GRADER_VERSION", None)
    doc["rows_sha256"] = gi.file_sha256(rows_path)
    try:
        gi.grader_identity(doc)                       # validates the whole stamp
    except (ValueError, TypeError) as exc:
        raise Failure(3, "stamp_uncomputable: %s" % exc)
    if as_of:
        doc["generated_at"] = as_of
    return doc


def write_new(doc, out_path):
    if os.path.exists(out_path):
        raise Failure(4, "refusing overwrite: %s already exists" % out_path)
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(dump(doc))
    return out_path


def dump(doc):
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


# ------------------------------------------------------------------ discovery
def grade_index(paths):
    """basename(rows_file) -> grade path, from any grade documents we can read."""
    index = {}
    for p in sorted(paths):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        rf = d.get("rows_file")
        if not isinstance(rf, str):
            continue
        key = os.path.basename(rf)
        index.setdefault(key, p)
    return index


def default_grade_paths(measure):
    out = []
    for name in sorted(os.listdir(measure)) if os.path.isdir(measure) else []:
        if name.endswith(".grade-v5.json"):
            out.append(os.path.join(measure, name))
    return out


def _resolve_label(label):
    """Resolve a grade's recorded rows_file to a real path, or None."""
    if not isinstance(label, str):
        return None
    cands = [label] if os.path.isabs(label) else [
        os.path.join(ENGINE, label), os.path.join(os.getcwd(), label)]
    for c in cands:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return None


def find_grade(rows_path, measure, explicit=None):
    """The existing grade document for THIS rows file.

    A basename is not identity: `.cell-demo/rows.jsonl` and `measure/rows.jsonl`
    share one. When a recorded label resolves on disk the match must be the same
    file; the basename fallback is used only for labels that do not resolve.
    """
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    target = os.path.abspath(rows_path)
    for p in default_grade_paths(measure):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        rf = d.get("rows_file")
        resolved = _resolve_label(rf)
        if resolved is not None:
            if os.path.samefile(resolved, target):
                return p
        elif (isinstance(rf, str) and not os.path.dirname(rf)
              and os.path.basename(rf) == os.path.basename(rows_path)):
            return p
    return None


# ------------------------------------------------------------------- compare
def _walk_diff(new, old, path="", out=None):
    out = [] if out is None else out
    if isinstance(new, dict) and isinstance(old, dict):
        for k in sorted(set(new) | set(old)):
            p = "%s.%s" % (path, k) if path else k
            if k not in old:
                out.append((p, "missing-in-grade", new[k]))
            elif k not in new:
                out.append((p, "missing-in-regrade", old[k]))
            else:
                _walk_diff(new[k], old[k], p, out)
        return out
    if isinstance(new, list) and isinstance(old, list):
        if len(new) != len(old):
            out.append((path + ".length", len(old), len(new)))
            return out
        for i, (a, b) in enumerate(zip(new, old)):
            _walk_diff(a, b, "%s[%d]" % (path, i), out)
        return out
    if new != old:
        out.append((path, old, new))
    return out


def compare_docs(new, old):
    """Dict-wise comparison ignoring only `generated_at`.

    Returns (differences, provenance_only). A provenance key is `provenance_only`
    only when the old document predates it; a key the old document DOES carry is
    compared normally (so a wrong recorded grader sha is a difference).
    """
    new = dict(new)
    new.pop("generated_at", None)
    old = dict(old)
    old.pop("generated_at", None)
    provenance = []
    for k in PROVENANCE_KEYS:
        if k in new and k not in old:
            provenance.append((k, new.pop(k)))
    # The label of the same file may be written relative or absolute; when the old
    # document names it, the regenerated document adopts that label (same file).
    for k in ("rows_file", "fixture_file"):
        if k in old and k in new and os.path.basename(str(old[k])) == \
                os.path.basename(str(new[k])):
            new[k] = old[k]
    diffs = _walk_diff(new, old)
    return diffs, provenance


def show_diff(diffs, limit=40):
    for path, old, new in diffs[:limit]:
        print("DIFF %s: grade=%r regrade=%r" % (path, old, new))
    if len(diffs) > limit:
        print("DIFF ... %d more" % (len(diffs) - limit))


# ---------------------------------------------------------------------- table
def counts(doc):
    pairs = len(doc.get("arms", {}))
    graded = sum(1 for c in doc.get("cells", [])
                 if c.get("verdict") in ("pass", "fail"))
    ungraded = len(doc.get("cells", [])) - graded
    return pairs, graded, ungraded


def report(rows_files, args, grader, grader_sha, identity=None):
    print("%-52s %5s %7s %9s %-16s %-44s %s" % (
        "rows_file", "pairs", "graded", "ungraded", "grader_sha256",
        "grade_file", "check"))
    rows_out = []
    for rows_path in rows_files:
        grade_path = find_grade(rows_path, args.measure)
        status, detail = "absent", ""
        if grade_path:
            try:
                with open(grade_path, "r", encoding="utf-8") as fh:
                    old = json.load(fh)
                doc = regrade(grader, rows_path, args.fixture, args.grader,
                              as_of=args.as_of, identity=identity,
                              like={k: old.get(k) for k in
                                    ("rows_file", "fixture_file")})
                diffs, _ = compare_docs(doc, old)
                status = "identical" if not diffs else "differs"
                if diffs:
                    detail = diffs[0][0]
            except Failure as exc:
                status, detail = "unreadable", exc.message
                doc = None
        else:
            doc = regrade(grader, rows_path, args.fixture, args.grader,
                          as_of=args.as_of, identity=identity)
        pairs, graded, ungraded = counts(doc) if doc else (0, 0, 0)
        print("%-52s %5d %7d %9d %-16s %-44s %s%s" % (
            os.path.relpath(rows_path, ENGINE) if rows_path.startswith(ENGINE)
            else rows_path,
            pairs, graded, ungraded, grader_sha[:16],
            os.path.basename(grade_path) if grade_path else "-", status,
            (" (%s)" % detail) if detail else ""))
        rows_out.append({
            "rows_file": label_path(rows_path),
            "pairs": pairs, "graded": graded, "ungraded": ungraded,
            "grader_sha256": grader_sha,
            "grade_file": grade_path,
            "check": status,
            "first_difference": detail or None,
        })
    return rows_out


def collect_rows(args):
    if args.rows:
        return [os.path.abspath(p) for p in args.rows]
    files = []
    for name in sorted(os.listdir(args.measure)):
        if name.startswith("rows") and name.endswith(".jsonl"):
            files.append(os.path.join(args.measure, name))
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Re-derive a grade from rows, deterministically (offline).")
    ap.add_argument("--rows", action="append",
                    help="rows file (.jsonl); repeatable")
    ap.add_argument("--all", action="store_true",
                    help="every rows*.jsonl under --measure")
    ap.add_argument("--measure", default=MEASURE)
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--grader", default=DEFAULT_GRADER)
    ap.add_argument("--sha256", default=None,
                    help="REQUIRE this grader sha256 (default: resolve the digest "
                         "from the grader and only report drift vs %s)"
                         % EXPECTED_GRADER_SHA)
    ap.add_argument("--out-dir", default=os.path.join(MEASURE, "regrade"))
    ap.add_argument("--as-of", default=None,
                    help="pin generated_at verbatim for byte-identical reruns")
    ap.add_argument("--check", action="store_true",
                    help="compare against the existing grade; never writes")
    ap.add_argument("--grade", default=None,
                    help="existing grade to compare in --check mode")
    ap.add_argument("--report", action="store_true",
                    help="table over every rows file")
    args = ap.parse_args(argv)

    grader_path = os.path.abspath(args.grader)
    try:
        identity = resolve_grader_identity(grader_path, args.sha256)
    except Failure as exc:
        print("ERROR %s" % exc.message)
        return exc.code
    actual = identity["sha256"]
    if args.sha256 and actual != args.sha256:
        print("ERROR grader sha256 mismatch: file=%s expected=%s"
              % (actual, args.sha256))
        return 3
    if identity["drift"]:
        print("NOTE grader sha256 drift: resolved=%s expected-pin=%s "
              "(identity resolved at run time; pass --sha256 to require a digest)"
              % (actual, identity["expected"]))
    try:
        grader = load_grader(grader_path)
    except Failure as exc:
        print("ERROR %s" % exc.message)
        return exc.code
    print("grader=%s sha256=%s source=%s" % (grader_path, actual,
                                             identity["source"]))

    try:
        rows_files = collect_rows(args)
        if not rows_files:
            raise Failure(2, "no rows files selected")

        if args.report:
            table = report(rows_files, args, grader, actual, identity=identity)
            out_json = os.path.join(args.measure, "REGRADE.json")
            doc = {
                "unit": "REGRADE-ONE-COMMAND",
                "command": " ".join(sys.argv[1:]),
                "rule": "Re-derivation only: each row is the grader's current "
                        "output over an existing rows file, compared dict-wise "
                        "against the grade file already on disk. No number here "
                        "is a new measurement.",
                "generated_at": args.as_of,
                "grader": os.path.basename(grader_path),
                "grader_sha256": actual,
                "fixture": args.fixture,
                "rows": table,
            }
            if args.as_of:
                doc["generated_at"] = args.as_of
            with open(out_json, "w", encoding="utf-8") as fh:
                fh.write(dump(doc))
            print("report: %s (%d rows files)" % (out_json, len(table)))
            return 0

        failures = 0
        for rows_path in rows_files:
            if args.check:
                grade_path = find_grade(rows_path, args.measure, args.grade)
                if not grade_path:
                    raise Failure(2, "no existing grade for %s" % rows_path)
                with open(grade_path, "r", encoding="utf-8") as fh:
                    old = json.load(fh)
                doc = regrade(grader, rows_path, args.fixture, grader_path,
                              as_of=args.as_of, identity=identity,
                              like={k: old.get(k) for k in
                                    ("rows_file", "fixture_file")})
                diffs, provenance = compare_docs(doc, old)
                if diffs:
                    failures += 1
                    print("DIFFERS %s vs %s" % (os.path.basename(rows_path),
                                                os.path.basename(grade_path)))
                    show_diff(diffs)
                else:
                    print("IDENTICAL %s (grader_sha256=%s)"
                          % (os.path.basename(rows_path), doc["grader_sha256"]))
                for k, v in provenance:
                    print("  provenance-only %s=%s" % (k, v))
                continue

            doc = regrade(grader, rows_path, args.fixture, grader_path,
                          as_of=args.as_of, identity=identity)
            stem = os.path.splitext(os.path.basename(rows_path))[0]
            out_path = os.path.join(args.out_dir, stem + ".grade-v5.json")
            write_new(doc, out_path)
            pairs, graded, ungraded = counts(doc)
            print("wrote %s  pairs=%d graded=%d ungraded=%d grader_sha256=%s"
                  % (out_path, pairs, graded, ungraded, doc["grader_sha256"]))
        return 1 if failures else 0
    except Failure as exc:
        print("ERROR %s" % exc.message)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
