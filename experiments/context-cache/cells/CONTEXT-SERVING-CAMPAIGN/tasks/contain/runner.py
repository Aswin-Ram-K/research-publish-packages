#!/usr/bin/env python3
"""bwrap-based containment runner. Refuses to run if bwrap is unavailable/unprivileged."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

BWRAP = shutil.which("bwrap")


def available() -> tuple[bool, str]:
    if BWRAP is None:
        return False, "bwrap not found on PATH"
    try:
        probe = subprocess.run(
            [BWRAP, "--unshare-net", "--ro-bind", "/", "/", "--dev", "/dev", "/bin/true"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover
        return False, f"bwrap probe failed: {exc}"
    if probe.returncode != 0:
        return False, (probe.stderr.strip() or probe.stdout.strip() or f"exit {probe.returncode}")
    return True, ""


def run_contained(command: str, workdir: str | Path, timeout: int = 30) -> dict:
    ok, reason = available()
    if not ok:
        return {"containment_engaged": False, "refused": True, "reason": reason,
                "returncode": None, "stdout": "", "stderr": reason}
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        BWRAP,
        "--unshare-net",
        "--ro-bind", "/", "/",
        "--bind", str(workdir), str(workdir),
        "--dev", "/dev",
        "--chdir", str(workdir),
        "--die-with-parent",
        "--",
        "sh", "-c", command,
    ]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "containment_engaged": True,
            "refused": False,
            "reason": "",
            "returncode": run.returncode,
            "stdout": run.stdout,
            "stderr": run.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "containment_engaged": True,
            "refused": False,
            "reason": "",
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + "\nTIMEOUT",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir")
    ap.add_argument("--command")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    if args.probe:
        pass
    elif not args.workdir or not args.command:
        ap.error("--workdir and --command required unless --probe")

    if args.probe:
        ok, reason = available()
        print(json.dumps({"bwrap_path": BWRAP, "available": ok, "reason": reason,
                          "version": _version()}))
        return 0 if ok else 1

    res = run_contained(args.command, args.workdir, args.timeout)
    print(json.dumps(res))
    return 0 if (res.get("containment_engaged") and res.get("returncode") == 0) else 1


def _version() -> str:
    if BWRAP is None:
        return ""
    try:
        r = subprocess.run([BWRAP, "--version"], capture_output=True, text=True, timeout=10)
        return (r.stdout.strip() or r.stderr.strip())
    except Exception:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
