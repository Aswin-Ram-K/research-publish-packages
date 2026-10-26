#!/usr/bin/env python3
"""Crossover sweep runner: corpus size x needed fraction x 2 arms x 2 cache
states x 2 models x 1 rep. One JSONL row per request, flushed to disk on write.

Cache regimes, without touching either server
---------------------------------------------
COLD  A unique random nonce is prepended to the system prefix of EVERY request,
      so the prefix can never be cache-matched. The nonce is recorded per row, and
      `cached_tokens / prompt_tokens` proves the regime instead of assuming it.
WARM  The identical request is sent a second time and the SECOND response's
      `prompt_tokens_details.cached_tokens` is recorded. The priming response is
      recorded too (`prime_*`), so the warm pair is visible rather than implied.
      A per-run nonce keeps one run's warm pair isolated from other runs; the nonce
      is stable across that run's rounds, which is what a stable system prefix does
      in production.

Neither /flush_cache nor a restart is used anywhere in this file.

Fetch protocol
--------------
Both models use the text-emulated `FETCH <id>` / `ANSWER` protocol, so the native
tool-calling vs text-emulation confound the first arm disclosed is gone. A fetched
body arrives as an ordinary user message, never as a tool message and never as a
tool_call, so neither server's tool parser is involved on either model.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import os
import pathlib
import sys
import time
import urllib.error
import uuid

ROOT = pathlib.Path(__file__).resolve().parent
PARENT = ROOT.parent
sys.path.insert(0, str(PARENT))

import runner as first_arm          # noqa: E402  reuse post()/usage_fields()/ENDPOINTS
import cx_harness as H              # noqa: E402

ROWS = ROOT / "rows.jsonl"
RUNS = ROOT / "runs.json"

ENDPOINTS = first_arm.ENDPOINTS     # same two servers, same URLs
MAX_COMPLETION_TOKENS = 1024        # 4x the 269 tokens the first arm observed
MAX_ROUNDS = 20
TIMEOUT_S = 900


_ROWS_FH = None


def emit(row: dict) -> None:
    """Append one row and force it to disk.

    A kill mid-sweep must leave every completed request on disk: the file is kept
    open in append mode and both flush() and fsync() run after every single row, so
    no row ever lives only in a process buffer.
    """
    global _ROWS_FH
    if _ROWS_FH is None:
        ROWS.parent.mkdir(parents=True, exist_ok=True)
        _ROWS_FH = ROWS.open("a", encoding="utf-8")
    _ROWS_FH.write(json.dumps(row, sort_keys=True) + "\n")
    _ROWS_FH.flush()
    os.fsync(_ROWS_FH.fileno())


def with_salt(messages: list[dict], salt: str) -> list[dict]:
    """Salt only the system prefix; the rest of the conversation is untouched."""
    out = [dict(m) for m in messages]
    out[0] = {"role": "system",
              "content": f"cache-salt: {salt}\n" + (out[0].get("content") or "")}
    return out


def send(base: str, model: str, messages: list[dict]) -> tuple[dict | None, dict, str | None, float]:
    """One request. Returns (payload, usage, error, elapsed)."""
    body = {"model": model, "messages": messages,
            "max_tokens": MAX_COMPLETION_TOKENS, "temperature": 0.0}
    t0 = time.time()
    try:
        payload = first_arm.post(base, body)
    except urllib.error.HTTPError as exc:
        return None, {}, f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}", round(time.time() - t0, 2)
    except Exception as exc:  # noqa: BLE001 - recorded, not raised
        return None, {}, f"{type(exc).__name__}: {exc}", round(time.time() - t0, 2)
    return payload, first_arm.usage_fields(payload), None, round(time.time() - t0, 2)


def run_one(model: str, base: str, arm: str, n_items: int, size: int,
            cache_state: str, rep: int, items: list[dict], index: dict[str, dict],
            task: str, needed: list[str]) -> dict:
    """One run: C0 = 1 request, L1 = 1 + one request per fetch round."""
    messages = (H.render_c0(items, task) if arm == "c0"
                else H.render_l1(items, task))
    protocol = "plain_chat" if arm == "c0" else "text_emulated"

    total_prompt = total_cached = total_completion = 0
    fetch_ids: list[str] = []
    fetched_body_chars = 0
    rounds = 0
    final_text = None
    error = None
    terminated_by = None
    reporting_seen = False

    while rounds < MAX_ROUNDS:
        rounds += 1
        # COLD: a fresh nonce per REQUEST, so no prefix can ever be reused.
        # WARM: NO nonce at all -- the system prefix is byte-identical across every
        #       round of this run (round 1 primes the server's prefix cache, rounds
        #       2..n are served from it). A per-run nonce would have isolated each
        #       run from every other run, which models a stable system prompt
        #       correctly but must be recorded, so it is: salt_scope=steady_prefix.
        salt = uuid.uuid4().hex[:16] if cache_state == "cold" else ""
        sent = with_salt(messages, salt)
        sent_chars = sum(len(m.get("content") or "") for m in sent)

        prime_prompt = prime_cached = None
        prime_reporting = None
        if cache_state == "warm":
            _, prime_usage, perr, _ = send(base, model, sent)
            if perr:
                error = perr
                break
            prime_prompt = prime_usage.get("prompt_tokens")
            prime_cached = prime_usage.get("cached_tokens")
            prime_reporting = prime_cached is not None

        payload, usage, err, elapsed = send(base, model, sent)
        if err:
            error = err
            break

        choice = payload["choices"][0]
        msg = choice.get("message") or {}
        content = msg.get("content")
        prompt_tokens = usage.get("prompt_tokens") or 0
        # None means the server returned prompt_tokens_details: null -- the cache
        # instrument is BLIND, which is not the same as a miss. Never coerce to 0.
        cached_raw = usage.get("cached_tokens")
        cache_reporting = cached_raw is not None
        reporting_seen = reporting_seen or cache_reporting
        cached_tokens = cached_raw if cache_reporting else None
        total_prompt += prompt_tokens
        total_cached += (cached_tokens or 0)
        total_completion += usage.get("completion_tokens") or 0

        action, item_id = (None, None)
        if arm == "l1":
            action, item_id = H.h.parse_emulated(content)

        emit({
            "model": model, "arm": arm, "protocol": protocol,
            "fetch_protocol": ("text_emulated" if arm == "l1" else None),
            "n_items": n_items, "size": size,
            "needed_fraction": round(len(needed) / n_items, 4),
            "cache_state": cache_state, "rep": rep, "round": rounds,
            "nonce": salt, "salt_scope": ("per_request" if cache_state == "cold"
                                          else "steady_prefix"),
            "sent_chars": sent_chars,
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached_tokens,
            "cache_reporting": cache_reporting,
            "cache_ratio": (round(cached_tokens / prompt_tokens, 4)
                            if (cache_reporting and prompt_tokens) else None),
            "prime_prompt_tokens": prime_prompt,
            "prime_cached_tokens": prime_cached,
            "prime_cache_reporting": prime_reporting,
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": usage.get("reasoning_tokens"),
            "finish_reason": choice.get("finish_reason"),
            "emulated_action": action,
            "fetched_item": item_id,
            "content": content,
            "error": None,
            "elapsed_s": elapsed,
        })

        if arm == "c0":
            final_text = content
            terminated_by = "final_text"
            break

        if action == "fetch":
            iid = (item_id or "").strip()
            hit = iid in index
            body = index[iid]["body"] if hit else None
            fetch_ids.append(iid)
            if hit:
                fetched_body_chars += len(body)
                reply = H.FETCH_REPLY.format(iid=iid, body=body)
            else:
                reply = H.FETCH_UNKNOWN.format(iid=iid)
            messages = messages + [
                {"role": "assistant", "content": content},
                {"role": "user", "content": reply},
            ]
            continue

        if action == "answer":
            messages = messages + [
                {"role": "assistant", "content": content},
                {"role": "user", "content": H.ANSWER_NUDGE},
            ]
            continue

        # no control line: treat what it wrote as its final answer
        final_text = content
        terminated_by = "final_text_without_answer_token"
        break

    if rounds >= MAX_ROUNDS and final_text is None and error is None:
        error = "max_rounds_exceeded"

    verdict = H.check_answer(final_text, n_items)
    return {
        "model": model, "arm": arm, "protocol": protocol,
        "fetch_protocol": ("text_emulated" if arm == "l1" else None),
        "n_items": n_items, "size": size,
        "needed_fraction": round(len(needed) / n_items, 4),
        "cache_state": cache_state, "rep": rep,
        "rounds": rounds, "requests": rounds,
        "prompt_tokens": total_prompt, "cached_tokens": total_cached,
        "completion_tokens": total_completion,
        "cache_reporting": reporting_seen,
        "cache_ratio": round(total_cached / total_prompt, 4) if total_prompt else None,
        "fetched_body_chars": fetched_body_chars,
        "fetch_count": len(fetch_ids), "fetch_ids": fetch_ids,
        "fetch_hits": sum(1 for i in fetch_ids if i in index),
        "needed_items_fetched": sorted(set(i for i in fetch_ids if i in needed)),
        "all_needed_fetched": all(i in set(fetch_ids) for i in needed),
        "final_text": final_text, "error": error, "terminated_by": terminated_by,
        **verdict,
    }


def plan(args) -> list[dict]:
    cells = []
    for n in args.counts:
        for s in args.sizes:
            for arm in args.arms:
                for cs in args.cache:
                    for model in args.models:
                        for rep in range(1, args.reps + 1):
                            cells.append({"n_items": n, "size": s, "arm": arm,
                                          "cache_state": cs, "model": model,
                                          "rep": rep})
    return cells


def cell_key(r: dict) -> str:
    return (f"{r['model']}|{r['n_items']}|{r['size']}|{r['arm']}|"
            f"{r['cache_state']}|{r['rep']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(ENDPOINTS))
    ap.add_argument("--sizes", default="3000,30000")
    ap.add_argument("--counts", default="12,30")
    ap.add_argument("--arms", default="c0,l1")
    ap.add_argument("--cache", default="cold,warm")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tag", default="",
                    help="suffix for rows/runs/lock, so a concurrent duplicate "
                         "unit sharing this directory cannot clobber this run")
    ap.add_argument("--resume", action="store_true",
                    help="skip runs already present in runs.json")
    args = ap.parse_args()
    args.models = [m.strip() for m in args.models.split(",") if m.strip()]
    args.sizes = [int(x) for x in args.sizes.split(",") if x.strip()]
    args.counts = [int(x) for x in args.counts.split(",") if x.strip()]
    args.arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    args.cache = [c.strip() for c in args.cache.split(",") if c.strip()]

    global ROWS, RUNS
    ROWS = ROOT / f"rows{args.tag}.jsonl"
    RUNS = ROOT / f"runs{args.tag}.json"

    # A duplicate incarnation of this card must not clobber rows.jsonl/runs.json.
    lock = (ROOT / f".run{args.tag}.lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(f"refusing to start: another run_cx.py already holds .run{args.tag}.lock",
              file=sys.stderr)
        return 3
    lock.write(str(os.getpid()))
    lock.flush()

    todo = plan(args)
    if args.dry_run:
        print("DRY RUN -- nothing is sent")
        for n in args.counts:
            for s in args.sizes:
                items = H.load_items(n, s)
                task = H.task_for(n)
                c0 = H.render_c0(items, task)
                l1 = H.render_l1(items, task)
                print(f"cell {n:02d}_{s:05d}: items={len(items)} "
                      f"bodies={sum(len(i['body']) for i in items)} "
                      f"c0_chars={sum(len(m['content']) for m in c0)} "
                      f"l1_chars={sum(len(m['content']) for m in l1)} "
                      f"needed={len(H.needed_for(n))} task_chars={len(task)}")
        print(f"plan: {len(todo)} runs "
              f"({len(args.models)} models x {len(args.counts)} counts x "
              f"{len(args.sizes)} sizes x {len(args.arms)} arms x "
              f"{len(args.cache)} cache states x {args.reps} reps)")
        print("\n--- task for the 30-item fraction (complete) ---")
        print(H.task_for(30))
        print("\n--- l1 system prompt, 12 items @ 3000 chars (complete) ---")
        print(H.render_l1(H.load_items(12, 3000), H.task_for(12))[0]["content"])
        return 0

    if args.fresh:
        ROWS.unlink(missing_ok=True)
        RUNS.unlink(missing_ok=True)
    summaries = (json.loads(RUNS.read_text(encoding="utf-8"))
                 if RUNS.exists() and not args.fresh else [])
    done = {cell_key(r) for r in summaries} if args.resume else set()
    if args.resume:
        todo = [t for t in todo if cell_key(t) not in done]
        print(f"resume: {len(done)} runs already present, {len(todo)} to go",
              flush=True)

    t_start = time.time()
    for i, cell in enumerate(todo, 1):
        n, s = cell["n_items"], cell["size"]
        items = H.load_items(n, s)
        index = H.item_index(items) if hasattr(H, "item_index") else {it["id"]: it for it in items}
        task, needed = H.task_for(n), H.needed_for(n)
        print(f"[{i}/{len(todo)}] {cell['model']} n={n} size={s} {cell['arm']} "
              f"{cell['cache_state']} rep{cell['rep']}", flush=True)
        summary = run_one(cell["model"], ENDPOINTS[cell["model"]], cell["arm"],
                          n, s, cell["cache_state"], cell["rep"], items, index,
                          task, needed)
        summary["_t"] = round(time.time() - t_start, 1)
        summaries.append(summary)
        tmp = RUNS.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, RUNS)          # atomic: a kill never leaves half a file
        print(f"      correct={summary['correct']} "
              f"facts={summary['facts_present']}/{summary['facts_required']} "
              f"rounds={summary['rounds']} prompt={summary['prompt_tokens']} "
              f"cached={summary['cached_tokens']} "
              f"fetch={summary['fetch_count']} err={summary['error']}", flush=True)

    print(f"\nrows: {sum(1 for _ in ROWS.open())}  runs: {len(summaries)}  "
          f"elapsed: {round(time.time() - t_start, 1)}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
