#!/usr/bin/env python3
"""ROW-PROVENANCE retrofit: read the provenance of the 14 rows files, change nothing.

WHY THIS EXISTS
---------------
`HARNESS-MAP-V2` had to infer a "harness era" axis from FILE MTIMES because a row
carried no harness, fixture, model or thinking field; `LATENCY-REPORT` then marked every
era-load-bearing pair NOT COMPARABLE, and `docs/OPERATOR-BRIEF.md` reports H1 as not
adjudicable partly for that reason.  Four revisions of the same fixture
(`LR-01.v2 -> v4 -> v5 -> v6/v7`) each changed the task while the rows stayed anonymous,
so a grid measured under v2 could not be told from one measured under v7 except by
guessing at filenames.

Rows written from now on carry the block themselves (`client.provenance_block`, stamped
by `run_longrun.make_row`).  This tool answers the same question for the rows ALREADY on
disk -- **by reading, never by rewriting**.  A rows file is a measurement; this tool
opens every one of them read-only and writes nothing back.

THE SOURCE-OF-TRUTH LADDER (per field, first hit wins)
------------------------------------------------------
1. ``row``      -- the row itself carries the field.  Strongest: it was stamped at write
                   time by the process that made the measurement.
2. ``manifest`` -- a sibling run manifest under ``longrun/manifests/`` whose
                   ``rows_path`` is this file, and whose ``arm``/``rep`` (and, when the
                   row carries one, ``fixture.sha256``) match.  Ties broken by
                   ``dry_run`` false first, then newest ``created_utc``.  Nothing is
                   inferred from a filename.
3. ``cell``     -- a cell report under ``measure/cell-*.json`` whose ``run.rows_path`` is
                   this file and whose ``arm`` matches.  This is the only place on disk
                   that records a ``harness.harness_sha256`` bound to a rows file.
4. ``"unknown"`` -- nothing says.  An admitted gap, never a plausible guess.

``fixture_id`` is resolved by CONTENT ADDRESS: the fixture sha is looked up among the
fixture files under ``longrun/tasks-*/`` and ``longrun/runtime/``, and the matching file's
own ``task_id``/``fixture_version`` name it.  When the sha matches no fixture on disk the
file was mutated in place (`runtime/LR-01.json` was, four times), so only the manifest's
``task_id`` survives and the version stays unresolved -- recorded as such, not invented.

USAGE
-----
    python3 experiments/ptr-engine/tools/row_provenance.py            # print the table
    python3 experiments/ptr-engine/tools/row_provenance.py --json experiments/ptr-engine/measure/ROW-PROVENANCE.json
    python3 experiments/ptr-engine/tools/row_provenance.py --cost     # the retrofit's cost

OFFLINE: no network, no inference request, no lock, no write to any rows file.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)                      # experiments/ptr-engine
REPO = os.path.dirname(os.path.dirname(ENGINE))
LONGRUN = os.path.join(ENGINE, "longrun")
MEASURE = os.path.join(ENGINE, "measure")

if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import client  # noqa: E402  - the ONE canonical definition of the field set

UNKNOWN = client.PROVENANCE_UNKNOWN
FIELDS = client.PROVENANCE_FIELDS                  # the nine fields a row names
LOAD_BEARING = client.PROVENANCE_LOAD_BEARING      # {fixture_sha256, model, thinking, tools_mode}

SOURCE_ROW = "row"
SOURCE_MANIFEST = "manifest"
SOURCE_CELL = "cell"
SOURCE_UNKNOWN = UNKNOWN


def same_provenance(cell_a, cell_b) -> tuple[bool, list[str]]:
    """Can two cells be compared at all?  ``(True, [])`` or ``(False, [differing])``.

    Compares ONLY the load-bearing set ``{fixture_sha256, model, thinking, tools_mode}``:
    a cell is {a row, a file-level provenance block, or a plain dict of the nine fields}.
    ``arm`` is NOT compared -- the arm is what a comparison is FOR, not a confounder --
    and neither is ``endpoint`` or ``max_tokens``, so two arms of one grid stay
    comparable while two fixture generations or two thinking settings do not.

    An ``"unknown"`` on either side counts as DIFFERING: two unknowns are not evidence
    of agreement, and an unknown may not be asserted equal to a known value.

    The logic lives in ``longrun/client.py`` (``client.same_provenance``) because the row
    writer and this tool must never disagree about what "same provenance" means; this is
    the tool's public re-export, not a second copy.
    """
    return client.same_provenance(cell_a, cell_b)


# ------------------------------------------------------------------ reading the disk
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path: str) -> str:
    try:
        return os.path.relpath(path, REPO)
    except ValueError:  # pragma: no cover - different drive on Windows
        return path


def _ledger_files(engine: str = ENGINE) -> list[str]:
    """The 14 rows files, as the request ledger already enumerates them."""
    ledger = os.path.join(engine, "measure", "REQUEST-LEDGER.json")
    if not os.path.exists(ledger):
        return []
    with open(ledger, encoding="utf-8") as fh:
        doc = json.load(fh)
    return [entry["file"] for entry in doc.get("per_file") or [] if entry.get("file")]


def load_rows(path: str) -> list[dict]:
    """Every parseable row of one rows file.  Read-only; the file is never opened for write."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def load_manifests() -> list[dict]:
    """Every run manifest on disk, tagged with its own filename."""
    out = []
    for path in sorted(glob.glob(os.path.join(LONGRUN, "manifests", "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict):
            continue
        if not str(doc.get("schema", "")).startswith("consonance.longrun-manifest/"):
            continue
        doc["_path"] = _rel(path)
        out.append(doc)
    return out


def load_cells(engine: str = ENGINE) -> list[dict]:
    """Every cell report, tagged with its own path (it holds harness.harness_sha256)."""
    out = []
    for path in sorted(glob.glob(os.path.join(engine, "measure", "cell-*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(doc, dict) and isinstance(doc.get("harness"), dict):
            doc["_path"] = _rel(path)
            out.append(doc)
    return out


def fixture_index() -> dict:
    """sha256 -> {task_id, fixture_version, path} for every fixture file on disk.

    Content addressing, so a fixture can be NAMED from its digest instead of from the
    filename a manifest happened to point at (``runtime/LR-01.json`` was overwritten in
    place across v2..v6, so its path names no generation at all).
    """
    index = {}
    patterns = [os.path.join(LONGRUN, "runtime", "*.json"),
                os.path.join(LONGRUN, "tasks-*", "*", "*.json"),
                os.path.join(LONGRUN, "tasks-*", "*.json")]
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            try:
                digest = sha256_file(path)
            except OSError:
                continue
            if digest in index:
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    fx = json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(fx, dict) or "task_id" not in fx:
                continue
            index[digest] = {"task_id": fx.get("task_id"),
                             "fixture_version": fx.get("fixture_version"),
                             "path": _rel(path)}
    return index


# ----------------------------------------------------------------- the manifest match
def _basename(value: str) -> str:
    return os.path.basename(str(value or "").replace("\\", "/"))


def manifest_candidates(manifests, filename, arm=None, rep=None, fixture_sha=None):
    """Every manifest that COULD describe one rows file, before the tie-break."""
    out = [m for m in manifests if _basename(m.get("rows_path")) == filename]
    if arm is not None:
        strict = [m for m in out if m.get("arm") == arm]
        out = strict or out
    if rep is not None:
        strict = [m for m in out
                  if m.get("rep") is None or int(m.get("rep")) == int(rep)]
        out = strict or out
    if fixture_sha:
        strict = [m for m in out
                  if (m.get("fixture") or {}).get("sha256") == fixture_sha]
        out = strict or out
    return out


def match_manifest(manifests, filename, arm=None, rep=None, fixture_sha=None):
    """The sibling manifest for one rows file (see the ladder in the module docstring)."""
    candidates = [m for m in manifests if _basename(m.get("rows_path")) == filename]
    if not candidates:
        return None
    if arm is not None:
        strict = [m for m in candidates if m.get("arm") == arm]
        candidates = strict or candidates
    if rep is not None:
        strict = [m for m in candidates
                  if m.get("rep") is None or int(m.get("rep")) == int(rep)]
        candidates = strict or candidates
    if fixture_sha:
        # content address beats a filename: a manifest frozen for THIS fixture wins
        strict = [m for m in candidates
                  if (m.get("fixture") or {}).get("sha256") == fixture_sha]
        candidates = strict or candidates
    candidates.sort(key=lambda m: (bool(m.get("dry_run")), str(m.get("created_utc") or "")))
    return candidates[-1] if candidates else None


def match_cell(cells, filename, arm=None):
    """The cell report whose ``run.rows_path`` is this rows file (harness provenance)."""
    hits = [c for c in cells
            if _basename((c.get("run") or {}).get("rows_path")) == filename]
    if not hits:
        return None
    if arm is not None:
        strict = [c for c in hits if c.get("arm") == arm]
        hits = strict or hits
    return hits[-1] if len(hits) == 1 else (hits and hits[0])


def _candidate_value(name, manifest):
    """One load-bearing field as a single manifest would supply it (for the audit column)."""
    if name == "fixture_sha256":
        return (manifest.get("fixture") or {}).get("sha256")
    if name == "model":
        return (manifest.get("model") or {}).get("name")
    if name == "thinking":
        return manifest.get("thinking") or (manifest.get("renderer") or {}).get("thinking")
    if name == "tools_mode":
        return _manifest_tools_mode(manifest)
    return None


def _manifest_fixture_id(manifest, index) -> str:
    """``<task_id>.<fixture_version>`` resolved by CONTENT, else the manifest's task_id."""
    fx = manifest.get("fixture") or {}
    sha = fx.get("sha256")
    hit = index.get(sha) if sha else None
    if hit:
        task, version = hit.get("task_id"), hit.get("fixture_version")
        if task and version:
            return "%s.%s" % (task, version)
        if task:
            return str(task)
    task = fx.get("task_id")
    return str(task) if task else UNKNOWN


def _manifest_tools_mode(manifest) -> str:
    """``tools_mode`` from a manifest: a ``tools`` block means on, its absence means off.

    `run_longrun.build_manifest` splices the ``tools`` block ONLY on a ``--tools`` run
    (`**({...} if tools_enabled(cfg) else {})`), so on a manifest written by this runner
    the absence of ``tools`` is positive evidence the run sent no tools -- not silence.
    """
    block = manifest.get("tools")
    if isinstance(block, dict):
        return client.tools_mode_label(block.get("names") or [])
    return client.TOOLS_MODE_OFF


# ------------------------------------------------------------- one row, one provenance
def row_provenance(row, manifest, cell, index) -> dict:
    """One row's provenance: each field from the highest rung that actually has it."""
    values, sources = {}, {}

    def take(name, value, source):
        if name in values:
            return
        if not client.is_provenance_known(value):
            return
        values[name] = value
        sources[name] = source

    # -- rung 1: the row itself
    for name in FIELDS:
        take(name, row.get(name), SOURCE_ROW)
    if row.get("task_id") and row.get("fixture_version"):
        take("fixture_id", "%s.%s" % (row["task_id"], row["fixture_version"]), SOURCE_ROW)

    # -- rung 2: the sibling manifest
    if manifest:
        take("arm", manifest.get("arm"), SOURCE_MANIFEST)
        take("model", (manifest.get("model") or {}).get("name"), SOURCE_MANIFEST)
        take("endpoint", (manifest.get("model") or {}).get("endpoint"), SOURCE_MANIFEST)
        take("fixture_id", _manifest_fixture_id(manifest, index), SOURCE_MANIFEST)
        take("fixture_sha256", (manifest.get("fixture") or {}).get("sha256"), SOURCE_MANIFEST)
        take("max_tokens", (manifest.get("renderer") or {}).get("max_tokens"), SOURCE_MANIFEST)
        take("thinking", manifest.get("thinking")
             or (manifest.get("renderer") or {}).get("thinking"), SOURCE_MANIFEST)
        take("tools_mode", _manifest_tools_mode(manifest), SOURCE_MANIFEST)

    # -- rung 3: the cell report (the only bound harness digest on disk)
    if cell:
        take("harness_sha256", (cell.get("harness") or {}).get("harness_sha256"), SOURCE_CELL)
        if cell.get("fixture_version"):
            take("fixture_id", "%s.%s" % ((manifest or {}).get("fixture", {}).get("task_id")
                                          or (cell.get("fixture") or "").split("/")[-1].split(".")[0],
                                          cell["fixture_version"]), SOURCE_CELL)

    # -- rung 4: an admitted gap
    block = client.provenance_block(**{name: values.get(name) for name in FIELDS})
    block["sources"] = {name: sources.get(name, SOURCE_UNKNOWN) for name in FIELDS}
    return block


# ------------------------------------------------------------------------ per-file view
def _distinct(values):
    seen = []
    for v in values:
        if v not in seen:
            seen.append(v)
    return seen


def aggregate(blocks: list[dict]) -> dict:
    """Collapse per-row provenance into one file-level record, honestly.

    A field on which the rows of one file DISAGREE is reported ``"mixed"``: the file then
    genuinely has no single provenance for it, and saying so is the point.  A field that
    some rows carry and others do not is reported with the value the rows that HAVE it
    agree on, and the gap is counted in ``partial_rows`` -- the file-level value is real,
    while ``rows_with_complete_provenance`` keeps the per-row truth visible.
    """
    out, sources, partial_rows = {}, {}, {}
    for name in FIELDS:
        raw = [b[name] for b in blocks] if blocks else [UNKNOWN]
        known = [v for v in raw if client.is_provenance_known(v)]
        partial_rows[name] = len(raw) - len(known)
        distinct = _distinct(known)
        if len(distinct) == 1:
            out[name] = distinct[0]
        elif len(distinct) == 0:
            out[name] = UNKNOWN
        else:
            out[name] = "mixed"
        srcs = _distinct([b["sources"][name] for b in blocks
                          if client.is_provenance_known(b[name])]) if blocks else [SOURCE_UNKNOWN]
        # a field only counts as resolved if EVERY row that has it resolves it the same way
        if not srcs:
            sources[name] = SOURCE_UNKNOWN
        elif len(srcs) == 1:
            sources[name] = srcs[0]
        else:
            sources[name] = "+".join(sorted(srcs))
    resolved = [n for n in FIELDS
                if client.is_provenance_known(out[n]) and out[n] != "mixed"]
    missing = [n for n in FIELDS if n not in resolved]
    rungs = sorted({token for src in sources.values() for token in str(src).split("+")
                    if token and token != SOURCE_UNKNOWN})
    return {
        "rows": len(blocks),
        "fields": out,
        "sources": sources,
        "partial_rows": {n: c for n, c in partial_rows.items() if c},
        "missing_fields": missing,
        "provenance_complete": not missing,
        # the compact word the report uses: which rungs supplied this file at all
        "rungs": rungs,
    }


def build_report(files=None, engine: str = ENGINE) -> dict:
    """The whole retrofit: 14 rows files, read only, nothing written back."""
    engine = os.path.abspath(engine)
    measure = os.path.join(engine, "measure")
    manifests = load_manifests()
    cells = load_cells(engine)
    index = fixture_index()
    files = files or _ledger_files(engine)
    records = []
    for filename in files:
        path = os.path.join(measure, filename)
        if not os.path.exists(path):
            records.append({"file": filename, "present": False,
                            "error": "rows file not found"})
            continue
        rows = load_rows(path)
        arm = next((r.get("arm") for r in rows if r.get("arm")), None)
        rep = next((r.get("rep") for r in rows if r.get("rep") is not None), None)
        fixture_sha = next((r.get("fixture_sha256") for r in rows if r.get("fixture_sha256")), None)
        candidates = manifest_candidates(manifests, filename, arm, rep, fixture_sha)
        manifest = match_manifest(manifests, filename, arm, rep, fixture_sha)
        cell = match_cell(cells, filename, arm)
        blocks = [row_provenance(r, manifest, cell, index) for r in rows]
        agg = aggregate(blocks)
        records.append({
            "file": filename,
            "present": True,
            "rows_read": len(rows),
            "rows_sha256": sha256_file(path),
            "manifest": manifest.get("_path") if manifest else None,
            "manifest_run_id": manifest.get("run_id") if manifest else None,
            # HOW MUCH THE PICK MATTERED: if these candidate values disagree, the
            # manifest rung could have supplied a different load-bearing value, so the
            # recorded one is a pick rather than a consensus.  Reported, never hidden.
            "manifest_candidates": len(candidates),
            "manifest_candidate_values": {
                name: sorted({str(v) for v in
                              (_candidate_value(name, m) for m in candidates)
                              if client.is_provenance_known(v)})
                for name in LOAD_BEARING
            } if len(candidates) > 1 else {},
            "cell": cell.get("_path") if cell else None,
            "arm": agg["fields"]["arm"],
            "fixture_id": agg["fields"]["fixture_id"],
            "fixture_sha256": agg["fields"]["fixture_sha256"],
            "harness_sha256": agg["fields"]["harness_sha256"],
            "model": agg["fields"]["model"],
            "endpoint": agg["fields"]["endpoint"],
            "max_tokens": agg["fields"]["max_tokens"],
            "thinking": agg["fields"]["thinking"],
            "tools_mode": agg["fields"]["tools_mode"],
            "provenance_complete": agg["provenance_complete"],
            "missing_fields": agg["missing_fields"],
            "source_of_truth": "+".join(agg["rungs"]) if agg["rungs"] else UNKNOWN,
            "sources": agg["sources"],
            "rows_with_complete_provenance": sum(1 for b in blocks if b["provenance_complete"]),
        })
    return {
        "unit": "ROW-PROVENANCE",
        "method": ("read-only retrofit: each field from the highest rung that has it -- "
                   "row, then a sibling run manifest matched by rows_path+arm+rep+(fixture "
                   "sha), then a cell report matched by run.rows_path+arm, else 'unknown'; "
                   "no rows file is opened for write and no value is inferred from a filename"),
        "fields": list(FIELDS),
        "load_bearing": list(LOAD_BEARING),
        "ladder": [SOURCE_ROW, SOURCE_MANIFEST, SOURCE_CELL, SOURCE_UNKNOWN],
        "files_declared_by": _rel(os.path.join(measure, "REQUEST-LEDGER.json")),
        "files": records,
        "cost": cost(records),
        "unresolved_deltas": unresolved_deltas(records),
    }


def cost(records: list[dict]) -> dict:
    """What the retrofit actually bought, and where it did not reach."""
    present = [r for r in records if r.get("present")]
    full = [r for r in present if r.get("provenance_complete")]
    none = [r for r in present if r.get("source_of_truth") == UNKNOWN]
    full_names = {r["file"] for r in full}
    none_names = {r["file"] for r in none}
    partial = [r for r in present
               if r["file"] not in full_names and r["file"] not in none_names]
    field_missing = {}
    for name in FIELDS:
        n = sum(1 for r in present if name in (r.get("missing_fields") or []))
        if n:
            field_missing[name] = n
    return {
        "files": len(records),
        "files_present": len(present),
        "files_full_provenance": len(full),
        "files_partial_provenance": len(partial),
        "files_unknown_only": len(none),
        "files_full": [r["file"] for r in full],
        "files_partial": [r["file"] for r in partial],
        "files_unknown_only_names": [r["file"] for r in none],
        "fields_missing_counts": dict(sorted(field_missing.items(),
                                             key=lambda kv: (-kv[1], kv[0]))),
        "fields_always_missing": [n for n in FIELDS if field_missing.get(n) == len(present)],
    }


def _comparable(record: dict) -> dict:
    """One file record as a cell a comparison may read.

    A file-level ``"mixed"`` (the rows of that file disagree) is NOT a provenance: it is
    downgraded to ``"unknown"`` here so it can never compare equal to anything.
    """
    cell = dict(record)
    for name in FIELDS:
        if cell.get(name) == "mixed":
            cell[name] = UNKNOWN
    return cell


def unresolved_deltas(records: list[dict]) -> list[dict]:
    """Pairs of files whose LOAD-BEARING provenance differs -- the retrofit's payoff.

    ``kind`` separates two very different results:
      * ``"proven"``          -- both sides resolved and they disagree: a head-to-head
                                 comparison between these files is invalid, on the
                                 evidence, not on an inference;
      * ``"unknown-involved"``-- at least one side is `"unknown"`/`"mixed"`, so the
                                 comparison cannot be *shown* to be valid either.  That
                                 is a gap in the record, not a proven difference.
    """
    out = []
    present = [_comparable(r) for r in records if r.get("present")]
    for i, a in enumerate(present):
        for b in present[i + 1:]:
            ok, differing = same_provenance(a, b)
            if ok:
                continue
            proven = all(client.is_provenance_known(a.get(n)) and client.is_provenance_known(b.get(n))
                         for n in differing)
            out.append({"a": a["file"], "b": b["file"],
                        "kind": "proven" if proven else "unknown-involved",
                        "same_fixture_id": a.get("fixture_id") == b.get("fixture_id"),
                        "fixture_id_a": a.get("fixture_id"),
                        "fixture_id_b": b.get("fixture_id"),
                        "differing": differing})
    out.sort(key=lambda d: (d["kind"] != "proven", d["a"], d["b"]))
    return out


# --------------------------------------------------------------------------- printing
def _short(value) -> str:
    text = str(value)
    if text == UNKNOWN:
        return UNKNOWN
    if len(text) == 64 and all(c in "0123456789abcdef" for c in text):
        return text[:12]
    return text


def format_table(report: dict) -> str:
    header = ["file", "arm", "fixture_id", "fixture_sha256", "harness_sha256",
              "model", "thinking", "tools_mode", "source_of_truth"]
    lines = []
    rows = []
    for r in report["files"]:
        if not r.get("present"):
            rows.append([r["file"], "-", "-", "-", "-", "-", "-", "-", "absent"])
            continue
        rows.append([r["file"], str(r["arm"]), str(r["fixture_id"]),
                     _short(r["fixture_sha256"]), _short(r["harness_sha256"]),
                     str(r["model"]), str(r["thinking"]), str(r["tools_mode"]),
                     r["source_of_truth"]])
    widths = [max(len(header[i]), max((len(row[i]) for row in rows), default=0))
              for i in range(len(header))]
    lines.append(" · ".join(header[i].ljust(widths[i]) for i in range(len(header))))
    lines.append(" · ".join("-" * widths[i] for i in range(len(header))))
    for row in rows:
        lines.append(" · ".join(row[i].ljust(widths[i]) for i in range(len(header))))
    return "\n".join(lines)


def format_cost(report: dict) -> str:
    c = report["cost"]
    lines = ["RETROFIT COST (%d files declared, %d present)" % (c["files"], c["files_present"]),
             "  full provenance   : %d" % c["files_full_provenance"],
             "  partial           : %d" % c["files_partial_provenance"],
             "  'unknown' only    : %d" % c["files_unknown_only"]]
    for name, n in c["fields_missing_counts"].items():
        lines.append("  missing %-16s: %d/%d files" % (name, n, c["files_present"]))
    if c["fields_always_missing"]:
        lines.append("  ALWAYS missing    : %s" % ", ".join(c["fields_always_missing"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Read-only provenance retrofit for the rows files.")
    ap.add_argument("--json", default="", metavar="PATH",
                    help="write the machine-readable table here (never a rows file)")
    ap.add_argument("--cost", action="store_true", help="print the retrofit cost instead")
    ap.add_argument("--deltas", action="store_true",
                    help="print file pairs whose load-bearing provenance differs")
    args = ap.parse_args(argv)

    report = build_report()
    if args.json:
        parent = os.path.dirname(os.path.abspath(args.json))
        os.makedirs(parent, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print("wrote %s (%d bytes)" % (_rel(os.path.abspath(args.json)),
                                       os.path.getsize(args.json)))
    if args.cost:
        print(format_cost(report))
    if args.deltas:
        for d in report["unresolved_deltas"]:
            print("%s <> %s  differing=%s  same_fixture_id=%s"
                  % (d["a"], d["b"], ",".join(d["differing"]), d["same_fixture_id"]))
    if not (args.cost or args.deltas):
        print(format_table(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
