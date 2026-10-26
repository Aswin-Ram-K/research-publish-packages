"""Pins that matter must be re-derived, not merely recorded.

Written by unit INTEGRITY-R1. RED→GREEN proof: `state/logs/INTEGRITY-R1-redgreen.txt`.

The defect this guards (found 2026-10-23): `papers/context-cache/verify_package.py` returns
PASS and `recompute.py all` returns PASS while a pinned Round-1 row file is truncated, because
neither re-hashes a file against the digest recorded for it. C63's expected values are
aggregates over the 1,136 of 2,780 rows its filters select, so dropping the source file's last
line changes nothing it reads. A digest nobody recomputes is a pin in name only.

`tests/test_paper_attribution_guard.py` guards a SENTENCE; this guards the BYTES.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "papers" / "context-cache" / "RUN.json"
CLAIMS = ROOT / "papers" / "context-cache" / "CLAIMS.md"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run():
    import json

    return json.loads(RUN.read_text())


def test_cell_digest_pins_recompute():
    """Every cell in cell_digests.rows carries a path AND a digest, and both hold on disk."""
    cd = _run()["cell_digests"]
    assert cd["rows"], "cell_digests.rows is empty"
    for r in cd["rows"]:
        for key in ("cell", "rows_file", "rows_sha256", "rows_count"):
            assert r.get(key) not in (None, ""), f"cell {r.get('cell')!r} pin lacks {key!r}"
        p = ROOT / r["rows_file"]
        assert p.is_file(), f"{r['cell']}: pinned file is missing: {r['rows_file']}"
        assert _sha(p) == r["rows_sha256"], f"{r['cell']}: sha256 drifted from its pin"
        assert len(p.read_bytes().splitlines()) == r["rows_count"], f"{r['cell']}: row count drifted"


def test_no_cell_is_pinned_live():
    """An 'unpinned_live' cell is a file whose digest is being asserted while it still grows —
    that is unverifiable by construction, so the record must carry none."""
    assert _run()["cell_digests"]["unpinned_live"] == []


def test_claims_source_table_recomputes():
    row = re.compile(
        r"^\| ([A-Za-z0-9-]+) \| `(experiments/[^`]+)` \| ([0-9,]+) \| ([0-9,]+) \| `([0-9a-f]{64})` \|$",
        re.M,
    )
    rows = row.findall(CLAIMS.read_text())
    assert rows, "CLAIMS.md source-rows table parsed to zero rows"
    for abbr, path, nbytes, nrows, sha in rows:
        p = ROOT / path
        assert p.is_file(), f"{abbr}: missing {path}"
        b = p.read_bytes()
        assert len(b) == int(nbytes.replace(",", "")), f"{abbr}: byte count drifted"
        assert len(b.splitlines()) == int(nrows.replace(",", "")), f"{abbr}: row count drifted"
        assert hashlib.sha256(b).hexdigest() == sha, f"{abbr}: sha256 drifted from the claim's source pin"


def test_verifier_handoff_and_recompute_scripts_are_pinned_to_disk():
    v = _run()["verification"]
    handoff = ROOT / v["verifier_handoff_file"]
    assert handoff.is_file()
    assert _sha(handoff).startswith(v["verifier_handoff_sha256_prefix"])
    sr = v["synthesis_recompute"]
    assert _sha(ROOT / sr["script_file"]) == sr["script_sha256"]


# --- the regression that motivated the guard -----------------------------------------

def test_recompute_alone_cannot_see_a_truncated_cell(tmp_path):
    """Documents the limitation so a later reader does not assume verify_package.py covers it.

    One row is dropped from a volatile COPY of the file (the source is never written); the
    recorded pin then no longer matches while the aggregate the record quotes still does,
    which is exactly why test_cell_digest_pins_recompute has to exist.
    """
    import json

    r = next(x for x in _run()["cell_digests"]["rows"] if x["cell"] == "MOE-VLLM")
    src = ROOT / r["rows_file"]
    original = src.read_bytes()
    lines = original.splitlines(keepends=True)
    truncated = b"".join(lines[:-1])
    assert hashlib.sha256(truncated).hexdigest() != r["rows_sha256"]
    assert _sha(ROOT / r["rows_file"]) == r["rows_sha256"], "the source file must be untouched by this test"
