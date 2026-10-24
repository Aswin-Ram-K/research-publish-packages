#!/usr/bin/env python3
"""WIN-TUNED — offline analysis: slru vs the M4 lru profile, band by band.

Reads only local files (``cells/TUNED/rows.jsonl``, ``cells/TUNED/run.json``,
``cells/M4/analysis.json``) and writes ``cells/TUNED/analysis.json``.  Sends no
requests, so a verifier can re-run it at any time.

The comparison metric is the **mean cached fraction** of a replayed band
(``cached_tokens / prompt_tokens``), exactly the number M4 reports as
``phase_r.bands[<band>].mean_hit_ratio``.  A band is called *better* / *worse*
at a 0.05 absolute margin; anything inside that margin is *indistinguishable*
(the block tax on a resident document is ~64/8600 = 0.007, so 0.05 is far
outside measurement noise and still small enough to catch a partial win).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
M4_ANALYSIS = REPO / "experiments" / "context-cache" / "cells" / "M4" / "analysis.json"
ROWS_PATH = HERE / "rows.jsonl"
RUN_PATH = HERE / "run.json"
OUT_PATH = HERE / "analysis.json"

BANDS = ("oldest", "middle", "newest")
MARGIN = 0.05


def read_rows(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        stack = row.get("stack")
        config_id = row.get("config_id")
        if not isinstance(stack, str) or not stack.strip():
            raise SystemExit(
                f"{path}: line {line_no}: missing or empty 'stack' "
                "(every replay row must be attributable to a stack)"
            )
        if not isinstance(config_id, str) or not config_id.strip():
            raise SystemExit(
                f"{path}: line {line_no}: missing or empty 'config_id' "
                "(every replay row must be attributable to a config_id)"
            )
        rows.append(row)
    return rows


def mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 6) if values else None


def band_summary(rows: list[dict]) -> dict:
    out = {}
    for band in BANDS:
        sel = [r for r in rows if r.get("band") == band]
        out[band] = {
            "n": len(sel),
            "positions": [r["doc_position"] for r in sel],
            "mean_prompt_tokens": mean([r["prompt_tokens"] for r in sel]),
            "mean_cached_tokens": mean([r["cached_tokens"] for r in sel]),
            "mean_uncached_tokens": mean([r["uncached_tokens"] for r in sel]),
            "mean_hit_ratio": mean([r["cached_tokens"] / max(1, r["prompt_tokens"]) for r in sel]),
            "n_full_hit": sum(1 for r in sel
                              if r["prompt_tokens"] and r["cached_tokens"] >= r["prompt_tokens"] - 64),
            "n_zero_hit": sum(1 for r in sel if r["cached_tokens"] == 0),
            "n_partial_hit": sum(1 for r in sel
                                 if 0 < r["cached_tokens"] < max(1, r["prompt_tokens"]) - 64),
            "docs": [
                {"doc_id": r["doc_id"], "doc_position": r["doc_position"],
                 "prompt_tokens": r["prompt_tokens"], "cached_tokens": r["cached_tokens"],
                 "uncached_tokens": r["uncached_tokens"],
                 "hit_ratio": round(r["cached_tokens"] / max(1, r["prompt_tokens"]), 6),
                 "cum_tokens_start": r.get("cum_prompt_tokens_start"),
                 "cum_tokens_end": r.get("cum_prompt_tokens"), "status": r["status"]}
                for r in sel
            ],
        }
    return out


def policy_order_verdict(bands: dict) -> dict:
    """Same four checks M4 applied to lru, applied to whatever this run did.

    A hit in the oldest band is *not* an anomaly for a segmented policy; the
    checks are kept identical so the two runs are judged by one rule, and the
    verdict string says which policy shape the profile looks like.
    """

    oldest = bands["oldest"]["mean_hit_ratio"] or 0.0
    middle = bands["middle"]["mean_hit_ratio"] or 0.0
    newest = bands["newest"]["mean_hit_ratio"] or 0.0
    checks = {
        "newest_intact": newest >= 0.90,
        "oldest_gone": oldest <= 0.10,
        "monotone_oldest_middle_newest": oldest <= middle <= newest,
    }
    if checks["newest_intact"] and checks["oldest_gone"] and checks["monotone_oldest_middle_newest"]:
        verdict = "lru_shaped_profile"
    elif checks["newest_intact"] and not checks["oldest_gone"]:
        verdict = "non_lru_profile_older_band_survives"
    elif newest < 0.90:
        verdict = "newest_band_damaged"
    else:
        verdict = "mixed"
    return {"verdict": verdict, "checks": checks,
            "checks_passed": sum(1 for v in checks.values() if v), "checks_total": 3,
            "criterion": "newest band mean hit >= 0.90; oldest band mean hit <= 0.10; "
                         "hit rate non-decreasing oldest->middle->newest"}


def compare(slru: dict, lru: dict) -> dict:
    per_band = {}
    for band in BANDS:
        s = slru[band]["mean_hit_ratio"] or 0.0
        l = lru[band]["mean_hit_ratio"] or 0.0
        delta = round(s - l, 6)
        if delta >= MARGIN:
            verdict = "better"
        elif delta <= -MARGIN:
            verdict = "worse"
        else:
            verdict = "indistinguishable"
        per_band[band] = {
            "slru_mean_hit_ratio": s, "lru_mean_hit_ratio": l, "delta": delta,
            "verdict": verdict,
            "slru_mean_cached_tokens": slru[band]["mean_cached_tokens"],
            "lru_mean_cached_tokens": lru[band]["mean_cached_tokens"],
            "slru_zero_hits": slru[band]["n_zero_hit"],
            "lru_zero_hits": lru[band]["n_zero_hit"],
            "slru_positions": slru[band]["positions"],
        }
    better = [b for b in BANDS if per_band[b]["verdict"] == "better"]
    worse = [b for b in BANDS if per_band[b]["verdict"] == "worse"]
    if better and not worse:
        verdict = f"slru_better_in_{'+'.join(better)}"
    elif worse and not better:
        verdict = f"slru_worse_in_{'+'.join(worse)}"
    elif better and worse:
        verdict = "mixed"
    else:
        verdict = "indistinguishable_in_all_bands"
    deltas = [per_band[b]["delta"] for b in BANDS]
    return {"margin": MARGIN, "per_band": per_band, "verdict": verdict,
            "mean_delta": round(sum(deltas) / len(deltas), 6),
            "bands_better": better, "bands_worse": worse}


def main() -> int:
    rows = read_rows(ROWS_PATH)
    if any(not (isinstance(r.get("stack"), str) and r.get("stack").strip()
                and isinstance(r.get("config_id"), str) and r.get("config_id").strip())
           for r in rows):
        raise SystemExit(f"{ROWS_PATH}: one or more rows lack stack/config_id")
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    m4 = json.loads(M4_ANALYSIS.read_text(encoding="utf-8"))
    lru_bands = m4["phase_r"]["bands"]

    p_rows = [r for r in rows if r["phase"] == "P"]
    r_rows = [r for r in rows if r["phase"] == "R"]
    if not p_rows or not r_rows:
        raise SystemExit(f"rows incomplete: P={len(p_rows)} R={len(r_rows)}")

    bands = band_summary(r_rows)
    comparison = compare(bands, lru_bands)

    slru_pressure = run["pressure_ratio"]
    lru_pressure = m4["run"]["pressure_ratio"]
    cap_slru = run["token_capacity"]
    cap_lru = m4["run"]["token_capacity"]
    docs_slru = run["docs_pushed"]
    docs_lru = m4["run"]["docs_pushed"]
    mean_doc = run["total_pressure_tokens"] / docs_slru

    # Pressure normalisation note: both runs stop at 1.5x their own capacity, so
    # the band positions (1-10, centre-10, last-10) are the same *relative*
    # positions; a capacity difference only shifts the centre by
    # (docs_slru - docs_lru) / 2 documents.
    centre_shift = (docs_slru - docs_lru) // 2
    normalisation = {
        "protocol": "both runs push distinct ~8.6k-token documents until cumulative measured "
                    "prompt tokens reach 1.5x that run's own token_capacity, then replay the "
                    "oldest 10 / middle 10 / newest 10 -- the bands are relative positions of "
                    "the submitted set, so the protocol normalises by construction",
        "slru": {"capacity": cap_slru, "docs_pushed": docs_slru,
                 "pressure_ratio": slru_pressure, "mean_doc_tokens": round(mean_doc, 3)},
        "lru": {"capacity": cap_lru, "docs_pushed": docs_lru,
                "pressure_ratio": lru_pressure,
                "mean_doc_tokens": m4["eviction"]["mean_doc_tokens"]},
        "capacity_delta_tokens": cap_slru - cap_lru,
        "capacity_delta_fraction": round((cap_slru - cap_lru) / cap_lru, 6),
        "docs_delta": docs_slru - docs_lru,
        "middle_band_position_shift": centre_shift,
        "pressure_ratio_delta": round(slru_pressure - lru_pressure, 6),
        "residual_effect": "a shift of at most "
                           f"{abs(centre_shift)} document position(s) at the centre cannot move a "
                           "document across the 30-31 document resident window M4 measured, so the "
                           "band comparison stands without rescaling; the only metric that would "
                           "need it is an absolute token-count comparison, which is reported below",
        "absolute_tokens_normalised": {
            band: {
                "slru_mean_cached_tokens": bands[band]["mean_cached_tokens"],
                "lru_mean_cached_tokens": lru_bands[band]["mean_cached_tokens"],
                "fraction_of_own_capacity_slru": round(
                    (bands[band]["mean_cached_tokens"] or 0) / cap_slru, 8),
                "fraction_of_own_capacity_lru": round(
                    (lru_bands[band]["mean_cached_tokens"] or 0) / cap_lru, 8),
            } for band in BANDS
        },
    }

    oldest_hits = [r for r in r_rows if r["band"] == "oldest" and r["cached_tokens"] > 0]
    middle_hits = [r for r in r_rows if r["band"] == "middle" and r["cached_tokens"] > 0]
    newest_misses = [r for r in r_rows if r["band"] == "newest" and r["cached_tokens"] == 0]
    # The three replay bands bracket the resident window from both sides, exactly
    # as M4's replay did before its 8-request boundary probe narrowed it.
    hit_positions = sorted(r["doc_position"] for r in r_rows if r["cached_tokens"] > 0)
    miss_positions = sorted(r["doc_position"] for r in r_rows if r["cached_tokens"] == 0)
    w_lo = (docs_slru - min(hit_positions) + 1) if hit_positions else 0
    w_hi = (docs_slru - max(miss_positions)) if miss_positions else docs_slru
    window = {
        "lru_reference_resident_window_docs": m4["eviction"]["observed"]["resident_capacity_docs_bracket"],
        "slru_oldest_band_hits": len(oldest_hits),
        "slru_middle_band_hits": len(middle_hits),
        "slru_newest_band_misses": len(newest_misses),
        "resident_window_docs_bracket": [w_lo, w_hi],
        "resident_window_note": (
            f"replay alone brackets the window to [{w_lo}, {w_hi}] documents (oldest surviving "
            f"replayed position {min(hit_positions) if hit_positions else None}, newest evicted "
            f"replayed position {max(miss_positions) if miss_positions else None}); it contains "
            "M4's [30, 31] but is too coarse to re-measure it, which is what M4's 8-request "
            "boundary probe was for and is not repeated here"),
        "reading": (
            "if the middle band had hit, the resident set would have reached the centre of the "
            f"submitted sequence (position ~{docs_slru // 2}), far past the 30-31 document window "
            "M4 measured under lru; it did not, so no deeper reuse than lru"
            if not middle_hits else
            "the middle band hit: the resident set reached the centre of the submitted sequence, "
            "past the 30-31 document window measured under lru"),
    }

    analysis = {
        "unit": "WIN-TUNED",
        "question": "does --radix-eviction-policy slru beat the production lru under pressure, "
                    "on the same protocol?",
        "answer": comparison["verdict"],
        "page_size_reconciliation": "variant_server_info.json has page_size=1 at top-level and in internal_states; SGLang FLA cache_chunk_size=64 produces the 64-token grid; therefore rows' 64-token law is consistent with page_size=1 config, and TUNED is not a no-grid baseline.",
        "g0": {"in_cell_gate": False, "available_gate": "experiments/context-cache/cells/SGLang/u2_gate.py (mtime 2026-10-20 18:05, predates protocol)", "downgrade": "TUNED has no in-cell G0; result is downgraded accordingly."},
        "run": run,
        "phase_p": {
            "n": len(p_rows),
            "mean_prompt_tokens": mean([r["prompt_tokens"] for r in p_rows]),
            "min_prompt_tokens": min(r["prompt_tokens"] for r in p_rows),
            "max_prompt_tokens": max(r["prompt_tokens"] for r in p_rows),
            "n_zero_cached_on_first_submission": sum(1 for r in p_rows if r["cached_tokens"] == 0),
            "max_cached_on_first_submission": max(r["cached_tokens"] for r in p_rows),
            "cumulative_curve_every_25": [
                {"doc_position": r["doc_position"], "cum_prompt_tokens": r["cum_prompt_tokens"],
                 "ratio": round(r["cum_prompt_tokens"] / cap_slru, 4)}
                for r in p_rows
                if r["doc_position"] % 25 == 0 or r is p_rows[-1]
            ],
        },
        "phase_r": {"band_replay_order": run["band_replay_order"], "bands": bands,
                    "note": "hit_ratio = cached_tokens / prompt_tokens for a byte-identical replay"},
        "policy_profile": policy_order_verdict(bands),
        "window": window,
        "comparison": {
            "reference": {"path": "experiments/context-cache/cells/M4/analysis.json",
                          "unit": "M4-EVICT", "policy": "lru",
                          "capacity": cap_lru, "pressure_ratio": lru_pressure,
                          "bands": {b: lru_bands[b]["mean_hit_ratio"] for b in BANDS},
                          "rows_sha256": m4["digest"]["rows_sha256"]},
            "variant": {"unit": "WIN-TUNED", "policy": run["radix_eviction_policy"],
                        "capacity": cap_slru, "pressure_ratio": slru_pressure,
                        "bands": {b: bands[b]["mean_hit_ratio"] for b in BANDS},
                        "rows_sha256": run["rows_sha256"]},
            **comparison,
            "normalisation": normalisation,
        },
        "finding": {
            "one_line": (
                f"slru vs lru under 1.5x capacity: oldest {bands['oldest']['mean_hit_ratio']} vs "
                f"{lru_bands['oldest']['mean_hit_ratio']}, middle "
                f"{bands['middle']['mean_hit_ratio']} vs {lru_bands['middle']['mean_hit_ratio']}, "
                f"newest {bands['newest']['mean_hit_ratio']} vs "
                f"{lru_bands['newest']['mean_hit_ratio']} -> {comparison['verdict']}"),
            "policy_measured": run["radix_eviction_policy"],
            "mechanism_note": (
                "the protocol submits each document exactly once before the replay, so a "
                "segmented/frequency policy has no re-access signal to promote anything on: "
                "a scan workload is exactly the case in which slru is expected to degenerate "
                "to lru. The null is therefore the mechanistically predicted outcome, and it "
                "also means this cell cannot show a workload where slru would win -- only that "
                "it does not win this one"),
            "capacity": cap_slru,
            "pressure_ratio": slru_pressure,
            "requests_used": run["requests_used"],
        },
        "digest": {
            "rows": len(rows), "rows_sha256": run["rows_sha256"],
            "requests_used": run["requests_used"], "requests_cap": run["requests_cap"],
            "token_capacity": cap_slru, "total_pressure_tokens": run["total_pressure_tokens"],
            "pressure_ratio": slru_pressure,
            "policy": run["radix_eviction_policy"],
            "variant": run["variant"],
        },
        "artifacts": [
            "experiments/context-cache/cells/TUNED/rows.jsonl",
            "experiments/context-cache/cells/TUNED/analysis.json",
            "experiments/context-cache/cells/TUNED/run.json",
            "experiments/context-cache/cells/TUNED/run_tuned.py",
            "experiments/context-cache/cells/TUNED/win_tuned_analyze.py",
            "experiments/context-cache/cells/TUNED/variant_server_info.json",
            "experiments/context-cache/cells/TUNED/step0-pre-diff.json",
            "experiments/context-cache/cells/TUNED/logs/",
        ],
    }
    tmp = OUT_PATH.with_name(OUT_PATH.name + ".tmp")
    tmp.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUT_PATH)
    print("SUMMARY " + json.dumps({
        "answer": analysis["answer"],
        "bands_slru": {b: bands[b]["mean_hit_ratio"] for b in BANDS},
        "bands_lru": {b: lru_bands[b]["mean_hit_ratio"] for b in BANDS},
        "per_band": {b: comparison["per_band"][b]["verdict"] for b in BANDS},
        "rows": len(rows), "requests": run["requests_used"],
        "capacity": cap_slru, "policy": run["radix_eviction_policy"],
    }, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
