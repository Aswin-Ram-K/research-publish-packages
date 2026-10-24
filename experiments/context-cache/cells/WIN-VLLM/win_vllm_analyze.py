#!/usr/bin/env python3
"""WIN-VLLM offline analysis: grid law, instrument verdict, four-arm battery.

Reads rows.jsonl + logs/*.json, makes zero live requests.  Usage:
    .venv/bin/python win_vllm_analyze.py
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROWS = HERE / "rows.jsonl"
LOGS = HERE / "logs"
OUT = HERE / "analysis.json"
SGLANG_LAW = "64*floor((L-1)/64)"
GRID_CANDIDATES = (16, 32, 64, 128, 1056)


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gcd_of(values) -> int:
    g = 0
    for v in values:
        g = math.gcd(g, int(v))
    return g


def fit_grid(points: list[tuple[int, int]]) -> dict:
    """points: (L, cached). Exact-fit counts for each candidate granularity."""
    out = {}
    for g in GRID_CANDIDATES:
        n_L = sum(1 for L, c in points if c == g * (L // g))
        n_Lm1 = sum(1 for L, c in points if c == g * ((L - 1) // g))
        out[str(g)] = {"exact_floor_L": n_L, "exact_floor_Lm1": n_Lm1, "n": len(points)}
    return out


def classify(points: list[tuple[int, int]], observed_g: int) -> dict:
    """Boundary probe: what happens exactly at multiples of the observed block?"""
    at_multiple = [(L, c) for L, c in points if L % observed_g == 0]
    off_multiple = [(L, c) for L, c in points if L % observed_g != 0]
    tax_at_multiple = [L - c for L, c in at_multiple]
    full_block = sum(1 for L, c in at_multiple if c == L)
    minus_one = sum(1 for L, c in at_multiple if c == L - observed_g)
    at_multiple_zero = sum(1 for L, c in at_multiple if c == 0)
    return {
        "n_at_multiple": len(at_multiple),
        "n_off_multiple": len(off_multiple),
        "at_multiple_full_cached": full_block,
        "at_multiple_n_zero": at_multiple_zero,
        "at_multiple_minus_one_block": minus_one,
        "at_multiple_tax_tokens": tax_at_multiple,
        "off_multiple_exact_floor_L": sum(1 for L, c in off_multiple if c == observed_g * (L // observed_g)),
    }


def battery_stats(rows: list[dict]) -> dict:
    by_arm = defaultdict(list)
    for r in rows:
        if r.get("phase") != "battery":
            continue
        by_arm[str(r.get("arm"))].append(r)
    out = {}
    for arm, rs in sorted(by_arm.items()):
        ok = [r for r in rs if r.get("status") == 200]
        tp = sum(int(r["prompt_tokens"]) for r in ok)
        tc = sum(int(r["cached_tokens"]) for r in ok)
        tu = sum(int(r["uncached"]) for r in ok)
        steady = [r for r in ok if int(r.get("turn") or 0) > 1]
        pts = [(int(r["prompt_tokens"]), int(r["cached_tokens"])) for r in steady]
        g = gcd_of([c for _, c in pts]) if pts else 0
        out[arm] = {
            "n": len(rs), "n_ok": len(ok),
            "errors": len(rs) - len(ok),
            "turns": [int(r.get("turn") or 0) for r in ok][:1] + [
                int(r.get("turn") or 0) for r in ok][-1:],
            "total_prompt_tokens": tp,
            "total_cached_tokens": tc,
            "total_uncached_tokens": tu,
            "hit_fraction": round(tc / tp, 6) if tp else None,
            "mean_uncached_per_turn": round(tu / len(ok), 2) if ok else None,
            "min_uncached": min((int(r["uncached"]) for r in ok), default=None),
            "median_uncached": (sorted(int(r["uncached"]) for r in ok)[len(ok) // 2] if ok else None),
            "steady_gcd_cached": g,
            "steady_fit": fit_grid(pts) if pts else {},
            "steady_points": pts,
            "max_prompt_tokens": max((int(r["prompt_tokens"]) for r in ok), default=None),
            "ttft_ms_median": (sorted(r["ttft_ms"] for r in ok)[len(ok) // 2] if ok else None),
        }
    return out


def dedupe_grid(grid_rows: list[dict]) -> list[dict]:
    """Keep the first observation per (salt, rep): later runs re-used salt indices."""
    seen = set()
    out = []
    for r in sorted(grid_rows, key=lambda r: str(r.get("ts_utc") or "")):
        key = (r.get("salt"), int(r.get("rep") or 0), int(r.get("prompt_tokens") or 0))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def law_forms(points, g: int) -> dict:
    """Candidate laws for an identical repeat of an L-token prompt."""
    if not g:
        return {}
    forms = {
        "g*floor(L/g)": lambda L: g * (L // g),
        "g*floor((L-1)/g)": lambda L: g * ((L - 1) // g),
        "g*(floor(L/g)-1), 0 at multiples":
            lambda L: 0 if L % g == 0 else max(0, g * ((L // g) - 1)),
    }
    out = {}
    for name, fn in forms.items():
        hits = [(L, c) for L, c in points if c == fn(L)]
        out[name] = {"exact": len(hits), "n": len(points),
                     "mismatches": [{"L": L, "cached": c, "law": fn(L)}
                                    for L, c in points if c != fn(L)]}
    return out


def grid_section(rows: list[dict]) -> dict:
    grid_rows = dedupe_grid([r for r in rows if r.get("phase") == "grid"])
    by_rep = defaultdict(list)
    for r in grid_rows:
        by_rep[int(r.get("rep") or 0)].append(r)
    rep1 = sorted(by_rep.get(1, []), key=lambda r: int(r.get("prompt_tokens") or 0))
    rep0 = {int(r["prompt_tokens"]): r for r in by_rep.get(0, [])}
    points = [(int(r["prompt_tokens"]), int(r["cached_tokens"])) for r in rep1]
    if not points:
        return {"measured": False}
    g = gcd_of([c for _, c in points if c])
    at_multiple = classify(points, g) if g else {}
    laws = law_forms(points, g)
    rep2 = sorted(by_rep.get(2, []), key=lambda r: int(r.get("target_L") or 0))
    rep3 = sorted(by_rep.get(3, []), key=lambda r: int(r.get("target_L") or 0))
    persistence = []
    for r2 in rep2:
        target = int(r2.get("target_L") or 0)
        r1 = next((x for x in rep1 if int(x.get("target_L") or 0) == target), None)
        r3 = next((x for x in rep3 if int(x.get("target_L") or 0) == target), None)
        persistence.append({
            "target_L": target, "L": r2["prompt_tokens"],
            "rep1": r1["cached_tokens"] if r1 else None,
            "rep2": r2["cached_tokens"],
            "rep3": r3["cached_tokens"] if r3 else None,
        })
    best = None
    if laws:
        best = max(laws.items(), key=lambda kv: kv[1]["exact"])[0]
    return {
        "measured": True,
        "n_lengths": len(rep1),
        "granularity_tokens": g,
        "law_forms": laws,
        "best_law": best,
        "points": [{"target_L": r["target_L"], "L": r["prompt_tokens"],
                    "cold_cached": (rep0.get(int(r["prompt_tokens"])) or {}).get("cached_tokens"),
                    "cached_rep1": r["cached_tokens"], "uncached": r["uncached"],
                    "wall_ms": r["wall_ms"], "status": r["status"]} for r in rep1],
        "fit": fit_grid(points),
        "boundary": at_multiple,
        "persistence": persistence,
        "vs_sglang": {
            "sglang_law": SGLANG_LAW,
            "exact_matches_floor_Lm1_64": sum(1 for L, c in points if c == 64 * ((L - 1) // 64)),
            "exact_matches_floor_L_64": sum(1 for L, c in points if c == 64 * (L // 64)),
            "n": len(points),
            "same_law": bool(g == 64 and all(c == 64 * (L // 64) for L, c in points)),
        },
    }


def sglang_baseline() -> dict:
    """SGLang S0 (page_size 1) 32k battery, as recorded by WIN-SGL from G3's rows."""
    path = REPO / "experiments" / "context-cache" / "cells" / "WIN-SGL" / "analysis.json"
    if not path.exists():
        return {"available": False}
    data = json.loads(path.read_text())
    depths = ((((data.get("configs") or {}).get("S0") or {}).get("battery") or {})
              .get("depths") or {})
    d32 = depths.get("32k") or {}
    return {
        "available": bool(d32),
        "source": str(path.relative_to(REPO)),
        "source_sha256": sha(path),
        "page_size": 1,
        "arms": {arm: {"n": v.get("n"), "hit_fraction": v.get("hit_fraction"),
                       "mean_uncached_per_turn": v.get("mean_uncached_per_turn"),
                       "total_uncached_tokens": v.get("total_uncached_tokens")}
                 for arm, v in d32.items()},
        "arm_mean_uncached": round(
            sum(v.get("mean_uncached_per_turn") or 0 for v in d32.values()) / len(d32), 2)
        if d32 else None,
    }


def v3_attempts() -> list:
    out = []
    for name, note in (("V3-launch-attempt1-mtp.json", "with production --speculative-config mtp"),
                       ("V3-launch.json", "retry without --speculative-config")):
        path = LOGS / name
        if not path.exists():
            continue
        rec = json.loads(path.read_text())
        tail = rec.get("log_tail") or ""
        root = [ln for ln in tail.splitlines()
                if "RuntimeError" in ln or "Error" in ln][-3:]
        out.append({
            "record": name, "note": note, "launched": rec.get("launched"),
            "health_status": rec.get("health_status"),
            "waited_s": rec.get("health_wait_s"),
            "root_cause_lines": [ln.strip() for ln in root],
            "spec_sha256": (rec.get("spec") or {}).get("config_sha256"),
            "block_size_resolved": (((rec.get("metrics") or {}).get("cache_config_info"))) or None,
        })
    return out


def main() -> int:
    rows = load_rows(ROWS)
    configs = {}
    for cfg in ("V1", "V2", "V3"):
        crows = [r for r in rows if r.get("config_id") == cfg]
        launch_path = LOGS / f"{cfg}-launch.json"
        restore_path = LOGS / f"{cfg}-restore.json"
        launch = json.loads(launch_path.read_text()) if launch_path.exists() else None
        restore = json.loads(restore_path.read_text()) if restore_path.exists() else None
        gate_rows = [r for r in crows if r.get("phase") == "gate"]
        gate_groups = defaultdict(list)
        for r in gate_rows:
            gate_groups[str(r.get("salt"))].append(r)
        gate_detail = []
        for salt, rs in gate_groups.items():
            rs = sorted(rs, key=lambda r: str(r.get("ts_utc") or ""))
            gate_detail.append({
                "salt": salt, "n": len(rs),
                "L": [r["prompt_tokens"] for r in rs],
                "cached": [r["cached_tokens"] for r in rs],
                "repeat_hit": bool(len(rs) >= 2 and (rs[-1].get("cached_tokens") or 0) > 0),
            })
        instrument = any(g["repeat_hit"] for g in gate_detail)
        cfg_info = {
            "config_id": cfg,
            "rows": len(crows),
            "block_size": (crows[0]["block_size"] if crows else (launch or {}).get("spec", {}).get("block_size")),
            "quant": (crows[0]["quant"] if crows else (launch or {}).get("spec", {}).get("quantization")),
            "served_model": (crows[0]["served_model"] if crows else None),
            "max_model_len": (crows[0]["max_model_len"] if crows else 32768),
            "config_sha256": (crows[0]["config_sha256"] if crows else (launch or {}).get("spec", {}).get("config_sha256")),
            "launched": bool(launch and launch.get("launched")),
            "launch_health": (launch or {}).get("health_status"),
            "launch_wait_s": (launch or {}).get("health_wait_s"),
            "launch_reason": (launch or {}).get("reason"),
            "startup_log_tail": ((launch or {}).get("log_tail") or "")[-4000:] if launch and not launch.get("launched") else None,
            "instrument_available": instrument,
            "gate": gate_detail,
            "restore": None if restore is None else {
                "health": restore.get("health"),
                "models_id": (restore.get("models") or {}).get("id"),
                "max_model_len": (restore.get("models") or {}).get("max_model_len"),
                "block_size_metric": (restore.get("metrics") or {}).get("cache_config_info"),
                "config_ok": restore.get("config_ok"),
                "compared_keys": restore.get("compared_keys"),
                "all_compared_ok": restore.get("all_compared_ok"),
                "occamy": (restore.get("occamy") or {}).get("status"),
            },
        }
        if cfg_info["launched"] and instrument:
            cfg_info["grid"] = grid_section(crows)
            cfg_info["battery"] = battery_stats(crows)
        configs[cfg] = cfg_info

    total_prompt = sum(int(r["prompt_tokens"]) for r in rows if r.get("status") == 200)
    total_cached = sum(int(r["cached_tokens"]) for r in rows if r.get("status") == 200)
    by_phase = Counter(str(r.get("phase")) for r in rows)
    by_cfg_phase = Counter((r.get("config_id"), r.get("phase")) for r in rows)

    laws = {}
    for cfg, info in configs.items():
        grid = info.get("grid") or {}
        if grid.get("measured"):
            g = grid["granularity_tokens"]
            best = grid.get("best_law")
            law_txt = {
                "g*floor(L/g)": f"{g}*floor(L/{g})",
                "g*floor((L-1)/g)": f"{g}*floor((L-1)/{g})",
                "g*(floor(L/g)-1), 0 at multiples":
                    f"{g}*(floor(L/{g})-1) for L mod {g} != 0; 0 at L mod {g} == 0",
            }.get(best, str(best))
            laws[cfg] = {
                "granularity_tokens": g,
                "law_form": law_txt,
                "law_exact": (grid.get("law_forms") or {}).get(best, {}).get("exact"),
                "law_n": (grid.get("law_forms") or {}).get(best, {}).get("n"),
                "all_law_fits": {k: v["exact"] for k, v in (grid.get("law_forms") or {}).items()},
                "same_as_sglang_64_floor_Lm1": (g == 64 and best in (
                    "g*floor(L/g)", "g*floor((L-1)/g)")),
                "sglang_law_matches": grid["vs_sglang"]["exact_matches_floor_Lm1_64"],
                "n_points": grid["vs_sglang"]["n"],
                "multiples_zero": grid["boundary"].get("at_multiple_n_zero")
                if "at_multiple_n_zero" in grid["boundary"] else None,
            }
        else:
            laws[cfg] = {"measured": False,
                         "reason": info.get("launch_reason") or "instrument unavailable"}

    payload = {
        "unit": "WIN-VLLM",
        "purpose": "characterise the vLLM 0.27.1 pager/flag space on a dense-but-hybrid 9B: "
                   "NVFP4 modelopt_fp4 at --block-size 64 (V1) and 16 (V2), instrument on",
        "stack": "vllm",
        "engine_version": "0.27.1",
        "image": "sha256:2c211a1273b48e8929f893b267aeb1509e6b84654cdbde1bad56d79e3964224d",
        "endpoint": "http://192.168.2.168:8014/v1",
        "row_fields": ["stack", "config_id", "config_sha256", "block_size", "quant",
                       "served_model", "max_model_len", "phase", "depth", "arm", "turn",
                       "target_L", "rep", "prompt_tokens", "cached_tokens", "uncached",
                       "ttft_ms", "wall_ms", "status"],
        "configs": configs,
        "grid_law": laws,
        "sglang_law_baseline": SGLANG_LAW,
        "sglang_32k_baseline": sglang_baseline(),
        "v3_launch_attempts": v3_attempts(),
        "requests": {
            "live_total": len(rows),
            "bound": 900,
            "by_phase": dict(by_phase),
            "by_config_phase": {f"{k[0]}/{k[1]}": v for k, v in sorted(by_cfg_phase.items())},
            "non_generation_calls": "POST /tokenize (token counting, no generation) is not "
                                    "counted against the live bound and is recorded separately",
        },
        "tokens": {"prompt": total_prompt, "cached": total_cached,
                   "hit_fraction": round(total_cached / total_prompt, 6) if total_prompt else None},
        "rows_sha256": sha(ROWS),
        "n_rows": len(rows),
        "assumptions": {
            "depth_64k": "not runnable: the 64k depth needs prompts up to ~67,000 tokens but the "
                         "launch invariant pins --max-model-len 32768; the 32k battery is itself "
                         "truncated where the rendered prompt would exceed 32768",
            "depth_32k": "same corpus, salts and renderer as G3 (SGLang S0), so rows are comparable "
                         "prompt-for-prompt; the truncation is computed offline from /tokenize",
            "v3": "occamy on vLLM is a bounded load probe only (40 min / 3 attempts), no battery",
            "comparison": "SGLang's 64-grid law was measured on occamy-1.0 (MoE hybrid) on SGLang; "
                          "here it is tested on a different model and stack, so a match is a "
                          "stack-level replication, not a same-weights comparison",
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("grid_law", "requests", "tokens", "n_rows")},
                     indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
