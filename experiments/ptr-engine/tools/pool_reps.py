#!/usr/bin/env python3
"""pool_reps.py -- assemble ONE arm's pooled R-all view from N per-rep rows files.

WHY THIS EXISTS
---------------
H1-CONDITIONING (PASS f17663d1) froze R-all = every completed turn, n = 144 per arm
(3 reps x 48 turns) as the only admissible H1 reading. TURN-CENSUS-60 then found that
no rows file on disk holds more than one rep, and that no single cell reaches the
frozen n >= 60 floor: with 48 turns per rep, 48 * (1 - 0.95) = 2.4 < TAIL_MIN = 3, so
`analyze_stats.quantile_ci(q=0.95)` REFUSES a per-rep p95 by arithmetic. The one
decisive number therefore depends on a pooling step that did not exist.

WHAT THIS IS, AND IS NOT
------------------------
The output is a DERIVED artefact, never a measurement: every pooled row carries
`derived: true`, the manifest carries `derived: true` and
`purpose: "H1 pooled R-all"`, the file lives under `measure/pooled/` and is named
`pooled-*` (never `rows-*`, never `rows-cell-*`). `analyze_stats` refuses to read it
unless `--pooled` is passed explicitly, so a derived file can never be mistaken for a
measured cell by an incidental glob.

Rows are read, never written: this tool is read-only on every input.

REFUSALS (each named, none silent)
----------------------------------
  insufficient_reps        fewer than --reps (default 3) comparable source files: a
                           pair-only or 1-rep pool is not H1's n=144 (and H3 needs
                           b + c >= 6, H1 needs n >= 60)
  incomparable_provenance  sources differ on fixture_sha256 / harness_sha256 / model /
                           tools_mode; the message names the field and both values
  era_a_excluded           a source is era A (or era unknown, which defaults to A):
                           era B is never pooled with era A
  source_unusable          a source is stamped `usable_for: []`
  source_unreadable        a source cannot be read or holds no JSON rows
  rows_sha_mismatch        a manifest declares a digest that the rows file does not have
  duplicate_source         the same path was passed twice (one cell counted twice)
  source_derived           a source is itself a pooled/derived file (double pooling)
  invalid_arm              the arm name cannot be used in a filename

CLI
---
  python3 experiments/ptr-engine/tools/pool_reps.py \
      --arm pointer-stable --rows a.jsonl b.jsonl c.jsonl \
      [--reps 3] [--manifest m1.json --manifest m2.json ...] \
      [--out-dir experiments/ptr-engine/measure/pooled] [--stamp 20261026T190000Z]

Exit codes: 0 pooled, 2 refused (the refusal is printed as
`REFUSED (<code>): <message>`), 3 bad usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PTR_ROOT = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(os.path.dirname(PTR_ROOT))
MANIFEST_DIR = os.path.join(PTR_ROOT, "longrun", "manifests")
SANITY_DOC = os.path.join(PTR_ROOT, "measure", "GRID-CELL-SANITY.json")
DEFAULT_OUT_DIR = os.path.join(PTR_ROOT, "measure", "pooled")

SCHEMA = "consonance.pooled-rows/1"
PURPOSE = "H1 pooled R-all"
POOLING_RULE = (
    "R-all: pool every COMPLETED turn row (kind in {turn, turn-initial}) of every source "
    "rep for the arm, in source order, and take no sample: rows are concatenated, one row "
    "per turn, with `rep` renumbered to the pooled rep index and the original rep kept in "
    "`source_rep`. Turns that are not completed (error / failed_turn / http_status >= 400) "
    "and duplicate (rep, turn) rows are excluded and counted in `excluded_turns`; a "
    "dimensionless statistic (TTFT, latency) is computed over the pooled turns exactly as "
    "analyze_stats computes it over a single cell's turns. No filtering by value, no "
    "trimming, no imputation: an unavailable timing stays null and is dropped by "
    "quantile_ci's own null accounting, not by this tool."
)

TURN_ROW_KINDS = ("turn", "turn-initial")
PROVENANCE_FIELDS = ("fixture_sha256", "harness_sha256", "model", "tools_mode")
EON = "era B"

#: TURN-CENSUS-60 froze n >= 60 as H1's floor; H3's McNemar needs b + c >= 6.
H1_MIN_N = 60
H3_MIN_DISCORDANT = 6

CODES = (
    "insufficient_reps",
    "incomparable_provenance",
    "era_a_excluded",
    "source_unusable",
    "source_unreadable",
    "rows_sha_mismatch",
    "duplicate_source",
    "source_derived",
    "invalid_arm",
)


class PoolRefused(Exception):
    """A named refusal; never a silent drop."""

    def __init__(self, code, message, detail=None):
        assert code in CODES, code
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.detail = detail or {}

    def render(self):
        return "REFUSED (%s): %s" % (self.code, self.message)

    def as_dict(self):
        out = {"code": self.code, "message": self.message}
        out.update(self.detail)
        return out


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path):
    """Repo-relative when inside the repo, absolute otherwise (stable provenance)."""
    try:
        real = os.path.realpath(path)
        root = os.path.realpath(REPO_ROOT)
        if real == root or real.startswith(root + os.sep):
            return os.path.relpath(real, root)
    except OSError:
        pass
    return path


def _norm(path):
    if not path:
        return ""
    if os.path.isabs(path):
        return os.path.realpath(path)
    for base in (REPO_ROOT, PTR_ROOT):
        cand = os.path.join(base, path)
        if os.path.exists(cand):
            return os.path.realpath(cand)
    return os.path.normpath(path)


def read_rows(path):
    """-> list of dict rows; `source_unreadable` when nothing readable is there."""
    try:
        with open(path, "rb") as fh:
            blob = fh.read()
    except OSError as exc:
        raise PoolRefused("source_unreadable",
                          "%s cannot be read: %s" % (_rel(path), exc))
    rows, bad = [], 0
    for line in blob.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            bad += 1          # a half-written tail is never fatal, but is counted
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    if not rows:
        raise PoolRefused("source_unreadable",
                          "%s holds no JSON rows (%d unparsable line(s))"
                          % (_rel(path), bad))
    return rows


def shape_era(rows):
    """Mirror of tranche_canary._shape_era: A when rows carry the engine stop_reason,
    B when only the wire finish_reason / answer_verified. Unknown defaults to A."""
    if any(r.get("stop_reason") for r in rows):
        return "A"
    if any(r.get("finish_reason") or r.get("answer_verified") is not None for r in rows):
        return "B"
    return "A"


def declared_era(manifest):
    if not isinstance(manifest, dict):
        return None
    for key in ("era", "shape_era", "answer_era"):
        val = manifest.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    prov = manifest.get("provenance")
    if isinstance(prov, dict):
        for key in ("era", "shape_era"):
            val = prov.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def load_manifests(paths, directory=MANIFEST_DIR):
    """-> list of manifest dicts; explicit paths first, then the manifest directory."""
    out, seen = [], set()
    for path in [p for p in (paths or []) if p]:
        try:
            with open(path, encoding="utf-8") as fh:
                man = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(man, dict) and man.get("rows_path") and path not in seen:
            man = dict(man)
            man["_manifest_path"] = path
            seen.add(path)
            out.append(man)
    if directory and os.path.isdir(directory):
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(directory, name)
            if path in seen:
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    man = json.load(fh)
            except (OSError, ValueError):
                continue
            if isinstance(man, dict) and man.get("rows_path"):
                man = dict(man)
                man["_manifest_path"] = path
                seen.add(path)
                out.append(man)
    return out


def manifest_for(rows_path, manifests):
    """The manifest whose `rows_path` resolves to this rows file (first hit wins)."""
    target = os.path.realpath(rows_path)
    for man in manifests:
        if _norm(man.get("rows_path")) == target:
            return man
    return None


def sanity_stamp(rows_path, path=SANITY_DOC):
    """The grid census stamp for this rows file, or None."""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    target = os.path.realpath(rows_path)
    for cell in (doc.get("cells") or []):
        if not isinstance(cell, dict):
            continue
        if _norm(cell.get("path")) == target:
            return cell
    return None


def usable_for_of(rows_path, manifest):
    if isinstance(manifest, dict) and "usable_for" in manifest:
        return manifest.get("usable_for")
    cell = sanity_stamp(rows_path)
    if isinstance(cell, dict) and "usable_for" in cell:
        return cell.get("usable_for")
    return None


def declared_rows_sha(manifest):
    if not isinstance(manifest, dict):
        return None
    for key in ("rows_sha256", "rows_sha", "sha256"):
        val = manifest.get(key)
        if isinstance(val, str) and len(val) == 64:
            return val
    return None


def provenance_of(manifest, rows):
    """The four comparability fields, from the manifest first, the rows second."""
    prov = manifest.get("provenance") if isinstance(manifest, dict) else None
    prov = prov if isinstance(prov, dict) else {}
    first = rows[0] if rows else {}
    out = {}
    for field in PROVENANCE_FIELDS:
        val = prov.get(field)
        if val is None and isinstance(manifest, dict):
            val = manifest.get(field)
        if val is None:
            val = first.get(field)
        if isinstance(val, str) and not val.strip():
            val = None
        out[field] = val
    return out


def completed_turn_rows(rows):
    """-> (kept, excluded): a completed turn row is kind turn/turn-initial, no error,
    no failed_turn, http_status < 400. Duplicate turn numbers keep the first row."""
    kept, excluded, seen = [], [], set()
    for row in rows:
        if row.get("kind") not in TURN_ROW_KINDS:
            continue
        if row.get("error") or row.get("failed_turn"):
            excluded.append({"turn": row.get("turn"), "reason": "failed_turn"})
            continue
        status = row.get("http_status")
        if isinstance(status, int) and status >= 400:
            excluded.append({"turn": row.get("turn"), "reason": "http_status",
                             "http_status": status})
            continue
        turn = row.get("turn")
        if turn in seen:
            excluded.append({"turn": turn, "reason": "duplicate_turn"})
            continue
        seen.add(turn)
        kept.append(row)
    return kept, excluded


# ---------------------------------------------------------------------------
# the pool
# ---------------------------------------------------------------------------
def pool(arm, rows_paths, reps=3, manifest_paths=None, out_dir=DEFAULT_OUT_DIR,
         stamp=None, created_at=None, write=True):
    """Pool `rows_paths` into one derived artefact; return (manifest, manifest_path).

    Raises PoolRefused (named) instead of ever dropping a source silently.
    """
    if not isinstance(arm, str) or not arm.strip() or any(
            ch in arm for ch in ("/", "\\", os.sep)) or arm.startswith("rows-"):
        raise PoolRefused("invalid_arm",
                          "arm %r cannot name a pooled file (no separators, no `rows-` "
                          "prefix); the artefact must never be mistakable for a cell" % (arm,))
    if int(reps) < 1:
        raise PoolRefused("insufficient_reps", "--reps must be >= 1, got %r" % (reps,))

    paths, dupes = [], set()
    for path in rows_paths:
        real = os.path.realpath(path)
        if real in dupes:
            raise PoolRefused("duplicate_source",
                              "%s was passed more than once: one cell cannot supply two "
                              "reps" % _rel(path))
        dupes.add(real)
        paths.append(path)

    if len(paths) < int(reps):
        raise PoolRefused(
            "insufficient_reps",
            "%d source file(s) supplied but --reps %d requires %d: a %d-rep pool is not "
            "H1's n=144/arm (3 x 48 turns), and H3's exact McNemar needs b + c >= %d "
            "discordant turns, while H1 needs n >= %d. Refusing rather than reading a "
            "smaller pool as if it were the frozen one."
            % (len(paths), int(reps), int(reps), len(paths), H3_MIN_DISCORDANT, H1_MIN_N))

    manifests = load_manifests(manifest_paths)
    sources, pooled_rows = [], []
    prov_seen = {}          # field -> [(value, path)]
    gaps = {field: [] for field in PROVENANCE_FIELDS}

    for index, path in enumerate(paths):
        rows = read_rows(path)
        if rows and (rows[0].get("derived") is True or rows[0].get("pooled_arm")):
            raise PoolRefused("source_derived",
                              "%s is itself a derived pooled artefact (derived=%r); pool "
                              "the measured cells, never a pool of a pool"
                              % (_rel(path), rows[0].get("derived")))
        man = manifest_for(path, manifests)
        declared = declared_rows_sha(man)
        digest = sha256_file(path)
        if declared and declared != digest:
            raise PoolRefused(
                "rows_sha_mismatch",
                "%s: manifest declares rows sha256 %s but the file on disk is %s"
                % (_rel(path), declared, digest),
                {"declared": declared, "measured": digest, "path": _rel(path)})

        usable = usable_for_of(path, man)
        if isinstance(usable, list) and usable == []:
            raise PoolRefused(
                "source_unusable",
                "%s is stamped usable_for: [] (%s); an excluded cell is never pooled"
                % (_rel(path), (man or sanity_stamp(path) or {}).get("usable_for_reason")
                   or "no reason stamped"))

        era = shape_era(rows)
        era_declared = declared_era(man)
        if era_declared and era_declared.strip().lower() in ("a", "pre-t3", "era a"):
            era = "A"
        if era != "B":
            raise PoolRefused(
                "era_a_excluded",
                "%s is era %s (%s); era B is never pooled with era A -- the two have "
                "different answer contracts and different row shapes"
                % (_rel(path), era,
                   "declared era %r" % era_declared if era_declared
                   else "rows carry `stop_reason` (engine field) or no era marker at all, "
                        "which defaults to A"))

        kept, excluded = completed_turn_rows(rows)
        if not kept:
            raise PoolRefused("source_unreadable",
                              "%s holds no completed turn rows to pool (%d row(s), %d "
                              "excluded)" % (_rel(path), len(rows), len(excluded)))

        prov = provenance_of(man, rows)
        for field in PROVENANCE_FIELDS:
            if prov[field] is None:
                gaps[field].append(_rel(path))
            else:
                prov_seen.setdefault(field, []).append((prov[field], _rel(path)))

        turn_rows_on_disk = sum(1 for r in rows if r.get("kind") in TURN_ROW_KINDS)
        source_sha = digest
        for row in kept:
            out = dict(row)
            out["derived"] = True
            out["purpose"] = PURPOSE
            out["pooled_arm"] = arm
            out["source_path"] = _rel(path)
            out["source_sha256"] = source_sha
            out["source_rep"] = row.get("rep", 1)
            out["rep"] = index + 1
            pooled_rows.append(out)

        sources.append({
            "path": _rel(path),
            "sha256": digest,
            "rep": index + 1,
            "source_rep": kept[0].get("rep", 1) if kept else None,
            "arm": (man or {}).get("arm") or kept[0].get("arm") or arm,
            "fixture_sha256": prov["fixture_sha256"],
            "harness_sha256": prov["harness_sha256"],
            "model": prov["model"],
            "tools_mode": prov["tools_mode"],
            "turns_on_disk": turn_rows_on_disk,
            "turns_pooled": len(kept),
            "turns_excluded": len(excluded),
            "excluded": excluded,
            "manifest": _rel(man["_manifest_path"]) if man and man.get("_manifest_path") else None,
            "era": era,
            "usable_for": usable,
            "provenance_missing": [f for f in PROVENANCE_FIELDS if prov[f] is None],
        })

    # comparability: a field that is present on more than one source must agree
    for field in PROVENANCE_FIELDS:
        values = prov_seen.get(field) or []
        distinct = []
        for value, path in values:
            if value not in [v for v, _ in distinct]:
                distinct.append((value, path))
        if len(distinct) > 1:
            (va, pa), (vb, pb) = distinct[0], distinct[1]
            raise PoolRefused(
                "incomparable_provenance",
                "sources differ on %s: %s has %r, %s has %r -- a pooled n is only "
                "meaningful when every rep ran the same fixture, harness, model and "
                "tools_mode; nothing is pooled across a provenance change"
                % (field, pa, va, pb, vb),
                {"field": field, "a": {"path": pa, "value": va},
                 "b": {"path": pb, "value": vb},
                 "distinct": sorted({str(v) for v, _ in distinct})})

    rows_arm = {(r.get("arm") or "").strip() for r in pooled_rows}
    rows_arm.discard("")
    if rows_arm and arm not in rows_arm:
        raise PoolRefused(
            "incomparable_provenance",
            "arm mismatch: --arm %r but the pooled rows are stamped %s"
            % (arm, ", ".join(sorted(rows_arm))),
            {"field": "arm", "expected": arm, "found": sorted(rows_arm)})

    n_turns = len(pooled_rows)
    excluded_turns = []
    for source in sources:
        for item in source["excluded"]:
            excluded_turns.append(dict(item, path=source["path"], rep=source["rep"]))
    complete_on = sum(1 for s in sources if not s["provenance_missing"])

    manifest = {
        "schema": SCHEMA,
        "unit": "POOL-REPS-TOOL",
        "derived": True,
        "purpose": PURPOSE,
        "arm": arm,
        "n_turns": n_turns,
        "n_sources": len(sources),
        "reps": int(reps),
        "h1_min_n": H1_MIN_N,
        "h1_admissible": n_turns >= H1_MIN_N,
        "h1_note": ("n=%d meets the frozen n>=%d floor" % (n_turns, H1_MIN_N)
                    if n_turns >= H1_MIN_N else
                    "n=%d is BELOW the frozen n>=%d floor: this pool is not an H1 reading"
                    % (n_turns, H1_MIN_N)),
        "excluded_turns": excluded_turns,
        "excluded_count": len(excluded_turns),
        "sources": sources,
        "pooling_rule": POOLING_RULE,
        "era": EON,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stamp": stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "provenance_complete_on": "%d/%d" % (complete_on, len(sources)),
        "provenance_gaps": {k: v for k, v in gaps.items() if v},
        "requests": 0,
        "read_only_inputs": True,
        "consumed_by": "analyze_stats.py --rows <this file> --pooled",
        "not_a_measurement": ("derived from measured rows; never a rows-cell-* and never "
                              "readable by analyze_stats without --pooled"),
    }
    name = "pooled-%s-%s" % (arm, manifest["stamp"])
    out_dir = out_dir or DEFAULT_OUT_DIR
    jsonl_path = os.path.join(out_dir, name + ".jsonl")
    manifest_path = os.path.join(out_dir, name + ".json")

    manifest["pooled_path"] = _rel(jsonl_path)
    manifest["manifest_path"] = _rel(manifest_path)

    if write:
        os.makedirs(out_dir, exist_ok=True)
        tmp_rows = jsonl_path + ".part"
        with open(tmp_rows, "w", encoding="utf-8") as fh:
            for row in pooled_rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        os.replace(tmp_rows, jsonl_path)
        manifest["pooled_sha256"] = sha256_file(jsonl_path)
        tmp_man = manifest_path + ".part"
        with open(tmp_man, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
        os.replace(tmp_man, manifest_path)
    return manifest, manifest_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(
        description="Pool N per-rep rows files into one DERIVED R-all view for one arm. "
                    "Never writes to a measured cell.")
    ap.add_argument("--arm", required=True, help="the arm every source must belong to")
    ap.add_argument("--rows", nargs="+", required=True,
                    help="one rows JSONL per rep (default expectation: 3)")
    ap.add_argument("--reps", type=int, default=3,
                    help="minimum number of source reps (default 3; H1 is 3 x 48 turns)")
    ap.add_argument("--manifest", action="append", default=None,
                    help="an explicit cell manifest (repeatable); rows_path joins it")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                    help="where the derived artefact goes (default measure/pooled)")
    ap.add_argument("--stamp", default=None, help="UTC stamp for the output filename")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        manifest, path = pool(
            arm=args.arm, rows_paths=args.rows, reps=args.reps,
            manifest_paths=args.manifest, out_dir=args.out_dir, stamp=args.stamp)
    except PoolRefused as exc:
        print(exc.render(), file=sys.stderr)
        return 2
    print("pooled %s  n=%d  sources=%d  -> %s"
          % (manifest["arm"], manifest["n_turns"], manifest["n_sources"],
             manifest["pooled_path"]))
    print("  manifest: %s" % manifest["manifest_path"])
    print("  h1: %s" % manifest["h1_note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
