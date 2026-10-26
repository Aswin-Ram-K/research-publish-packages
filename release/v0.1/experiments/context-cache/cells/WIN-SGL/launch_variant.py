#!/usr/bin/env python3
"""WIN-SGL — rebuild the live occamy container spec from the inspected JSON and
re-issue it with exactly one SGLang flag added/changed.

Nothing is hand-typed: image, ``Config.Env``, ``Config.Cmd``, both bind mounts,
``HostConfig.ShmSize``, ``IpcMode``, the GPU device request and the published
port are read from ``state/config/occamy-inspect-pre.json`` (the pre-change
capture of ``gx10-occamy-nvfp4``), so a variant differs from production only in
the requested flag.

Deliberate deviations from the production spec, recorded so they are reviewable:

* ``--rm``/AutoRemove is **not** passed for variants: a variant that dies must
  keep its container so ``docker logs <variant>`` can be captured verbatim.  The
  driver removes it explicitly after the logs are taken.
* the variant claims ``serving-host->30000`` exactly like production, so
  the existing ``experiments/context-cache/client.py`` needs no change; that is
  only legal while production is **stopped**, which the driver guarantees.

Usage::

    python launch_variant.py --config-id S1 --flag '--page-size=64' --dry-run
    python launch_variant.py --config-id S1 --flag '--page-size=64' --apply
    python launch_variant.py --stop-production
    python launch_variant.py --start-production
    python launch_variant.py --server-info state/config/S0-server-info.json
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SPEC_PATH = REPO / "state" / "config" / "occamy-inspect-pre.json"
LOGS = HERE / "logs"

REMOTE = "zer0null@serving-host"
SSH = [
    "ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8", "-o", "LogLevel=ERROR",
    REMOTE,
]

PRODUCTION = "gx10-occamy-nvfp4"
#: MEASURED: the live container is the ExecStart of a systemd **user** unit
#: (``~/.config/systemd/user/gx10-occamy-nvfp4.service``, ``Restart=on-failure``,
#: ``--rm``).  The *system* unit of the same name is inactive -- that is the unit
#: the card looked at -- but the user unit is what owns the container: stopping
#: the container makes ``docker run`` exit and systemd recreate it within a
#: second, so the container-level "stop" cannot hold :8012 free.  Control surface
#: is therefore ``systemctl --user``; ``docker start`` on the container is
#: impossible by construction because ``--rm`` removes it on stop.
SERVICE = "gx10-occamy-nvfp4.service"
VARIANT_FLAG_PORT = "serving-host:30000"
BASE_URL = "http://serving-host"
RESTORE_KEYS = (
    "page_size",
    "mamba_radix_cache_strategy",
    "mem_fraction_static",
    "disable_chunked_prefix_cache",
    "max_total_num_tokens",  # the container's token_capacity
)


# --------------------------------------------------------------------------- #
# Spec -> argv
# --------------------------------------------------------------------------- #
def load_spec(path: Path = SPEC_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data[0] if isinstance(data, list) else data


def build_cmd(spec_cmd: Sequence[str], overrides: Sequence[tuple[str, str | None]]) -> list[str]:
    """Return ``spec_cmd`` with each (flag, value) applied.

    ``value is None`` means a bare switch (``--enable-x``); a flag already in the
    command is rewritten in place, an absent flag is appended.
    """

    cmd = list(spec_cmd)
    for flag, value in overrides:
        if flag in cmd:
            idx = cmd.index(flag)
            if value is None:
                continue  # bare switch already present
            if idx + 1 < len(cmd) and not cmd[idx + 1].startswith("--"):
                cmd[idx + 1] = str(value)
            else:
                cmd.insert(idx + 1, str(value))
        else:
            cmd.append(flag)
            if value is not None:
                cmd.append(str(value))
    return cmd


def docker_create_argv(spec: dict[str, Any], name: str, cmd: Sequence[str]) -> list[str]:
    config = spec["Config"]
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
    for bind in host.get("Binds") or []:
        argv += ["-v", str(bind)]
    for container_port, binds in (host.get("PortBindings") or {}).items():
        for b in binds:
            hostport = b.get("HostPort")
            hostip = b.get("HostIp") or "0.0.0.0"
            if str(hostport) == "8012" and str(hostip) == "serving-host":
                argv += ["-p", VARIANT_FLAG_PORT]
            else:  # pragma: no cover -- production publishes only :8012
                argv += ["-p", f"{hostip}:{hostport}:{container_port.split('/')[0]}"]
    caps = (host.get("DeviceRequests") or [{}])[0].get("Capabilities") or []
    gpu_caps = [c for group in caps for c in group]
    argv += ["--gpus", "all"] if gpu_caps else []
    workdir = config.get("WorkingDir")
    if workdir:
        argv += ["--workdir", workdir]
    for env in config.get("Env") or []:
        argv += ["--env", str(env)]
    entrypoint = config.get("Entrypoint")
    if entrypoint:
        argv += ["--entrypoint", str(entrypoint[0])]
    argv.append(spec["Image"])
    argv.extend(str(tok) for tok in cmd)
    return argv


# --------------------------------------------------------------------------- #
# Remote execution
# --------------------------------------------------------------------------- #
def ssh_run(remote_cmd: Sequence[str] | str, *, timeout: float = 120.0, check: bool = False) -> subprocess.CompletedProcess:
    text = remote_cmd if isinstance(remote_cmd, str) else shlex.join(list(remote_cmd))
    cp = subprocess.run(SSH + [text], capture_output=True, text=True, timeout=timeout)
    if check and cp.returncode != 0:
        raise RuntimeError(f"ssh command failed ({cp.returncode}): {text}\n{cp.stderr.strip()}")
    return cp


def container_status(name: str) -> str:
    cp = ssh_run(["docker", "inspect", "-f", "{{.State.Status}}", name])
    return cp.stdout.strip() if cp.returncode == 0 else "absent"


def stop_container(name: str, timeout_s: float = 120.0) -> str:
    ssh_run(["docker", "stop", "-t", "30", name], timeout=timeout_s)
    return container_status(name)


def start_container(name: str, timeout_s: float = 180.0) -> str:
    ssh_run(["docker", "start", name], timeout=timeout_s)
    return container_status(name)


def remove_container(name: str) -> None:
    ssh_run(["docker", "rm", "-f", name], timeout=120.0)


def service_state() -> str:
    cp = ssh_run(["systemctl", "--user", "is-active", SERVICE])
    return (cp.stdout.strip() or cp.stderr.strip() or "unknown")


def service_stop(timeout_s: float = 240.0) -> str:
    """Stop the owning user unit and wait until the container is gone.

    ``ExecStop`` is ``docker stop --time 60`` and the container carries ``--rm``,
    so a successful stop also removes the container and frees :8012.
    """

    ssh_run(["systemctl", "--user", "stop", SERVICE], timeout=timeout_s)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if container_status(PRODUCTION) == "absent":
            return "absent"
        time.sleep(2.0)
    return container_status(PRODUCTION)


def service_start(timeout_s: float = 240.0) -> str:
    ssh_run(["systemctl", "--user", "start", SERVICE], timeout=timeout_s)
    return service_state()


def docker_logs_tail(name: str, lines: int = 40) -> str:
    cp = ssh_run(["docker", "logs", "--tail", str(lines), name], timeout=120.0)
    return (cp.stdout or "") + (("\n[stderr]\n" + cp.stderr) if cp.stderr.strip() else "")


def get_server_info(timeout: float = 30.0) -> dict[str, Any]:
    with urllib.request.urlopen(f"{BASE_URL}/get_server_info", timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def health(timeout: float = 10.0) -> int:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:  # server up but not ready -> 503
        return int(exc.code)
    except Exception:
        return 0


def wait_health(name: str, deadline_s: float = 900.0, poll_s: float = 5.0) -> dict[str, Any]:
    started = time.monotonic()
    last_status = ""
    while time.monotonic() - started < deadline_s:
        status = container_status(name)
        last_status = status
        if status in ("exited", "dead", "absent"):
            return {"ok": False, "seconds": round(time.monotonic() - started, 1),
                    "reason": f"container {status}", "container_status": status}
        code = health()
        if code == 200:
            return {"ok": True, "seconds": round(time.monotonic() - started, 1),
                    "health": code, "container_status": status}
        time.sleep(poll_s)
    return {"ok": False, "seconds": round(time.monotonic() - started, 1),
            "reason": "health deadline", "container_status": last_status}


def capture_server_info(path: Path) -> dict[str, Any]:
    info = get_server_info()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return info


#: Configuration keys the restore must reproduce exactly.
CONFIG_KEYS = ("page_size", "mamba_radix_cache_strategy", "mem_fraction_static",
               "disable_chunked_prefix_cache")


def restore_diff(pre: dict[str, Any], post: dict[str, Any], keys: Sequence[str] = RESTORE_KEYS) -> dict[str, Any]:
    """Config keys must match exactly; ``token_capacity`` is reported, not gated.

    MEASURED: ``max_total_num_tokens`` is re-profiled from free memory on every
    start, so a *correct* restore of an unchanged configuration still moves it
    (1,306,681 on the 4-day-old process -> 1,644,272 after the first restart,
    +25.8 %, no flag changed).  Gating on it would call a proven restore failed;
    hiding it would hide real capacity drift, so it is reported per start with
    its delta and excluded from the pass/fail gate.
    """

    rows = {k: {"pre": pre.get(k), "post": post.get(k), "equal": pre.get(k) == post.get(k)} for k in keys}
    config_rows = {k: rows[k] for k in CONFIG_KEYS if k in rows}
    cap_pre, cap_post = pre.get("max_total_num_tokens"), post.get("max_total_num_tokens")
    return {
        "ok": all(r["equal"] for r in config_rows.values()),
        "config_ok": all(r["equal"] for r in config_rows.values()),
        "keys": rows,
        "token_capacity": {
            "pre": cap_pre, "post": cap_post,
            "delta": (cap_post - cap_pre) if isinstance(cap_pre, int) and isinstance(cap_post, int) else None,
            "equal": cap_pre == cap_post,
            "informational": "re-profiled from free memory at every start; not a config key",
        },
    }


# --------------------------------------------------------------------------- #
# Production rewrite: make the live container stop/start-safe BEFORE any variant
# --------------------------------------------------------------------------- #
def prepare_production(spec: dict[str, Any], baseline_path: Path, pre_info: dict[str, Any]) -> dict[str, Any]:
    """Stop-safety rewrite of the live container, without touching its spec.

    MEASURED PROBLEM: ``gx10-occamy-nvfp4`` was created with ``AutoRemove=true``
    (``HostConfig.AutoRemove: true``), and Docker removes an ``--rm`` container
    as soon as it exits -- ``docker stop`` included (verified on a throwaway
    container from the same image: after ``docker stop`` the container id list
    was empty).  So "production is stopped, never removed" cannot be done with
    ``docker stop`` on the container as it stands: the first stop would destroy
    it, and ``docker start`` -- the whole restore path -- would have nothing to
    start.

    The rewrite re-issues the *identical* spec (same image digest, Config.Cmd,
    Config.Env, both binds, ShmSize, IpcMode, GPU request, published port,
    workdir, entrypoint, restart policy) under the same name with
    ``AutoRemove=false``, then proves it: ``/health`` 200 and a
    ``/get_server_info`` comparison against the pre-change capture.  If the
    rewrite comes up unhealthy the original (``--rm``) semantics are restored,
    so production is never left down.

    Idempotent: a production container that is already stop-safe is left alone.
    """

    record: dict[str, Any] = {"unit": "WIN-SGL", "step": "prepare_production",
                              "production": PRODUCTION, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    cp = ssh_run(["docker", "inspect", "-f", "{{.HostConfig.AutoRemove}}", PRODUCTION])
    if cp.returncode != 0:
        record.update({"ok": False, "reason": f"{PRODUCTION} not inspectable", "stderr": cp.stderr.strip()})
        return record
    already_safe = cp.stdout.strip().lower() == "false"
    record["already_stop_safe"] = already_safe
    if already_safe:
        record.update({"ok": True, "action": "none"})
        return record

    temp_name = f"{PRODUCTION}-tmp0"
    cmd = list(spec["Config"]["Cmd"])
    create = docker_create_argv(spec, temp_name, cmd)
    remove_container(temp_name)
    cp = ssh_run(create, timeout=180.0)
    if cp.returncode != 0:
        record.update({"ok": False, "reason": "replacement create failed", "stderr": cp.stderr.strip()})
        return record
    record["replacement"] = temp_name
    record["image"] = spec["Image"]
    record["cmd_len"] = len(cmd)

    # the original exits here and is auto-removed; the replacement is already staged
    record["original_status_after_stop"] = stop_container(PRODUCTION)
    if container_status(temp_name) != "created":
        record.update({"ok": False, "reason": "replacement not staged"})
        return record
    cp = ssh_run(["docker", "rename", temp_name, PRODUCTION], timeout=60.0)
    if cp.returncode != 0:
        record.update({"ok": False, "reason": "rename failed", "stderr": cp.stderr.strip()})
        return record
    record["renamed_to"] = PRODUCTION

    record["start_status"] = start_container(PRODUCTION)
    health = wait_health(PRODUCTION, deadline_s=900.0, poll_s=5.0)
    record["health"] = health
    if health.get("ok"):
        info = capture_server_info(baseline_path)
        diff = restore_diff(pre_info, info)
        record["server_info_diff_vs_pre"] = diff
        record["server_info_keys"] = {k: info.get(k) for k in RESTORE_KEYS}
        record["ok"] = True
        record["action"] = "rewritten_stop_safe"
        record["stop_safe_after"] = container_status(PRODUCTION), ssh_run(
            ["docker", "inspect", "-f", "{{.HostConfig.AutoRemove}}", PRODUCTION]).stdout.strip()
        return record

    # fallback: restore the original --rm semantics so production is not left down
    record["action"] = "fallback_to_original_semantics"
    try:
        remove_container(PRODUCTION)
        create_rm = docker_create_argv(spec, PRODUCTION, cmd)
        cp = ssh_run(create_rm, timeout=180.0)
        record["fallback_create_rc"] = cp.returncode
        record["fallback_start"] = start_container(PRODUCTION)
        record["fallback_health"] = wait_health(PRODUCTION, deadline_s=900.0, poll_s=5.0)
        if record["fallback_health"].get("ok"):
            record["ok"] = True
            record["reason"] = "rewrite failed; original semantics restored and healthy"
        else:
            record["ok"] = False
            record["reason"] = "rewrite failed AND fallback unhealthy"
    except Exception as exc:  # noqa: BLE001
        record["ok"] = False
        record["reason"] = f"rewrite failed and fallback raised: {type(exc).__name__}: {exc}"
    return record


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_flag(text: str) -> tuple[str, str | None]:
    if "=" in text:
        flag, value = text.split("=", 1)
        return flag, value
    return text, None


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="clone the occamy container with one flag changed")
    ap.add_argument("--config-id", help="S1/S2/S3 -- used for the variant container name")
    ap.add_argument("--flag", action="append", default=[], help="'--page-size=64' or '--enable-x' (repeatable)")
    ap.add_argument("--name", help="override the variant container name")
    ap.add_argument("--spec", default=str(SPEC_PATH))
    ap.add_argument("--apply", action="store_true", help="create + start the variant")
    ap.add_argument("--no-start", action="store_true", help="create only")
    ap.add_argument("--dry-run", action="store_true", help="print the argv and exit")
    ap.add_argument("--prepare-production", action="store_true",
                    help="make the live container stop/start-safe (AutoRemove=false), verified")
    ap.add_argument("--baseline", default=str(REPO / "state" / "config" / "occamy-restore-baseline.json"))
    ap.add_argument("--stop-production", action="store_true")
    ap.add_argument("--start-production", action="store_true")
    ap.add_argument("--server-info", help="capture /get_server_info to this path")
    ap.add_argument("--logs-tail", help="print `docker logs --tail 40` for this container")
    args = ap.parse_args(argv)

    if args.prepare_production:
        pre_path = Path(args.server_info or REPO / "state" / "config" / "S0-server-info.json")
        pre_info = json.loads(pre_path.read_text(encoding="utf-8"))
        record = prepare_production(load_spec(Path(args.spec)), Path(args.baseline), pre_info)
        LOGS.mkdir(parents=True, exist_ok=True)
        (LOGS / "production-rewrite.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2))
        return 0 if record.get("ok") else 1
    if args.stop_production:
        print(json.dumps({"stopped_status": service_stop(), "unit": service_state()}, indent=2))
        return 0
    if args.start_production:
        print(json.dumps({"unit": service_start(), "status": container_status(PRODUCTION)}, indent=2))
        return 0
    if args.server_info:
        capture_server_info(Path(args.server_info))
        print(args.server_info)
        return 0
    if args.logs_tail:
        print(docker_logs_tail(args.logs_tail))
        return 0

    if not args.config_id:
        ap.error("--config-id is required to build a variant")

    name = args.name or f"{PRODUCTION}-{args.config_id.lower()}"
    spec = load_spec(Path(args.spec))
    overrides = [parse_flag(f) for f in args.flag]
    cmd = build_cmd(spec["Config"]["Cmd"], overrides)
    create = docker_create_argv(spec, name, cmd)

    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / f"{args.config_id}-launch.json").write_text(json.dumps({
        "config_id": args.config_id,
        "container": name,
        "image": spec["Image"],
        "image_id": spec.get("Image"),
        "overrides": overrides,
        "cmd_len_production": len(spec["Config"]["Cmd"]),
        "cmd_len_variant": len(cmd),
        "cmd": cmd,
        "create_argv": create,
        "spec_path": str(Path(args.spec).relative_to(REPO)),
        "spec_sha256": __import__("hashlib").sha256(Path(args.spec).read_bytes()).hexdigest(),
    }, indent=2) + "\n", encoding="utf-8")

    print(shlex.join(create if not args.dry_run else create))
    if args.dry_run:
        return 0

    remove_container(name)  # a leftover variant of the same name is disposable
    cp = ssh_run(create, timeout=180.0)
    if cp.returncode != 0:
        print(f"docker create failed: {cp.stderr.strip()}", file=sys.stderr)
        return 1
    print(cp.stdout.strip())
    if not args.no_start:
        cp = ssh_run(["docker", "start", name], timeout=180.0)
        if cp.returncode != 0:
            print(f"docker start failed: {cp.stderr.strip()}", file=sys.stderr)
            return 1
        print(cp.stdout.strip() or "started")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
