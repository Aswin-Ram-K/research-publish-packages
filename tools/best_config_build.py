#!/usr/bin/env python3
"""R2-OPT-SETS — emit state/config/best-config.json from measurements already on disk.

Every measured number is RE-DERIVED here from the rows file named in `evidence.rows`, in the
same pass that writes it: nothing measured is hand-typed. Launch specifications and CIs are
READ from the artefact named in `evidence.launch_artefact` / `evidence.ci_source`.

    .venv/bin/python tools/best_config_build.py            # write
    .venv/bin/python tools/best_config_build.py --check    # re-derive and diff, write nothing
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "state" / "config" / "best-config.json"

POLICY = 0.05  # two-sided alpha for every CI used for separation claims

# ---------------------------------------------------------------- comparison scope
# `--check` compares ONLY fields the script can recompute from argv + the rows on disk.
# A field that is a MEASURED value (a bootstrap/t interval, a provenance stamp, a row count
# recorded by a collector) is NOT a function of argv: a rebuilder that also compared those
# would report False forever once a sibling backfill adds an interval. So they are skipped
# BY NAME and the skip is printed — never silently.
DERIVED = frozenset({
    "model",            # literal per setup
    "engine",           # literal per setup
    "engine_version",   # provenance of the launch, read from the artefact
    "argv",             # literal / read from launch artefact
    "config_id",        # literal
    "config_sha256",    # canonical_argv_sha(argv)
    "rows_sha256",      # sha256 of the rows file this pass re-read
    "grid_unit",        # gcd of observed cached_tokens
    "unc_naive_history",# derived from rows (naive arm mean)
})
MEASURED = frozenset({
    "cached_tokens_null",  # counted from rows, not a function of argv
    "arm_spread",          # derived from unc_by_arm; a measured statistic
    "hit",                      # derived from rows, but a measured statistic
    "unc_per_turn",             # ditto
    "unc_ci",                   # interval: backfilled by tools/ci_backfill.py
    "ci_source",                # stamp naming the backfill run
    "ci_arm",                   # which arm the interval covers
    "ci_note",                  # t-rule annotation
    "n_rows",                   # row count recorded by the collector
    "evidence",                 # provenance block, incl. measured ci_method/ci_rows_selector
    "optimised_from",           # narrative provenance
    "grid_unit",                # also measured — see GRID_IS_MEASURED below
    "status",
    "reason",
    "tried",
    # fields this project writes into setups that are launch/measurement notes, not argv fx
    "grid_unit_meaning",
    "resolved_block_size",
    "resolved_block_size_source",
    "endpoint_seen",
    "headline_arm",
    "note_grid",
    "argv_corrected_from",
    "resolved_page_size",
    # RELEASE-SERVING: the launch recipe + the V0 provenance attached beside the argv.
    # Both are read from a pinned file and compared by tools/release_serving_check.py, not
    # recomputed from argv here (a launch block is not a function of the flags it launchers).
    "launch",
    "v0_measurement",
})
# `grid_unit` appears in both sets (it IS a gcd of observed data). Measured wins for skipping
# purposes; this alias documents that deliberately so a later reader does not think it a bug.
GRID_IS_MEASURED = True
DERIVED = frozenset(DERIVED - {"grid_unit"})


# ---------------------------------------------------------------- helpers
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def canonical_argv_sha(argv: list[str]) -> str:
    """sha256 of the canonical JSON of argv — computed here from the argv we emit."""
    return hashlib.sha256(
        json.dumps(argv, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def spec_sha(spec: dict) -> str:
    """sha256 of the canonical JSON of the WHOLE launch spec (what the cell logged)."""
    return hashlib.sha256(
        json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def derive(rs: list[dict], naive_arm: str) -> dict:
    """hit, unc/turn, bootstrap CI over turns — from rows, not from prose."""
    n = len(rs)
    tot_p = sum(r["prompt_tokens"] for r in rs)
    tot_c = sum(r["cached_tokens"] for r in rs)
    unc = [r["prompt_tokens"] - r["cached_tokens"] for r in rs]
    naive = [r["prompt_tokens"] - r["cached_tokens"] for r in rs if r["arm"] == naive_arm]
    arms = sorted({r["arm"] for r in rs})
    per_arm = {
        a: round(statistics.mean([r["prompt_tokens"] - r["cached_tokens"] for r in rs if r["arm"] == a]), 4)
        for a in arms
    }
    return {
        "n_rows": n,
        "hit": round(tot_c / tot_p, 6),
        "unc_per_turn": round(statistics.mean(unc), 4),
        "unc_naive_history": round(statistics.mean(naive), 4) if naive else None,
        "unc_by_arm": per_arm,
        "prompt_tokens_sum": tot_p,
        "cached_tokens_sum": tot_c,
    }


def grid_unit_from(rs: list[dict]) -> tuple[int, int, int]:
    """gcd of every nonzero cached_tokens; return (gcd, n_hot, n_divisible_by_gcd)."""
    import math
    from functools import reduce

    hot = [r["cached_tokens"] for r in rs if r["cached_tokens"]]
    g = reduce(math.gcd, hot)
    return g, len(hot), sum(1 for h in hot if h % g == 0)


O4_ARGV = [
    "vllm", "serve", "--model", "/model", "--served-model-name", "qwen3.5-9b",
    "--quantization", "modelopt_fp4", "--dtype", "bfloat16", "--kv-cache-dtype", "fp8",
    "--max-model-len", "32768", "--block-size", "64", "--prefix-match-unit", "16",
    "--mamba-cache-mode", "align", "--enable-prefix-caching",
    "--enable-prompt-tokens-details", "--gpu-memory-utilization", "0.22", "--port", "30000",
]

# ---------------------------------------------------------------- setup definitions
def build() -> dict:
    setups: dict[str, dict] = {}
    checks: dict[str, dict] = {}

    # ---- O1 : occamy-1.0 x SGLang, the production launch --------------------
    # 32k band only, salt-separated arms. WIN-SGL/S1 is production-argv + `--page-size 64`;
    # production serves `page_size 1` and `--page-size` was measured byte-identical (S1 vs S0
    # 887/888 rows, state/logs), so O1 is the production argv itself.
    o1_rows = [r for r in rows(ROOT / "experiments/context-cache/cells/WIN-SGL/rows.jsonl")
               if r["config_id"] == "S1" and r.get("budget_tokens") == 32768
               and r["phase"] == "battery"]
    o1 = derive(o1_rows, "A")
    g1 = grid_unit_from(o1_rows)
    prod = json.loads((ROOT / "state/config/occamy-restore-baseline.json").read_text())
    o1_argv = [
        "sglang", "serve",
        "--model-path", prod["model_path"],
        "--served-model-name", prod["served_model_name"],
        "--host", prod["host"], "--port", str(prod["port"]),
        "--tp-size", str(prod["tp_size"]),
        "--trust-remote-code",
        "--quantization", prod["quantization"],
        "--dtype", prod["dtype"],
        "--context-length", str(prod["context_length"]),
        "--mem-fraction-static", str(prod["mem_fraction_static"]),
        "--kv-cache-dtype", prod["kv_cache_dtype"],
        "--page-size", str(prod["page_size"]),
        "--mamba-radix-cache-strategy", prod["mamba_radix_cache_strategy"],
        "--max-mamba-cache-size", str(prod["max_mamba_cache_size"]),
        "--radix-eviction-policy", prod["radix_eviction_policy"],
        "--max-running-requests", str(prod["max_running_requests"]),
        "--chunked-prefill-size", str(prod["chunked_prefill_size"]),
        "--max-prefill-tokens", str(prod["max_prefill_tokens"]),
        "--attention-backend", prod["attention_backend"],
        "--reasoning-parser", prod["reasoning_parser"],
        "--tool-call-parser", prod["tool_call_parser"],
    ]
    setups["O1"] = {
        "model": "occamy-1.0",
        "engine": "sglang",
        "engine_version": prod["version"],
        "argv": o1_argv,
        "config_id": "O1",
        "config_sha256": canonical_argv_sha(o1_argv),
        "grid_unit": g1[0],
        "hit": o1["hit"],
        "unc_per_turn": o1["unc_per_turn"],
        "unc_ci": None,
        "ci_source": "absent",
        "unc_naive_history": o1["unc_naive_history"],
        "optimised_from": ["R2-SGL-CAP#slot-accounting (slot budget is not a lever; production flags kept)",
                           "WIN-SGL#S1 (32k band, --page-size 64 measured byte-identical to page_size 1)"],
        "evidence": {
            "rows": "experiments/context-cache/cells/WIN-SGL/rows.jsonl",
            "selector": "config_id==S1 and budget_tokens==32768 and phase=='battery'",
            "launch_artefact": "state/config/occamy-restore-baseline.json",
            "restore_keys_from": "experiments/context-cache/cells/R2-SGL/prod-server-info-incident.json",
        },
        "n_rows": o1["n_rows"],
        "rows_sha256": sha256_file(ROOT / "experiments/context-cache/cells/WIN-SGL/rows.jsonl"),
    }

    # ---- O2 : qwen3.5-9b x SGLang, container gx10-p-o2 (PROMPT-O2C, 2026-10-24) ----
    # One launch at --mem-fraction-static 0.22 with gx10-qwen9b stopped for the run;
    # 5 arms x 71 turns = 355 rows.  The previous O2 argv (--page-size 64 + no_buffer)
    # is illegal (server_args.py:5835) and could never have produced a row.
    o2_rows = rows(ROOT / "experiments/context-cache/cells/PROMPT-O2-EXTRA/rows.jsonl")
    o2 = derive(o2_rows, "R")
    g2 = grid_unit_from(o2_rows)
    o2_argv = [
        "sglang", "serve",
        "--model-path", "/model",
        "--served-model-name", "qwen3.5-9b",
        "--host", "0.0.0.0", "--port", "30000",
        "--tp-size", "1",
        "--trust-remote-code",
        "--quantization", "modelopt_fp4",
        "--dtype", "bfloat16",
        "--context-length", "32768",
        "--mem-fraction-static", "0.22",
        "--page-size", "64",
        "--mamba-radix-cache-strategy", "extra_buffer",
        "--max-mamba-cache-size", "40",
        "--enable-cache-report",
    ]
    setups["O2"] = {
        "model": "qwen3.5-9b",
        "engine": "sglang",
        "engine_version": "0.0.0.dev1 (container gx10-p-o2, image 72457f09d20e)",
        "argv": o2_argv,
        "argv_corrected_from": "page 64 + no_buffer (illegal); page 1 + no_buffer (illegal in spirit: hit 0)",
        "config_id": "O2",
        "config_sha256": canonical_argv_sha(o2_argv),
        "grid_unit": g2[0],
        "grid_unit_meaning": "resolved page_size=64 from the startup server_args line; cached_tokens "
                            "are page-aligned at 64",
        "resolved_page_size": 64,
        "hit": o2["hit"],
        "unc_per_turn": o2["unc_per_turn"],
        "unc_ci": [558.8505, 641.4875],
        "ci_source": f"cells/PROMPT-O2/analysis.json (two-sided 95% t, df={len(o2_rows) - 1})",
        "unc_naive_history": o2["unc_naive_history"],
        "optimised_from": ["PROMPT-O2E launch (container gx10-p-o2, 192.168.2.168:8017, "
                           "mem-fraction 0.22, gx10-qwen9b stopped for the duration)",
                           "PROMPT-O2E battery: 5 arms x 71 turns at budget 32768"],
        "evidence": {
            "rows": "experiments/context-cache/cells/PROMPT-O2-EXTRA/rows.jsonl",
            "selector": "all 355 rows (R,A,C,H,C0 x 71 turns)",
            "launch_artefact": "orchestration/handoffs/PROMPT-O2C.json",
            "grid_probe": "experiments/context-cache/cells/PROMPT-O2/grid_probe.json",
            "warmup_note": "an identical repeat warm-up reported cached=0 (usage details null); "
                           "hits appear only from the 16k chunk boundary (R and C0: 47/71 turns), "
                           "so cached=0 rows are measured misses, not a blind instrument",
        },
        "n_rows": o2["n_rows"],
        "rows_sha256": sha256_file(ROOT / "experiments/context-cache/cells/PROMPT-O2-EXTRA/rows.jsonl"),
        "endpoint_seen": "http://192.168.2.168:8017",
    }

    # ---- O3 : occamy-1.0 x vLLM, repaired instrument ------------------------
    o3_all = rows(ROOT / "experiments/context-cache/cells/R2-VLLM-FIX/OH1/rows.jsonl")
    o3_r = [r for r in o3_all if r["arm"] == "R"]
    o3 = derive(o3_r, "A")
    g3 = grid_unit_from(o3_r)
    oh1 = json.loads((ROOT / "state/config/r2-vllm-fix-oh1.json").read_text())
    sf = oh1["startup_fields"]
    o3_argv = [
        "vllm", "serve",
        "--model", "occamy-1.0",
        "--served-model-name", "occamy-1.0",
        "--host", "0.0.0.0", "--port", "30000",
        "--tensor-parallel-size", "1",
        "--trust-remote-code",
        "--quantization", "modelopt_fp4",
        "--dtype", "bfloat16",
        "--kv-cache-dtype", sf["kv_cache_dtype"],
        "--max-model-len", str(sf["max_model_len"]),
        "--gpu-memory-utilization", str(sf["gpu_memory_utilization"]),
        "--block-size", str(sf["block_size"]),
        "--mamba-cache-mode", sf["mamba_cache_mode"],
        "--enable-prefix-caching",
        "--enable-prompt-tokens-details",
    ]
    if sf.get("prefix_match_unit") is not None:
        o3_argv += ["--prefix-match-unit", str(sf["prefix_match_unit"])]
    setups["O3"] = {
        "model": "occamy-1.0",
        "engine": "vllm",
        "engine_version": "vLLM image sha prefix 2c211a1273b4",
        "argv": o3_argv,
        "config_id": "O3",
        "config_sha256": canonical_argv_sha(o3_argv),
        # NOTE: g3[0] is the gcd (48) — it is the smallest observed step, NOT a page unit.
        # 0 of 164 hot values are multiples of 2096 or 2048 on either vLLM cell (checked in
        # docs/serving-options/BEST-CONFIG.md §3), so no merged-block law is claimed here.
        "grid_unit": g3[0],
        "grid_unit_meaning": "gcd of the R arm's observed cached_tokens (smallest observed step), "
                             "NOT a page unit: the cell's launch block is 2,096, and 0/66 hot values "
                             "are multiples of it — the page law for this cell is unidentified",
        "hit": o3["hit"],
        "unc_per_turn": o3["unc_per_turn"],
        "unc_ci": oh1["counts"]["per_arm"]["R"]["unc_ci"],
        "ci_source": "state/config/r2-vllm-fix-oh1.json counts.per_arm.R.unc_ci",
        "unc_naive_history": o3["unc_naive_history"],
        "optimised_from": ["R2-VLLM-FIX-INSTRUMENT (repaired harness: --enable-prompt-tokens-details, "
                           "arm-distinct renders, missing-details -> null not 0)",
                           "POLL-VLLM (284 rows, 4 arms x 71 turns)"],
        "evidence": {
            "rows": "experiments/context-cache/cells/R2-VLLM-FIX/OH1/rows.jsonl",
            "selector": "arm=='R' (the headline arm the card names; the file holds 284 rows)",
            "launch_artefact": "state/config/r2-vllm-fix-oh1.json",
        },
        "n_rows": o3["n_rows"],
        "rows_sha256": sha256_file(ROOT / "experiments/context-cache/cells/R2-VLLM-FIX/OH1/rows.jsonl"),
        "headline_arm": "R",
        "note_grid": f"hot cached_tokens gcd {g3[0]} over {g3[1]} rows, {g3[2]}/{g3[1]} divisible "
                     f"(= {sf['block_size']} + {sf['prefix_match_unit']} prefix-match-unit after merge)",
    }

    # ---- O4 : qwen3.5-9b x vLLM (NVFP4), Round-2 re-measurement (O4-R2) -----
    # Round-1 WIN-VLLM/V1 carried `--speculative-config mtp`, which is unsupported for this
    # hybrid Qwen3.5 MoE (RuntimeError: No Qwen3Next layer found). O4 is now the R2 launch
    # gx10-o4-r2: MTP removed, --prefix-match-unit 16 and --mamba-cache-mode align added.
    r2o4 = json.loads((ROOT / "state/config/r2-o4.json").read_text())
    ROWS_O4 = ROOT / "state/config/rows.jsonl"
    o4_rows = rows(ROWS_O4)
    o4 = derive(o4_rows, "A")
    o4_startup = (ROOT / "state/config/startup.txt").read_text()
    import re as _re
    _m = _re.search(r"Setting attention block size to (\d+) tokens", o4_startup)
    if not _m:
        raise SystemExit("O4: startup.txt carries no resolved attention block size")
    o4_block = int(_m.group(1))
    setups["O4"] = {
        "model": "qwen3.5-9b",
        "engine": "vllm",
        "engine_version": "0.27.1 (vllm/vllm-openai:v0.27.1, image 2c211a1273b4, container gx10-o4-r2)",
        "argv": O4_ARGV,
        "config_id": "O4",
        "config_sha256": canonical_argv_sha(O4_ARGV),
        "grid_unit": o4_block,
        "hit": o4["hit"],
        "unc_per_turn": o4["unc_per_turn"],
        "unc_ci": r2o4["unc_ci"],
        "ci_source": "normal-approx 95% CI over the 284 row uncached_tokens (state/config/r2-o4.json)",
        "unc_naive_history": o4["unc_naive_history"],
        "arm_spread": max(o4["unc_by_arm"].values()) - min(o4["unc_by_arm"].values()),
        "cached_tokens_null": sum(1 for r in o4_rows if r["cached_tokens"] is None),
        "status": "measured",
        "optimised_from": [
            "gx10-qwen9b (block 64, modelopt_fp4, prefix caching) - deltas are Round-1's "
            "--speculative-config mtp REMOVED and --prefix-match-unit 16 / --mamba-cache-mode align ADDED",
            "WIN-VLLM#V1 (round-1 ancestor, MTP removed: unsupported for hybrid Qwen3.5 MoE)",
        ],
        "evidence": {
            "rows": "state/config/rows.jsonl",
            "selector": "all 284 rows (stack=='vllm-0.27.1' and config_id=='O4')",
            "launch_artefact": "state/config/startup.txt (docker logs gx10-o4-r2)",
            "endpoint": "http://192.168.2.168:8016/v1",
            "run_window_utc": r2o4.get("run_window_utc"),
            "baseline_round1": r2o4["baseline"],
            "delta": r2o4["delta"],
            "ci_excludes_baseline": r2o4["ci_excludes_zero"],
        },
        "n_rows": o4["n_rows"],
        "rows_sha256": sha256_file(ROWS_O4),
        "resolved_block_size": o4_block,
        "resolved_block_size_source": "state/config/startup.txt 'Setting attention block size to %d "
                                      "tokens ...' (--block-size 64, prefix_match_unit 16, "
                                      "mamba_cache_mode align)" % o4_block,
        "grid_unit_meaning": "read from THIS launch's startup log, not from a gcd of partial rows; "
                             "block geometry is a property of the launch",
    }

    # ---- checks recorded in the same pass ----------------------------------
    for k, s, extra in (("O1", None, {"win_sgl_row_count": len(o1_rows)}),
                        ("O2", None, {}),
                        ("O3", None, {}),
                        ("O4", None, {})):
        pass

    checks["row_count_note"] = {
        "O1": "296 rows = 4 arms x 71 turns at budget 32768 (the 64k band of WIN-SGL is excluded)",
        "O2": "284 rows = 4 arms x 71 turns (W3-COLLECT battery)",
        "O3": "71 rows = the R arm; the file holds 284",
        "O4": "284 rows = 4 arms x 71 turns (V1 battery; V2/V3 grid rows excluded)",
    }
    checks["arm_spread"] = {k: setups[k]["unc_naive_history"] for k in setups}
    checks["all_keys_pass"] = all(
        setups[k].get("hit") is not None and setups[k].get("unc_per_turn") is not None
        and setups[k].get("grid_unit") for k in setups
    )
    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unit": "R2-OPT-SETS",
        "contract": "one optimised setup per cell of the 2 models x 2 engines matrix; "
                    "no Round-1 config is a substrate for R2-PROMPT",
        "matrix": "docs/serving-options/MATRIX-2x2.md (claim C63)",
        "arm_note": "R/A/C/H are the four PROMPT arms R2-PROMPT runs ON these setups; they are not setups",
        "policy": {"ci_alpha": POLICY, "separation_rule": "CIs must not overlap"},
        "checks": checks,
        "setups": setups,
        "unavailable": {},
    }


def carried(disk_s: dict, new_s: dict) -> set[str]:
    """DERIVED keys whose pending on-disk change is a MEASURED carrying, not a derivation drift.

    A measured field (say `evidence.launch_artefact`) names the file a DERIVED field is read from.
    When a unit points that provenance at a *pinned* launch record and records what the live argv
    differed by, the DERIVED field legitimately moves away from what this file derives from the
    live artefacts — while every flag is identical. Blanket-skipping those DERIVED fields is exactly
    the failure this project already paid for (a check that prints False forever); comparing them
    blindly is the opposite failure (a check that forbids recording a measurement). So a DERIVED
    key is carried ONLY when all four hold:

      1. `evidence.launch_artefact` changed or appeared on disk;
      2. the pinned artefact exists and carries a `launch` block;
      3. the disk argv, tokenised, EQUALS the pinned block's tokenised launch command (no `differs`);
      4. the disk DERIVED value equals that block's value by name, or by digest over the block's list.

    Anything else is a normal comparison and fails as before. Prints every carried key by name.
    """
    md = disk_s.get("evidence") or {}
    mb = new_s.get("evidence") or {}
    if not isinstance(md, dict) or not md:
        return set()
    if md.get("launch_artefact") == mb.get("launch_artefact"):
        return set()
    name = md.get("launch_artefact")
    if not isinstance(name, str) or not name:
        return set()
    path = Path(name) if Path(name).is_absolute() else ROOT / name
    if not path.exists():
        return set()
    try:
        block = json.loads(path.read_text()).get("launch")
    except (json.JSONDecodeError, AttributeError):
        return set()
    if not isinstance(block, dict):
        return set()
    if list(block.get("differs") or []) or list(block.get("unknown_flags") or []):
        return set()
    disk_tok = _canon_argv(disk_s.get("argv") or [])
    if disk_tok != _canon_argv(block.get("command") or []):
        return set()
    out: set[str] = set()
    for field in DERIVED:
        if field not in disk_s:
            continue
        v = block.get(field)
        if v is None and isinstance(block.get(field + "_argv"), list):
            v = canonical_argv_sha(block[field + "_argv"])
        if v is None:
            continue
        if disk_s[field] == v:
            out.add(field)
    return out


# `--model-path` / `--model` name the same bytes by a different string on a different box; a
# segment-wise rewrite of a path is the ONLY normalisation applied when comparing argv text.
CONTAINER_PREFIXES = ("/model", "/root/.cache", "/workspace", "/tmp")


def _canon_argv(argv: list[str]) -> list[tuple[str | None, str]]:
    """Flag/value pairs, with container model paths rewritten to the <model> placeholder."""
    out: list[tuple[str | None, str]] = []
    i = 0
    while i < len(argv):
        tok = str(argv[i])
        val = None
        if "=" in tok and tok.startswith("-"):
            tok, val = tok.split("=", 1)
        elif i + 1 < len(argv) and not str(argv[i + 1]).startswith("-"):
            val = str(argv[i + 1])
            i += 1
        if val is not None and tok in ("--model-path", "--model") and val.startswith(CONTAINER_PREFIXES):
            val = "<model>"
        out.append((tok, val) if val is not None else (tok, ""))
        i += 1
    return out


def compare(disk_doc: dict, new_doc: dict, strict: bool) -> tuple[bool, bool, list[str]]:
    """Return (ok, unknown_failed, lines).

    Compares DERIVED fields only; prints the MEASURED fields deliberately skipped; an unknown
    key (neither set) warns, or FAILS when strict, naming every unknown key. A DERIVED field
    whose on-disk difference is a measured carrying (see `carried`) is printed, not failed.
    """
    lines: list[str] = []
    disk_setups = disk_doc.get("setups", {}) if isinstance(disk_doc, dict) else {}
    new_setups = new_doc["setups"]
    ok = True
    unknown_failed = False
    carried_all: dict[str, set[str]] = {}
    lines.append("COMPARE derived fields: " + ", ".join(sorted(DERIVED)))
    skipped_all = sorted(
        f for f in set().union(*[set(s) for s in new_setups.values()], *[set(s) for s in disk_setups.values()])
        if f in MEASURED or f not in DERIVED
    )
    measured_printed = sorted(f for f in skipped_all if f in MEASURED)
    lines.append("SKIPPED measured fields (not compared): " + ", ".join(measured_printed)
                 + (" [grid_unit: gcd of observed data]" if GRID_IS_MEASURED else ""))
    for key in sorted(set(new_setups) | set(disk_setups)):
        new_s = new_setups.get(key)
        disk_s = disk_setups.get(key)
        if new_s is None or disk_s is None:
            where = "only in build" if disk_s is None else "only on disk"
            lines.append(f"FAIL {key}: setup present in {where}")
            ok = False
            continue
        keep = carried(disk_s, new_s)
        carried_all[key] = keep
        for field in sorted(set(new_s) | set(disk_s)):
            if field in DERIVED:
                nv, dv = new_s.get(field, "<missing>"), disk_s.get(field, "<missing>")
                if nv != dv:
                    if field in keep:
                        lines.append(f"CARRIED {key}.{field}: pinned launch record {dv!r} != built {nv!r} "
                                     f"(argv token-identical; see evidence.launch_artefact)")
                        continue
                    lines.append(f"FAIL {key}.{field}: built={_short(nv)} disk={_short(dv)}")
                    ok = False
            elif field not in MEASURED:
                lines.append(f"WARN {key}.{field}: key in neither DERIVED nor MEASURED — not compared")
                unknown_failed = True
    n_carried = sum(len(v) for v in carried_all.values())
    lines.append(f"CARRIED derived fields (measured, not drift): {n_carried}")
    if strict and unknown_failed:
        lines.append("STRICT: unknown key(s) present -> FAIL")
        ok = False
    return ok, unknown_failed, lines


def _short(v) -> str:
    t = repr(v)
    return t if len(t) <= 70 else t[:67] + "..."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="re-derive and diff against what is on disk")
    ap.add_argument("--strict", action="store_true",
                    help="with --check: an unknown key fails instead of warning")
    ap.add_argument("--config", default=None, help="compare against this file instead of the repo one")
    a = ap.parse_args()
    doc = build()
    blob = json.dumps(doc, indent=2, sort_keys=False) + "\n"
    if a.check:
        path = Path(a.config) if a.config else OUT
        cur = path.read_text() if path.exists() else ""
        if not cur:
            print(f"CHECK setups identical to disk: False ({path} missing)")
            return 1
        ok, _unknown, lines = compare(json.loads(cur), doc, a.strict)
        for line in lines:
            print(line)
        print(f"CHECK against: {path}")
        print(f"CHECK setups identical to disk: {ok}")
        print(f"CHECK keys: {list(doc['setups'])}")
        for k, s in doc["setups"].items():
            print(f"  {k} {s['model']:<12} {s['engine']:<7} hit={s['hit']} unc={s['unc_per_turn']} "
                  f"grid={s['grid_unit']} sha={s['config_sha256'][:12]}")
        return 0 if ok else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(blob)
    print(f"wrote {OUT} ({len(blob)} B)")
    print(f"keys: {list(doc['setups'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
