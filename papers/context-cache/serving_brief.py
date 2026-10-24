#!/usr/bin/env python3
"""Assemble, render and verify ``papers/context-cache/SERVING-BRIEF.md``.

The brief is operator-facing, so its numbers must be defensible by a single command.
Every figure in it is an item in this module's ledger, and every item carries:

  * ``cell``   -- the measurement cell on disk the figure comes from;
  * ``source`` -- the one command or file that re-derives it;
  * ``measured`` -- the machine-readable values the rendered sentence was built from.

Three kinds of item exist, and each is verified against an authority that is not the
brief itself:

  1. **claim-backed** -- recomputed by ``recompute.py``'s own ``FUNCS[cid]()`` and compared
     against that file's ``EXPECTED[cid]`` (the paper's value).  This is the independent
     path: the row file, not this module, is the authority.
  2. **row-backed** -- computed here from a cell's ``rows.jsonl`` (only where no claim owns
     the figure yet), with the cell's row digest pinned in the ledger.
  3. **artefact-backed** -- read from a cell's ``analysis.json``, whose own ``rows`` digest
     is checked against ``rows.jsonl`` so the artefact cannot be stale relative to its rows.

Commands::

    .venv/bin/python papers/context-cache/serving_brief.py --check   # fail on any drift
    .venv/bin/python papers/context-cache/serving_brief.py --json    # the ledger
    .venv/bin/python papers/context-cache/serving_brief.py --table   # the rendered table
    .venv/bin/python papers/context-cache/serving_brief.py --inject  # rewrite the blocks

Reads only the cells and the config capture. Makes no live request. ``--inject`` writes
only ``SERVING-BRIEF.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
CELLS = ROOT / "experiments" / "context-cache" / "cells"
BRIEF = PKG / "SERVING-BRIEF.md"
LEDGER = ROOT / "state" / "serving-brief.json"
LIVE_CONFIG = ROOT / "state" / "config" / "live-server-config.json"

BEGIN_NUMBERS, END_NUMBERS = "<!-- BEGIN SERVING-BRIEF NUMBERS -->", "<!-- END SERVING-BRIEF NUMBERS -->"
BEGIN_MATRIX, END_MATRIX = "<!-- BEGIN SERVING-BRIEF MATRIX -->", "<!-- END SERVING-BRIEF MATRIX -->"

DATED = "2026-10-23"


class Drift(Exception):
    """A figure no longer re-derives from its cell."""


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def jd(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


_RC = None


def rc():
    global _RC
    if _RC is None:
        if str(PKG) not in sys.path:
            sys.path.insert(0, str(PKG))
        import recompute  # noqa: E402  (local module, imported once)
        _RC = recompute
    return _RC


def _tol_close(got, want, tol: float) -> bool:
    if isinstance(want, bool) or isinstance(want, str):
        return got == want
    if isinstance(want, (int, float)):
        return abs(float(got) - float(want)) <= max(tol, abs(float(want)) * tol)
    if isinstance(want, (list, tuple)):
        return (
            isinstance(got, (list, tuple))
            and len(got) == len(want)
            and all(_tol_close(g, w, tol) for g, w in zip(got, want))
        )
    return got == want


def claim(cid: str, keys: list[str]) -> dict:
    """Recompute a claim through recompute.py and check it against the paper's value."""
    R = rc()
    if cid not in R.FUNCS:
        raise Drift(f"{cid}: no runner in recompute.py")
    got = R.FUNCS[cid]()
    if cid in R.FLATTEN:
        got = R.FLATTEN[cid](got)
    want = R.EXPECTED[cid]
    tol = R.TOLERANCE.get(cid, 1e-9)
    for key, expected in want.items():
        if key not in got:
            raise Drift(f"{cid}: runner returned no {key!r}")
        if not _tol_close(got[key], expected, tol):
            raise Drift(f"{cid}.{key}: recomputed {got[key]!r} != paper {expected!r} (tol {tol})")
    missing = [k for k in keys if k not in got]
    if missing:
        raise Drift(f"{cid}: runner returned no {missing}")
    return {k: got[k] for k in keys}


def item(item_id, fact, value, cell, source, measured, matrix=None) -> dict:
    out = {
        "id": item_id,
        "fact": fact,
        "value": value,
        "cell": cell,
        "source": source,
        "measured": measured,
    }
    if matrix is not None:
        out["matrix"] = matrix
    return out


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
def n(x, decimals: int = 0) -> str:
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, int):
        return f"{x:,}"
    return f"{x:,.{decimals}f}"


def e(x) -> str:
    return f"{x:.2e}"


# --------------------------------------------------------------------------- #
# Items
# --------------------------------------------------------------------------- #
def s01() -> dict:
    c = claim("C47", ["rows_total", "status_200", "hit_fraction", "mean_uncached_per_turn",
                      "mean_uncached_32k", "mean_uncached_64k", "steady_n"])
    value = (
        f"{n(c['rows_total'])} rows, all {n(c['status_200'])} OK, {n(c['steady_n'])} steady · "
        f"hit {c['hit_fraction']:.6f} · {c['mean_uncached_per_turn']:.1f} uncached/turn "
        f"(32k {c['mean_uncached_32k']:.2f}; 64k {c['mean_uncached_64k']:.2f})"
    )
    return item("S01", "Production SGLang battery, both depth bands", value, "G3",
                "recompute.py C47", {"C47": c})


MATRIX_CELLS = {
    ("occamy-1.0", "vllm"): ("S02", "occamy-1.0 (MoE)", "vLLM 0.27.1", "MOE-VLLM"),
    ("occamy-1.0", "sglang"): ("S03", "occamy-1.0 (MoE)", "SGLang", "G3"),
    ("qwen3.5-9b", "vllm"): ("S04", "qwen3.5-9b (dense)", "vLLM 0.27.1", "WIN-VLLM"),
    ("qwen3.5-9b", "sglang"): ("S05", "qwen3.5-9b (dense)", "SGLang", "DENSE-SGL"),
}


def s02_s05() -> list[dict]:
    c = claim("C63", ["rows_total", "rows_per_cell", "paired_turns", "cells"])
    out = []
    for model, engine, count, hit, uncached, block in c["cells"]:
        item_id, model_label, engine_label, cell = MATRIX_CELLS[(model, engine)]
        value = (
            f"hit {hit:.6f} · {uncached:.4f} uncached/turn · block {block} · {n(count)} rows"
        )
        out.append(item(item_id, f"{model_label} on {engine_label}, 32k band", value, cell,
                        "recompute.py C63", {"C63": {"hit_fraction": hit,
                                                     "mean_uncached_per_turn": uncached,
                                                     "block": block, "rows": count}},
                        matrix={"model": model_label, "engine": engine_label, "block": block,
                                "hit": hit, "unc": uncached, "rows": count}))
    return out


def s06() -> dict:
    c = claim("C63", ["engine_ratio_moe", "engine_ratio_dense", "engine_effect",
                      "model_effect", "engine_share_of_grand"])
    value = (
        f"engine costs {c['engine_ratio_moe']:.4f}x (MoE) / {c['engine_ratio_dense']:.4f}x (dense) · "
        f"engine effect {c['engine_effect']:,.2f} vs model {c['model_effect']:,.2f} uncached tokens/turn · "
        f"engine share {c['engine_share_of_grand']:.4f}"
    )
    return item("S06", "Engine main effect vs model main effect", value, "four cells",
                "recompute.py C63", {"C63": c})


def s07() -> dict:
    c = claim("C63", ["model_ratio_sglang", "model_ratio_vllm",
                      "model_effect_ratio_vllm_over_sglang"])
    value = (
        f"model ratio {c['model_ratio_sglang']:.4f} under SGLang vs {c['model_ratio_vllm']:.4f} "
        f"under vLLM · vLLM/SGLang model effect {c['model_effect_ratio_vllm_over_sglang']:,.4f}"
    )
    return item("S07", "Does the model choice matter on each engine?", value, "four cells",
                "recompute.py C63", {"C63": c})


def s08() -> dict:
    c = claim("C53", ["B_over_A_mean", "B_over_A_ci95_low", "B_over_A_ci95_high",
                      "A_uncached", "B_uncached", "n_fanouts", "n_branches"])
    value = (
        f"late branch B/A = {c['B_over_A_mean']:.4f} "
        f"[{c['B_over_A_ci95_low']:.4f}, {c['B_over_A_ci95_high']:.4f}] · "
        f"A {n(c['A_uncached'])} vs B {n(c['B_uncached'])} uncached tokens · "
        f"{c['n_fanouts']} fan-outs, {c['n_branches']} branches"
    )
    return item("S08", "Fan-out: branch late, keep shared bytes identical", value, "G5",
                "recompute.py C53", {"C53": c})


def s09() -> dict:
    c40 = claim("C40", ["L1024_misses", "L1024_n", "L1088_misses", "L1088_n",
                        "L1008_misses", "L1023_misses", "L1025_misses",
                        "miss_ttft_ms_1024_median"])
    c41 = claim("C41", ["pooled_multiple_misses", "pooled_multiple_n",
                        "pooled_nonmultiple_misses", "pooled_nonmultiple_n",
                        "pooled_fisher_p"])
    value = (
        f"1,024 and 1,088 (exact unit multiples): {c40['L1024_misses']}/{c40['L1024_n']} and "
        f"{c40['L1088_misses']}/{c40['L1088_n']} miss on the immediate repeat; "
        f"1,008 / 1,023 / 1,025: {c40['L1008_misses']} misses each; "
        f"pooled {c41['pooled_multiple_misses']}/{c41['pooled_multiple_n']} vs "
        f"{c41['pooled_nonmultiple_misses']}/{c41['pooled_nonmultiple_n']}, p {e(c41['pooled_fisher_p'])} · "
        f"missed prefill {c40['miss_ttft_ms_1024_median']:.1f} ms TTFT"
    )
    return item("S09", "Boundary lengths pay a full re-prefill on a warm repeat", value, "U10",
                "recompute.py C40, C41", {"C40": c40, "C41": c41})


def s10() -> dict:
    c46 = claim("C46", ["S1_hit_fraction", "S1_mean_uncached_per_turn",
                        "S2_hit_fraction", "S2_mean_uncached_per_turn"])
    c47 = claim("C47", ["mean_uncached_per_turn"])
    c57 = claim("C57", ["S1_vs_S0_paired", "S1_vs_S0_identical", "S0_gcd_cached",
                        "S1_gcd_cached", "S2_gcd_cached"])
    value = (
        f"S1 (page 64) {c46['S1_mean_uncached_per_turn']:.1f} vs S2 (page 128) "
        f"{c46['S2_mean_uncached_per_turn']:.1f} vs S0 (production) "
        f"{c47['mean_uncached_per_turn']:.1f} uncached/turn · "
        f"S1 vs S0 identical on {n(c57['S1_vs_S0_identical'])}/{n(c57['S1_vs_S0_paired'])} paired rows · "
        f"grid {c57['S0_gcd_cached']}/{c57['S1_gcd_cached']}/{c57['S2_gcd_cached']}"
    )
    return item("S10", "Page size: 64 and 128 against the production default", value,
                "WIN-SGL, G3", "recompute.py C46, C47, C57",
                {"C46": c46, "C47": c47, "C57": c57})


def s11() -> dict:
    c = claim("C58", ["paired_rows", "identical", "S2_lower_by_64", "S2_higher",
                      "ttft_ratio_median", "mean_uncached_S1", "mean_uncached_S2"])
    value = (
        f"{n(c['paired_rows'])} paired rows: {n(c['identical'])} identical, "
        f"{n(c['S2_lower_by_64'])} lower by 64, {n(c['S2_higher'])} higher · "
        f"TTFT ratio median {c['ttft_ratio_median']:.3f} · "
        f"{c['mean_uncached_S1']:.1f} vs {c['mean_uncached_S2']:.2f} uncached/turn"
    )
    return item("S11", "The one page-size condition that moved the grid", value, "WIN-SGL",
                "recompute.py C58", {"C58": c})


def s12() -> dict:
    c59 = claim("C59", ["rows_total", "pressure_ratio", "band_newest_hits", "band_newest_n",
                        "band_middle_hits", "band_middle_n", "band_oldest_hits",
                        "band_oldest_n", "radix_eviction_policy"])
    c60 = claim("C60", ["TUNED_hit_fraction", "TUNED_mean_uncached", "TUNED_over_S0_per_turn"])
    value = (
        f"hit {c60['TUNED_hit_fraction']:.6f} · {c60['TUNED_mean_uncached']:,.1f} uncached/turn "
        f"({c60['TUNED_over_S0_per_turn']:,.4f}x production) at {c59['pressure_ratio']:.6f}x pressure · "
        f"bands newest {c59['band_newest_hits']}/{c59['band_newest_n']}, "
        f"middle {c59['band_middle_hits']}/{c59['band_middle_n']}, "
        f"oldest {c59['band_oldest_hits']}/{c59['band_oldest_n']} · "
        f"policy {c59['radix_eviction_policy']}"
    )
    return item("S12", "SLRU eviction policy under deliberate pressure", value, "TUNED",
                "recompute.py C59, C60", {"C59": c59, "C60": c60})


def s13() -> dict:
    """Row-backed bands + artefact-backed pressure discipline (M4)."""
    rows = jl(CELLS / "M4" / "rows.jsonl")
    replay = [r for r in rows if r.get("phase") == "R"]
    bands = {}
    for band in ("newest", "middle", "oldest"):
        sub = [r for r in replay if r.get("band") == band]
        if not sub:
            raise Drift(f"M4: no replay rows for band {band!r}")
        bands[band] = {
            "n": len(sub),
            "hit": sum(int(r["cached_tokens"]) for r in sub) / sum(int(r["prompt_tokens"]) for r in sub),
        }
    analysis = jd(CELLS / "M4" / "analysis.json")
    recorded = analysis.get("digest", {}).get("rows_sha256") or analysis.get("rows", {}).get("rows_sha256")
    actual = sha256(CELLS / "M4" / "rows.jsonl")
    if recorded != actual:
        raise Drift(f"M4 analysis.json pins rows {recorded!r}, disk has {actual!r}")
    docs = analysis.get("phase_d", {}).get("documents", [])
    appended = [d["appended_tokens"] for d in docs if d.get("shape") == "append_note"]
    resend = [d["appended_tokens"] for d in docs if d.get("shape") == "full_resend"]
    if not appended or not resend:
        raise Drift("M4 analysis.json phase_d has no append_note/full_resend documents")
    mean_appended = sum(appended) / len(appended)
    hits = [d["hit_ratio"] for d in docs]
    if any(h != 0.0 for h in hits):
        raise Drift(f"M4 phase_d hit_ratio is not all zero: {hits!r}")
    value = (
        f"replay bands: newest {bands['newest']['hit']:.3f}, "
        f"middle {bands['middle']['hit']:.3f}, oldest {bands['oldest']['hit']:.3f} · "
        f"append-note under pressure: hit 0.000 both shapes, "
        f"{mean_appended:.1f} tokens appended"
    )
    return item("S13", "LRU at pressure, and whether an appended note survives it", value, "M4",
                "rows.jsonl phase R + analysis.json phase_d",
                {"bands": bands, "phase_d": {"n": len(docs), "mean_appended": mean_appended,
                                             "hit": 0.0}})


def s14() -> dict:
    c = claim("C54", ["resident_capacity_docs_low", "resident_capacity_docs_high",
                      "resident_capacity_tokens_low", "resident_capacity_tokens_high",
                      "resident_capacity_ratio_low", "resident_capacity_ratio_high",
                      "token_capacity", "total_pressure_tokens", "pressure_ratio",
                      "docs_pushed", "binding_constraint", "verdict", "token_pool_lru_docs"])
    value = (
        f"declared {n(c['token_capacity'])} tokens · resident "
        f"{n(c['resident_capacity_docs_low'])}-{n(c['resident_capacity_docs_high'])} docs = "
        f"{n(c['resident_capacity_tokens_low'])}-{n(c['resident_capacity_tokens_high'])} tokens = "
        f"{c['resident_capacity_ratio_low']:.4f}-{c['resident_capacity_ratio_high']:.4f} of capacity · "
        f"{n(c['docs_pushed'])} docs, {c['pressure_ratio']:.6f}x pressure, "
        f"{n(c['total_pressure_tokens'])} tokens · binding constraint {c['binding_constraint']} "
        f"({c['verdict']}; token-pool LRU {c['token_pool_lru_docs']:.2f} docs excluded)"
    )
    return item("S14", "Declared KV capacity vs resident reusable capacity", value, "M4",
                "recompute.py C54", {"C54": c})


def s15() -> dict:
    c = claim("C62", ["rows", "compaction_rows", "post_delta_min", "post_delta_max",
                      "post_turn_delta_min", "post_turn_delta_max",
                      "boundary_turn_uncached_min", "boundary_turn_uncached_max",
                      "baseline_drop_uncached_min", "baseline_drop_uncached_max"])
    value = (
        f"{n(c['compaction_rows'])} compactions in {n(c['rows'])} rows · post-boundary "
        f"+{c['post_delta_min']:.1f} to +{c['post_delta_max']:.1f} uncached/turn on average · "
        f"per turn {c['post_turn_delta_min']:,.1f} to +{n(c['post_turn_delta_max'])} · "
        f"boundary turn {n(c['boundary_turn_uncached_min'])}-{n(c['boundary_turn_uncached_max'])} vs "
        f"baseline drop {n(c['baseline_drop_uncached_min'])}-{n(c['baseline_drop_uncached_max'])}"
    )
    return item("S15", "Compaction at a real 32k/64k boundary", value, "G3-LIMIT-V2",
                "recompute.py C62", {"C62": c})


def s16() -> dict:
    c25 = claim("C25", ["A_first_prompt", "A_last_prompt", "A_growth_factor",
                        "A_total_prompt", "C_total_prompt"])
    c21 = claim("C21", ["R_over_A", "R_F_gap_pct"])
    value = (
        f"append window {n(c25['A_first_prompt'])} -> {n(c25['A_last_prompt'])} tokens "
        f"({c25['A_growth_factor']:.4f}x) · total prompt {n(c25['A_total_prompt'])} vs control "
        f"{n(c25['C_total_prompt'])} · A beats summarise-in-place by {c21['R_over_A']:.4f}x"
    )
    return item("S16", "Append-a-note: cheap per turn, unbounded window", value, "U15",
                "recompute.py C25, C21", {"C25": c25, "C21": c21})


def s17() -> dict:
    c32 = claim("C32", ["miss", "hit", "ratio", "delta"])
    c34 = claim("C34", ["miss_ms_per_token", "hit_ms_per_token", "hit_us_per_token"])
    value = (
        f"31,415-token prompt: {c32['miss']:,.1f} ms miss -> {c32['hit']:.1f} ms hit "
        f"({c32['ratio']:.4f}) · hit {c34['hit_us_per_token']:.2f} us/token vs miss "
        f"{c34['miss_ms_per_token']:.6f} ms/token"
    )
    return item("S17", "What a cache hit is worth in latency", value, "U9",
                "recompute.py C32, C34", {"C32": c32, "C34": c34})


def s18() -> dict:
    analysis = jd(CELLS / "CROSS-HTTP" / "analysis.json")
    rows = jl(CELLS / "CROSS-HTTP" / "rows.jsonl")
    counts = analysis["counts"]
    if counts.get("rows") != len(rows):
        raise Drift(f"CROSS-HTTP counts.rows {counts.get('rows')!r} != {len(rows)} rows on disk")
    reported = analysis["cache_signal"]["prompt_tokens_details_reported"]
    block = analysis["engine_counters"]["implied_block_size"]
    if reported is not False:
        raise Drift("CROSS-HTTP: analysis now reports prompt_tokens_details")
    if block != 1056.0:
        raise Drift(f"CROSS-HTTP: implied block changed to {block!r}")
    value = (
        f"cached_tokens field absent from every response · engine counter moves exactly "
        f"{block:,.0f} tokens per repeat · {n(counts['rows'])} rows, "
        f"{n(counts['live_requests'])} live requests"
    )
    return item("S18", "vLLM without the usage flag cannot report cache hits", value,
                "CROSS-HTTP", "analysis.json cache_signal + engine_counters",
                {"reported": False, "implied_block_size": block,
                 "rows": counts["rows"], "live_requests": counts["live_requests"]})


def s19() -> dict:
    cfg = jd(LIVE_CONFIG)
    state = cfg["raw_top_level_config"]["internal_states"][0]
    measured = {
        "context_length": state["context_length"],
        "page_size": state["page_size"],
        "max_mamba_cache_size": state["max_mamba_cache_size"],
        "mem_fraction_static": state["mem_fraction_static"],
        "disable_chunked_prefix_cache": state["disable_chunked_prefix_cache"],
    }
    value = (
        f"context {n(measured['context_length'])} · page_size {measured['page_size']} · "
        f"max_mamba_cache_size {measured['max_mamba_cache_size']} · "
        f"mem_fraction_static {measured['mem_fraction_static']} · "
        f"disable_chunked_prefix_cache {str(measured['disable_chunked_prefix_cache']).lower()}"
    )
    return item("S19", "The production flag set a reader must not change blind", value,
                "no cell; pinned config capture", "state/config/live-server-config.json",
                {"capture": measured})


# --------------------------------------------------------------------------- #
# Ledger
# --------------------------------------------------------------------------- #
CELLS_USED = ("G3", "MOE-VLLM", "WIN-VLLM", "DENSE-SGL", "G5", "U10", "WIN-SGL",
              "TUNED", "M4", "G3-LIMIT-V2", "U15", "U9", "CROSS-HTTP")

# A cell's rows are not always named rows.jsonl; pin every row file the ledger leans on.
CELL_FILES = {
    "U9": ("u9_trials.jsonl",),
    "U10": ("u10_rows.jsonl", "u10_rows_p23.jsonl"),
}
DEFAULT_ROW_FILE = ("rows.jsonl",)


def build_ledger() -> dict:
    items = [s01(), *s02_s05(), s06(), s07(), s08(), s09(), s10(), s11(), s12(),
             s13(), s14(), s15(), s16(), s17(), s18(), s19()]
    ids = [it["id"] for it in items]
    if len(ids) != len(set(ids)):
        raise Drift(f"duplicate item ids: {ids}")
    cells = {}
    for cell in CELLS_USED:
        files = {}
        for name in CELL_FILES.get(cell, DEFAULT_ROW_FILE):
            path = CELLS / cell / name
            if not path.is_file():
                raise Drift(f"cell {cell}: {path} is missing")
            files[f"experiments/context-cache/cells/{cell}/{name}"] = sha256(path)
        cells[cell] = {"files": files}
    return {
        "unit": "SERVING-BRIEF",
        "dated": DATED,
        "live_requests": 0,
        "evidence_rule": (
            "Every figure in SERVING-BRIEF.md is an item below. Claim-backed items are "
            "recomputed by papers/context-cache/recompute.py and compared with that file's "
            "EXPECTED value; row-backed items are recomputed from the named cell's rows.jsonl; "
            "artefact-backed items are read from the named cell's analysis.json, whose pinned "
            "rows digest is checked against rows.jsonl. The pinned config capture is hashed, "
            "not probed."
        ),
        "cells": cells,
        "config_capture": {
            "path": "state/config/live-server-config.json",
            "sha256": sha256(LIVE_CONFIG),
        },
        "items": items,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_numbers(ledger: dict) -> str:
    lines = [
        "| ID | Operator question | Measured value | Cell | Recompute from |",
        "|---|---|---|---|---|",
    ]
    for it in ledger["items"]:
        lines.append(f"| {it['id']} | {it['fact']} | {it['value']} | {it['cell']} | {it['source']} |")
    return "\n".join(lines)


def render_matrix(ledger: dict) -> str:
    lines = [
        "| ID | Model | Engine | Reuse block | Hit fraction | Uncached/turn | Rows |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for it in ledger["items"]:
        m = it.get("matrix")
        if not m:
            continue
        lines.append(
            f"| {it['id']} | {m['model']} | {m['engine']} | {m['block']} | {m['hit']:.6f} | "
            f"{m['unc']:.4f} | {n(m['rows'])} |"
        )
    return "\n".join(lines)


def block_bounds(text: str, begin: str, end: str) -> tuple[int, int]:
    start = text.index(begin)
    stop = text.index(end) + len(end)
    return start, stop


def block_body(text: str, begin: str, end: str) -> str:
    start, stop = block_bounds(text, begin, end)
    inner = text[start + len(begin):stop - len(end)]
    return inner.strip("\n")


def inject(text: str, begin: str, end: str, body: str) -> str:
    start, stop = block_bounds(text, begin, end)
    return f"{text[:start]}{begin}\n{body}\n{end}{text[stop:]}"


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
NUMBER = re.compile(r"(?<![\w§.])(\d[\d,]*(?:\.\d+)?(?:[eE]-?\d+)?k?)(?![\w])")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def table_numbers(*blocks: str) -> set[str]:
    out = set()
    for block in blocks:
        for token in NUMBER.findall(block):
            out.add(token.replace(",", ""))
    return out


def prose_lines(text: str):
    in_code = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if stripped.startswith("|"):
            continue
        if stripped.startswith("<!--"):
            continue
        yield line


def check_markers(text: str, ledger: dict) -> list[str]:
    ids = [it["id"] for it in ledger["items"]]
    found = set(re.findall(r"\b(S\d{2})\b", text))
    problems = []
    unknown = sorted(found - set(ids))
    unused = sorted(set(ids) - found)
    if unknown:
        problems.append(f"brief cites unknown item(s): {', '.join(unknown)}")
    if unused:
        problems.append(f"ledger item(s) never cited in the brief: {', '.join(unused)}")
    return problems


def check_prose_numbers(text: str, ledger: dict) -> list[str]:
    allowed = table_numbers(render_numbers(ledger), render_matrix(ledger))
    problems = []
    cleaned = ISO_DATE.sub("<date>", text)
    for lineno, line in enumerate(cleaned.splitlines(), 1):
        if line.lstrip().startswith("|") or line.lstrip().startswith("<!--"):
            continue
        for token in NUMBER.findall(line):
            if token in ("<date>",):
                continue
            if token.replace(",", "") not in allowed:
                problems.append(f"line {lineno}: number {token!r} appears in prose but in no ledger row")
    return problems


def check(quiet: bool = False) -> int:
    problems: list[str] = []
    try:
        built = build_ledger()
    except Drift as exc:
        print(f"SERVING-BRIEF CHECK FAIL  {exc}")
        return 1
    if not LEDGER.is_file():
        problems.append(f"{LEDGER} does not exist; run --write")
    else:
        committed = jd(LEDGER)
        if json.dumps(built, sort_keys=True) != json.dumps(committed, sort_keys=True):
            problems.append("state/serving-brief.json is stale: rebuild with --write")
    if not BRIEF.is_file():
        problems.append(f"{BRIEF} does not exist")
    else:
        text = BRIEF.read_text(encoding="utf-8")
        for begin, end, render, name in (
            (BEGIN_NUMBERS, END_NUMBERS, render_numbers, "numbers table"),
            (BEGIN_MATRIX, END_MATRIX, render_matrix, "matrix table"),
        ):
            expected = render(built)
            actual = block_body(text, begin, end)
            if actual != expected:
                problems.append(f"{name} block does not match the ledger rendering")
        problems.extend(check_markers(text, built))
        problems.extend(check_prose_numbers(text, built))
    # Row digests: the ledger's own pins must still be the files on disk.
    for cell, info in built["cells"].items():
        for rel, pinned in info["files"].items():
            disk = sha256(ROOT / rel)
            if disk != pinned:
                problems.append(f"{cell}: {rel} digest moved ({pinned[:12]} -> {disk[:12]})")
    if problems:
        print(f"SERVING-BRIEF CHECK FAIL  {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    if not quiet:
        print(f"SERVING-BRIEF CHECK PASS  {len(built['items'])} items, "
              f"{len(built['cells'])} cells, all figures re-derived; "
              "tables, markers and prose numbers match the ledger")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the ledger and the brief")
    parser.add_argument("--json", action="store_true", help="print the ledger")
    parser.add_argument("--table", action="store_true", help="print the numbers table")
    parser.add_argument("--matrix", action="store_true", help="print the matrix table")
    parser.add_argument("--write", action="store_true", help="write state/serving-brief.json")
    parser.add_argument("--inject", action="store_true", help="rewrite the brief's table blocks")
    args = parser.parse_args(argv[1:])
    if not any(vars(args).values()):
        parser.print_help()
        return 0
    if args.check:
        return check()
    ledger = build_ledger()
    if args.json:
        print(json.dumps(ledger, indent=1, sort_keys=True))
    if args.table:
        print(render_numbers(ledger))
    if args.matrix:
        print(render_matrix(ledger))
    if args.write:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {LEDGER.relative_to(ROOT)}")
    if args.inject:
        text = BRIEF.read_text(encoding="utf-8")
        text = inject(text, BEGIN_NUMBERS, END_NUMBERS, render_numbers(ledger))
        text = inject(text, BEGIN_MATRIX, END_MATRIX, render_matrix(ledger))
        BRIEF.write_text(text, encoding="utf-8")
        print(f"rewrote {BRIEF.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
