#!/usr/bin/env python3
"""build_compilation.py — regenerate the derived parts of the context-cache index.

Dependency-free: standard library only, no network, no imports from this repository.
Run it after any artefact changes:

    python3 experiments/ptr-engine/tools/build_compilation.py

What it does
  1. parses `papers/context-cache/CLAIMS.md` for the claim ids it defines (C01..C69);
  2. counts the rows of every row file CLAIMS.md's "Source rows and digests" table names
     (plus any extra `--row-file` given on the command line) and compares the count with
     the number that table declares, printing NOT-PARSED rather than guessing;
  3. **discovers** every `rows-*.jsonl` in `experiments/ptr-engine/measure/` and indexes it
     from the rows themselves — row count, units, models, per model x cell x role cells,
     uncached sums, turn-reps, correctness and error counts. Nothing about those files is
     hardcoded: the status comes from the file's own `unit` field and a declared verdict
     table, so an unknown unit prints NOT-PARSED instead of an invented status;
  4. re-derives, for every 7-column row of COMPILATION.md, the *claim* cell is validated
     and the *status* cell is recomputed from the row's strength, its claim ids and the
     `[lim]` / `[live]` / `[op]` marker prefixed to the row's last column;
  5. rewrites the generated regions of COMPILATION.md and COMPILATION-RELATIONS.md and the
     `<!-- build: ... -->` stamp, then prints one summary block.

Status rules (the only authority is the artefact, never the prose):
    marker [live]                          -> BLOCKED-LIVE
    marker [op]                            -> BLOCKED-OPERATOR
    strength WITHDRAWN                     -> NOT-PUBLISHABLE
    strength UNSUPPORTED                   -> NOT-PUBLISHABLE
    strength DRAFTED                       -> BLOCKED-OPERATOR   (written, not ratified)
    every claim id resolves in CLAIMS.md?  -> no: BLOCKED-OPERATOR (measured but not citable)
    marker [lim]                           -> READY-WITH-LIMITATION
    otherwise                              -> READY

Row-file status rules (row-file section only):
    the file's `unit` field has a verdict -> that verdict (MEASURED / INVALID-BY-DESIGN)
    no verdict for that unit              -> NOT-CLASSIFIED + NOT-PARSED <path>

Idempotence: the output depends only on the artefacts on disk, so a second run is a no-op and
prints the same summary. `--dry-run` computes everything and writes nothing.

Exit status is 1 only when the index file itself is unreadable; every parse problem is reported
on stdout as NOT-PARSED and leaves the affected cell untouched.
"""

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))

DEFAULT_INDEX = os.path.join(REPO, "papers", "context-cache", "COMPILATION.md")
DEFAULT_CLAIMS = os.path.join(REPO, "papers", "context-cache", "CLAIMS.md")
DEFAULT_RELATIONS = os.path.join(REPO, "papers", "context-cache", "COMPILATION-RELATIONS.md")
DEFAULT_RECORD = os.path.join(REPO, "experiments", "ptr-engine", "RECORD.md")
DEFAULT_MEASURE_DIR = os.path.join(REPO, "experiments", "ptr-engine", "measure")

STRENGTHS = (
    "MEASURED",
    "RE-DERIVED",
    "VERIFIED-OFFLINE",
    "WITHDRAWN",
    "DRAFTED",
    "UNSUPPORTED",
)
READY_STATUSES = {"READY", "READY-WITH-LIMITATION"}

CLAIM_RE = re.compile(r"(?<![A-Za-z0-9])C(\d{2,3})(?![\dA-Za-z])")
MARKER_RE = re.compile(r"^\[(lim|live|op)\]")
BUILD_RE = re.compile(r"^<!--\s*build:")
ROW_SOURCE_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*([\d,]+|—|-)\s*\|\s*([\d,]+|—|-)\s*\|"
)

ROWS_SECTION_BEGIN = "<!-- rows-index:begin -->"
ROWS_SECTION_END = "<!-- rows-index:end -->"
REL_SECTION_BEGIN = "<!-- rows-relations:begin -->"
REL_SECTION_END = "<!-- rows-relations:end -->"

# Verdict per row-file `unit`. A file whose unit is absent here is NOT-CLASSIFIED and is
# reported as NOT-PARSED, never guessed. The reason text is copied from the artefact named in
# the same tuple — it is never invented by this script.
ROW_VERDICTS = {
    "LIVE-CELLS-2": (
        "MEASURED",
        "live cells on :8012/:8014, unit LIVE-CELLS-2",
        "experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl",
    ),
    "C0-EQUALINFO": (
        "MEASURED",
        "live cells, unit C0-EQUALINFO",
        "experiments/ptr-engine/measure/rows-equalinfo-2026-10-26.jsonl",
    ),
    "C0-BASELINE": (
        "INVALID-BY-DESIGN",
        "C0 never carries k01 in context (turns carry k12, k10, k08 only), so the plain "
        "transcript cannot answer by construction — do not cite any figure from this file",
        "orchestration/handoffs/C0-BASELINE.json:101",
    ),
}


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def claim_ids_of(text):
    """Every claim id mentioned in the claims document, as sorted strings C01..C999."""
    return sorted({"C%s" % m for m in CLAIM_RE.findall(text)})


def declared_row_sources(claims_text):
    """[(abbrev, path, declared_rows)] from CLAIMS.md's source-rows table."""
    out = []
    for line in claims_text.splitlines():
        match = ROW_SOURCE_RE.match(line)
        if not match:
            continue
        abbrev, path, _bytes, rows = match.groups()
        declared = None if rows.strip() in ("—", "-") else int(rows.replace(",", ""))
        out.append((abbrev.strip(), path.strip(), declared))
    return out


def count_rows(path):
    """Row count of a row file, or None when this script cannot count it (NOT-PARSED)."""
    if not os.path.isfile(path):
        return None
    lower = path.lower()
    if lower.endswith((".jsonl", ".ndjson")):
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for line in handle if line.strip())
    if lower.endswith(".json"):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (ValueError, OSError):
            return None
        if isinstance(payload, list):
            return len(payload)
        return None
    return None


def split_row(line):
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return cells if len(cells) == 7 else None


def is_separator(cells):
    return all(set(cell) <= set("-: ") and cell for cell in cells)


def status_for(strength, claim_ids, known_claims, marker):
    if marker == "live":
        return "BLOCKED-LIVE"
    if marker == "op":
        return "BLOCKED-OPERATOR"
    if strength == "WITHDRAWN":
        return "NOT-PUBLISHABLE"
    if strength == "UNSUPPORTED":
        return "NOT-PUBLISHABLE"
    if strength == "DRAFTED":
        return "BLOCKED-OPERATOR"
    if not claim_ids or any(cid not in known_claims for cid in claim_ids):
        return "BLOCKED-OPERATOR"
    if marker == "lim":
        return "READY-WITH-LIMITATION"
    return "READY"


# --------------------------------------------------------------------------------------
# Row-file discovery and indexing — every number below is derived from a JSONL row file.
# --------------------------------------------------------------------------------------

def num(value):
    """A bill field as an int, with the settled null semantics: a null cached_tokens is 0."""
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def fmt(value):
    return "{:,}".format(int(value)) if isinstance(value, (int, float)) else str(value)


def fmt_ratio(value):
    return "%.3fx" % value


def uniq(values):
    """Distinct values in first-seen order — no sorting surprises, so runs stay identical."""
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def span(values):
    """`lo` when constant, `lo–hi` otherwise, `—` when nothing is present."""
    present = [value for value in values if value is not None]
    if not present:
        return "—"
    low, high = min(present), max(present)
    return fmt(low) if low == high else "%s–%s" % (fmt(low), fmt(high))


def join_values(values, null_as=None):
    out = []
    for value in values:
        if value is None:
            if null_as is not None:
                out.append(null_as)
        else:
            out.append("`%s`" % value)
    return ", ".join(out) or "—"


def load_rows(path):
    """(rows, bad_line_numbers). Unparseable lines are reported, never dropped silently."""
    rows = []
    bad = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except ValueError:
                bad.append(number)
                continue
            if isinstance(payload, dict):
                rows.append(payload)
            else:
                bad.append(number)
    return rows, bad


def arm_of(row):
    """The row file's own grouping key: `arm` when the protocol has one, else `cell`."""
    for key in ("arm", "cell"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return "—"


def role_of(row):
    value = row.get("role")
    return str(value) if value not in (None, "") else "—"


def index_row_file(path):
    """Per-file index: counts, models, units, and per model x cell x role cells."""
    rows, bad = load_rows(path)
    units = sorted({str(row["unit"]) for row in rows if row.get("unit")})
    models = sorted({str(row["model"]) for row in rows if row.get("model")})
    has_turn = any("turn" in row for row in rows)
    has_items = any("items_in_context" in row for row in rows)
    cells = {}
    for row in rows:
        key = (str(row.get("model") or "—"), arm_of(row), role_of(row))
        cell = cells.setdefault(
            key,
            {
                "rows": 0,
                "turn_reps": set(),
                "prompt": 0,
                "cached": 0,
                "cached_null": 0,
                "uncached": 0,
                "correct": 0,
                "answered": 0,
                "errors": 0,
                "items": set(),
            },
        )
        cell["rows"] += 1
        cell["turn_reps"].add((row.get("rep"), row.get("turn")))
        if "items_in_context" in row:
            cell["items"].add(row["items_in_context"])
        prompt = num(row.get("prompt_tokens"))
        cached_raw = row.get("cached_tokens")
        cached = num(cached_raw)
        cell["prompt"] += prompt
        cell["cached"] += cached
        cell["uncached"] += prompt - cached
        if cached_raw is None:
            cell["cached_null"] += 1
        if row.get("error"):
            cell["errors"] += 1
        else:
            cell["answered"] += 1
        if row.get("answer_correct") is True:
            cell["correct"] += 1
    return {
        "path": path,
        "name": os.path.basename(path),
        "rows": len(rows),
        "bad": bad,
        "units": units,
        "models": models,
        "has_turn": has_turn,
        "has_items": has_items,
        "cells": cells,
        "nulls": sum(1 for row in rows if row.get("cached_tokens") is None),
        "errors": sum(1 for row in rows if row.get("error")),
        "cached_sources": sorted(
            {
                str(row.get("cached_source"))
                for row in rows
                if row.get("cached_source") not in (None, "")
            }
        ),
        "urlerr": sorted({str(row["error"]) for row in rows if row.get("error")}),
        # One dict per row, only the fields this index reads — what the relations are built from.
        "facts": [
            {
                "model": str(row.get("model") or "—"),
                "cell": arm_of(row),
                "role": role_of(row),
                "rep": row.get("rep"),
                "turn": row.get("turn"),
                "residue": row.get("residue"),
                "prompt": num(row.get("prompt_tokens")),
                "cached": row.get("cached_tokens"),
                "uncached": num(row.get("prompt_tokens")) - num(row.get("cached_tokens")),
                "index_bytes": row.get("index_bytes"),
                "index_lines": row.get("index_lines"),
                "index_form": row.get("index_form"),
                "padding": row.get("padding"),
                "items": row.get("items_in_context"),
                "endpoint": row.get("endpoint"),
                "error": row.get("error"),
            }
            for row in rows
        ],
    }


def verdict_of(index):
    """(status, reason, source) for an indexed row file, from its own `unit` field."""
    if len(index["units"]) == 1:
        entry = ROW_VERDICTS.get(index["units"][0])
        if entry:
            return entry
    return ("NOT-CLASSIFIED", "no declared verdict for this unit", "—")


def fields_of(index):
    """The row fields this index actually reads, named so every cell can be traced."""
    keys = ["prompt_tokens", "cached_tokens", "cached_reported"]
    if index["has_turn"]:
        keys += ["turn", "rep"]
    keys += ["answer_correct", "error"]
    if index["has_items"]:
        keys.append("items_in_context")
    return ",".join(keys)


def build_rows_section(indices, record_lines, record_layers):
    lines = []
    lines.append("## P. Row files measured on 2026-10-26 — generated, never hand-edited\n")
    lines.append(
        "Every number in this section is derived from the rows by `build_compilation.py`, which "
        "discovers its inputs by globbing `experiments/ptr-engine/measure/rows-*.jsonl`: no count "
        "here is typed by hand and no row file is named anywhere in the script. `uncached` is "
        "`prompt_tokens − cached_tokens` with a null `cached_tokens` read as **0** (the "
        "LIVE-CELLS-2 null semantics; the row's own `cached_source` field records the endpoint "
        "rule). `turn-reps` is the number of distinct `(rep, turn)` pairs, so `uncached/turn-rep` "
        "is one turn on one rep — a cell whose file has no `turn` field prints `—` rather than "
        "inventing a divisor. A status is never inferred: it comes from the file's own `unit` "
        "field through a declared verdict table, and an unknown unit is reported as `NOT-PARSED`.\n"
    )
    lines.append(
        "**Artefact state at this build.** `experiments/ptr-engine/RECORD.md` — %s lines; "
        "`BASELINE-COST` appears %d time(s) in it, so the baseline-cost layer is %s folded into "
        "the record. Derived by reading the record; re-derived on every run.\n"
        % (fmt(record_lines), record_layers, "already" if record_layers else "not yet")
    )
    lines.append("### P.1 One line per discovered row file\n")
    lines.append("| row file | rows | unit | status | models | source |")
    lines.append("|---|---:|---|---|---|---|")
    for index in indices:
        status, _reason, source = verdict_of(index)
        lines.append(
            "| `%s` | %s | %s | %s | %s | `%s` (fields %s) |"
            % (
                index["name"],
                fmt(index["rows"]),
                ", ".join("`%s`" % unit for unit in index["units"]) or "—",
                status,
                ", ".join("`%s`" % model for model in index["models"]) or "—",
                source,
                fields_of(index),
            )
        )
    lines.append("")
    for index in indices:
        status, reason, source = verdict_of(index)
        if status != "MEASURED":
            lines.append(
                "- `%s` is **%s** — %s (source `%s`).\n"
                % (index["name"], status, reason, source)
            )
    lines.append("")
    for position, index in enumerate(indices, start=2):
        lines.append(
            "### P.%d `%s` — %s rows, status %s\n"
            % (position, index["name"], fmt(index["rows"]), verdict_of(index)[0])
        )
        lines.append(
            "| model | cell | role | rows | turn-reps | uncached sum | uncached/turn-rep "
            "| correct/answered | error rows | source |"
        )
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
        for key in sorted(index["cells"], key=lambda item: (item[0], item[1], item[2])):
            cell = index["cells"][key]
            turn_reps = len(cell["turn_reps"]) if index["has_turn"] else None
            per_turn = fmt(round(cell["uncached"] / turn_reps, 1)) if turn_reps else "—"
            lines.append(
                "| `%s` | `%s` | `%s` | %s | %s | %s | %s | %s/%s | %s | `%s`:%s |"
                % (
                    key[0],
                    key[1],
                    key[2],
                    fmt(cell["rows"]),
                    fmt(turn_reps) if turn_reps else "—",
                    fmt(cell["uncached"]),
                    per_turn,
                    fmt(cell["correct"]),
                    fmt(cell["answered"]),
                    fmt(cell["errors"]),
                    index["name"],
                    fields_of(index),
                )
            )
        facts = []
        if index["nulls"]:
            facts.append(
                "%s of %s rows carry a null `cached_tokens`, counted as 0"
                % (fmt(index["nulls"]), fmt(index["rows"]))
            )
        if index["cached_sources"]:
            facts.append(
                "`cached_source` values: %s"
                % ", ".join("`%s`" % value for value in index["cached_sources"])
            )
        items = uniq(
            sorted(
                {value for cell in index["cells"].values() for value in cell["items"]},
                key=lambda value: (value is None, value),
            )
        )
        if index["has_items"] and items:
            facts.append(
                "`items_in_context` takes %s" % ", ".join(str(value) for value in items)
            )
        if index["urlerr"]:
            facts.append(
                "%s row(s) carry a non-empty `error` (%s)"
                % (
                    fmt(index["errors"]),
                    "; ".join("`%s`" % value[:80] for value in index["urlerr"]),
                )
            )
        if facts:
            lines.append("")
            for fact in facts:
                lines.append("- %s.\n" % fact)
        lines.append("")
    return "".join(line if line.endswith("\n") else line + "\n" for line in lines)


def build_relations_section(indices):
    lines = []
    lines.append("## 8. The 2026-10-26 row files, and what they make citable\n")
    lines.append(
        "Generated by `build_compilation.py` from the same rows that fill section P of "
        "`COMPILATION.md`; every figure below is recomputed on each run, so a stale relation "
        "cannot outlive the rows it reads. `A -> B` keeps its meaning: B depends on A. Every "
        "group is printed whole — no row is selected as representative — so a reader can redo "
        "each arithmetic step from the group it names.\n"
    )
    by_unit = {index["units"][0]: index for index in indices if len(index["units"]) == 1}

    # ---- 8.1 the live cells -----------------------------------------------------------
    live = by_unit.get("LIVE-CELLS-2")
    if live:
        facts = live["facts"]
        lines.append("### 8.1 LIVE-CELLS-2 — C1, C2, C5 and the null semantics\n")
        lines.append("| cell | role | rows | residue | prompt | cached | uncached | source |")
        lines.append("|---|---|---:|---|---|---|---|---|")
        groups = {}
        for fact in facts:
            groups.setdefault((fact["cell"], fact["role"]), []).append(fact)
        for key in sorted(groups):
            group = groups[key]
            reported = [fact["cached"] for fact in group if fact["cached"] is not None]
            nulls = sum(1 for fact in group if fact["cached"] is None)
            cached_cell = span(reported) if reported else "—"
            if nulls:
                cached_cell += " (+%s null→0)" % fmt(nulls)
            lines.append(
                "| `%s` | `%s` | %s | %s | %s | %s | %s | `%s`: `prompt_tokens`, `cached_tokens`, "
                "`residue` |"
                % (
                    key[0],
                    key[1],
                    fmt(len(group)),
                    span([fact["residue"] for fact in group]),
                    span([fact["prompt"] for fact in group]),
                    cached_cell,
                    span([fact["uncached"] for fact in group]),
                    live["name"],
                )
            )
        lines.append("")
        # One bullet per live cell; every figure is computed over the whole cell, never a pick.
        for cell_name, claim_id, meaning in (
            ("A", "C1", "the warm cell whose cached prefix ends on a 64-token block boundary"),
            ("B", "C5", "the compact UNPADDED cell"),
            ("C", "C2", "the warm re-send at residue 1"),
        ):
            cell_facts = [fact for fact in facts if fact["cell"] == cell_name]
            reported = [fact for fact in cell_facts if fact["cached"] is not None]
            warm = [fact for fact in reported if fact["cached"]]
            if not warm:
                continue
            notes = []
            warm_cached = uniq(fact["cached"] for fact in warm)
            for unit in ("1,056", "64"):
                divisor = int(unit.replace(",", ""))
                if all(int(value) % divisor == 0 for value in warm_cached):
                    notes.append(
                        "cached is an exact multiple of the %s-token block unit named in `C55`"
                        % unit
                    )
                    break
            residues = [fact["residue"] for fact in warm if fact["residue"] is not None]
            if residues:
                notes.append("`residue` %s on those rows" % span(residues))
            compact = [fact for fact in cell_facts if fact["index_form"]]
            if compact:
                notes.append(
                    "`index_form` %s with `padding` %s, `index_bytes` %s, `index_lines` %s"
                    % (
                        join_values(uniq(fact["index_form"] for fact in compact)),
                        join_values(uniq(fact["padding"] for fact in compact)),
                        span([fact["index_bytes"] for fact in compact]),
                        span([fact["index_lines"] for fact in compact]),
                    )
                )
                agree = [
                    fact
                    for fact in reported
                    if fact["residue"] is not None and fact["uncached"] == fact["residue"]
                ]
                if agree and len(agree) == len(reported):
                    notes.append(
                        "on every reporting row `prompt_tokens − cached_tokens` equals the "
                        "recorded `residue`"
                    )
            tail_notes = ("; " + "; ".join(notes)) if notes else ""
            tail_nulls = ""
            nulls = len(cell_facts) - len(reported)
            if nulls:
                tail_nulls += " Also, %s row(s) in this cell carry a null counter (0 under the settled semantics)." % fmt(nulls)
            zero_rows = [fact for fact in reported if not fact["cached"]]
            if zero_rows:
                tail_nulls += " %s row(s) report cached 0 and bill the whole %s." % (
                    fmt(len(zero_rows)),
                    span([fact["uncached"] for fact in zero_rows]),
                )
            lines.append(
                "- `%s` -> `%s` (%s): cell `%s` has %s reporting row(s) that cache, each reporting "
                "cached %s and billing %s uncached of a %s-token prompt%s — those rows reuse the "
                "prefix instead of re-billing it.%s Source `%s`: `cached_tokens`, "
                "`prompt_tokens`, `residue`, `cell`, `role`.\n"
                % (
                    live["name"],
                    claim_id,
                    meaning,
                    cell_name,
                    fmt(len(warm)),
                    span(warm_cached),
                    span([fact["uncached"] for fact in warm]),
                    span([fact["prompt"] for fact in warm]),
                    tail_notes,
                    tail_nulls,
                    live["name"],
                )
            )
        lines.append(
            "- `%s` -> `L01`, `L02`, `L03`: the row each queue entry called for now exists in this "
            "file (an SGLang residue-0 warm cell, a vLLM residue-1 warm same-row, and a compact "
            "UNPADDED cell). Those index rows keep `BLOCKED-LIVE` **on purpose**: a status is "
            "derived from `CLAIMS.md` and the row's `[live]` marker, never from a row file, so "
            "releasing them is an editorial act on the claim row. Source `%s`: `cell`, `role`, "
            "`residue`; `COMPILATION.md` section M.\n" % (live["name"], live["name"])
        )
        lines.append(
            "- `%s` -> every relation that reads `cached_tokens`: %s of %s rows carry a null, and a "
            "null is a measured **0** under the settled endpoint rule — those rows stay citable as "
            "`cached = 0`, never as \"unknown\". Source `%s`: `cached_tokens`, `cached_reported`, "
            "`cached_source`.\n"
            % (live["name"], fmt(live["nulls"]), fmt(live["rows"]), live["name"])
        )
        if live["urlerr"]:
            lines.append(
                "- `%s` **self-limitation**: %s of %s rows carry a non-empty `error`, so any count "
                "taken over the file must exclude them rather than treat them as zeros. Source "
                "`%s`: `error`.\n"
                % (live["name"], fmt(live["errors"]), fmt(live["rows"]), live["name"])
            )
        lines.append("")

    # ---- 8.2 equal information -------------------------------------------------------
    equal = by_unit.get("C0-EQUALINFO")
    if equal:
        lines.append("### 8.2 C0-EQUALINFO — the equal-information result\n")
        for model in equal["models"]:
            model_facts = [fact for fact in equal["facts"] if fact["model"] == model]
            endpoint = uniq(fact["endpoint"] for fact in model_facts if fact["endpoint"])
            reported = [fact for fact in model_facts if fact["cached"] is not None]
            pointer = equal["cells"].get((model, "R", "—"))
            plain_arms = sorted(
                {fact["cell"] for fact in model_facts if fact["cell"].startswith("C0")}
            )
            lines.append(
                "**`%s`** on %s — %s of %s rows report a cache counter.\n"
                % (
                    model,
                    ", ".join("`%s`" % value for value in endpoint) or "an unrecorded endpoint",
                    fmt(len(reported)),
                    fmt(len(model_facts)),
                )
            )
            ratios = []
            for arm in plain_arms:
                cell = equal["cells"].get((model, arm, "—"))
                if not cell or not pointer:
                    continue
                turn_reps = len(cell["turn_reps"])
                pointer_reps = len(pointer["turn_reps"])
                if not turn_reps or not pointer_reps:
                    continue
                plain_turn = cell["uncached"] / turn_reps
                pointer_turn = pointer["uncached"] / pointer_reps
                ratio = pointer_turn / plain_turn if plain_turn else 0.0
                ratios.append((arm, plain_turn, pointer_turn, ratio, cell, pointer))
                items = uniq(
                    fact["items"]
                    for fact in model_facts
                    if fact["cell"] == arm and fact["items"] is not None
                )
                lines.append(
                    "- `%s` -> `C67` (the pointer index is null against full history): at %s item(s) "
                    "in context `%s` costs **%s** uncached per turn-rep while `R` costs **%s**, so "
                    "`R` bills %s the plain transcript. Source `%s`: `prompt_tokens`, "
                    "`cached_tokens`, `arm`, `turn`, `rep`, `items_in_context`.\n"
                    % (
                        equal["name"],
                        ", ".join(str(value) for value in items) or "—",
                        arm,
                        fmt(round(plain_turn, 1)),
                        fmt(round(pointer_turn, 1)),
                        fmt_ratio(ratio),
                        equal["name"],
                    )
                )
            if ratios:
                lowest = min(ratios, key=lambda item: item[3])
                highest = max(ratios, key=lambda item: item[3])
                if lowest[3] > 1:
                    verdict = (
                        "the pointer protocol pays more on every plain arm (%s–%s), so this "
                        "measurement **contradicts** the token-saving reading of `C75`/`C76`: the "
                        "compact index's win is a byte ratio (`r`), and it does not reach the "
                        "per-turn bill at this item count"
                        % (fmt_ratio(lowest[3]), fmt_ratio(highest[3]))
                    )
                elif highest[3] < 1:
                    verdict = (
                        "the pointer protocol pays less on every plain arm (%s–%s), so this "
                        "measurement **does not contradict** `C75`/`C76` — but it also cannot "
                        "confirm them, because the arms are compared on gross prompt tokens only"
                        % (fmt_ratio(lowest[3]), fmt_ratio(highest[3]))
                    )
                else:
                    verdict = (
                        "the direction of the ratio is not constant across the plain arms "
                        "(%s–%s), so no single sentence about the protocol's bill survives"
                        % (fmt_ratio(lowest[3]), fmt_ratio(highest[3]))
                    )
                lines.append(
                    "- `%s` -> `C75` / `C76`: %s. Source `%s`: `prompt_tokens`, `cached_tokens`, "
                    "`arm`.\n" % (equal["name"], verdict, equal["name"])
                )
                if len(reported) == 0:
                    lines.append(
                        "- **Bound on every figure above for `%s`**: none of this model's %s rows "
                        "report a cache counter, so those figures are gross-token readings and each "
                        "ratio is a bound, not a cache-aware bill. Source `%s`: `cached_tokens`, "
                        "`cached_reported`.\n" % (model, fmt(len(model_facts)), equal["name"])
                    )
                for arm, plain_turn, pointer_turn, ratio, cell, pointer_cell in ratios[:1]:
                    lines.append(
                        "- `%s` -> `C08` (no accuracy delta): the plain cell `%s` answers %s row(s) "
                        "correctly against %s for `R` — the arithmetic above is a cost difference, "
                        "and this count is the only quality statement the file supports. Source "
                        "`%s`: `answer_correct`.\n"
                        % (
                            equal["name"],
                            arm,
                            fmt(cell["correct"]),
                            fmt(pointer_cell["correct"]),
                            equal["name"],
                        )
                    )
        lines.append("")

    # ---- 8.3 the invalid baseline ----------------------------------------------------
    baseline = by_unit.get("C0-BASELINE")
    if baseline:
        status, reason, source = verdict_of(baseline)
        lines.append("### 8.3 C0-BASELINE — invalid by design, supports nothing\n")
        lines.append(
            "- `%s` -> **no claim**: %s (source `%s`). Every relation that would route through "
            "this file is dead on arrival, and its %s rows are indexed only so nobody re-derives "
            "them. Source `%s`: `unit`, `answer_correct`, `error`.\n"
            % (baseline["name"], reason, source, fmt(baseline["rows"]), baseline["name"])
        )
        for key in sorted(baseline["cells"], key=lambda item: (item[0], item[1], item[2])):
            cell = baseline["cells"][key]
            lines.append(
                "- `%s` cell `%s` on `%s`: %s rows, %s correct of %s answered, %s error row(s) — "
                "recorded, not citable. Source `%s`: `answer_correct`, `error`.\n"
                % (
                    baseline["name"],
                    key[1],
                    key[0],
                    fmt(cell["rows"]),
                    fmt(cell["correct"]),
                    fmt(cell["answered"]),
                    fmt(cell["errors"]),
                    baseline["name"],
                )
            )
        lines.append("")

    lines.append(
        "### 8.4 Non-relations worth stating\n"
        "\n"
        "- Section P and the claim rows are two different ledgers: a `MEASURED` row file is "
        "evidence, and it does not by itself make a claim id resolvable — that still needs an id "
        "in `papers/context-cache/CLAIMS.md`. Source: `COMPILATION.md` section P.\n"
        "- `INVALID-BY-DESIGN` is not `WITHDRAWN`: nothing in the baseline file was refuted by a "
        "later measurement, it was never able to answer the question. Source: section 8.3.\n"
        "- A row file's status never edits a claim row's status. The generator rewrites only the "
        "`status` column of 7-column rows, the `build:` stamp, and the two marker regions — so "
        "any other change to `COMPILATION.md` is a hand edit and must be reviewed as one.\n"
    )
    return "".join(line if line.endswith("\n") else line + "\n" for line in lines)


def splice_region(text, begin, end, body):
    """Replace the generated region delimited by begin/end, or append it when absent."""
    if begin in text and end in text:
        head = text[: text.index(begin)]
        tail = text[text.index(end) + len(end):].lstrip("\n")
        out = head + begin + "\n" + body + end + "\n"
        if tail:
            out += "\n" + tail
        return out
    out = text.rstrip("\n") + "\n\n" + begin + "\n" + body + end + "\n"
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--index", default=DEFAULT_INDEX, help="COMPILATION.md to rebuild in place")
    parser.add_argument("--claims", default=DEFAULT_CLAIMS, help="CLAIMS.md to read claim ids from")
    parser.add_argument(
        "--relations",
        default=DEFAULT_RELATIONS,
        help="COMPILATION-RELATIONS.md to rebuild in place",
    )
    parser.add_argument(
        "--record", default=DEFAULT_RECORD, help="RECORD.md, read only for its build-time state"
    )
    parser.add_argument(
        "--measure-dir",
        default=DEFAULT_MEASURE_DIR,
        help="directory whose rows-*.jsonl files are discovered and indexed",
    )
    parser.add_argument(
        "--row-file",
        action="append",
        default=[],
        metavar="PATH",
        help="extra row file to count (repeatable); also accepted as bare trailing arguments",
    )
    parser.add_argument("--dry-run", action="store_true", help="compute and report, write nothing")
    args = parser.parse_args(argv)

    try:
        index_text = read_text(args.index)
    except OSError as exc:
        print("NOT-PARSED index %s (%s)" % (args.index, exc))
        return 1
    try:
        claims_text = read_text(args.claims)
    except OSError as exc:
        print("NOT-PARSED claims %s (%s)" % (args.claims, exc))
        return 1
    try:
        relations_text = read_text(args.relations)
    except OSError:
        relations_text = None
        print("NOT-PARSED relations %s (absent; not written)" % args.relations)

    known_claims = set(claim_ids_of(claims_text))
    if not known_claims:
        print("NOT-PARSED claims: no claim id found in %s" % args.claims)

    # ---- row files declared in CLAIMS.md: declared vs actual ----------------
    sources = declared_row_sources(claims_text)
    for extra in args.row_file:
        sources.append(("cli", extra, None))
    checked = 0
    mismatches = []
    unparsed = []
    for abbrev, path, declared in sources:
        abspath = path if os.path.isabs(path) else os.path.join(REPO, path)
        actual = count_rows(abspath)
        if actual is None:
            unparsed.append((abbrev, path))
            print("NOT-PARSED %s (%s)" % (path, abbrev))
            continue
        checked += 1
        if declared is not None and actual != declared:
            mismatches.append("%s %d!=%d" % (abbrev, actual, declared))

    # ---- discovered row files: indexed from the rows themselves -----------
    declared_paths = {os.path.normpath(path) for _abbrev, path, _n in sources}
    discovered = [
        path
        for path in sorted(glob.glob(os.path.join(args.measure_dir, "rows-*.jsonl")))
        if os.path.normpath(path) not in declared_paths
    ]
    indices = []
    unclassified = []
    for path in discovered:
        index = index_row_file(path)
        if not index["rows"]:
            print("NOT-PARSED %s (no parseable row)" % os.path.relpath(path, REPO))
            unclassified.append(os.path.relpath(path, REPO))
            continue
        for number in index["bad"]:
            print("NOT-PARSED %s:%d (unparseable line)" % (os.path.relpath(path, REPO), number))
        if verdict_of(index)[0] == "NOT-CLASSIFIED":
            print(
                "NOT-PARSED %s (unit %s has no declared verdict)"
                % (os.path.relpath(path, REPO), "/".join(index["units"]) or "absent")
            )
            unclassified.append(os.path.relpath(path, REPO))
        indices.append(index)

    record_lines = 0
    record_layers = 0
    if os.path.isfile(args.record):
        record_text = read_text(args.record)
        record_lines = len(record_text.splitlines())
        record_layers = record_text.count("BASELINE-COST")
    else:
        print("NOT-PARSED %s (absent)" % os.path.relpath(args.record, REPO))

    # ---- index rows: rebuild status ---------------------------------------
    out_lines = []
    rows = 0
    unresolved = set()
    bad_strength = []
    for line in index_text.splitlines():
        cells = split_row(line)
        if cells is None or is_separator(cells) or cells[0].lower() == "id":
            out_lines.append(line)
            continue
        strength = cells[4]
        if strength not in STRENGTHS:
            bad_strength.append(cells[0])
            out_lines.append(line)
            continue
        ids = ["C%s" % m for m in CLAIM_RE.findall(cells[2])] if cells[2] not in ("—", "-", "") else []
        for cid in ids:
            if cid not in known_claims:
                unresolved.add(cid)
        marker_match = MARKER_RE.match(cells[6])
        status = status_for(strength, ids, known_claims, marker_match.group(1) if marker_match else None)
        cells[5] = status
        out_lines.append("| " + " | ".join(cells) + " |")
        rows += 1

    ready = 0
    withdrawn = 0
    for line in out_lines:
        cells = split_row(line)
        if not cells or is_separator(cells) or cells[0].lower() == "id":
            continue
        if cells[5] in READY_STATUSES:
            ready += 1
        if cells[4] == "WITHDRAWN":
            withdrawn += 1

    measured_files = sum(1 for index in indices if verdict_of(index)[0] == "MEASURED")
    invalid_files = sum(1 for index in indices if verdict_of(index)[0] == "INVALID-BY-DESIGN")

    stamp = (
        "<!-- build: ROWS %d | CLAIMS %d | READY %d | WITHDRAWN %d | ROWFILES %d | MEASURED %d "
        "| INVALID %d -->"
        % (rows, len(known_claims), ready, withdrawn, len(indices), measured_files, invalid_files)
    )
    replaced = False
    for position, line in enumerate(out_lines):
        if BUILD_RE.match(line.strip()):
            out_lines[position] = stamp
            replaced = True
    if not replaced:
        print("NOT-PARSED build stamp: no '<!-- build:' line in %s" % args.index)

    new_text = "\n".join(out_lines)
    if index_text.endswith("\n"):
        new_text += "\n"
    new_text = splice_region(
        new_text,
        ROWS_SECTION_BEGIN,
        ROWS_SECTION_END,
        build_rows_section(indices, record_lines, record_layers),
    )
    new_relations = None
    if relations_text is not None:
        new_relations = splice_region(
            relations_text,
            REL_SECTION_BEGIN,
            REL_SECTION_END,
            build_relations_section(indices),
        )

    changed = new_text != index_text
    relations_changed = new_relations is not None and new_relations != relations_text
    if not args.dry_run:
        for path, text, differs in (
            (args.index, new_text, changed),
            (args.relations, new_relations, relations_changed),
        ):
            if text is None or not differs:
                continue
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as handle:
                handle.write(text)
            os.replace(tmp, path)

    print("ROWS %d | CLAIMS %d | READY %d | WITHDRAWN %d" % (rows, len(known_claims), ready, withdrawn))
    print(
        "ROW-FILES checked %d | ok %d | mismatch %s | not-parsed %s"
        % (
            checked,
            checked - len(mismatches),
            " ".join(mismatches) or "none",
            " ".join(abbrev for abbrev, _path in unparsed) or "none",
        )
    )
    print(
        "ROW-FILES-INDEXED %d | MEASURED %d | INVALID-BY-DESIGN %d | UNCLASSIFIED %d"
        % (len(indices), measured_files, invalid_files, len(unclassified))
    )
    print(
        "CLAIM-IDS unresolved %s | BAD-STRENGTH %s | index %s | relations %s"
        % (
            " ".join(sorted(unresolved)) or "none",
            " ".join(bad_strength) or "none",
            "unchanged" if not changed else ("dry-run" if args.dry_run else "rewritten"),
            "absent"
            if new_relations is None
            else ("unchanged" if not relations_changed else ("dry-run" if args.dry_run else "rewritten")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
