"""Build the deterministic fixture tree for ``tests/test_dashboard.py``.

Run:  ``.venv/bin/python tests/fixtures/dashboard-store/build.py``

Creates, under this directory:
  * ``state.sqlite``            — seeded runs/candidates/claims/verdicts/web rows
  * ``journal/fixture-run.jsonl``  — 6 hash-chained events, **no** reasoning_content
  * ``journal/sparse-run.jsonl``   — chain that stops without run_end (resume point)
  * ``dockets/ok-docket/``      — a valid docket (claims resolve to copied material)
  * ``dockets/broken-docket/``  — a corrupt MANIFEST.json
  * ``ok-docket/``              — decoy *outside* the dockets root, the escape target
                                  used by the directory-traversal red→green guard
  * ``graph-mini.json``         — a 3-node/2-edge/2-community graph
  * ``dockets-empty/``          — an empty directory (the "no dockets at all" case)

Idempotent: it rebuilds the tree from scratch each run.

Reproducibility / red→green guard (a *fixture-build* guard, not an assertion guard)
----------------------------------------------------------------------------------
The dashboard suite used to read the pre-generated ``state.sqlite`` in this
directory directly, and ``dockets/`` is matched by ``.gitignore``'s ``dockets/``
rule (which applies at any depth), so a fresh checkout was not a green suite.
``build(dest_dir)`` lets the suite build the whole tree on demand into a pytest
``tmp_path`` instead.

Guard reverted (``tests/test_dashboard.py`` back to reading this directory),
with the pre-generated ``state.sqlite`` and the gitignored ``dockets/`` removed::

    $ .venv/bin/python -m pytest tests/test_dashboard.py -q
    E  AssertionError: assert ('error' not in {'error': 'store not found:
       /home/zer0null/reserach extarctor/tests/fixtures/dashboard-store/state.sqlite',
       'tables': {}} or 'store not found: .../state.sqlite' is None)
    FAILED tests/test_dashboard.py::test_status_reports_fixture_counts
    FAILED tests/test_dashboard.py::test_dockets_board_lists_valid_and_corrupt
    FAILED tests/test_dashboard.py::test_docket_detail_renders_headings - KeyError: 'manifest'
    12 failed, 36 passed in 12.40s

Guard restored (on-demand build into ``tmp_path``), same clean state::

    $ .venv/bin/python -m pytest tests/test_dashboard.py -q
    48 passed in 11.52s

``sha256(tests/test_dashboard.py)`` before the revert and after the restore were
equal (``9ea0b8cca6110499b1d2a5687d3965b5594c70e31e8269ec407286497707dae5``),
so the revert was fully undone.  With the committed ``state.sqlite`` present the
suite also passes (48 passed in 11.76s), and a second consecutive run from the
clean state passes too (48 passed in 15.18s — the on-demand build is idempotent).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
sys.path.insert(0, str(WORKSPACE / "src"))

from resextract import journal as journal_mod  # noqa: E402
from resextract.docket.manifest import (  # noqa: E402
    Claim,
    DocketManifest,
    Freshness,
    GeneratedBy,
    Lane,
    MaterialItem,
    Target,
    write_manifest,
)
from resextract.store import init_db  # noqa: E402
import resextract.store as store  # noqa: E402

NOTE = "line one\nline two\nline three\nline four\nline five\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_docket(directory: Path, lane_slug: str) -> None:
    material_dir = directory / "material"
    material_dir.mkdir(parents=True, exist_ok=True)
    note = material_dir / "note.txt"
    note.write_text(NOTE, encoding="utf-8")
    manifest = DocketManifest(
        lane=Lane(
            slug=lane_slug,
            type="report",
            thesis="fixture docket: claims are fixture assertions over a real copied byte.",
            audience="dashboard testers",
        ),
        target=Target(slug="duval-fixture", head_sha="deadbeef", graph_hash="cafefeed"),
        status="ready",
        freshness=Freshness(
            verified_at="2026-10-07T00:00:00Z",
            age_days=1.5,
            state="stale",
        ),
        claims=[
            Claim(
                id="C1",
                text="the fixture material note.txt exists and is copied with a matching sha256",
                kind="finding",
                provenance=["file:note.txt#L1-L2"],
                verdict="CONFIRMS",
                # U6.23: ``CONFIRMS`` standing requires a ``model`` backing
                # producer (U5.22 ``_claim_standing_problems``).  The fixture is
                # named ``ok-docket`` and the suite asserts it verifies ok, so
                # the claim declares the producer that produced it *here* -- the
                # model-backed path -- instead of failing verification by
                # default.  The fixture is now valid by construction.
                producer="model",
                evidence=["material/note.txt#L1-L2"],
            ),
            Claim(
                id="C2",
                text="a second fixture claim deliberately left UNVERIFIED so the UI shows an open verdict",
                kind="code-fact",
                provenance=["file:note.txt#L3-L4"],
                verdict="UNVERIFIED",
                evidence=["material/note.txt#L3-L4"],
            ),
        ],
        material=[
            MaterialItem(
                src="/nonexistent/fixture/note.txt",
                dest="note.txt",
                sha256=sha256_text(NOTE),
                bytes=len(NOTE.encode("utf-8")),
            )
        ],
        open_questions=["does the fixture cover every claim it makes?"],
        rework_open=["refresh evidence for C2 once the model endpoint is back"],
        # U6.23: docket-level producer must agree with the claim's standing, so
        # ``verify_docket``'s message no longer reports a non-model run.
        generated_by=GeneratedBy(
            app="resextract",
            version="0.1.0",
            model="fixture-claims-u6.1",
            producer="model",
        ),
        generated_at="2026-10-08T00:00:00Z",
    )
    write_manifest(str(directory), manifest)
    (directory / "README.md").write_text(
        "# Fixture docket\n\n## Thesis\n\nfixture claims over a real copied byte.\n\n## Verdict\n\nCONFIRMS (fixture)\n",
        encoding="utf-8",
    )
    (directory / "CLAIMS.md").write_text(
        "# Claims\n\n## C1\n\nthe note exists.\n\n## C2\n\nopen verdict.\n",
        encoding="utf-8",
    )
    (directory / "EVIDENCE.md").write_text(
        "# Evidence\n\n## material/note.txt\n\ncopied, sha256 verified.\n",
        encoding="utf-8",
    )
    (directory / "UPDATE_BACKLOG.md").write_text(
        "# Update backlog\n\n## open\n\nrefresh C2 when Occamy returns.\n",
        encoding="utf-8",
    )
    (directory / "HISTORY.md").write_text("# History\n\n## 1\n\nbuilt as a fixture.\n", encoding="utf-8")


def write_manifest_text(directory: Path, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "MANIFEST.json").write_text(text, encoding="utf-8")


def build_journal(path: Path, entries: list[tuple[int, str, str, dict]]) -> None:
    prev = ""
    lines = []
    for seq, ts, kind, fields in entries:
        entry = {"seq": seq, "ts": ts, "kind": kind}
        entry.update(journal_mod.redact(fields))
        entry["prev"] = prev
        entry["hash"] = journal_mod.entry_hash(entry)
        prev = entry["hash"]
        lines.append(journal_mod.canonical(entry))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_store(path: Path) -> None:
    if path.exists():
        path.unlink()
    init_db(path)
    con = store.connect(path)
    try:
        store.upsert_run(con, id=1, target="/tmp/target", started_at="2026-10-08T10:00:00.000Z",
                         finished_at="2026-10-08T10:00:30.000Z", status="done",
                         budget={"max_calls": 18, "max_tokens": 200000}, tokens_used=1200,
                         notes="fixture-run accepted=1 rejected=1")
        store.upsert_run(con, id=2, target="/tmp/target", started_at="2026-10-08T10:05:00.000Z",
                         finished_at=None, status="running",
                         budget={"max_calls": 18, "max_tokens": 200000}, tokens_used=0,
                         notes="sparse-run interrupted before run_end")
        store.upsert_candidate(con, id=1, run_id=1, kind="novel_primitive", title="fixture primitive",
                               summary="a fixture candidate accepted by the miner",
                               provenance_json={"refs": ["src/a.ts#L1-L2"]},
                               graph_nodes_json=["node_a"], score=0.9, state="mined")
        store.upsert_candidate(con, id=2, run_id=1, kind="negative_result", title="fixture ghost",
                               summary="all-refs-invalid", provenance_json={"refs": ["graph:ghost"]},
                               graph_nodes_json=[], score=0.1, state="rejected")
        store.insert_claim(con, candidate_id=1, kind="finding", text="the fixture primitive exists",
                           provenance_json={"refs": ["src/a.ts#L1-L2"]},
                           verification_state="verified", confidence=0.8)
        store.insert_claim(con, candidate_id=1, kind="code-fact", text="a second fixture claim",
                           provenance_json={"refs": ["src/a.ts#L3-L4"]},
                           verification_state="unverified", confidence=0.4)
        store.insert_evidence(con, claim_id=1, source_kind="local", source_ref="src/a.ts#L1-L2",
                              sha256="a" * 64, quote="export const a = 1", context="fixture",
                              retrieved_at="2026-10-08T10:00:10.000Z", copy_path="material/src/a.ts")
        store.insert_verdict(con, claim_id=1, verdict="CONFIRMS", rationale="fixture evidence matches",
                             evidence_ids_json=[1], checked_at="2026-10-08T10:00:11.000Z")
        store.upsert_web_source(con, url="https://example.invalid/ok", sha256="b" * 64,
                                title="fixture source", fetched_at="2026-10-08T09:00:00.000Z",
                                http_status=200, extracted_text_path="state/web/ok.txt")
        store.upsert_web_source(con, url="https://example.invalid/gone", sha256=None,
                                title="gone fixture source", fetched_at="2026-10-08T09:01:00.000Z",
                                http_status=404, failure_reason="HTTP 404")
        store.insert_search_health(con, ts="2026-10-08T09:00:00.000Z", engine="duckduckgo",
                                   query="fixture query", result_count=5, ok=True)
        store.insert_search_health(con, ts="2026-10-08T09:02:00.000Z", engine="google",
                                   query="fixture query failed", result_count=0, ok=False,
                                   error="SearXNG 429: too many requests")
        store.upsert_lane(con, id=1, target="duval-fixture", slug="fixture-lane", title="Fixture lane",
                          thesis="fixture", audience="testers", type="report", status="ready")
        store.upsert_docket(con, id=1, lane_id=1, dir="dockets/ok-docket", source_head="deadbeef",
                            graph_hash="cafefeed", freshness="stale",
                            verified_at="2026-10-07T00:00:00Z")
        store.open_rework(con, docket_id=1, reason="source moved",
                          required_work="re-copy material and re-verify C2",
                          opened_at="2026-10-08T09:30:00.000Z")
    finally:
        con.close()


def build_graph(path: Path) -> None:
    graph = {
        "directed": True,
        "nodes": [
            {"id": "node_a", "source_file": "src/a.ts", "type": "code", "community": 1},
            {"id": "node_b", "source_file": "src/b.ts", "type": "code", "community": 1},
            {"id": "node_c", "source_file": "docs/c.md", "type": "doc", "community": 2},
        ],
        "links": [
            {"source": "node_a", "target": "node_b", "relation": "imports"},
            {"source": "node_b", "target": "node_c", "relation": "documents"},
        ],
    }
    path.write_text(json.dumps(graph, indent=1, sort_keys=True), encoding="utf-8")


def _write_tree(ROOT: "Path | str" = ROOT) -> int:
    """Write the whole fixture tree under ``ROOT``.

    The parameter shadows the module-level default on purpose: the body below
    is unchanged and reusable, so ``build(dest_dir)`` can write the identical
    tree anywhere (e.g. a pytest ``tmp_path``).
    """
    ROOT = Path(ROOT)
    if ROOT.exists():
        for child in list(ROOT.iterdir()):
            if child.name == "build.py":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    ROOT.mkdir(parents=True, exist_ok=True)

    build_store(ROOT / "state.sqlite")

    build_journal(
        ROOT / "journal" / "fixture-run.jsonl",
        [
            (1, "2026-10-08T10:00:00.000Z", "run_start",
             {"target": "/tmp/target", "queries": ["fixture-query"], "budget_tokens": 200000,
              "max_model_calls": 18, "nodes": 3, "edges": 2}),
            (2, "2026-10-08T10:00:01.000Z", "query_run",
             {"intent": "fixture", "query": "fixture-query", "question": "does the fixture work?"}),
            (3, "2026-10-08T10:00:02.000Z", "candidate_accepted",
             {"query": "fixture-query", "title": "fixture primitive", "cand_kind": "novel_primitive",
              "confidence": "high", "refs": ["src/a.ts#L1-L2"], "failed": 0}),
            (4, "2026-10-08T10:00:03.000Z", "candidate_rejected",
             {"query": "fixture-query", "title": "fixture ghost", "cand_kind": "negative_result",
              "reason": "all-refs-invalid", "refs": ["graph:ghost"], "failed": 2}),
            (5, "2026-10-08T10:00:04.000Z", "query_unmatched",
             {"query": "fixture-unmatched", "reason": "no-refs-matched"}),
            (6, "2026-10-08T10:00:30.000Z", "run_end",
             {"status": "done", "accepted": 1, "rejected": 1, "deduped": 0, "model_calls": 1,
              "reasoning_tokens": 0, "queries_run": 1, "queries_unmatched": 1,
              "resumed": 0, "partial": False, "wall_s": 30.0}),
        ],
    )
    build_journal(
        ROOT / "journal" / "sparse-run.jsonl",
        [
            (1, "2026-10-08T10:05:00.000Z", "run_start", {"target": "/tmp/target"}),
            (2, "2026-10-08T10:05:01.000Z", "query_run", {"query": "sparse-query", "intent": "sparse"}),
        ],
    )

    write_docket(ROOT / "dockets" / "ok-docket", "fixture-lane")
    write_manifest_text(ROOT / "dockets" / "broken-docket", "{ this is not valid JSON ")
    write_docket(ROOT / "ok-docket", "decoy-lane")  # escape target, outside dockets/
    (ROOT / "dockets-empty").mkdir(parents=True, exist_ok=True)
    build_graph(ROOT / "graph-mini.json")
    return 0


def build(dest_dir: Path | str) -> Path:
    """Build the entire fixture tree under ``dest_dir`` and return that path.

    Self-contained and idempotent: it resolves the workspace ``resextract``
    package relative to this file and writes only under ``dest_dir``, so a test
    can build the fixture on demand (into a pytest ``tmp_path``) rather than
    depending on a pre-generated ``state.sqlite`` on disk.

    This is the guard behind the dashboard suite's reproducibility: the
    committed ``state.sqlite`` was a generated binary, and
    ``tests/fixtures/dashboard-store/dockets/`` is matched by ``.gitignore``'s
    ``dockets/`` rule, so a fresh checkout has neither guaranteed.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    _write_tree(dest)
    return dest


def main() -> int:
    build(ROOT)
    print(f"fixture store built at {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
