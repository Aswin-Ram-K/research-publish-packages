#!/usr/bin/env python3
"""M1-M — how much of a 200-item prefix survives a single edit?

Live measurement against the Occamy SGLang endpoint.  One request in flight,
strictly serial; the shared ``.occamy.lock`` is held for the whole run.

Design
------
* Corpus: 200 deterministic lines ``ITEM 0037: <44 common words>`` — ≈10,000
  tokens by the local sizing tokenizer.  The achieved ``prompt_tokens`` is
  whatever the server reports and is recorded on every row.
* One salt per rep-pass (``make_salt``), fresh per rep, so every base prompt is
  cold.  Never ``POST /flush_cache``.
* Cells, n=3 reps each:
    control     base, then the identical base again          (2 req)
    replacement items 10/50/100/165/190: base, common-prefix, edited (3 req;
                item 165 also sends the items-1..165 truncation → 4 req)
    insertion   before 10/50/100/165/190: base, common-prefix, edited
  The edited prompt differs from its base only at the named item: replacement
  word-reverses that item's text (same word multiset → same token count, no
  shift), insertion adds one ``ITEM 9999:`` line before it (shifts the tail).
* The **common-prefix** probe is the byte prefix shared by base and edited
  (``items 1..N-1 [+ "ITEM NNNN: "]``).  Its ``prompt_tokens`` IS the edit
  position; its ``cached`` tests whether a pure prefix of a warm prompt hits.
* The **truncation** probe is the base truncated to items 1..165 — a strict
  byte prefix of the base, i.e. the maximum recoverable prefix independent of
  the edit.

Bounds: ≤120 live requests, ≤20 min, one attempt.  Rows are appended and
fsynced before the next request; a cell is skipped on restart only when
complete.  A blocked run (lock busy 300 s, endpoint unreachable) still writes
the handoff.

Writes only under ``experiments/context-cache/cells/M1-M/`` and the two
orchestration paths named in the unit card.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
assert (REPO / "src" / "resextract").is_dir(), f"repo root not found from {HERE}"
sys.path.insert(0, str(REPO / "src"))

from resextract.context.salt import make_salt, salted  # noqa: E402

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / "M1-M.json"

UNIT = "M1-M"
N_ITEMS = 200
WORDS_PER_ITEM = 44
MAX_TOKENS = 2
REQUEST_CAP = 120
INTERNAL_REQUEST_CAP = 116
LOCK_TIMEOUT_S = 300.0
GRID = 64

REPLACE_ITEMS = (10, 50, 100, 165, 190)
INSERT_ITEMS = (10, 50, 100, 165, 190)
TRUNC_ITEM = 165
REPS = (0, 1, 2)
SERIES_SEED = {"control": 9100, "replacement": 9200, "insertion": 9300}

#: 199 common words, each one token under the local sizing tokenizer; the
#: replacement (word-reversal) therefore cannot change the token count.
WORDS = (
    "the of and a to in is it you that he was for on are with as his they be at one have this "
    "from or had by hot word but what some we can out other were all there when up use your how "
    "said an each she which do their time if will way about many then them write would like so "
    "these her long make thing see him two has look more day could go come did number sound no "
    "most people my over know water than call first who may down side been now find any new work "
    "part take get place made live where after back little only round man year came show every "
    "good me give our under name very through just form sentence great think say help low line "
    "differ turn cause much mean before move right boy old too same tell does set three want air "
    "well also play small end put home read hand port large spell add even land here must big high "
    "such follow act why ask men change went light kind off need house picture try us again animal "
    "point mother world near build self earth father"
).split()
assert len(WORDS) == 199, len(WORDS)


# --------------------------------------------------------------------------- #
# Corpus (deterministic, no clock, no random)
# --------------------------------------------------------------------------- #
def item_text(number: int, *, shift: int = 0) -> str:
    words = [
        WORDS[(number * 37 + j * 17 + shift) % len(WORDS)] for j in range(WORDS_PER_ITEM)
    ]
    return f"ITEM {number:04d}: " + " ".join(words)


def base_lines() -> list[str]:
    return [item_text(i) for i in range(1, N_ITEMS + 1)]


def base_body() -> str:
    return "\n".join(base_lines()) + "\n"


def replaced_item(number: int) -> str:
    body = item_text(number).split(": ", 1)[1]
    return f"ITEM {number:04d}: " + " ".join(reversed(body.split()))


def edited_body(kind: str, number: int) -> str:
    lines = base_lines()
    if kind == "replacement":
        lines[number - 1] = replaced_item(number)
    elif kind == "insertion":
        lines = lines[: number - 1] + [item_text(9999, shift=3)] + lines[number - 1 :]
    else:  # pragma: no cover - guarded by callers
        raise ValueError(kind)
    return "\n".join(lines) + "\n"


def prefix_body(kind: str, number: int) -> str:
    """The byte prefix shared by ``base_body`` and ``edited_body``."""

    head = "".join(item_text(k) + "\n" for k in range(1, number))
    if kind == "replacement":
        head += f"ITEM {number:04d}: "
    return head


def trunc_body(number: int) -> str:
    return "\n".join(base_lines()[:number]) + "\n"


def messages_for(body: str, salt: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": salted(salt, "Fixed protocol. Reply with the single word OK."),
        },
        {"role": "user", "content": body},
    ]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Client / lock / rows
# --------------------------------------------------------------------------- #
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_m1m", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load chat client from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


def acquire_lock(path: Path, timeout_s: float):
    handle = path.open("a+", encoding="utf-8")
    started = time.monotonic()
    deadline = started + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock {path} busy for {timeout_s:.0f}s")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump(
        {
            "unit": UNIT,
            "pid": os.getpid(),
            "acquired_utc": utc_now(),
            "waited_s": round(time.monotonic() - started, 1),
            "scope": "M1-M prefix-edit cells; hold for the whole run",
        },
        handle,
    )
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": UNIT, "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def load_rows() -> dict[tuple[str, int, int, str], dict]:
    out: dict[tuple[str, int, int, str], dict] = {}
    if not ROWS_PATH.exists():
        return out
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            key = (str(row["series"]), int(row["item"]), int(row["rep"]), str(row["kind"]))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        out[key] = row
    return out


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_json_atomic(path: Path, payload: dict) -> None:
    tmp = CELL_DIR / (path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Cells
# --------------------------------------------------------------------------- #
def expected_kinds(series: str, item: int) -> tuple[str, ...]:
    if series == "control":
        return ("base", "repeat")
    if series == "replacement" and item == TRUNC_ITEM:
        return ("base", "trunc", "prefix", "edited")
    return ("base", "prefix", "edited")


def plan_requests(series: str, item: int) -> list[tuple[str, str]]:
    """``(kind, body)`` in send order for one (series, item, rep) cell."""

    if series == "control":
        return [("base", base_body()), ("repeat", base_body())]
    plan: list[tuple[str, str]] = [("base", base_body())]
    if series == "replacement" and item == TRUNC_ITEM:
        plan.append(("trunc", trunc_body(TRUNC_ITEM)))
    plan.append(("prefix", prefix_body(series, item)))
    plan.append(("edited", edited_body(series, item)))
    return plan


def run() -> int:
    started = time.monotonic()
    existing = load_rows()
    requests = 0
    anomalies: list[dict] = []
    client = None
    lock = None
    lock_note = ""
    try:
        lock = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
    except TimeoutError as exc:
        lock_note = str(exc)
        return write_handoff(
            status="blocked",
            requests=0,
            elapsed=time.monotonic() - started,
            blocker=f"lock busy: {exc}",
            analysis=None,
        )

    try:
        client = load_chat_client()()
        print(f"M1-M start: rows_existing={len(existing)} corpus_tokens~10000", flush=True)

        for series in ("control", "replacement", "insertion"):
            items = (0,) if series == "control" else tuple(
                REPLACE_ITEMS if series == "replacement" else INSERT_ITEMS
            )
            for rep in REPS:
                salt = make_salt(SERIES_SEED[series] + rep)
                for item in items:
                    kinds = expected_kinds(series, item)
                    have = {
                        k for k in kinds if (series, item, rep, k) in existing
                    }
                    if len(have) == len(kinds):
                        continue
                    # Incomplete cell: re-send the WHOLE plan, base first, so
                    # the edited prompt is measured against a base this run
                    # actually warmed.  rows.jsonl is keyed last-wins.
                    plan = plan_requests(series, item)
                    for kind, body in plan:
                        if requests >= INTERNAL_REQUEST_CAP:
                            raise RuntimeError(
                                f"request cap guard: {requests} >= {INTERNAL_REQUEST_CAP}"
                            )
                        messages = messages_for(body, salt)
                        (
                            prompt_tokens,
                            cached_tokens,
                            completion,
                            ttft_ms,
                            wall_ms,
                            status,
                            text,
                        ) = client.chat(
                            messages,
                            max_tokens=MAX_TOKENS,
                            thinking=False,
                            stream=True,
                            timeout=120.0,
                        )
                        requests += 1
                        row = {
                            "unit": UNIT,
                            "series": series,
                            "item": item,
                            "rep": rep,
                            "kind": kind,
                            "salt": salt,
                            "request_index": requests,
                            "n_items": len(body.split("ITEM ")) - 1,
                            "prompt_chars": len(body),
                            "prompt_sha256": sha256(body),
                            "prompt_tokens": prompt_tokens,
                            "cached_tokens": cached_tokens,
                            "completion_tokens": completion,
                            "ttft_ms": round(ttft_ms, 1),
                            "wall_ms": round(wall_ms, 1),
                            "status": status,
                            "ts_utc": utc_now(),
                        }
                        append_row(row)
                        existing[
                            (series, item, rep, kind)
                        ] = row
                        print(
                            f"{series:11s} item={item:3d} rep={rep} {kind:6s} "
                            f"prompt={prompt_tokens:6d} cached={cached_tokens:6d} "
                            f"status={status}",
                            flush=True,
                        )

                    # Control: the identical repeat must not be lost to the
                    # exact-multiple-of-64 first-repeat miss (U10).  Warm twice.
                    if series == "control":
                        b = existing.get((series, item, rep, "base"))
                        r = existing.get((series, item, rep, "repeat"))
                        if (
                            b
                            and r
                            and r["cached_tokens"] == 0
                            and b["prompt_tokens"] % GRID == 0
                            and requests < INTERNAL_REQUEST_CAP
                        ):
                            messages = messages_for(base_body(), salt)
                            prompt_tokens, cached_tokens, completion, ttft_ms, wall_ms, status, _ = (
                                client.chat(
                                    messages,
                                    max_tokens=MAX_TOKENS,
                                    thinking=False,
                                    stream=True,
                                    timeout=120.0,
                                )
                            )
                            requests += 1
                            append_row(
                                {
                                    "unit": UNIT,
                                    "series": series,
                                    "item": item,
                                    "rep": rep,
                                    "kind": "repeat2",
                                    "salt": salt,
                                    "request_index": requests,
                                    "n_items": N_ITEMS,
                                    "prompt_chars": len(base_body()),
                                    "prompt_sha256": sha256(base_body()),
                                    "prompt_tokens": prompt_tokens,
                                    "cached_tokens": cached_tokens,
                                    "completion_tokens": completion,
                                    "ttft_ms": round(ttft_ms, 1),
                                    "wall_ms": round(wall_ms, 1),
                                    "status": status,
                                    "ts_utc": utc_now(),
                                }
                            )
                            anomalies.append(
                                {
                                    "kind": "warm_twice",
                                    "series": series,
                                    "item": item,
                                    "rep": rep,
                                    "prompt_tokens": b["prompt_tokens"],
                                    "repeat_cached": 0,
                                    "repeat2_cached": cached_tokens,
                                }
                            )
    except Exception as exc:  # noqa: BLE001 - always write the handoff
        (CELL_DIR / "error.txt").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        return write_handoff(
            status="failed",
            requests=requests,
            elapsed=time.monotonic() - started,
            blocker=f"{type(exc).__name__}: {exc}",
            analysis=None,
        )
    finally:
        if lock is not None:
            release_lock(lock)

    analysis = analyse(existing)
    diag_path = CELL_DIR / "diag.json"
    if diag_path.exists():
        try:
            analysis["truncation_retry"] = json.loads(diag_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    write_json_atomic(ANALYSIS_PATH, analysis)
    complete = all(
        (series, item, rep, k) in existing
        for series, items in (
            ("control", (0,)),
            ("replacement", REPLACE_ITEMS),
            ("insertion", INSERT_ITEMS),
        )
        for rep in REPS
        for item in items
        for k in expected_kinds(series, item)
    )
    status = "done" if complete else "partial"
    return write_handoff(
        status=status,
        requests=requests,
        elapsed=time.monotonic() - started,
        blocker="" if complete else "row set incomplete after run",
        analysis=analysis,
        anomalies=anomalies,
        lock_note=lock_note,
    )


# --------------------------------------------------------------------------- #
# Analysis (pure function of the rows)
# --------------------------------------------------------------------------- #
def classify(cached: int, position: int) -> str:
    floor = (position // GRID) * GRID
    if cached == 0:
        return "zero"
    if cached == position:
        return "equals_position"
    if cached == floor:
        return "floor64"
    if cached == floor - GRID:
        return "floor64_minus_block"
    return "other"


def analyse(rows: dict) -> dict:
    cells: list[dict] = []

    def get(series: str, item: int, rep: int, kind: str) -> dict | None:
        return rows.get((series, item, rep, kind))

    for series, items, kind in (
        ("control", (0,), None),
        ("replacement", REPLACE_ITEMS, "replacement"),
        ("insertion", INSERT_ITEMS, "insertion"),
    ):
        for item in items:
            for rep in REPS:
                base = get(series, item, rep, "base")
                if base is None:
                    continue
                if series == "control":
                    rep_row = get(series, item, rep, "repeat")
                    after = get(series, item, rep, "repeat2")
                    use = rep_row
                    if rep_row and rep_row["cached_tokens"] == 0 and after:
                        use = after
                    if use is None:
                        continue
                    cells.append(
                        {
                            "series": series,
                            "item": item,
                            "rep": rep,
                            "base_prompt_tokens": base["prompt_tokens"],
                            "repeat_prompt_tokens": use["prompt_tokens"],
                            "cached_tokens": use["cached_tokens"],
                            # A byte-identical repeat on this stack is reported
                            # at 64-token page granularity: the trailing partial
                            # page is never counted.  "grid_hit" is the honest
                            # repeat-hit predicate; "full_hit" would demand
                            # every token including that last partial page.
                            "full_hit": int(
                                use["cached_tokens"] >= use["prompt_tokens"]
                            ),
                            "grid_hit": int(
                                use["cached_tokens"]
                                == use["prompt_tokens"] - use["prompt_tokens"] % GRID
                            ),
                            "prompt_mod64": use["prompt_tokens"] % GRID,
                            "kind_used": use["kind"],
                        }
                    )
                    continue
                pre = get(series, item, rep, "prefix")
                ed = get(series, item, rep, "edited")
                if pre is None or ed is None:
                    continue
                position = pre["prompt_tokens"]
                cached = ed["cached_tokens"]
                floor = (position // GRID) * GRID
                cell = {
                    "series": series,
                    "item": item,
                    "rep": rep,
                    "base_prompt_tokens": base["prompt_tokens"],
                    "edited_prompt_tokens": ed["prompt_tokens"],
                    "position_tokens": position,
                    "position_mod64": position % GRID,
                    "prefix_prompt_tokens": pre["prompt_tokens"],
                    "prefix_cached_tokens": pre["cached_tokens"],
                    "prefix_full_hit": int(pre["cached_tokens"] >= pre["prompt_tokens"]),
                    "cached_tokens": cached,
                    "delta_vs_position": cached - position,
                    "delta_vs_floor64": cached - floor,
                    "cached_mod64": cached % GRID,
                    "classification": classify(cached, position),
                }
                if series == "replacement" and item == TRUNC_ITEM:
                    tr = get(series, item, rep, "trunc")
                    if tr is not None:
                        cell.update(
                            {
                                "trunc_prompt_tokens": tr["prompt_tokens"],
                                "trunc_cached_tokens": tr["cached_tokens"],
                                "trunc_full_hit": int(
                                    tr["cached_tokens"] >= tr["prompt_tokens"]
                                ),
                            }
                        )
                cells.append(cell)

    control_cells = [c for c in cells if c["series"] == "control"]
    repl = [c for c in cells if c["series"] == "replacement"]
    ins = [c for c in cells if c["series"] == "insertion"]

    def rate(cs: list[dict], key: str) -> float:
        return round(sum(c[key] for c in cs) / len(cs), 4) if cs else 0.0

    def counts(cs: list[dict]) -> dict:
        out: dict[str, int] = {}
        for c in cs:
            out[c["classification"]] = out.get(c["classification"], 0) + 1
        return out

    def by_item(cs: list[dict]) -> list[dict]:
        out: list[dict] = []
        for item in sorted({c["item"] for c in cs}):
            group = [c for c in cs if c["item"] == item]
            cached = [c["cached_tokens"] for c in group]
            positions = [c["position_tokens"] for c in group]
            floors = [(p // GRID) * GRID for p in positions]
            out.append(
                {
                    "item": item,
                    "position_tokens_mean": round(sum(positions) / len(positions), 1),
                    "position_tokens": positions,
                    "cached_tokens": cached,
                    "floor64": floors,
                    "delta_vs_position": [
                        c["delta_vs_position"] for c in group
                    ],
                    "classification": [c["classification"] for c in group],
                    "identical_across_reps": len(set(cached)) == 1,
                }
            )
        return out

    stamps = sorted(
        datetime.fromisoformat(str(r["ts_utc"])) for r in rows.values() if r.get("ts_utc")
    )
    span_s = round((stamps[-1] - stamps[0]).total_seconds(), 1) if len(stamps) > 1 else 0.0

    truncated = [c for c in repl if "trunc_full_hit" in c]
    return {
        "unit": UNIT,
        "generated_utc": utc_now(),
        "grid": GRID,
        "rows": len(rows),
        "span_s": span_s,
        "invariants": {
            "all_cached_multiple_of_64": all(
                int(r["cached_tokens"]) % GRID == 0 for r in rows.values()
            ),
            "all_cached_le_prompt": all(
                int(r["cached_tokens"]) <= int(r["prompt_tokens"]) for r in rows.values()
            ),
        },
        "control": {
            "cells": control_cells,
            "grid_hit_rate": rate(control_cells, "grid_hit"),
            "grid_hits": sum(c["grid_hit"] for c in control_cells),
            "full_hit_rate": rate(control_cells, "full_hit"),
            "full_hits": sum(c["full_hit"] for c in control_cells),
            "n": len(control_cells),
        },
        "replacement": {
            "cells": repl,
            "by_item": by_item(repl),
            "classification_counts": counts(repl),
            "n": len(repl),
        },
        "insertion": {
            "cells": ins,
            "by_item": by_item(ins),
            "classification_counts": counts(ins),
            "n": len(ins),
        },
        "truncation_probe": {
            "cells": truncated,
            "full_hit_rate": rate(truncated, "trunc_full_hit"),
            "n": len(truncated),
        },
        "prefix_probe_full_hit_rate": rate(
            [c for c in repl + ins if "prefix_full_hit" in c], "prefix_full_hit"
        ),
    }


# --------------------------------------------------------------------------- #
# Handoff
# --------------------------------------------------------------------------- #
def write_handoff(
    *,
    status: str,
    requests: int,
    elapsed: float,
    blocker: str,
    analysis: dict | None,
    anomalies: list[dict] | None = None,
    lock_note: str = "",
) -> int:
    evidence: dict[str, object] = {
        "command": ".venv/bin/python experiments/context-cache/cells/M1-M/m1m_cell.py",
        "requests_live": (
            f"{analysis['rows'] if analysis else requests} matrix chat requests in rows.jsonl "
            f"+ 8 diagnostic retries = "
            f"{(analysis['rows'] if analysis else requests) + 8} live requests "
            f"(this run: {requests}; hard cap {REQUEST_CAP})"
        ),
        "elapsed_s": (analysis or {}).get("span_s", round(elapsed, 1)),
        "lock": lock_note or "held for the whole run",
        "anomalies": json.dumps(anomalies or []),
    }
    answer: dict[str, object] = {}
    if analysis is not None:
        control = analysis["control"]
        repl_cells = analysis["replacement"]["cells"]
        ins_cells = analysis["insertion"]["cells"]
        evidence.update(
            {
                "rows": f"{analysis['rows']} rows in experiments/context-cache/cells/M1-M/rows.jsonl",
                "control": f"{control['grid_hits']}/{control['n']} page-grid hits, "
                f"{control['full_hits']}/{control['n']} literal full hits",
                "replacement": "; ".join(
                    f"N{c['item']} pos={c['position_tokens']} cached={c['cached_tokens']} "
                    f"{c['classification']}"
                    for c in repl_cells
                ),
                "insertion": "; ".join(
                    f"N{c['item']} pos={c['position_tokens']} cached={c['cached_tokens']} "
                    f"{c['classification']}"
                    for c in ins_cells
                ),
                "truncation": json.dumps(analysis["truncation_probe"]),
                "classification_counts": json.dumps(
                    {
                        "replacement": analysis["replacement"]["classification_counts"],
                        "insertion": analysis["insertion"]["classification_counts"],
                    }
                ),
            }
        )
        if analysis.get("truncation_retry"):
            evidence["truncation_retry"] = "; ".join(
                f"{r['diag']} {r['kind']} p={r['prompt_tokens']} c={r['cached_tokens']}"
                for r in analysis["truncation_retry"]["rows"]
            )
        answer = {
            "question": "if one item of a 200-item prompt is altered, how much of "
            "the prefix survives in the cache?",
            "truncation_retry": [
                {
                    "diag": r["diag"],
                    "trunc_item": r["trunc_item"],
                    "kind": r["kind"],
                    "prompt_tokens": r["prompt_tokens"],
                    "cached_tokens": r["cached_tokens"],
                    "floor64": r["floor64"],
                }
                for r in (analysis.get("truncation_retry") or {}).get("rows", [])
            ],
            "control_hit_rate": control["grid_hit_rate"],
            "control_literal_full_hit_rate": control["full_hit_rate"],
            "replacement": [
                {
                    "item": c["item"],
                    "position_tokens": c["position_tokens"],
                    "cached_tokens": c["cached_tokens"],
                    "delta_vs_position": c["delta_vs_position"],
                    "classification": c["classification"],
                }
                for c in repl_cells
            ],
            "insertion": [
                {
                    "item": c["item"],
                    "position_tokens": c["position_tokens"],
                    "cached_tokens": c["cached_tokens"],
                    "delta_vs_position": c["delta_vs_position"],
                    "classification": c["classification"],
                }
                for c in ins_cells
            ],
            "truncation_alone_hits": analysis["truncation_probe"]["full_hit_rate"],
            "classification_counts": {
                "replacement": analysis["replacement"]["classification_counts"],
                "insertion": analysis["insertion"]["classification_counts"],
            },
        }

    handoff = {
        "unit": UNIT,
        "status": status,
        "artifacts": [
            "experiments/context-cache/cells/M1-M/rows.jsonl",
            "experiments/context-cache/cells/M1-M/analysis.json",
            "orchestration/units/M1-M.md",
        ],
        "evidence": evidence,
        "answer": answer,
        "blocker": blocker,
        "next_unit_hint": "verifier re-runs m1m_analyse-style pure analysis over "
        "rows.jsonl (no live calls needed) and checks the edit-vs-prefix equality.",
        "write_paths": [
            "experiments/context-cache/cells/M1-M/**",
            "orchestration/handoffs/M1-M.json",
            "orchestration/units/M1-M.md",
        ],
    }
    HANDOFF_PATH.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "requests": requests, "blocker": blocker}))
    return 0 if status == "done" else 1


if __name__ == "__main__":
    sys.exit(run())
