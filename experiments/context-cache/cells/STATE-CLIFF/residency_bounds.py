#!/usr/bin/env python3
"""Derive the corrected residency record for the STATE-CLIFF sweep.

Reads only the frozen per-rung ``analysis.json`` + ``rows.jsonl`` written by the
battery; writes ``residency-bounds.json`` next to this file.  No network, no
docker, no writes outside this cell.

Why this file exists: ``sweep_summary.json`` was assembled ad hoc after the
rungs ran and its ``res_docs`` / ``res_tok`` columns have no generator in this
cell (grep for ``res_docs`` finds nothing).  It must not be used for resident
counts.  What the rows actually support is a *sampled lower bound* plus a
*bracket* between the deepest sampled hit and the shallowest sampled miss.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNGS = (64, 48, 32, 16)
BANDS = ("oldest", "middle", "newest")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def band_view(analysis: dict, band: str) -> dict:
    docs = analysis["phase_r"]["bands"][band]["docs"]
    hits = [d for d in docs if d["cached_tokens"] > 0]
    return {
        "n_sampled": len(docs),
        "n_hit": len(hits),
        "hit_ratio_mean": (
            sum(d["hit_ratio"] for d in docs) / len(docs) if docs else None
        ),
        "hit_doc_positions": [d["doc_position"] for d in hits],
        "positions_sampled": [d["doc_position"] for d in docs],
        "prompt_tokens": sum(d["prompt_tokens"] for d in docs),
        "cached_tokens": sum(d["cached_tokens"] for d in docs),
    }


def main() -> int:
    out = {"schema": "state-cliff.residency-bounds/1", "rungs": [], "rung_64_reference": None}
    for n in RUNGS:
        d = HERE / f"rung-{n}"
        analysis = json.loads((d / "analysis.json").read_text())
        run = analysis["run"]
        ev = analysis["eviction"]
        bands = {b: band_view(analysis, b) for b in BANDS}
        hit_positions = sorted(
            p for b in BANDS for p in bands[b]["hit_doc_positions"]
        )
        miss_positions = sorted(
            p
            for b in BANDS
            for p in bands[b]["positions_sampled"]
            if p not in bands[b]["hit_doc_positions"]
        )
        deepest_hit = min(hit_positions) if hit_positions else None
        shallowest_miss = max(miss_positions) if miss_positions else None
        # Rung 16 never hit: the only defensible statement is that the boundary
        # sits below the shallowest *replayed* position in the newest band.
        newest_positions = bands["newest"]["positions_sampled"]
        boundary_below = (
            min(newest_positions) if not hit_positions and newest_positions else None
        )
        rec = {
            "max_mamba_cache_size": run["max_mamba_cache_size"],
            "server_version": run["server_version"],
            "capacity_tokens": run["token_capacity"],
            "docs_pushed": run["docs_pushed"],
            "total_pressure_tokens": run["total_pressure_tokens"],
            "pressure_ratio": run["pressure_ratio"],
            "pressure_target_ratio": run["pressure_target_ratio"],
            "pressure_shortened": run["pressure_shortened"],
            "requests_used": run["requests_used"],
            "requests_by_phase": run["requests_by_phase"],
            "failures": run["failures"],
            "bands": bands,
            "sampled_hit_positions": hit_positions,
            "sampled_miss_positions": miss_positions,
            "sampled_hit_docs": len(hit_positions),
            "sampled_miss_docs": len(miss_positions),
            "sampled_hit_tokens_est": sum(
                bands[b]["cached_tokens"] for b in BANDS
            ),
            "resident_lower_bound_docs": len(hit_positions),
            "resident_lower_bound_tokens": bands["newest"]["cached_tokens"]
            + bands["middle"]["cached_tokens"]
            + bands["oldest"]["cached_tokens"],
            "boundary_bracket": {
                "resident_from_doc_position": deepest_hit,
                "evicted_up_to_doc_position": shallowest_miss,
                "boundary_below_doc_position": boundary_below,
                "evicted_up_to_cum_tokens": ev["bracket"]["evicted_up_to_cum_tokens"],
                "resident_from_cum_tokens": ev["bracket"]["resident_from_cum_tokens"],
                "width_docs": (deepest_hit - shallowest_miss)
                if deepest_hit and shallowest_miss
                else None,
            },
            "predicted_resident_docs_if_kv_bound": ev["predicted_resident_docs"],
            "lru_verdict": analysis["lru"]["verdict"],
            "rows_sha256": run["rows_sha256"],
            "analysis_sha256": sha256(d / "analysis.json"),
            "rows_file_sha256": sha256(d / "rows.jsonl"),
        }
        # The rows file must match the digest the analysis recorded: same
        # evidence, two derivations.
        rec["rows_digest_matches_analysis"] = (
            rec["rows_file_sha256"] == rec["rows_sha256"]
        )
        out["rungs"].append(rec)
        if n == 64:
            out["rung_64_reference"] = {
                "capacity_tokens": rec["capacity_tokens"],
                "pressure_ratio": rec["pressure_ratio"],
            }

    ref = out["rung_64_reference"]
    for rec in out["rungs"]:
        rec["capacity_delta_vs_64_tokens"] = rec["capacity_tokens"] - ref["capacity_tokens"]
        rec["capacity_delta_vs_64_pct"] = round(
            100.0 * rec["capacity_delta_vs_64_tokens"] / ref["capacity_tokens"], 2
        )
        # Sampled bands are only comparable as *bands*; a shared band pattern
        # does not establish a shared resident window.
        rec["sampled_band_pattern"] = (
            "hits_only_in_newest"
            if rec["bands"]["newest"]["n_hit"] == 10
            and rec["bands"]["middle"]["n_hit"] == 0
            and rec["bands"]["oldest"]["n_hit"] == 0
            else (
                "no_hits_anywhere"
                if rec["sampled_hit_docs"] == 0
                else "other"
            )
        )

    out["corrections"] = [
        "sweep_summary.json's res_docs/res_tok columns have no generator in this "
        "cell (grep res_docs finds only predicted_resident_docs in battery.py) and "
        "are not used here; treat that file's residency columns as void.",
        "A 10-document newest-band replay is a sampled LOWER BOUND on residency, "
        "never a resident count: only 30 of 283-300 pushed documents were replayed.",
        "The 64/48/32 rungs share an identical sampled band pattern; that is not "
        "evidence of equal resident windows, because the bracket (146..274) is wide "
        "enough to hide a large difference.",
        "Pressure was not held constant: ratios 1.504 / 1.498 / 1.447 / 1.374 while "
        "capacity itself moved (the flag changes static-memory split), so a rung "
        "delta cannot be attributed to the mamba slot budget alone.",
        "No boundary probe was run; the resident boundary is bracketed, not measured.",
        "Rung 16's zero sampled hits has no established cause: it is consistent with "
        "a smaller resident window, with the higher capacity pushing the newest "
        "documents closer to a harder eviction edge, or with both.",
    ]
    (HERE / "residency-bounds.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n"
    )
    for rec in out["rungs"]:
        print(
            f"rung {rec['max_mamba_cache_size']:>2}: cap={rec['capacity_tokens']} "
            f"pr={rec['pressure_ratio']} bands={rec['sampled_band_pattern']} "
            f"hits={rec['sampled_hit_docs']}/{rec['sampled_hit_docs'] + rec['sampled_miss_docs']} "
            f"lb_docs={rec['resident_lower_bound_docs']} "
            f"bracket={rec['boundary_bracket']['evicted_up_to_doc_position']}"
            f"..{rec['boundary_bracket']['resident_from_doc_position']}"
            f" below={rec['boundary_bracket']['boundary_below_doc_position']} "
            f"capdelta={rec['capacity_delta_vs_64_pct']}% "
            f"digest_ok={rec['rows_digest_matches_analysis']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
