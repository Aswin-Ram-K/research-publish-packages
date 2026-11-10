#!/usr/bin/env python3
"""Execute one artifact against one task and print JSON lines."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

CELL = Path(__file__).resolve().parents[2]
TASKS = CELL / "tasks"
SEED = TASKS / "seed.py"
PYTHON = sys.executable


def load_fixture(task_id: str) -> dict:
    path = TASKS / f"{task_id}.json"
    if not path.is_file():
        raise SystemExit(f"fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def extract_code(text: str) -> str:
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    if m:
        return m.group(1)
    return text


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_tree(root: Path) -> dict[str, str]:
    out = {}
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root))] = sha256_file(p)
    return out


def match_text(text: str, expected, mode: str, ignore_case: bool = False) -> bool:
    text = str(text).strip()
    if isinstance(expected, list):
        return any(match_text(text, item, mode, ignore_case) for item in expected)
    want = str(expected).strip()
    if mode == "exact":
        return text.lower() == want.lower() if ignore_case else text == want
    if mode == "contains":
        return (want.lower() in text.lower()) if ignore_case else (want in text)
    if mode == "regex":
        flags = re.I if ignore_case else 0
        try:
            return re.search(want, text, flags) is not None
        except re.error:
            return False
    return False


def run_artifact(seed_root: Path, code: str) -> tuple[int, str, str, Path]:
    solution = seed_root / "solution.py"
    solution.write_text(code, encoding="utf-8")
    broader_root = seed_root.parent.parent
    scratch = Path(tempfile.mkdtemp(prefix="ccs-scratch-"))
    netlog = scratch / "network.log"
    shim_dir = CELL / "tasks" / "grade" / "shim"
    cmd = [
        "bwrap",
        "--ro-bind", "/", "/",
        "--ro-bind", str(shim_dir), str(shim_dir),
        "--tmpfs", "/tmp",
        "--dir", str(scratch),
        "--bind", str(broader_root), str(broader_root),
        "--bind", str(scratch), str(scratch),
        "--chdir", str(seed_root),
        "--setenv", "PYTHONPATH", str(shim_dir),
        "--setenv", "NETWORK_LOG", str(netlog),
        "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        PYTHON, str(solution),
    ]
    try:
        run = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=30,
        )
        return run.returncode, run.stdout, run.stderr, netlog
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", (exc.stderr or "") + "\nTIMEOUT", netlog


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--artifact", help="path to artifact")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    task_id = args.task
    fixture = load_fixture(task_id)

    if args.list:
        for check in fixture.get("acceptance", {}).get("checks", []):
            print(
                f"{check.get('id')} kind={check.get('kind')} target={check.get('target')} "
                f"threshold={check.get('expected')} match={check.get('match', 'contains')}"
            )
        return 0

    if not args.artifact:
        raise SystemExit("--artifact required unless --list")

    artifact_path = Path(args.artifact).resolve()
    code = extract_code(artifact_path.read_text(encoding="utf-8"))

    work_parent = TASKS / "work" / task_id
    work_parent.mkdir(parents=True, exist_ok=True)
    seed_root = work_parent / "seed"
    if seed_root.exists():
        shutil.rmtree(seed_root)

    proc = subprocess.run(
        [PYTHON, str(SEED), "--task", task_id],
        cwd=str(CELL),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(json.dumps({"check": "seed", "ok": False, "evidence": proc.stderr.strip() or proc.stdout.strip()}))
        print(json.dumps({"verified_success": False}))
        return 1

    before_seed = snapshot_tree(seed_root)
    broader_root = seed_root.parent.parent
    before_broader = snapshot_tree(broader_root)

    exit_code, stdout, stderr, netlog = run_artifact(seed_root, code)

    after_seed = snapshot_tree(seed_root)
    after_broader = snapshot_tree(broader_root)

    seed_changed = []
    for rel, digest in before_seed.items():
        if rel == "SEED_MANIFEST.json":
            continue
        if after_seed.get(rel) != digest:
            seed_changed.append(rel)

    outside_new = []
    outside_changed = []
    for rel in after_broader:
        if rel.startswith(f"{task_id}/seed/"):
            continue
        if rel.startswith(f"{task_id}/seed-perturbed"):
            continue
        if rel not in before_broader:
            outside_new.append(rel)
        else:
            # track changed existing files outside seed
            if before_broader.get(rel) != after_broader.get(rel):
                outside_changed.append(rel)

    network_hit_regex = re.search(
        r"\b(import\s+(socket|urllib|requests|httpx|http\.client)\b|from\s+(socket|urllib|requests|httpx|http\.client)\b)",
        code,
    ) is not None

    network_hit_exec = False
    network_module = None
    if netlog.exists():
        lines = [ln.strip() for ln in netlog.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            network_hit_exec = True
            network_module = lines[0]

    network_hit = network_hit_regex or network_hit_exec

    results = []
    all_ok = True

    for raw in fixture.get("acceptance", {}).get("checks", []):
        check_id = str(raw.get("id"))
        kind = str(raw.get("kind"))
        target = raw.get("target", "stdout")
        expected = raw.get("expected")
        mode = str(raw.get("match", "contains"))
        ignore_case = bool(raw.get("ignore_case", False))

        if kind == "derivation":
            # Run against a perturbed copy and require the output to track it.
            pert = raw.get("perturbation") or {}
            pert_root = work_parent / f"seed-perturbed-{uuid.uuid4().hex}"
            try:
                shutil.copytree(seed_root, pert_root)
                target_file = pert_root / pert["path"]
                original_text = target_file.read_text(encoding="utf-8")
                if pert["find"] not in original_text:
                    raise RuntimeError(f"perturbation find string not found in {pert['path']}")
                target_file.write_text(
                    original_text.replace(pert["find"], pert["replace"], 1),
                    encoding="utf-8",
                )
                pert_exit, pert_stdout, pert_stderr, _ = run_artifact(pert_root, code)
                pert_expected = raw.get("perturbed_expected")
                ok = (
                    exit_code == 0
                    and pert_exit == 0
                    and match_text(stdout, expected, mode, ignore_case)
                    and match_text(pert_stdout, pert_expected, mode, ignore_case)
                )
                evidence = (
                    f"original stdout has {expected!r}; perturbed stdout has {pert_expected!r}"
                    if ok
                    else (
                        f"tracking failed: original exit {exit_code}, perturbed exit {pert_exit}; "
                        f"original stdout {stdout.strip()[:200]!r}; perturbed stdout {pert_stdout.strip()[:200]!r}"
                    )
                )
            except Exception as exc:
                ok = False
                evidence = f"derivation setup failed: {exc}"
            finally:
                if pert_root.exists():
                    shutil.rmtree(pert_root, ignore_errors=True)
        elif target == "exit_code":
            ok = exit_code == expected
            evidence = f"exit code {exit_code}" + (
                f"; stderr: {stderr.strip()[:200]}" if not ok else ""
            )
        else:
            ok = match_text(stdout, expected, mode, ignore_case)
            evidence = (
                f"stdout contains {expected!r}"
                if ok
                else f"stdout missing {expected!r}; got {stdout.strip()[:300]!r}"
            )

        results.append({"check": check_id, "ok": bool(ok), "evidence": evidence})
        all_ok = all_ok and bool(ok)

    for raw in fixture.get("acceptance", {}).get("negative_constraints", []):
        cid = str(raw.get("id"))
        detect = raw.get("detect")
        fired = False
        evidence = "not fired"
        if detect == "network_import":
            if network_hit:
                fired = True
                if network_hit_exec and network_module:
                    evidence = f"runtime import hook fired: {network_module} (mechanism: import hook)"
                elif network_hit_regex:
                    evidence = "network import detected in artifact (literal regex)"
                else:
                    evidence = "network import detected in artifact"
        elif detect == "seed_digests":
            if seed_changed:
                fired = True
                evidence = "seeded input changed: " + ", ".join(seed_changed)
        elif detect == "outside_writes":
            if outside_new or outside_changed:
                fired = True
                parts = []
                if outside_new:
                    parts.append("new: " + ", ".join(outside_new))
                if outside_changed:
                    parts.append("changed: " + ", ".join(outside_changed))
                evidence = "write outside seed directory: " + "; ".join(parts)
        else:
            pattern = raw.get("pattern")
            if pattern and re.search(pattern, code, re.I if raw.get("ignore_case") else 0):
                fired = True
                evidence = "forbidden pattern matched"
        ok = not fired
        results.append({"check": cid, "ok": bool(ok), "evidence": evidence})
        all_ok = all_ok and bool(ok)

    for r in results:
        print(json.dumps(r, separators=(",", ":")))
    print(json.dumps({"verified_success": bool(all_ok)}))

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
