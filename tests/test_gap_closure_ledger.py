"""Machine-check the gap ledger (GAP-LEDGER2).

`state/gap-ledger.json` claims, for every gap in `papers/context-cache/GAPS.md`, a
`derived_status` computed from evidence that exists on disk.  This test re-derives that
status independently and fails when:

  (a) the ledger states closed/narrowed for a gap whose derived status is open/unverifiable;
  (b) an evidence ref does not resolve (path missing, line out of range, claim absent);
  (c) a gap present in GAPS.md is missing from the ledger;
  (d) the ledger carries an entry with no gap.

Exemptions are named in EXEMPTIONS with a one-line reason — there are no silent skips.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "papers" / "context-cache"
GAPS = PKG / "GAPS.md"
LEDGER = ROOT / "state" / "gap-ledger.json"
CLAIMS = PKG / "CLAIMS.md"
BASES = (ROOT, PKG, ROOT / "experiments" / "context-cache")
CHECKER_KINDS = frozenset({"claim", "cell", "handoff"})

# gap id -> one-line reason.  No silent skips: an exemption that names no gap fails.
EXEMPTIONS: dict[str, str] = {}


def _known_missing() -> set[tuple[str, str]]:
    """Acknowledged, named misses at the top level of the ledger (gap id, ref)."""
    return {(m["gap"], m["ref"]) for m in _ledger().get("known_missing", [])}


def _ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _entries() -> list[dict]:
    return _ledger()["gaps"]


def gap_ids_in_prose() -> list[str]:
    text = GAPS.read_text(encoding="utf-8")
    ids = re.findall(r"^## (G\d+)\.", text, flags=re.M)
    if re.search(r"^## Downgrade note", text, flags=re.M):
        ids.append("DOWNGRADE")
    return ids


def _resolve(rel: str) -> Path | None:
    for base in BASES:
        cand = base / rel
        if cand.exists():
            return cand
    return None


def _claims_text() -> str:
    return CLAIMS.read_text(encoding="utf-8")


def _handoff_status(name: str) -> str:
    path = ROOT / "orchestration" / "handoffs" / f"{name}.json"
    if not path.is_file():
        return ""
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("status", ""))
    except json.JSONDecodeError:
        return ""


def ref_resolves(ref: dict) -> bool:
    kind, name = ref["kind"], ref["ref"]
    if kind == "claim":
        return re.search(rf"\b{re.escape(name)}\b", _claims_text()) is not None
    if kind == "handoff":
        return _handoff_status(name) == "done"
    if kind in {"path", "cell"}:
        path = _resolve(name)
        if path is None:
            return False
        return (path / "rows.jsonl").is_file() if kind == "cell" else True
    if kind == "file_line":
        rel, sep, line_s = name.rpartition(":")
        if not sep or not line_s.isdigit():
            return False
        path = _resolve(rel)
        if path is None or not path.is_file():
            return False
        return 1 <= int(line_s) <= len(path.read_text(encoding="utf-8").splitlines())
    raise AssertionError(f"unknown ref kind {kind!r} in {name!r}")


def ref_line(ref: dict) -> str:
    rel, _, line_s = ref["ref"].rpartition(":")
    path = _resolve(rel)
    assert path is not None and path.is_file(), ref["ref"]
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[int(line_s) - 1]


def derive(entry: dict) -> tuple[str, list[str]]:
    refs = entry["evidence_refs"]
    unresolved = [r["ref"] for r in refs if not ref_resolves(r)]
    if unresolved:
        return "unverifiable", unresolved
    closure = [
        r for r in refs if r.get("role") == "closure" and r["kind"] in CHECKER_KINDS
    ]
    if closure:
        return ("narrowed" if entry["remainder"]["present"] else "closed"), []
    return "open", []


def stated_class(stated: str | None) -> str:
    text = (stated or "").upper()
    if "NARROWED" in text or "PARTIAL CLOSURE" in text:
        return "narrowed"
    if "CLOSED" in text:
        return "closed"
    if re.search(r"\bOPEN\b", text):
        return "open"
    return "none"


def test_gap_ids_match_ledger() -> None:
    prose = gap_ids_in_prose()
    ledger = [e["id"] for e in _entries()]
    assert len(set(ledger)) == len(ledger), f"duplicate ledger ids: {ledger}"
    missing = [g for g in prose if g not in ledger]
    extra = [g for g in ledger if g not in prose]
    assert not missing, f"gaps in GAPS.md missing from the ledger: {missing}"
    assert not extra, f"ledger entries with no gap in GAPS.md: {extra}"


def test_evidence_refs_resolve() -> None:
    bad = []
    for entry in _entries():
        if entry["id"] in EXEMPTIONS:
            continue
        for ref in entry["evidence_refs"]:
            if (entry["id"], ref["ref"]) in _known_missing():
                continue
            if not ref_resolves(ref):
                bad.append(f"{entry['id']}: `{ref['ref']}` ({ref['kind']}) does not resolve")
    assert not bad, "unresolvable evidence refs:\n" + "\n".join(bad)


def test_stated_closure_is_backed() -> None:
    bad = []
    for entry in _entries():
        if entry["id"] in EXEMPTIONS:
            continue
        claimed, derived = stated_class(entry["stated_status"]), derive(entry)[0]
        if claimed in {"closed", "narrowed"} and derived in {"open", "unverifiable"}:
            unresolved, = (derive(entry)[1],)
            bad.append(
                f"{entry['id']}: stated {entry['stated_status']!r} claims {claimed} "
                f"but derived {derived!r}"
                + (f"; unresolved {unresolved}" if unresolved else "")
            )
    assert not bad, "stated status not backed by evidence:\n" + "\n".join(bad)


def test_derived_status_is_recomputed_not_copied() -> None:
    bad = []
    for entry in _entries():
        if entry["id"] in EXEMPTIONS:
            continue
        derived = derive(entry)[0]
        if entry["derived_status"] != derived:
            bad.append(f"{entry['id']}: ledger says {entry['derived_status']!r}, re-derived {derived!r}")
    assert not bad, "ledger derived_status is stale:\n" + "\n".join(bad)


def test_stored_resolution_flags_match_disk() -> None:
    bad = []
    for entry in _entries():
        for ref in entry["evidence_refs"]:
            live = ref_resolves(ref)
            if bool(ref.get("resolves", live)) != live:
                bad.append(f"{entry['id']}: `{ref['ref']}` flagged resolves={ref['resolves']} but live={live}")
    assert not bad, "ledger resolution flags disagree with disk:\n" + "\n".join(bad)


def test_stale_citation_audit_is_accurate() -> None:
    """A ref carrying `expect` must match its line unless the ledger marks it stale."""
    bad = []
    for entry in _entries():
        for ref in entry["evidence_refs"]:
            if "expect" not in ref:
                continue
            line = ref_line(ref)
            present = ref["expect"] in line
            if present == bool(ref.get("stale", False)):
                bad.append(f"{entry['id']}: `{ref['ref']}` stale={ref.get('stale')} but expect {ref['expect']!r} "
                           f"{'is' if present else 'is not'} on the line")
            if ref.get("stale") and "found" in ref:
                found = ref["found"]
                ok = line.strip().startswith(found) if found else line.strip() == ""
                if not ok:
                    bad.append(f"{entry['id']}: `{ref['ref']}` found quote does not match: {line.strip()[:80]!r}")
    assert not bad, "stale-citation audit is inaccurate:\n" + "\n".join(bad)


def test_exemptions_are_named_and_justified() -> None:
    ledger = {e["id"] for e in _entries()}
    bad = [gid for gid, reason in EXEMPTIONS.items() if gid not in ledger or not reason.strip()]
    assert not bad, f"exemptions naming no gap or carrying no reason: {bad}"


def test_known_missing_is_honest() -> None:
    """Every acknowledged miss is a real, cited miss with a reason; no silent misses."""
    ledger = _ledger()
    entries = {e["id"]: e for e in ledger["gaps"]}
    declared = _known_missing()
    bad = []
    for miss in ledger.get("known_missing", []):
        gap, ref = miss["gap"], miss["ref"]
        if gap not in entries:
            bad.append(f"known_missing names no gap: {gap!r}")
            continue
        cited = {r["ref"]: r for r in entries[gap]["evidence_refs"]}
        if ref not in cited:
            bad.append(f"{gap}: known_missing ref {ref!r} is not cited by the gap")
        elif ref_resolves(cited[ref]):
            bad.append(f"{gap}: {ref!r} is declared missing but resolves")
        if not miss.get("reason", "").strip():
            bad.append(f"{gap}: known_missing {ref!r} carries no reason")
    for entry in ledger["gaps"]:
        for ref in entry["evidence_refs"]:
            if not ref_resolves(ref) and (entry["id"], ref["ref"]) not in declared:
                bad.append(f"{entry['id']}: `{ref['ref']}` does not resolve and is not acknowledged")
    assert not bad, "known_missing is not honest:\n" + "\n".join(bad)
