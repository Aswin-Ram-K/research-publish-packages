"""Tests for the docket manifest contract and assembler (U5.2).

Fixtures are synthetic: ``tests/fixtures/docket-store/`` holds a tiny
read-only source tree plus ``seed.json``; each test builds a real
``state.sqlite`` from that seed, copies the source files with the real
:class:`resextract.docket.copy.Copier`, and then assembles a docket from the
stored facts.  Only the *claims* are fixtures — the copying and hashing path is
the production one.

Red→green: the two hard gates this unit owns were reverted one at a time and
the failure output pasted below (see the docstrings of
``test_orphan_claim_refused`` and ``test_material_tampering_refused``).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from resextract import store
from resextract.docket import (
    AssemblyRefused,
    Copier,
    CopyRequest,
    MeasuredResult,
    assemble_docket as assemble,
    material_report_from_docket,
    read_manifest,
    sha256_file,
    validate_manifest,
    verify_docket,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "docket-store"
SOURCES = FIXTURES / "sources"

GENERATED_AT = "2026-10-08T00:00:00Z"

LANE = {
    "slug": "fixture-lane",
    "type": "report",
    "thesis": "The fixture target's trace chain verifies at 503 records.",
    "audience": "maintainers",
}
TARGET = {"slug": "fixture-target", "head_sha": "abc123def456", "graph_hash": "deadbeefcafe"}
FRESHNESS = {
    "verified_at": GENERATED_AT,
    "prior_art_checked_at": None,
    "age_days": 0,
    "state": "current",
}
RESULTS = [
    MeasuredResult(
        name="trace records verified",
        value=503,
        unit="records",
        command="./scripts/run.sh tools/trace.ts verify",
        source_ref="material/docs/FINDINGS.md#L1-L8",
    )
]


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #


def build_store(db_path: Path):
    """Build a real ``state.sqlite`` from the fixture seed and return it."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store.init_db(db_path)
    con = store.connect(db_path)
    seed = json.loads((FIXTURES / "seed.json").read_text(encoding="utf-8"))
    target = dict(seed["target"])
    target["path"] = str(SOURCES)
    store.upsert_target(con, **target)
    store.upsert_lane(con, **seed["lane"])
    for row in seed["claims"]:
        claim_id = store.insert_claim(
            con,
            kind=row["kind"],
            text=row["text"],
            provenance_json=row["provenance"],
            verification_state=row.get("verification_state"),
        )
        store.insert_verdict(
            con, claim_id=claim_id, verdict=row["verdict"], rationale=row.get("rationale", "")
        )
        for ev in row["evidence"]:
            ref = ev["source_ref"]
            source_file = SOURCES / ref.split("#", 1)[0]
            store.insert_evidence(
                con,
                claim_id=claim_id,
                source_kind="local",
                source_ref=ref,
                sha256=sha256_file(source_file),
                quote=ev.get("quote"),
            )
    con.commit()
    return con


def claims_from_store(con) -> list[dict]:
    """Read claims + evidence + verdicts back out of the store.

    Rows are read with raw SQL, so ``*_json`` columns come back as JSON text
    (the store's ``_load`` decoding lives in its accessor helpers).
    """
    out: list[dict] = []
    for claim in con.execute("SELECT * FROM claims ORDER BY id").fetchall():
        provenance = claim["provenance_json"]
        if isinstance(provenance, str):
            provenance = json.loads(provenance)
        evidence = con.execute(
            "SELECT * FROM evidence WHERE claim_id = ? ORDER BY id", (claim["id"],)
        ).fetchall()
        verdicts = con.execute(
            "SELECT * FROM verdicts WHERE claim_id = ? ORDER BY id", (claim["id"],)
        ).fetchall()
        out.append(
            {
                "id": f"C{claim['id']}",
                "text": claim["text"],
                "kind": claim["kind"],
                "provenance": list(provenance or []),
                "verdict": verdicts[-1]["verdict"] if verdicts else "UNVERIFIED",
                "evidence": [f"material/{e['source_ref']}" for e in evidence],
            }
        )
    return out


def copy_material(docket: Path):
    """Copy the fixture's real material into ``docket`` with the U5.1 engine."""
    copier = Copier(SOURCES, docket)
    requests = [
        CopyRequest(
            str(SOURCES / "docs" / "FINDINGS.md"),
            "docs/FINDINGS.md",
            reason="headline findings",
            excerpt=(1, 8),
        ),
        CopyRequest(str(SOURCES / "src" / "core.ts"), "src/core.ts", reason="measured entrypoint"),
        CopyRequest(
            str(SOURCES / "data" / "metrics.json"), "data/metrics.json", reason="measured numbers"
        ),
    ]
    return copier.execute(copier.plan(requests))


def assemble_docket(docket: Path, report, claims, **overrides):
    kwargs = dict(
        lane=dict(LANE),
        claims=claims,
        evidence=[],
        material_report=report,
        web_sources=[],
        target_meta=dict(TARGET),
        freshness=dict(FRESHNESS),
        open_questions=["Is 503 stable across runs?"],
        rework=[
            {
                "text": "re-measure the trace chain after the next release",
                "provenance": "model-suggested",
            }
        ],
        model="fixture-v0",
        generated_at=GENERATED_AT,
        results=list(RESULTS),
        licence="AGPL-3.0-only",
    )
    kwargs.update(overrides)
    return assemble(docket, **kwargs)


def facts(tmp_path: Path, docket: Path):
    """Build the store, copy material, return ``(docket, report, claims)``."""
    con = build_store(tmp_path / "state" / "state.sqlite")
    report = copy_material(docket)
    return docket, report, claims_from_store(con)


# --------------------------------------------------------------------------- #
# happy path
# --------------------------------------------------------------------------- #


def test_happy_path_manifest_and_evidence_bytes(tmp_path):
    docket = tmp_path / "dockets" / "fixture-target" / "fixture-lane"
    docket, report, claims = facts(tmp_path, docket)
    result = assemble_docket(docket, report, claims)

    for name in (
        "README.md",
        "ITEM.md",
        "MANIFEST.json",
        "CLAIMS.md",
        "EVIDENCE.md",
        "PRIOR_ART.md",
        "REFERENCES.md",
        "REFERENCES.bib",
        "RESULTS.md",
        "METHOD.md",
        "CHECKLIST.md",
        "OPEN_QUESTIONS.md",
        "UPDATE_BACKLOG.md",
        "HISTORY.md",
    ):
        assert (docket / name).is_file(), name
    for name in ("web/README.md", "repro/README.md", "repro/run.sh"):
        assert (docket / name).is_file(), name

    manifest = read_manifest(docket / "MANIFEST.json")
    assert manifest.schema_ == "resextract/docket/1"
    assert validate_manifest(docket / "MANIFEST.json") == []
    assert result.claims == 2
    assert result.material == 3
    assert result.downgrades == []

    evidence = (docket / "EVIDENCE.md").read_text(encoding="utf-8")
    # the actual copied bytes, quoted from material/ (never from the source tree)
    assert "KNOWN-EXCERPT-SUBSTRING: the trace chain verifies at 503 records." in evidence
    assert "## `material/docs/FINDINGS.md` — lines 1-8" in evidence
    assert sha256_file(docket / "material" / "docs" / "FINDINGS.md") in evidence

    # RESULTS renders only structured input
    assert "503" in (docket / "RESULTS.md").read_text(encoding="utf-8")
    # UPDATE_BACKLOG marks model-suggested provenance
    assert "[model-suggested]" in (docket / "UPDATE_BACKLOG.md").read_text(encoding="utf-8")


def test_results_empty_renders_explicit_line(tmp_path):
    docket = tmp_path / "dockets" / "empty-results"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims, results=[])
    text = (docket / "RESULTS.md").read_text(encoding="utf-8")
    assert "No measured results recorded" in text


def test_prior_art_stub_lists_unverified_claims(tmp_path):
    docket = tmp_path / "dockets" / "prior-art-stub"
    docket, report, claims = facts(tmp_path, docket)
    claims[0]["verdict"] = "UNVERIFIED"
    assemble_docket(docket, report, claims)
    text = (docket / "PRIOR_ART.md").read_text(encoding="utf-8")
    assert "No external prior art was supplied" in text
    assert "C1" in text
    item = (docket / "ITEM.md").read_text(encoding="utf-8")
    assert "No `PRIOR_ART.md` entries exist yet" in item


# --------------------------------------------------------------------------- #
# gate 1: orphan claims  (RED→GREEN #1)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "overrides,needle",
    [
        ({"provenance": []}, "no provenance"),
        ({"evidence": []}, "no evidence"),
    ],
)
def test_orphan_claim_refused(tmp_path, overrides, needle):
    """RED (orphan-claim gate reverted) — the test fails, pasted output:

    E   ValueError: refusing to write an invalid MANIFEST.json: claims[C1]: no provenance
    src/resextract/docket/manifest.py:197: ValueError: refusing to write an invalid MANIFEST.json: claims[C1]: no provenance
    E   ValueError: refusing to write an invalid MANIFEST.json: claims[C1]: no evidence
    src/resextract/docket/manifest.py:197: ValueError: refusing to write an invalid MANIFEST.json: claims[C1]: no evidence

    With the gate reverted, ``assemble`` no longer raises ``AssemblyRefused``
    itself; the atomic manifest writer's second-layer validation catches it
    instead.  The test still fails, which is what red→green requires.
    """
    docket = tmp_path / "dockets" / "orphan"
    docket, report, claims = facts(tmp_path, docket)
    claims[0].update(overrides)
    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(docket, report, claims)
    message = str(excinfo.value)
    assert "C1" in message
    assert needle in message
    assert not (docket / "MANIFEST.json").exists()
    assert not (docket / "README.md").exists()


def test_orphan_provenance_ref_must_resolve(tmp_path):
    """A provenance ref that names no copied file is fabricated → refuse."""
    docket = tmp_path / "dockets" / "fabricated"
    docket, report, claims = facts(tmp_path, docket)
    claims[0]["provenance"] = ["file:docs/NOPE.md#L1-L5"]
    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(docket, report, claims)
    assert "docs/NOPE.md" in str(excinfo.value)
    assert not (docket / "MANIFEST.json").exists()


def test_evidence_span_past_eof_refused(tmp_path):
    docket = tmp_path / "dockets" / "past-eof"
    docket, report, claims = facts(tmp_path, docket)
    claims[0]["evidence"] = ["material/docs/FINDINGS.md#L900-L999"]
    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(docket, report, claims)
    assert "outside material/docs/FINDINGS.md" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# gate 2: material tampering  (RED→GREEN #2)
# --------------------------------------------------------------------------- #


def test_material_tampering_refused(tmp_path):
    """RED (sha256 gate reverted) — the test fails, pasted output:

    E   ValueError: refusing to write an invalid MANIFEST.json: claims[C1].evidence: sha256 mismatch for material/docs/FINDINGS.md (manifest 1ac9f4239172…, disk 6c0e099667eb…); material[docs/FINDINGS.md]: sha256 mismatch (manifest 1ac9f4239172…, disk 6c0e099667eb…)
    src/resextract/docket/manifest.py:197: ValueError: refusing to write an invalid MANIFEST.json: ...

    Same shape as above: with the sha256 gate reverted the tampered byte is
    only caught by ``write_manifest``'s re-validation, the test's expected
    ``AssemblyRefused`` never arrives, and the test fails.
    """
    docket = tmp_path / "dockets" / "tampered"
    docket, report, claims = facts(tmp_path, docket)
    victim = docket / "material" / "docs" / "FINDINGS.md"
    victim.write_bytes(victim.read_bytes() + b"\nTAMPER\n")

    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(docket, report, claims)
    message = str(excinfo.value)
    assert "sha256 mismatch" in message
    assert "docs/FINDINGS.md" in message
    assert not (docket / "MANIFEST.json").exists()


# --------------------------------------------------------------------------- #
# §3.6 publication-type guards + downgrade
# --------------------------------------------------------------------------- #


def test_paper_without_external_anchor_refused(tmp_path):
    docket = tmp_path / "dockets" / "paper-no-anchor"
    docket, report, claims = facts(tmp_path, docket)
    for claim in claims:
        claim["verdict"] = "UNVERIFIED"
    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(docket, report, claims, lane=dict(LANE, type="paper"))
    message = str(excinfo.value)
    assert "§3.6 guard" in message
    assert "CONFIRMS or EXTENDS" in message
    assert not (docket / "MANIFEST.json").exists()


def test_paper_without_measured_result_refused(tmp_path):
    docket = tmp_path / "dockets" / "paper-no-result"
    docket, report, claims = facts(tmp_path, docket)
    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(
            docket, report, claims, lane=dict(LANE, type="paper"), results=[]
        )
    assert "measured result" in str(excinfo.value)
    assert not (docket / "MANIFEST.json").exists()


def test_benchmark_card_without_recomputable_results_refused(tmp_path):
    docket = tmp_path / "dockets" / "bench-no-result"
    docket, report, claims = facts(tmp_path, docket)
    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(
            docket, report, claims, lane=dict(LANE, type="benchmark_card"), results=[]
        )
    assert "benchmark_card" in str(excinfo.value)
    assert "§3.6 guard" in str(excinfo.value)


def test_paper_with_anchor_and_result_is_allowed(tmp_path):
    docket = tmp_path / "dockets" / "paper-ok"
    docket, report, claims = facts(tmp_path, docket)
    result = assemble_docket(docket, report, claims, lane=dict(LANE, type="paper"))
    assert result.manifest.lane.type == "paper"


def test_unknown_type_downgrades_to_memo(tmp_path):
    docket = tmp_path / "dockets" / "downgrade"
    docket, report, claims = facts(tmp_path, docket)
    result = assemble_docket(docket, report, claims, lane=dict(LANE, type="podcast"))
    assert result.manifest.lane.type == "memo"
    assert result.downgrades and "downgraded to 'memo'" in result.downgrades[0]
    history = (docket / "HISTORY.md").read_text(encoding="utf-8")
    assert "downgrade" in history and "podcast" in history
    assert "memo" in (docket / "CHECKLIST.md").read_text(encoding="utf-8")


def test_conflicting_lane_refused(tmp_path):
    docket = tmp_path / "dockets" / "conflict"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims)
    with pytest.raises(AssemblyRefused) as excinfo:
        assemble_docket(docket, report, claims, lane=dict(LANE, slug="other-lane"))
    assert "other-lane" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# determinism, append-only history, ITEM preservation
# --------------------------------------------------------------------------- #


def test_deterministic_renders_with_frozen_generated_at(tmp_path):
    first = tmp_path / "dockets" / "first"
    _, report_a, claims_a = facts(tmp_path / "a", first)
    assemble_docket(first, report_a, claims_a)

    second = tmp_path / "dockets" / "second"
    _, report_b, claims_b = facts(tmp_path / "b", second)
    assemble_docket(second, report_b, claims_b)

    for name in ("README.md", "CLAIMS.md", "RESULTS.md", "MANIFEST.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_history_append_only_and_item_preserved(tmp_path):
    docket = tmp_path / "dockets" / "repeat"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims)
    first_item = (docket / "ITEM.md").read_text(encoding="utf-8")
    first_history = (docket / "HISTORY.md").read_text(encoding="utf-8")

    assemble_docket(docket, report, claims)
    second_history = (docket / "HISTORY.md").read_text(encoding="utf-8")

    assert second_history.startswith(first_history.rstrip("\n"))
    assert second_history.count(f"## {GENERATED_AT} — assembly") == 2
    assert (docket / "ITEM.md.r1").is_file()
    assert (docket / "ITEM.md.r1").read_text(encoding="utf-8") == first_item


# --------------------------------------------------------------------------- #
# verify_docket
# --------------------------------------------------------------------------- #


def test_verify_docket_passes_on_good_docket(tmp_path):
    docket = tmp_path / "dockets" / "verify-ok"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims)
    verification = verify_docket(docket)
    assert verification.ok, verification.problems
    assert verification.problems == []
    assert verification.claims == 2
    assert verification.material == 3


def test_verify_docket_fails_after_material_tamper(tmp_path):
    docket = tmp_path / "dockets" / "verify-tamper"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims)
    victim = docket / "material" / "src" / "core.ts"
    victim.write_bytes(victim.read_bytes() + b"// tampered\n")

    verification = verify_docket(docket)
    assert not verification.ok
    joined = " | ".join(verification.problems)
    assert "src/core.ts" in joined
    assert "sha256 mismatch" in joined


def test_verify_docket_fails_on_dangling_evidence_ref(tmp_path):
    docket = tmp_path / "dockets" / "verify-dangling"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims)
    manifest_path = docket / "MANIFEST.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["claims"][0]["evidence"] = ["material/docs/DOES_NOT_EXIST.md"]
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    verification = verify_docket(docket)
    assert not verification.ok
    assert any("DOES_NOT_EXIST.md" in p for p in verification.problems)


def test_verify_docket_reports_missing_manifest(tmp_path):
    verification = verify_docket(tmp_path / "nothing-here")
    assert not verification.ok
    assert "MANIFEST.json not found" in verification.problems[0]


# --------------------------------------------------------------------------- #
# checklist
# --------------------------------------------------------------------------- #


def test_checklist_has_licence_gate_and_pdf_note(tmp_path, monkeypatch):
    import importlib

    assemble_mod = importlib.import_module("resextract.docket.assemble")
    monkeypatch.setattr(assemble_mod.shutil, "which", lambda name: None)
    docket = tmp_path / "dockets" / "checklist"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims)
    text = (docket / "CHECKLIST.md").read_text(encoding="utf-8")
    assert "Licence gate" in text
    assert "AGPL-3.0-only" in text
    assert "PDF export unavailable" in text
    assert "pdflatex" in text and "pandoc" in text and "tectonic" in text


# --------------------------------------------------------------------------- #
# manifest contract strictness
# --------------------------------------------------------------------------- #


def test_manifest_forbids_unknown_fields():
    from pydantic import ValidationError

    from resextract.docket.manifest import DocketManifest

    with pytest.raises(ValidationError):
        DocketManifest.model_validate(
            {
                "schema": "resextract/docket/1",
                "lane": {"slug": "s", "type": "memo", "thesis": "", "audience": ""},
                "target": {"slug": "t"},
                "status": "draft",
                "freshness": {"state": "current"},
                "typo_field": 1,
            }
        )


def test_validate_manifest_flags_bad_enum_and_empty_claim():
    raw = {
        "schema": "resextract/docket/1",
        "lane": {"slug": "s", "type": "memo", "thesis": "", "audience": ""},
        "target": {"slug": "t"},
        "status": "draft",
        "freshness": {"state": "current"},
        "claims": [{"id": "C1", "text": "x", "provenance": [], "evidence": []}],
        "material": [],
        "web_sources": [],
        "open_questions": [],
        "rework_open": [],
        "generated_by": {"app": "resextract", "version": "0.1.0", "model": ""},
        "generated_at": None,
    }
    problems = validate_manifest(raw)
    assert any("no provenance" in p for p in problems)
    assert any("no evidence" in p for p in problems)

    bad = dict(raw)
    bad["status"] = "published"
    assert any("status" in p for p in validate_manifest(bad))


def test_material_report_bridge_reads_excerpts_not_repo(tmp_path):
    docket = tmp_path / "dockets" / "bridge"
    docket, _report, _claims = facts(tmp_path, docket)
    bridge = material_report_from_docket(docket, source_root=str(SOURCES))
    assert bridge.copied_count == 3
    spans = {i.dest: i.excerpt for i in bridge.copied}
    assert spans["docs/FINDINGS.md"] == (1, 8)
    assert spans["src/core.ts"] is None


# --------------------------------------------------------------------------- #
# U5.22 -- the boundary: standing is capped where it is *written*
# --------------------------------------------------------------------------- #


def test_assembled_confirms_capped_when_claim_producer_is_replay(tmp_path):
    """ITEM 1: a caller-supplied CONFIRMS with a non-model producer renders EXTENDS.

    Red→green (guard: revert ``_cap_uncapped_claims``):
RED: test_assembled_confirms_capped_when_claim_producer_is_replay
    590: AssertionError: assert 'CONFIRMS' == 'EXTENDS'
    """
    docket = tmp_path / "dockets" / "capped"
    docket, report, claims = facts(tmp_path, docket)
    def _usable(c):
        if isinstance(c, dict):
            return bool(c.get("provenance") and c.get("evidence"))
        return bool(getattr(c, "provenance", None) and getattr(c, "evidence", None))

    good = next(c for c in claims if _usable(c))
    bad = dict(good.model_dump() if hasattr(good, "model_dump") else good)
    bad.update({"id": "C-smuggled", "verdict": "CONFIRMS", "producer": "replay"})

    assemble_docket(docket, report, [bad], producer="replay")

    rendered = {c.id: c for c in read_manifest(docket / "MANIFEST.json").claims}
    assert rendered["C-smuggled"].verdict == "EXTENDS"
    assert rendered["C-smuggled"].producer == "replay"
    assert rendered["C-smuggled"].verdict_reason is not None
    assert "not 'model'" in rendered["C-smuggled"].verdict_reason
    text = (docket / "CLAIMS.md").read_text(encoding="utf-8")
    assert "## C-smuggled — EXTENDS" in text
    assert "## C-smuggled — CONFIRMS" not in text


def test_verify_docket_flags_confirms_without_model_producer(tmp_path):
    """ITEM 2: the verifier detects a standing that contradicts its producer.

    Red→green (guard: revert ``_claim_standing_problems``):
RED: test_verify_docket_flags_confirms_without_model_producer
    618: AssertionError: assert not True
    """
    docket = tmp_path / "dockets" / "smuggled"
    docket, report, claims = facts(tmp_path, docket)
    assemble_docket(docket, report, claims)
    assert verify_docket(docket).ok  # baseline: nothing contradicts itself yet

    path = docket / "MANIFEST.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["claims"][0]["verdict"] = "CONFIRMS"
    raw["claims"][0]["verdict_reason"] = None
    raw["claims"][0]["producer"] = "replay"
    path.write_text(json.dumps(raw, indent=2, sort_keys=True), encoding="utf-8")

    caught = verify_docket(docket)
    assert not caught.ok
    assert any("CONFIRMS" in p and "not 'model'" in p for p in caught.problems), caught.problems

    # no false positive: the same standing backed by a *model* producer passes
    for c in raw["claims"]:
        c["producer"] = "model"
    path.write_text(json.dumps(raw, indent=2, sort_keys=True), encoding="utf-8")
    assert verify_docket(docket).problems == []


def test_item_rotation_bounded_and_current_item_survives(tmp_path):
    """ITEM 3: the ``.rN`` rotation keeps the newest N and never eats ITEM.md.

    Red→green (guard: revert the bound in ``_preserve_item``):
RED: test_item_rotation_bounded_and_current_item_survives
    634: ImportError: cannot import name 'ITEM_SNAPSHOT_KEEP' from 'resextract.docket.assemble' (/home/zer0null/reserach extarctor/src/resextract/docket/assemble.py)
    """
    from resextract.docket.assemble import ITEM_SNAPSHOT_KEEP

    docket = tmp_path / "dockets" / "rotate"
    docket, report, claims = facts(tmp_path, docket)
    for k in range(8):
        (docket / "ITEM.md").write_text(f"# sentinel {k}\n", encoding="utf-8")
        assemble_docket(docket, report, claims)

    snaps = sorted(docket.glob("ITEM.md.r*"), key=lambda p: int(p.suffix[2:]))
    assert len(snaps) == ITEM_SNAPSHOT_KEEP == 5
    # the newest snapshot is the most recent prior ITEM.md -- content not lost
    assert snaps[-1].read_text(encoding="utf-8") == "# sentinel 7\n"
    assert [p.name for p in snaps] == [
        "ITEM.md.r4", "ITEM.md.r5", "ITEM.md.r6", "ITEM.md.r7", "ITEM.md.r8",
    ]
    # the live document survives pruning and is the freshly rendered one
    live = (docket / "ITEM.md").read_text(encoding="utf-8")
    assert live and "sentinel" not in live
