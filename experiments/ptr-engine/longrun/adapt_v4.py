#!/usr/bin/env python3
"""adapt_v4.py — adapt the V4 slice-widened authored fixture
(``tasks-v4/LR-0N.v4.json``, schema ``consonance.fixture/1``) to the RUNTIME shape
``run_longrun.py`` loads (``consonance.longrun-fixture/1``), writing
``tasks-v4/runtime-v4/LR-0N.v4.json``.

Relationship to adapt_v3.py (NOT edited): this adapter IMPORTS it and reuses its
whole adaptation pass (``adapt_v3.adapt_v2``), which in turn imports
``adapt_fixture.py`` for pinned-source loading, digest verification, pointer slicing
and the bytes-per-token measurement.  It therefore differs from v3 in exactly four
places:

  1. the source pointers come from the v4 authored fixture (widened slices), so the
     materialised bodies carry the values the checkpoints ask for — see
     ``REACHABILITY-V4.md`` for the before/after measurements;
  2. ``fixture_version`` is carried from the v4 authored fixture
     (``v4-slice-widened``), which is the recorded fixture-version change;
  3. output lands in ``tasks-v4/runtime-v4/LR-0N.v4.json`` (the v3 runtime tree is
     never written) and ``adaptation.adapter`` names this file;
  4. ``adaptation`` also records the v3→v4 pointer delta, copied from the authored
     ``slice_repair`` block, so a reader can see which slice moved and why.

Nothing else is reconstructed: digests, checks, budgets, turns and the answer
marker are carried through the v3 path verbatim.  A source whose file digest does
not match the authored ``sha256`` is still a HARD FAILURE (raised by adapt_fixture).

Deterministic: ``json.dumps(..., indent=2, sort_keys=True, ensure_ascii=False) + "\n"``
— two runs produce identical bytes, no timestamps, no absolute paths.

Zero network access.

Usage:
    python3 experiments/ptr-engine/longrun/adapt_v4.py --all
    python3 experiments/ptr-engine/longrun/adapt_v4.py --fixture .../LR-01.v4.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import adapt_v3 as v3  # noqa: E402  (sys.path set above)
import adapt_fixture as base  # noqa: E402

DEFAULT_FIXTURE_DIR = os.path.join("experiments", "ptr-engine", "longrun", "tasks-v4")
DEFAULT_OUT_DIR = os.path.join("experiments", "ptr-engine", "longrun", "tasks-v4", "runtime-v4")
ADAPTER_PATH = "experiments/ptr-engine/longrun/adapt_v4.py"


def runtime_path(out_dir: str, task_id: str) -> str:
    return os.path.join(out_dir, f"{task_id}.v4.json")


def write_runtime(runtime: dict, out_dir: str) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    path = runtime_path(out_dir, runtime["task_id"])
    data = json.dumps(runtime, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)
    return path, base.sha256_text(data)


def adapt_v4(path: str) -> dict:
    """Run the v3 adaptation, then stamp v4 provenance and the slice delta."""
    # The authored v4 fixture only states a fixture_version when it really is v4;
    # refuse to silently re-emit a v3 fixture under a .v4 name.
    with open(path, encoding="utf-8") as fh:
        authored = json.load(fh)
    runtime = v3.adapt_v2(path)
    if authored.get("fixture_version") != "v4-slice-widened":
        raise v3.AdaptError(
            f"{path}: fixture_version is {authored.get('fixture_version')!r}, expected "
            "'v4-slice-widened' — this adapter only rewrites the v4 tier")
    runtime["adaptation"]["adapter"] = ADAPTER_PATH
    runtime["adaptation"]["imports"] = (
        "experiments/ptr-engine/longrun/adapt_v3.py -> adapt_fixture.py")
    runtime["adaptation"]["slice_repair"] = authored.get("slice_repair", {})
    runtime["adaptation"]["fixture_version"] = runtime.get("fixture_version")
    return runtime


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true", help="adapt every authored v4 fixture")
    ap.add_argument("--fixture", action="append", default=None, help="authored v4 fixture")
    ap.add_argument("--fixture-dir", default=DEFAULT_FIXTURE_DIR)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    if args.all:
        names = sorted(n for n in os.listdir(args.fixture_dir)
                       if re.match(r"^LR-\d+.*\.json$", n))
        paths = [os.path.join(args.fixture_dir, n) for n in names]
    elif args.fixture:
        paths = list(args.fixture)
    else:
        ap.error("give --all or --fixture PATH")
        return 2

    if not paths:
        print(f"no authored fixtures found in {args.fixture_dir}", file=sys.stderr)
        return 2

    rc = 0
    for path in paths:
        try:
            runtime = adapt_v4(path)
        except v3.AdaptError as exc:
            print(f"ADAPT FAILED {path}: {exc}", file=sys.stderr)
            rc = 1
            continue
        out, sha = write_runtime(runtime, args.out_dir)
        a = runtime["adaptation"]
        print(f"{out}  sha256:{sha}")
        print(f"  task_id={runtime['task_id']} N={runtime['N']} items={len(runtime['items'])} "
              f"bytes_per_token={runtime['bytes_per_token']} "
              f"checks_structured={a['checks_structured_count']} "
              f"checkpoints={a['checkpoint_count']} version={runtime['fixture_version']}")
        for it in runtime["items"]:
            print(f"  item {it['id']:24s} {it['source']['pointer']:12s} "
                  f"{it['body_bytes']:5d} B sha256:{it['body_sha256'][7:23]}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
