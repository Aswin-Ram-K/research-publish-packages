#!/usr/bin/env python3
"""Freeze the control-set digests for the typed-context pilot.

Offline: reads files, runs two read-only git queries against the read-only Duval
target (``--no-optional-locks``), and writes ``PINS.json`` beside this file.
Every path is relative to the worktree root; ``main_checkout`` entries are read
from the primary checkout, never written.

Re-run it to prove nothing in the control set moved.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

WT = Path(__file__).resolve().parents[5]
MAIN = Path("/home/zer0null/research extractor")
DUVAL = Path("/home/zer0null/Duval")

# (path, why it is pinned)
CONTROL = [
    ("docs/PLAN.md", "spec of record"),
    ("handoff from consonance/EXPERIMENTS.md", "E1/E2 pre-registration skeletons and falsifiers"),
    ("handoff from consonance/INTERFACE_CONTRACT.md", "call/run/fixture record contract"),
    ("handoff from consonance/DO_NOT_REDO.md", "ten paid-for traps; constraint list"),
    ("AGENTS.md", "workspace rules (unit protocol, Duval read-only, no auto-ask)"),
    ("experiments/context-cache/cells/STATE-CLIFF/plan.md", "sweep design as approved"),
    ("experiments/context-cache/cells/STATE-CLIFF/sweep.py", "sweep executor (dry-run source)"),
    ("experiments/context-cache/cells/STATE-CLIFF/run_sweep.py", "sweep orchestrator as executed"),
    ("experiments/context-cache/cells/STATE-CLIFF/run_sweep.log", "rung-by-rung execution log"),
    ("experiments/context-cache/cells/STATE-CLIFF/sweep_summary.json", "ad-hoc summary; residency columns void"),
    ("experiments/context-cache/cells/STATE-CLIFF/residency_bounds.py", "corrected derivation"),
    ("experiments/context-cache/cells/STATE-CLIFF/residency-bounds.json", "corrected derivation output"),
    ("experiments/context-cache/cells/STATE-CLIFF/RESIDENCY-BOUNDS.md", "corrected record"),
    ("orchestration/handoffs/M4-EVICT.json", "restored original handoff"),
    ("experiments/context-cache/cells/STATE-CLIFF/provenance/M4-EVICT.overwritten-by-STATE-CLIFF-16.json",
     "bytes the sweep wrote over M4-EVICT"),
    ("experiments/context-cache/cells/M4/rows.jsonl", "M4 evidence rows (digest is quoted by the handoff)"),
    ("experiments/context-cache/cells/M4/analysis.json", "M4 analysis"),
    ("src/resextract/context/nodes.py", "renderer fingerprint input: node addressing"),
    ("src/resextract/context/render.py", "renderer fingerprint input: chain -> messages"),
    ("src/resextract/context/budget.py", "compaction policies (APPEND_NOTE etc.)"),
    ("src/resextract/context/meter.py", "normalise_cache (null->zero behaviour)"),
    ("src/resextract/context/salt.py", "prefix salt"),
    ("src/resextract/pointers.py", "pointer expansion used by recoverable references"),
    ("experiments/context-cache/client.py", "live client used by earlier cells"),
    ("experiments/context-cache/runner.py", "cell runner"),
    ("experiments/context-cache/cells/HL-PILOT/notes/server-info-2026-11-04-occamy.json", "production readback"),
    ("experiments/context-cache/cells/HL-PILOT/notes/server-info-2026-11-04-qwen9b.json", "second endpoint (404 body)"),
    ("experiments/context-cache/cells/HL-PILOT/notes/container-inspect-2026-11-04.json", "production container spec"),
    ("state/config/occamy-restore-baseline.json", "six restore keys (compact copy the sweep gated on)"),
]
MAIN_ONLY = [
    ("experiments/ptr-engine/measure/REQUEST-LEDGER.json", "request budget book (main checkout only)"),
    ("state/config/occamy-restore-baseline.json", "full production readback; six keys match the compact copy"),
    ("docs/STATE.md", "main checkout state page"),
    ("AGENTS.md", "main checkout workspace rules"),
    ("measure/research/tool-channel-sglang.json", "research-note shape example"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(root: Path, rel: str, why: str) -> dict:
    p = root / rel
    if not p.exists():
        return {"path": str(p), "exists": False, "why": why}
    st = p.stat()
    return {
        "path": str(p),
        "exists": True,
        "why": why,
        "bytes": st.st_size,
        "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
        "sha256": sha256(p),
    }


def duval_snapshot() -> dict:
    status = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(DUVAL), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    head = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(DUVAL), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    listing = subprocess.run(
        ["find", str(DUVAL), "-type", "f", "-printf", "%T@ %p\n"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = sorted(listing.stdout.splitlines())
    newest = lines[-5:]
    return {
        "method": "git --no-optional-locks status/rev-parse + find -printf mtime sweep",
        "porcelain_lines": len([x for x in status.stdout.splitlines() if x.strip()]),
        "head": head.stdout.strip(),
        "file_count": len(lines),
        "mtime_manifest_sha256": hashlib.sha256(
            "\n".join(lines).encode("utf-8")
        ).hexdigest(),
        "newest_paths": newest,
        "note": (
            "external sessions write inside .worktrees/ continuously; this "
            "signature is expected to move without any action by this pilot. "
            "It is a baseline, not an immutability claim."
        ),
    }


def main() -> int:
    out = {
        "schema": "typed-context-pilot.pins/1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "worktree": str(WT),
        "main_checkout": str(MAIN),
        "git": {
            "worktree_branch": subprocess.run(
                ["git", "-C", str(WT), "branch", "--show-current"],
                capture_output=True, text=True, check=False).stdout.strip(),
            "worktree_head": subprocess.run(
                ["git", "-C", str(WT), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=False).stdout.strip(),
        },
        "control": [entry(WT, rel, why) for rel, why in CONTROL],
        "main_checkout_files": [entry(MAIN, rel, why) for rel, why in MAIN_ONLY],
        "fixtures_pending": "LR-01..LR-06 pinned in step 2 (fixtures.json)",
        "duval": duval_snapshot(),
    }
    missing = [e["path"] for e in out["control"] if not e["exists"]]
    out["missing"] = missing
    path = Path(__file__).resolve().parent / "PINS.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=False) + "\n")
    print(f"wrote {path} ({len(out['control'])} control entries, {len(missing)} missing)")
    for e in out["control"]:
        if e["exists"]:
            print(f"  {e['sha256'][:16]}  {e['bytes']:>9}  {e['path']}")
    print(f"  duval porcelain_lines={out['duval']['porcelain_lines']} "
          f"head={out['duval']['head'][:12]} files={out['duval']['file_count']}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
