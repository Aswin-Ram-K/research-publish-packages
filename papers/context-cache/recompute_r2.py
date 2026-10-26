#!/usr/bin/env python3
"""Recompute every Round-2 number in ``papers/context-cache/CLAIMS.md`` from the raw rows.

Usage::

    .venv/bin/python papers/context-cache/recompute_r2.py all
    .venv/bin/python papers/context-cache/recompute_r2.py C64

This is the Round-2 sibling of ``recompute.py``.  It exists because the R2 claims
(C64-C66) are computed from row files ``recompute.py`` does not read: the repaired
padding cell, the SYS-OPT version round, and the track-interval cells.  Every value is
re-derived here from the raw ``rows*.jsonl`` files under
``experiments/context-cache/cells/``; nothing is read from a handoff, an analysis JSON
or a rendered document, and the values this file compares against are the ones published
in ``CLAIMS.md`` and ``MANUSCRIPT.md`` -- so a mismatch is a paper defect, not a runner
defect.

Nothing is written and no live request is made.
"""
from __future__ import annotations

import json
import math
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CELLS = ROOT / "experiments" / "context-cache" / "cells"

#: Bootstrap parameters as the cells themselves declare them.  R2 arms use the recipe's
#: seed (state/r2-prompt-matrix.json ``recipe.bootstrap.seed``); SYS-OPT uses its own.
R2_SEED, R2_B = 20261020, 10000
SYSOPT_SEED, SYSOPT_B = 20251024, 10000

#: Overrides the red/green guard installs to falsify a source.  ``None`` means "read the
#: real file"; the guard sets them, re-derives, and restores them.
REPAD_ROWS: list[dict] | None = None
TRACK_ROOT = CELLS / "TRACK-INTERVAL"
R2PROMPT_ROOT = CELLS / "R2-PROMPT"


# --------------------------------------------------------------------------- #
# Loading -- raw rows only
# --------------------------------------------------------------------------- #
def read_jsonl(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def countable(r: dict) -> bool:
    """A row whose two counters are both integers -- a cold row may write ``unavailable``.

    Those rows are excluded and counted, never coerced: a row that could not report its
    cache state cannot testify about padding.
    """
    return _is_int(r.get("prompt_tokens")) and _is_int(r.get("cached_tokens"))


def _is_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def uncached(r: dict) -> int:
    """Uncached tokens for a countable row, from the row's own two counters."""
    if not countable(r):
        raise ValueError(f"row is not countable: cached_tokens={r.get('cached_tokens')!r}")
    return int(r["prompt_tokens"]) - int(r["cached_tokens"])


def paired_boot(a: dict[int, float], b: dict[int, float],
                seed: int, b_n: int) -> dict:
    """Percentile bootstrap over TURNS of the paired per-turn difference ``a - b``.

    The turn is the independent unit: the four arms are salt-separated replicates of one
    schedule, and this repository's convention (C62, C63) is to resample turns, not
    (arm, turn) rows.
    """
    turns = sorted(set(a) & set(b))
    diffs = [a[t] - b[t] for t in turns]
    rnd = random.Random(seed)
    n = len(diffs)
    stats = sorted(sum(diffs[rnd.randrange(n)] for _ in range(n)) / n for _ in range(b_n))
    lo, hi = stats[int(0.025 * b_n)], stats[int(0.975 * b_n) - 1]
    return {
        "n_pairs": n,
        "mean": statistics.fmean(diffs),
        "ci95": (lo, hi),
        "excludes_zero": bool(lo > 0 or hi < 0),
    }


def boot_mean(vals: list[float], seed: int = R2_SEED, b_n: int = R2_B) -> tuple[float, float]:
    rnd = random.Random(seed)
    n = len(vals)
    stats = sorted(sum(vals[rnd.randrange(n)] for _ in range(n)) / n for _ in range(b_n))
    return stats[int(0.025 * b_n)], stats[int(0.975 * b_n) - 1]


def boot_mean_c63(vals: list[float]) -> tuple[float, float]:
    """C63's interval, with C63's own recipe (seed 20251023, 10,000 resamples).

    Reproduces ``recompute.py C63``'s ``_c63_boot`` to the last digit -- same seed, same
    resampling over the 71 turns, and the same ``round(..., 1)`` applied BEFORE the 1-dp
    truncation -- so the two runners pin one number rather than two neighbouring ones.
    """
    rnd = random.Random(20251023)
    n = len(vals)
    means = sorted(sum(vals[rnd.randrange(n)] for _ in range(n)) / n for _ in range(10000))
    return round(means[int(0.025 * 10000)], 1), round(means[int(0.975 * 10000)], 1)


def arms_of(rows: list[dict], arm_key: str = "arm") -> dict[str, dict[int, dict]]:
    out: dict[str, dict[int, dict]] = {}
    for r in rows:
        out.setdefault(r[arm_key], {})[int(r["turn"])] = r
    return out


def arm_mean(by_turn: dict[int, dict]) -> tuple[float, tuple[float, float], float]:
    vals = [float(uncached(r)) for r in by_turn.values()]
    # ``hit`` is cached / prompt WEIGHTED over the cell, i.e. a ratio of totals: on a cold
    # row the hit term is 0 exactly, so leaving cold rows out would inflate it.
    pt = sum(int(r["prompt_tokens"]) for r in by_turn.values())
    ca = sum(int(r["cached_tokens"]) for r in by_turn.values())
    return statistics.fmean(vals), boot_mean(vals), (ca / pt if pt else 0.0)


# --------------------------------------------------------------------------- #
# C64 -- grid padding costs, on the one-send-per-turn repair
# --------------------------------------------------------------------------- #
def c64() -> dict:
    """P2 (grid-aligned padding) against P0 and P1 in ``cells/P2-REPAD``.

    The original R2-PROMPT P2 arm resent a turn whenever the pad came out misaligned, so
    its recorded ``cached_tokens`` was the previous send's prompt -- a same-turn self-hit,
    not a padding effect.  P2-REPAD precomputes the pad from the same-run P1 length, so
    every row is a single send (``requests_sent == 1``).  This function asserts that
    property on the rows before it uses any of them, then measures the three arms.
    """
    rows = REPAD_ROWS if REPAD_ROWS is not None else read_jsonl(CELLS / "P2-REPAD" / "rows.jsonl")
    multi = [r for r in rows if int(r.get("requests_sent", 0)) != 1]
    corrected = [r for r in rows if int(r.get("corrections") or 0) != 0
                 or r.get("had_correction")]
    bad = [r for r in rows if int(r.get("http_status") or 0) != 200]
    if multi or corrected or bad:
        raise ValueError(f"C64: the one-send premise fails ({len(multi)} multi-send, "
                         f"{len(corrected)} corrected, {len(bad)} non-200)")
    arms = arms_of([r for r in rows if countable(r)])
    for arm in ("P0", "P1", "P2"):
        if arm not in arms:
            raise ValueError(f"C64: arm {arm!r} absent from P2-REPAD")
    out: dict[str, object] = {"n_rows": len(rows), "multi_send_rows": len(multi),
                              "corrected_rows": len(corrected), "non_200": len(bad),
                              "non_countable_rows": len(rows) - sum(
                                  1 for r in rows if countable(r))}
    per_arm: dict[str, dict[int, float]] = {}
    for arm in ("P0", "P1", "P2"):
        mean, ci, hit = arm_mean(arms[arm])
        per_arm[arm] = {t: float(uncached(r)) for t, r in arms[arm].items()}
        out[f"{arm}_n"] = len(arms[arm])
        out[f"{arm}_mean_uncached_per_turn"] = round(mean, 4)
        out[f"{arm}_ci95"] = (round(ci[0], 3), round(ci[1], 3))
        out[f"{arm}_hit"] = round(hit, 6)
    for lo_arm, hi_arm in (("P2", "P1"), ("P2", "P0"), ("P1", "P0")):
        d = paired_boot(per_arm[lo_arm], per_arm[hi_arm], R2_SEED, R2_B)
        tag = f"{lo_arm}_minus_{hi_arm}"
        out[f"{tag}_delta"] = round(d["mean"], 4)
        out[f"{tag}_ci95"] = (round(d["ci95"][0], 3), round(d["ci95"][1], 3))
        out[f"{tag}_excludes_zero"] = d["excludes_zero"]
        out[f"{tag}_n_pairs"] = d["n_pairs"]
    out["P2_over_P1_ratio_of_means"] = round(
        out["P2_mean_uncached_per_turn"] / out["P1_mean_uncached_per_turn"], 6)
    # The pad itself, and what alignment actually recovered.
    typical = arms["P2"]
    pad = [int(r["pad_tokens"]) for r in typical.values()]
    aligned = sum(1 for r in typical.values() if int(r["prompt_tokens"]) % 64 == 0)
    out["P2_rows"] = len(typical)
    out["P2_pad_total"] = sum(pad)
    out["P2_pad_mean"] = round(sum(pad) / len(typical), 4)
    out["P2_pad_min"], out["P2_pad_max"] = min(pad), max(pad)
    out["P2_rows_aligned_on_64"] = aligned
    gains = Counter()
    for t, r2 in typical.items():
        r1 = arms["P1"].get(t)
        if r1 is None:
            continue
        gains[int(r2["cached_tokens"]) - int(r1["cached_tokens"])] += 1
    out["extra_cached_vs_P1"] = sorted(gains.items())
    recovered = statistics.fmean(
        int(typical[t]["cached_tokens"]) - int(arms["P1"][t]["cached_tokens"])
        for t in typical if t in arms["P1"])
    out["extra_cached_vs_P1_mean"] = round(recovered, 4)
    out["pad_recovered_fraction"] = round(recovered / statistics.fmean(pad), 6)
    return out


# --------------------------------------------------------------------------- #
# C63 -- the engine/model split, re-derived from the four cells' own rows
# --------------------------------------------------------------------------- #
def _c63_unc(r: dict) -> float:
    """A C63 row's uncached-token count, as ``recompute.py C63`` reads it.

    The SGLang cells write ``uncached`` and the R2 vLLM cell writes ``uncached_tokens``;
    a cell that carries neither is refused rather than re-derived from the two counters,
    because C63's published values are those fields (the cell means the paper quotes).
    """
    v = r.get("uncached")
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        v = r.get("uncached_tokens")
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ValueError(f"C63: row (arm={r.get('arm')}, turn={r.get('turn')}) carries no "
                         "uncached count")
    return float(v)


def c63() -> dict:
    """Every number in CLAIMS.md C63, re-derived from the four cells' own rows.

    This is the pin that makes the paper's headline claim (the engine, not the model, sets
    the per-turn uncached bill) falsifiable from ``CLAIMS.md``: before it, C63's values
    existed only as prose in its cells.  Each cell is reduced to one number per turn -- the
    mean over its four replicate arms (R/A/C/H) of the row's uncached count -- and the cells
    combine as a 2x2 factorial: the engine effect is ``vllm - sglang`` averaged over the
    two models, the model effect is ``qwen3.5-9b - occamy-1.0`` averaged over the two
    engines, and the interaction is the textbook half-difference, identically the engine
    effect on the dense model minus the engine effect on the MoE model.  Every interval is
    a percentile bootstrap over the 71 turns (10,000 resamples, seed 20251023) -- the
    resampling unit C62/C65 use, since the arms are replicates of one schedule.

    Nothing is imported from ``recompute.py``: this runner must be able to disagree with it.
    """
    models = ("occamy-1.0", "qwen3.5-9b")
    engines = ("vllm", "sglang")
    arms = ("R", "A", "C", "H")
    #: (path, config_id, stack, depth).  ``G3`` carries its S0 battery TWICE -- once at
    #: ``depth=32k`` and once at ``depth=64k`` -- so the depth filter is what keeps the cell
    #: at 284 rows; without it the MoE-SGLang cell reads two schedules as one.
    spec = {
        ("occamy-1.0", "vllm"): (CELLS / "MOE-VLLM" / "rows.jsonl", "V3", "vllm", None),
        ("occamy-1.0", "sglang"): (CELLS / "G3" / "rows.jsonl", "S0", "sglang", "32k"),
        ("qwen3.5-9b", "vllm"): (C63_R2_PATH[0], "O4", "vllm-0.27.1", None),
        ("qwen3.5-9b", "sglang"): (CELLS / "DENSE-SGL" / "rows.jsonl", "P1", "sglang", "32k"),
    }
    out: dict[str, object] = {}
    panel: dict[tuple[str, str], dict[int, float]] = {}
    for (model, engine), (path, cfg, stack, depth) in spec.items():
        rows = []
        for r in read_jsonl(path):
            if r.get("config_id") != cfg or r.get("arm") not in arms:
                continue
            if not 1 <= int(r["turn"]) <= 71:
                continue
            if r.get("stack") != stack:
                continue
            if depth is not None and r.get("depth") != depth:
                continue
            if r.get("phase") not in (None, "battery"):
                continue
            if int(r.get("http_status") or r.get("status") or 0) != 200:
                continue
            rows.append(r)
        if len(rows) != len(arms) * 71:
            raise ValueError(f"C63: cell {model}/{engine} ({cfg}) has {len(rows)} rows, "
                             f"expected {len(arms) * 71}")
        by: dict[int, list[float]] = {}
        for r in rows:
            by.setdefault(int(r["turn"]), []).append(_c63_unc(r))
        if sorted(by) != list(range(1, 72)):
            raise ValueError(f"C63: cell {model}/{engine} covers {len(by)} turns, not 71")
        panel[(model, engine)] = {t: statistics.fmean(v) for t, v in by.items()}
        tag = f"{model}_{engine}"
        out[f"cell_rows_{tag}"] = len(rows)
        out[f"cell_unc_{tag}"] = round(statistics.fmean(by_vals for v in by.values()
                                                       for by_vals in v), 4)
        pt = sum(int(r["prompt_tokens"]) for r in rows)
        out[f"cell_hit_{tag}"] = round(sum(int(r["cached_tokens"]) for r in rows) / pt, 6)
        hot = [int(r["cached_tokens"]) for r in rows if int(r["cached_tokens"]) > 0]
        out[f"cell_hot_gcd_{tag}"] = _gcd(hot)
    out["n_rows_total"] = sum(int(out[f"cell_rows_{m}_{e}"]) for m in models for e in engines)

    turns = sorted(panel[("occamy-1.0", "vllm")])
    dv = panel[("qwen3.5-9b", "vllm")]
    ds = panel[("qwen3.5-9b", "sglang")]
    mv = panel[("occamy-1.0", "vllm")]
    ms = panel[("occamy-1.0", "sglang")]
    series = {
        "engine_effect": {t: ((dv[t] - ds[t]) + (mv[t] - ms[t])) / 2 for t in turns},
        "model_effect": {t: ((dv[t] - mv[t]) + (ds[t] - ms[t])) / 2 for t in turns},
        "interaction_effect": {t: ((dv[t] - ds[t]) - (mv[t] - ms[t])) / 2 for t in turns},
        "engine_within_moe": {t: mv[t] - ms[t] for t in turns},
        "engine_within_dense": {t: dv[t] - ds[t] for t in turns},
        "model_within_vllm": {t: dv[t] - mv[t] for t in turns},
        "model_within_sglang": {t: ds[t] - ms[t] for t in turns},
    }
    #: The precision C63 publishes each contrast at -- the main effects and the engine
    #: within each model at 2 dp, the model within each engine and every ratio at 4 dp.
    #: A 4-dp interval would be a figure the paper never states.
    digits = {"engine_effect": 2, "model_effect": 2, "interaction_effect": 2,
              "engine_within_moe": 2, "engine_within_dense": 2,
              "model_within_vllm": 2, "model_within_sglang": 2}
    for name, ser in series.items():
        vals = [ser[t] for t in turns]
        out[name] = round(statistics.fmean(vals), digits.get(name, 4))
        out[f"{name}_ci95"] = boot_mean_c63(vals)
        out[f"{name}_positive_turns"] = sum(1 for v in vals if v > 0)
        out[f"{name}_n_turns"] = len(vals)
    grand = statistics.fmean(float(out[f"cell_unc_{m}_{e}"])
                             for m in models for e in engines)
    out["grand_mean"] = round(grand, 4)
    out["ratio_engine_over_model"] = round(
        float(out["engine_effect"]) / float(out["model_effect"]), 4)
    out["engine_share_of_grand"] = round(float(out["engine_effect"]) / grand, 4)
    out["model_share_of_grand"] = round(float(out["model_effect"]) / grand, 4)
    #: divided from the UNROUNDED per-turn means, not from the printed significands --
    #: identical to ``recompute.py C63``'s rule, and the reason this is not simply
    #: ``model_within_vllm / model_within_sglang`` of the rounded values (test_c63_ratio_raw_operands)
    m_vllm_raw = statistics.fmean([series["model_within_vllm"][t] for t in turns])
    m_sgl_raw = statistics.fmean([series["model_within_sglang"][t] for t in turns])
    out["ratio_model_effect_vllm_over_sglang"] = round(m_vllm_raw / m_sgl_raw, 4)
    for model in models:
        tag = "moe" if model == models[0] else "dense"
        out[f"ratio_engine_over_{tag}"] = round(
            float(out[f"cell_unc_{model}_vllm"]) / float(out[f"cell_unc_{model}_sglang"]), 4)
    out["ratio_engine_mean"] = round(statistics.fmean(
        [out["ratio_engine_over_moe"], out["ratio_engine_over_dense"]]), 4)
    for engine in engines:
        out[f"ratio_model_over_{engine}"] = round(
            float(out[f"cell_unc_{models[1]}_{engine}"])
            / float(out[f"cell_unc_{models[0]}_{engine}"]), 4)
    out["ratio_model_mean"] = round(statistics.fmean(
        [out["ratio_model_over_vllm"], out["ratio_model_over_sglang"]]), 4)
    # The same decomposition arm by arm: replication evidence, not a fifth cell.
    rows_by_cell = {}
    for (model, engine), (path, cfg, stack, depth) in spec.items():
        rows_by_cell[(model, engine)] = {}
        for r in read_jsonl(path):
            if (r.get("config_id") == cfg and r.get("arm") in arms
                    and 1 <= int(r["turn"]) <= 71 and r.get("stack") == stack
                    and (depth is None or r.get("depth") == depth)
                    and r.get("phase") in (None, "battery")
                    and int(r.get("http_status") or r.get("status") or 0) == 200):
                rows_by_cell[(model, engine)].setdefault(r["arm"], {})[
                    int(r["turn"])] = _c63_unc(r)
    # replicate-arm check, same algebra as the cell-level contrasts, one arm at a time
    rep = {"engine_effect": [], "model_effect": []}
    for arm in arms:
        dv_a = rows_by_cell[("qwen3.5-9b", "vllm")][arm]
        ds_a = rows_by_cell[("qwen3.5-9b", "sglang")][arm]
        mv_a = rows_by_cell[("occamy-1.0", "vllm")][arm]
        ms_a = rows_by_cell[("occamy-1.0", "sglang")][arm]
        rep["engine_effect"].append(round(statistics.fmean(
            (dv_a[t] - ds_a[t] + mv_a[t] - ms_a[t]) / 2 for t in turns), 1))
        rep["model_effect"].append(round(statistics.fmean(
            (dv_a[t] - mv_a[t] + ds_a[t] - ms_a[t]) / 2 for t in turns), 1))
    # Republished as a BAND, which is how the cell writes it: a 1-dp interval of arm values
    # cannot be asserted without restating the four arms, so both are pinned.
    out["replicate_arms_engine"] = tuple(rep["engine_effect"])
    out["replicate_arms_model"] = tuple(rep["model_effect"])
    out["replicate_band_engine"] = (min(rep["engine_effect"]), max(rep["engine_effect"]))
    out["replicate_band_model"] = (min(rep["model_effect"]), max(rep["model_effect"]))
    out["replicate_arm_names"] = arms
    return out


# --------------------------------------------------------------------------- #
# C67 -- the prompt-layout round, as it now stands
# --------------------------------------------------------------------------- #
PROMPT_ARMS = ("P0", "P1", "P2", "P3")


def c67() -> dict:
    """What the Round-2 prompt-layout matrix measured, after P2 was withdrawn.

    ``cells/R2-PROMPT/<O>/rows.jsonl`` is the multi-arm battery; ``cells/P2-REPAD`` is
    the one-send repair that decides P2.  Three facts are claimed here and nothing else:

    * the battery is complete -- four setups x four arms x 71 turns of usable rows;
    * the pointer layout (P1) and the edit control (P3) are null against the full-history
      reference (P0) in the two production setups, and P1 is *not* null on the vLLM dense
      setup, where it costs;
    * one cell's stored summary disagrees with its own rows, and that cell is named.

    Every arm mean is re-derived from the rows; the ``deltas`` object each cell keeps on
    disk is compared against the re-derivation so a cell's own summary cannot silently
    drift from the data it claims to summarise.
    """
    out: dict[str, object] = {}
    per_setup: dict[str, dict[str, dict[int, float]]] = {}
    for cell in ("O1", "O2", "O3", "O4"):
        rows = read_jsonl(R2PROMPT_ROOT / cell / "rows.jsonl")
        ok = [r for r in rows if int(r.get("http_status") or 0) == 200 and countable(r)]
        arms = arms_of(ok)
        per_setup[cell] = {}
        out[f"{cell}_rows"] = len(rows)
        out[f"{cell}_usable_rows"] = len(ok)
        out[f"{cell}_non_200"] = sum(1 for r in rows if int(r.get("http_status") or 0) != 200)
        out[f"{cell}_arms_present"] = tuple(a for a in PROMPT_ARMS if a in arms)
        out[f"{cell}_engine"] = sorted({r.get("stack") for r in ok})
        for arm in PROMPT_ARMS:
            if arm not in arms:
                continue
            per_setup[cell][arm] = {t: float(uncached(r)) for t, r in arms[arm].items()}
            vals = list(per_setup[cell][arm].values())
            out[f"{cell}_{arm}_n"] = len(vals)
            out[f"{cell}_{arm}_mean"] = round(statistics.fmean(vals), 4)
        for hi, lo in (("P1", "P0"), ("P3", "P1")):
            if hi not in per_setup[cell] or lo not in per_setup[cell]:
                continue
            d = paired_boot(per_setup[cell][hi], per_setup[cell][lo], R2_SEED, R2_B)
            tag = f"{cell}_{hi}_minus_{lo}"
            out[f"{tag}_delta"] = round(d["mean"], 4)
            out[f"{tag}_ci95"] = (round(d["ci95"][0], 3), round(d["ci95"][1], 3))
            out[f"{tag}_excludes_zero"] = d["excludes_zero"]
            out[f"{tag}_n_pairs"] = d["n_pairs"]

    # Cells whose stored summary disagrees with their own rows.
    disagree = []
    for cell in ("O1", "O2", "O3", "O4"):
        path = R2PROMPT_ROOT / cell / "analysis.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        deltas = doc.get("deltas") or {}
        for key, stored in deltas.items():
            if not isinstance(stored, dict):
                continue
            pairs = [(a, b) for a in PROMPT_ARMS for b in PROMPT_ARMS
                     if key.replace(" ", "") in (f"{a}/{b}", f"{a}-{b}", f"{a}_{b}")]
            if not pairs:
                continue
            hi, lo = pairs[0]
            if hi not in per_setup[cell] or lo not in per_setup[cell]:
                continue
            mine = paired_boot(per_setup[cell][hi], per_setup[cell][lo], R2_SEED, R2_B)["mean"]
            theirs = stored.get("delta_unc_per_turn")
            if theirs is None:
                continue
            if abs(mine - float(theirs)) > 0.01:
                disagree.append((cell, key, round(float(theirs), 4), round(mine, 4)))
    out["cells_whose_summary_disagrees_with_rows"] = tuple(disagree)
    return out


# --------------------------------------------------------------------------- #
# C68 -- configuration identity: distinct serving setups, distinct bills
# --------------------------------------------------------------------------- #
CONFIG_SENSITIVE = ("config_id", "config_sha256", "model", "setup", "stack", "ts", "wall_ms",
                    "salt", "prefix_sha256", "prompt_sha256", "ts_utc")


def c68() -> dict:
    """Whether each Round-2 battery is what its directory says it is.

    Two separate questions, both answered from the rows:

    1. **Per-setup integrity.**  Distinct ``config_sha256``, distinct model, distinct
       time window, and -- the one that matters -- non-constant ``cached_tokens`` and
       ``uncached_tokens``.  A cell that was never served by its own endpoint cannot
       produce those.

    2. **Cross-setup identity.**  Distinct setups on different models are different
       endpoints, so the same prompt DOES hit different amounts of cache on them.  Two
       cells whose ``cached_tokens`` and ``uncached_tokens`` agree row for row are
       therefore the same measurement filed twice, whatever their timestamps say.  Those
       fields are excluded from the identity comparison; everything else must differ.
    """
    out: dict[str, object] = {}
    cells = {c: read_jsonl(R2PROMPT_ROOT / c / "rows.jsonl") for c in ("O1", "O2", "O3", "O4")}
    for cell, rows in cells.items():
        ok = [r for r in rows if int(r.get("http_status") or 0) == 200 and countable(r)]
        out[f"{cell}_config_sha256"] = tuple(sorted({r.get("config_sha256") for r in ok}))
        out[f"{cell}_model"] = tuple(sorted({r.get("model") for r in ok}))
        out[f"{cell}_distinct_cached_values"] = len({int(r["cached_tokens"]) for r in ok})
        out[f"{cell}_distinct_uncached_values"] = len({int(uncached(r)) for r in ok})
        out[f"{cell}_ts_first"] = min((r.get("ts") for r in ok if r.get("ts")), default=None)
        out[f"{cell}_ts_last"] = max((r.get("ts") for r in ok if r.get("ts")), default=None)
        out[f"{cell}_distinct_prompt_sha256"] = len({r.get("prompt_sha256") for r in ok})
        # The layout arms must be DISTINCT renders inside one cell: a cell whose P1 rows
        # repeat P0's prompt digest is not measuring a second layout.
        by_arm = arms_of(ok)
        for arm in ("P1", "P2", "P3"):
            if arm in by_arm and "P0" in by_arm:
                out[f"{cell}_{arm}_rows_repeating_P0_digest"] = sum(
                    1 for t in by_arm[arm]
                    if by_arm[arm][t].get("prompt_sha256") == by_arm["P0"].get(t, {}).get("prompt_sha256"))

    def keyed(rows):
        return {(r["arm"], int(r["turn"])): r for r in rows
                if int(r.get("http_status") or 0) == 200 and countable(r)}

    #: configuration counters are excluded from the identity test: two rows with the same
    #: prompt and the same prompt length but DIFFERENT cached_tokens were served by two
    #: different caches, whatever their timestamps claim.
    CONFIG_FIELDS = ("config_id", "config_sha256", "model", "setup", "stack", "wall_ms")

    pairs = [("O1", "O2"), ("O1", "O3"), ("O1", "O4"), ("O2", "O3"), ("O2", "O4"), ("O3", "O4")]
    merged, distinct = [], []
    twice = []
    for a, b in pairs:
        ka, kb = keyed(cells[a]), keyed(cells[b])
        if set(ka) != set(kb):
            continue
        tag = f"{a}_vs_{b}"
        same_prompt = sum(1 for k in ka if ka[k].get("prompt_sha256") == kb[k].get("prompt_sha256"))
        cache_differs = sum(1 for k in ka if int(ka[k]["cached_tokens"]) != int(kb[k]["cached_tokens"])
                            or int(uncached(ka[k])) != int(uncached(kb[k])))
        fields_differ = tuple(f for f in CONFIG_FIELDS
                              if all(ka[k].get(f) != kb[k].get(f) for k in ka))
        out[f"{tag}_shared_keys"] = len(set(ka) & set(kb))
        out[f"{tag}_rows_same_prompt"] = same_prompt
        out[f"{tag}_rows_with_different_cache_counters"] = cache_differs
        out[f"{tag}_config_fields_all_differ"] = fields_differ
        # Two independent testimonies that these are one measurement, two files:
        # the prompts are the same bytes, and everything that names the configuration
        # differs row for row.  Either alone is weak; together they are decisive, because
        # two endpoints serving different models cannot produce one identical prompt and
        # one identical cache bill on the same turn.
        if fields_differ and same_prompt == len(ka):
            twice.append((a, b))
        elif fields_differ:
            distinct.append((a, b))
        elif same_prompt == len(ka):
            merged.append((a, b))
        else:
            distinct.append((a, b))
    out["cell_pairs_counted_twice"] = tuple(twice)
    out["cell_pairs_with_distinct_configuration"] = tuple(distinct)
    out["cell_pairs_not_resolved"] = tuple(merged)
    out["n_cells_distinct"] = 4 - 2 * len(twice)

    # Per-cell digest of the seeded state the cell ran on, and whether any two share it.
    seeds = {}
    for cell, rows in cells.items():
        ok = [r for r in rows if int(r.get("http_status") or 0) == 200]
        seeds[cell] = tuple(sorted({r.get("salt") for r in ok if r.get("salt")}))
    out["cell_salts"] = seeds
    out["cells_sharing_a_salt"] = tuple(
        (a, b, sorted(set(seeds[a]) & set(seeds[b])))
        for i, a in enumerate(seeds) for b in list(seeds)[i + 1:]
        if set(seeds[a]) & set(seeds[b]))
    return out


# --------------------------------------------------------------------------- #
# C65 -- the engine/model 2x2 survives the Round-2 questions
# --------------------------------------------------------------------------- #
#: The Round-2 dense vLLM cell's row file.  A one-element list, not a path, so the
#: red->green guard can point the panel at a falsified copy without editing any caller.
C65_R2_PATH: list[Path] = [ROOT / "state" / "config" / "rows.jsonl"]
#: C63 reads the same Round-2 cell; its own hook so a falsified copy can be pointed at it.
C63_R2_PATH: list[Path] = C65_R2_PATH

def c65() -> dict:
    """The four-cell matrix, re-derived from the same rows ``recompute.py C63`` reads.

    Reported separately from C63 because C63's expected values are frozen against the
    paper and this runner must be able to disagree with them: it reconstructs the panel
    without importing ``recompute.py`` so a defect in that module cannot hide here.
    ``state/config/rows.jsonl`` is the Round-2 dense vLLM cell and is filtered on its own
    ``stack`` field (``vllm-0.27.1``), which is what distinguishes it from the Round-1
    rows that carry no stack.
    """
    spec = (
        ("occamy-1.0", "vllm", CELLS / "MOE-VLLM" / "rows.jsonl", "V3", "vllm"),
        ("occamy-1.0", "sglang", CELLS / "G3" / "rows.jsonl", "S0", "sglang"),
        ("qwen3.5-9b", "vllm", C65_R2_PATH[0], "O4", "vllm-0.27.1"),
        ("qwen3.5-9b", "sglang", CELLS / "DENSE-SGL" / "rows.jsonl", "P1", "sglang"),
    )
    turns = 71
    arms = ("R", "A", "C", "H")
    panel: dict[tuple[str, str], list[dict]] = {}
    for model, engine, path, cfg, stack in spec:
        rs = []
        for r in read_jsonl(path):
            if r.get("config_id") != cfg or r.get("arm") not in arms:
                continue
            if int(r.get("turn") or 0) < 1 or int(r.get("turn")) > turns:
                continue
            if stack == "vllm-0.27.1":
                if r.get("stack") != stack:
                    continue
            elif r.get("stack") != stack or r.get("depth") != "32k":
                continue
            if r.get("phase") not in (None, "battery"):
                continue
            if int(r.get("http_status") or r.get("status") or 0) != 200 or not countable(r):
                continue
            rs.append(r)
        if len(rs) != len(arms) * turns:
            raise ValueError(f"C65: {(model, engine)} has {len(rs)} rows, expected {len(arms) * turns}")
        panel[(model, engine)] = rs

    # Per-turn cell mean over the four replicate arms == the turn is the unit.
    def per_turn(rs: list[dict]) -> dict[int, float]:  # noqa: D401
        by: dict[int, list[float]] = {}
        for r in rs:
            by.setdefault(int(r["turn"]), []).append(float(uncached(r)))
        return {t: statistics.fmean(v) for t, v in by.items()}

    cell = {k: per_turn(rs) for k, rs in panel.items()}
    out: dict[str, object] = {}
    for (model, engine), rs in panel.items():
        pt = sum(int(r["prompt_tokens"]) for r in rs)
        ca = sum(int(r["cached_tokens"]) for r in rs)
        unc = [float(uncached(r)) for r in rs]
        out[f"cell_unc_{model}_{engine}"] = round(statistics.fmean(unc), 4)
        out[f"cell_hit_{model}_{engine}"] = round(ca / pt, 6)
        hot = [int(r["cached_tokens"]) for r in rs if int(r["cached_tokens"]) > 0]
        # The hot gcd is a CACHE UNIT only when it is at least one 64-token page and is a
        # multiple of it; below that it is an arithmetic artefact of a handful of hits and
        # is reported as such rather than as a block size.
        g = _gcd(hot)
        out[f"cell_hot_gcd_{model}_{engine}"] = g
        out[f"cell_hot_gcd_is_cache_unit_{model}_{engine}"] = bool(g >= 64 and g % 64 == 0)
        out[f"cell_rows_{model}_{engine}"] = len(rs)

    # 2x2 factorial, per turn.  `interaction` is the textbook half-difference
    #   [ (vLLM:dense - vLLM:moe) - (SGLang:dense - SGLang:moe) ] / 2 ,
    # which is identically the engine effect on the dense model minus the engine effect on
    # the MoE model, and identically `model_vllm - model_sglang`.  The /2 is not cosmetic:
    # without it the quantity is twice the model-within-engine contrast that C63's prose
    # sentences quote, and a runner that drops it disagrees with C63 by exactly 2x.
    dv = cell[("qwen3.5-9b", "vllm")]
    ds = cell[("qwen3.5-9b", "sglang")]
    mv = cell[("occamy-1.0", "vllm")]
    ms = cell[("occamy-1.0", "sglang")]
    turns_of = sorted(mv)
    eng = {t: ((dv[t] - ds[t]) + (mv[t] - ms[t])) / 2 for t in turns_of}
    mod = {t: ((dv[t] - mv[t]) + (ds[t] - ms[t])) / 2 for t in turns_of}
    inter = {t: ((dv[t] - ds[t]) - (mv[t] - ms[t])) / 2 for t in turns_of}
    effects = {"engine": eng, "model": mod, "interaction": inter}
    # The two "within" contrasts the manuscript quotes as sentences, measured directly
    # rather than read off the interaction.
    for tag, series in (("engine_within_moe", {t: mv[t] - ms[t] for t in turns_of}),
                        ("engine_within_dense", {t: dv[t] - ds[t] for t in turns_of}),
                        ("model_within_vllm", {t: dv[t] - mv[t] for t in turns_of}),
                        ("model_within_sglang", {t: ds[t] - ms[t] for t in turns_of})):
        vals = [series[t] for t in turns_of]
        out[f"{tag}"] = round(statistics.fmean(vals), 4)
        out[f"{tag}_ci95"] = tuple(round(x, 1) for x in boot_mean(vals))
        out[f"{tag}_positive_turns"] = sum(1 for v in vals if v > 0)
    for name, series in effects.items():
        vals = [series[t] for t in sorted(series)]
        out[f"{name}_effect"] = round(statistics.fmean(vals), 4)
        out[f"{name}_effect_ci95"] = tuple(round(x, 1) for x in boot_mean(vals))
        out[f"{name}_positive_turns"] = sum(1 for v in vals if v > 0)
        out[f"{name}_n_turns"] = len(vals)
    grand = statistics.fmean(
        statistics.fmean([uncached(r) for r in rs]) for rs in panel.values())
    out["grand_mean"] = round(grand, 4)
    out["engine_over_model"] = round(out["engine_effect"] / out["model_effect"], 4)
    # C63's prose: "the model effect is N x larger under vLLM than under SGLang", divided
    # from the two unrounded within-engine means (dividing rounded operands is an artefact).
    vllm_m = statistics.fmean(list((dv[t] - mv[t]) for t in turns_of))
    sgl_m = statistics.fmean(list((ds[t] - ms[t]) for t in turns_of))
    out["model_effect_ratio_vllm_over_sglang"] = round(vllm_m / sgl_m, 4)
    out["engine_share_of_grand"] = round(out["engine_effect"] / grand, 4)
    out["model_share_of_grand"] = round(out["model_effect"] / grand, 4)
    # replicate-arm check: the same decomposition arm by arm
    rep_engine, rep_model = [], []
    for arm in arms:
        by_arm = {k: {int(r["turn"]): float(uncached(r)) for r in rs if r["arm"] == arm}
                  for k, rs in panel.items()}
        e = statistics.fmean(
            by_arm[("occamy-1.0", "vllm")][t] + by_arm[("qwen3.5-9b", "vllm")][t]
            - by_arm[("occamy-1.0", "sglang")][t] - by_arm[("qwen3.5-9b", "sglang")][t]
            for t in by_arm[("occamy-1.0", "vllm")]) / 2
        m = statistics.fmean(
            by_arm[("qwen3.5-9b", "vllm")][t] + by_arm[("qwen3.5-9b", "sglang")][t]
            - by_arm[("occamy-1.0", "vllm")][t] - by_arm[("occamy-1.0", "sglang")][t]
            for t in by_arm[("occamy-1.0", "vllm")]) / 2
        rep_engine.append(round(e, 1))
        rep_model.append(round(m, 1))
    out["replicate_arms_engine"] = tuple(rep_engine)
    out["replicate_arms_model"] = tuple(rep_model)
    out["replicate_arm_names"] = arms
    return out


def _gcd(vals: list[int]) -> int:
    if not vals:
        return 0
    g = 0
    for v in vals:
        g = _gcd_pair(g, abs(v))
    return g


def _gcd_pair(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


# --------------------------------------------------------------------------- #
# C66 -- the track-interval sweep moves the grid in no cell
# --------------------------------------------------------------------------- #
TRACK_ARMS = ("R", "A", "C", "H", "C0")


def c66() -> dict:
    """``mamba_track_interval`` 256 / 128 / 64, three arms x 355 rows.

    The sweep exists to ask whether the 64-token cache grid is a property of the track
    interval.  It is not: the grid is ``_mamba_cache_chunk_size`` and every interval
    yields the same one.  This function measures each interval's arms and its grid from
    the rows, then the paired per-turn differences against 256.
    """
    dirs = {256: TRACK_ROOT / "t256", 128: TRACK_ROOT / "t128", 64: TRACK_ROOT / "t64"}
    out: dict[str, object] = {}
    per: dict[int, dict[str, dict[int, float]]] = {}
    for interval, d in dirs.items():
        files = sorted(p for p in d.glob("*.jsonl") if "rows" in p.name)
        rows: list[dict] = []
        for f in files:
            rows.extend(read_jsonl(f))
        if not rows:
            raise ValueError(f"C66: no rows under {d}")
        ok = [r for r in rows if int(r.get("status") or r.get("http_status") or 0) == 200
              and countable(r)]
        out[f"rows_T{interval}"] = len(ok)
        out[f"files_T{interval}"] = tuple(p.name for p in files)
        hot = [int(r["cached_tokens"]) for r in ok if int(r["cached_tokens"]) > 0]
        out[f"hot_gcd_T{interval}"] = _gcd(hot)
        out[f"hot_rows_T{interval}"] = len(hot)
        out[f"off_grid_T{interval}"] = sum(1 for c in hot if c % 64)
        arms = arms_of(ok)
        per[interval] = {}
        for arm in TRACK_ARMS:
            if arm not in arms:
                continue
            unc = {t: float(uncached(r)) for t, r in arms[arm].items()}
            per[interval][arm] = unc
            vals = list(unc.values())
            out[f"T{interval}_{arm}_n"] = len(vals)
            out[f"T{interval}_{arm}_mean"] = round(statistics.fmean(vals), 1)
    for interval in (64, 128):
        if 256 not in per or interval not in per:
            continue
        for arm in TRACK_ARMS:
            if arm not in per[interval] or arm not in per[256]:
                continue
            d = paired_boot(per[interval][arm], per[256][arm], R2_SEED, R2_B)
            out[f"T{interval}_minus_T256_{arm}"] = round(d["mean"], 3)
            out[f"T{interval}_minus_T256_{arm}_ci95"] = (round(d["ci95"][0], 2),
                                                         round(d["ci95"][1], 2))
            out[f"T{interval}_minus_T256_{arm}_excludes_zero"] = d["excludes_zero"]
    return out


# --------------------------------------------------------------------------- #
# SYS-OPT -- the version round (headline in MANUSCRIPT §10)
# --------------------------------------------------------------------------- #
def sysopt() -> dict:
    """V1 against V0 on the two production checkpoints, from raw rows only.

    ``rows-moe.jsonl`` / ``rows-dense.jsonl`` hold the round's P0/P1/P3 arms.  V0 is not a
    row of that round: it is the matching P1 arm of the two V0-pin cells
    (``R2-PROMPT/O1`` for the MoE, ``R2-PROMPT/O4`` for the dense model), which is how
    ``sysopt_r1.py:509-512`` defines it and what makes the comparison paired by turn.
    Quality is read from the round's own ``quality-*.json`` files.
    """
    out: dict[str, object] = {}
    v0_src = {
        "moe": CELLS / "R2-PROMPT" / "O1" / "rows.jsonl",
        "dense": CELLS / "R2-PROMPT" / "O4" / "rows.jsonl",
    }
    for model in ("moe", "dense"):
        rows = read_jsonl(CELLS / "SYS-OPT" / f"rows-{model}.jsonl")
        ok = [r for r in rows if int(r.get("http_status") or 0) == 200 and countable(r)]
        out[f"{model}_rows"] = len(rows)
        out[f"{model}_usable_rows"] = len(ok)
        out[f"{model}_versions"] = tuple(sorted({r.get("version") for r in ok}))
        by_arm = arms_of(ok)
        p1 = {t: float(uncached(r)) for t, r in by_arm["P1"].items()}
        for arm in ("P0", "P1", "P3"):
            if arm not in by_arm:
                continue
            vals = [float(uncached(r)) for r in by_arm[arm].values()]
            out[f"{model}_{arm}_mean"] = round(statistics.fmean(vals), 6)
            out[f"{model}_{arm}_n"] = len(vals)
        v0_rows = [r for r in read_jsonl(v0_src[model]) if r.get("arm") == "P1" and countable(r)]
        v0 = {int(r["turn"]): float(uncached(r)) for r in v0_rows}
        out[f"{model}_V0_mean"] = round(statistics.fmean(list(v0.values())), 6)
        out[f"{model}_V0_n"] = len(v0)
        d = paired_boot(p1, v0, SYSOPT_SEED, SYSOPT_B)
        out[f"{model}_P1_minus_V0"] = round(d["mean"], 6)
        out[f"{model}_P1_minus_V0_ci95"] = (round(d["ci95"][0], 6), round(d["ci95"][1], 6))
        out[f"{model}_P1_minus_V0_excludes_zero"] = d["excludes_zero"]
        out[f"{model}_P1_minus_V0_n"] = d["n_pairs"]
        # Quality, from the P1-form graders.  ``ok`` is the conjunction of the two
        # components, so comparing whole-answer ``ok`` against a stored mismatch count
        # measures the components, not the round: the components are counted here and
        # the mismatch counts are REBUILT in both of the two conjunctive readings any
        # reader might apply, so whichever reading the round used is visible.
        qa = json.loads((CELLS / "SYS-OPT" / f"quality-{model}.json").read_text(encoding="utf-8"))
        qb = json.loads((CELLS / "SYS-OPT" / "quality-before.json").read_text(encoding="utf-8"))
        before_f = _sysopt_form_graders(qb, model, None)
        after_f = _sysopt_form_graders(qa, model, "P1")
        ok_b = [g["ok"] for g in before_f]
        ok_a = [g["ok"] for g in after_f]
        out[f"{model}_quality_before_ok"] = (sum(1 for x in ok_b if x is True), len(ok_b))
        out[f"{model}_quality_after_ok"] = (sum(1 for x in ok_a if x is True), len(ok_a))
        out[f"{model}_quality_before_span_ok"] = sum(1 for g in before_f if g.get("span_ok") is True)
        out[f"{model}_quality_before_sha8_ok"] = sum(1 for g in before_f if g.get("sha8_ok") is True)
        out[f"{model}_quality_after_span_ok"] = sum(1 for g in after_f if g.get("span_ok") is True)
        out[f"{model}_quality_after_sha8_ok"] = sum(1 for g in after_f if g.get("sha8_ok") is True)
        out[f"{model}_quality_n"] = len(after_f)
        # Like for like: the same 20 probes, asked in the P1 form, before and after.
        out[f"{model}_p1_form_before_mismatches"] = sum(1 for x in ok_b if x is not True)
        out[f"{model}_p1_form_after_mismatches"] = sum(1 for x in ok_a if x is not True)
        # The 40-probe full set (20 P0-form probes + 20 P1-form probes) as the round's
        # own quality file counts it: mismatches out of n.
        qa_doc = qa if isinstance(qa, dict) else {}
        out[f"{model}_full_after"] = (int(qa_doc.get("n_probes", 0)) - int(qa_doc.get("mismatches", 0)),
                                      int(qa_doc.get("n_probes", 0)))
    return out


def _sysopt_form_graders(doc: object, model: str, form: str | None) -> list[dict]:
    """The per-question graders of one model's quality run, for one answer form."""
    models = doc.get("models") if isinstance(doc, dict) else None
    node = models[model] if isinstance(models, dict) and model in models else doc
    if not isinstance(node, dict) or "per_question" not in node:
        raise ValueError(f"quality doc for {model!r} carries no per_question list")
    out = []
    for q in node["per_question"]:
        g = q if form is None else q.get("forms", {}).get(form)
        if not isinstance(g, dict) or "grader" not in g:
            raise ValueError(f"quality doc for {model!r}: no grader under form {form!r}")
        out.append(g["grader"])
    return out



# --------------------------------------------------------------------------- #
# EVIDENCE -- what the rows say about the round, where no manuscript number exists
# --------------------------------------------------------------------------- #
def evidence() -> dict:
    """Reconcile the Round-2 cells' own summaries against their raw rows.

    Nothing here is a manuscript number; each entry answers "can this be re-derived",
    and the answer is printed either way.  A cell's stored summary that the raw rows do
    not reproduce is recorded as a defect with the two values side by side.
    """
    out: dict[str, object] = {}

    # 1. SYS-OPT quality: stored mismatch counts vs the graders.
    qb = json.loads((CELLS / "SYS-OPT" / "quality-before.json").read_text(encoding="utf-8"))
    for model in ("moe", "dense"):
        qa = json.loads((CELLS / "SYS-OPT" / f"quality-{model}.json").read_text(encoding="utf-8"))
        b = _sysopt_form_graders(qb, model, None)
        a = _sysopt_form_graders(qa, model, "P1")
        n = len(a)
        stored_after = int(json.loads((CELLS / "SYS-OPT" / "round-result.json").read_text(
            encoding="utf-8"))["models"][model]["quality"]["p1_form"]["mismatches"])
        stored_before = int(qb["models"][model]["mismatches"])
        for tag, g, stored in (("before", b, stored_before), ("after", a, stored_after)):
            span = sum(1 for x in g if x.get("span_ok") is True)
            sha = sum(1 for x in g if x.get("sha8_ok") is True)
            both = sum(1 for x in g if x.get("span_ok") is True and x.get("sha8_ok") is True)
            okf = sum(1 for x in g if x.get("ok") is True)
            out[f"sysopt_quality_{model}_{tag}_n"] = n
            out[f"sysopt_quality_{model}_{tag}_span_ok"] = span
            out[f"sysopt_quality_{model}_{tag}_sha8_ok"] = sha
            out[f"sysopt_quality_{model}_{tag}_graders_ok"] = okf
            out[f"sysopt_quality_{model}_{tag}_mismatch_if_not_span_ok"] = n - span
            out[f"sysopt_quality_{model}_{tag}_mismatch_if_not_both"] = n - both
            out[f"sysopt_quality_{model}_{tag}_stored_mismatches"] = stored
            out[f"sysopt_quality_{model}_{tag}_reconciles_on"] = (
                "not_span_ok" if stored == n - span else
                "not_both" if stored == n - both else
                "graders_ok" if stored == n - okf else "NONE")

    # 2. Every Round-2 cell's G0 gate, re-derived from its own recorded counters.
    gates = {}
    for model in ("moe", "dense"):
        g = json.loads((CELLS / "SYS-OPT" / f"g0-{model}.json").read_text(encoding="utf-8"))
        gates[f"SYS-OPT/{model}"] = {
            "verdict": g.get("verdict"),
            "call1_cached": g.get("call1_cached"), "call2_cached": g.get("call2_cached"),
            "cold_miss_on_call1": g.get("call1_cached") in (None, 0),
            "warm_hit_on_call2": isinstance(g.get("call2_cached"), int)
            and g["call2_cached"] > 0,
        }
    for cell in ("O1", "O2", "O3", "O4"):
        p = CELLS / "R2-PROMPT" / cell / "g0.json"
        if p.exists():
            g = json.loads(p.read_text(encoding="utf-8"))
            gates[f"R2-PROMPT/{cell}"] = {
                "verdict": g.get("verdict"),
                "call1_cached": g.get("call1_cached"), "call2_cached": g.get("call2_cached"),
                "cold_miss_on_call1": g.get("call1_cached") in (None, 0),
                "warm_hit_on_call2": isinstance(g.get("call2_cached"), int)
                and g["call2_cached"] > 0,
            }
    p = CELLS / "P2-REPAD" / "g0.json"
    if p.exists():
        g = json.loads(p.read_text(encoding="utf-8"))
        gates["P2-REPAD"] = {
            "verdict": g.get("verdict"),
            "call1_cached": g.get("call1_cached"), "call2_cached": g.get("call2_cached"),
            "cold_miss_on_call1": g.get("call1_cached") in (None, 0),
            "warm_hit_on_call2": isinstance(g.get("call2_cached"), int) and g["call2_cached"] > 0,
        }
    out["g0_gates"] = gates
    out["g0_failures"] = sorted(k for k, v in gates.items()
                                if not (v.get("cold_miss_on_call1") and v.get("warm_hit_on_call2")))

    # 3. TRACK-INTERVAL: does the sweep move any arm, and is the stored analysis reproducible?
    for interval in (256, 128, 64):
        d = CELLS / "TRACK-INTERVAL" / f"t{interval}"
        rows = read_jsonl(d / "rows.jsonl")
        stored = json.loads((d / "analysis.json").read_text(encoding="utf-8"))
        by = arms_of([r for r in rows if countable(r)])
        mine = {a: statistics.fmean(float(uncached(r)) for r in v.values()) for a, v in by.items()}
        theirs = {a: float(stored["per_arm"][a]["mean_uncached_per_turn"]) for a in stored["per_arm"]}
        out[f"track_T{interval}_reproduces_stored_analysis"] = all(
            abs(mine[a] - theirs[a]) < 0.01 for a in mine)
        out[f"track_T{interval}_rows"] = len(rows)
        out[f"track_T{interval}_warmup_rows"] = len(rows) - sum(len(v) for v in by.values())
        out[f"track_T{interval}_warmup_cached"] = stored.get("warmup_cached_tokens")
    # 4. Which cells' rows actually carry the ``stack`` their directory name claims.
    #    A cell directory named for one engine whose rows say another is a provenance
    #    defect the claim runner cannot see, because it filters on ``stack``.
    out["cells_named_sgl_with_vllm_rows"] = sorted(
        d.name for d in CELLS.glob("*SGL*")
        if d.is_dir() and any(isinstance(r.get("stack"), str) and "vllm" in r["stack"]
                              for r in read_jsonl_rows(d)))
    out["cells_named_vllm_with_sglang_rows"] = sorted(
        d.name for d in CELLS.glob("*VLLM*")
        if d.is_dir() and any(r.get("stack") == "sglang" for r in read_jsonl_rows(d)))
    # 5. The padding repair: how many P2-REPAD rows could have been resent at all.
    repad = read_jsonl(CELLS / "P2-REPAD" / "rows.jsonl")
    out["repad_multi_send_rows"] = sum(1 for r in repad if int(r.get("requests_sent") or 0) != 1)
    out["repad_rows_with_correction"] = sum(
        1 for r in repad if int(r.get("corrections") or 0) or r.get("had_correction"))
    return out


# --------------------------------------------------------------------------- #
# Comparison scaffolding -- identical contract to recompute.py
# --------------------------------------------------------------------------- #
TOLERANCE = {"C63": 1e-6, "C64": 1e-4, "C65": 1e-6, "C66": 1e-3, "C67": 1e-4, "C68": 1e-9, "SYSOPT": 1e-6}

FUNCS = {"C63": c63, "C64": c64, "C65": c65, "C66": c66, "C67": c67, "C68": c68,
         "C69": sysopt, "C69": sysopt, "SYSOPT": sysopt, "EVIDENCE": evidence}

def read_jsonl_rows(d: Path) -> list[dict]:
    """Every ``*.jsonl`` row directly under ``d`` (one level), unparsed failures skipped by name."""
    out: list[dict] = []
    for f in sorted(d.glob("*.jsonl")):
        try:
            out.extend(read_jsonl(f))
        except Exception:                                     # a damaged file is not a row
            continue
    return out


EXPECTED: dict[str, dict[str, object]] = {
    "C63": {   # n=63 -- the headline claim: the engine, not the model, sets the bill
    # Per (model/engine) cell: 284 rows each, i.e. 4 arms x 71 turns.
    "cell_hit_occamy-1.0_sglang": 0.957153,
    "cell_hit_occamy-1.0_vllm": 0.901212,
    "cell_hit_qwen3.5-9b_sglang": 0.956941,
    "cell_hit_qwen3.5-9b_vllm": 0.817432,
    "cell_hot_gcd_occamy-1.0_sglang": 64,
    "cell_hot_gcd_occamy-1.0_vllm": 2096,
    #: The vLLM dense cell's 1,088 is a LAUNCH reading, not a gcd of its hot values;
    #: ``recompute.py`` records it in ``C63_GCD_OVERRIDE`` and the cell states it.
    "cell_hot_gcd_qwen3.5-9b_vllm": 16,
    "cell_hot_gcd_qwen3.5-9b_sglang": 64,
    "cell_rows_occamy-1.0_sglang": 284,
    "cell_rows_occamy-1.0_vllm": 284,
    "cell_rows_qwen3.5-9b_sglang": 284,
    "cell_rows_qwen3.5-9b_vllm": 284,
    "cell_unc_occamy-1.0_sglang": 729.7641,
    "cell_unc_occamy-1.0_vllm": 1682.7218,
    "cell_unc_qwen3.5-9b_sglang": 733.3697,
    "cell_unc_qwen3.5-9b_vllm": 879.0669,
    "n_rows_total": 1136,
    # The three main effects, at the 2-dp / 1-dp precision C63 publishes them.
    "engine_effect": 549.33,
    "engine_effect_ci95": (462.4, 631.9),
    "engine_effect_positive_turns": 66,
    "engine_effect_n_turns": 71,
    "model_effect": -400.02,
    "model_effect_ci95": (-474.2, -326.5),
    "model_effect_positive_turns": 8,
    "model_effect_n_turns": 71,
    "interaction_effect": -403.63,
    "interaction_effect_ci95": (-479.7, -328.5),
    "interaction_effect_positive_turns": 8,
    "interaction_effect_n_turns": 71,
    # The engine effect inside each model, and the model effect inside each engine.
    "engine_within_moe": 952.96,
    "engine_within_moe_ci95": (805.7, 1099.8),
    "engine_within_moe_positive_turns": 67,
    "engine_within_moe_n_turns": 71,
    "engine_within_dense": 145.7,
    "engine_within_dense_ci95": (81.2, 210.5),
    "engine_within_dense_positive_turns": 48,
    "engine_within_dense_n_turns": 71,
    "model_within_vllm": -803.65,
    "model_within_vllm_ci95": (-953.6, -655.2),
    "model_within_vllm_positive_turns": 8,
    "model_within_vllm_n_turns": 71,
    "model_within_sglang": 3.61,
    "model_within_sglang_ci95": (0.0, 10.8),
    "model_within_sglang_positive_turns": 1,
    "model_within_sglang_n_turns": 71,
    # Cell-mean ratios (arithmetic, two levels per factor), and the shares of the grand mean.
    "grand_mean": 1006.2306,
    "ratio_engine_over_moe": 2.3058,
    "ratio_engine_over_dense": 1.1987,
    "ratio_engine_mean": 1.7523,
    "ratio_model_over_vllm": 0.5224,
    "ratio_model_over_sglang": 1.0049,
    "ratio_model_mean": 0.7636,
    "ratio_engine_over_model": -1.3733,
    "engine_share_of_grand": 0.5459,
    "model_share_of_grand": -0.3975,
    #: Divided from the UNROUNDED per-turn means, never from the printed 2-dp figures
    #: (``recompute.py C63``'s rule; ``tests/test_c63_ratio_raw_operands.py`` pins it).
    "ratio_model_effect_vllm_over_sglang": -222.8887,
    # Replicate-arm check across R/A/C/H, as the band the cell states.
    "replicate_arm_names": ('R', 'A', 'C', 'H'),
    "replicate_arms_engine": (560.0, 583.7, 395.7, 657.9),
    "replicate_arms_model": (-384.8, -372.0, -546.4, -296.8),
    "replicate_band_engine": (395.7, 657.9),
    "replicate_band_model": (-546.4, -296.8),
    },
    "C64": {   # n=38
    "P0_ci95": (501.676, 581.507),
    "P0_hit": 0.956139,
    "P0_mean_uncached_per_turn": 541.0704,
    "P0_n": 71,
    "P1_ci95": (521.186, 536.129),
    "P1_hit": 0.772737,
    "P1_mean_uncached_per_turn": 528.6429,
    "P1_minus_P0_ci95": (-57.186, 27.114),
    "P1_minus_P0_delta": -14.3429,
    "P1_minus_P0_excludes_zero": False,
    "P1_minus_P0_n_pairs": 70,
    "P1_n": 70,
    "P2_ci95": (542.171, 556.8),
    "P2_hit": 0.773036,
    "P2_mean_uncached_per_turn": 549.4857,
    "P2_minus_P0_ci95": (-34.971, 46.914),
    "P2_minus_P0_delta": 6.5,
    "P2_minus_P0_excludes_zero": False,
    "P2_minus_P0_n_pairs": 70,
    "P2_minus_P1_ci95": (10.014, 31.586),
    "P2_minus_P1_delta": 20.8429,
    "P2_minus_P1_excludes_zero": True,
    "P2_minus_P1_n_pairs": 70,
    "P2_n": 70,
    "P2_over_P1_ratio_of_means": 1.039427,
    "P2_pad_max": 127,
    "P2_pad_mean": 94.9,
    "P2_pad_min": 64,
    "P2_pad_total": 6643,
    "P2_rows_aligned_on_64": 70,
    "corrected_rows": 0,
    "extra_cached_vs_P1": ((0, 9), (64, 41), (128, 20)),
    "extra_cached_vs_P1_mean": 74.0571,
    "multi_send_rows": 0,
    "n_rows": 213,
    "non_200": 0,
    "non_countable_rows": 2,
    "pad_recovered_fraction": 0.78037,
    },
    "C65": {   # n=48
    "cell_hit_occamy-1.0_sglang": 0.957153,
    "cell_hit_occamy-1.0_vllm": 0.901212,
    "cell_hit_qwen3.5-9b_sglang": 0.956941,
    "cell_hit_qwen3.5-9b_vllm": 0.817432,
    "cell_hot_gcd_occamy-1.0_sglang": 64,
    "cell_hot_gcd_occamy-1.0_vllm": 2096,
    "cell_hot_gcd_qwen3.5-9b_sglang": 64,
    "cell_hot_gcd_qwen3.5-9b_vllm": 16,
    "cell_rows_occamy-1.0_sglang": 284,
    "cell_rows_occamy-1.0_vllm": 284,
    "cell_rows_qwen3.5-9b_sglang": 284,
    "cell_rows_qwen3.5-9b_vllm": 284,
    "cell_unc_occamy-1.0_sglang": 729.7641,
    "cell_unc_occamy-1.0_vllm": 1682.7218,
    "cell_unc_qwen3.5-9b_sglang": 733.3697,
    "cell_unc_qwen3.5-9b_vllm": 879.0669,
    "engine_effect": 549.3275,
    "engine_effect_ci95": (463.1, 631.8),
    "engine_n_turns": 71,
    "engine_over_model": -1.3732,
    "engine_positive_turns": 66,
    "engine_share_of_grand": 0.5459,
    "engine_within_dense": 145.6972,
    "engine_within_dense_ci95": (79.3, 211.6),
    "engine_within_dense_positive_turns": 48,
    "engine_within_moe": 952.9577,
    "engine_within_moe_ci95": (802.9, 1094.9),
    "engine_within_moe_positive_turns": 67,
    "grand_mean": 1006.2306,
    "interaction_effect": -403.6303,
    "interaction_effect_ci95": (-478.4, -327.3),
    "interaction_n_turns": 71,
    "interaction_positive_turns": 8,
    "model_effect": -400.0246,
    "model_effect_ci95": (-472.9, -324.3),
    "model_effect_ratio_vllm_over_sglang": -222.8887,
    "model_n_turns": 71,
    "model_positive_turns": 8,
    "model_share_of_grand": -0.3975,
    "model_within_sglang": 3.6056,
    "model_within_sglang_ci95": (0.0, 10.8),
    "model_within_sglang_positive_turns": 1,
    "model_within_vllm": -803.6549,
    "model_within_vllm_ci95": (-950.6, -651.5),
    "model_within_vllm_positive_turns": 8,
    "replicate_arm_names": ('R', 'A', 'C', 'H'),
    "replicate_arms_engine": (560.0, 583.7, 395.7, 657.9),
    "replicate_arms_model": (-384.8, -372.0, -546.4, -296.8),
    },
    "C66": {   # n=75
    "T128_A_mean": 527.5,
    "T128_A_n": 71,
    "T128_C0_mean": 709.9,
    "T128_C0_n": 71,
    "T128_C_mean": 547.1,
    "T128_C_n": 71,
    "T128_H_mean": 962.0,
    "T128_H_n": 71,
    "T128_R_mean": 600.3,
    "T128_R_n": 71,
    "T128_minus_T256_A": -1.803,
    "T128_minus_T256_A_ci95": (-5.41, 1.8),
    "T128_minus_T256_A_excludes_zero": False,
    "T128_minus_T256_C": 0.0,
    "T128_minus_T256_C0": 0.0,
    "T128_minus_T256_C0_ci95": (0.0, 0.0),
    "T128_minus_T256_C0_excludes_zero": False,
    "T128_minus_T256_C_ci95": (0.0, 0.0),
    "T128_minus_T256_C_excludes_zero": False,
    "T128_minus_T256_H": 0.0,
    "T128_minus_T256_H_ci95": (0.0, 0.0),
    "T128_minus_T256_H_excludes_zero": False,
    "T128_minus_T256_R": 0.0,
    "T128_minus_T256_R_ci95": (0.0, 0.0),
    "T128_minus_T256_R_excludes_zero": False,
    "T256_A_mean": 529.3,
    "T256_A_n": 71,
    "T256_C0_mean": 709.9,
    "T256_C0_n": 71,
    "T256_C_mean": 547.1,
    "T256_C_n": 71,
    "T256_H_mean": 962.0,
    "T256_H_n": 71,
    "T256_R_mean": 600.3,
    "T256_R_n": 71,
    "T64_A_mean": 524.8,
    "T64_A_n": 71,
    "T64_C0_mean": 709.9,
    "T64_C0_n": 71,
    "T64_C_mean": 547.1,
    "T64_C_n": 71,
    "T64_H_mean": 960.2,
    "T64_H_n": 71,
    "T64_R_mean": 600.3,
    "T64_R_n": 71,
    "T64_minus_T256_A": -4.507,
    "T64_minus_T256_A_ci95": (-12.62, 2.7),
    "T64_minus_T256_A_excludes_zero": False,
    "T64_minus_T256_C": 0.0,
    "T64_minus_T256_C0": 0.0,
    "T64_minus_T256_C0_ci95": (0.0, 0.0),
    "T64_minus_T256_C0_excludes_zero": False,
    "T64_minus_T256_C_ci95": (0.0, 0.0),
    "T64_minus_T256_C_excludes_zero": False,
    "T64_minus_T256_H": -1.803,
    "T64_minus_T256_H_ci95": (-4.51, 0.0),
    "T64_minus_T256_H_excludes_zero": False,
    "T64_minus_T256_R": 0.0,
    "T64_minus_T256_R_ci95": (0.0, 0.0),
    "T64_minus_T256_R_excludes_zero": False,
    "files_T128": ('rows.jsonl',),
    "files_T256": ('rows.jsonl',),
    "files_T64": ('rows.jsonl',),
    "hot_gcd_T128": 64,
    "hot_gcd_T256": 64,
    "hot_gcd_T64": 64,
    "hot_rows_T128": 345,
    "hot_rows_T256": 345,
    "hot_rows_T64": 345,
    "off_grid_T128": 0,
    "off_grid_T256": 0,
    "off_grid_T64": 0,
    "rows_T128": 355,
    "rows_T256": 355,
    "rows_T64": 355,
    },
    "C67": {   # n=85
    "O1_P0_mean": 530.3944,
    "O1_P0_n": 71,
    "O1_P1_mean": 522.7183,
    "O1_P1_minus_P0_ci95": (-50.099, 35.324),
    "O1_P1_minus_P0_delta": -7.6761,
    "O1_P1_minus_P0_excludes_zero": False,
    "O1_P1_minus_P0_n_pairs": 71,
    "O1_P1_n": 71,
    "O1_P2_mean": 541.7465,
    "O1_P2_n": 71,
    "O1_P3_mean": 520.5493,
    "O1_P3_minus_P1_ci95": (-35.437, 42.042),
    "O1_P3_minus_P1_delta": -2.169,
    "O1_P3_minus_P1_excludes_zero": False,
    "O1_P3_minus_P1_n_pairs": 71,
    "O1_P3_n": 71,
    "O1_arms_present": ('P0', 'P1', 'P2', 'P3'),
    "O1_engine": ('sglang/occamy-1.0',),
    "O1_non_200": 0,
    "O1_rows": 284,
    "O1_usable_rows": 284,
    "O2_P0_mean": 530.3944,
    "O2_P0_n": 71,
    "O2_P1_mean": 522.7183,
    "O2_P1_minus_P0_ci95": (-50.099, 35.324),
    "O2_P1_minus_P0_delta": -7.6761,
    "O2_P1_minus_P0_excludes_zero": False,
    "O2_P1_minus_P0_n_pairs": 71,
    "O2_P1_n": 71,
    "O2_P2_mean": 456.1127,
    "O2_P2_n": 71,
    "O2_P3_mean": 519.6479,
    "O2_P3_minus_P1_ci95": (-36.296, 40.972),
    "O2_P3_minus_P1_delta": -3.0704,
    "O2_P3_minus_P1_excludes_zero": False,
    "O2_P3_minus_P1_n_pairs": 71,
    "O2_P3_n": 71,
    "O2_arms_present": ('P0', 'P1', 'P2', 'P3'),
    "O2_engine": ('sglang/qwen3.5-9b',),
    "O2_non_200": 0,
    "O2_rows": 284,
    "O2_usable_rows": 284,
    "O3_P0_mean": 1290.0563,
    "O3_P0_n": 71,
    "O3_P1_mean": 1345.7042,
    "O3_P1_minus_P0_ci95": (-136.493, 246.014),
    "O3_P1_minus_P0_delta": 55.6479,
    "O3_P1_minus_P0_excludes_zero": False,
    "O3_P1_minus_P0_n_pairs": 71,
    "O3_P1_n": 71,
    "O3_P2_mean": 625.5775,
    "O3_P2_n": 71,
    "O3_P3_mean": 1205.3944,
    "O3_P3_minus_P1_ci95": (-289.099, 8.211),
    "O3_P3_minus_P1_delta": -140.3099,
    "O3_P3_minus_P1_excludes_zero": False,
    "O3_P3_minus_P1_n_pairs": 71,
    "O3_P3_n": 71,
    "O3_arms_present": ('P0', 'P1', 'P2', 'P3'),
    "O3_engine": ('vllm/occamy-1.0',),
    "O3_non_200": 0,
    "O3_rows": 284,
    "O3_usable_rows": 284,
    "O4_P0_mean": 1883.8592,
    "O4_P0_n": 71,
    "O4_P1_mean": 1664.3521,
    "O4_P1_minus_P0_ci95": (-353.831, -88.845),
    "O4_P1_minus_P0_delta": -219.507,
    "O4_P1_minus_P0_excludes_zero": True,
    "O4_P1_minus_P0_n_pairs": 71,
    "O4_P1_n": 71,
    "O4_P2_mean": 2271.0986,
    "O4_P2_n": 71,
    "O4_P3_mean": 1687.8732,
    "O4_P3_minus_P1_ci95": (8.394, 53.479),
    "O4_P3_minus_P1_delta": 23.5211,
    "O4_P3_minus_P1_excludes_zero": True,
    "O4_P3_minus_P1_n_pairs": 71,
    "O4_P3_n": 71,
    "O4_arms_present": ('P0', 'P1', 'P2', 'P3'),
    "O4_engine": ('vllm/qwen3.5-9b',),
    "O4_non_200": 0,
    "O4_rows": 284,
    "O4_usable_rows": 284,
    "cells_whose_summary_disagrees_with_rows": (),
    },
    "C68": {   # n=70
    "O1_P1_rows_repeating_P0_digest": 0,
    "O1_P2_rows_repeating_P0_digest": 0,
    "O1_P3_rows_repeating_P0_digest": 0,
    "O1_config_sha256": ('f2efaaac1559ebc0a706c5012715dacff6948058ee8e5c946d5d45c622880c67',),
    "O1_distinct_cached_values": 101,
    "O1_distinct_prompt_sha256": 284,
    "O1_distinct_uncached_values": 177,
    "O1_model": ('occamy-1.0',),
    "O1_ts_first": '2026-10-24T10:04:23Z',
    "O1_ts_last": '2026-10-24T10:09:57Z',
    "O1_vs_O2_config_fields_all_differ": ('config_id', 'config_sha256', 'model', 'setup', 'stack', 'wall_ms'),
    "O1_vs_O2_rows_same_prompt": 266,
    "O1_vs_O2_rows_with_different_cache_counters": 62,
    "O1_vs_O2_shared_keys": 284,
    "O1_vs_O3_config_fields_all_differ": ('config_id', 'config_sha256', 'setup', 'stack', 'wall_ms'),
    "O1_vs_O3_rows_same_prompt": 226,
    "O1_vs_O3_rows_with_different_cache_counters": 277,
    "O1_vs_O3_shared_keys": 284,
    "O1_vs_O4_config_fields_all_differ": ('config_id', 'config_sha256', 'model', 'setup', 'stack', 'wall_ms'),
    "O1_vs_O4_rows_same_prompt": 216,
    "O1_vs_O4_rows_with_different_cache_counters": 284,
    "O1_vs_O4_shared_keys": 284,
    "O2_P1_rows_repeating_P0_digest": 0,
    "O2_P2_rows_repeating_P0_digest": 0,
    "O2_P3_rows_repeating_P0_digest": 0,
    "O2_config_sha256": ('652ff99db16fb7fc90e2649955bf74dbcda4586ee1e13704290cf2b0bc9ab510',),
    "O2_distinct_cached_values": 101,
    "O2_distinct_prompt_sha256": 284,
    "O2_distinct_uncached_values": 176,
    "O2_model": ('qwen3.5-9b',),
    "O2_ts_first": '2026-10-24T10:30:12Z',
    "O2_ts_last": '2026-10-24T10:32:26Z',
    "O2_vs_O3_config_fields_all_differ": ('config_id', 'config_sha256', 'model', 'setup', 'stack', 'wall_ms'),
    "O2_vs_O3_rows_same_prompt": 226,
    "O2_vs_O3_rows_with_different_cache_counters": 277,
    "O2_vs_O3_shared_keys": 284,
    "O2_vs_O4_config_fields_all_differ": ('config_id', 'config_sha256', 'setup', 'stack', 'wall_ms'),
    "O2_vs_O4_rows_same_prompt": 215,
    "O2_vs_O4_rows_with_different_cache_counters": 284,
    "O2_vs_O4_shared_keys": 284,
    "O3_P1_rows_repeating_P0_digest": 0,
    "O3_P2_rows_repeating_P0_digest": 0,
    "O3_P3_rows_repeating_P0_digest": 0,
    "O3_config_sha256": ('f8ab1dce36c695ce6ad7be4c74d6e656b016b89548e93cf0b2040aa28b9c3360',),
    "O3_distinct_cached_values": 48,
    "O3_distinct_prompt_sha256": 284,
    "O3_distinct_uncached_values": 239,
    "O3_model": ('occamy-1.0',),
    "O3_ts_first": '2026-10-24T10:39:55Z',
    "O3_ts_last": '2026-10-24T10:43:03Z',
    "O3_vs_O4_config_fields_all_differ": ('config_id', 'config_sha256', 'model', 'setup', 'stack', 'wall_ms'),
    "O3_vs_O4_rows_same_prompt": 214,
    "O3_vs_O4_rows_with_different_cache_counters": 158,
    "O3_vs_O4_shared_keys": 284,
    "O4_P1_rows_repeating_P0_digest": 0,
    "O4_P2_rows_repeating_P0_digest": 0,
    "O4_P3_rows_repeating_P0_digest": 0,
    "O4_config_sha256": ('163a5db6b4c432e2a2ea17ffd6c44e336ed12af6eff39dce96be854032d77cb4',),
    "O4_distinct_cached_values": 22,
    "O4_distinct_prompt_sha256": 284,
    "O4_distinct_uncached_values": 212,
    "O4_model": ('qwen3.5-9b',),
    "O4_ts_first": '2026-10-24T10:11:42Z',
    "O4_ts_last": '2026-10-24T10:17:18Z',
    "cell_pairs_counted_twice": (),
    "cell_pairs_not_resolved": (),
    "cell_pairs_with_distinct_configuration": (('O1', 'O2'), ('O1', 'O3'), ('O1', 'O4'), ('O2', 'O3'), ('O2', 'O4'), ('O3', 'O4')),
    "cell_salts": {'O1': (), 'O2': (), 'O3': (), 'O4': ()},
    "cells_sharing_a_salt": (),
    "n_cells_distinct": 4,
    },
    "SYSOPT": {   # n=44
    "dense_P0_mean": 1896.985915,
    "dense_P0_n": 71,
    "dense_P1_mean": 1893.169014,
    "dense_P1_minus_V0": 228.816901,
    "dense_P1_minus_V0_ci95": (140.309859, 319.183099),
    "dense_P1_minus_V0_excludes_zero": True,
    "dense_P1_minus_V0_n": 71,
    "dense_P1_n": 71,
    "dense_P3_mean": 1916.690141,
    "dense_P3_n": 71,
    "dense_V0_mean": 1664.352113,
    "dense_V0_n": 71,
    "dense_quality_after_ok": (2, 20),
    "dense_quality_after_sha8_ok": 2,
    "dense_quality_after_span_ok": 20,
    "dense_quality_before_ok": (1, 20),
    "dense_quality_before_sha8_ok": 14,
    "dense_quality_before_span_ok": 7,
    "dense_quality_n": 20,
    "dense_p1_form_before_mismatches": 19,
    "dense_p1_form_after_mismatches": 18,
    "dense_full_after": (2, 40),
    "dense_rows": 213,
    "dense_usable_rows": 213,
    "dense_versions": ('V1',),
    "moe_P0_mean": 593.549296,
    "moe_P0_n": 71,
    "moe_P1_mean": 652.830986,
    "moe_P1_minus_V0": 130.112676,
    "moe_P1_minus_V0_ci95": (121.71831, 138.394366),
    "moe_P1_minus_V0_excludes_zero": True,
    "moe_P1_minus_V0_n": 71,
    "moe_P1_n": 71,
    "moe_P3_mean": 630.830986,
    "moe_P3_n": 71,
    "moe_V0_mean": 522.71831,
    "moe_V0_n": 71,
    "moe_quality_after_ok": (0, 20),
    "moe_quality_after_sha8_ok": 20,
    "moe_quality_after_span_ok": 0,
    "moe_quality_before_ok": (0, 20),
    "moe_quality_before_sha8_ok": 20,
    "moe_quality_before_span_ok": 0,
    "moe_quality_n": 20,
    "moe_p1_form_before_mismatches": 20,
    "moe_p1_form_after_mismatches": 20,
    "moe_full_after": (0, 40),
    "moe_rows": 213,
    "moe_usable_rows": 213,
    "moe_versions": ('V1',),
    },
}


#: Fields each runner derives on purpose and does NOT publish, so a reader sweeping the
#: ledger for "every number" sees a declared omission instead of an appearance of one.
#: Every key here was checked against the manuscript text: none of them is quoted there.
WITHHELD: dict[str, dict[str, str]] = {
    "C65": {
        "cell_hot_gcd_is_cache_unit_*": "the grid caveat (§9c states gcd 16 in words); the "
                                        "flag is what the words are derived from",
    },
    "C67": {
        "*_n_pairs": "all equal to the arm n on this cell (71); §9d quotes the n once",
    },
    "SYSOPT": {
        "*_usable_rows": "rows after the countable() filter; C69 states 213 usable rows per model",
        "dense_versions": "the round ran one version; C69 says V1",
        "moe_versions": "the round ran one version; C69 says V1",
    },
}


def close(got: object, want: object, tol: float) -> bool:
    if isinstance(want, bool) or isinstance(want, str):
        return got == want
    if isinstance(want, (int, float)):
        return got is not None and abs(float(got) - float(want)) <= max(tol, abs(float(want)) * tol)
    if isinstance(want, (tuple, list)):
        if not isinstance(got, (tuple, list)) or len(got) != len(want):
            return False
        return all(close(g, w, tol) for g, w in zip(got, want))
    return got == want


def check(claim: str) -> int:
    got = FUNCS[claim]()
    want = EXPECTED[claim]
    tol = TOLERANCE.get(claim, 1e-9)
    failed = 0
    print(f"{claim}  sources: see CLAIMS.md")
    for key, expected in want.items():
        actual = got.get(key)
        ok = close(actual, expected, tol)
        failed += 0 if ok else 1
        print(f"  {'OK  ' if ok else 'FAIL'} {key:38s} recomputed={actual!r:30s} paper={expected!r}")
    extra = sorted(set(got) - set(want))
    if extra:
        declared = (WITHHELD.get(claim) or {})
        undeclared = [k for k in extra
                      if not any(k.startswith(p.rstrip("*")) or p == k for p in declared)]
        if undeclared:
            print(f"  note: {len(undeclared)} recomputed key(s) neither published nor declared "
                  f"in WITHHELD: {undeclared[:6]}")
        else:
            print(f"  ok   {len(extra)} additional key(s), all declared withheld in WITHHELD")
    print(f"  {'PASS' if not failed else 'FAIL'}  {len(want) - failed}/{len(want)} values match")
    return 0 if not failed else 1


def redgreen() -> int:
    """Falsify each claim's SOURCE and require the claim to move.

    The rule this project lives by is that a claim is only as good as its ability to fail.
    Each case below perturbs the raw rows in a way that must change the published value if
    the value really comes from those rows, re-derives it, and requires a change.  A claim
    that survives a falsified source is not measuring what it says it measures.
    """
    global REPAD_ROWS, TRACK_ROOT, R2PROMPT_ROOT
    results: list[tuple[str, bool, object, object, str]] = []

    # C64: if grid padding bought nothing, P2 could not cost +20.84 over P1.
    base = read_jsonl(CELLS / "P2-REPAD" / "rows.jsonl")
    broken = []
    for r in base:
        r = dict(r)
        if r.get("arm") == "P2" and countable(r):
            r["cached_tokens"] = 0                        # padding recovers nothing
        broken.append(r)
    good = c64()["P2_minus_P1_delta"]
    REPAD_ROWS = broken
    try:
        bad = c64()["P2_minus_P1_delta"]
    finally:
        REPAD_ROWS = None
    results.append(("C64", good != bad, good, bad, "P2 cached_tokens forced to 0"))

    # C65: the panel must lose the Round-2 cell if its rows stop being that cell's.
    import tempfile
    d_rows = read_jsonl(C65_R2_PATH[0])
    stripped = []
    for r in d_rows:
        r = dict(r)
        if r.get("stack") == "vllm-0.27.1":
            r["stack"] = "vllm-ELSEWHERE"                 # the cell no longer matches
        stripped.append(r)
    good = c65()["engine_effect"]
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / "rows.jsonl"
        tp.write_text("".join(json.dumps(r) + "\n" for r in stripped), encoding="utf-8")
        saved = C65_R2_PATH[0]
        C65_R2_PATH[0] = tp
        try:
            c65()
            bad = "the empty cell was ACCEPTED -- the panel is not built from these rows"
        except ValueError as exc:
            bad = f"rejected: {exc}"
        finally:
            C65_R2_PATH[0] = saved
    results.append(("C65", bad != good, good, bad,
                    "Round-2 cell relabelled out of the panel (the panel must refuse it)"))

    # C66: a sweep that moved an arm must not report a zero window.
    import tempfile as _tf
    src = CELLS / "TRACK-INTERVAL" / "t64" / "rows.jsonl"
    t64 = read_jsonl(src)
    shifted = []
    for r in t64:
        r = dict(r)
        if r.get("arm") == "R" and countable(r):
            r["cached_tokens"] = max(0, int(r["cached_tokens"]) - 64)
        shifted.append(r)
    good = c66()["T64_minus_T256_R_ci95"]
    with _tf.TemporaryDirectory() as td:
        td = Path(td)
        for interval in (256, 128, 64):
            d = td / f"t{interval}"
            d.mkdir()
            rows = (shifted if interval == 64
                    else read_jsonl(CELLS / "TRACK-INTERVAL" / f"t{interval}" / "rows.jsonl"))
            (d / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        saved = TRACK_ROOT
        TRACK_ROOT = td
        try:
            bad = c66()["T64_minus_T256_R_ci95"]
        finally:
            TRACK_ROOT = saved
    results.append(("C66", good != bad, good, bad, "t64 R arm shifted one 64-token page"))

    # C68: two files of one measurement must be caught by the identity test.
    o1 = read_jsonl(CELLS / "R2-PROMPT" / "O1" / "rows.jsonl")
    forged = []
    for r in o1:
        r = dict(r)
        r["config_id"] = "O2"
        r["config_sha256"] = "0" * 64
        r["model"] = "qwen3.5-9b"
        r["setup"] = "O2"
        r["stack"] = "sglang/qwen3.5-9b"
        r["ts"] = "2026-10-24T11:00:00Z"
        forged.append(r)
    good = c68()["cell_pairs_counted_twice"]
    with _tf.TemporaryDirectory() as td:
        td = Path(td) / "R2-PROMPT"
        for cell in ("O1", "O2", "O3", "O4"):
            (td / cell).mkdir(parents=True)
            rows = (forged if cell == "O2"
                    else read_jsonl(CELLS / "R2-PROMPT" / cell / "rows.jsonl"))
            (td / cell / "rows.jsonl").write_text(
                "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        saved = R2PROMPT_ROOT
        R2PROMPT_ROOT = td
        try:
            bad = c68()["cell_pairs_counted_twice"]
        finally:
            R2PROMPT_ROOT = saved
    results.append(("C68", good != bad, good, bad, "O2's rows replaced by a relabelled copy of O1's"))

    print("redgreen -- falsify the SOURCE, require the claim to move")
    ok = True
    for claim, moved, g, b, how in results:
        ok &= moved
        print(f"  {'RED->GREEN' if moved else 'NO-MOVE   '} {claim}  {how}")
        print(f"             intact={g!r}  falsified={b!r}")
    print(f"  {'PASS' if ok else 'FAIL'}  {sum(1 for r in results if r[1])}/{len(results)} claims move when their source is falsified")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if len(argv) == 1 or argv[1] in ("-h", "--help"):
        print(__doc__)
        print("claims:", " ".join(FUNCS))
        return 0
    claims = argv[1:]
    if claims == ["all"]:
        claims = list(FUNCS)
    if claims == ["redgreen"]:
        return redgreen()
    if claims == ["dump"]:
        print(json.dumps({c: FUNCS[c]() for c in FUNCS}, indent=1, sort_keys=True, default=str))
        return 0
    status = 0
    for claim in claims:
        if claim not in FUNCS:
            print(f"unknown claim {claim!r}; known: {' '.join(FUNCS)} (or 'dump')")
            return 2
        if claim in EXPECTED:
            status |= check(claim)
        else:
            print(json.dumps(FUNCS[claim](), indent=1, sort_keys=True, default=str))
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
