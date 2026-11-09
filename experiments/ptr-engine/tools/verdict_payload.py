#!/usr/bin/env python3
"""verdict_payload.py — turn one acceptance run into an `orchestration_verdict` payload.

Why this exists: `orchestration/VERDICT-RITUAL.md`. The binary gate derives PASS/FAIL from a
verdict row `{command, exitCode, sha}`; a card that never writes one settles FAIL `no-verdict`
however much work it delivered. This tool runs the acceptance command once, in the same shell
form the judge uses (`/bin/sh -c <command>`), and prints the row ready to paste.

    python3 experiments/ptr-engine/tools/verdict_payload.py \
        --task 5b8c6ec4-a9e2-4d32-983f-037c46b327e7 \
        --execution d026f43f-25f3-4a4e-a95c-a6e5ab48c4aa \
        --command 'python3 experiments/ptr-engine/longrun/tests/test_verdict_payload.py'

Stdout: exactly one JSON object, one line, keys in this order:
    taskId, executionId, command, exitCode, sha, output_tail

`command` is echoed BYTE-IDENTICAL to the `--command` argv — no re-quoting, no shell escaping —
because the gate freezes that string per execution and a re-quoted retry is refused
(`command-frozen`). The process exits with the acceptance command's own exit code, so the tool
never turns a failure into a success.

Honesty rules baked in:
  * `sha` is read from `git --no-optional-locks rev-parse HEAD` BEFORE the command runs. If git
    cannot answer, `sha` is dropped from the payload and an `UNSTAMPED` warning goes to stderr —
    an absent sha is honest, a guessed one is not.
  * a non-empty `git --no-optional-locks status --porcelain` prints a warning on stderr: the sha
    is still the head, but the tree the command ran against differs from it.
"""

import argparse
import json
import os
import subprocess
import sys

OUTPUT_TAIL_CHARS = 2000
KEYS = ["taskId", "executionId", "command", "exitCode", "sha", "output_tail"]


def _head_sha(cwd=None):
    """The 40-hex commit the command is about to run against; None if git cannot answer."""
    proc = subprocess.run(
        ["git", "--no-optional-locks", "rev-parse", "HEAD"],
        cwd=cwd, capture_output=True, text=True,
    )
    sha = (proc.stdout or "").strip()
    if proc.returncode != 0 or len(sha) != 40:
        return None
    return sha


def _dirty_paths(cwd=None):
    """Uncommitted paths, or None when this is not a git worktree."""
    proc = subprocess.run(
        ["git", "--no-optional-locks", "status", "--porcelain"],
        cwd=cwd, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    return [line for line in (proc.stdout or "").splitlines() if line.strip()]


def build_payload(task, execution, command, cwd=None, run=None):
    """Run `command` and return (payload, dirty_paths). sha is sampled before the run."""
    runner = run or (lambda c: subprocess.run(
        c, shell=True, cwd=cwd, capture_output=True, text=True, errors="replace",
    ))
    sha = _head_sha(cwd)
    dirty = _dirty_paths(cwd)
    proc = runner(command)
    combined = (proc.stdout or "") + (proc.stderr or "")
    payload = {
        "taskId": task,
        "executionId": execution,
        "command": command,
        "exitCode": proc.returncode,
        "sha": sha,
        "output_tail": combined[-OUTPUT_TAIL_CHARS:],
    }
    # An unknown sha is dropped, never faked: the record call will then be refused `bad-sha`,
    # which is the honest outcome.
    payload = {k: payload[k] for k in KEYS if payload.get(k) is not None}
    return payload, dirty


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--task", required=True, help="task board card id")
    parser.add_argument("--execution", required=True, help="execution id of this run")
    parser.add_argument("--command", required=True,
                        help="the acceptance command, as one frozen string (echoed verbatim)")
    parser.add_argument("--cwd", default=None, help="where to run it (default: process cwd)")
    args = parser.parse_args(argv)

    payload, dirty = build_payload(args.task, args.execution, args.command, cwd=args.cwd)

    if "sha" not in payload:
        print("UNSTAMPED: `git rev-parse HEAD` gave no 40-hex sha; payload has no `sha` key. "
              "Record it as unstamped in the handoff rather than inventing one.", file=sys.stderr)
    if dirty:
        print("WARNING: dirty tree — `git status --porcelain` reports %d uncommitted path(s). "
              "The sha is still the head, but the tree the command ran against differs from it."
              % len(dirty), file=sys.stderr)
        for line in dirty[:10]:
            print("  " + line, file=sys.stderr)
        if len(dirty) > 10:
            print("  ... %d more" % (len(dirty) - 10), file=sys.stderr)

    print(json.dumps(payload, ensure_ascii=False))
    return payload["exitCode"]


if __name__ == "__main__":
    sys.exit(main())
