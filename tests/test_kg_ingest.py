"""Offline tests for :mod:`resextract.kg.ingest` — coverage audit + normalisers.

Everything runs against ``tests/fixtures/ingest-repo/``: a multi-cell ``.ipynb``
(markdown + code + stream output + error output + base64 PNG outputs), an empty
notebook, a **malformed** notebook, a mixed scalar/nested ``.jsonl``, a 400-row
``big.jsonl`` (for the bounds check), a ``.csv``, a ``.tsv``, a ``.tex``, a
``.bmp``, a ``.md``, a ``.py``, an extensionless ``LICENSE``, and a symlink
pointing outside the fixture root. No network, no LLM, no writes outside the
test's temp dir.

Red→green guards
================
Two guards protect the two behaviours this unit exists to provide. Each was
reverted and re-run to prove it fails. The reverts go through the two explicit
seams in the module (``ingest._record_unsupported`` and
``ingest._render_code_cell``) and the *same* guard assertions are re-run by the
harness at ``state/logs/U1.4_redgreen/test_redgreen.py``; the failures below are
its verbatim pytest output (``2 failed``).

**Guard 1 — an unclassifiable extension is reported, never silently dropped.**
``test_guard_unsupported_extension_is_reported`` / harness
``test_g1_reverted_unsupported_is_silently_dropped``. Reverted:
``_record_unsupported`` -> no-op (graphify's pre-#1692 behaviour, where an
unclassified file "left no trace at all")::

    >           assert report.unsupported.get(ext, 0) >= 1, f"{ext} vanished from the report: {report.unsupported}"
    E           AssertionError: .ipynb vanished from the report: {}
    E           assert 0 >= 1
    E            +  where 0 = {}.get('.ipynb', 0)
    E            +    where {} = CoverageReport(target_root='.../ingest-repo', supported={'.md': 1, '.py': ...
    tests/test_kg_ingest.py:73: AssertionError
    1 failed

**Guard 2 — notebook code cells *and* their outputs are preserved.**
``test_guard_notebook_code_cell_and_output_preservation`` / harness
``test_g2_reverted_notebook_keeps_only_prose``. Reverted:
``_render_code_cell`` -> ``[]``, so the render keeps only the prose —::

    >       assert "```python" in md, "code cell input lost: no ```python fence in the markdown"
    E       AssertionError: code cell input lost: no ```python fence in the markdown
    E       assert '```python' in '<!-- normalized from experiment.ipynb (notebook) -->\n\n# experiment.ipynb\n\ncells: 5 (markdown 1, code 4, raw 0) · ...\n\n# Experiment\n\nThis is a **markdown** cell with prose.\n'
    tests/test_kg_ingest.py:87: AssertionError
    1 failed
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from resextract.kg import ingest

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ingest-repo"


# --------------------------------------------------------------------------- #
# Shared guard bodies (imported by the red→green revert harness in state/logs)
# --------------------------------------------------------------------------- #
def _assert_guard_a(report) -> None:
    """Every unclassifiable file must appear in the report, or the gap is a secret."""
    for ext in (".ipynb", ".jsonl", ".csv", ".tsv", ".tex", ".bmp"):
        assert report.unsupported.get(ext, 0) >= 1, f"{ext} vanished from the report: {report.unsupported}"
    assert report.no_extension.get("LICENSE", 0) == 1, (
        f"extensionless LICENSE vanished: {report.no_extension}"
    )
    assert report.unsupported_files >= 9


def _assert_guard_b(fixture_root: Path, tmp: Path) -> None:
    """A notebook render must keep code inputs, outputs and figures."""
    result = ingest.normalize_notebook(fixture_root / "experiment.ipynb", tmp)
    assert result.kind == "notebook"
    assert result.output is not None and result.output.exists()
    md = result.output.read_text(encoding="utf-8")

    assert "```python" in md, "code cell input lost: no ```python fence in the markdown"
    assert 'print("hello from stream")' in md, "code cell source text lost"
    assert "This is a **markdown** cell with prose." in md, "markdown cell lost"
    assert "hello from stream" in md, "stream output text lost"
    assert "ValueError: boom" in md, "traceback text lost"

    images = sorted(tmp.glob("fig-*.png"))
    assert images, "embedded base64 PNG was not saved as a file next to the markdown"
    assert images[0].stat().st_size > 0, "saved figure is empty"
    assert f"]({images[0].name})" in md, "saved figure is not referenced by relative link"


# --------------------------------------------------------------------------- #
# coverage_audit
# --------------------------------------------------------------------------- #
def test_coverage_audit_counts_supported_vs_unsupported():
    report = ingest.coverage_audit(FIXTURE)
    # graphify really ingests these two
    assert report.supported == {".md": 1, ".py": 1}
    assert report.supported_files == 2
    # and it silently skips these nine
    assert report.unsupported == {
        ".bmp": 1, ".csv": 1, ".ipynb": 3, ".jsonl": 2, ".tex": 1, ".tsv": 1,
    }
    assert report.no_extension == {"LICENSE": 1}
    assert report.unsupported_files == 10
    assert report.unreadable == []
    assert report.symlinks_skipped == 1, "the out-of-root symlink must be recorded, not followed"
    assert report.total_files == 12


def test_coverage_audit_reports_top_gaps_and_pct():
    report = ingest.coverage_audit(FIXTURE)
    assert report.top_gaps[0] == (".ipynb", 3)
    assert (".jsonl", 2) in report.top_gaps
    assert report.top_gaps == sorted(report.top_gaps, key=lambda kv: (-kv[1], kv[0]))
    assert report.coverage_pct == pytest.approx(100.0 * 2 / 12, abs=0.01)
    assert any("ignored_predicate" in n for n in report.notes), "must state which ignore machinery was used"


@pytest.mark.parametrize("ext", [".ipynb", ".jsonl", ".csv", ".tsv", ".tex", ".bmp"])
def test_uncovered_types_are_present_not_absent(ext):
    report = ingest.coverage_audit(FIXTURE)
    assert ext in report.unsupported, f"{ext} was silently dropped from the audit"
    assert ext not in report.supported


def test_extensionless_file_is_reported_as_no_extension():
    report = ingest.coverage_audit(FIXTURE)
    assert "LICENSE" in report.no_extension
    assert "LICENSE" not in report.unsupported


def test_audit_never_raises_on_bad_roots(tmp_path):
    missing = ingest.coverage_audit(tmp_path / "nope")
    assert missing.total_files == 0 and missing.coverage_pct == 0.0 and missing.notes
    as_file = tmp_path / "a.txt"
    as_file.write_text("x")
    not_a_dir = ingest.coverage_audit(as_file)
    assert not_a_dir.total_files == 0
    assert any("not a directory" in n for n in not_a_dir.notes)


def test_audit_is_deterministic():
    a, b = ingest.coverage_audit(FIXTURE), ingest.coverage_audit(FIXTURE)
    assert a.as_dict() == b.as_dict()


# --------------------------------------------------------------------------- #
# Notebook normaliser
# --------------------------------------------------------------------------- #
def test_notebook_normalizer_preserves_markdown_code_outputs_and_images(tmp_path):
    _assert_guard_b(FIXTURE, tmp_path)


def test_notebook_header_reports_cell_and_input_counts(tmp_path):
    result = ingest.normalize_notebook(FIXTURE / "experiment.ipynb", tmp_path)
    md = result.output.read_text(encoding="utf-8")
    assert result.records == 5 and result.sampled == 5
    assert "cells: 5 (markdown 1, code 4, raw 0)" in md
    assert "code inputs: 4" in md and "outputs: 5" in md
    assert "language: python" in md
    # two display_data PNG outputs -> two files
    assert len(sorted(tmp_path.glob("fig-*.png"))) == 2
    assert "fig-001.png" in md and "fig-002.png" in md
    # execute_result text is preserved too
    assert "> 42" in md
    # the bounds that were in force are recorded in the output
    assert "<!-- bounds:" in md and "max_image_bytes" in md


def test_empty_notebook_is_handled(tmp_path):
    result = ingest.normalize_notebook(FIXTURE / "empty.ipynb", tmp_path)
    assert result.kind == "notebook" and result.records == 0
    assert "cells: 0 (markdown 0, code 0, raw 0)" in result.output.read_text(encoding="utf-8")


def test_malformed_notebook_records_parse_error_and_stays_uncovered(tmp_path):
    result = ingest.normalize_notebook(FIXTURE / "malformed.ipynb", tmp_path)  # must not raise
    assert result.kind == "ipynb-error"
    assert result.output is None
    assert any("parse error" in n for n in result.notes)
    # ...and it is still reported as uncovered material by the audit
    report = ingest.coverage_audit(FIXTURE)
    assert report.unsupported[".ipynb"] == 3


def test_non_json_notebook_records_parse_error(tmp_path):
    bad = tmp_path / "not-json.ipynb"
    bad.write_text("this is not json at all", encoding="utf-8")
    result = ingest.normalize_notebook(bad, tmp_path / "out")
    assert result.kind == "ipynb-error" and result.output is None and result.notes


# --------------------------------------------------------------------------- #
# JSONL normaliser
# --------------------------------------------------------------------------- #
def test_jsonl_normalizer_reports_total_vs_sampled_and_names_nested(tmp_path):
    result = ingest.normalize_jsonl(FIXTURE / "records.jsonl", tmp_path)
    md = result.output.read_text(encoding="utf-8")
    assert result.kind == "jsonl"
    assert result.records == 4, "total record count"
    assert result.sampled == 4, "records parsed for the schema"
    assert "records: 4 · sampled for schema: 4" in md
    # scalar columns became a table; nested fields are named, not flattened
    assert "| `id` | `score` | `tag` |" in md
    assert "| 1 | 0.5 | alpha |" in md
    assert "**Nested fields not flattened (2):**" in md
    assert "`metrics`" in md and "`nested_list`" in md
    assert any("metrics" in n for n in result.notes)


def test_jsonl_names_unrendered_rows_and_records_caps(tmp_path):
    result = ingest.normalize_jsonl(FIXTURE / "big.jsonl", tmp_path)
    md = result.output.read_text(encoding="utf-8")
    assert result.records == 400 and result.sampled == 200, "schema sampling is capped at 200"
    assert "_Table shows 50 of 400 records; 200 parsed for the schema._" in md
    assert "sample_size=200" in md and "max_scan_records=100000" in md


def test_jsonl_bounds_stop_reading_the_whole_file(tmp_path, monkeypatch):
    """A file bigger than the scan cap is partially read, and says so."""
    monkeypatch.setattr(ingest, "JSONL_MAX_SCAN_RECORDS", 100)
    src = FIXTURE / "big.jsonl"
    result = ingest.normalize_jsonl(src, tmp_path)
    md = result.output.read_text(encoding="utf-8")
    assert result.records == 100, "counting must stop at max_scan"
    assert "records: 100+" in md
    assert "scan stopped at max_scan=100" in " ".join(result.notes)
    m = re.search(r"read (\d+) of (\d+) bytes", " ".join(result.notes))
    assert m, f"no bounded-read accounting in notes: {result.notes}"
    read, total = int(m.group(1)), int(m.group(2))
    assert read < total, f"read {read}/{total} bytes — the whole file was consumed"


# --------------------------------------------------------------------------- #
# CSV normaliser
# --------------------------------------------------------------------------- #
def test_csv_normalizer_quotes_delimiter_and_header(tmp_path):
    result = ingest.normalize_csv(FIXTURE / "data.csv", tmp_path)
    md = result.output.read_text(encoding="utf-8")
    assert result.kind == "csv" and result.records == 3
    assert 'delimiter: ","' in md, "the delimiter must be quoted in the output"
    assert 'header: ["id", "name", "score"]' in md, "column names must be reported"
    assert "| id | name | score |" in md
    assert "| 1 | alpha | 0.5 |" in md
    assert result.sampled == 3


def test_tsv_normalizer_uses_tab(tmp_path):
    result = ingest.normalize_csv(FIXTURE / "data.tsv", tmp_path)
    md = result.output.read_text(encoding="utf-8")
    assert result.kind == "tsv" and result.records == 2
    assert 'delimiter: "\\t"' in md
    assert 'header: ["id", "name", "score"]' in md


def test_csv_bounds_are_stated(tmp_path):
    result = ingest.normalize_csv(FIXTURE / "data.csv", tmp_path, table_rows=1)
    md = result.output.read_text(encoding="utf-8")
    assert "_Table shows 1 of 3 data rows._" in md
    assert "table_rows=1" in md


# --------------------------------------------------------------------------- #
# Dispatcher, gap closing, determinism
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name,kind",
    [
        ("experiment.ipynb", "notebook"),
        ("records.jsonl", "jsonl"),
        ("data.csv", "csv"),
        ("data.tsv", "tsv"),
    ],
)
def test_normalize_dispatches_by_extension(tmp_path, name, kind):
    result = ingest.normalize(FIXTURE / name, tmp_path)
    assert result.kind == kind and result.output is not None and result.output.exists()
    assert result.bytes_out > 0


def test_normalize_reports_unroutable_types(tmp_path):
    result = ingest.normalize(FIXTURE / "figure.bmp", tmp_path)
    assert result.kind == "unsupported" and result.output is None
    assert any("no normaliser" in n for n in result.notes)


def test_ingest_uncovered_normalizes_the_top_gaps(tmp_path):
    report = ingest.coverage_audit(FIXTURE)
    results = ingest.ingest_uncovered(report, FIXTURE, tmp_path, max_files=4)
    assert results, "the top gaps must actually be normalised, not just measured"
    kinds = {r.kind for r in results}
    assert "notebook" in kinds, "the biggest gap (.ipynb) must be closed first"
    assert all(r.output is not None and r.output.exists() for r in results)
    # highest-count gap first
    assert Path(results[0].source).suffix == ".ipynb"


@pytest.mark.parametrize("name", ["experiment.ipynb", "records.jsonl", "data.csv", "data.tsv"])
def test_normalizing_twice_is_byte_identical(tmp_path, name):
    a = ingest.normalize(FIXTURE / name, tmp_path / "a")
    b = ingest.normalize(FIXTURE / name, tmp_path / "b")
    assert a.output.read_bytes() == b.output.read_bytes()
    assert a.bytes_out == b.bytes_out


# --------------------------------------------------------------------------- #
# RED→GREEN guards
# --------------------------------------------------------------------------- #
def test_guard_unsupported_extension_is_reported(monkeypatch):
    """Guard 1: an unclassifiable extension is *reported*, never silently dropped.

    Reverted (``_record_unsupported`` -> no-op), this test fails with::

        AssertionError: .ipynb vanished from the report: {}
        assert 0 >= 1
    """
    report = ingest.coverage_audit(FIXTURE)
    _assert_guard_a(report)


def test_guard_notebook_code_cell_and_output_preservation(tmp_path):
    """Guard 2: notebook code inputs, outputs, tracebacks and figures survive.

    Reverted (``_render_code_cell`` -> ``[]``), this test fails with::

        AssertionError: code cell input lost: no ```python fence in the markdown
    """
    _assert_guard_b(FIXTURE, tmp_path)
