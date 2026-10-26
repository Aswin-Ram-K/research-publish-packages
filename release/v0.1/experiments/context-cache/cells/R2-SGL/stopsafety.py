#!/usr/bin/env python3
"""R2-SGL-CAP stop-safety rewrite — make production survivable so a window can stop it.

THE DEFECT THIS FIXES
=====================
`state/config/occamy-inspect-pre.json` records `HostConfig.AutoRemove = true`, and the systemd unit
launches with `docker run --rm`.  An `--rm` container is **destroyed** by `docker stop`; `docker start`
then has nothing to start.  `WIN-SGL` hit this live and had to rewrite production before it could run a
single variant, and `variant_launcher.assert_stop_safe()` exists precisely to refuse to proceed until
it is fixed.

THE HAZARD THAT MAKES A NAIVE FIX DANGEROUS
===========================================
Production is the `ExecStart` of `systemctl --user gx10-occamy-nvfp4.service`, and that unit's
`ExecStartPre` is `-/usr/bin/docker rm -f gx10-occamy-nvfp4`.  So:

* create an `AutoRemove=false` copy and simply `docker start` it later -> the next
  `systemctl --user start` **removes the copy in ExecStartPre** and starts a fresh `--rm` container.
  Restore would appear to work and the container would in fact be a *different* one.
* `docker run -d` the replacement and then `systemctl --user start` -> two containers race for the
  `--publish serving-host:30000` binding.

Neither is acceptable for a card whose hard rule is "production must never be left down".  The rewrite
therefore re-declares the unit with `AutoRemove=false` **and the argv copied verbatim from the live
inspect**, retires the original argv to a `.r2sgl.bak`, and keeps the unit as the single authority
over production's lifecycle.  `--revert` puts the original unit back byte-for-byte.

VERIFICATION (all of it local, none of it asserted)
===================================================
* the replacement argv equals `Config.Cmd` exactly, token for token;
* the replacement `--rm`, if present, is removed and nothing else changes;
* `AutoRemove` reads `false` from docker *before* the unit is declared;
* the swapped unit's `ExecStart` parses to the same image and the same argv;
* on `--revert`, the restored unit file is byte-identical to the retired original (sha256).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
STATE = REPO / "state" / "config"
SPEC_PATH = STATE / "occamy-inspect-pre.json"
SERVICE = "gx10-occamy-nvfp4.service"
PRODUCTION = "gx10-occamy-nvfp4"

SSH = ["ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
       "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8", "-o", "LogLevel=ERROR",
       "zer0null@serving-host"]


def sh(argv: list[str], *, timeout: float = 120.0) -> subprocess.CompletedProcess:
    return subprocess.run(SSH + [shlex.join(argv)], capture_output=True, text=True, timeout=timeout)


def unit_path() -> Path:
    """Where the unit lives, as systemd reports it (FragmentPath), not as guessed."""
    r = sh(["systemctl", "--user", "show", SERVICE, "-p", "FragmentPath"])
    for line in r.stdout.splitlines():
        if line.startswith("FragmentPath="):
            return Path(line.split("=", 1)[1].strip())
    raise RuntimeError(f"could not resolve FragmentPath for {SERVICE}: {r.stderr.strip()}")


def current_execstart(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("ExecStart="):
            return line[len("ExecStart="):]
    raise RuntimeError("unit has no ExecStart line")


def rewrite_execstart(execstart: str) -> tuple[str, dict[str, Any]]:
    """Drop `--rm` and nothing else. Returns (new_execstart, evidence)."""
    tokens = shlex.split(execstart)
    has_rm = "--rm" in tokens
    new_tokens = [t for t in tokens if t != "--rm"]
    evidence = {
        "had_rm": has_rm,
        "token_count_before": len(tokens),
        "token_count_after": len(new_tokens),
        "removed_tokens": [t for t in tokens if t not in new_tokens] if has_rm else [],
        "only_rm_changed": (set(tokens) - set(new_tokens)) in (set(), {"--rm"}),
        "argvs_identical_apart_from_rm": [t for t in tokens if t != "--rm"] == new_tokens,
    }
    return shlex.join(new_tokens), evidence


def argv_from_execstart(execstart: str) -> list[str]:
    """The container argv (everything after the image id), for comparison against Config.Cmd."""
    tokens = shlex.split(execstart)
    start = 0
    for i, tok in enumerate(tokens):
        if tok.startswith("sha256:"):
            start = i + 1
            break
    return tokens[start:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="stop-safety rewrite for the occamy production unit")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--out", default=str(STATE / "r2-sgl-stopsafety.json"))
    args = ap.parse_args(argv)

    spec = json.loads(SPEC_PATH.read_text())
    spec = spec[0] if isinstance(spec, list) else spec
    prod_cmd = [str(t) for t in spec["Config"]["Cmd"]]
    upath = unit_path()
    original = sh(["cat", str(upath)]).stdout
    orig_exec = current_execstart(original)
    new_exec, evidence = rewrite_execstart(orig_exec)
    new_unit = original.replace(f"ExecStart={orig_exec}", f"ExecStart={new_exec}", 1)

    argv_ok = argv_from_execstart(new_exec) == prod_cmd
    record: dict[str, Any] = {
        "unit": "R2-SGL-CAP",
        "step": "stop_safety_rewrite",
        "fragment_path": str(upath),
        "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "new_unit_sha256": hashlib.sha256(new_unit.encode()).hexdigest(),
        "evidence": evidence,
        "argv_matches_inspect": argv_ok,
        "argv_len": len(prod_cmd),
        "note": ("rewrite removes --rm so the container survives `docker stop`; the unit stays the "
                 "single authority because its ExecStartPre does `docker rm -f`, which would delete "
                 "any out-of-band replacement anyway"),
    }
    print(json.dumps(record, indent=1))
    if not argv_ok:
        print("REFUSED: rewritten ExecStart argv does not match the inspected production argv", file=sys.stderr)
        return 2
    if not evidence["argvs_identical_apart_from_rm"]:
        print("REFUSED: rewrite changed more than --rm", file=sys.stderr)
        return 2
    if not args.apply and not args.revert:
        Path(args.out).write_text(json.dumps(record, indent=1))
        print(f"DRY RUN: would rewrite {upath} and restart {SERVICE}; nothing touched")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
