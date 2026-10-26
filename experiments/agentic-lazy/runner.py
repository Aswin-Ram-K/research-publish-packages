#!/usr/bin/env python3
"""Measure the two arms against two models, one JSONL row per request.

Design notes that keep the comparison honest
--------------------------------------------
* A request is one HTTP round trip. A *run* is all requests needed to answer one
  task: C0 always takes exactly 1 request; L1 takes 1 + one per fetch round.
* Rows are per request, so the tool-loop's extra round trips are countable rather
  than hidden. Savings are computed over the whole run.
* The completion budget is generous and identical across arms and models,
  because both servers emit hidden reasoning that consumes the budget before any
  visible content. A truncated run would be scored as wrong for a reason that has
  nothing to do with the arm.
* Temperature 0. Reps differ only by the server's non-determinism, which is the
  noise we want measured, not introduced.

Protocol per request: POST {base}/chat/completions with a raw OpenAI body.
The existing repo client (src/resextract/llm/occamy.py) always sends
chat_template_kwargs, which the :8014 server rejects, so the two servers are
driven through one minimal body builder here.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

import harness

ROOT = pathlib.Path(__file__).resolve().parent
ROWS = ROOT / "rows.jsonl"

ENDPOINTS = {
    "occamy-1.0": "http://192.168.2.168:8012/v1",
    "qwen3.5-9b": "http://192.168.2.168:8014/v1",
}

# :8014 has no tool-call parser (400: "auto" tool choice requires
# --enable-auto-tool-choice and --tool-call-parser to be set) and must not be
# restarted. On that server the L1 arm therefore uses a text-emulated fetch
# protocol; on :8012 it uses native function calling. Both are recorded as arm
# "l1" and distinguished by the "protocol" column, never silently merged.
NO_TOOL_PARSER = {"qwen3.5-9b"}

MAX_COMPLETION_TOKENS = 2048   # generous: hidden reasoning is billed here
MAX_FETCH_ROUNDS = 8           # a run needing more is not lazy, it is a search
TIMEOUT_S = 900


def post(base: str, body: dict) -> dict:
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def usage_fields(payload: dict) -> dict:
    u = payload.get("usage") or {}
    details = u.get("prompt_tokens_details") or {}
    return {
        "prompt_tokens": u.get("prompt_tokens"),
        "cached_tokens": details.get("cached_tokens"),
        "completion_tokens": u.get("completion_tokens"),
        "reasoning_tokens": u.get("reasoning_tokens"),
    }


def emit(row: dict) -> None:
    with ROWS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def run_one(model: str, arm: str, rep: int, items: list[dict],
            index: dict[str, dict], base: str) -> dict:
    """Execute one run; append a row per request; return the run summary."""
    emulated = arm == "l1" and model in NO_TOOL_PARSER
    protocol = ("plain_chat" if arm == "c0"
                else "text_emulated" if emulated else "native_function_calling")
    messages = (harness.render_c0(items) if arm == "c0"
                else harness.render_l1(items, emulated=emulated))
    fetch_calls: list[dict] = []
    fetched_tokens = 0
    total_prompt = total_cached = 0
    rounds = 0
    final_text = None
    error = None

    while True:
        rounds += 1
        body: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": MAX_COMPLETION_TOKENS,
            "temperature": 0.0,
        }
        if arm == "l1" and not emulated:
            body["tools"] = [harness.FETCH_TOOL]
            body["tool_choice"] = "auto"

        t0 = time.time()
        try:
            payload = post(base, body)
        except urllib.error.HTTPError as exc:
            error = f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:400]}"
            break
        except Exception as exc:  # noqa: BLE001 - recorded, not raised
            error = f"{type(exc).__name__}: {exc}"
            break
        elapsed = round(time.time() - t0, 2)

        choice = payload["choices"][0]
        msg = choice["message"]
        u = usage_fields(payload)
        total_prompt += u["prompt_tokens"] or 0
        total_cached += u["cached_tokens"] or 0

        calls = msg.get("tool_calls") or []
        served = []
        emulated_action = None
        if emulated:
            # one textual instruction per request; no native tool_calls exist
            emulated_action, fetch_id = harness.parse_emulated(msg.get("content"))
            if emulated_action == "fetch":
                calls = [{"id": f"emulated-{rounds}", "type": "function",
                          "function": {"name": "get_library_item",
                                       "arguments": json.dumps({"item_id": fetch_id})}}]
        for call in calls:
            name = call["function"]["name"]
            raw_args = call["function"]["arguments"]
            try:
                item_id = json.loads(raw_args).get("item_id")
            except Exception:  # noqa: BLE001
                item_id = None
            item_id = (item_id or "").strip()
            hit = item_id in index
            known = index[item_id]["body"] if hit else ""
            if hit:
                fetched_tokens += len(known)
            fetch_calls.append({"item_id": item_id, "known": hit,
                                "body_chars": len(known)})
            served.append({"call_id": call["id"], "name": name,
                           "item_id": item_id, "known": hit})

        emit({
            "model": model, "arm": arm, "rep": rep, "round": rounds,
            "request_index": len(fetch_calls) if arm == "l1" else 0,
            "prompt_chars": sum(len(m.get("content") or "") for m in messages),
            **u,
            "finish_reason": choice.get("finish_reason"),
            "protocol": protocol,
            "emulated_action": emulated_action,
            "tool_calls": served,
            "completion_text": msg.get("content"),
            "error": None,
            "elapsed_s": elapsed,
        })

        if emulated and emulated_action == "answer":
            # copy the model's own ANSWER out, then demand the final formatted answer
            messages.append({"role": "assistant", "content": msg.get("content")})
            messages.append({"role": "user", "content": harness.EMULATED_ANSWER})
            continue
        if not calls:
            final_text = msg.get("content")
            break
        if rounds > MAX_FETCH_ROUNDS:
            error = "max_fetch_rounds_exceeded"
            break

        # Append the tool exchange and go again.
        messages.append({
            "role": "assistant",
            "content": msg.get("content"),
            "tool_calls": [
                {"id": c["id"], "type": "function",
                 "function": {"name": c["function"]["name"],
                              "arguments": c["function"]["arguments"]}}
                for c in calls
            ],
        })
        for s in served:
            messages.append({
                "role": "tool",
                "tool_call_id": s["call_id"],
                "content": index[s["item_id"]]["body"] if s["known"]
                else f"ERROR: no item with id {s['item_id']!r} in the library.",
            })

    verdict = harness.check_answer(final_text)
    ids = [c["item_id"] for c in fetch_calls]
    return {
        "model": model, "arm": arm, "rep": rep, "protocol": protocol,
        "rounds": rounds,
        "prompt_tokens": total_prompt,
        "cached_tokens": total_cached,
        "fetched_body_chars": fetched_tokens,
        "fetch_count": len(fetch_calls),
        "fetch_ids": ids,
        "fetch_hits": sum(1 for c in fetch_calls if c["known"]),
        "final_text": final_text,
        "error": error,
        **verdict,
        "required_items_fetched": sorted(set(i for i in ids
                                             if i in harness.REQUIRED_ITEMS)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and the renderings; send nothing")
    ap.add_argument("--models", default=",".join(ENDPOINTS))
    ap.add_argument("--arms", default="c0,l1")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--fresh", action="store_true",
                    help="truncate rows.jsonl/runs.json instead of appending")
    args = ap.parse_args()

    items = harness.load_items()
    index = harness.item_index(items)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    if args.dry_run:
        c0, l1 = harness.render_c0(items), harness.render_l1(items)
        print("DRY RUN -- no requests will be sent")
        print(f"corpus: {len(items)} items, "
              f"{sum(len(i['body']) for i in items)} chars")
        print(f"c0 system chars: {len(c0[0]['content'])}")
        print(f"l1 system chars: {len(l1[0]['content'])}")
        print(f"task chars     : {len(harness.TASK)}")
        plan = [(m, a, r) for m in models for a in arms
                for r in range(1, args.reps + 1)]
        print(f"plan: {len(plan)} runs")
        for m, a, r in plan:
            print(f"  run {m:12s} {a:3s} rep{r}")
        print("\n--- l1 system prompt (complete) ---")
        print(l1[0]["content"])
        print("--- task (complete) ---")
        print(harness.TASK)
        return 0

    if args.fresh:
        ROWS.unlink(missing_ok=True)
    summaries = json.loads((ROOT / "runs.json").read_text()) if (ROOT / "runs.json").exists() and not args.fresh else []
    for model in models:
        base = ENDPOINTS[model]
        for arm in arms:
            for rep in range(1, args.reps + 1):
                print(f"[run] {model} {arm} rep{rep}", flush=True)
                s = run_one(model, arm, rep, items, index, base)
                summaries.append(s)
                print(f"      correct={s['correct']} rounds={s['rounds']} "
                      f"prompt={s['prompt_tokens']} fetch={s['fetch_count']} "
                      f"err={s['error']}", flush=True)
                (ROOT / "runs.json").write_text(
                    json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    print(f"\nrows: {sum(1 for _ in ROWS.open())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
