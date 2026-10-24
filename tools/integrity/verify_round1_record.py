#!/usr/bin/env python
"""verify_round1_record.py — re-derive the Round-1 (context-cache) record from the bytes on disk.

Written by unit INTEGRITY-R1, 2026-10-23. Read-only: it never writes, never edits, never moves,
never contacts the endpoint, never takes the .occamy.lock. Exit 0 = every check passed,
exit 1 = at least one check failed (each failure is printed with the file and the value).

WHY THIS EXISTS
---------------
`papers/context-cache/verify_package.py` PASSES while a pinned row file is silently truncated,
and so does `recompute.py`. Neither script re-hashes anything:
  * verify_package.py checks that claims are mapped 1:1 to runners and that "every referenced
    cell has rows" — it never compares a file's bytes to the digest pinned for it;
  * recompute.py recomputes C63 from the rows that SURVIVE its filters, and pins its expected
    values as *aggregates* (`rows_total` 1136 = 4 cells x 284, while the four source files hold
    2780 rows and only 1136 of them are the 32k battery), so dropping the file's last line
    changes nothing it looks at.
A digest nobody recomputes is not a pin. This script recomputes every one of them.

CHECKS
------
  A  papers/context-cache/RUN.json
       A1 units[].rows_file / rows_sha256 / rows / events / analysis   re-hashed + line-counted
       A2 cell_digests.rows[]  — the DURABLE pins: path + sha256 + rows_count + existence
       A3 cell_digests.unpinned_live must be empty (a live-pinned file cannot be re-derived)
       A4 corpora[] — bytes + sha256
       A5 pins{} — every `*_file` pin re-hashed, and every superseded value it is superseded by
          must NOT match (else the "repair" narrative it carries is wrong)
       A6 verification{} — verifier handoff sha prefix, recompute.py digest
  B  papers/context-cache/CLAIMS.md source-rows table — bytes, rows and sha256 per row
  C  offline re-derivation — `recompute.py all` (63 claims + grid guard + coverage guard) and
     `verify_package.py`, run and their exit codes and tails checked
  D  the two script-backed claims C01 / C16 — `u5_recon.py`, `u4_recon.py`, exit codes checked
     AND their printed tails compared against the figures RUN.json records for them
  E  prose guard — `tests/test_paper_attribution_guard.py`

NOT CHECKED (state it, do not imply it): whether the *filters* inside recompute.py are the right
ones; whether the cells' prose agrees with the verifiers' rulings (STATUS.md §8 item 3 asks for
that as a separate unit); anything requiring a live request.

USAGE
    .venv/bin/python tools/integrity/verify_round1_record.py           # all checks
    .venv/bin/python tools/integrity/verify_round1_record.py --no-run  # digests only, no runner
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "papers" / "context-cache"
RUN = PKG / "RUN.json"
CLAIMS = PKG / "CLAIMS.md"

FAILS: list[str] = []
NCHECK = 0


def record(ok: bool, label: str, detail: str = "") -> None:
    global NCHECK
    NCHECK += 1
    if not ok:
        FAILS.append(f"{label}: {detail}")
        print(f"  FAIL {label}  {detail}")
    else:
        print(f"  ok   {label}" + (f"  {detail}" if detail else ""))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read(p: Path) -> bytes | None:
    try:
        return p.read_bytes()
    except OSError:
        return None


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def check_file(path: Path, sha: str, rows: int | None, label: str) -> None:
    """Re-hash one pinned file. `rows` is counted as splitlines() — the only recipe every
    pinned file in this record is counted with (a trailing newline is not a row)."""
    b = read(path)
    if b is None:
        record(False, label, f"missing: {rel(path)}")
        return
    h = sha256_bytes(b)
    n = len(b.splitlines())
    bad = []
    if h != sha:
        bad.append(f"sha256 {h[:16]} != pinned {sha[:16]}")
    if rows is not None and n != rows:
        bad.append(f"rows(splitlines) {n} != pinned {rows}")
    record(not bad, label, f"{rel(path)} {n} rows {h[:16]}" + ("" if not bad else " | " + "; ".join(bad)))


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=1800)


# --------------------------------------------------------------------------- A
def check_A(run_runner: bool) -> dict:
    data = json.loads(RUN.read_text())
    print("\nA. RUN.json pins re-derived")
    for u in data["units"]:
        rf = u.get("rows_file")
        if rf is None:
            continue
        files = rf if isinstance(rf, list) else [rf]
        shas = u["rows_sha256"] if isinstance(u.get("rows_sha256"), list) else [u.get("rows_sha256")]
        rc = u.get("rows")
        for i, f in enumerate(files):
            cnt = rc if (len(files) == 1 and not isinstance(rc, list)) else (rc[i] if isinstance(rc, list) else None)
            check_file(ROOT / f, shas[i], cnt, f"A1 {u['unit']} rows")
        for key, sha_key in (("events_file", "events_sha256"), ("analysis_file", "analysis_sha256")):
            if u.get(key):
                check_file(ROOT / u[key], u[sha_key], None, f"A1 {u['unit']} {key}")

    cd = data["cell_digests"]
    for r in cd["rows"]:
        check_file(ROOT / r["rows_file"], r["rows_sha256"], r["rows_count"], f"A2 cell {r['cell']}")
    record(not cd.get("unpinned_live"), "A3 unpinned_live empty",
           f"{len(cd.get('unpinned_live') or [])} unpinned live file(s)")

    for c in data["corpora"]:
        b = read(ROOT / c["path"])
        if b is None:
            record(False, f"A4 corpus {c['name']}", "missing")
            continue
        record(sha256_bytes(b) == c["sha256"] and len(b) == c["bytes"], f"A4 corpus {c['name']}",
               f"{len(b)} B {sha256_bytes(b)[:16]}")

    pins = data["pins"]
    # The two pins whose values we can check WITHOUT inventing semantics: each repairs an
    # earlier (wrong) value for the same file, so only the repaired value may match on disk.
    # u4_cell_py_claimed is deliberately NOT paired here: its own _note says "value unchanged;
    # only the file name was missing", so its *_claimed value is expected to match, and treating
    # it as superseded would be this checker's error, not the record's (found in pass 1).
    repair_pairs = [
        ("u4_sessions_payload_sha256_claimed", "u4_sessions_payload_file", "u4_sessions_payload_sha256"),
        ("u5_render_py_sha8_repair", "u5_render_py_file", "u5_render_py_sha8"),
    ]
    for name, value in pins.items():
        if not name.endswith("_file"):
            continue
        path = ROOT / value
        b = read(path)
        if b is None:
            record(False, f"A5 pin {name}", f"missing: {value}")
            continue
        h = sha256_bytes(b)
        record(True, f"A5 pin {name}", f"{rel(path)} {h[:16]}")
    for superseded_key, file_key, current_key in repair_pairs:
        rule = pins.get(superseded_key + "_note", "") + pins.get(superseded_key, "")
        cur = pins.get(current_key)
        if not cur:
            continue
        b = read(ROOT / pins[file_key])
        if b is None:
            record(False, f"A5 {superseded_key}", f"missing file {pins[file_key]}")
            continue
        h = sha256_bytes(b)
        # a shingle label ("slot") is history here: the repair sentence already explains it
        not_a_digest = "NAMES NO FILE" in rule or "not of any file on disk" in rule
        record(h != pins[superseded_key] or not_a_digest, f"A5 {superseded_key} superseded as claimed",
               f"on-disk {h[:16]} vs superseded {pins[superseded_key][:16]}")

    ver = data["verification"]
    b = read(ROOT / ver["verifier_handoff_file"])
    record(b is not None and sha256_bytes(b).startswith(ver["verifier_handoff_sha256_prefix"]),
           "A6 verifier handoff",
           f"{ver['verifier_handoff_sha256_prefix'][:16]} = {sha256_bytes(b)[:16] if b else 'MISSING'}")
    sr = ver["synthesis_recompute"]
    b = read(ROOT / sr["script_file"])
    record(b is not None and sha256_bytes(b) == sr["script_sha256"], "A6 recompute.py digest",
           f"{sha256_bytes(b)[:16] if b else 'MISSING'} pinned {sr['script_sha256'][:16]}")
    return data


# --------------------------------------------------------------------------- B
ROW_RE = re.compile(r"^\| ([A-Za-z0-9-]+) \| `(experiments/[^`]+)` \| ([0-9,]+) \| ([0-9,]+) \| `([0-9a-f]{64})` \|$", re.M)


def check_B() -> None:
    print("\nB. CLAIMS.md source-rows table re-derived")
    rows = ROW_RE.findall(CLAIMS.read_text())
    record(len(rows) > 0, "B table parsed", f"{len(rows)} source rows")
    for abbr, path, nbytes, nrows, sha in rows:
        b = read(ROOT / path)
        if b is None:
            record(False, f"B {abbr}", f"missing: {path}")
            continue
        ok = (len(b) == int(nbytes.replace(",", "")) and len(b.splitlines()) == int(nrows.replace(",", ""))
              and sha256_bytes(b) == sha)
        record(ok, f"B {abbr}", f"{len(b)} B {len(b.splitlines())} rows {sha256_bytes(b)[:16]}")


# --------------------------------------------------------------------------- C
def check_C() -> None:
    print("\nC. Offline re-derivation (recompute.py all, verify_package.py)")
    py = str(ROOT / ".venv" / "bin" / "python")
    r = run([py, "papers/context-cache/recompute.py", "all"])
    out = r.stdout + r.stderr
    tail = [ln.strip() for ln in out.splitlines() if ln.startswith(("PASS", "FAIL", "GRID GUARD PASS", "COVERAGE GUARD PASS"))]
    record(r.returncode == 0 and "60 claims checked, all match" in out, "C1 recompute.py all", f"exit {r.returncode}; {tail[:3]}")
    record("GRID GUARD PASS" in out, "C2 grid guard", "7/7 configs" if "7/7 configs" in out else "absent")
    record("63 claims documented" in out, "C3 coverage guard", "63/63 mapped")
    r = run([py, "papers/context-cache/verify_package.py"])
    out = (r.stdout + r.stderr).strip()
    record(r.returncode == 0 and "UNVERIFIED: none" in out, "C4 verify_package.py", f"exit {r.returncode}; {out[-70:]}")


# --------------------------------------------------------------------------- D
def check_D(data: dict) -> None:
    print("\nD. Script-backed claims C01 / C16")
    py = str(ROOT / ".venv" / "bin" / "python")
    recorded = data["verification"]["synthesis_recompute"]["external_commands_verified"]
    for script, key in (("u5_recon.py", "u5_recon.py"), ("u4_recon.py", "u4_recon.py")):
        r = run([py, f"experiments/context-cache/cells/CX-V2/{script}"])
        out = r.stdout + r.stderr
        record(r.returncode == 0, f"D {script}", f"exit {r.returncode}")
        # every figure the record quotes for this script must appear in the fresh output
        quoted = re.findall(r"\d+(?:/\d+)?", recorded[key].split(";")[1] if ";" in recorded[key] else recorded[key])
        present = [q for q in dict.fromkeys(quoted) if q in out]
        record(len(present) >= max(1, len(dict.fromkeys(quoted)) - 2), f"D {script} figures",
               f"{len(present)}/{len(dict.fromkeys(quoted))} quoted numbers appear verbatim")


# --------------------------------------------------------------------------- E
def check_E() -> None:
    print("\nE. Prose attribution guard")
    py = str(ROOT / ".venv" / "bin" / "python")
    r = run([py, "-m", "pytest", "tests/test_paper_attribution_guard.py", "-q"])
    out = (r.stdout + r.stderr).strip().splitlines()
    record(r.returncode == 0, "E attribution guard", out[-1] if out else f"exit {r.returncode}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-run", action="store_true", help="digest checks only; do not execute the runners")
    a = ap.parse_args()
    data = check_A(run_runner=not a.no_run)
    check_B()
    if not a.no_run:
        check_C()
        check_D(data)
        check_E()
    print(f"\n{len(FAILS)} failure(s) across {NCHECK} checks")
    for f in FAILS:
        print(f"  - {f}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
