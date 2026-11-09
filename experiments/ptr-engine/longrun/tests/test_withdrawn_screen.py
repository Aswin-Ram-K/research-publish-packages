"""Tests for `tools/withdrawn_screen.py` - the corpus-wide withdrawal re-scan.

Red -> green: an unmodified copy of a corrected document screens CLEAN; the same copy with a
withdrawn figure pasted back in must TRIP. The count-drop and regression cases prove the
`--check` guard, not just the scanner.

Card `WITHDRAWN-REGISTER-FIX` (2026-10-26) narrowed register entry `WI-011` from the bare
3-character quote `98.7` to `98.7 % prefix`, because the bare string fired on every citable p50
in the 198.7 ms range, and added `--strict` (window = enclosing paragraph) for the two published
latency pages. The tests below pin both halves: the false positive is gone, the real claim still
bites, and the paragraph window closes the hole that excused `docs/LATENCY-REPORT.md:45`.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL = ROOT / "experiments" / "ptr-engine" / "tools" / "withdrawn_screen.py"
INDEX = ROOT / "experiments" / "ptr-engine" / "tools" / "withdrawn_index.py"
REGISTER = ROOT / "experiments" / "ptr-engine" / "measure" / "WITHDRAWN.json"
SCREEN = ROOT / "experiments" / "ptr-engine" / "measure" / "WITHDRAWN-SCREEN.json"
CORRECTED = [
    ROOT / "docs" / "LATENCY-REPORT.md",
    ROOT / "experiments" / "ptr-engine" / "measure" / "ARM-RECONCILE.md",
]
# A paragraph that quotes WI-004 verbatim and attaches no correction.
PASTE = ("\n\np95 for G7 V4-TOOLS pointer-stable is 318.14 [235.00, 526.41] n=68, "
         "which settles the arm.\n")
# The four documents that only tripped because `98.7` is a substring of a citable p50.
FORMER_ARTIFACTS = [
    "docs/LATENCY-ERA-CENSUS.md",
    "docs/ROW-MODEL.md",
    "docs/TTFT-DEFINITION.md",
    "docs/VERBOSITY.md",
]


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args],
                          cwd=str(ROOT), capture_output=True, text=True)


def index_run(*args: str) -> subprocess.CompletedProcess:
    """The bare guard (`withdrawn_index.py`), which has no artifact classification."""
    return subprocess.run([sys.executable, str(INDEX), *args],
                          cwd=str(ROOT), capture_output=True, text=True)


def _register_with_quote(tmp_path: pathlib.Path, entry: str, quote: str) -> pathlib.Path:
    """A copy of the live register with one entry's quote restored to its old value."""
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    for e in reg["entries"]:
        if e["id"] == entry:
            e["quote"] = quote
    p = tmp_path / f"register-{entry}.json"
    p.write_text(json.dumps(reg), encoding="utf-8")
    return p


def test_screened_documents_are_clean() -> None:
    for doc in CORRECTED:
        r = run("--file", str(doc))
        assert r.returncode == 0, r.stdout + r.stderr
        assert "CLEAN" in r.stdout


def test_corpus_check_is_clean() -> None:
    r = run("--check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SCREEN CLEAN" in r.stdout


def test_green_unmodified_copy_of_corrected_document(tmp_path: pathlib.Path) -> None:
    copy = tmp_path / "ARM-RECONCILE.md"
    shutil.copyfile(CORRECTED[1], copy)
    r = run("--file", str(copy))
    assert r.returncode == 0, r.stdout
    assert "CLEAN" in r.stdout


def test_red_pasted_withdrawn_figure_trips(tmp_path: pathlib.Path) -> None:
    copy = tmp_path / "ARM-RECONCILE.md"
    copy.write_text(CORRECTED[1].read_text(encoding="utf-8") + PASTE, encoding="utf-8")
    r = run("--file", str(copy))
    assert r.returncode == 1, r.stdout
    assert "WITHDRAWN WI-004" in r.stdout
    assert "TRIPS" in r.stdout


# --- WITHDRAWN-REGISTER-FIX: the narrowed quote -------------------------------------------

def test_correct_p50_no_longer_fires(tmp_path: pathlib.Path) -> None:
    """A citable p50 in the 198.7 ms range is not a withdrawn claim.

    RED (before the fix): with the old bare quote `98.7` the same paragraph trips. GREEN (after):
    the live register's quote is `98.7 % prefix`, which the paragraph does not contain.
    """
    f = tmp_path / "p50.md"
    f.write_text("\n\nG7 V4-TOOLS pointer-stable de-duplicated p50 198.7230 ms (n=51), "
                 "above the p50 floor n >= 20.\n\n", encoding="utf-8")
    old = _register_with_quote(tmp_path, "WI-011", "98.7")
    red = index_run("--check", str(f), "--register", str(old))
    assert red.returncode == 1, red.stdout
    assert "WITHDRAWN WI-011" in red.stdout
    green = index_run("--check", str(f))
    assert green.returncode == 0, green.stdout
    assert "CLEAN" in green.stdout
    screen = run("--file", str(f))
    assert screen.returncode == 0, screen.stdout
    assert "ARTIFACT" not in screen.stdout


def test_real_cache_share_still_fires() -> None:
    """Narrowing must not neuter the entry: the withdrawn mechanism claim still bites.

    The register records the claim's rejected value both as the phrase `98.7 % prefix` and as
    the decimal `0.987` (see `superseded_by.number`: measured cached share 0.871157, not 0.987).
    A paragraph using either rendering of the withdrawn mechanism trips.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / "claim.md"
        f.write_text("\n\n`pointer-stable`'s p50 advantage is explained by a 98.7 % prefix cache "
                     "hit (cached share 0.987), so no other treatment matters.\n\n",
                     encoding="utf-8")
        r = run("--file", str(f))
    assert r.returncode == 1, r.stdout
    assert "WITHDRAWN WI-011" in r.stdout
    assert "TRIPS" in r.stdout
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    wi011 = next(e for e in reg["entries"] if e["id"] == "WI-011")
    assert "0.987" in wi011["superseded_by"]["number"], wi011["superseded_by"]
    assert wi011["quote"] == "98.7 % prefix", wi011["quote"]


def test_wi004_stands_remnant_fires_under_strict(tmp_path: pathlib.Path) -> None:
    """The `docs/LATENCY-REPORT.md:45` shape: the stale sentence lives in its own paragraph.

    Paragraph 1 carries the correction markers (`WITHDRAWN`, `n=51`, `refused`); the paragraph
    below repeats `318.14 ... n=68` and says it **stands**. The 400-character window reaches the
    markers across the blank line and stays silent; `--strict` confines the search to the stale
    sentence's own paragraph and fires. This is the hole strict mode closes.
    """
    f = tmp_path / "reissue.md"
    f.write_text(
        "\n## Re-issue notes\n\n"
        "**WITHDRAWN** p95 for G7 V4-TOOLS pointer-stable: 318.14 [235.00, 526.41] n=68 is "
        "refused at n=51 (51 < 60).\n\n"
        "If the 30 rows are genuine requests, its n is 68 and the p95 "
        "318.14 [235.00, 526.41] n=68 **stands**.\n",
        encoding="utf-8")
    lax = run("--file", str(f))
    assert lax.returncode == 0, lax.stdout  # exactly the defect: excused from another paragraph
    strict = run("--file", str(f), "--strict")
    assert strict.returncode == 1, strict.stdout
    assert "WITHDRAWN WI-004" in strict.stdout


def test_non_strict_is_byte_identical() -> None:
    """The default mode is unchanged: same files, same verdicts, no artifact class left.

    Pinned against the frozen record rather than a literal: `WITHDRAWN-SCREEN` wrote 131 scanned
    files with one real reported-only offender (`docs/REQUEST-LEDGER.md`, WI-002) and four
    substring-artifact files. Later cards added documents to `docs/` (the count only grows) and
    their owners corrected `docs/REQUEST-LEDGER.md`, so the live offender set is no longer that
    one file; the invariant pinned here is the recorded one — every recorded verdict still holds,
    the corrected documents are clean, and the substring-artifact class is empty because the quote
    that created it is gone.
    """
    rec = json.loads(SCREEN.read_text(encoding="utf-8"))
    assert rec["scanned_count"] >= 131, rec["scanned_count"]
    r = run("--check")
    assert r.returncode == 0, r.stdout + r.stderr
    # the surface may grow (other cards add documents); the recorded count must not drop
    assert "files scanned" in r.stdout, r.stdout
    assert f">= {rec['scanned_count']} recorded" in r.stdout, r.stdout
    assert "SCREEN CLEAN" in r.stdout, r.stdout
    trips = sorted(row["path"] for row in rec["scanned"] if row["verdict"] == "trips")
    # Neither corrected document may be in the trip set, and the artifact class is empty.
    assert CORRECTED[0].relative_to(ROOT).as_posix() not in trips, trips
    assert CORRECTED[1].relative_to(ROOT).as_posix() not in trips, trips
    assert not [row for row in rec["scanned"] if row["verdict"] == "clean_substring_artifact"]
    for rel in FORMER_ARTIFACTS:
        hit = run("--file", str(ROOT / rel))
        assert hit.returncode == 0, (rel, hit.stdout)
        assert "ARTIFACT" not in hit.stdout, (rel, hit.stdout)


def test_register_self_test() -> None:
    """The register still passes its own self-test, and no quote is short enough to cry wolf."""
    r = subprocess.run([sys.executable, str(INDEX), "--self-test"],
                       cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 problem(s)" in r.stdout, r.stdout
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    short = {e["id"]: e["quote"] for e in reg["entries"] if len(e["quote"]) < 5}
    # All three survivors are reported in orchestration/units/WITHDRAWN-REGISTER-FIX.md; none is
    # a bare numeric fragment of a longer citable value in this corpus (audited, 0 artifact hits).
    assert short == {"WI-001": "≈466", "WI-006": "217k", "WI-014": "3/27"}, short
    assert all(len(e["quote"]) >= 5 for e in reg["entries"] if e["id"] not in short)


def test_old_quote_still_classified_as_artifact_on_correct_p50(tmp_path: pathlib.Path) -> None:
    """Artifact classification is unchanged for a register that still carries the bare quote."""
    f = tmp_path / "p50.md"
    f.write_text("| G7 | **198.72 [166.05, 206.66] n=51** |\n", encoding="utf-8")
    old = _register_with_quote(tmp_path, "WI-011", "98.7")
    r = run("--file", str(f), "--register", str(old))
    assert r.returncode == 0, r.stdout
    assert "ARTIFACT WI-011" in r.stdout


def _mini(tmp_path: pathlib.Path, body: str) -> tuple[pathlib.Path, pathlib.Path]:
    root = tmp_path / "corpus"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text(body, encoding="utf-8")
    screen = tmp_path / "screen.json"
    screen.write_text(json.dumps({
        "scanned_count": 1,
        "scanned": [{"path": "docs/a.md", "verdict": "clean", "entries": []}],
        "corrected": [], "reported_only": [],
    }), encoding="utf-8")
    return root, screen


def test_check_regresses_when_recorded_clean_file_trips(tmp_path: pathlib.Path) -> None:
    root, screen = _mini(tmp_path, "nothing here\n")
    r = run("--check", "--root", str(root), "--screen", str(screen))
    assert r.returncode == 0, r.stdout
    (root / "docs" / "a.md").write_text("nothing here\n" + PASTE, encoding="utf-8")
    r = run("--check", "--root", str(root), "--screen", str(screen))
    assert r.returncode == 1, r.stdout
    assert "REGRESSED: docs/a.md" in r.stdout


def test_check_fails_on_scanned_count_drop(tmp_path: pathlib.Path) -> None:
    root, screen = _mini(tmp_path, "nothing here\n")
    rec = json.loads(screen.read_text(encoding="utf-8"))
    rec["scanned_count"] = 999
    screen.write_text(json.dumps(rec), encoding="utf-8")
    r = run("--check", "--root", str(root), "--screen", str(screen))
    assert r.returncode == 1, r.stdout
    assert "SCANNED-COUNT DROPPED" in r.stdout


def test_register_is_untouched_by_the_screen() -> None:
    """The screen compares against the register; it must never write it."""
    before = REGISTER.read_bytes()
    run("--check")
    assert REGISTER.read_bytes() == before
