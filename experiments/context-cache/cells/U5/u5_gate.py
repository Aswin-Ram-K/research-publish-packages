#!/usr/bin/env python3
"""U5 live gate: run the quality cells against occamy-1.0.

Protocol (unit card):
* acquire ``experiments/context-cache/.occamy.lock`` with ``flock`` before the
  first live request and hold it for the whole batch (40-minute wait cap);
* one request in flight at a time;
* ``temperature=0``, ``thinking=False``, ``max_tokens=64``, ``stream=True``;
* retry once on failure, 3 consecutive failures -> STOP, status ``blocked``;
* <= 900 live requests and a hard wall-clock deadline.

Cells: 190 cases x (1 shallow + 3 deep conditions) = 760 requests.  Both
compaction arms are actually run at deep even though their rendered prompts are
byte-identical (asserted); the shallow cell is run once per case and reported
for both shallow arms, because the two shallow renderings are byte-identical by
construction.

Every raw response is stored in ``u5_raw.jsonl`` so a verifier can re-parse
without re-running the model.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

import importlib.util  # noqa: E402

import u5_cells as cellsmod  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "u5_occamy_client", ROOT / "experiments" / "context-cache" / "client.py"
)
_client_mod = importlib.util.module_from_spec(_spec)
sys.modules["u5_occamy_client"] = _client_mod
_spec.loader.exec_module(_client_mod)
ChatClient = _client_mod.ChatClient

LOCK_PATH = ROOT / "experiments" / "context-cache" / ".occamy.lock"
RAW_PATH = HERE / "u5_raw.jsonl"
SUMMARY_PATH = HERE / "u5_summary.json"
PROGRESS_PATH = HERE / "u5_progress.json"

MAX_REQUESTS = 900
LOCK_WAIT_S = 40 * 60
DEADLINE_S = 50 * 60          # hard stop; unit budget is 60 minutes
PROBE_BUDGET_S = 40 * 60      # projected-full-run must fit under this

DEEP_CONDITIONS = ("baseline", "summarise", "fork")


# ---------------------------------------------------------------------- #
# Answer parsing
# ---------------------------------------------------------------------- #
def parse_letter(text: str, n_options: int) -> dict[str, Any]:
    """First option letter that appears; strict variant for sensitivity."""

    allowed = cellsmod.LETTERS[:n_options]
    raw = text or ""

    m = re.search(r"\b([" + allowed + r"])\b", raw)
    if m:
        return {"letter": m.group(1), "method": "boundary"}
    m = re.search(r"[" + allowed + r"]", raw)
    if m:
        return {"letter": m.group(0), "method": "any_char"}
    m = re.search(r"\b([" + allowed.lower() + r"])\b", raw)
    if m:
        return {"letter": m.group(1).upper(), "method": "lowercase"}
    return {"letter": None, "method": "none"}


def strict_letter(text: str, n_options: int) -> str | None:
    stripped = (text or "").strip()
    if stripped and stripped[0].upper() in cellsmod.LETTERS[:n_options]:
        return stripped[0].upper()
    return None


# ---------------------------------------------------------------------- #
# Lock
# ---------------------------------------------------------------------- #
def acquire_lock(deadline: float) -> tuple[Any, dict[str, Any]]:
    fh = open(LOCK_PATH, "a+", encoding="utf-8")
    waited = 0.0
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            if waited >= LOCK_WAIT_S or time.time() > deadline:
                fh.close()
                raise TimeoutError(f"could not acquire {LOCK_PATH} within {LOCK_WAIT_S}s")
            time.sleep(5)
            waited += 5
    info = {
        "unit": "U5",
        "pid": os.getpid(),
        "acquired_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "waited_s": waited,
    }
    fh.seek(0)
    fh.truncate(0)
    fh.write(json.dumps(info) + "\n")
    fh.flush()
    return fh, info


# ---------------------------------------------------------------------- #
# Request
# ---------------------------------------------------------------------- #
def one_request(client: ChatClient, messages: list[dict[str, str]]) -> tuple[Any, str | None]:
    """Exactly one chat call.  Returns (7-tuple, error-string-or-None)."""

    try:
        return (
            client.chat(
                messages,
                max_tokens=64,
                thinking=False,
                stream=True,
                timeout=180.0,
            ),
            None,
        )
    except Exception as exc:  # noqa: BLE001 - surfaced as-is in the row
        return None, f"{type(exc).__name__}: {exc}"


def run_cell(
    client: ChatClient,
    case: dict[str, Any],
    index: int,
    depth: str,
    condition: str,
    pinned: dict[str, Any],
    out: Any,
    stats: dict[str, Any],
) -> dict[str, Any] | None:
    cell = cellsmod.build_cell(case, index, depth, condition, pinned)
    messages = cell["messages"]
    prompt_text = cellsmod.concat(messages)
    n_options = len(case["options"])
    correct_letter = cellsmod.LETTERS[int(case["correct"])]
    retain = cellsmod.retention(cell, case)

    result, error = one_request(client, messages)
    stats["requests"] += 1

    row: dict[str, Any] = {
        "case_id": case["id"],
        "kind": case["kind"],
        "depth": depth,
        "condition": condition,
        "correct_index": int(case["correct"]),
        "correct_letter": correct_letter,
        "n_options": n_options,
        "prompt_sha256": cellsmod.sha(prompt_text),
        "prompt_chars": len(prompt_text),
        "prompt_est_tokens": sum(cellsmod.default_est_tokens(m["content"]) for m in messages),
        "messages": len(messages),
        "history_turns": cell["history_turns"],
        "compacted": cell["compacted"],
        "compaction_event": cell["compaction_event"],
        "retained": retain,
        "raw": None,
        "prompt_tokens": None,
        "cached_tokens": None,
        "completion_tokens": None,
        "ttft_ms": None,
        "wall_ms": None,
        "status": None,
        "error": error,
    }

    if result is not None:
        prompt, cached, completion, ttft, wall, status, text = result
        parsed = parse_letter(text, n_options)
        row.update(
            {
                "raw": text,
                "prompt_tokens": int(prompt),
                "cached_tokens": int(cached),
                "completion_tokens": int(completion),
                "ttft_ms": round(float(ttft), 3),
                "wall_ms": round(float(wall), 3),
                "status": int(status),
                "parsed_letter": parsed["letter"],
                "parse_method": parsed["method"],
                "strict_letter": strict_letter(text, n_options),
                "correct": parsed["letter"] == correct_letter,
            }
        )
        stats["wall_s"] += float(wall) / 1000.0
        if text.strip():
            stats["nonempty"] += 1

    out.write(json.dumps(row) + "\n")
    out.flush()
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=0, help="0 = decide from probe")
    ap.add_argument("--max-requests", type=int, default=MAX_REQUESTS)
    args = ap.parse_args()

    started = time.time()
    deadline = started + DEADLINE_S
    cases = cellsmod.load_cases()
    pinned = cellsmod.load_pinned()

    # ---- offline assertions (free) ------------------------------------
    shallow = cellsmod.shallow_identity(cases, pinned)
    pointer = cellsmod.pointer_equivalence(cases, pinned)
    deep = cellsmod.deep_identity(cases, pinned)
    print(
        f"[assert] shallow summarise==fork {shallow['identical']} ({shallow['cases']} cases); "
        f"pointer==append {pointer['identical']} ({pointer['cells_checked']} cells); "
        f"deep summarise==fork {deep['identical_cases']}/{deep['cases']}",
        flush=True,
    )
    print(
        f"[assert] gold retained baseline={deep['gold_retained']['baseline']} "
        f"summarise={deep['gold_retained']['summarise']} fork={deep['gold_retained']['fork']}",
        flush=True,
    )

    lock_fh, lock_info = acquire_lock(deadline)
    print(f"[lock] acquired after {lock_info['waited_s']}s: {lock_info}", flush=True)

    client = ChatClient()
    RAW_PATH.write_text("", encoding="utf-8")
    out = open(RAW_PATH, "a", encoding="utf-8")
    stats = {"requests": 0, "wall_s": 0.0, "nonempty": 0, "failures": 0}

    def write_progress(phase: str, done: int, total: int, n_cases: int) -> None:
        PROGRESS_PATH.write_text(
            json.dumps(
                {
                    "phase": phase,
                    "done": done,
                    "total": total,
                    "cases": n_cases,
                    "requests": stats["requests"],
                    "consecutive_failures": stats["failures"],
                    "elapsed_s": round(time.time() - started, 1),
                }
            )
            + "\n",
            encoding="utf-8",
        )

    rows_all: list[dict[str, Any]] = []
    try:
        # ---- probe -----------------------------------------------------
        probe = run_cell(client, cases[0], 0, "deep", "baseline", pinned, out, stats)
        probe_ok = probe is not None and probe.get("status") == 200
        if not probe_ok:
            print(f"[probe] FAILED: {probe and probe.get('error')}", flush=True)
            summary = {
                "status": "blocked",
                "blocker": f"server unreachable or request failed: {probe and probe.get('error')}",
                "requests": stats["requests"],
            }
            SUMMARY_PATH.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
            raise SystemExit(3)

        deep_wall = float(probe["wall_ms"]) / 1000.0
        print(
            f"[probe] baseline deep: prompt={probe['prompt_tokens']} tokens "
            f"cached={probe['cached_tokens']} wall={deep_wall:.2f}s",
            flush=True,
        )

        # Projected cost of a full 190-case run: 190 shallow + 190*3 deep.
        # Assume compacted deep cells cost ~35% of the baseline cell and
        # shallow ~15% (measured against the probe where possible).
        compact_wall = max(0.4, deep_wall * 0.35)
        shallow_wall = max(0.3, deep_wall * 0.15)
        per_case = len(DEEP_CONDITIONS) * 0.0 + (deep_wall + 2 * compact_wall + shallow_wall)
        projected_full = per_case * len(cases)
        print(
            f"[probe] projected full 190-case run: {per_case:.2f}s/case -> "
            f"{projected_full/60:.1f} min",
            flush=True,
        )

        if args.cases:
            n_cases = min(args.cases, len(cases))
        elif projected_full <= PROBE_BUDGET_S:
            n_cases = len(cases)
        else:
            n_cases = 100
        subset = list(range(len(cases)))
        if n_cases < len(cases):
            # Deterministic subset: take every k-th case, k = len//n, seeded
            # start = 0.  Fixed and reproducible from (190, n_cases).
            step = len(cases) // n_cases
            subset = list(range(0, len(cases), step))[:n_cases]
        n_req = len(subset) * (1 + len(DEEP_CONDITIONS))
        if n_req > args.max_requests:  # pragma: no cover - guard
            raise SystemExit(f"request budget exceeded: {n_req} > {args.max_requests}")
        print(
            f"[plan] cases={len(subset)} (of 190) requests={n_req} "
            f"first={cases[subset[0]]['id']} last={cases[subset[-1]]['id']}",
            flush=True,
        )

        total = n_req
        done = 0
        consecutive = 0
        for pos, index in enumerate(subset):
            case = cases[index]
            # Rows for the probe case were already written; skip it so the
            # raw file has exactly one row per cell.
            for condition in ("_shallow",) + DEEP_CONDITIONS:
                if not (pos == 0 and condition == "baseline"):
                    pass
                if time.time() > deadline:
                    print(f"[stop] deadline reached at {done}/{total}", flush=True)
                    raise TimeoutError("deadline")
                if condition == "_shallow":
                    row = run_cell(client, case, index, "shallow", "shared", pinned, out, stats)
                elif pos == 0 and condition == "baseline":
                    row = probe  # reuse the probe response for this exact cell
                else:
                    row = run_cell(client, case, index, "deep", condition, pinned, out, stats)
                done += 1
                if row is None or row.get("status") != 200:
                    consecutive += 1
                    stats["failures"] = consecutive
                    print(
                        f"[fail] {case['id']} {condition}: {row and row.get('error')} "
                        f"(consecutive={consecutive})",
                        flush=True,
                    )
                    if consecutive >= 3:
                        raise RuntimeError("3 consecutive failures")
                else:
                    consecutive = 0
                    stats["failures"] = 0
                if done % 10 == 0 or done == total:
                    write_progress("run", done, total, len(subset))
                    rate = (time.time() - started) / max(1, done)
                    print(
                        f"[run] {done}/{total} req={stats['requests']} "
                        f"{rate:.2f}s/cell-item eta={(total-done)*rate/60:.1f} min",
                        flush=True,
                    )

        summary = {
            "status": "done",
            "cases_used": len(subset),
            "subset_rule": "all 190" if len(subset) == 190 else f"every {len(cases)//len(subset)}-th case from 0",
            "subset_ids": [cases[i]["id"] for i in subset],
            "requests": stats["requests"],
            "wall_s": round(time.time() - started, 1),
            "probe": {
                "prompt_tokens": probe["prompt_tokens"],
                "cached_tokens": probe["cached_tokens"],
                "wall_s": round(deep_wall, 3),
            },
            "assertions": {
                "shallow_arms_identical": shallow["identical"],
                "pointer_equals_append": pointer["identical"],
                "pointer_cells_checked": pointer["cells_checked"],
                "deep_summarise_equals_fork": f"{deep['identical_cases']}/{deep['cases']}",
                "gold_retained": deep["gold_retained"],
                "question_retained": deep["question_retained"],
                "options_retained": deep["options_retained"],
            },
        }
    except TimeoutError as exc:
        summary = {
            "status": "partial",
            "blocker": f"deadline: {exc}",
            "requests": stats["requests"],
            "wall_s": round(time.time() - started, 1),
        }
    except RuntimeError as exc:
        summary = {
            "status": "blocked",
            "blocker": f"3 consecutive failures: {exc}",
            "requests": stats["requests"],
            "wall_s": round(time.time() - started, 1),
        }
    finally:
        out.close()
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        lock_fh.close()

    SUMMARY_PATH.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(f"[done] {json.dumps({k: v for k, v in summary.items() if k != 'subset_ids'})}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
