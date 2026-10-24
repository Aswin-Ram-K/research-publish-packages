#!/usr/bin/env python3
"""WIN-VLLM — launch a vLLM variant on the gx10 box and restore production.

Hard rules encoded here (see the unit card):
  * absolute host paths only, never a literal "~";
  * the NVFP4 checkout is mounted at /model-nvfp4 (production's /model untouched);
  * the vllm-cache mount is copied verbatim from the production container;
  * every flag except --model / --quantization / --block-size /
    --enable-prompt-tokens-details is copied verbatim from
    `docker inspect gx10-qwen9b` (measured 2026-10-22, not from a doc);
  * production is stopped, never removed -> restore is `docker start`;
  * occamy (:8012) is never touched and its health is re-checked after every step.

CLI:
  --capture-pre        capture production inspect + /v1/models + /health + /metrics
  --launch V1|V2|V3    stop production, run the variant, wait for /health, capture
  --restore V1|V2|V3   remove the variant, start production, prove it is back
  --health             occamy + production health only (0 model requests)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LOGS = HERE / "logs"
STATE = REPO / "state" / "config"

SSH = [
    "ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8", "-o", "LogLevel=ERROR",
    "zer0null@192.168.2.168",
]

IMAGE = "sha256:2c211a1273b48e8929f893b267aeb1509e6b84654cdbde1bad56d79e3964224d"
PROD_NAME = "gx10-qwen9b"
PROD_PORT = 8014
BASE_URL = f"http://192.168.2.168:{PROD_PORT}"

# verbatim from the production container (docker inspect gx10-qwen9b, 2026-10-22)
PROD_FLAGS = [
    "--served-model-name", "qwen3.5-9b",
    "--host", "0.0.0.0",
    "--port", "30000",
    "--tensor-parallel-size", "1",
    "--dtype", "bfloat16",
    "--kv-cache-dtype", "fp8",
    "--max-model-len", "32768",
    "--gpu-memory-utilization", "0.15",
    "--max-num-seqs", "6",
    "--max-num-batched-tokens", "8192",
    "--enable-chunked-prefill",
    "--enable-prefix-caching",
    "--speculative-config", '{"method":"mtp","num_speculative_tokens":1}',
    "--reasoning-parser", "qwen3",
    "--trust-remote-code",
]
CACHE_MOUNT = "/home/zer0null/.local/share/gx10-qwen9b/vllm-cache"
ENV = ["VLLM_CACHE_ROOT=/root/.cache/vllm", "HF_HUB_OFFLINE=1", "TRANSFORMERS_OFFLINE=1",
       "VLLM_ENABLE_CUDA_COMPATIBILITY=0"]

OCCAMY_SNAPSHOT = ("/home/zer0null/.cache/huggingface/hub/"
                   "models--Accio-Lab--occamy-1.0-NVFP4/snapshots/"
                   "fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652")

CONFIGS = {
    "V1": {
        "config_id": "V1",
        "stack": "vllm",
        "label": "nvfp4-9b block64",
        "model_host": "/home/zer0null/models/qwen3.5-9b-nvfp4",
        "model_ctr": "/model-nvfp4",
        "quantization": "modelopt_fp4",
        "block_size": 64,
        "served_model": "qwen3.5-9b",
        "max_model_len": 32768,
        "host_port": 8014,
        "container": "wv-v1",
    },
    "V2": {
        "config_id": "V2",
        "stack": "vllm",
        "label": "nvfp4-9b block16",
        "model_host": "/home/zer0null/models/qwen3.5-9b-nvfp4",
        "model_ctr": "/model-nvfp4",
        "quantization": "modelopt_fp4",
        "block_size": 16,
        "served_model": "qwen3.5-9b",
        "max_model_len": 32768,
        "host_port": 8014,
        "container": "wv-v2",
    },
    "V3": {
        "config_id": "V3",
        "stack": "vllm",
        "label": "occamy-nvfp4-moe on vllm (bounded probe)",
        "model_host": "/home/zer0null/.cache/huggingface",
        "model_ctr": "/hf-cache",
        "model_arg": "/hf-cache/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/"
                     "fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652",
        "quantization": "modelopt_fp4",
        "block_size": None,
        "served_model": "occamy-1.0",
        "max_model_len": 32768,
        "host_port": 8020,
        "container": "wv-v3",
        "gpu_mem": "0.32",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sh(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
    """Run a shell snippet on the box through `bash -s` (no local quoting involved)."""
    proc = subprocess.run([*SSH, "bash -s"], input=cmd, capture_output=True, text=True,
                          timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def docker(cmd: str, timeout: int = 180) -> tuple[int, str, str]:
    return sh(f"sudo -n docker {cmd}", timeout=timeout)


def http_get(path: str, port: int = PROD_PORT, timeout: int = 10) -> tuple[int, str]:
    code, out, _ = sh(
        f"curl -s -m {timeout} -o /tmp/winvllm.out -w '%{{http_code}}' "
        f"http://192.168.2.168:{port}{path} && cat /tmp/winvllm.out", timeout=timeout + 5)
    body = out
    status = 0
    if out and out[:3].isdigit():
        status = int(out[:3])
        body = out[3:]
    return status or (0 if code else 0), body


def capture_models(port: int = PROD_PORT) -> dict:
    status, body = http_get("/v1/models", port)
    out = {"http_status": status, "body": None, "id": None, "max_model_len": None, "root": None}
    try:
        data = json.loads(body)
        entry = (data.get("data") or [{}])[0]
        out["body"] = data
        out["id"] = entry.get("id")
        out["max_model_len"] = entry.get("max_model_len")
        out["root"] = entry.get("root")
    except Exception:
        out["raw"] = body[:2000]
    return out


def capture_metrics(port: int = PROD_PORT) -> dict:
    status, body = http_get("/metrics", port, timeout=15)
    info = None
    for line in body.splitlines():
        if line.startswith("vllm:cache_config_info"):
            info = line
            break
    return {"http_status": status, "cache_config_info": info}


def health(port: int) -> int:
    status, _ = http_get("/health", port)
    return status


def occamy_health() -> dict:
    return {"port": 8012, "status": health(8012), "checked_utc": utc_now()}


def config_sha256(spec: dict) -> str:
    payload = {
        "config_id": spec["config_id"],
        "image": IMAGE,
        "quantization": spec["quantization"],
        "block_size": spec["block_size"],
        "model_ctr": spec["model_ctr"],
        "cmd": spec["cmd"],
        "binds": spec["binds"],
        "env": ENV,
        "served_model": spec["served_model"],
        "max_model_len": spec["max_model_len"],
        "host_port": spec["host_port"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _replace_value(cmd: list, flag: str, value: str) -> list:
    out = list(cmd)
    if flag in out:
        out[out.index(flag) + 1] = value
    return out


def build_spec(config_id: str) -> dict:
    spec = dict(CONFIGS[config_id])
    model = spec.get("model_arg") or spec["model_ctr"]
    cmd = ["--model", model, *PROD_FLAGS]
    cmd = _replace_value(cmd, "--served-model-name", spec["served_model"])
    if spec.get("gpu_mem"):
        cmd = _replace_value(cmd, "--gpu-memory-utilization", spec["gpu_mem"])
    if spec.get("no_spec") and "--speculative-config" in cmd:
        idx = cmd.index("--speculative-config")
        del cmd[idx:idx + 2]
    if spec["block_size"] is not None:
        cmd += ["--block-size", str(spec["block_size"])]
    cmd += ["--quantization", spec["quantization"], "--enable-prompt-tokens-details"]
    binds = [f"{spec['model_host']}:{spec['model_ctr']}:ro", f"{CACHE_MOUNT}:/root/.cache/vllm"]
    spec["cmd"] = cmd
    spec["binds"] = binds
    spec["env"] = ENV
    spec["image"] = IMAGE
    spec["config_sha256"] = config_sha256(spec)
    return spec


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def capture_pre() -> dict:
    code, out, err = docker(f"inspect {PROD_NAME}", timeout=60)
    payload = {"unit": "WIN-VLLM", "captured_utc": utc_now(), "docker_inspect_rc": code}
    if code == 0:
        try:
            payload["inspect"] = json.loads(out)[0]
        except Exception:
            payload["inspect_raw"] = out[:20000]
    else:
        payload["stderr"] = err
    payload["models"] = capture_models()
    payload["metrics"] = capture_metrics()
    payload["health"] = health(PROD_PORT)
    payload["occamy"] = occamy_health()
    write_json(STATE / "qwen9b-inspect-pre.json", payload)
    print(f"capture-pre: health={payload['health']} id={payload['models']['id']} "
          f"max_model_len={payload['models']['max_model_len']} occamy={payload['occamy']['status']}",
          flush=True)
    return payload


def launch(config_id: str, timeout_s: int = 420) -> dict:
    spec = build_spec(config_id)
    LOGS.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    record: dict = {"unit": "WIN-VLLM", "phase": "launch", "config_id": config_id,
                    "started_utc": utc_now(), "spec": spec, "steps": []}

    def step(name: str, rc: int, out: str, err: str) -> None:
        record["steps"].append({"step": name, "rc": rc,
                                "stdout": out[-4000:], "stderr": err[-2000:]})

    rc, out, err = docker(f"stop {PROD_NAME}", timeout=120)
    step("stop-production", rc, out, err)
    rc, out, err = docker(f"rm -f {spec['container']}", timeout=120)
    step("rm-stale-variant", rc, out, err)

    args = ["run", "-d", "--name", spec["container"], "--restart", "no",
            "--gpus", "all", "--ipc", "host", "--shm-size", "16g",
            "--ulimit", "memlock=-1",
            "-p", f"{spec['host_port']}:30000"]
    for bind in spec["binds"]:
        args += ["-v", bind]
    for env in spec["env"]:
        args += ["-e", env]
    args.append(IMAGE)
    args += spec["cmd"]
    quoted = " ".join(shlex.quote(a) for a in args)
    rc, out, err = docker(quoted, timeout=180)
    step("docker-run", rc, out, err)
    record["container_id"] = out.strip()[:64]
    if rc != 0:
        record.update({"launched": False, "reason": "docker run failed", "stderr": err[-4000:]})
        write_json(LOGS / f"{config_id}-launch.json", record)
        return record

    deadline = started + timeout_s
    status = 0
    last_logs = ""
    while time.monotonic() < deadline:
        time.sleep(3)
        status = health(spec["host_port"])
        if status == 200:
            break
        _, lout, _ = docker(f"logs --tail 40 {spec['container']}", timeout=60)
        last_logs = lout
        _, ps, _ = docker(f"inspect -f '{{{{.State.Status}}}}' {spec['container']}", timeout=60)
        if ps.strip() in {"exited", "dead"}:
            break
    record["health_wait_s"] = round(time.monotonic() - started, 1)
    record["health_status"] = status

    _, logs_out, _ = docker(f"logs --tail 200 {spec['container']}", timeout=90)
    record["log_tail"] = logs_out[-12000:]
    record["models"] = capture_models(spec["host_port"]) if status == 200 else None
    record["metrics"] = capture_metrics(spec["host_port"]) if status == 200 else None
    record["occamy"] = occamy_health()
    record["launched"] = status == 200
    record["reason"] = "" if status == 200 else "health never returned 200"
    write_json(LOGS / f"{config_id}-launch.json", record)
    print(f"launch {config_id}: health={status} waited={record['health_wait_s']}s "
          f"launched={record['launched']} occamy={record['occamy']['status']}", flush=True)
    return record


def restore(config_id: str, timeout_s: int = 240) -> dict:
    spec = build_spec(config_id)
    record: dict = {"unit": "WIN-VLLM", "phase": "restore", "config_id": config_id,
                    "started_utc": utc_now()}
    rc, out, err = docker(f"rm -f {spec['container']}", timeout=180)
    record["rm_variant"] = {"rc": rc, "stdout": out[-500:], "stderr": err[-500:]}
    rc, out, err = docker(f"start {PROD_NAME}", timeout=120)
    record["start_production"] = {"rc": rc, "stdout": out[-500:], "stderr": err[-500:]}
    deadline = time.monotonic() + timeout_s
    status = 0
    while time.monotonic() < deadline:
        time.sleep(3)
        status = health(PROD_PORT)
        if status == 200:
            break
    record["health_wait_status"] = status
    record["health"] = status
    record["models"] = capture_models()
    record["metrics"] = capture_metrics()
    record["occamy"] = occamy_health()
    record["config_ok"] = bool(
        status == 200
        and record["models"]["id"] == "qwen3.5-9b"
        and record["models"]["max_model_len"] == 32768
        and "block_size=\"1056\"" in (record["metrics"]["cache_config_info"] or "")
    )
    record["finished_utc"] = utc_now()
    write_json(LOGS / f"{config_id}-restore.json", record)
    print(f"restore {config_id}: health={status} id={record['models']['id']} "
          f"max_model_len={record['models']['max_model_len']} config_ok={record['config_ok']} "
          f"occamy={record['occamy']['status']}", flush=True)
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture-pre", action="store_true")
    ap.add_argument("--launch", choices=sorted(CONFIGS))
    ap.add_argument("--no-spec", action="store_true", help="drop --speculative-config (V3 retry)")
    ap.add_argument("--wait", type=int, default=420, help="health wait budget (s)")
    ap.add_argument("--restore", choices=sorted(CONFIGS))
    ap.add_argument("--health", action="store_true")
    ap.add_argument("--spec", choices=sorted(CONFIGS))
    args = ap.parse_args()
    if args.capture_pre:
        capture_pre()
    if args.spec:
        print(json.dumps(build_spec(args.spec), indent=1))
    if args.launch:
        if args.no_spec:
            CONFIGS[args.launch]["no_spec"] = True
        rec = launch(args.launch, timeout_s=args.wait)
        return 0 if rec.get("launched") else 2
    if args.restore:
        rec = restore(args.restore)
        return 0 if rec.get("config_ok") else 3
    if args.health:
        print(json.dumps({"occamy": occamy_health(), "prod_health": health(PROD_PORT),
                          "models": capture_models()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
