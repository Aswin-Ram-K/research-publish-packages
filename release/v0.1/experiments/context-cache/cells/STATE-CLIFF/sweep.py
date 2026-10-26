#!/usr/bin/env python3
"""STATE-CLIFF sweep — one rung of the `max_mamba_cache_size` ladder.

Dry-run by default: prints the exact command sequence for one rung and exits
0 **without touching the box**. Nothing executes unless `--execute` is passed;
the operator has approved preparation only, so this unit never passes it.

Usage (the card's proof command):

    python3 experiments/context-cache/cells/STATE-CLIFF/sweep.py \
        --dry-run --mamba-cache-size 48 --port 8021

Exit codes: 0 = printed/ran the sequence; 2 = refused (pre-flight failed);
3 = execute-mode failure (restore attempted, proof recorded).
Design doc: experiments/context-cache/cells/STATE-CLIFF/plan.md
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

ROOT = Path(__file__).resolve().parents[4]          # .../reserach extarctor
CELL = ROOT / "experiments/context-cache/cells/STATE-CLIFF"
BASELINE = ROOT / "state/config/occamy-restore-baseline.json"
LOCK = ROOT / "experiments/context-cache/.occamy.lock"
BATTERY = ROOT / "experiments/context-cache/cells/M4/battery.py"

PRODUCTION = "gx10-occamy-nvfp4"
VARIANT_PREFIX = "gx10-occamy-sweep"
IMAGE = "sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7"
PROD_PORT = 8012
CONTAINER_PORT = 30000
HEALTH_DEADLINE_S = 900
HEALTH_POLL_S = 5
LOCK_WAIT_S = 300
LADDER = (64, 48, 32, 16)

#: The six restore keys of record (plan.md §5). token_capacity is NOT among
#: them: the pool is re-profiled on every start (informational).
RESTORE_KEYS = {
    "page_size": 1,
    "mamba_radix_cache_strategy": "extra_buffer",
    "radix_eviction_policy": "lru",
    "mem_fraction_static": 0.45,
    "kv_cache_dtype": "fp8_e4m3",
    "max_mamba_cache_size": 64,
}

#: Assumption A2 (plan.md §8): battery.py's CLI was not read offline, so the
#: execute path gates on `battery.py --help` exposing a base-URL flag before
#: running it; if the battery hard-codes :8012, edit this one line first.
M4_MEASURE_ARGV = ["python3", str(BATTERY), "--base-url", "http://127.0.0.1:{port}"]


# --------------------------------------------------------------------------- #
# offline pre-flight
# --------------------------------------------------------------------------- #
def preflight(size: int, port: int) -> list[str]:
    """Local-only checks. No network, no docker. Returns a problem list."""
    problems: list[str] = []
    if size not in LADDER:
        problems.append(f"--mamba-cache-size {size} not in ladder {LADDER}")
    if port == PROD_PORT:
        problems.append(f"--port must differ from production port {PROD_PORT}")
    if not (1024 <= port <= 65535):
        problems.append(f"--port {port} out of range 1024-65535")
    try:
        base = json.loads(BASELINE.read_text())
    except FileNotFoundError:
        problems.append(f"baseline missing: {BASELINE}")
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"baseline unreadable: {exc}")
    else:
        for key, want in RESTORE_KEYS.items():
            if key not in base:
                problems.append(f"baseline missing key {key}")
            elif base[key] != want:
                problems.append(f"baseline {key}={base[key]!r} != expected {want!r}")
    return problems


def rung_dir(size: int) -> Path:
    return CELL / f"rung-{size}"


# --------------------------------------------------------------------------- #
# the command sequence (printed verbatim in dry-run)
# --------------------------------------------------------------------------- #
def build_steps(size: int, port: int) -> list[str]:
    variant = f"{VARIANT_PREFIX}-{size}"
    rung = rung_dir(size)
    measure_argv = " ".join(
        shlex.quote(a) for a in
        [a.format(port=port) if "{port}" in a else a for a in M4_MEASURE_ARGV]
    )
    return [
        # 0 - offline, done in-process before anything below is printed
        f"[0] pre-flight (offline): six-key baseline check vs {BASELINE}",
        # 0b - execute mode only: proves the live container is stop-safe and
        # sources the variant's binds/shm (AutoRemove must be false!)
        f"docker inspect {PRODUCTION} --format "
        "'{{.HostConfig.AutoRemove}} {{.HostConfig.RestartPolicy.Name}} "
        "{{.HostConfig.Binds}} {{.HostConfig.ShmSize}}'",
        # 1 - production is stopped, never removed
        f"docker stop -t 60 {PRODUCTION}",
        # 2 - variant rung: identical spec apart from the knob and host port;
        # every bind absolute and :ro, HF_HUB_OFFLINE=1 (plan.md §7)
        f"docker run -d --name {variant} --restart no --gpus all "
        f"--shm-size <SHM_FROM_[0b]> -p {port}:{CONTAINER_PORT} "
        f"-e HF_HUB_OFFLINE=1 <ABSOLUTE_RO_BINDS_FROM_[0b]> {IMAGE} "
        f"--max-mamba-cache-size={size}",
        # 3
        f"[3] health gate: poll http://127.0.0.1:{port}/health every "
        f"{HEALTH_POLL_S}s until HTTP 200 or {HEALTH_DEADLINE_S}s "
        "(abort -> [6] restore)",
        # 4 - per-config capture + readback gate (assumption A1)
        f"curl -sf http://127.0.0.1:{port}/get_server_info "
        f"-o {rung}/server_info.json && "
        f"readback: max_mamba_cache_size == {size} and page_size == 1",
        # 5 - M4 protocol reused (plan.md §6)
        f"[5] wait <= {LOCK_WAIT_S}s for {LOCK} to be free, then "
        f"`python3 {BATTERY} --help` argv gate (A2)",
        f"{measure_argv}   # 1.50x measured capacity + oldest/middle/newest replay",
        # 6 - variant removed; production was only stopped
        f"docker stop -t 60 {variant} && docker rm {variant}",
        # 7
        f"docker start {PRODUCTION}",
        # 8
        f"[8] health gate: poll http://127.0.0.1:{PROD_PORT}/health every "
        f"{HEALTH_POLL_S}s until HTTP 200 or {HEALTH_DEADLINE_S}s",
        # 9 - restore proof (plan.md §5)
        f"curl -sf http://127.0.0.1:{PROD_PORT}/get_server_info "
        f"-o {rung}/restore_server_info.json && "
        f"six-key restore proof vs {BASELINE}",
    ]


def dry_run(size: int, port: int) -> int:
    print(f"STATE-CLIFF sweep rung max_mamba_cache_size={size} port={port}")
    print(f"root={ROOT}")
    print("DRY RUN — no docker, no ssh, no HTTP request will be issued.")
    for i, step in enumerate(build_steps(size, port)):
        print(f"{i:>3}| {step}")
    print(f"end| restore proof keys: {', '.join(RESTORE_KEYS)}")
    print("DRY RUN complete — nothing executed.")
    return 0


# --------------------------------------------------------------------------- #
# execute mode (never used by the preparation card)
# --------------------------------------------------------------------------- #
def sh(argv: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(shlex.quote(a) for a in argv), flush=True)
    return subprocess.run(argv, check=check, text=True,
                          capture_output=True)


def health(url: str, deadline_s: int = HEALTH_DEADLINE_S) -> None:
    end = time.time() + deadline_s
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    print(f"health OK {url}")
                    return
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(HEALTH_POLL_S)
    raise RuntimeError(f"health gate failed after {deadline_s}s: {url}")


def capture(url: str, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as resp:
        doc = json.loads(resp.read())
    out.write_text(json.dumps(doc, indent=2, sort_keys=True))
    return doc


def restore_proof(doc: dict) -> list[str]:
    """plan.md §5 — exactly the six keys; token_capacity deliberately absent."""
    return [f"{k}: got {doc.get(k, '<absent>')!r}, want {v!r}"
            for k, v in RESTORE_KEYS.items() if doc.get(k) != v]


def wait_lock_free() -> None:
    """Wait until .occamy.lock is free, then RELEASE it.

    The M4 battery holds the lock for the whole measurement batch; the sweep
    must not hold it while the battery runs or the two flocks deadlock.
    """
    import fcntl
    end = time.time() + LOCK_WAIT_S
    while time.time() < end:
        with open(LOCK, "a") as fh:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fh, fcntl.LOCK_UN)   # hand it to the battery
                return
            except OSError:
                pass
        time.sleep(5)
    raise RuntimeError(f"lock busy > {LOCK_WAIT_S}s: {LOCK}")


def variant_argv(size: int, port: int, inspect: dict) -> list[str]:
    binds = []
    for bind in inspect.get("Binds") or []:
        parts = bind.split(":")
        if len(parts) < 2 or not parts[0].startswith("/"):
            raise RuntimeError(f"non-absolute bind refused: {bind!r}")
        binds += ["-v", f"{parts[0]}:{parts[1]}:ro"]   # absolute + :ro (§7)
    argv = ["docker", "run", "-d", "--name", f"{VARIANT_PREFIX}-{size}",
            "--restart", "no", "--gpus", "all",
            "--shm-size", str(inspect.get("ShmSize") or 16 * 1024 ** 3),
            "-p", f"{port}:{CONTAINER_PORT}", "-e", "HF_HUB_OFFLINE=1"]
    for b in binds:
        argv.append(b)
    argv += [IMAGE, f"--max-mamba-cache-size={size}"]
    return argv


def execute(size: int, port: int) -> int:
    variant = f"{VARIANT_PREFIX}-{size}"
    rung = rung_dir(size)
    # [0b] stop-safety gate — WIN-SGL measured: an --rm/AutoRemove container
    # is DESTROYED by `docker stop`, so `docker start` restore would be void.
    out = sh(["docker", "inspect", PRODUCTION, "--format",
              "{{json .HostConfig}}"])
    host = json.loads(out.stdout)
    if host.get("AutoRemove") or (host.get("RestartPolicy") or {}).get("Name") not in (None, "no"):
        print("REFUSED: live container is not stop-safe "
              f"(AutoRemove={host.get('AutoRemove')}, "
              f"Restart={((host.get('RestartPolicy') or {}).get('name'))}). "
              "Rewrite stop-safe per WIN-SGL prepare_production under "
              "operator approval first.", file=sys.stderr)
        return 2
    sh(["docker", "stop", "-t", "60", PRODUCTION])
    status = "failed"
    try:
        sh(variant_argv(size, port, host))
        health(f"http://127.0.0.1:{port}/health")
        doc = capture(f"http://127.0.0.1:{port}/get_server_info",
                      rung / "server_info.json")
        if doc.get("max_mamba_cache_size") != size or doc.get("page_size") != 1:
            raise RuntimeError(
                f"readback gate failed: max_mamba_cache_size="
                f"{doc.get('max_mamba_cache_size')!r} page_size="
                f"{doc.get('page_size')!r} (want {size} / 1) — flag rejected?")
        wait_lock_free()
        help_out = sh(["python3", str(BATTERY), "--help"], check=False)
        if "--base-url" not in (help_out.stdout + help_out.stderr):
            raise RuntimeError("battery.py exposes no --base-url flag: edit "
                               "M4_MEASURE_ARGV in sweep.py (assumption A2)")
        measure = [a.format(port=port) if "{port}" in a else a
                   for a in M4_MEASURE_ARGV]
        sh(measure)
        status = "measured"
    finally:
        sh(["docker", "stop", "-t", "60", variant], check=False)
        sh(["docker", "rm", variant], check=False)
        sh(["docker", "start", PRODUCTION])
        health(f"http://127.0.0.1:{PROD_PORT}/health")
        doc = capture(f"http://127.0.0.1:{PROD_PORT}/get_server_info",
                      rung / "restore_server_info.json")
        mismatches = restore_proof(doc)
        if mismatches:
            (rung / "restore-proof-FAILED.json").write_text(
                json.dumps({"mismatches": mismatches,
                            "captured": {k: doc.get(k) for k in RESTORE_KEYS}},
                           indent=2))
            print("RESTORE PROOF FAILED — sweep halted:\n  " +
                  "\n  ".join(mismatches), file=sys.stderr)
            return 3
        print(f"restore proof PASS ({status})")
    return 0


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mamba-cache-size", type=int, required=True,
                    help=f"rung value, one of {LADDER}")
    ap.add_argument("--port", type=int, required=True,
                    help="host port for the variant container")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="print the exact command sequence (default)")
    mode.add_argument("--execute", action="store_true",
                      help="actually run the rung (operator approval required)")
    args = ap.parse_args(argv)

    problems = preflight(args.mamba_cache_size, args.port)
    if problems:
        print("REFUSED — pre-flight baseline check failed:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    if args.execute:
        return execute(args.mamba_cache_size, args.port)
    return dry_run(args.mamba_cache_size, args.port)


if __name__ == "__main__":
    sys.exit(main())
