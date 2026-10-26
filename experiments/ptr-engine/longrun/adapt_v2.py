#!/usr/bin/env python3
"""Adapt a BOUNDED-tier authored fixture (``tasks-v2/LR-0N.v2.json``, schema
``consonance.fixture/1``) to the RUNTIME shape ``run_longrun.py`` can load
(``consonance.longrun-fixture/1``), writing ``tasks-v2/runtime-v2/LR-0N.v2.json``.

Relationship to ``adapt_fixture.py`` (v1 tier, NOT edited here):
  * this adapter IMPORTS it for the pieces that are already proven -- schema
    constants, pinned-source loading with digest verification, the pointer slice,
    the bytes-per-token measurement and the authored-turn question mapping --
    instead of reimplementing them;
  * it differs in exactly the places the v2 tier requires:
      - the system prompt is ``adapt_fixture.SYSTEM_PROMPT`` + the v2 budget
        instruction (``answer_budget.system_prompt_addition``), because
        ``run_longrun.py:210`` sends ``fixture["system_prompt"]`` verbatim as the
        request's system message -- that single string is the only channel the
        budget sentence can travel on;
      - ``answer_budget``, ``acceptance.checks_structured``, ``checkpoints``,
        ``negative_constraints``, ``class``/``objective``, ``long_run`` and
        ``fixture_version`` are carried through verbatim;
      - output file name keeps the ``.v2`` suffix, so the v1 ``runtime/`` tree and
        its digests cannot be touched.

Required keys are checked explicitly: a fixture missing any of them is a HARD
FAILURE (non-zero exit, that fixture named, nothing written for it).

Deterministic: ``json.dumps(..., indent=2, sort_keys=True) + "\\n"`` -- no
timestamps, no absolute paths that depend on the invocation, so two runs produce
identical bytes.

Usage:
    .venv/bin/python experiments/ptr-engine/longrun/adapt_v2.py --all
    .venv/bin/python experiments/ptr-engine/longrun/adapt_v2.py --fixture .../LR-01.v2.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import adapt_fixture as base  # noqa: E402  (sys.path set above)

AUTHORED_SCHEMA = base.AUTHORED_SCHEMA
RUNTIME_SCHEMA = base.RUNTIME_SCHEMA
DEFAULT_FIXTURE_DIR = os.path.join("experiments", "ptr-engine", "longrun", "tasks-v2")
DEFAULT_OUT_DIR = os.path.join("experiments", "ptr-engine", "longrun", "tasks-v2", "runtime-v2")

# Keys this adapter refuses to run without (the runner's required set plus the
# v2 tiers's contract fields).
REQUIRED_TOP = ("schema", "task_id", "sources", "turns", "checkpoints",
                "acceptance", "answer_budget")

BUDGET_HEADER = "ANSWER BUDGET"


class AdaptError(base.AdaptError):
    """A required key is missing or a stated value contradicts the derived one."""


def require(doc: dict, key: str, path: str, where: str = "fixture"):
    if key not in doc or doc[key] in (None, "", [], {}):
        raise AdaptError(f"{path}: {where} missing required key {key!r}")
    return doc[key]


def budget_system_prompt(doc: dict, path: str) -> str:
    """Base system prompt + the tier's budget instruction, as ONE string."""
    budget = require(doc, "answer_budget", path)
    addition = require(budget, "system_prompt_addition", path, "answer_budget")
    if not isinstance(addition, str):
        raise AdaptError(f"{path}: answer_budget.system_prompt_addition is not a string")
    return f"{base.SYSTEM_PROMPT}\n\n{addition.strip()}"


def adapt_v2(path: str) -> dict:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise AdaptError(f"cannot read authored fixture {path}: {exc}") from exc
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdaptError(f"authored fixture {path} is not JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise AdaptError(f"{path}: authored fixture is not a JSON object")

    for key in REQUIRED_TOP:
        require(doc, key, path)

    if doc["schema"] != AUTHORED_SCHEMA:
        raise AdaptError(f"{path}: unsupported authored schema {doc['schema']!r} "
                         f"(expected {AUTHORED_SCHEMA!r})")

    acceptance = doc["acceptance"]
    if not isinstance(acceptance, dict):
        raise AdaptError(f"{path}: acceptance is not an object")
    checks_structured = require(acceptance, "checks_structured", path, "acceptance")
    if not isinstance(checks_structured, list):
        raise AdaptError(f"{path}: acceptance.checks_structured is not a list")
    negative_constraints = require(acceptance, "negative_constraints", path, "acceptance")
    if not isinstance(negative_constraints, list):
        raise AdaptError(f"{path}: acceptance.negative_constraints is not a list")
    checkpoints = doc["checkpoints"]
    if not isinstance(checkpoints, list) or not checkpoints:
        raise AdaptError(f"{path}: checkpoints is not a non-empty list")

    items, verified = base.load_items(doc["sources"])

    turns = sorted(doc["turns"], key=lambda t: int(t["turn"]))
    numbered = [int(t["turn"]) for t in turns]
    n = len(turns)
    if numbered != list(range(1, n + 1)):
        raise AdaptError(f"{path}: authored turns are not numbered 1..{n}: {numbered[:5]}…")

    # N: carried from the stated long_run.turns when present, and refused if it
    # contradicts len(turns) -- the runner computes requests as N x reps and
    # requires turns numbered 1..N, so the two must agree.
    stated_n = None
    if isinstance(doc.get("long_run"), dict):
        stated_n = doc["long_run"].get("turns")
    if stated_n is not None and int(stated_n) != n:
        raise AdaptError(f"{path}: long_run.turns={stated_n} contradicts len(turns)={n}")

    runtime_turns = []
    for t in turns:
        entry = {"turn": int(t["turn"]), "question": base.authored_turn_question(t)}
        if t.get("kind"):
            entry["kind"] = t["kind"]
        runtime_turns.append(entry)

    bpt, nbytes, ntokens = base.measure_bytes_per_token(items)

    wall_tokens = doc.get("wall_tokens")
    if wall_tokens is None and isinstance(doc.get("long_run"), dict):
        wall_tokens = doc["long_run"].get("wall_tokens")
    stated_wall = wall_tokens is not None
    wall_tokens = int(wall_tokens) if stated_wall else base.DEFAULT_WALL_TOKENS

    system_prompt = budget_system_prompt(doc, path)

    # Stable provenance path (relative to the longrun dir) so two runs from
    # different cwds still produce identical bytes.
    rel = os.path.relpath(os.path.abspath(path), HERE).replace(os.sep, "/")

    return {
        "schema": RUNTIME_SCHEMA,
        "task_id": doc["task_id"],
        "N": n,
        "wall_tokens": wall_tokens,
        "window_tokens": wall_tokens,
        "bytes_per_token": bpt,
        "system_prompt": system_prompt,
        "items": items,
        "turns": runtime_turns,
        # ---- v2 carry-through ----
        "class": doc.get("class"),
        "objective": doc.get("objective"),
        "fixture_version": doc.get("fixture_version"),
        "long_run": doc.get("long_run", {}),
        "answer_budget": doc["answer_budget"],
        "checkpoints": checkpoints,
        "acceptance": acceptance,
        "repair": doc.get("repair", {}),
        "expected": doc.get("expected", {}),
        "derived_from": {"path": rel, "sha256": base.sha256_bytes(raw)},
        "adaptation": {
            "adapter": "experiments/ptr-engine/longrun/adapt_v2.py",
            "imports": "experiments/ptr-engine/longrun/adapt_fixture.py",
            "authored_schema": AUTHORED_SCHEMA,
            "runtime_schema": RUNTIME_SCHEMA,
            "bytes_per_token_method": "tiktoken cl100k_base tokens over the loaded item bodies",
            "body_bytes": nbytes,
            "body_tokens": ntokens,
            "wall_tokens_default_used": not stated_wall,
            "wall_tokens_default": base.DEFAULT_WALL_TOKENS,
            "turn_field_mapped": "instruction -> question",
            "sources_verified": verified,
            "system_prompt_contains_budget": BUDGET_HEADER in system_prompt,
            "system_prompt_added_chars": len(system_prompt) - len(base.SYSTEM_PROMPT),
            "checks_structured_count": len(checks_structured),
            "negative_constraints_count": len(negative_constraints),
            "checkpoint_count": len(checkpoints),
            "n_stated": stated_n,
        },
    }


def runtime_path(out_dir: str, task_id: str) -> str:
    return os.path.join(out_dir, f"{task_id}.v2.json")


def write_runtime(runtime: dict, out_dir: str) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    path = runtime_path(out_dir, runtime["task_id"])
    data = json.dumps(runtime, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)
    return path, base.sha256_text(data)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true", help="adapt every authored v2 fixture")
    ap.add_argument("--fixture", action="append", default=None, help="authored v2 fixture")
    ap.add_argument("--fixture-dir", default=DEFAULT_FIXTURE_DIR)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    if args.all:
        names = sorted(n for n in os.listdir(args.fixture_dir)
                       if re.match(r"^LR-\d+.*\.json$", n))
        paths = [os.path.join(args.fixture_dir, n) for n in names]
    elif args.fixture:
        paths = list(args.fixture)
    else:
        ap.error("give --all or --fixture PATH")
        return 2

    if not paths:
        print(f"no authored fixtures found in {args.fixture_dir}", file=sys.stderr)
        return 2

    rc = 0
    for path in paths:
        try:
            runtime = adapt_v2(path)
        except AdaptError as exc:
            print(f"ADAPT FAILED {path}: {exc}", file=sys.stderr)
            rc = 1
            continue
        out, sha = write_runtime(runtime, args.out_dir)
        a = runtime["adaptation"]
        print(f"{out}  sha256:{sha}")
        print(f"  task_id={runtime['task_id']} N={runtime['N']} items={len(runtime['items'])} "
              f"wall_tokens={runtime['wall_tokens']} bytes_per_token={runtime['bytes_per_token']} "
              f"checks_structured={a['checks_structured_count']} negative_constraints="
              f"{a['negative_constraints_count']} checkpoints={a['checkpoint_count']} "
              f"budget_in_system_prompt={a['system_prompt_contains_budget']} "
              f"derived_from=sha256:{runtime['derived_from']['sha256'][:16]}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
