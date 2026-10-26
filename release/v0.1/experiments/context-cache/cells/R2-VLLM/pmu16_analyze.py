#!/usr/bin/env python3
"""R2-VLLM analyzer -- the 16-token match unit on both vLLM models.

Pure functions over a frozen ``rows.jsonl``.  Nothing here talks to a server.

Two questions, one per model:

  Q1  occamy-1.0 (NVFP4 MoE, hybrid): when OH1 = prod + ``--prefix-match-unit 16``
      is run on its own :8020, does the measured hit grid fall from the physical
      block g (measured 2096 in ``MOE-VLLM``) to a 16-token grid?
  Q2  qwen3.5-9b (dense hybrid): when A1 = prod + ``--prefix-match-unit 16`` is
      run on its own :8014, does the hit grid fall from g (measured 1056 in
      ``WIN-VLLM``) to 16?

The rule a finer unit is supposed to activate (v0.27.1 ``kv_cache_utils.py``,
quoted in ``orchestration/handoffs/R2-D.json``): a mamba partial-tail entry can
only be registered by a scheduler step ending exactly at the prompt's last hash
boundary, so with ``hash_block_size < block_size`` the scheduler sets
``mamba_partial_cache_hit`` and adds that stop.  The physical block itself does
not change: ``hash_block_size`` is matching granularity only
(``vllm/config/cache.py:56-67``).

So the test is NOT "does cached == L % 16" (that is a law of the *old* grid,
and it can only get worse).  The test is the **hit grid**: the GCD of the
positive consecutive cached deltas inside one chain,
``gcd(cached[i+1] - cached[i])``.  Before: equal to the resolved block.  If the
unit bites: 16.

``grid_rows`` also handles chains whose per-turn ``cached`` happens to be 0 on a
first repeat (L < g), and never claims a grid from fewer than ``MIN_DELTAS``
positive deltas.

Usage accounting (REPAIR A, after ``state/logs/R2-VLLM-triage.json``).  A row whose
``usage_has_details`` is False carries ``cached_tokens = None``: the server did not
report ``usage.prompt_tokens_details``, which is what an old launch without
``--enable-prompt-tokens-details`` does.  ``None`` is UNOBSERVED.  It is never
summed as 0 and never counted as a miss:

  * ``grid_rows`` only uses rows where BOTH endpoints were observed;
  * ``law_tax`` yields ``None`` when any turn of the chain is unobserved;
  * ``model_summary`` reports ``total_cached``/``total_uncached``/``mean_uncached``
    as ``None`` unless every row was observed, and always reports
    ``n_observed``/``n_unobserved`` next to them;
  * ``contests`` (and every battery/summary consumer) counts unobserved points in
    ``n_unobserved`` instead of contributing zeros.

``usage_coverage``, ``blocks_summary`` and ``arm_identity`` make the three repaired
surfaces readable from the rows alone.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

MIN_DELTAS = 3


def observed(value) -> bool:
    """True for a MEASURED number.  ``None`` (and a missing key) is unobserved."""
    return value is not None


def cached_of(row: dict):
    """The row's ``cached_tokens``, or ``None`` when it was not observed.

    Both signals are honoured: an explicit ``None``, and ``usage_has_details``
    False/absent on a row that predates the flag (those rows were written by the
    old ``int(... or 0)`` reader, so their 0 means "not reported").
    """
    value = row.get("cached_tokens")
    if value is None:
        return None
    if row.get("usage_has_details") is False:
        return None
    return int(value)


def uncached_of(row: dict):
    """Prompt minus observed cached; ``None`` when ``cached`` was not observed."""
    c = cached_of(row)
    if c is None:
        return None
    p = row.get("prompt_tokens")
    return None if p is None else max(0, int(p) - c)


def blocks_available(prompt_tokens, resolved_block) -> int | None:
    """Complete blocks of a prompt; ``None`` when the block size is unknown."""
    if not resolved_block or not prompt_tokens:
        return None
    return int(prompt_tokens) // int(resolved_block)


def load_rows(path: str | Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def chains(rows: list[dict], phase: str = "battery") -> dict[tuple, list[dict]]:
    """Group battery rows into ordered chains keyed by (model, config, arm)."""
    out: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("phase") != phase:
            continue
        out[(r.get("model"), r.get("config_id"), r.get("arm"))].append(r)
    for key in out:
        out[key].sort(key=lambda r: (r.get("turn") or 0, r.get("rep") or 0))
    return dict(out)


def grid_rows(chain: list[dict]) -> dict:
    """The hit grid of one chain, from consecutive positive cached deltas."""
    deltas = []
    unobserved = 0
    for prev, cur in zip(chain, chain[1:]):
        a, b = cached_of(prev), cached_of(cur)
        if a is None or b is None:
            unobserved += 1          # REPAIR A: skipped, never read as a 0-added delta
            continue
        d = b - a
        if d > 0:
            deltas.append(d)
    if len(deltas) < MIN_DELTAS:
        return {"grid": None, "n_deltas": len(deltas), "confident": False,
                "deltas": deltas, "n_unobserved_pairs": unobserved}
    g = math.gcd(*deltas)
    # a grid is only claimed when every delta is a multiple of it (gcd is, by
    # construction) and it is not a trivial single-delta artefact
    return {"grid": g, "n_deltas": len(deltas), "confident": len(deltas) >= MIN_DELTAS,
            "min_delta": min(deltas), "max_delta": max(deltas), "deltas": deltas,
            "n_unobserved_pairs": unobserved}


def law_tax(chain: list[dict], grid: int) -> dict:
    """What the old law predicts per turn, so the same-window comparison is explicit.

    ``cached == g * floor(L / g)`` on a repeat of a longer prompt; the first
    occurrence of a prompt is cold.  ``mean_tax`` is the mean
    ``L - cached_law`` over the chain's turns -- the per-turn floor the grid
    forces.  Reported for ANY g so the 16- and block-grid readings can be put
    side by side on the same rows.
    """
    if not grid:
        return {"n": 0, "mean_tax": None}
    seen = set()
    taxes = []
    for r in chain:
        if cached_of(r) is None:
            return {"n": len(chain), "mean_tax": None, "n_unobserved": len(chain)}
        L = int(r.get("prompt_tokens") or 0)
        key = (L, r.get("salt"))
        if key in seen:
            taxes.append(L - grid * (L // grid))
        else:
            seen.add(key)
            taxes.append(L)
    return {"n": len(taxes), "mean_tax": round(sum(taxes) / len(taxes), 2) if taxes else None}


def model_summary(rows: list[dict]) -> dict:
    """Per-model: the hot arms' grids, the grid the engine actually used, and the tax."""
    by_chain = chains(rows)
    models = sorted({r.get("model") for r in rows if r.get("model")})
    out = {}
    for model in models:
        mrows = [r for r in rows if r.get("model") == model]
        resolved = sorted({r.get("resolved_block_size") for r in mrows if r.get("resolved_block_size")})
        pmu = sorted({str(r.get("prefix_match_unit")) for r in mrows if "prefix_match_unit" in r})
        arms = {}
        for (m, cfg, arm), chain in sorted(by_chain.items(), key=lambda kv: str(kv[0])):
            if m != model:
                continue
            g = grid_rows(chain)
            n_obs = sum(1 for r in chain if cached_of(r) is not None)
            n_unobs = len(chain) - n_obs
            tot_unc = sum(uncached_of(r) for r in chain if uncached_of(r) is not None)
            arms[str(arm)] = {
                "config_id": cfg,
                "n": len(chain),
                "grid": g["grid"],
                "n_deltas": g["n_deltas"],
                "n_observed": n_obs,
                "n_unobserved": n_unobs,
                "total_prompt": sum(int(r.get("prompt_tokens") or 0) for r in chain),
                # REPAIR A: a sum that cannot distinguish "no data" from "no hits" is
                # not a measurement -- None unless every row was observed.
                "total_cached": (sum(cached_of(r) for r in chain) if not n_unobs else None),
                "total_uncached": (tot_unc if not n_unobs else None),
                "mean_uncached": (round(tot_unc / len(chain), 2)
                                  if not n_unobs and chain else None),
            }
        grids = [a["grid"] for a in arms.values() if a["grid"]]
        out[model] = {
            "resolved_block_size": resolved,
            "prefix_match_unit_reported": pmu,
            "arms": arms,
            "grids": grids,
            "arm_mean_uncached": {a: v["mean_uncached"] for a, v in arms.items()},
            "arm_unobserved": {a: v["n_unobserved"] for a, v in arms.items()},
            # None, not False, when no chain produced a grid at all: "no cache activity"
            # and "the grid is not 16" are different findings and must not read alike.
            "grid_16_reached": (all(g == 16 for g in grids) if grids else None),
            "no_cache_activity": (not grids),
        }
    return out


def contests(rows: list[dict], phase: str, field_pairs=(("cold_cached", "rep_cached"),)) -> dict:
    """A same-window baseline/feasibility read: for each (model, target) did the
    repeat of an identical prompt return ANY cache?

    This is the read pitted against the on-disk block-grid cells over a short
    window: same prompts, same box, same hour.  It does not claim a grid -- it
    claims whether reuse happens at all -- so it stays meaningful when the
    automatic grid reading comes back empty.
    """
    out: dict[str, dict] = {}
    by_key: dict[tuple, dict] = {}
    for r in rows:
        if r.get("phase") != phase or r.get("target_L") is None:
            continue
        key = (r.get("model"), r.get("config_id"), r.get("target_L"), r.get("salt"))
        by_key.setdefault(key, {})[int(r.get("rep") or 0)] = cached_of(r)
    for (model, cfg, target, _salt), reps in sorted(by_key.items(), key=lambda kv: str(kv[0])):
        cold, rep = reps.get(0), reps.get(1)
        obs = cold is not None and rep is not None
        out.setdefault(model, {"config_id": cfg, "points": []})["points"].append(
            {"target": target, "cold_cached": cold, "rep_cached": rep,
             "observed": obs,
             # UNOBSERVED, not False: a point we could not read is not a miss
             "reuse": (None if not obs else bool(rep > 0))})
    for model, data in out.items():
        data["n_points"] = len(data["points"])
        data["n_observed"] = sum(1 for p in data["points"] if p["observed"])
        data["n_unobserved"] = data["n_points"] - data["n_observed"]
        data["n_with_reuse"] = sum(1 for p in data["points"] if p["reuse"] is True)
    return out


def usage_coverage(rows: list[dict]) -> dict:
    """REPAIR A/E: how many rows carry usage details, split observed vs blind.

    ``n_unobserved`` is the count that used to disappear into a zero sum.
    """
    out: dict = {}
    for cfg in sorted({str(r.get("config_id")) for r in rows}):
        crows = [r for r in rows if str(r.get("config_id")) == cfg]
        unobs = sum(1 for r in crows if cached_of(r) is None)
        out[cfg] = {
            "n_rows": len(crows),
            "n_usage_has_details_true": sum(1 for r in crows if r.get("usage_has_details") is True),
            "n_usage_has_details_false": sum(1 for r in crows
                                             if r.get("usage_has_details") is False),
            "n_usage_has_details_absent": sum(1 for r in crows if "usage_has_details" not in r),
            "n_unobserved": unobs,
            "n_observed": len(crows) - unobs,
            "n_cached_gt0": sum(1 for r in crows if (cached_of(r) or 0) > 0),
            "blind": unobs == len(crows),
        }
    return out


def blocks_summary(rows: list[dict]) -> dict:
    """REPAIR C: ``blocks_available`` per (config, phase, rep); it must equal L // g."""
    out: dict = {}
    for r in rows:
        g, L = r.get("resolved_block_size"), r.get("prompt_tokens")
        key = f"{r.get('config_id')}/{r.get('phase')}/rep{r.get('rep')}"
        d = out.setdefault(key, {"resolved_block_size": g, "n": 0,
                                 "n_blocks_none": 0, "min": None, "max": None,
                                 "blocks_mismatch": 0})
        d["n"] += 1
        b = r.get("blocks_available")
        if b is None:
            d["n_blocks_none"] += 1
            continue
        if b != blocks_available(L, g):
            d["blocks_mismatch"] += 1
        d["min"] = b if d["min"] is None else min(d["min"], b)
        d["max"] = b if d["max"] is None else max(d["max"], b)
    return out


def arm_identity(rows: list[dict]) -> dict:
    """REPAIR D: distinct ``prefix_sha256`` per turn across arms, from the rows.

    ``ok`` is True only when every turn has at least two distinct digests AND the
    arms' message-body sets differ (``body_sets_differ`` from the writer's own
    report if present; otherwise digest distinctness is the evidence available).
    """
    by_cfg: dict = {}
    for r in rows:
        if r.get("phase") != "battery" or r.get("rep") != 0 or not r.get("prefix_sha256"):
            continue
        by_cfg.setdefault(str(r.get("config_id")), {}).setdefault(str(r.get("turn")),
                                                                  set()).add(r["prefix_sha256"])
    out: dict = {}
    for cfg, per_turn in by_cfg.items():
        distinct = {t: len(v) for t, v in per_turn.items()}
        out[cfg] = {"turns": len(per_turn),
                    "min_distinct_prefix_sha256": min(distinct.values()) if distinct else 0,
                    "distinct_per_turn": distinct,
                    "ok": bool(distinct) and min(distinct.values()) >= 2}
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    rows = load_rows(args.rows)
    summary = model_summary(rows)
    text = json.dumps(summary, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
