#!/usr/bin/env python3
"""Freeze a cs.envelope/1 for the context-serving campaign."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CAMPAIGN_ROOT = Path(os.environ.get(
    "CAMPAIGN_ROOT",
    "/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN",
)).resolve()

FORBIDDEN = ("cells/COMBINED-CONTEXT-SERVING", "cells/HL-PILOT")


def _sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _sha256_obj(obj):
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _check_path(p):
    s = str(p)
    if any(f in s for f in FORBIDDEN):
        raise SystemExit(f"refusing path containing forbidden cell: {s}")
    # resolve inside campaign root
    pp = Path(p)
    if not pp.is_absolute():
        pp = (CAMPAIGN_ROOT / pp).resolve()
    else:
        pp = pp.resolve()
    try:
        pp.relative_to(CAMPAIGN_ROOT)
    except ValueError:
        raise SystemExit(f"refusing path outside campaign root: {pp}")
    return str(pp)


def _normalise_server_info(si):
    # keep deterministic subset
    return si


def compute_fingerprint(server_info_path=None, models_path=None):
    si = None
    models = None
    if server_info_path and Path(server_info_path).is_file():
        si = json.loads(Path(server_info_path).read_text())
    if models_path and Path(models_path).is_file():
        models = json.loads(Path(models_path).read_text())
    if si is None:
        # default from pins
        inv = json.loads((CAMPAIGN_ROOT / "pins" / "serving-inventory.json").read_text())
        si = {
            "model_path": inv["sglang"]["model_path_container"],
            "arch": inv["sglang"].get("architecture"),
            "kv_cache_dtype": inv["sglang"].get("kv_cache_dtype"),
            "context_length": inv["sglang"].get("context_length"),
            "radix_cache_enabled": inv["sglang"].get("radix_cache_enabled"),
            "hicache_enabled": inv["sglang"].get("hicache_enabled"),
        }
        models = {"data": [{"id": inv["sglang"]["served_model_name"]}]}
    norm = {"server_info": si, "models": models}
    return _sha256_obj(norm), si, models


def build_envelope(args):
    inv = json.loads((CAMPAIGN_ROOT / "pins" / "serving-inventory.json").read_text())
    fp, si, models = compute_fingerprint(args.server_info, args.models)
    weights_path = inv["sglang"]["model_path_container"]
    arch = inv["sglang"]["architecture"]
    hashes = inv["hashes"]
    serving_flags = [
        "sglang", "serve",
        "--model-path", weights_path,
        "--served-model-name", inv["sglang"]["served_model_name"],
        "--host", "0.0.0.0", "--port", "30000", "--tp-size", "1",
        "--trust-remote-code", "--quantization", "modelopt_fp4", "--dtype", "bfloat16",
        "--context-length", "131072", "--mem-fraction-static", "0.45",
        "--kv-cache-dtype", "fp8_e4m3",
        "--chunked-prefill-size", "8192", "--max-running-requests", "5",
        "--mamba-radix-cache-strategy", "extra_buffer", "--mamba-track-interval", "256",
        "--max-mamba-cache-size", "64", "--mamba-ssm-dtype", "float32",
        "--attention-backend", "triton", "--mamba-backend", "triton",
        "--mm-attention-backend", "sdpa", "--moe-runner-backend", "flashinfer_cutlass",
        "--cuda-graph-max-bs-decode", "8", "--reasoning-parser", "qwen3", "--tool-call-parser", "qwen3_coder",
        "--enable-metrics", "--enable-cache-report",
    ]
    # renderer hashes
    arms_dir = CAMPAIGN_ROOT / "arms"
    if str(arms_dir) not in sys.path:
        sys.path.insert(0, str(arms_dir))
    # invalidate caches
    import importlib
    importlib.invalidate_caches()
    # remove pycache
    import shutil
    pc = arms_dir / "__pycache__"
    if pc.exists():
        shutil.rmtree(pc, ignore_errors=True)
    import render_arms as ra
    importlib.reload(ra)
    arms_list = ["A", "B", "C", "D"]
    per_arm = {a: ra.renderer_sha256(a) for a in arms_list}
    # grader
    grader_path = CAMPAIGN_ROOT / "tasks" / "grade.py"
    grader_sha = _sha256_file(grader_path)
    # tasks
    instances_dir = CAMPAIGN_ROOT / "tasks" / "instances"
    discovery = sorted(p.stem for p in instances_dir.glob("D*.json"))
    heldout = sorted(p.stem for p in instances_dir.glob("H*.json"))
    # normalize to D1.. not file stem? keep as is
    discovery = [p.stem for p in sorted(instances_dir.glob("D*.json"))]
    heldout = [p.stem for p in sorted(instances_dir.glob("H*.json"))]
    # digest over instance files
    inst_hash = hashlib.sha256()
    for p in sorted(instances_dir.glob("*.json")):
        inst_hash.update(p.name.encode())
        inst_hash.update(p.read_bytes())
    instances_sha256 = inst_hash.hexdigest()

    max_tokens = args.max_tokens
    # paths
    root_rel = "."
    def R(rel):
        return rel
    env = {
        "schema": "cs.envelope/1",
        "run_id": args.run_id,
        "revision": 1,
        "campaign_root": str(CAMPAIGN_ROOT),
        "endpoint": {
            "base_url": args.base_url,
            "model": inv["sglang"]["served_model_name"],
            "fingerprint_sha256": fp,
            "resolved_config_sha256": __import__("hashlib").sha256(__import__("json").dumps(serving_flags, sort_keys=True).encode()).hexdigest(),
        },
        "model": {
            "weights_path": weights_path,
            "arch": arch,
            "weights_index_sha256": hashes["model.safetensors.index.json"],
            "tokenizer_sha256": hashes["tokenizer.json"],
            "tokenizer_config_sha256": hashes["tokenizer_config.json"],
            "config_sha256": hashes["config.json"],
        },
        "image": {
            "container": inv["sglang"]["container"],
            "image_sha256": inv["sglang"]["image_digest"],
        },
        "serving_flags": serving_flags,
        "renderer": {
            "arms": arms_list,
            "per_arm_renderer_sha256": per_arm,
            "mask_after": args.mask_after,
        },
        "grader": {
            "path": str(grader_path.relative_to(CAMPAIGN_ROOT)),
            "sha256": grader_sha,
        },
        "tasks": {
            "discovery": discovery,
            "heldout": heldout,
            "instances_sha256": instances_sha256,
        },
        "seeds": {
            "preflight": args.preflight_seeds,
            "context": args.context_seeds,
            "prompt_format": args.prompt_seeds,
            "serving": args.serving_seeds,
            "holdout": args.holdout_seeds,
            "contingency": args.contingency_seeds,
        },
        "limits": {
            "max_tokens": max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "turns_per_task": args.turns,
            "reps": args.reps,
            "request_timeout_s": args.request_timeout,
        },
        "watcher": {
            "interval_s": args.watcher_interval,
            "first_row_deadline_s": args.first_row_deadline,
            "row_gap_deadline_s": args.row_gap_deadline,
        },
        "paths": {
            "rows": {ph: f"run/rows/{ph}.jsonl" for ph in
                     ["preflight", "context", "prompt_format", "serving", "holdout", "contingency"]},
            "intents": {ph: f"run/intents/{ph}.jsonl" for ph in
                        ["preflight", "context", "prompt_format", "serving", "holdout", "contingency"]},
            "graded": {ph: f"run/graded/{ph}" for ph in
                       ["preflight", "context", "prompt_format", "serving", "holdout", "contingency"]},
            "artifacts": {ph: f"run/artifacts/{ph}" for ph in
                          ["preflight", "context", "prompt_format", "serving", "holdout", "contingency"]},
            "watcher_events": f"run/watcher/{{phase}}.jsonl",
        },
        "planned_calls": {
            "preflight": 48,
            "context": 384,
            "prompt_format": 192,
            "serving": 288,
            "holdout": 384,
            "contingency": 204,
        },
        "cache": {
            "namespace": args.namespace,
            "cold_warm_order": args.cold_warm_order,
        },
        "freeze": {
            "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "supersedes": None,
            "revision_reason": args.reason,
        },
    }
    # hand-supplied renderer hash check
    hand = getattr(args, "renderer_hashes_json", None)
    if hand:
        try:
            expected = json.loads(Path(hand).read_text()) if Path(hand).is_file() else json.loads(hand)
        except Exception:
            expected = json.loads(hand)
        for arm in arms_list:
            if arm in expected and expected[arm] != per_arm[arm]:
                raise SystemExit(f"freeze abort: hand-supplied renderer hash mismatch for {arm}: {expected[arm]} != {per_arm[arm]}")

    # validate paths
    for cat in ("rows", "intents", "graded", "artifacts"):
        for ph, p in env["paths"][cat].items():
            _check_path(p)
    _check_path(env["paths"]["watcher_events"])
    # health check
    health_check = getattr(args, "_health_check", None) or "offline: no live health check"
    env["freeze"]["health_check"] = health_check

    # self digest over canonical body excluding freeze.envelope_sha256
    body = {k: v for k, v in env.items() if k != "freeze"}
    # include freeze except envelope_sha256
    body["freeze"] = {k: v for k, v in env["freeze"].items() if k != "envelope_sha256"}
    digest = _sha256_obj(body)
    env["freeze"]["envelope_sha256"] = digest
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", default="CONTEXT-SERVING-2026-11-05")
    ap.add_argument("--base-url", default="http://192.168.2.168:8012")
    ap.add_argument("--max-tokens", type=int, default=3200)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--turns", type=int, default=12)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--request-timeout", type=int, default=180)
    ap.add_argument("--mask-after", type=int, default=6)
    ap.add_argument("--watcher-interval", type=int, default=120)
    ap.add_argument("--first-row-deadline", type=int, default=300)
    ap.add_argument("--row-gap-deadline", type=int, default=600)
    ap.add_argument("--namespace", default="campaign-v1")
    ap.add_argument("--cold-warm-order", default="cold_then_warm")
    ap.add_argument("--reason", default=None)
    ap.add_argument("--server-info", default=None)
    ap.add_argument("--models", default=None)
    ap.add_argument("--preflight-seeds", nargs="+", type=int, default=[1101, 1102])
    ap.add_argument("--context-seeds", nargs="+", type=int, default=[1101, 1102])
    ap.add_argument("--prompt-seeds", nargs="+", type=int, default=[1101, 1102])
    ap.add_argument("--serving-seeds", nargs="+", type=int, default=[1101, 1102])
    ap.add_argument("--holdout-seeds", nargs="+", type=int, default=[2101, 2102, 2103, 2104])
    ap.add_argument("--contingency-seeds", nargs="+", type=int, default=[3101])
    ap.add_argument("--allow-revision", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--renderer-hashes-json", default=None)
    ap.add_argument("--verify-endpoint", action="store_true")
    args = ap.parse_args()

    health_check = "offline: no live health check"
    if args.verify_endpoint:
        import urllib.request
        try:
            base = args.base_url.rstrip("/")
            with urllib.request.urlopen(base + "/v1/models", timeout=10) as r:
                models = json.loads(r.read())
            with urllib.request.urlopen(base + "/get_server_info", timeout=10) as r:
                si = json.loads(r.read())
            model_id = None
            try:
                model_id = models["data"][0]["id"]
            except Exception:
                model_id = models.get("id")
            mp = si.get("model_path") or si.get("modelPath")
            ok = (model_id == "occamy-1.0")
            # pinned snapshot
            pinned = "/root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652"
            if mp is not None:
                ok = ok and (mp == pinned)
            health_check = json.dumps({"models": models, "server_info": si, "ok": ok})
            if not ok:
                print("error: health check failed", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"error: health check failed: {e}", file=sys.stderr)
            sys.exit(1)
    args._health_check = health_check

    out = Path(args.out)
    if not out.is_absolute():
        out = (CAMPAIGN_ROOT / out).resolve()
    else:
        out = out.resolve()
    # re-freeze check
    if out.exists():
        old = json.loads(out.read_text())
        # check spent phases via ledger
        spent_any = False
        try:
            import subprocess
            # find ledger.py
            ledger_py = CAMPAIGN_ROOT / "ledger" / "ledger.py"
            res = subprocess.run(
                [sys.executable, str(ledger_py), "status", "--json"],
                capture_output=True, text=True,
            )
            if res.returncode == 0:
                st = json.loads(res.stdout)
                for ph, info in st.get("per_phase", {}).items():
                    if info.get("spent", 0) > 0:
                        spent_any = True
        except Exception:
            spent_any = False
        if spent_any and not args.force:
            if not args.allow_revision:
                print("error: re-freeze refused: a phase has already spent calls; pass --allow-revision --reason ...", file=sys.stderr)
                sys.exit(1)
            # require reason
            if not args.reason:
                print("error: revision requires --reason", file=sys.stderr)
                sys.exit(1)
            # check diff only max_tokens
            new_env = build_envelope(args)
            # compare canonical (excluding freeze) 
            def canon(e):
                c = {k: v for k, v in e.items() if k != "freeze"}
                c["freeze"] = {k: v for k, v in e["freeze"].items() if k not in ("envelope_sha256", "supersedes", "revision_reason", "frozen_at")}
                return c
            old_c = canon(old)
            new_c = canon(new_env)
            # remove max_tokens from comparison
            def strip_mt(e):
                e = json.loads(json.dumps(e))
                if "limits" in e and isinstance(e["limits"], dict):
                    e["limits"].pop("max_tokens", None)
                return e
            if (not args.force) and strip_mt(old_c) != strip_mt(new_c):
                print("error: re-freeze may only change limits.max_tokens", file=sys.stderr)
                sys.exit(1)
            new_env["freeze"]["supersedes"] = old.get("freeze", {}).get("envelope_sha256")
            new_env["revision"] = old.get("revision", 0) + 1
            # recompute digest
            body = {k: v for k, v in new_env.items() if k != "freeze"}
            body["freeze"] = {k: v for k, v in new_env["freeze"].items() if k != "envelope_sha256"}
            body["freeze"]["supersedes"] = new_env["freeze"]["supersedes"]
            new_env["freeze"]["envelope_sha256"] = _sha256_obj(body)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(new_env, indent=2) + "\n")
            print(str(out))
            return
    new_env = build_envelope(args)
    if out.exists():
        # no spent: allow overwrite? still record supersedes maybe
        try:
            old = json.loads(out.read_text())
            new_env["freeze"]["supersedes"] = old.get("freeze", {}).get("envelope_sha256")
            new_env["revision"] = old.get("revision", 0) + 1
            body = {k: v for k, v in new_env.items() if k != "freeze"}
            body["freeze"] = {k: v for k, v in new_env["freeze"].items() if k != "envelope_sha256"}
            new_env["freeze"]["envelope_sha256"] = _sha256_obj(body)
        except Exception:
            pass
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(new_env, indent=2) + "\n")
    print(str(out))


if __name__ == "__main__":
    main()
