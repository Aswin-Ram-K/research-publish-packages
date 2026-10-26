#!/usr/bin/env python3
"""Red->green proof for ``coverage_ids`` / ``coverage_guard`` in recompute.py.

The defect: with no claim id parsing out of CLAIMS.md, the gap check called ``max()`` on an
empty sequence and the guard died with ``ValueError: max() iterable argument is empty`` --
a raw traceback instead of a verdict line, and every check after it silently skipped.

Fixtures are written to a temp directory; CLAIMS.md itself is never touched, and no claim is
registered.  Run from the repo root:

    .venv/bin/python papers/context-cache/coverage_guard_selftest.py
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recompute as R  # noqa: E402

# Every anchor spelling CLAIMS.md has been written with, plus the plain form.
FIXTURE = """\
# fixture

**Source rows and digests**

| Abbrev | Path | Bytes | Rows | sha256 |
|---|---|---:|---:|---|
| U2-rows | `rows.jsonl` | 1 | 1 | `ab` |

## A

| # | Claim | Value | Source | One recompute command |
|---|---|---|---|---|
| <a id="C01"></a> C01 spaced label | x | y | z | w |
| <a id="C02"></a>C02 tight label | x | y | z | w |
| <a id="C03"></a>C03a sub-claim | x | y | z | w |
| <a id="C04">tolerated tag</a>C04 odd close | x | y | z | w |
| C05 plain label | x | y | z | w |
  | <a id="C06"></a> C06 indented row | x | y | z | w |
"""

failures = 0


def expect(label: str, got, want) -> None:
    global failures
    ok = got == want
    failures += 0 if ok else 1
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got={got!r} want={want!r}")


def census_verdict(tmp: Path, text: str) -> tuple[int, str]:
    path = tmp / "CLAIMS.md"
    path.write_text(text, encoding="utf-8")
    original = R.CLAIMS_MD_PATH
    R.CLAIMS_MD_PATH = path
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            rc = R.coverage_guard()
    except Exception as exc:  # the very thing the fix removes
        return 99, f"{type(exc).__name__}: {exc}"
    finally:
        R.CLAIMS_MD_PATH = original
    return rc, out.getvalue()


with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)

    print("--- parse ---")
    path = tmp / "CLAIMS.md"
    path.write_text(FIXTURE, encoding="utf-8")
    saved = R.CLAIMS_MD_PATH
    R.CLAIMS_MD_PATH = path
    try:
        expect("census", R.coverage_ids(), ["C01", "C02", "C03", "C04", "C05", "C06"])
    finally:
        R.CLAIMS_MD_PATH = saved

    print("--- GREEN: anchored rows are seen, so the fixture id-contiguity check reports ok ---")
    rc, out = census_verdict(tmp, FIXTURE)
    expect("contiguity verdict", "claim ids are contiguous C01..C06" in out, True)
    expect("no crash", rc != 99, True)

    print("--- RED: empty census must FAIL, not raise ---")
    for name, text in (("empty file", ""), ("header table only", "| # | Claim |\n|---|---|\n")):
        rc, out = census_verdict(tmp, text)
        expect(f"{name}: raised", rc == 99, False)
        expect(f"{name}: exit", rc, 1)
        expect(f"{name}: names the empty census", "the census is empty" in out, True)

    print("--- RED: a lost id below the maximum still fails ---")
    gapped = FIXTURE.replace('| <a id="C03"></a>C03a sub-claim', '| <a id="C09"></a>C09 far row')
    rc, out = census_verdict(tmp, gapped)
    expect("gap named", "below the maximum C09: C03, C07, C08" in out, True)

print("SELFTEST", "PASS" if not failures else f"FAIL ({failures})")
sys.exit(0 if not failures else 1)
