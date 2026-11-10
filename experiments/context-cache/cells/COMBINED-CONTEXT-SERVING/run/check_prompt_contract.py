#!/usr/bin/env python3
"""Static conformance: rendered prompts carry the capability + reply-format sentences."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
ARMS = CELL / "arms"
TASKS = CELL / "tasks"
if str(ARMS) not in sys.path:
    sys.path.insert(0, str(ARMS))

import render_arms  # noqa: E402

NO_TOOLS = "You have no tools and cannot read files."
REPLY_FORMAT = "Reply with exactly one fenced ```python block that prints the requested values."
FORBIDDEN = ("read the", "open the file", "cat ", "grep")
DUVAL_PREFIX = "/home/zer0null/Duval/"


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`]*`", "", text)
    return text


def main() -> int:
    total = 0
    ok = 0
    failures = []
    for task_path in sorted(TASKS.glob("*.json")):
        if not task_path.name.startswith(("T1", "T2", "T3", "T4")):
            continue
        fixture = json.loads(task_path.read_text(encoding="utf-8"))
        task_id = fixture["task_id"]

        # reply_format equals stdout thresholds
        stdout_thresholds = [c["expected"] for c in fixture["acceptance"]["checks"] if c.get("target") == "stdout"]
        rf = fixture.get("reply_format", {})
        if rf.get("required_output") != stdout_thresholds:
            failures.append(f"{task_id}: reply_format.required_output {rf.get('required_output')} != {stdout_thresholds}")
        if rf.get("kind") != "python_block" or rf.get("executed_in") != "seeded_dir":
            failures.append(f"{task_id}: bad reply_format kind/executed_in")

        # fresh seed for this task
        seed_proc = subprocess.run(
            [sys.executable, str(TASKS / "seed.py"), "--task", task_id],
            cwd=str(CELL), capture_output=True, text=True)
        if seed_proc.returncode != 0:
            failures.append(f"{task_id}: seed.py failed: {seed_proc.stderr.strip()}")
            continue
        seed_root = TASKS / "work" / task_id / "seed"

        turns = fixture.get("turns", [])
        for arm in ("A", "B", "C"):
            for turn in range(1, len(turns) + 1):
                turn_obj = turns[turn-1] if 0 <= turn-1 < len(turns) else {}
                total += 1
                msgs = render_arms.build_messages(arm, fixture, [], turn)
                system = msgs[0]["content"] if msgs else ""
                first_user = msgs[1]["content"] if len(msgs) > 1 else ""
                blob = system + "\n" + first_user
                problems = []
                if NO_TOOLS not in blob:
                    problems.append("missing no-tools sentence")
                if REPLY_FORMAT not in blob:
                    problems.append("missing reply-format sentence")
                stripped = strip_code(blob)
                low = stripped.lower()
                for phrase in FORBIDDEN:
                    if phrase.lower() in low:
                        problems.append(f"forbidden phrase {phrase!r}")
                # new assertion: no instruction-shaped absolute path outside origin:
                no_origin = re.sub(r"origin:[^\n]*", "", blob)
                if re.search(r"/home/zer0null|/Duval", no_origin):
                    problems.append("instruction-shaped absolute path outside origin:")
                # new assertion: question states the explicit print contract
                q = turn_obj.get("question", "") if isinstance(turn_obj, dict) else ""
                stdout_checks = [c for c in fixture.get("acceptance", {}).get("checks", []) if c.get("target") == "stdout"]
                if stdout_checks:
                    if "key=value" not in q:
                        problems.append("missing key=value requirement")
                    if "print exactly" not in q or "nothing else" not in q:
                        problems.append("missing explicit print contract")
                    for c in stdout_checks:
                        exp = str(c.get("expected", ""))
                        key = exp.split("=", 1)[0] if "=" in exp else exp
                        if f"{key}=" not in q:
                            problems.append(f"missing expected token key {key}=")
                else:
                    if "print" not in q.lower():
                        problems.append("missing declared print target")

                # relative paths listed must exist in fresh seed
                for m in re.finditer(r"path=(\S+)", blob):
                    rel = m.group(1).rstrip(",")
                    if rel.startswith("/"):
                        continue
                    if not (seed_root / rel).is_file():
                        problems.append(f"relative path not in seed: {rel}")
                if problems:
                    failures.append(f"{task_id} arm={arm} turn={turn}: " + "; ".join(problems))
                else:
                    ok += 1

    print(f"conformance: {ok}/{total} (4 tasks x 3 arms x 12 turns)")
    if failures:
        for f in failures[:20]:
            print("FAIL:", f)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
