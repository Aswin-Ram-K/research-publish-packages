#!/usr/bin/env python3
"""MOE-VLLM — launch occamy-1.0 (NVFP4 MoE) on vLLM 0.27.1 at :8020, and restore production.

The launch recipe is WIN-VLLM's *measured* V3 spec, imported rather than
re-typed so `config_sha256` stays 302ebd820e9c7b87dbba18905ad91a20a37ee55060ee97871edb8cfdb43cd060
(verified identical offline against logs/V3-launch.json).  The only local
change is where the logs go: this cell's logs/, never WIN-VLLM's frozen record.

Every hard rule of the original wrapper still holds:
  * absolute host paths only, never a literal "~";
  * production gx10-qwen9b is stopped, never removed -> restore is `docker start`;
  * occamy :8012 (gx10-occamy-nvfp4) is never touched, and its health is
    re-checked after every step;
  * the variant is a fresh container (wv-v3) on :8020, --gpu-memory-utilization
    0.32 so it coexists with the production SGLang container (0.45).

The V3 probe showed the recipe serves occamy-1.0 only WITHOUT
--speculative-config: attempt 1 died with
"RuntimeError: No Qwen3Next layer found in the model.layers."  `no_spec` is
therefore pinned here, not left to the caller.

CLI:
  --capture            capture production + occamy state into this cell's logs
  --launch             stop production, run the variant, wait for /health
  --restore            remove the variant, start production, prove it is back
  --health             occamy + production health only (0 model requests)
  --spec               print the resolved spec (no network)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WIN_DIR = HERE.parent / "WIN-VLLM"
LOGS = HERE / "logs"
LOGS.mkdir(parents=True, exist_ok=True)


def _load_recipe():
    path = WIN_DIR / "launch_variant.py"
    spec = importlib.util.spec_from_file_location("win_vllm_launch_variant", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lv = _load_recipe()
# Redirect this cell's records away from WIN-VLLM's frozen 692-row record.
lv.LOGS = LOGS
lv.CONFIGS["V3"]["no_spec"] = True
lv.CONFIGS["V3"]["label"] = "occamy-nvfp4-moe on vllm (full four-arm battery)"

CONFIGS = lv.CONFIGS
build_spec = lv.build_spec
launch = lv.launch
restore = lv.restore
capture_models = lv.capture_models


def capture() -> dict:
    payload = {
        "unit": "MOE-VLLM",
        "phase": "capture",
        "prod_health": lv.health(lv.PROD_PORT),
        "prod_models": capture_models(lv.PROD_PORT),
        "occamy": lv.occamy_health(),
    }
    out = LOGS / "capture.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(f"capture: prod_health={payload['prod_health']} "
          f"prod_id={payload['prod_models'].get('id')} occamy={payload['occamy']['status']}",
          flush=True)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--health", action="store_true")
    ap.add_argument("--spec", action="store_true")
    ap.add_argument("--wait", type=int, default=480, help="health wait budget (s)")
    args = ap.parse_args()
    if args.spec:
        print(json.dumps(build_spec("V3"), indent=1))
    if args.capture:
        capture()
    if args.launch:
        rec = launch("V3", timeout_s=args.wait)
        return 0 if rec.get("launched") else 2
    if args.restore:
        rec = restore("V3")
        return 0 if rec.get("config_ok") else 3
    if args.health:
        print(json.dumps({"occamy": lv.occamy_health(),
                          "prod_health": lv.health(lv.PROD_PORT),
                          "models": capture_models(lv.PROD_PORT)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
