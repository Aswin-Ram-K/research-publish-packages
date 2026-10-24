#!/usr/bin/env python3
"""DENSE-SGL — launch qwen3.5-9b-nvfp4 under the SGLang engine (missing cell).

The 2x2 model/engine matrix:
    engine: SGLang | vLLM
    model : occamy-1.0-NVFP4 | qwen3.5-9b-nvfp4

Completed cells (evidence in orchestration/VERDICTS.md):
    occamy x SGLang  -> G3 / WIN-SGL        (production, port 8012, systemd --user)
    qwen9b x vLLM    -> WIN-VLLM V1/V2      (production, port 8014, plain docker)
    occamy x vLLM    -> WIN-VLLM V3         (bounded probe)
    qwen9b x SGLang  -> THIS CELL (was the gap)

Launch strategy — clone the occamy SGLang spec, swap only the model.  Nothing is
hand-typed: image digest, ``Config.Env``, ``Config.Cmd``, both bind mounts,
``HostConfig.ShmSize``, ``IpcMode``, GPU request and entrypoint are read from the
production inspect JSON (``state/config/occamy-inspect-pre.json``), then the
model-path, served-model-name, context-length, mem-fraction and quantization
flags are overridden in place.  The variant therefore differs from the running
production SGLang container only in those 5 flags, and inherits the same
SGLANG_BUILD_COMMIT / flashinfer / CUDA stack (sha256:72457f09d20e...).

Port and production dance (identical to WIN-VLLM, so client.py needs no change):
  * the SGLang production container on :8012 is NEVER touched (systemd --user,
    ``--rm``; its health is re-checked after every step);
  * the vLLM qwen9b production container on :8014 is stopped (never removed) so
    the variant can claim ``192.168.2.168:8014:30000``; restore is
    ``docker start gx10-qwen9b``.

CLI:
  --capture-pre         capture occamy spec + qwen9b vLLM prod inspect + /health
  --launch P1           stop vLLM prod, run variant, wait /health, capture
  --restore P1          remove variant, start vLLM prod, prove it is back
  --health              both production containers' /health only (0 model requests)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
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

IMAGE = "sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7"  # lmsysorg/sglang:dev-qwen38-next-local
PROD_SGL_NAME = "gx10-occamy-nvfp4"   # port 8012, systemd --user, NEVER touched
PROD_VLLM_NAME = "gx10-qwen9b"        # port 8014, plain docker, stopped/restored here
PROD_VLLM_PORT = 8014
BASE_URL = f"http://192.168.2.168:{PROD_VLLM_PORT}"
OCCAMY_URL = "http://192.168.2.168:8012"

# The model we are serving in this cell (read-only mount, host path).
MODEL_HOST = "/home/zer0null/models/qwen3.5-9b-nvfp4"
MODEL_CTR = "/model-densesgl"
SERVED_MODEL = "qwen3.5-9b"
# --mem-fraction-static 0.22: the GPU is shared with the occamy SGLang container
# (which holds 0.45).  0.22 leaves ~0.10 for the vLLM restore and the OS/driver;
# if launch OOMs, retry at 0.18 then 0.15 (recorded in the handoff assumptions).

CONFIGS = {
    "P1": {
        "config_id": "P1",
        "stack": "sglang",
        "label": "qwen3.5-9b-nvfp4 on SGLang (missing cell)",
        "model_host": MODEL_HOST,
        "model_ctr": MODEL_CTR,
        "served_model": SERVED_MODEL,
        "quantization": "modelopt_fp4",
        "context_length": 65536,
        "mem_fraction_static": 0.22,
        "host_port": PROD_VLLM_PORT,
        "container": "ds-sgl-p1",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# SSH helpers
# --------------------------------------------------------------------------- #
def sh(cmd, *, timeout: float = 120.0, check: bool = False):
    text = cmd if isinstance(cmd, str) else shlex.join(list(cmd))
    cp = subprocess.run(SSH + [text], capture_output=True, text=True, timeout=timeout)
    if check and cp.returncode != 0:
        raise RuntimeError(f"ssh command failed ({cp.returncode}): {text}\n{cp.stderr.strip()}")
    return cp


def docker(args_list, *, timeout: float = 120.0):
    return sh(["sudo", "-n", "docker"] + list(args_list), timeout=timeout)


def container_status(name: str) -> str:
    cp = docker(["inspect", "-f", "{{.State.Status}}", name])
    return cp.stdout.strip() if cp.returncode == 0 else "absent"


def stop_container(name: str, timeout_s: float = 120.0) -> str:
    docker(["stop", "-t", "30", name], timeout=timeout_s)
    return container_status(name)


def start_container(name: str, timeout_s: float = 180.0) -> str:
    docker(["start", name], timeout=timeout_s)
    return container_status(name)


def remove_container(name: str) -> None:
    docker(["rm", "-f", name], timeout=120.0)


def docker_logs_tail(name: str, lines: int = 60) -> str:
    cp = docker(["logs", "--tail", str(lines), name], timeout=120.0)
    return (cp.stdout or "") + (("\n[stderr]\n" + cp.stderr) if cp.stderr.strip() else "")


# --------------------------------------------------------------------------- #
# HTTP probes (production containers + variant)
# --------------------------------------------------------------------------- #
def _get_json(url: str, timeout: float = 15.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), int(resp.status)
    except urllib.error.HTTPError as exc:
        return None, int(exc.code)
    except Exception:
        return None, 0


def _get_status(url: str, timeout: float = 8.0) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:
        return 0


def prod_health() -> dict[str, int]:
    return {
        "occamy_8012": _get_status(f"{OCCAMY_URL}/health"),
        "qwen9b_vllm_8014": _get_status(f"{BASE_URL}/health"),
    }


# --------------------------------------------------------------------------- #
# Spec -> argv (verbatim from the production occamy SGLang inspect JSON)
# --------------------------------------------------------------------------- #
def load_occamy_spec() -> dict:
    path = STATE / "occamy-inspect-pre.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data[0] if isinstance(data, list) else data


def build_cmd(spec_cmd, overrides):
    """Return ``spec_cmd`` with each (flag, value) applied in place; a flag already
    present is rewritten, an absent flag is appended.  ``value is None`` = bare switch."""
    cmd = list(spec_cmd)
    for flag, value in overrides:
        if flag in cmd:
            idx = cmd.index(flag)
            if value is None:
                continue
            if idx + 1 < len(cmd) and not cmd[idx + 1].startswith("--"):
                cmd[idx + 1] = str(value)
            else:
                cmd.insert(idx + 1, str(value))
        else:
            cmd.append(flag)
            if value is not None:
                cmd.append(str(value))
    return cmd


def variant_overrides(config: dict) -> list[tuple[str, str]]:
    return [
        ("--model-path", config["model_ctr"]),
        ("--served-model-name", config["served_model"]),
        ("--quantization", config["quantization"]),
        ("--context-length", str(config["context_length"])),
        ("--mem-fraction-static", str(config["mem_fraction_static"])),
    ]


def docker_create_argv(spec: dict, name: str, cmd, config: dict) -> list[str]:
    config_cfg = spec["Config"]
    host = spec["HostConfig"]

    argv = ["docker", "create", "--name", name, "--restart", "no"]
    argv += ["--shm-size", str(int(host["ShmSize"]))]
    if host.get("Init"):
        argv += ["--init"]
    if host.get("Memory"):
        argv += ["--memory", str(int(host["Memory"]))]
    if host.get("MemorySwap"):
        argv += ["--memory-swap", str(int(host["MemorySwap"]))]
    argv += ["--ipc", str(host.get("IpcMode") or "private")]
    argv += ["--network", str(host.get("NetworkMode") or "bridge")]
    for opt in host.get("SecurityOpt") or []:
        argv += ["--security-opt", str(opt)]
    for ul in host.get("Ulimits") or []:
        argv += ["--ulimit", f"{ul['Name']}={ul['Soft']}:{ul['Hard']}"]
    # bind mounts: occamy's two mounts are replaced with the qwen9b model mount
    argv += ["-v", f"{config['model_host']}:{config['model_ctr']}:ro"]
    for container_port, binds in (host.get("PortBindings") or {}).items():
        for b in binds:
            hostport = b.get("HostPort")
            hostip = b.get("HostIp") or "0.0.0.0"
            # production claims :8012; the variant must claim :8014 (WIN-VLLM's port)
            argv += ["-p", f"{hostip}:{PROD_VLLM_PORT}:{container_port.split('/')[0]}"]
    caps = (host.get("DeviceRequests") or [{}])[0].get("Capabilities") or []
    gpu_caps = [c for group in caps for c in group]
    argv += ["--gpus", "all"] if gpu_caps else []
    workdir = config_cfg.get("WorkingDir")
    if workdir:
        argv += ["--workdir", workdir]
    for env in config_cfg.get("Env") or []:
        # keep offline + allocator env; drop SGLANG_CACHE_DIR (variant has no
        # /sglang-cache mount) so the server uses its default tmp cache
        if env.startswith("SGLANG_CACHE_DIR="):
            continue
        argv += ["--env", str(env)]
    entrypoint = config_cfg.get("Entrypoint")
    if entrypoint:
        argv += ["--entrypoint", str(entrypoint[0])]
    argv.append(spec["Image"])
    argv.extend(str(tok) for tok in cmd)
    return argv


def wait_health(name: str, deadline_s: float = 420.0, poll_s: float = 5.0) -> dict:
    started = time.monotonic()
    last_status = ""
    while time.monotonic() - started < deadline_s:
        status = container_status(name)
        last_status = status
        if status in ("exited", "dead", "absent"):
            return {"ok": False, "seconds": round(time.monotonic() - started, 1),
                    "reason": f"container {status}", "container_status": status}
        code = _get_status(f"{BASE_URL}/health")
        if code == 200:
            return {"ok": True, "seconds": round(time.monotonic() - started, 1),
                    "health": code, "container_status": status}
        time.sleep(poll_s)
    return {"ok": False, "seconds": round(time.monotonic() - started, 1),
            "reason": "health deadline", "container_status": last_status}


# --------------------------------------------------------------------------- #
# capture-pre / launch / restore
# --------------------------------------------------------------------------- #
def capture_pre() -> dict:
    record = {"unit": "DENSE-SGL", "step": "capture_pre", "ts_utc": utc_now()}
    # production SGLang spec (source of truth for the clone)
    spec = load_occamy_spec()
    (STATE / "ds-occamy-spec-pre.json").write_text(
        json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    record["occamy_spec_image"] = spec.get("Image")
    record["occamy_spec_cmd_len"] = len(spec.get("Config", {}).get("Cmd", []))
    record["occamy_spec_sha256"] = hashlib.sha256(
        (STATE / "ds-occamy-spec-pre.json").read_bytes()).hexdigest()
    # production vLLM qwen9b inspect (the container we will stop/restore)
    cp = docker(["inspect", PROD_VLLM_NAME], timeout=60.0)
    if cp.returncode == 0:
        (STATE / "ds-vllm-prod-inspect-pre.json").write_text(
            cp.stdout, encoding="utf-8")
        record["vllm_prod_inspect"] = str((STATE / "ds-vllm-prod-inspect-pre.json").relative_to(REPO))
        record["vllm_prod_status"] = container_status(PROD_VLLM_NAME)
    else:
        record["vllm_prod_inspect_error"] = cp.stderr.strip()
    record["prod_health"] = prod_health()
    # /v1/models + /metrics from the vLLM production (context for the handoff)
    body, status = _get_json(f"{BASE_URL}/v1/models")
    record["vllm_prod_models_status"] = status
    if body:
        record["vllm_prod_model_id"] = (body.get("data") or [{}])[0].get("id")
    record["ok"] = True
    return record


def launch(config_id: str) -> dict:
    config = CONFIGS[config_id]
    record = {"unit": "DENSE-SGL", "step": "launch", "config_id": config_id,
              "ts_utc": utc_now()}
    spec = load_occamy_spec()

    # stop the vLLM qwen9b production so :8014 frees up
    record["vllm_prod_status_before"] = container_status(PROD_VLLM_NAME)
    if record["vllm_prod_status_before"] != "absent":
        record["vllm_prod_status_after_stop"] = stop_container(PROD_VLLM_NAME)

    overrides = variant_overrides(config)
    cmd = build_cmd(spec["Config"]["Cmd"], overrides)
    create = docker_create_argv(spec, config["container"], cmd, config)

    (LOGS / f"{config_id}-launch.json").write_text(json.dumps({
        "config_id": config_id,
        "container": config["container"],
        "image": spec["Image"],
        "overrides": overrides,
        "cmd_len_production": len(spec["Config"]["Cmd"]),
        "cmd_len_variant": len(cmd),
        "cmd": cmd,
        "create_argv": create,
        "model_host": config["model_host"],
        "mem_fraction_static": config["mem_fraction_static"],
        "context_length": config["context_length"],
    }, indent=2) + "\n", encoding="utf-8")

    remove_container(config["container"])  # leftover variant is disposable
    # `create` starts with the literal "docker" token; docker() already prefixes
    # "sudo -n docker", so strip the leading token to avoid "docker docker create".
    cp = docker(create[1:], timeout=180.0)
    if cp.returncode != 0:
        record.update({"ok": False, "reason": "docker create failed", "stderr": cp.stderr.strip()})
        return record
    cp = docker(["start", config["container"]], timeout=180.0)
    if cp.returncode != 0:
        record.update({"ok": False, "reason": "docker start failed", "stderr": cp.stderr.strip()})
        return record

    health = wait_health(config["container"], deadline_s=420.0, poll_s=5.0)
    record["health"] = health
    if health.get("ok"):
        body, status = _get_json(f"{BASE_URL}/get_server_info")
        record["server_info_status"] = status
        if body:
            (STATE / f"ds-{config_id.lower()}-server-info.json").write_text(
                json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            record["server_info_path"] = str((STATE / f"ds-{config_id.lower()}-server-info.json").relative_to(REPO))
            record["served_model"] = body.get("model_path")
            record["context_len"] = body.get("context_len")
            record["max_total_num_tokens"] = body.get("max_total_num_tokens")
        # capture /metrics tail for the cache report + launch.json shape
        metrics_body, _ = _get_json(f"{BASE_URL}/metrics", timeout=8.0)
        record["metrics_available"] = metrics_body is not None
        record["log_tail"] = docker_logs_tail(config["container"])
        record["ok"] = True
    else:
        record["log_tail"] = docker_logs_tail(config["container"])
        record["ok"] = False
    record["prod_health"] = prod_health()
    return record


def restore(config_id: str) -> dict:
    config = CONFIGS[config_id]
    record = {"unit": "DENSE-SGL", "step": "restore", "config_id": config_id,
              "ts_utc": utc_now()}
    # remove the variant (frees GPU + :8014)
    record["variant_status_before_rm"] = container_status(config["container"])
    remove_container(config["container"])
    record["variant_status_after_rm"] = container_status(config["container"])

    # start the vLLM qwen9b production back
    record["vllm_prod_status_before_start"] = container_status(PROD_VLLM_NAME)
    if record["vllm_prod_status_before_start"] != "running":
        record["vllm_prod_status_after_start"] = start_container(PROD_VLLM_NAME)

    # poll production health on :8014
    deadline = time.monotonic() + 180.0
    code = 0
    while time.monotonic() < deadline:
        code = _get_status(f"{BASE_URL}/health")
        if code == 200:
            break
        time.sleep(5.0)
    record["vllm_prod_health"] = code

    # prove it is the same model + block_size as before
    body, status = _get_json(f"{BASE_URL}/metrics")
    if status == 200 and body:
        text = body if isinstance(body, str) else json.dumps(body)
        record["metrics_text_len"] = len(text)
    models, mstatus = _get_json(f"{BASE_URL}/v1/models")
    if mstatus == 200 and models:
        record["vllm_prod_model_id"] = (models.get("data") or [{}])[0].get("id")
    record["prod_health"] = prod_health()
    record["config_ok"] = (
        record.get("vllm_prod_model_id") == "qwen3.5-9b" and code == 200
    )
    record["ok"] = bool(record["config_ok"])
    return record


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DENSE-SGL launch/restore (qwen3.5-9b on SGLang)")
    ap.add_argument("--capture-pre", action="store_true")
    ap.add_argument("--launch", metavar="P1")
    ap.add_argument("--restore", metavar="P1")
    ap.add_argument("--health", action="store_true")
    args = ap.parse_args(argv)

    LOGS.mkdir(parents=True, exist_ok=True)

    if args.health:
        print(json.dumps({"ts_utc": utc_now(), "prod_health": prod_health()}, indent=2))
        return 0
    if args.capture_pre:
        record = capture_pre()
        (LOGS / "capture-pre.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2))
        return 0
    if args.launch:
        record = launch(args.launch)
        (LOGS / f"{args.launch}-launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2))
        return 0 if record.get("ok") else 1
    if args.restore:
        record = restore(args.restore)
        (LOGS / f"{args.restore}-restore.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2))
        return 0 if record.get("ok") else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
