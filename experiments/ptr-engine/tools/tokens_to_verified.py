#!/usr/bin/env python3
"""tokens_to_verified.py -- tokens-to-verified-success (TVS) for the LR-01 grids.

TVS = prompt_tokens + completion_tokens summed over every DISTINCT request the run
billed from its first request through the checkpoint's own turn, inclusive, for the
FIRST checkpoint that the instrument of record graded `pass`.

ROWS IDENTITY (TVS-ROWS-IDENTITY). A TVS figure is a function of one rows file's
BYTES. Every emitted record therefore carries the stamp

    rows_file, rows_sha256, rows_size, computed_at, grader_sha256

where `rows_sha256` is the sha256 of the exact bytes that were parsed (read once,
hashed, then decoded -- never hash-after-parse of a second read), and
`grader_sha256` is resolved through tools/grader_identity.py from the grade
document itself. No pin is hardcoded as an answer: `INSTRUMENT_SHA_PIN` below is a
DECLARED historical claim, used only to compute a `pin_check` fact, never written
as this record's grader identity. When the grade document carries no stamp (every
historical grade_v5 file) `grader_sha256` is null and `grader_sha_source` says
`unstamped_grade_document` -- the honest value, because re-grading is a different
unit's job and the current grader bytes are not the bytes that graded these runs.

REFUSAL, NOT GUESSING. If the rows file is missing, unreadable, or does not match a
sha the caller supplied, the tool exits 2 with reason `rows_missing`,
`rows_unreadable` or `rows_sha_mismatch` (naming both shas) and emits NO tvs
number. A figure that cannot name its bytes is not printed.

Instrument of record: experiments/ptr-engine/longrun/grade_v5.py

Offline: reads row/grade files only, issues zero inference requests, writes nothing
unless --json/--all is given.

Usage:
  tokens_to_verified.py --rows FILE --grade FILE [--arm A] [--cutoff-turn N|--whole-run]
                        [--expect-rows-sha256 SHA]
  tokens_to_verified.py --all --json OUT
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PTR = os.path.dirname(TOOLS_DIR)              # experiments/ptr-engine
MEASURE = os.path.join(PTR, "measure")
GRADER_PATH = os.path.join(PTR, "longrun", "grade_v5.py")

sys.path.insert(0, TOOLS_DIR)
from grader_identity import (                                  # noqa: E402
    STAMP, file_sha256, grader_identity, missing_stamp_keys,
)

# The five fields every emitted tvs record carries (TVS-ROWS-IDENTITY).
ROWS_STAMP_FIELDS = ("rows_file", "rows_sha256", "rows_size", "computed_at", "grader_sha256")

# A DECLARED historical claim (docs/TVS.md:5-7), used only to report a `pin_check`
# fact. It is never used as a record's grader identity, and never as a fallback sha.
INSTRUMENT_SHA_PIN = "6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077"

INSTRUMENT = {
    "grader": "grade_v5",
    "path": "experiments/ptr-engine/longrun/grade_v5.py",
    "sha256": INSTRUMENT_SHA_PIN,
    "sha256_status": "declared claim (docs/TVS.md:5-7); reported as pin_check, never bound to a record",
    "rule": "ANSWER-CONTRACT v1 (forced one-line answer, value graded against AST truth)",
}

DEFINITION = {
    "tokens": "prompt_tokens + completion_tokens per request row (all prompt tokens, cached and uncached). "
              "A row with a null prompt_tokens or completion_tokens is EXCLUDED from the sum and counted in "
              "tvs.excluded_null_token_rows; it is never treated as 0.",
    "cached_share": "sum(cached_tokens)/sum(prompt_tokens) over rows whose cached_tokens is non-null; "
                    "reported as a diagnostic only, never in place of the primary number.",
    "verified_success": "a checkpoint cell whose verdict is `pass` under grade_v5 (the instrument of record). "
                        "A cell with verdict `fail` or `undecidable` is not a success.",
    "window": "every DISTINCT request from the run's first request through the checkpoint's own turn, "
              "inclusive; fetch/tool-follow-up requests at that turn are included because they bill. "
              "Duplicate records of one request (same arm/rep/turn/ts/prompt/completion/content_sha256) are "
              "counted once and reported as duplicate_records_skipped.",
    "first_success": "the earliest passing checkpoint turn; later passes do not change the number.",
    "no_success": "tvs is null with reason 'no_verified_success' -- never 0, never the whole-run total.",
    "pooling": "never pooled across grids; a grid whose code changed mid-cell carries that fact beside the number.",
    "identity": "every emitted record carries rows_file/rows_sha256/rows_size/computed_at/grader_sha256. "
                "rows_sha256 is the sha256 of the bytes actually parsed; grader_sha256 is the grade document's "
                "own stamp resolved through tools/grader_identity.py, or null when that document is unstamped "
                "(grader_sha_source names which). A record that cannot name its rows bytes is REFUSED and "
                "carries no number.",
}

IDENTITY = ("arm", "rep", "turn", "ts", "prompt_tokens", "completion_tokens", "content_sha256")


class RowsRefusal(Exception):
    """The rows file cannot be bound to bytes. No number may be printed."""

    def __init__(self, reason, rows_file, detail="", expected_sha256=None, actual_sha256=None):
        self.reason = reason
        self.rows_file = rows_file
        self.detail = detail
        self.expected_sha256 = expected_sha256
        self.actual_sha256 = actual_sha256
        msg = "%s: %s" % (reason, rows_file)
        if reason == "rows_sha_mismatch":
            msg += " (expected sha256 %s, actual sha256 %s)" % (expected_sha256, actual_sha256)
        elif detail:
            msg += " (%s)" % detail
        super().__init__(msg)

    def as_dict(self):
        out = {"reason": self.reason, "rows_file": self.rows_file}
        if self.detail:
            out["detail"] = self.detail
        if self.reason == "rows_sha_mismatch":
            out["expected_sha256"] = self.expected_sha256
            out["actual_sha256"] = self.actual_sha256
        out["number_emitted"] = False
        return out


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_rows_bytes(rows_path, expect_sha256=None, expect_size=None):
    """Return (bytes, sha256) of the ONE read that is later parsed. Refuses rather than guesses."""
    if not rows_path or not os.path.isfile(rows_path):
        raise RowsRefusal("rows_missing", rows_path or "<none>", "no such file")
    try:
        with open(rows_path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        raise RowsRefusal("rows_unreadable", rows_path, str(exc))
    sha = hashlib.sha256(data).hexdigest()
    if expect_sha256 and expect_sha256.strip().lower() != sha:
        raise RowsRefusal("rows_sha_mismatch", rows_path,
                          expected_sha256=expect_sha256.strip().lower(), actual_sha256=sha)
    if expect_size is not None and int(expect_size) != len(data):
        raise RowsRefusal("rows_sha_mismatch", rows_path,
                          "size expected %s, actual %s" % (expect_size, len(data)),
                          expected_sha256=expect_sha256, actual_sha256=sha)
    return data, sha


def load_rows(rows_path, expect_sha256=None, expect_size=None):
    """Parse the same bytes whose sha256 is returned. -> (rows, {"rows_sha256","rows_size"})"""
    data, sha = read_rows_bytes(rows_path, expect_sha256=expect_sha256, expect_size=expect_size)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RowsRefusal("rows_unreadable", rows_path, "not utf-8: %s" % exc)
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows, {"rows_sha256": sha, "rows_size": len(data)}


def grader_stamp(grade_path):
    """Resolve the grade document's identity THROUGH grader_identity.py -- never a pin.

    unstamped document -> sha256 is None (grader_identity refuses to invent one) and
    grader_sha_source says so. A stamped document -> its own grader_sha256.
    """
    grade_sha = None
    doc = None
    try:
        with open(grade_path, "rb") as fh:
            raw = fh.read()
        grade_sha = hashlib.sha256(raw).hexdigest()
        doc = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        doc = None
    ident = grader_identity(doc) if isinstance(doc, dict) else {
        "sha256": None, "source": "derived", "stamped": False,
        "missing": list(("grader_sha256", "grader_version", "rows_sha256")),
        "requires": "regrade_result",
    }
    grader_now = None
    if os.path.isfile(GRADER_PATH):
        try:
            grader_now = file_sha256(GRADER_PATH)
        except OSError:
            grader_now = None
    return {
        "grader_sha256": ident.get("sha256"),
        "grader_sha_source": (STAMP if ident.get("source") == STAMP else "unstamped_grade_document"),
        "grader_identity": ident,
        "grader_file_sha256_now": grader_now,
        "grade_file": grade_path,
        "grade_sha256": grade_sha,
        "grade_stamp_missing": ([] if isinstance(doc, dict) and not missing_stamp_keys(doc)
                                else list(ident.get("missing") or [])),
        "grader_pin_check": {
            "declared_sha256": INSTRUMENT_SHA_PIN,
            "declared_in": "docs/TVS.md:5-7 (and INSTRUMENT below)",
            "grader_file_sha256_now": grader_now,
            "match": (grader_now == INSTRUMENT_SHA_PIN) if grader_now else None,
        },
    }


def dedupe(rows):
    """Collapse byte-identical repeat records of one billed request; keep order."""
    seen = set()
    out = []
    for r in rows:
        key = tuple(r.get(k) for k in IDENTITY)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out, len(rows) - len(out)


def tokens_through(rows, turn, arm=None):
    prompt = completion = cached = cached_prompt = 0
    excluded = 0
    counted = 0
    null_turns = []
    for r in rows:
        if arm is not None and r.get("arm") != arm:
            continue
        t = r.get("turn")
        if not isinstance(t, int) or t > turn:
            continue
        counted += 1
        p, c = r.get("prompt_tokens"), r.get("completion_tokens")
        if p is None or c is None:
            excluded += 1
            null_turns.append(t)
            continue
        prompt += int(p)
        completion += int(c)
        ca = r.get("cached_tokens")
        if ca is not None:
            cached += int(ca)
            cached_prompt += int(p)
    return {
        "turn": turn,
        "tokens": prompt + completion,
        "prompt": prompt,
        "completion": completion,
        "cached_share": (round(cached / cached_prompt, 4) if cached_prompt else None),
        "cached_tokens": cached,
        "requests_counted": counted - excluded,
        "excluded_null_token_rows": excluded,
        "null_token_turns": null_turns,
    }


def grade_passes(grade):
    """{(arm): [(checkpoint_id, turn, reason)]} for cells PASSED by the grade file's own instrument.

    grade_v5 shape: cells[] with verdict; grade_v3/grade_v4 shape: arms[arm].checks[] with pass.
    Constraint checks (acc.*) are never successes; only checkpoint ids are.
    """
    res = {}
    cells = grade.get("cells")
    if isinstance(cells, list) and cells and "verdict" in cells[0]:
        for c in cells:
            if c.get("verdict") != "pass":
                continue
            arm = c.get("arm") or "<none>"
            res.setdefault(arm, []).append((c.get("id"), c.get("turn"), c.get("reason")))
    else:
        for arm, a in (grade.get("arms") or {}).items():
            for chk in (a.get("checks") or []):
                cid = chk.get("id") or ""
                if chk.get("pass") is True and cid.startswith("cp."):
                    res.setdefault(arm, []).append((cid, chk.get("turn"), chk.get("reason")))
    return res


def declared_space(grade):
    """The checkpoint ids the instrument actually graded, in file order."""
    cells = grade.get("cells")
    ids = []
    if isinstance(cells, list) and cells and "verdict" in cells[0]:
        for c in cells:
            if c.get("id"):
                ids.append(c["id"])
    else:
        for _arm, a in (grade.get("arms") or {}).items():
            for chk in (a.get("checks") or []):
                cid = chk.get("id") or ""
                if cid.startswith("cp.") and cid not in ids:
                    ids.append(cid)
    return ids


def arms_in(rows):
    seen = []
    for r in rows:
        a = r.get("arm")
        if a not in seen:
            seen.append(a)
    return seen


def mid_cell_note(grid):
    if "v6" in grid:
        return {
            "mid_cell_code_change": True,
            "detail": "V6 ran turns 1-6 before a correction, then turns 7-48. The summed window for a "
                      "checkpoint at turn >= 7 therefore spans two code states; the number is carried beside "
                      "this fact, never as if the cell were homogeneous.",
        }
    return {"mid_cell_code_change": False, "detail": ""}


def analyse(rows_path, grade_path=None, arm=None, grid=None, cutoff_turn=None, whole_run=False,
            expect_rows_sha256=None, expect_rows_size=None):
    """One cell. Never raises for the normal cases: missing grade, no checkpoints, nulls, zero successes.

    RAISES RowsRefusal when the rows bytes cannot be bound -- the caller must print no number.
    """
    rows, rident = load_rows(rows_path, expect_sha256=expect_rows_sha256, expect_size=expect_rows_size)
    computed_at = utc_now()
    deduped, dup_skipped = dedupe(rows)
    grid = grid or os.path.splitext(os.path.basename(rows_path))[0]
    arm = arm if arm is not None else (arms_in(deduped) or [None])[0]

    stamp = {
        "rows_file": rows_path,
        "rows_sha256": rident["rows_sha256"],
        "rows_size": rident["rows_size"],
        "computed_at": computed_at,
        "grader_sha256": None,
    }
    if grade_path:
        gs = grader_stamp(grade_path)
        stamp.update(gs)

    out = {
        "grid": grid,
        "arm": arm,
        "declared_space": None,
        "pass_turns": [],
        "tvs": None,
        "reason": None,
        "duplicate_records_skipped": dup_skipped,
        "rows_in_file": len(rows),
        "requests_distinct": len(deduped),
        "stamps": dict(stamp),
    }
    out.update({k: stamp[k] for k in ROWS_STAMP_FIELDS})
    out.update({k: v for k, v in stamp.items() if k not in ROWS_STAMP_FIELDS})

    if not grade_path or not os.path.exists(grade_path):
        out["reason"] = "not_produced_no_grade_file"
        return out
    try:
        with open(grade_path, encoding="utf-8") as fh:
            grade = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        out["reason"] = "not_produced_unreadable_grade_file: %s" % exc
        return out

    out["declared_space"] = declared_space(grade)
    passes = grade_passes(grade)
    if arm is None:
        arm = (list(passes) or [None])[0]
        out["arm"] = arm
    cell_passes = sorted(passes.get(arm, []), key=lambda t: (t[1] is None, t[1]))
    out["pass_turns"] = [{"id": cid, "turn": t, "reason": r} for cid, t, r in cell_passes]

    if not cell_passes:
        out["reason"] = "no_verified_success"
        return out

    real = [t for _cid, t, _r in cell_passes if isinstance(t, int)]
    if not real:
        out["reason"] = "no_verified_success"     # a pass with no turn cannot be located in time
        return out
    first = min(real)
    if whole_run or cutoff_turn is not None and cutoff_turn < first:
        first = max(t for t in (r.get("turn") for r in deduped) if isinstance(t, int))
    tvs = tokens_through(deduped, first, arm=arm)
    tvs["grid_arm_rows"] = sum(1 for r in deduped if r.get("arm") == arm)
    tvs.update({k: stamp[k] for k in ROWS_STAMP_FIELDS})   # the tvs record carries the identity
    out["tvs"] = tvs
    out["whole_run_total"] = sum(
        (r.get("prompt_tokens") or 0) + (r.get("completion_tokens") or 0)
        for r in deduped if r.get("arm") == arm
    )
    out["code_state"] = mid_cell_note(grid)
    return out


def refusal_record(rows_path, refusal, grid=None, arm=None):
    """A refused record: names the reason and both shas where they exist, carries NO number."""
    return {
        "grid": grid or os.path.splitext(os.path.basename(rows_path or ""))[0],
        "arm": arm,
        "declared_space": None,
        "pass_turns": [],
        "tvs": None,
        "reason": refusal.reason,
        "refused": True,
        "refusal": refusal.as_dict(),
        "rows_file": rows_path,
        "computed_at": utc_now(),
        # no rows_sha256 / rows_size: they are exactly what could not be established
    }


def cell_grade_files():
    """measure/cell-*.grade-v5.json -> {rows_file basename: path} (the declared-grid grade_v5 outputs)."""
    mapping = {}
    for path in sorted(glob.glob(os.path.join(MEASURE, "cell-*.grade-v5.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                g = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        rf = g.get("rows_file")
        if rf:
            mapping[os.path.basename(rf)] = path
    return mapping


def build_all():
    g5 = cell_grade_files()
    cells = []
    secondary = []
    out_of_scope = []
    refused = []
    for rows_path in sorted(glob.glob(os.path.join(MEASURE, "rows-*.jsonl"))):
        base = os.path.basename(rows_path)
        grid = os.path.splitext(base)[0]
        try:
            rows = dedupe(load_rows(rows_path)[0])[0]
        except RowsRefusal as exc:
            cells.append(refusal_record(rows_path, exc, grid=grid))
            refused.append(exc.as_dict())
            continue
        if not base.startswith("rows-longrun-"):
            out_of_scope.append({"rows_file": base, "arms": arms_in(rows),
                                 "why": "not a declared long-run grid (declared space = rows-longrun-*.jsonl "
                                        "carrying the LR-01 fixture task_id)"})
            continue
        arms = arms_in(rows)
        if base in g5:
            for arm in arms:
                cells.append(analyse(rows_path, g5[base], arm=arm, grid=grid))
        else:
            for arm in arms:
                cells.append({"grid": grid, "arm": arm, "declared_space": None, "pass_turns": [],
                              "tvs": None, "reason": "not_produced_no_grade_v5",
                              "note": "grade_v3/grade_v4 outputs exist for this grid but are not the "
                                      "instrument of record; no grade_v5 output was produced for it."})
        # secondary instruments: report their passes, clearly labelled, never certified
        for version in ("grade-v4", "grade-v3"):
            gpath = os.path.join(MEASURE, "%s.%s.json" % (grid, version))
            if not os.path.exists(gpath):
                continue
            with open(gpath, encoding="utf-8") as fh:
                grade = json.load(fh)
            if version == "grade-v3" and os.path.exists(
                    os.path.join(MEASURE, "%s.grade-v3-final.json" % grid)):
                gpath = os.path.join(MEASURE, "%s.grade-v3-final.json" % grid)
                with open(gpath, encoding="utf-8") as fh:
                    grade = json.load(fh)
            for arm, plist in grade_passes(grade).items():
                if not plist:
                    continue
                c = analyse(rows_path, gpath, arm=arm, grid=grid)
                c["instrument"] = version
                c["certified"] = False
                secondary.append(c)
            break  # prefer the newest legacy instrument present for this grid

    pass_cells = [c for c in cells if c.get("tvs") is not None]
    return {
        "unit": "TVS-DEFINE-AND-COMPUTE",
        "definition": DEFINITION,
        "instrument": INSTRUMENT,
        "identity": {
            "fields": list(ROWS_STAMP_FIELDS),
            "rows_sha256": "sha256 of the exact bytes parsed (one read, hashed then decoded)",
            "grader_sha256": "the grade document's own stamp via tools/grader_identity.py; null when unstamped",
            "refusal": "rows_missing / rows_unreadable / rows_sha_mismatch -> exit 2, no number emitted",
            "computed_at": "UTC ISO-8601 at read time; a restamp records its own date",
        },
        "denominator": {
            "declared_run_arm_pairs": len(cells),
            "pairs_with_grade_v5_output": sum(1 for c in cells
                                              if c.get("reason") != "not_produced_no_grade_v5"),
            "pairs_with_verified_success": len(pass_cells),
            "pairs_null_no_verified_success": sum(1 for c in cells
                                                  if c.get("reason") == "no_verified_success"),
            "pairs_not_produced": sum(1 for c in cells if c.get("reason") == "not_produced_no_grade_v5"),
            "pairs_refused_rows_unbound": len(refused),
            "refusals": refused,
            "pairs_not_produced_why": "no grade_v5 output exists; grade_v3/grade_v4 are not the instrument of record",
            "repair_t30": "dropped from TVS's declared space: grade_v5 emits no verdict for it, so it can neither "
                          "certify a success nor sit in the denominator",
        },
        "cells": cells,
        "secondary_instrument_cells": secondary,
        "out_of_scope_row_files": out_of_scope,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="tokens to verified success (grade_v5 of record)")
    ap.add_argument("--rows")
    ap.add_argument("--grade")
    ap.add_argument("--arm")
    ap.add_argument("--grid")
    ap.add_argument("--cutoff-turn", type=int, default=None,
                    help="debug/red-green: force the window to end at this turn")
    ap.add_argument("--whole-run", action="store_true",
                    help="debug/red-green: sum the whole run instead of through the pass turn")
    ap.add_argument("--expect-rows-sha256", default=None,
                    help="refuse (rows_sha_mismatch) unless the rows bytes hash to this sha256")
    ap.add_argument("--expect-rows-size", type=int, default=None,
                    help="refuse (rows_sha_mismatch) unless the rows file is this many bytes")
    ap.add_argument("--all", action="store_true", help="walk measure/rows-*.jsonl")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    exit_code = 0
    if args.all:
        doc = build_all()
        if doc["denominator"]["pairs_refused_rows_unbound"]:
            exit_code = 2
    elif args.rows:
        try:
            doc = analyse(args.rows, args.grade, arm=args.arm, grid=args.grid,
                          cutoff_turn=args.cutoff_turn, whole_run=args.whole_run,
                          expect_rows_sha256=args.expect_rows_sha256,
                          expect_rows_size=args.expect_rows_size)
        except RowsRefusal as exc:
            doc = refusal_record(args.rows, exc, grid=args.grid, arm=args.arm)
            exit_code = 2
            sys.stderr.write("REFUSED %s\n" % exc)
    else:
        ap.error("give --rows/--grade or --all")

    text = json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=False)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
