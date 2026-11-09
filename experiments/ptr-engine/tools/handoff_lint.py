#!/usr/bin/env python3
"""handoff_lint — validate orchestration handoffs against the two contracted shapes.

AGENTS.md contracts two handoff shapes:

  unit handoff      unit, status, artifacts, evidence, blocker, next_unit_hint, write_paths
  verifier verdict  unit, overall, checks, blocker, next_unit_hint, write_paths

`tests/test_orchestration_handoffs.py` only proves each file PARSES. This tool checks
that the claims inside are substantiated: that listed artifacts exist, that a `done`
claim carries evidence, and that a handoff is not still a pre-run stub.

Checks (each has a stable code):

  E_PARSE              not valid JSON. Mid-write tolerance mirrors the existing guard:
                       a file whose bytes change between two immediate reads is
                       reported as skipped_mid_write and never as a failure.
  E_SHAPE              matches neither contracted shape (neither `status` nor `overall`).
  E_MISSING_KEY        a required key for the detected shape is absent.
  E_ARTIFACT_ABSENT    a path in `artifacts` does not exist on disk. The path is
                       reported VERBATIM; existence is checked after stripping a
                       trailing line anchor (`#L12`, `:128`) and surrounding
                       backticks, resolving relative paths against --root.
  E_DONE_NO_EVIDENCE   status:"done" (or overall:"pass") with empty/absent
                       evidence/checks, or with an empty `artifacts` list.
  E_DONE_NO_ARTIFACTS  status:"done" naming zero artifacts that exist on disk.
  E_RECOVERED_NO_EVIDENCE
                       status:"recovered" with empty/absent evidence, or with no
                       `recovery` block. A recovered record is a positive claim: a
                       stub was re-run and the real work landed, so it must carry
                       both its own evidence and the provenance of the recovery.
  E_RECOVERED_NO_PROVENANCE
                       `recovery` block present but missing `from_stub_sha256`
                       and/or `evidence_basis` — the recovered record cannot be
                       tied back to the stub it replaced, nor its basis stated.
  E_STUB               byte- or structurally-identical to a pre-run stub: status
                       "partial", "stub" or "recovered" with no artifacts, no
                       evidence, no commands.
  E_JOURNAL_MISSING    the unit's journal (orchestration/journals/<UNIT>.jsonl) has no
                       usable last record: the file is absent, empty, its last line is
                       not valid JSON, or the last line carries no step number and no
                       timestamp. The detail says which. FORWARD-ONLY: a miss already
                       frozen in the baseline (state/logs/journal-lint-baseline.json) is
                       reported under the record's `journal.exempt` field and never as
                       this error, so the historical corpus cannot be failed
                       retroactively. A unit with no journal and no handoff is invisible
                       here by construction -- the rule is keyed off handoffs, because a
                       handoff is the artefact that names the unit.
                       LIMIT, stated rather than implied: a linter that runs inside a
                       unit's own test suite cannot police a unit that never runs it --
                       the unit that writes no journal is exactly the unit that skips
                       the suite. The alternative is a board-side pre-handoff hook that
                       refuses to settle a card whose journal is absent; that needs
                       operator approval, which this workspace cannot grant, so the
                       check stays advisory-plus-CI instead of blocking on its own.
  W_JOURNAL_STALE      the journal exists but its mtime is older than the handoff's:
                       the handoff was written after the last journal record, so the
                       journal does not describe the work the handoff reports.
  W_NO_COMMANDS        evidence present but carrying no `commands` array.
  W_PARTIAL_NO_EVIDENCE
                       status/overall is "partial" and NO substance key carries
                       anything. A partial is a legitimate result, so this is a
                       warning -- but an empty one is not a result at all. The test is
                       SUBSTANCE UNDER ANY CONTRACTED KEY, not the presence of one key
                       name: `evidence`, `checks`, `measurements`, `findings`,
                       `commands` and `command_or_count` all count. This list exists
                       because rules keyed on `evidence` alone are false-positive
                       generators: V-FIXTURE-V8 is done+pass with NO `evidence` key and
                       is fully substantive (checks, measurements, findings), while a
                       verifier verdict legitimately carries its substance under the
                       shape-mandated `checks`. Measured over this corpus, 2 of the 4
                       cards that prompted this rule are now substantive on disk and
                       correctly pass clean. Never re-narrow this to one key.
  W_PARTIAL_NO_COMMAND a partial WITH substance but with no command string and no
                       non-trivial countable: no `commands`/`command` list and no
                       `command_or_count` (top-level or inside `evidence`). Substance
                       that a reader cannot re-run is a claim, not evidence. A bare
                       `counts` dict is NOT a countable -- {"counts":{"cells":63}}
                       names a number without naming what produced it.
  E_STATUS_WORD_CONTRADICTION
                       `status`/`overall` says "done"/"pass" while no substance key is
                       present: the combination that lets a false PASS into the record
                       with nothing under it. V-FIXTURE-V8 is the negative control and
                       must stay clean. Forward-only baselined like E_JOURNAL_MISSING
                       (state/logs/handoff-partial-baseline.json), so the historical
                       corpus is recorded rather than failed retroactively.
  W_VERSION_STALE      best-effort: the handoff's unit card
                       (orchestration/units/<UNIT>.md) contains a `superseded` marker
                       and the card is NEWER than the handoff, i.e. the unit was
                       superseded by a later card and this handoff describes the old one.

Statuses: a unit handoff may be "done", "partial", "stub" or "recovered". `recovered`
is a third VALID terminal status (a stub that was re-run to completion), not an
exemption: it must satisfy the full unit shape, its artifacts must exist, and it must
carry evidence plus a `recovery` provenance block.

Exit codes: 0 no errors, 1 at least one E_*, 2 usage/IO.  --strict promotes warnings.
Every invocation returns one of 0/1/2 — a `None` exit code is itself a defect, so the
__main__ wrapper normalises anything else to 2.

Read-only: this tool never writes to orchestration/handoffs/.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time

UNIT_REQUIRED = ("unit", "status", "artifacts", "evidence", "blocker", "next_unit_hint", "write_paths")
VERIFIER_REQUIRED = ("unit", "overall", "checks", "blocker", "next_unit_hint", "write_paths")

CODE_ORDER = [
    "E_PARSE", "E_SHAPE", "E_MISSING_KEY", "E_ARTIFACT_ABSENT", "E_DONE_NO_EVIDENCE",
    "E_DONE_NO_ARTIFACTS", "E_RECOVERED_NO_EVIDENCE", "E_RECOVERED_NO_PROVENANCE",
    "E_STUB", "E_JOURNAL_MISSING", "W_JOURNAL_STALE", "W_NO_COMMANDS", "W_VERSION_STALE",
    "W_PARTIAL_NO_EVIDENCE", "W_PARTIAL_NO_COMMAND", "E_STATUS_WORD_CONTRADICTION",
]

UNIT_STATUSES = ("done", "partial", "stub", "recovered")
RECOVERY_PROVENANCE = ("from_stub_sha256", "evidence_basis")
ERROR_CODES = [c for c in CODE_ORDER if c.startswith("E_")]

ANCHOR_RE = re.compile(r"(?:#L\d+(?:-L?\d+)?|:\d+(?:-\d+)?)$")
NOTE_RE = re.compile(r"\s+\(.*\)$")
PTR_RE = re.compile(r"#[A-Za-z0-9_.\[\]~-]+$")
REMOTE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*:(?!/)")


def repo_root_for(path: str) -> str:
    """Walk up from a handoff path looking for the workspace root (has AGENTS.md)."""
    d = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.exists(os.path.join(d, "AGENTS.md")) or os.path.isdir(os.path.join(d, "orchestration")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.getcwd()
        d = parent


def read_stable(path: str):
    """Read bytes twice immediately; return (bytes, changed)."""
    with open(path, "rb") as fh:
        b1 = fh.read()
    with open(path, "rb") as fh:
        b2 = fh.read()
    return b1, b1 != b2


def norm_artifact(p) -> str:
    """Strip the annotations writers habitually append to a path, so a real file is
    not called absent because of a trailing note, line anchor or JSON pointer."""
    s = str(p).strip()
    if len(s) >= 2 and s[0] == s[-1] == "`":
        s = s[1:-1].strip()
    s = NOTE_RE.sub("", s).strip()
    s = ANCHOR_RE.sub("", s)
    s = PTR_RE.sub("", s)
    return s


def _exists(cand: str) -> bool:
    if os.path.exists(cand):
        return True
    try:
        return bool(glob.glob(cand))
    except Exception:
        return False


def artifact_exists(p, root: str) -> bool:
    s = norm_artifact(p)
    if not s:
        return False
    if REMOTE_RE.match(s):
        return False
    # a single entry may carry a brace expansion (dir/{a,b}) or a comma list of paths
    if "{" in s and "}" in s:
        m = re.match(r"^(.*)\{([^{}]*)\}(.*)$", s)
        if m:
            pre, body, post = m.group(1), m.group(2), m.group(3)
            parts = [pre + b.strip() + post for b in body.split(",") if b.strip()]
            return bool(parts) and all(artifact_exists(x, root) for x in parts)
    if ", " in s:
        parts = [x.strip() for x in s.split(", ") if x.strip()]
        if parts:
            return all(artifact_exists(x, root) for x in parts)
    cand = s if os.path.isabs(s) else os.path.join(root, s)
    return _exists(cand)


def is_remote(p) -> bool:
    return bool(REMOTE_RE.match(norm_artifact(p)))


def detect_shape(d: dict) -> str:
    if not isinstance(d, dict):
        return "neither"
    if "overall" in d:
        return "verifier"
    if "status" in d:
        return "unit"
    return "neither"


# --- partial-substance rules -------------------------------------------------
# Substance may live under ANY of these; a rule keyed on one name produces false
# positives (see the module docstring). `counts` is deliberately ABSENT: a number
# without its producer is not evidence.
SUBSTANCE_KEYS = ("evidence", "checks", "measurements", "findings", "commands", "command_or_count")
COMMAND_FIELDS = ("commands", "command", "command_or_count")
PARTIAL_CODES = ("W_PARTIAL_NO_EVIDENCE", "W_PARTIAL_NO_COMMAND", "E_STATUS_WORD_CONTRADICTION")
SUCCESS_WORDS = ("done", "pass")


def nonempty(v) -> bool:
    """True when a value carries something a reader could act on."""
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, (list, tuple, set)):
        return any(nonempty(x) for x in v)
    if isinstance(v, dict):
        return any(nonempty(x) for x in v.values())
    return True


def has_substance(d: dict) -> bool:
    return any(nonempty(d.get(k)) for k in SUBSTANCE_KEYS)


def has_command(d: dict) -> bool:
    ev = d.get("evidence")
    for src in (d, ev if isinstance(ev, dict) else {}):
        for k in COMMAND_FIELDS:
            if nonempty(src.get(k)):
                return True
    return False


def partial_findings(d: dict):
    """The three partial-substance findings for one handoff, as [{code,detail}]."""
    words = set()
    for k in ("status", "overall"):
        v = d.get(k)
        if isinstance(v, str):
            words.add(v.strip().lower())
    out = []
    substance = has_substance(d)
    if "partial" in words:
        if not substance:
            out.append({"code": "W_PARTIAL_NO_EVIDENCE",
                        "detail": "partial with no substance under any of %s" % (", ".join(SUBSTANCE_KEYS),)})
        if not has_command(d):
            out.append({"code": "W_PARTIAL_NO_COMMAND",
                        "detail": "partial with no command string and no non-trivial command_or_count"})
    if words & set(SUCCESS_WORDS) and not substance:
        out.append({"code": "E_STATUS_WORD_CONTRADICTION",
                    "detail": "%s:%s with no substance under any of %s" % (
                        "status" if "status" in d else "overall",
                        "/".join(sorted(words & set(SUCCESS_WORDS))), ", ".join(SUBSTANCE_KEYS))})
    return out


DEFAULT_PARTIAL_BASELINE = os.path.join("state", "logs", "handoff-partial-baseline.json")


def load_partial_baseline(path):
    """Frozen forward-only baseline for the partial-substance codes."""
    empty = {"units": {}, "frozen_at": None, "path": path, "loaded": False}
    if not path or not os.path.exists(path):
        return empty
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return empty
    units = d.get("units") if isinstance(d, dict) else None
    return {
        "units": units if isinstance(units, dict) else {},
        "frozen_at": d.get("frozen_at") if isinstance(d, dict) else None,
        "grace_seconds": d.get("grace_seconds") if isinstance(d, dict) else None,
        "path": path,
        "loaded": True,
    }


def partial_exempt(path: str, mtime: float, base):
    """None when the file is a NEW hit; otherwise the exemption reason."""
    base = base if isinstance(base, dict) else {}
    name = os.path.basename(path)
    if name in (base.get("units") or {}):
        return "frozen-baseline"
    frozen_at = base.get("frozen_at")
    if isinstance(frozen_at, (int, float)) and mtime <= float(frozen_at):
        return "pre-baseline-timestamp"
    if isinstance(frozen_at, (int, float)) and mtime > float(frozen_at):
        try:
            grace = float(base.get("grace_seconds"))
        except (TypeError, ValueError):
            grace = 0.0
        age = time.time() - mtime
        if 0 <= age < grace:  # a future mtime is not "in flight", it is wrong
            return "in-flight-grace"
    return None


def lint_doc(d, root: str) -> dict:
    """Return {'shape':..., 'errors':[{code,detail}], 'warnings':[...]}."""
    shape = detect_shape(d)
    errors, warnings = [], []
    if shape == "neither":
        errors.append({"code": "E_SHAPE", "detail": "neither 'status' (unit) nor 'overall' (verifier)"})
        return {"shape": shape, "errors": errors, "warnings": warnings}

    required = UNIT_REQUIRED if shape == "unit" else VERIFIER_REQUIRED
    for k in required:
        if k not in d:
            errors.append({"code": "E_MISSING_KEY", "detail": f"{shape} shape requires '{k}'"})

    artifacts = d.get("artifacts")
    arts = artifacts if isinstance(artifacts, list) else []
    existing = 0
    absent = []
    for a in arts:
        if artifact_exists(a, root):
            existing += 1
        else:
            absent.append(str(a))
    for a in absent:
        errors.append({"code": "E_ARTIFACT_ABSENT", "detail": a})

    status = d.get("status")
    overall = d.get("overall")
    claims_success = (shape == "unit" and status == "done") or (shape == "verifier" and overall == "pass")

    evidence = d.get("evidence")
    checks = d.get("checks")
    if claims_success:
        has_ev = bool(evidence) if not isinstance(evidence, dict) else bool(evidence)
        has_ck = bool(checks) if isinstance(checks, list) else bool(checks)
        if shape == "unit":
            if not has_ev or not arts:
                errors.append({
                    "code": "E_DONE_NO_EVIDENCE",
                    "detail": ("evidence empty/absent" if not has_ev else "artifacts list empty"),
                })
            if not existing:
                errors.append({"code": "E_DONE_NO_ARTIFACTS", "detail": f"done with {len(arts)} artifacts, 0 exist"})
        else:
            if not has_ck:
                errors.append({"code": "E_DONE_NO_EVIDENCE", "detail": "overall:pass with empty/absent checks"})

    # recovered: a third VALID status that still carries every duty of the unit shape
    recovered = shape == "unit" and status == "recovered"
    if recovered:
        if not evidence:
            errors.append({
                "code": "E_RECOVERED_NO_EVIDENCE",
                "detail": "status:recovered with empty/absent evidence",
            })
        recovery = d.get("recovery")
        if not isinstance(recovery, dict) or not recovery:
            errors.append({
                "code": "E_RECOVERED_NO_EVIDENCE",
                "detail": "status:recovered with no 'recovery' provenance block",
            })
        else:
            for k in RECOVERY_PROVENANCE:
                if not recovery.get(k):
                    errors.append({
                        "code": "E_RECOVERED_NO_PROVENANCE",
                        "detail": f"recovery block missing '{k}'",
                    })

    # stub detection
    stub_candidate = status in ("partial", "stub") or recovered
    if stub_candidate and not arts and not evidence:
        cmds = d.get("commands")
        if cmds is None and isinstance(evidence, dict):
            cmds = evidence.get("commands")
        if not cmds:
            errors.append({"code": "E_STUB", "detail": f"status:{status} with no artifacts, no evidence, no commands"})

    # W_NO_COMMANDS
    if isinstance(evidence, dict) and evidence:
        cmds = evidence.get("commands")
        if not isinstance(cmds, list) or not cmds:
            warnings.append({"code": "W_NO_COMMANDS", "detail": "evidence present but no 'commands' array"})

    return {"shape": shape, "errors": errors, "warnings": warnings,
            "partial_findings": partial_findings(d)}


def version_stale(d, root: str, handoff_mtime: float):
    """Best-effort: unit card carries a 'superseded' marker and is newer than the handoff."""
    unit = d.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        return None
    card = os.path.join(root, "orchestration", "units", unit.strip() + ".md")
    if not os.path.exists(card):
        return None
    try:
        txt = open(card, encoding="utf-8", errors="replace").read().lower()
        cmtime = os.path.getmtime(card)
    except OSError:
        return None
    if "supersed" not in txt:
        return None
    if cmtime > handoff_mtime + 1.0:
        return {"code": "W_VERSION_STALE",
                "detail": f"card orchestration/units/{unit.strip()}.md is newer and carries a superseded marker"}
    return None


JOURNAL_STEP_KEYS = ("step", "n", "step_no", "step_number")
JOURNAL_TS_KEYS = ("t", "ts", "time", "timestamp", "at")
DEFAULT_JOURNAL_BASELINE = os.path.join("state", "logs", "journal-lint-baseline.json")


def journal_path(root: str, unit: str) -> str:
    return os.path.join(root, "orchestration", "journals", unit + ".jsonl")


def load_journal_baseline(path):
    """Frozen forward-only baseline: {'units': {basename: {...}}, 'frozen_at': epoch}.

    Absent or unreadable -> empty baseline, i.e. no exemption (a missing baseline must
    never silently green a real miss)."""
    empty = {"units": {}, "frozen_at": None, "path": path, "loaded": False}
    if not path or not os.path.exists(path):
        return empty
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return empty
    units = d.get("units") if isinstance(d, dict) else None
    if not isinstance(units, dict):
        units = {}
    return {
        "units": units,
        "frozen_at": d.get("frozen_at") if isinstance(d, dict) else None,
        "frozen_at_iso": d.get("frozen_at_iso") if isinstance(d, dict) else None,
        "grace_seconds": (d.get("grace_seconds") if isinstance(d, dict) else None),
        "path": path,
        "loaded": True,
    }


def _first_key(rec: dict, keys):
    for k in keys:
        if k in rec and rec.get(k) is not None:
            return k
    return None


def journal_state(path: str) -> dict:
    """Read-only census of one journal. A torn FINAL line is tolerated the way
    tools/unit_journal.py tolerates it (the earlier records are still usable); the
    last VALID record is what carries the step number and timestamp."""
    st = {
        "path": path, "exists": False, "bytes": 0, "lines": 0, "valid_lines": 0,
        "unparseable_lines": 0, "last_valid": None, "last_line_valid": False,
        "last_has_step": False, "last_has_ts": False, "mtime": None,
    }
    if not os.path.exists(path):
        return st
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        st["mtime"] = round(os.path.getmtime(path), 3)
    except OSError:
        return st
    st["exists"] = True
    st["bytes"] = len(raw)
    text = raw.decode("utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    st["lines"] = len(lines)
    last = None
    for i, ln in enumerate(lines):
        try:
            rec = json.loads(ln)
        except Exception:
            st["unparseable_lines"] += 1
            if i == len(lines) - 1:
                st["last_line_valid"] = False
            continue
        st["valid_lines"] += 1
        if isinstance(rec, dict):
            last = rec
            if i == len(lines) - 1:
                st["last_line_valid"] = True
    st["last_valid"] = last
    if last is not None:
        st["last_has_step"] = _first_key(last, JOURNAL_STEP_KEYS) is not None
        st["last_has_ts"] = _first_key(last, JOURNAL_TS_KEYS) is not None
    return st


def journal_check(unit, handoff_path: str, root: str, handoff_mtime: float, baseline=None):
    """Return (errors, warnings, meta) for the journal rule.

    Only applied when the workspace has an orchestration/journals directory: a synthetic
    or unrelated workspace has no journal convention to police, and the pre-existing
    behaviour of this linter there must not change."""
    meta = {"unit": unit, "exempt": None}
    if not isinstance(unit, str) or not unit.strip():
        return [], [], meta
    jdir = os.path.join(root, "orchestration", "journals")
    if not os.path.isdir(jdir):
        meta["applicable"] = False
        return [], [], meta

    base = baseline if isinstance(baseline, dict) else load_journal_baseline(
        os.path.join(root, DEFAULT_JOURNAL_BASELINE))
    name = os.path.basename(handoff_path)
    st = journal_state(journal_path(root, unit.strip()))
    meta.update(st)
    meta["applicable"] = True
    meta["baseline_loaded"] = bool(base.get("loaded"))

    absent_reason = None
    if not st["exists"]:
        absent_reason = "journal file absent"
    elif st["bytes"] == 0:
        absent_reason = "journal file empty (0 bytes)"
    elif st["valid_lines"] == 0:
        absent_reason = "no valid journal record (%d line(s), %d unparseable)" % (
            st["lines"], st["unparseable_lines"])
    elif st["last_valid"] is not None and not st["last_has_step"]:
        absent_reason = "last valid journal record carries no step number"
    elif st["last_valid"] is not None and not st["last_has_ts"]:
        absent_reason = "last valid journal record carries no timestamp"

    errors, warnings = [], []
    if absent_reason:
        frozen_at = base.get("frozen_at")
        in_units = name in (base.get("units") or {})
        old_enough = isinstance(frozen_at, (int, float)) and handoff_mtime <= float(frozen_at)
        grace = base.get("grace_seconds")
        try:
            grace = float(grace) if grace is not None else 0.0
        except (TypeError, ValueError):
            grace = 0.0
        in_grace = bool(in_units is False and not old_enough
                        and isinstance(frozen_at, (int, float))
                        and handoff_mtime > float(frozen_at)
                        and (time.time() - handoff_mtime) < grace)
        if in_units or old_enough or in_grace:
            meta["exempt"] = ("frozen-baseline" if in_units else
                              "pre-baseline-timestamp" if old_enough else "in-flight-grace")
            meta["exempt_reason"] = absent_reason
        else:
            errors.append({"code": "E_JOURNAL_MISSING", "detail": "%s: %s" % (absent_reason, unit)})
    elif st["mtime"] is not None and st["mtime"] < handoff_mtime - 1.0:
        warnings.append({"code": "W_JOURNAL_STALE",
                         "detail": "%s journal mtime %s precedes handoff mtime %s" % (
                             unit, st["mtime"], round(handoff_mtime, 3))})
    return errors, warnings, meta


def lint_file(path: str, root: str, strict: bool, baseline=None, partial_baseline=None) -> dict:
    rec = {
        "file": path,
        "shape": "neither",
        "bytes": 0,
        "mtime": None,
        "skipped_mid_write": False,
        "errors": [],
        "warnings": [],
        "journal": None,
        "partial_findings": [],
        "ok": True,
    }
    try:
        st = os.stat(path)
        raw, changed = read_stable(path)
    except OSError as exc:
        rec["errors"] = [{"code": "E_PARSE", "detail": f"IO error: {exc}"}]
        rec["ok"] = False
        return rec
    rec["bytes"] = len(raw)
    rec["mtime"] = round(st.st_mtime, 3)
    rec["mtime_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime))
    if changed:
        rec["skipped_mid_write"] = True
        return rec
    try:
        d = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as exc:
        rec["errors"] = [{"code": "E_PARSE", "detail": f"json: {str(exc)[:160]}"}]
        rec["ok"] = False
        return rec
    if not isinstance(d, dict):
        rec["errors"] = [{"code": "E_SHAPE", "detail": f"top-level {type(d).__name__}, expected object"}]
        rec["ok"] = False
        return rec

    res = lint_doc(d, root)
    rec["shape"] = res["shape"]
    rec["errors"] = res["errors"]
    rec["warnings"] = res["warnings"]
    rec["unit"] = d.get("unit")
    rec["status"] = d.get("status", d.get("overall"))
    vs = version_stale(d, root, st.st_mtime)
    if vs:
        rec["warnings"].append(vs)
    jerr, jwarn, jmeta = journal_check(d.get("unit"), path, root, st.st_mtime, baseline)
    rec["journal"] = jmeta
    rec["errors"] += jerr
    rec["warnings"] += jwarn
    if strict:
        rec["errors"] += [{"code": w["code"], "detail": w["detail"], "promoted": True} for w in rec["warnings"]]
    pf = res.get("partial_findings") or []
    exempt_reason = partial_exempt(path, st.st_mtime, partial_baseline)
    for f in pf:
        item = dict(f)
        if exempt_reason:
            item["exempt"] = exempt_reason
            rec.setdefault("partial_exempt", []).append(item)
        else:
            rec["partial_findings"].append(item)
            bucket = rec["errors"] if f["code"].startswith("E_") else rec["warnings"]
            bucket.append({"code": f["code"], "detail": f["detail"]})
    rec["ok"] = not [e for e in rec["errors"] if e["code"].startswith("E_")]
    return rec


def collect(paths, root):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, "*.json")))
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise IOError(f"no such file or directory: {p}")
    return files


def summarize(records):
    by_code, by_shape = {}, {"unit": 0, "verifier": 0, "neither": 0}
    jc = {
        "handoffs_with_unit": 0, "journal_present": 0, "journal_missing": 0,
        "journal_empty": 0, "journal_unparseable": 0, "journal_no_step": 0,
        "journal_no_ts": 0, "journal_stale": 0, "exempt_frozen": 0,
    }
    examples = {}
    done_missing = []
    done_claims = 0
    absent_entries = 0
    absent_remote = 0
    absent_ephemeral = 0
    skipped = 0
    for r in records:
        if r["skipped_mid_write"]:
            skipped += 1
            continue
        by_shape[r["shape"]] = by_shape.get(r["shape"], 0) + 1
        for e in list(r["errors"]) + list(r["warnings"]):
            c = e["code"]
            by_code[c] = by_code.get(c, 0) + 1
            examples.setdefault(c, [])
            if len(examples[c]) < 3 and r["file"] not in examples[c]:
                examples[c].append(r["file"])
            if c == "E_ARTIFACT_ABSENT":
                absent_entries += 1
                if is_remote(e["detail"]):
                    absent_remote += 1
                elif e["detail"].strip().startswith(("/tmp/", "/var/tmp/")):
                    absent_ephemeral += 1
        if r.get("status") in ("done", "pass"):
            done_claims += 1
            # substantiation gap: a success claim whose own artifact list is not all present
            if any(e["code"] in ("E_ARTIFACT_ABSENT", "E_DONE_NO_ARTIFACTS") for e in r["errors"]):
                done_missing.append(r["file"])
        j = r.get("journal") or {}
        if j.get("applicable"):
            jc["handoffs_with_unit"] += 1
            if not j.get("exists"):
                jc["journal_missing"] += 1
            else:
                jc["journal_present"] += 1
                if not j.get("bytes"):
                    jc["journal_empty"] += 1
                if j.get("unparseable_lines"):
                    jc["journal_unparseable"] += 1
                if not j.get("last_has_step"):
                    jc["journal_no_step"] += 1
                if not j.get("last_has_ts"):
                    jc["journal_no_ts"] += 1
                if j.get("mtime") is not None and r.get("mtime") is not None and j["mtime"] < r["mtime"] - 1.0:
                    jc["journal_stale"] += 1
            if j.get("exempt"):
                jc["exempt_frozen"] += 1
    pc = {c: {"new": 0, "exempt": 0} for c in PARTIAL_CODES}
    for r in records:
        for f in r.get("partial_findings") or []:
            pc.setdefault(f["code"], {"new": 0, "exempt": 0})["new"] += 1
        for f in r.get("partial_exempt") or []:
            pc.setdefault(f["code"], {"new": 0, "exempt": 0})["exempt"] += 1
    return {
        "partial_census": pc,
        "files_scanned": len(records),
        "journal_census": jc,
        "skipped_mid_write": skipped,
        "shape_split": by_shape,
        "counts_by_code": by_code,
        "examples_by_code": examples,
        "done_claims": done_claims,
        "done_claims_with_missing_artifacts": len(done_missing),
        "absent_entries": absent_entries,
        "absent_remote_scheme": absent_remote,
        "absent_ephemeral_tmp": absent_ephemeral,
        "done_claim_examples": done_missing[:10],
    }


def exit_code_for(summary) -> int:
    """Every run ends 0 (clean), 1 (any E_*) or 2 (usage/IO). Never None."""
    if any(summary["counts_by_code"].get(c, 0) for c in ERROR_CODES):
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint orchestration handoffs against the two contracted shapes.")
    ap.add_argument("paths", nargs="*", default=[], help="handoff .json file(s) or directory(ies)")
    ap.add_argument("--root", default=None, help="workspace root for resolving relative artifact paths")
    ap.add_argument("--out", default=None, help="write the full JSON report here")
    ap.add_argument("--summary", action="store_true", help="print counts by code and by shape")
    ap.add_argument("--strict", action="store_true", help="promote warnings to errors")
    ap.add_argument("--quiet", action="store_true", help="do not print the per-file table")
    ap.add_argument("--journal-baseline", default=None,
                    help="frozen forward-only journal baseline (default: <root>/state/logs/journal-lint-baseline.json)")
    ap.add_argument("--partial-baseline", default=None,
                    help="frozen forward-only baseline for the partial-substance codes "
                         "(default: <root>/state/logs/handoff-partial-baseline.json)")
    ap.add_argument("--partial-baseline-out", default=None,
                    help="freeze the current NEW partial-substance hits into this JSON (never rewrites)")
    ap.add_argument("--journal-baseline-out", default=None,
                    help="freeze the current E_JOURNAL_MISSING set into this JSON (additive, never rewrites an existing one)")
    args = ap.parse_args(argv)

    paths = args.paths or ["orchestration/handoffs"]
    try:
        files = collect(paths, args.root)
    except IOError as exc:
        print(f"handoff_lint: {exc}", file=sys.stderr)
        return 2
    if not files:
        print(f"handoff_lint: no handoff files under {paths}", file=sys.stderr)
        return 2

    root = args.root or repo_root_for(files[0])
    bpath = args.journal_baseline or os.path.join(root, DEFAULT_JOURNAL_BASELINE)
    baseline = load_journal_baseline(bpath)
    pbpath = args.partial_baseline or os.path.join(root, DEFAULT_PARTIAL_BASELINE)
    pbaseline = load_partial_baseline(pbpath)
    records = [lint_file(f, root, args.strict, baseline=baseline, partial_baseline=pbaseline)
               for f in files]
    summary = summarize(records)
    summary["partial_baseline"] = {"path": pbpath, "loaded": bool(pbaseline.get("loaded")),
                                   "frozen_at": pbaseline.get("frozen_at"),
                                   "frozen_units": len(pbaseline.get("units") or {})}
    summary["journal_baseline"] = {"path": bpath, "loaded": bool(baseline.get("loaded")),
                                   "frozen_at": baseline.get("frozen_at"),
                                   "frozen_units": len(baseline.get("units") or {})}

    if args.journal_baseline_out:
        out_path = args.journal_baseline_out
        if os.path.exists(out_path):
            print(f"handoff_lint: refusing to rewrite an existing frozen baseline: {out_path}", file=sys.stderr)
            return 2
        frozen_at = time.time()
        units = {}
        for r in records:
            j = r.get("journal") or {}
            if j.get("applicable") and not j.get("exempt"):
                # only real misses become baseline entries; a mid-write skip carries no
                # errors at all and so contributes nothing here
                if any(e["code"] == "E_JOURNAL_MISSING" for e in r["errors"]):
                    units[os.path.basename(r["file"])] = {
                        "unit": j.get("unit"),
                        "journal": j.get("path"),
                        "reason": j.get("exempt_reason") or "no usable journal",
                        "handoff_mtime": r.get("mtime"),
                    }
        doc = {
            "frozen_by": "JOURNAL-LINT",
            "frozen_at": frozen_at,
            "frozen_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(frozen_at)),
            "purpose": ("Frozen record of E_JOURNAL_MISSING over the pre-existing corpus. These are "
                        "RECORDED misses, not excused ones: no handoff or journal was edited to satisfy "
                        "the rule. The guard fails only on a miss NOT in this file and newer than "
                        "frozen_at."),
            "rule": ("Forward-only: a handoff is exempt when its basename is a key here, or when its "
                     "mtime is not newer than frozen_at, or when it was written less than "
                     "grace_seconds ago (a sibling unit may still be running its journal-first "
                     "protocol). Everything else that has no usable journal is a new miss and fails "
                     "the test."),
            "grace_seconds": 180,
            "counts": {"entries": len(units),
                       "handoffs_scanned": summary["files_scanned"],
                       "journal_census": summary["journal_census"]},
            "units": units,
        }
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        print(f"\nwrote frozen journal baseline ({len(units)} entries) to {out_path}")

    if args.partial_baseline_out:
        out_path = args.partial_baseline_out
        if os.path.exists(out_path):
            print(f"handoff_lint: refusing to rewrite an existing frozen baseline: {out_path}", file=sys.stderr)
            return 2
        frozen_at = time.time()
        units = {}
        for r in records:
            if not r.get("partial_findings"):
                continue
            units[os.path.basename(r["file"])] = {
                "unit": r.get("unit"),
                "status": r.get("status"),
                "codes": sorted({f["code"] for f in r["partial_findings"]}),
                "bytes": r.get("bytes"),
                "handoff_mtime": r.get("mtime"),
            }
        doc = {
            "frozen_by": "HANDOFF-PARTIAL-SUBSTANCE",
            "frozen_at": frozen_at,
            "frozen_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(frozen_at)),
            "purpose": ("Frozen record of the partial-substance codes over the pre-existing corpus. "
                        "These are RECORDED hits, not excused ones: no handoff was edited to satisfy "
                        "the rule and no evidence was filled in. The guard reports only hits newer "
                        "than frozen_at or absent from this file."),
            "rule": ("Forward-only: exempt when the basename is a key here, or the handoff mtime is "
                     "not newer than frozen_at, or the handoff was written less than grace_seconds "
                     "ago (a sibling unit may still be mid-write)."),
            "substance_keys": list(SUBSTANCE_KEYS),
            "command_fields": list(COMMAND_FIELDS),
            "grace_seconds": 180,
            "counts": {"entries": len(units), "handoffs_scanned": summary["files_scanned"],
                       "partial_census": summary["partial_census"]},
            "units": units,
        }
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        print(f"\nwrote frozen partial baseline ({len(units)} entries) to {out_path}")

    if not args.quiet:
        for r in records:
            if r["skipped_mid_write"]:
                print(f"skip   {r['file']}  (mid-write, bytes changed between reads)")
                continue
            if not r["errors"] and not r["warnings"]:
                continue
            codes = ",".join(e["code"] for e in r["errors"]) or "-"
            warns = ",".join(w["code"] for w in r["warnings"]) or "-"
            print(f"{'FAIL' if not r['ok'] else 'warn'}  {r['file']}  shape={r['shape']}  errors={codes}  warnings={warns}")
            for e in r["errors"]:
                print(f"        {e['code']}: {e['detail']}")

    if args.summary:
        print("\n== summary ==")
        print(f"files scanned          : {summary['files_scanned']}")
        print(f"skipped mid-write      : {summary['skipped_mid_write']}")
        print(f"shape split            : unit={summary['shape_split'].get('unit',0)} "
              f"verifier={summary['shape_split'].get('verifier',0)} neither={summary['shape_split'].get('neither',0)}")
        for c in CODE_ORDER:
            n = summary["counts_by_code"].get(c, 0)
            ex = ", ".join(os.path.basename(x) for x in summary["examples_by_code"].get(c, []))
            print(f"  {c:<20} {n:>5}  {ex}")
        jc = summary["journal_census"]
        print(f"done/pass with missing artifacts: {summary['done_claims_with_missing_artifacts']}")
        print(f"journal census         : handoffs={jc['handoffs_with_unit']} present={jc['journal_present']} "
              f"missing={jc['journal_missing']} empty={jc['journal_empty']} "
              f"unparseable={jc['journal_unparseable']} no_step={jc['journal_no_step']} "
              f"no_ts={jc['journal_no_ts']} stale={jc['journal_stale']} exempt_frozen={jc['exempt_frozen']}")
        for c in PARTIAL_CODES:
            e = summary["partial_census"].get(c, {"new": 0, "exempt": 0})
            print(f"  {c:<20} new={e['new']:>4} exempt_frozen={e['exempt']:>4}")
        pb = summary["partial_baseline"]
        print(f"partial baseline       : {pb['path']} loaded={pb['loaded']} frozen_units={pb['frozen_units']}")
        jb = summary["journal_baseline"]
        print(f"journal baseline       : {jb['path']} loaded={jb['loaded']} frozen_units={jb['frozen_units']}")

    report = {
        "tool": "experiments/ptr-engine/tools/handoff_lint.py",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "root": root,
        "strict": args.strict,
        "summary": summary,
        "files": records,
    }
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
            fh.write("\n")
        print(f"\nwrote {args.out}")

    return exit_code_for(summary)


if __name__ == "__main__":
    _code = main()
    sys.exit(_code if _code in (0, 1, 2) else 2)
