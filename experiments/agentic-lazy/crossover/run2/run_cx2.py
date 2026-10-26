#!/usr/bin/env python3
"""LAZY-LOAD-CROSSOVER-2 — self-contained crossover runner.

Why a separate file
-------------------
`../run_cx.py` is shared with a concurrent session that relaunches it with a wider
grid (3k/10k/30k, 3 reps) and kills any `run_cx.py` process it finds. Reusing that
entry point means being killed mid-sweep and racing for its files. This script keeps
its own data under `run2/` so the two can never delete each other's evidence.

It still REUSES the killed attempt's work, as instructed: `../cx_corpus.py` (corpora,
unchanged), `../cx_harness.py` (rendering, tasks, checkers), `../runner.py` (HTTP and
usage parsing). Only the top-level loop is new.

Kill-safety (the reason this unit exists)
-----------------------------------------
* `rows.jsonl` is opened ONCE in append mode; every row is `write` + `flush` + `fsync`
  immediately, so a kill loses at most the in-flight request.
* `runs.json` is replaced atomically after every completed run.
* The handoff JSON is updated by the caller after every completed run.

Cache regimes
-------------
COLD  a fresh random nonce is prepended to the system prefix of EVERY request, so no
      prefix can ever be reused. `cached_tokens/prompt_tokens` proves it per row.
WARM  no nonce; the system prefix is byte-identical for every round of the run, so
      round 1 primes the server's prefix cache and rounds 2..n are served from it.
      The steady-prefix design is what a production system prompt actually is.

Neither /flush_cache nor a server restart is used anywhere.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.error
import uuid

HERE = pathlib.Path(__file__).resolve().parent          # .../crossover/run2
CX = HERE.parent                                        # .../crossover
PARENT = CX.parent                                      # .../agentic-lazy
for _p in (str(PARENT), str(CX)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import runner as first_arm      # noqa: E402  reuse post()/usage_fields()/ENDPOINTS
import cx_harness as H          # noqa: E402  reuse render/tasks/checkers

ROWS = HERE / "rows.jsonl"
RUNS = HERE / "runs.json"
ENDPOINTS = first_arm.ENDPOINTS
MAX_COMPLETION_TOKENS = 1024
MAX_ROUNDS = 20

_FH = None


def emit(row: dict) -> None:
    """Append one row and force it to disk before returning."""
    global _FH
    if _FH is None:
        ROWS.parent.mkdir(parents=True, exist_ok=True)
        _FH = ROWS.open("a", encoding="utf-8")
    _FH.write(json.dumps(row, sort_keys=True) + "\n")
    _FH.flush()
    os.fsync(_FH.fileno())


def send(base: str, model: str, messages: list[dict]):
    body = {"model": model, "messages": messages,
            "max_tokens": MAX_COMPLETION_TOKENS, "temperature": 0.0}
    t0 = time.time()
    try:
        payload = first_arm.post(base, body)
    except urllib.error.HTTPError as exc:
        return None, {}, f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}", round(time.time() - t0, 2)
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        return None, {}, f"{type(exc).__name__}: {exc}", round(time.time() - t0, 2)
    return payload, first_arm.usage_fields(payload), None, round(time.time() - t0, 2)


def salted(messages: list[dict], salt: str) -> list[dict]:
    out = [dict(m) for m in messages]
    out[0] = {"role": "system", "content": f"cache-salt: {salt}\n" + (out[0].get("content") or "")}
    return out


def run_one(model, base, arm, n_items, size, cache_state, rep, items, index, task, needed) -> dict:
    messages = H.render_c0(items, task) if arm == "c0" else H.render_l1(items, task)
    protocol = "plain_chat" if arm == "c0" else "text_emulated"

    total_prompt = total_cached = total_completion = 0
    fetch_ids: list[str] = []
    fetched_chars = 0
    rounds = 0
    final_text = None
    error = None
    terminated_by = None
    reporting_seen = False

    while rounds < MAX_ROUNDS:
        rounds += 1
        salt = uuid.uuid4().hex[:16] if cache_state == "cold" else ""
        sent = salted(messages, salt) if salt else [dict(m) for m in messages]
        sent_chars = sum(len(m.get("content") or "") for m in sent)

        prime_prompt = prime_cached = None
        if cache_state == "warm":
            _, pu, perr, _ = send(base, model, sent)
            if perr:
                error = perr
                break
            prime_prompt, prime_cached = pu.get("prompt_tokens"), pu.get("cached_tokens")

        payload, usage, err, elapsed = send(base, model, sent)
        if err:
            error = err
            break

        choice = payload["choices"][0]
        content = (choice.get("message") or {}).get("content")
        prompt_tokens = usage.get("prompt_tokens") or 0
        cached_raw = usage.get("cached_tokens")
        cache_reporting = cached_raw is not None
        reporting_seen = reporting_seen or cache_reporting
        total_prompt += prompt_tokens
        total_cached += (cached_raw or 0)
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
            "nonce": salt or None,
            "salt_scope": "per_request" if cache_state == "cold" else "steady_prefix",
            "sent_chars": sent_chars,
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached_raw,          # None = instrument blind, NOT a miss
            "cache_reporting": cache_reporting,
            "prime_prompt_tokens": prime_prompt,
            "prime_cached_tokens": prime_cached,
            "completion_tokens": usage.get("completion_tokens"),
            "finish_reason": choice.get("finish_reason"),
            "emulated_action": action,
            "fetched_item": item_id,
            "content": content,
            "error": None,
            "elapsed_s": elapsed,
        })

        if arm == "c0":
            final_text, terminated_by = content, "final_text"
            break
        if action == "fetch":
            iid = (item_id or "").strip()
            hit = iid in index
            fetch_ids.append(iid)
            if hit:
                fetched_chars += len(index[iid]["body"])
                reply = H.FETCH_REPLY.format(iid=iid, body=index[iid]["body"])
            else:
                reply = H.FETCH_UNKNOWN.format(iid=iid)
            messages = messages + [{"role": "assistant", "content": content},
                                   {"role": "user", "content": reply}]
            continue
        if action == "answer":
            messages = messages + [{"role": "assistant", "content": content},
                                   {"role": "user", "content": H.ANSWER_NUDGE}]
            continue
        final_text, terminated_by = content, "final_text_without_answer_token"
        break

    if final_text is None and error is None:
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
        "fetched_body_chars": fetched_chars,
        "fetch_count": len(fetch_ids), "fetch_ids": fetch_ids,
        "fetch_hits": sum(1 for i in fetch_ids if i in index),
        "final_text": final_text, "error": error, "terminated_by": terminated_by,
        **verdict,
    }


def save_runs(summaries: list[dict]) -> None:
    tmp = RUNS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, RUNS)


def main() -> int:
    # The card's grid: 3k and 30k; 2-of-12 at both, 6-of-30 at 30k only; 1 rep.
    cells = [(12, 3000), (12, 30000), (30, 30000)]
    reps = 1
    if "--dry-run" in sys.argv:
        print("DRY RUN -- nothing is sent")
        for n, s in cells:
            items = H.load_items(n, s)
            c0, l1 = H.render_c0(items, H.task_for(n)), H.render_l1(items, H.task_for(n))
            print(f"{n:02d}_{s:05d}: items={len(items)} "
                  f"bodies={sum(len(i['body']) for i in items)} "
                  f"c0_chars={sum(len(m['content']) for m in c0)} "
                  f"l1_chars={sum(len(m['content']) for m in l1)} "
                  f"needed={len(H.needed_for(n))}")
        print(f"plan: {len(cells) * 2 * 2 * 2 * reps} runs "
              f"({len(list(ENDPOINTS))} models x {len(cells)} cells x 2 arms x 2 cache x {reps} rep)")
        return 0

    started = time.time()
    for n, s in cells:
        items = H.load_items(n, s)
        index = H.item_index(items)
        task, needed = H.task_for(n), H.needed_for(n)
        for arm in ("c0", "l1"):
            for cs in ("cold", "warm"):
                for model in ENDPOINTS:
                    summaries = (json.loads(RUNS.read_text()) if RUNS.exists() else [])
                    tag = f"{model} n={n} size={s} {arm} {cs} rep{reps}"
                    print(f"[{round(time.time() - started, 1):6.1f}s] {tag}", flush=True)
                    r = run_one(model, ENDPOINTS[model], arm, n, s, cs, reps,
                                items, index, task, needed)
                    summaries.append(r)
                    save_runs(summaries)
                    print(f"        correct={r['correct']} facts={r['facts_present']}/"
                          f"{r['facts_required']} rounds={r['rounds']} "
                          f"prompt={r['prompt_tokens']} cached={r['cached_tokens']} "
                          f"fetch={r['fetch_count']} err={r['error']}", flush=True)
    print(f"\nrows: {sum(1 for _ in ROWS.open())} runs: "
          f"{len(json.loads(RUNS.read_text()))} elapsed: {round(time.time() - started, 1)}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
