#!/usr/bin/env python3
"""WIN-SGL cell — one SGLang pager configuration measured twice, identically.

The cell is deliberately a *clone* of the G3 design (`cells/G3/g3_cell.py`) so its
battery is directly comparable to the S0 rows already on disk:

* same corpus slice (`corpora/endtoend.json` scenario 0), same preamble, same
  turn texts and the same 32k/64k depths (74 / 148 turns);
* same arms R / A / C / H, same fixed salts (``make_salt(3201..3204)``), same
  ``keep_last=2``, same ``max_tokens=4`` -- so every rendered prompt in this
  cell is **byte-identical** to the S0 row at the same (depth, arm, turn);
* same per-turn row schema, plus the per-config fields the card requires
  (``stack``, ``config_id``, ``config_sha256``, ``page_size``, ``layer_types``).

On top of the battery it runs a controlled **grid probe**: four targets, each
sent three times byte-identically (``cold``/``rep1``/``rep2``), with the target
lengths chosen so that a 64-token grid and a 128-token grid predict *different*
cached values (``L`` in the odd-64-quotient region).  That is the direct
``cached = f(L)`` measurement the card asks for; the 888 battery rows are the
paired (identical-prompt) second instrument.

Budget: ``--cap`` live requests for the whole cell (battery first, probe last,
hard stop, one POST per counted request -- no hidden client retries).

Lock: ``fcntl.flock`` on ``experiments/context-cache/.occamy.lock`` for the whole
run, released on exit.

Usage::

    python win_sgl_cell.py --config-id S1 --page-size 64 --cap 900
    python win_sgl_cell.py --dry-run          # offline: fake send, no network
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
EXP = REPO / "experiments" / "context-cache"
for _p in (str(SRC), str(EXP), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    default_est_tokens,
    make_salt,
    needs_compaction,
    render,
)
from resextract.context.meter import normalise_cache  # noqa: E402
from resextract.context.render import canonical_bytes  # noqa: E402

ROWS_PATH = HERE / "rows.jsonl"
LOCK_PATH = EXP / ".occamy.lock"
CORPUS_PATH = EXP / "corpora" / "endtoend.json"
G3_ROWS = EXP / "cells" / "G3" / "rows.jsonl"
MODEL_CONFIG_LAYER_TYPES = {"linear_attention": 30, "full_attention": 10}
MODEL_LAYER_TYPES_SHA256 = None  # filled by run_unit from the checkpoint config.json

BASE_URL = "http://192.168.2.168:8012/v1"
MODEL = "occamy-1.0"
API_KEY = "EMPTY"
STACK = "sglang"
MAX_TOKENS = 4
KEEP_LAST = 2
SUMMARY_CHARS = 750
TIMEOUT_S = 180.0
PROBE_SLEEP_S = 1.0
LOCK_DEADLINE_S = 1800.0

#: (label, budget_tokens, turns) -- identical to G3.
DEPTHS: tuple[tuple[str, int, int], ...] = (
    ("32k", 32768, 74),
    ("64k", 65536, 148),
)

ARMS: tuple[dict[str, Any], ...] = (
    {"arm": "R", "policy": "summarise_in_place", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3201},
    {"arm": "A", "policy": "append_note", "compaction": CompactionPolicy.APPEND_NOTE, "seed": 3202},
    {"arm": "C", "policy": "none", "compaction": None, "seed": 3203},
    {"arm": "H", "policy": "hybrid", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3204},
)

#: Grid-probe targets, spaced 64 tokens apart on purpose: the quotient
#: ``(L-1)//64`` therefore alternates parity across the four targets, so *two of
#: the four discriminate a 64-token grid from a 128-token grid for any constant
#: chat-template/probe-calibration offset.  A 64-grid predicts
#: ``64*floor((L-1)/64)`` (1088 / 1152 / 1216 / 1280), a 128-grid predicts
#: ``128*floor((L-1)/128)`` (1024 / 1152 / 1152 / 1280) -- the 1100 and 1228
#: targets separate the two by a full 64-token block.
#: CPT below is the corpus-measured chars/token (3.7422, median over the 872 G3
#: rows with prompt>2000); the *actual* length of every probe is read back from
#: the response and recorded, never assumed.
PROBE_TARGETS: tuple[int, ...] = (1100, 1164, 1228, 1292)
PROBE_ROLES: tuple[str, ...] = ("cold", "rep1", "rep2")
PROBE_CPT = 3.7422
PROBE_BUDGET = len(PROBE_TARGETS) * len(PROBE_ROLES)


class StopBatch(RuntimeError):
    """A hard bound was hit (requests / consecutive failures)."""


STATE: dict[str, Any] = {
    "requests": 0,
    "failures": 0,
    "consec": 0,
    "started": 0.0,
    "last_end": 0.0,
    "aborted": "",
    "lock_wait_s": None,
    "notes": [],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


u10_corpus = _load("win_u10_corpus", EXP / "cells" / "U10" / "u10_corpus.py")


# --------------------------------------------------------------------------- #
# Wire: one POST == one counted request, no hidden retry
# --------------------------------------------------------------------------- #
def post_once(messages: Iterable[Mapping[str, Any]], *, max_tokens: int = MAX_TOKENS) -> tuple[int, int, int, float, float, int, str]:
    import httpx

    body = {
        "model": MODEL,
        "messages": list(messages),
        "max_tokens": int(max_tokens),
        "temperature": 0.0,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    chunks: list[str] = []
    usage: dict[str, Any] | None = None
    ttft_ms = 0.0
    started = time.perf_counter()
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_S,
                      headers={"Authorization": f"Bearer {API_KEY}"}) as http:
        with http.stream("POST", "/chat/completions", json=body) as response:
            status = response.status_code
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event.get("usage"), Mapping):
                    usage = dict(event["usage"])
                for choice in event.get("choices") or []:
                    piece = (choice.get("delta") or {}).get("content") or ""
                    if piece:
                        if ttft_ms == 0.0:
                            ttft_ms = (time.perf_counter() - started) * 1000.0
                        chunks.append(piece)
    wall_ms = (time.perf_counter() - started) * 1000.0
    if ttft_ms == 0.0:
        ttft_ms = wall_ms
    prompt, cached = normalise_cache(usage)
    completion = int((usage or {}).get("completion_tokens") or 0)
    return prompt, cached, completion, ttft_ms, wall_ms, status, "".join(chunks)


FAKE_SEND: Any = None


def send(messages: Iterable[Mapping[str, Any]]) -> tuple[int, int, int, float, float, int, str]:
    if STATE["requests"] >= STATE["cap"]:
        raise StopBatch(f"request cap reached ({STATE['requests']}/{STATE['cap']})")
    STATE["requests"] += 1
    started = time.perf_counter()
    gap_ms = (started - STATE["last_end"]) * 1000.0 if STATE["last_end"] else None
    STATE["last_gap_ms"] = None if gap_ms is None else round(gap_ms, 3)
    try:
        if FAKE_SEND is not None:
            result = FAKE_SEND(messages)
        else:
            result = post_once(messages)
        STATE["consec"] = 0
    except StopBatch:
        STATE["requests"] -= 1
        raise
    except Exception as exc:  # noqa: BLE001 -- any wire failure is a data point
        STATE["failures"] += 1
        STATE["consec"] += 1
        STATE["last_error"] = f"{type(exc).__name__}: {exc}"
        if STATE["consec"] >= 3:
            raise StopBatch(f"3 consecutive failures: {STATE['last_error']}") from exc
        raise
    finally:
        STATE["last_end"] = time.perf_counter()
    return result


# --------------------------------------------------------------------------- #
# Battery (G3 clone)
# --------------------------------------------------------------------------- #
def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def total_est(chain) -> int:
    return sum(default_est_tokens(n.text) for n in chain)


def load_slice(n: int):
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = (scenario["turns"] * ((n // len(scenario["turns"])) + 1))[:n]
    assert len(turns) == n, (len(turns), n)
    return scenario, turns


def compaction_schedule(preamble: str, turns, budget: int) -> list[int]:
    chain = [StateNode.create(preamble, "invariant")]
    schedule = []
    for turn_no, turn in enumerate(turns, 1):
        chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
        if needs_compaction(chain, budget_tokens=budget, est_tokens=default_est_tokens):
            schedule.append(turn_no)
            chain, _ = compact(chain, CompactionPolicy.SUMMARISE_IN_PLACE, keep_last=KEEP_LAST,
                               summarizer=summarise, est_tokens=default_est_tokens)
    return schedule


def digest_prefix(messages, keep: int = 2) -> str:
    return hashlib.sha256(canonical_bytes(messages[:keep])).hexdigest()


def append_row(row: dict[str, Any]) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def existing_keys(config_id: str) -> set[tuple]:
    keys: set[tuple] = set()
    if not ROWS_PATH.exists():
        return keys
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("config_id") != config_id:
            continue
        if row.get("phase") == "probe":
            keys.add(("probe", row.get("target"), row.get("role")))
        else:
            keys.add(("battery", row.get("depth"), row.get("arm"), row.get("turn")))
    return keys


def row_base(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "unit": "WIN-SGL",
        "stack": STACK,
        "config_id": config["config_id"],
        "page_size": config["page_size"],
        "config_sha256": config["config_sha256"],
        "layer_types": MODEL_CONFIG_LAYER_TYPES,
        "layer_types_sha256": MODEL_LAYER_TYPES_SHA256,
    }


def run_battery(config: dict[str, Any], base: dict[str, Any], done: set[tuple], cap: int) -> dict[str, Any]:
    scenario, _ = load_slice(DEPTHS[0][2])
    _ = scenario
    salts = {str(s["arm"]): make_salt(int(s["seed"])) for s in ARMS}
    counts = {"rows": 0, "requests": 0, "skipped_existing": 0, "warm_retries": 0, "errors": 0}
    for depth_label, budget, n_turns in DEPTHS:
        scenario, turns = load_slice(n_turns)
        preamble = scenario["preamble"]
        schedule = compaction_schedule(preamble, turns, budget)
        print(f"[battery] depth={depth_label} budget={budget} turns={n_turns} schedule={schedule}", flush=True)
        for spec in ARMS:
            arm = str(spec["arm"])
            base_compaction = spec["compaction"]
            salt = salts[arm]
            chain = [StateNode.create(preamble, "invariant")]
            crossed = False
            for turn_no, turn in enumerate(turns, 1):
                chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
                est_before = total_est(chain)
                scheduled = bool(base_compaction is not None and turn_no in schedule)
                if arm == "H" and scheduled:
                    crossed = True
                if arm == "A" and scheduled:
                    compaction_policy = CompactionPolicy.APPEND_NOTE
                elif arm == "H":
                    compaction_policy = CompactionPolicy.APPEND_NOTE if not crossed else CompactionPolicy.SUMMARISE_IN_PLACE
                else:
                    compaction_policy = base_compaction
                event = None
                if scheduled and compaction_policy is not None:
                    chain, event = compact(chain, compaction_policy, keep_last=KEEP_LAST,
                                          summarizer=summarise, est_tokens=default_est_tokens)
                    _ = event
                messages = render(RenderPolicy.NAIVE_APPEND, chain, preamble=preamble, volatile={}, salt=salt)
                if ("battery", depth_label, arm, turn_no) in done:
                    counts["skipped_existing"] += 1
                    continue
                if STATE["requests"] >= cap:
                    STATE["notes"].append(f"battery stopped at {depth_label}/{arm}/t{turn_no}: cap")
                    return counts
                warm_retry = False
                warm1_prompt = None
                warm1_cached = None
                try:
                    prompt, cached, completion, ttft, wall, status, _text = send(messages)
                except StopBatch:
                    raise
                except Exception as exc:  # recorded as a data point, then abort
                    counts["errors"] += 1
                    row = {**base, "phase": "battery", "depth": depth_label, "budget_tokens": budget,
                           "arm": arm, "policy": str(spec["policy"]), "turn": turn_no,
                           "turns_total": n_turns, "salt": salt, "prompt_tokens": None,
                           "cached_tokens": None, "uncached": None, "completion_tokens": None,
                           "ttft_ms": None, "wall_ms": None, "status": 0,
                           "scheduled_compaction": scheduled, "error": STATE.get("last_error"),
                           "request_index": STATE["requests"], "ts_utc": utc_now()}
                    append_row(row)
                    counts["rows"] += 1
                    continue
                else:
                    counts["requests"] += 1
                # G3's warm-retry control (only if the budget still allows it)
                if (cached == 0 and prompt > 0 and prompt % 64 == 0 and turn_no > 1 and not scheduled
                        and STATE["requests"] < cap):
                    warm1_prompt, warm1_cached = prompt, cached
                    try:
                        prompt, cached, completion, ttft, wall, status, _text = send(messages)
                        warm_retry = True
                        counts["warm_retries"] += 1
                        counts["requests"] += 1
                    except (StopBatch, Exception):  # noqa: B014 -- any failure keeps the cold row
                        prompt, cached = warm1_prompt, warm1_cached
                        STATE["notes"].append(f"warm retry skipped at {depth_label}/{arm}/t{turn_no}")
                if turn_no == 1 and cached != 0:
                    STATE["notes"].append(f"{arm}/{depth_label}: cold start cached={cached}")
                uncached = max(0, prompt - cached)
                row = {
                    **base,
                    "phase": "battery",
                    "cell": f"WIN-SGL/{config['config_id']}/{depth_label}/{arm}",
                    "depth": depth_label,
                    "budget_tokens": budget,
                    "arm": arm,
                    "policy": str(spec["policy"]),
                    "turn": turn_no,
                    "turns_total": n_turns,
                    "salt": salt,
                    "prompt_tokens": prompt,
                    "cached_tokens": cached,
                    "uncached": uncached,
                    "completion_tokens": completion,
                    "ttft_ms": round(ttft, 3),
                    "wall_ms": round(wall, 3),
                    "status": status,
                    "scheduled_compaction": scheduled,
                    "est_chain_tokens_before": est_before,
                    "est_chain_tokens_after": total_est(chain),
                    "nodes": len(chain),
                    "messages": len(messages),
                    "chars": sum(len(str(m["content"])) for m in messages),
                    "prefix_sha256": digest_prefix(messages, keep=2),
                    "warm_retry": warm_retry,
                    "warm1_prompt_tokens": warm1_prompt,
                    "warm1_cached_tokens": warm1_cached,
                    "request_index": STATE["requests"],
                    "gap_ms": STATE.get("last_gap_ms"),
                    "ts_utc": utc_now(),
                }
                append_row(row)
                done.add(("battery", depth_label, arm, turn_no))
                counts["rows"] += 1
                if counts["rows"] % 25 == 0:
                    print(f"[battery] {config['config_id']} rows={counts['rows']} req={STATE['requests']} "
                          f"{depth_label}/{arm}/t{turn_no} L={prompt} cached={cached}", flush=True)
    return counts


# --------------------------------------------------------------------------- #
# Grid probe: four targets x three byte-identical sends
# --------------------------------------------------------------------------- #
def run_probe(config: dict[str, Any], base: dict[str, Any], done: set[tuple], cap: int) -> dict[str, Any]:
    counts = {"rows": 0, "requests": 0, "skipped_existing": 0}
    for target in PROBE_TARGETS:
        seed = 700000 + target
        salt = make_salt(seed)
        chars = max(400, int(round(target * PROBE_CPT)))
        text = u10_corpus.prompt_text(u10_corpus.marker_for(salt), chars, 0, 0)
        digest = hashlib.sha256(text.encode()).hexdigest()
        for role in PROBE_ROLES:
            if ("probe", target, role) in done:
                counts["skipped_existing"] += 1
                continue
            if STATE["requests"] >= cap:
                STATE["notes"].append(f"probe stopped before target={target} role={role}: cap")
                return counts
            try:
                prompt, cached, completion, ttft, wall, status, _text = send([{"role": "user", "content": text}])
            except StopBatch:
                raise
            except Exception:  # recorded, then abort
                append_row({**base, "phase": "probe", "target": target, "role": role, "seed": seed,
                            "salt": salt, "chars": len(text), "sha256": digest,
                            "prompt_tokens": None, "cached_tokens": None, "uncached": None,
                            "status": 0, "error": STATE.get("last_error"),
                            "request_index": STATE["requests"], "ts_utc": utc_now()})
                counts["rows"] += 1
                continue
            counts["requests"] += 1
            row = {
                **base,
                "phase": "probe",
                "target": target,
                "role": role,
                "seed": seed,
                "salt": salt,
                "chars": len(text),
                "sha256": digest,
                "prompt_tokens": prompt,
                "cached_tokens": cached,
                "uncached": max(0, prompt - cached),
                "completion_tokens": completion,
                "ttft_ms": round(ttft, 3),
                "wall_ms": round(wall, 3),
                "status": status,
                "request_index": STATE["requests"],
                "gap_ms": STATE.get("last_gap_ms"),
                "ts_utc": utc_now(),
            }
            append_row(row)
            done.add(("probe", target, role))
            counts["rows"] += 1
            print(f"[probe] {config['config_id']} target={target} L={prompt} role={role} cached={cached} "
                  f"(L%64={prompt % 64 if prompt else None})", flush=True)
            time.sleep(PROBE_SLEEP_S)
    return counts


# --------------------------------------------------------------------------- #
# Lock
# --------------------------------------------------------------------------- #
def acquire_lock(path: Path, deadline_s: float):
    handle = path.open("a+", encoding="utf-8")
    started = time.monotonic()
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() - started >= deadline_s:
                handle.close()
                raise TimeoutError(f"occamy lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "WIN-SGL", "pid": os.getpid(), "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, time.monotonic() - started


def release_lock(handle) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "WIN-SGL", "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
def fake_send_factory() -> Any:
    """Offline rehearsal: a deterministic 64-grid server on a warm cache."""

    seen: set[str] = set()

    def _fake(messages: Sequence[Mapping[str, Any]]) -> tuple[int, int, int, float, float, int, str]:
        text = "".join(str(m.get("content")) for m in messages)
        L = max(1, int(round(len(text) / 3.7422)))
        key = hashlib.sha256(text.encode()).hexdigest()
        cached = 64 * ((L - 1) // 64) if key in seen else 0
        seen.add(key)
        return L, cached, 1, 1.0, 2.0, 200, "ok"

    return _fake


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WIN-SGL cell: one pager config, battery + grid probe")
    ap.add_argument("--config-id", help="S1 / S2 / S3")
    ap.add_argument("--page-size", type=int, default=1, help="page_size as reported by /get_server_info")
    ap.add_argument("--cap", type=int, default=900, help="hard live-request cap for this cell")
    ap.add_argument("--server-info", help="path of this config's /get_server_info capture")
    ap.add_argument("--skip-battery", action="store_true")
    ap.add_argument("--skip-probe", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="offline rehearsal with a fake send")
    ap.add_argument("--out", help="cell summary json (default logs/<config>-cell.json)")
    args = ap.parse_args(argv)

    config_id = args.config_id or "DRY"
    STATE["cap"] = int(args.cap)
    out_path = Path(args.out) if args.out else HERE / "logs" / f"{config_id}-cell.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    server_info_path = Path(args.server_info) if args.server_info else None
    config_sha = None
    if server_info_path and server_info_path.exists():
        config_sha = hashlib.sha256(server_info_path.read_bytes()).hexdigest()
    config = {
        "config_id": config_id,
        "page_size": int(args.page_size),
        "config_sha256": config_sha or ("dry" if args.dry_run else None),
    }
    if args.dry_run:
        global FAKE_SEND, ROWS_PATH
        FAKE_SEND = fake_send_factory()
        ROWS_PATH = HERE / "logs" / f"dry-run-{config_id}-rows.jsonl"
        ROWS_PATH.unlink(missing_ok=True)
        ROWS_PATH.touch()

    base = row_base(config)
    done = existing_keys(config_id)
    handle = None
    summary: dict[str, Any] = {"unit": "WIN-SGL", "config_id": config_id, "phase": "cell",
                               "page_size": config["page_size"], "config_sha256": config_sha,
                               "cap": STATE["cap"], "dry_run": bool(args.dry_run)}
    started = time.monotonic()
    try:
        if not args.dry_run:
            handle, waited = acquire_lock(LOCK_PATH, LOCK_DEADLINE_S)
            STATE["lock_wait_s"] = round(waited, 1)
        STATE["started"] = time.time()
        battery = {"rows": 0, "requests": 0}
        probe = {"rows": 0, "requests": 0}
        if not args.skip_battery:
            battery = run_battery(config, base, done, STATE["cap"])
        if not args.skip_probe and STATE["requests"] < STATE["cap"]:
            probe = run_probe(config, base, done, STATE["cap"])
        summary.update({
            "status": "done",
            "battery": battery,
            "probe": probe,
            "requests_live": STATE["requests"],
            "requests_cap": STATE["cap"],
            "failures": STATE["failures"],
            "notes": STATE["notes"],
            "lock_wait_s": STATE.get("lock_wait_s"),
            "elapsed_s": round(time.monotonic() - started, 1),
        })
    except (StopBatch, TimeoutError) as exc:
        summary.update({
            "status": "partial",
            "reason": f"{type(exc).__name__}: {exc}",
            "requests_live": STATE["requests"],
            "requests_cap": STATE["cap"],
            "failures": STATE["failures"],
            "notes": STATE["notes"],
            "lock_wait_s": STATE.get("lock_wait_s"),
            "elapsed_s": round(time.monotonic() - started, 1),
        })
        out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2), flush=True)
        return 2
    finally:
        if handle is not None:
            release_lock(handle)
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
