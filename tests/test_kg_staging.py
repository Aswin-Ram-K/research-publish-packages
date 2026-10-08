"""Offline tests for :mod:`resextract.kg.staging` — corpus, provenance, merge.

Everything runs against ``tests/fixtures/staging-repo/``: two ``.md`` docs, a
``.txt``, a ``.py``, a 260-row nested ``.jsonl`` (more rows than the normaliser's
200-record sample cap), a well-formed ``.xml`` carrying an **internal-entity**
payload, a **malformed** ``.xml``, a 200 KB ``.md``, a gitignored ``ignored/``
tree, and a ``.bmp`` with no normaliser.  No network, no LLM, no writes outside
the test's ``tmp_path``.

Red→green guards
================
Two guards protect the two behaviours this unit exists to provide: the honesty
gate on the LLM half, and provenance honesty on the staging half.  Each was
reverted through an explicit seam in the module and re-run by the harness at
``state/logs/U1.5_redgreen/test_redgreen.py``; the failures below are that
harness's verbatim pytest output (``2 failed``).

**Guard 1 — endpoint down ⇒ nothing is executed.** Seam:
``staging._endpoint_executable`` (reverted to ``return True``). The guard asserts
``_run_command`` was never called, so the pass cannot launch against a dead
endpoint::

    ________________ test_g1_reverted_endpoint_down_still_executes _________________
    ...
        monkeypatch.setattr(staging, "_endpoint_executable", lambda code: True)
        monkeypatch.setattr(staging, "_http_probe", lambda url, timeout=10.0: 0)
        sem_out = tmp_path / "semantic"
        launched: list[list[str]] = []
    ...
        # GUARD (same assertion as the main suite's blocked-endpoint test)
    >       assert launched == [], "endpoint down must not launch the LLM pass"
    E       AssertionError: endpoint down must not launch the LLM pass
    E       assert [['stdbuf', '...corpus', ...]] == []
    E         Left contains one more item: ['stdbuf', '-oL', '-eL', '/home/zer0null/reserach extarctor/.venv/bin/graphify', 'extract', '/tmp/pytest-of-zer0null/pytest-0/test_g1_reverted_endpoint_down0/corpus', ...]
    E         Use -v to get more diff

    state/logs/U1.5_redgreen/test_redgreen.py:52: AssertionError

**Guard 2 — provenance round-trips to the real repo path.** Seam:
``staging._repo_relative`` (reverted to ``Path(path).name``, dropping the
directory). The guard asserts ``resolve_provenance`` returns
``data/results.jsonl``; reverted it returns ``results.jsonl``, a path that does
not exist at the repo root::

    _________________ test_g2_reverted_provenance_drops_directory __________________
    ...
        monkeypatch.setattr(staging, "_repo_relative", lambda p, r: Path(p).name)
    ...
        # GUARD (same assertion as the main suite's provenance round-trip test)
    >       assert staging.resolve_provenance(entry["staged_path"], corpus) == "data/results.jsonl"
    E       AssertionError: assert 'results.jsonl' == 'data/results.jsonl'
    E         
    E         - data/results.jsonl
    E         ? -----
    E         + results.jsonl

    state/logs/U1.5_redgreen/test_redgreen.py:64: AssertionError
    ============================== 2 failed in 0.04s ===============================
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from resextract.kg import staging
from resextract.kg.staging import (
    build_staging_corpus,
    combined_graph_report,
    merge_with_code_graph,
    normalize_xml,
    resolve_provenance,
    semantic_ingest,
    staging_summary,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "staging-repo"


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _manifest(corpus) -> dict:
    return json.loads(Path(corpus.manifest_path).read_text(encoding="utf-8"))


def _entries(corpus) -> list[dict]:
    return _manifest(corpus)["files"]


def _staged(corpus, rel: str) -> dict:
    return next(
        e
        for e in _entries(corpus)
        if e["original_path"] == rel and e["kind"] in ("doc_copy", "normalized")
    )


def _skipped(corpus, rel: str) -> dict:
    return next(
        e for e in _entries(corpus) if e["original_path"] == rel and e["kind"] == "skipped"
    )


# --------------------------------------------------------------------------- #
# 1. docs copied byte-for-byte, with correct original_path
# --------------------------------------------------------------------------- #
def test_docs_copied_byte_for_byte_and_recorded(tmp_path: Path) -> None:
    corpus = build_staging_corpus(FIXTURE, tmp_path / "corpus")
    for rel in ("docs/readme.md", "docs/guide.md", "notes.txt"):
        entry = _staged(corpus, rel)
        assert entry["kind"] == "doc_copy"
        staged = Path(corpus.out_dir) / entry["staged_path"]
        assert staged.exists(), staged
        assert staged.read_bytes() == (FIXTURE / rel).read_bytes()   # byte-for-byte
        assert _sha(staged) == _sha(FIXTURE / rel)                   # sha256 equal
        assert entry["sha256"] == _sha(staged)
        assert entry["bytes_in"] == entry["bytes_out"] == (FIXTURE / rel).stat().st_size
        assert entry["sampled"] is False
        assert entry["original_path"] == rel
    # a code file graphify already sees is recorded, never silently absent
    assert _skipped(corpus, "mod.py")["note"] == "covered-by-graphify"
    # a binary with no normaliser is recorded too
    assert _skipped(corpus, "assets/logo.bmp")["note"] == "unsupported-no-normalizer"


# --------------------------------------------------------------------------- #
# 2. jsonl + xml normalised; manifest round-trips
# --------------------------------------------------------------------------- #
def test_jsonl_and_xml_normalized_and_provenance_roundtrip(tmp_path: Path) -> None:
    corpus = build_staging_corpus(FIXTURE, tmp_path / "corpus")
    jl = _staged(corpus, "data/results.jsonl")
    xl = _staged(corpus, "data/schema.xml")

    assert jl["kind"] == "normalized" and jl["bytes_in"] > 0 and jl["bytes_out"] > 0
    assert jl["sampled"] is True                     # 260 rows > 200-record sample cap
    assert Path(corpus.out_dir, jl["staged_path"]).read_text(encoding="utf-8").strip()

    assert xl["kind"] == "normalized" and xl["bytes_out"] > 0
    assert Path(corpus.out_dir, xl["staged_path"]).read_text(encoding="utf-8").strip()

    for rel, entry in (("data/results.jsonl", jl), ("data/schema.xml", xl)):
        assert resolve_provenance(entry["staged_path"], corpus) == rel
        assert resolve_provenance(Path(corpus.out_dir) / entry["staged_path"], corpus) == rel
        assert resolve_provenance(entry["staged_path"], corpus.manifest_path) == rel
    assert resolve_provenance("does/not/exist.md", corpus) is None


# --------------------------------------------------------------------------- #
# 3. oversized + gitignored are recorded as skipped, with reasons
# --------------------------------------------------------------------------- #
def test_oversized_and_gitignored_are_recorded_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(staging, "MAX_SINGLE_FILE_BYTES", 4096)
    corpus = build_staging_corpus(FIXTURE, tmp_path / "corpus")
    big = _skipped(corpus, "big/huge.md")
    assert big["note"].startswith("oversized")
    assert big["staged_path"] == ""

    ignored = [
        e
        for e in _entries(corpus)
        if e["kind"] == "skipped"
        and (e["original_path"] == "ignored" or e["original_path"].startswith("ignored/"))
    ]
    assert ignored, "the gitignored tree must leave a trace"
    assert all("ignored" in e["note"] for e in ignored)
    assert not any(e["original_path"].startswith("ignored/") and e["kind"] != "skipped" for e in _entries(corpus))


# --------------------------------------------------------------------------- #
# 4. every cap is recorded in notes and stops staging deterministically
# --------------------------------------------------------------------------- #
def test_max_files_cap_recorded(tmp_path: Path) -> None:
    corpus = build_staging_corpus(FIXTURE, tmp_path / "corpus", max_files=2)
    assert corpus.counts["doc_copy"] + corpus.counts["normalized"] == 2
    assert any("max_files" in n for n in corpus.notes)
    assert staging_summary(corpus)["caps_hit"] == ["max_files"]


def test_max_total_bytes_cap_recorded(tmp_path: Path) -> None:
    corpus = build_staging_corpus(FIXTURE, tmp_path / "corpus", max_total_bytes=1)
    assert corpus.counts["doc_copy"] == 0
    assert any("max_total_bytes" in n for n in corpus.notes)
    assert _skipped(corpus, "notes.txt")["note"] == "over-total-bytes"


def test_max_normalize_files_cap_recorded(tmp_path: Path) -> None:
    corpus = build_staging_corpus(FIXTURE, tmp_path / "corpus", max_normalize_files=1)
    assert corpus.counts["normalized"] == 1
    assert any("max_normalize_files" in n for n in corpus.notes)
    over = [e for e in _entries(corpus) if e["note"] == "over-normalize-files"]
    assert over, "beyond-cap normalisables must be recorded, not dropped"
    # docs are unaffected by the normalise cap
    assert corpus.counts["doc_copy"] >= 3


# --------------------------------------------------------------------------- #
# 5. XML: no entity expansion, no crash on malformed input
# --------------------------------------------------------------------------- #
def test_xml_does_not_expand_entities(tmp_path: Path) -> None:
    nf = normalize_xml(FIXTURE / "data/schema.xml", tmp_path / "x")
    assert nf.kind == "xml" and nf.output is not None
    text = Path(nf.output).read_text(encoding="utf-8")
    assert "EXPANDED_SECRET_VALUE" not in text, "internal entity must never be expanded"
    assert "xxe" in text, "the literal entity reference should be shown, not resolved"
    assert any("entity" in n.lower() for n in nf.notes)


def test_xml_malformed_does_not_crash(tmp_path: Path) -> None:
    nf = normalize_xml(FIXTURE / "data/broken.xml", tmp_path / "x")
    assert nf.kind == "xml" and nf.output is not None and Path(nf.output).exists()
    assert any("malformed" in n for n in nf.notes)
    # and it does not abort the whole corpus
    corpus = build_staging_corpus(FIXTURE, tmp_path / "corpus")
    assert corpus.counts["normalized"] >= 3


# --------------------------------------------------------------------------- #
# 6. semantic ingest — the honesty gate
# --------------------------------------------------------------------------- #
def _fixture_corpus(tmp_path: Path):
    return build_staging_corpus(FIXTURE, tmp_path / "corpus")


def test_semantic_ingest_blocked_when_probe_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _fixture_corpus(tmp_path)
    sem_out = tmp_path / "semantic"
    launched: list[list[str]] = []

    monkeypatch.setattr(staging, "_http_probe", lambda url, timeout=10.0: 0)

    def _forbidden(*args, **kwargs):
        launched.append(list(args[0]) if args else [])
        raise AssertionError("the runner must not be called when the endpoint is down")

    monkeypatch.setattr(staging, "_run_command", _forbidden)

    result = semantic_ingest(corpus, sem_out)
    assert result.status == "blocked_endpoint_down"
    assert result.http_code == 0
    for token in ("stdbuf", "-oL", "-eL", "--token-budget 1500", "--max-concurrency 1",
                  "--backend openai", "occamy-1.0"):
        assert token in result.command, token
    assert launched == [], "endpoint down must launch no subprocess"
    assert not (sem_out / "graphify-out" / "graph.json").exists(), "no graph may be produced"


def test_semantic_ingest_ok_with_mocked_probe_and_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _fixture_corpus(tmp_path)
    sem_out = tmp_path / "semantic"

    monkeypatch.setattr(staging, "_http_probe", lambda url, timeout=10.0: 200)
    seen_env: dict = {}

    def fake_run(argv, env, timeout_s):
        seen_env.update(env or {})
        graph = sem_out / "graphify-out" / "graph.json"
        graph.parent.mkdir(parents=True, exist_ok=True)
        graph.write_text(
            json.dumps(
                {
                    "directed": True,
                    "nodes": [
                        {"id": "a", "label": "A", "file_type": "document"},
                        {"id": "b", "label": "B", "file_type": "code", "source_location": "L1"},
                        {"id": "c", "label": "C", "file_type": "concept"},
                    ],
                    "links": [{"source": "a", "target": "b"}],
                }
            ),
            encoding="utf-8",
        )
        return staging._RunOutcome(0, "done", "", 0.25)

    monkeypatch.setattr(staging, "_run_command", fake_run)
    result = semantic_ingest(corpus, sem_out)
    assert result.status == "ok"
    assert (result.nodes, result.edges) == (3, 1)
    assert result.semantic_nodes == 2          # document + concept, not the code node
    assert result.exit_code == 0 and result.http_code == 200
    assert seen_env["OPENAI_BASE_URL"].endswith("/v1")
    assert seen_env["OPENAI_MODEL"] == "occamy-1.0"
    assert "OPENAI_API_KEY" in seen_env


def test_semantic_ingest_dry_run_launches_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _fixture_corpus(tmp_path)

    def _forbidden(*args, **kwargs):
        raise AssertionError("dry_run must not execute anything")

    monkeypatch.setattr(staging, "_http_probe", _forbidden)
    monkeypatch.setattr(staging, "_run_command", _forbidden)

    result = semantic_ingest(corpus, tmp_path / "semantic", dry_run=True)
    assert result.status == "dry_run"
    for token in ("stdbuf", "-oL", "-eL", "--token-budget 1500", "--max-concurrency 1"):
        assert token in result.command, token


# --------------------------------------------------------------------------- #
# 7. merge — no LLM, proven on fixture graphs
# --------------------------------------------------------------------------- #
def _write_graph(path: Path, ids: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "directed": True,
                "nodes": [
                    {"id": i, "label": i.upper(), "file_type": "code", "source_location": "L1"}
                    for i in ids
                ],
                "links": [],
            }
        ),
        encoding="utf-8",
    )


def test_merge_with_code_graph_on_fixtures(tmp_path: Path) -> None:
    g1 = tmp_path / "g1.json"
    g2 = tmp_path / "g2.json"
    _write_graph(g1, ["a", "b", "c"])
    _write_graph(g2, ["x", "y"])
    sha1, sha2 = _sha(g1), _sha(g2)

    # a real merge (graphify merge-graphs needs no LLM)
    result = merge_with_code_graph(g1, g2, tmp_path / "combined")
    assert result.exit_code == 0 and result.ok
    assert result.nodes >= 3, result.as_dict()      # >= the larger input
    assert Path(result.graph_path).exists()
    assert result.code_sha256 == sha1 and result.semantic_sha256 == sha2
    assert _sha(g1) == sha1 and _sha(g2) == sha2    # inputs untouched

    # and the dry run returns the argv without writing anything
    dry = merge_with_code_graph(g1, g2, tmp_path / "combined-dry", dry_run=True)
    assert "merge-graphs" in dry.command and "stdbuf" not in dry.command
    assert not (tmp_path / "combined-dry" / "graph.json").exists()

    report = combined_graph_report(result.graph_path)
    assert report["nodes"] == result.nodes and "top_dirs" in report


# --------------------------------------------------------------------------- #
# 8. determinism + summary
# --------------------------------------------------------------------------- #
def test_staging_twice_is_byte_identical(tmp_path: Path) -> None:
    out = tmp_path / "corpus"
    first = build_staging_corpus(FIXTURE, out)
    bytes_first = Path(first.manifest_path).read_bytes()
    second = build_staging_corpus(FIXTURE, out)
    bytes_second = Path(second.manifest_path).read_bytes()
    assert bytes_first == bytes_second

    summary = staging_summary(second)
    assert summary["counts"]["doc_copy"] >= 3
    assert summary["counts"]["normalized"] >= 3       # jsonl + 2 xml
    assert ".bmp" in summary["uncovered_types"]
    assert summary["total_bytes"] == second.total_bytes
