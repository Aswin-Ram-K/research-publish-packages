"""Guard the GAP-TRIAGE decisions (2026-10-23).

`state/gap-ledger.json` derives a status for every section of `papers/context-cache/GAPS.md`.
Eleven of them derive `open`, while `papers/context-cache/verify_package.py` passes with
``UNVERIFIED: none`` — a census of claim *values*, not of scope.  The triage unit recorded, for
each of them, whether it is a **stated limitation** (the measurement that would close it has
not been run and no claim depends on it) or **stale prose** (a later cell had already outdated
the sentence).  Two were stale: G12 (a blanket "no eviction pressure" sentence and a capacity
figure superseded by C54/C59) and G14 ("neither half has been tested at the limit", superseded
by G3-LIMIT-V2/C62 — the hybrid arm itself is still unrun).  G16 was raised by CACHE-AUDIT after
the triage and was triaged by FIX-G16-LEDGER (2026-10-23) under the same stated-limitation rule:
the four options it names (HiCache, lfu/tlru, `--kv-offloading-size`, a chunked-prefix attempt that
launches) were not run and no claim depends on them.

This guard does **not** re-derive gap status; ``tests/test_gap_closure_ledger.py`` owns that.
It checks the triage record is complete and that the two corrected assertions cannot return
without the guard failing.

Green: eleven decisions, nine stated limitations, two stale-prose fixes present.
Red (verified 2026-10-23): restoring either retired sentence fails the matching check below.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "papers" / "context-cache"
GAPS = PKG / "GAPS.md"
PACKAGE = PKG / "PACKAGE.md"
LEDGER = ROOT / "state" / "gap-ledger.json"
TRIAGE = ROOT / "state" / "gap-triage.json"

VALID = frozenset({"stated-limitation", "stale-prose"})
STALE = frozenset({"G12", "G14"})


def _json(path: Path) -> dict:
    assert path.is_file(), f"{path.relative_to(ROOT)} is missing"
    return json.loads(path.read_text(encoding="utf-8"))


def _triage() -> list[dict]:
    return _json(TRIAGE)["decisions"]


# The ids triaged before G16 existed (GAP-TRIAGE 2026-10-23), then G16 (FIX-G16-LEDGER 2026-10-23).
EXPECTED_OPEN = frozenset({
    "G2", "G6", "G7", "G8", "G9", "G10", "G12", "G13", "G14", "G15", "G16",
})
EXPECTED_COUNTS = {
    "gaps_in_ledger": 17,
    "derived_open": 11,
    "stated_limitation": 9,
    "stale_prose": 2,
}


def _gap_block(text: str, gid: str) -> str:
    start = text.find(f"## {gid}.")
    assert start >= 0, f"GAPS.md has no '## {gid}.' section"
    nxt = text.find("\n## ", start + 4)
    return text[start: nxt if nxt > start else len(text)]


def test_decisions_cover_exactly_the_derived_open_gaps() -> None:
    ledger = _json(LEDGER)
    open_ids = [g["id"] for g in ledger["gaps"] if g["derived_status"] == "open"]
    ids = [d["id"] for d in _triage()]
    assert len(ids) == len(set(ids)), f"duplicate triage ids: {ids}"
    assert len(ids) == 11, f"expected eleven derived-open gaps, triaged {len(ids)}: {ids}"
    assert set(ids) == set(open_ids), (
        f"triage ids {sorted(ids)} do not match the eleven derived-open gaps {sorted(open_ids)}"
    )
    assert set(ids) == EXPECTED_OPEN


def test_every_decision_is_labelled_and_evidenced() -> None:
    bad = []
    for d in _triage():
        if d.get("decision") not in VALID:
            bad.append(f"{d.get('id')}: decision {d.get('decision')!r}")
        if not d.get("evidence"):
            bad.append(f"{d.get('id')}: no evidence refs")
        for key in ("why", "action"):
            if not str(d.get(key, "")).strip():
                bad.append(f"{d.get('id')}: empty {key}")
    assert not bad, "incomplete triage decisions:\n" + "\n".join(bad)


def test_counts_match_the_decisions() -> None:
    triage = _json(TRIAGE)
    decisions = triage["decisions"]
    stale = {d["id"] for d in decisions if d["decision"] == "stale-prose"}
    assert stale == STALE, f"stale-prose ids changed: {sorted(stale)}"
    triaged = {d["id"] for d in decisions}
    assert triaged == EXPECTED_OPEN, (
        f"{sorted(triaged ^ EXPECTED_OPEN)} not triaged as expected"
    )
    assert triage["counts"] == EXPECTED_COUNTS, triage["counts"]


def test_each_open_gap_carries_a_status_line() -> None:
    text = GAPS.read_text(encoding="utf-8")
    bad = []
    for d in _triage():
        head = _gap_block(text, d["id"]).splitlines()[0]
        if "STATUS: OPEN" not in head:
            bad.append(f"{d['id']}: {head!r}")
        if "stated limitation" not in head:
            bad.append(f"{d['id']}: status line does not name the classification: {head!r}")
    assert not bad, "open gaps lost their triage status line:\n" + "\n".join(bad)


def test_no_open_gap_is_restyled_as_closed() -> None:
    text = GAPS.read_text(encoding="utf-8")
    bad = []
    for d in _triage():
        head = _gap_block(text, d["id"]).splitlines()[0]
        if re.search(r"\b(CLOSED|NARROWED)\b", head.upper()):
            bad.append(f"{d['id']}: heading claims closure: {head!r}")
    assert not bad, "an open gap's heading claims closure:\n" + "\n".join(bad)


def test_g12_stale_capacity_and_pressure_are_corrected() -> None:
    block = _gap_block(GAPS.read_text(encoding="utf-8"), "G12")
    assert "1,620,892" in block, "G12 lost the declared-capacity figure (C54)"
    assert "no eviction pressure was applied" not in block, (
        "G12 reintroduced the blanket 'no eviction pressure was applied' sentence"
    )
    assert "1.3 M tokens" not in block, "G12 reintroduced the stale 1.3 M capacity figure"
    assert "C54" in block and "C59" in block, "G12 lost its superseding evidence refs"
    assert "GAP-TRIAGE 2026-10-23" in block, "G12 lost its dated correction note"


def test_g14_limit_regime_is_no_longer_denied() -> None:
    block = _gap_block(GAPS.read_text(encoding="utf-8"), "G14")
    assert "G3-LIMIT-V2" in block and "C62" in block, "G14 lost the measured limit-regime refs"
    assert "neither has been tested" not in block.lower(), (
        "G14 reintroduced the blanket 'neither has been tested' sentence"
    )
    assert "hybrid" in block.lower(), "G14 lost the hybrid policy it leaves unrun"
    assert "GAP-TRIAGE 2026-10-23" in block, "G14 lost its dated correction note"


def test_gaps_md_states_the_scope_distinction() -> None:
    text = GAPS.read_text(encoding="utf-8")
    assert "## Triage ledger (GAP-TRIAGE, 2026-10-23)" in text, (
        "GAPS.md lost the triage ledger section"
    )
    assert "not a statement about this list" in text, (
        "GAPS.md no longer distinguishes UNVERIFIED: none from the open-gap list"
    )


def test_package_points_at_the_scope_distinction() -> None:
    text = PACKAGE.read_text(encoding="utf-8")
    assert "claim values" in text, "PACKAGE.md no longer says what UNVERIFIED: none covers"
    assert "state/gap-triage.json" in text, "PACKAGE.md lost the triage pointer"
