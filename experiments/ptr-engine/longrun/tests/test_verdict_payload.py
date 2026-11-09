#!/usr/bin/env python3
"""test_verdict_payload.py — the acceptance test for `tools/verdict_payload.py`.

Run: python3 experiments/ptr-engine/longrun/tests/test_verdict_payload.py

Checks:
  (a) the tool prints one JSON object with all six keys, and `command` is byte-identical to the
      `--command` argv it was given (no re-quoting);
  (b) a non-zero acceptance command propagates: the tool exits with it and reports it;
  (c) a dirty worktree warns on stderr and still prints a payload with the head sha;
  (d) red->green: with the sha computation removed the payload loses the `sha` key (the guard
      fails), and restoring the line makes it green again.

Exit 0 = all pass.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOOL = os.path.join(REPO, "experiments", "ptr-engine", "tools", "verdict_payload.py")
PY = sys.executable
SIX = ["taskId", "executionId", "command", "exitCode", "sha", "output_tail"]

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print("PASS %s%s" % (name, (" — " + detail) if detail else ""))
    else:
        print("FAIL %s%s" % (name, (" — " + detail) if detail else ""))
        FAILS.append(name)


def run_tool(command, cwd=None, tool=TOOL):
    proc = subprocess.run(
        [PY, tool, "--task", "T-1", "--execution", "E-1", "--command", command],
        cwd=cwd, capture_output=True, text=True,
    )
    return proc


def parse(proc):
    return json.loads(proc.stdout.strip())


def test_keys_and_verbatim_command():
    # Deliberately full of runs of spaces and quotes: any re-quoting shows up here.
    command = "python3 -c \"print('a  b', 'c')\""
    proc = run_tool(command)
    payload = parse(proc)
    check("a.keys", sorted(payload) == sorted(SIX), "keys=%s" % sorted(payload))
    check("a.command_verbatim", payload["command"] == command,
          "given=%r got=%r" % (command, payload["command"]))
    check("a.exit_zero", proc.returncode == 0 and payload["exitCode"] == 0,
          "tool exit=%d exitCode=%s" % (proc.returncode, payload["exitCode"]))
    check("a.sha_40_hex", isinstance(payload.get("sha"), str) and len(payload["sha"]) == 40,
          "sha=%s" % payload.get("sha"))
    check("a.stdout_single_object", len(proc.stdout.strip().splitlines()) == 1)


def test_exit_code_propagates():
    command = "python3 -c \"import sys; sys.exit(7)\""
    proc = run_tool(command)
    payload = parse(proc)
    check("b.exit_code_propagates", proc.returncode == 7 and payload["exitCode"] == 7,
          "tool exit=%d exitCode=%s (not swallowed)" % (proc.returncode, payload["exitCode"]))


def test_dirty_tree_warns():
    tmp = tempfile.mkdtemp(prefix="verdict-payload-dirty-")
    try:
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True, env=env)
        with open(os.path.join(tmp, "tracked.txt"), "w") as fh:
            fh.write("clean\n")
        subprocess.run(["git", "add", "tracked.txt"], cwd=tmp, check=True, env=env)
        subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-qm", "base"],
                       cwd=tmp, check=True, env=env)
        head = subprocess.run(["git", "--no-optional-locks", "rev-parse", "HEAD"],
                              cwd=tmp, capture_output=True, text=True).stdout.strip()
        with open(os.path.join(tmp, "tracked.txt"), "a") as fh:
            fh.write("dirty now\n")
        proc = run_tool("true", cwd=tmp)
        payload = parse(proc)
        check("c.warns_on_stderr", "WARNING: dirty tree" in proc.stderr, proc.stderr.strip()[:80])
        check("c.payload_still_printed", proc.stdout.strip().startswith("{") and payload["sha"] == head,
              "sha=%s head=%s" % (payload.get("sha"), head[:8]))
        check("c.exit_zero", proc.returncode == 0 and payload["exitCode"] == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_red_green_sha_key():
    """Remove the sha computation -> the payload must lose the key -> the guard fails."""
    src = open(TOOL, encoding="utf-8").read()
    line = "    sha = _head_sha(cwd)\n"
    check("d.line_present", line in src, "line=%r" % line.strip())

    tmp = tempfile.mkdtemp(prefix="verdict-payload-neutered-")
    try:
        neutered = os.path.join(tmp, "verdict_payload.py")
        with open(neutered, "w", encoding="utf-8") as fh:
            fh.write(src.replace(line, "    sha = None  # NEUTERED (red->green demonstration)\n"))
        red = run_tool("true", tool=neutered)
        red_payload = parse(red)
        print("RED   verdict_payload.py with `sha = None`: keys=%s" % sorted(red_payload))
        check("d.red_loses_sha", "sha" not in red_payload and sorted(red_payload) == sorted(SIX[0:4] + ["output_tail"]),
              "keys=%s" % sorted(red_payload))

        green = run_tool("true")
        green_payload = parse(green)
        print("GREEN restored (%d B): keys=%s" % (len(src), sorted(green_payload)))
        check("d.green_regains_sha", sorted(green_payload) == sorted(SIX))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    test_keys_and_verbatim_command()
    test_exit_code_propagates()
    test_dirty_tree_warns()
    test_red_green_sha_key()
    if FAILS:
        print("\n%d check(s) FAILED: %s" % (len(FAILS), ", ".join(FAILS)))
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
