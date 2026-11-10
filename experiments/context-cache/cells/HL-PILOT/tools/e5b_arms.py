#!/usr/bin/env python3
"""Step 4 (second instrument) — the same three arms, an instrument that can answer.

Why a second run. E4 (``envelopes/E4.json``) failed its own instrument, not its
arms: every arm scored 1/8 and 0/7 checks, and the rows show why.
``enable_thinking`` was false and ``max_tokens`` was 160, so a reasoning model
answered arithmetic checkpoints (``predict_billed(128,10,64)``) without
reasoning — the probe recorded afterwards answers the same question correctly
once reasoning is allowed (187 reasoning tokens, then ``(138, True)``). Half the
remaining checks ask the assistant to *run* pytest and report exit codes, which
a text-only replay cannot do at all. So E4 measured my generation config, not the
context policy, and its quality numbers are void.

E5 fixes the instrument and nothing else:

  * full source files are embedded in the stable prefix (E4 embedded only the
    pointed line ranges, so some checkpoint values were underivable from the
    prompt by construction);
  * thinking is enabled and ``max_tokens`` is 1200; the answer is the returned
    content, with reasoning tokens reported separately by the engine;
  * checks are scored per check and split by applicability: a checkpoint fact is
    answerable in replay, a "run the tests and report exit codes" check is
    pre-registered as impossible for a text-only replay and reported as such for
    every arm alike;
  * the arms themselves are byte-identical in construction to E4.

That is an instrument repair made before the run, applied to all arms equally,
and recorded rather than quietly applied. Nothing about the arms changed.

Budget: 3 arms x (40 + 48) turns = 264 calls, cap 320.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
WT = Path(__file__).resolve().parents[5]
TOOLS = CELL / "tools"
sys.path.insert(0, str(TOOLS))

import httpx  # noqa: E402
from adapter import Adapter  # noqa: E402
from e4_arms import (  # noqa: E402
    ARMS, MASK_AFTER, TASKS, eval_checks, first_line, load_fixture, normalise,
    render_history, sha8, stable_prefix, FIXTURES,
)

# DEFECT FIX 2026-11-04: the first launch iterated every fixture (its envelope even listed
# both) and spent 8 calls re-running LR-04 into rows/e5b.jsonl. Those rows are quarantined in
# rows/e5b-lr04-duplicates.jsonl. This runner is held-out only.
TASKS = ("LR-01",)

LOCK = WT / "experiments/context-cache/.occamy.lock"
BASE = "http://192.168.2.168:8012"
ENVELOPE = CELL / "envelopes/E5B.json"
ROWS = CELL / "rows/e5b.jsonl"
ANALYSIS = CELL / "notes/e5b-analysis.json"
MAX_TOKENS = 1200
USER_ASK = "Output ONLY the answer line. No preamble, no deliberation."


def full_sources(fx: dict) -> tuple[str, list[dict]]:
    """Whole files, pinned by digest. The pointer becomes an annotation."""
    parts, meta = [], []
    for src in fx["sources"]:
        path = WT / src["path"]
        digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        body = path.read_text()
        ok = digest == src["sha256"]
        meta.append({"id": src["id"], "path": src["path"],
                     "pointer": src.get("pointer"), "digest_ok": ok,
                     "digest": digest, "declared": src["sha256"],
                     "lines": len(body.splitlines()), "embedded": "full file"})
        parts.append(
            f"#### source {src['id']} | {src['path']} (focus {src.get('pointer') or 'whole file'}) "
            f"| {digest}\n{body}\n")
    # one file may be listed twice with different focus ranges; keep one copy
    seen, unique = set(), []
    for part in parts:
        key = part.split("\n", 1)[1][:200]
        if key not in seen:
            seen.add(key)
            unique.append(part)
    return "\n".join(unique), meta


def instruction_kind(fx: dict, turn: int) -> str:
    for t in fx["turns"]:
        if t["turn"] == turn:
            low = t["instruction"].lower()
            if t["kind"] == "verify" or "run the acceptance" in low or "exit code" in low:
                return "requires-execution"
            return "answerable-in-replay"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args()
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]

    fixtures = {t: load_fixture(t) for t in TASKS}
    blocks = {t: full_sources(fixtures[t]) for t in TASKS}
    prefixes = {t: stable_prefix(fixtures[t], blocks[t][0]) for t in TASKS}
    n_calls = sum(len(fixtures[t]["turns"]) for t in tasks) * len(ARMS)

    if args.analyze:
        return analyse()

    if args.dry_run:
        for t in TASKS:
            print(t, "turns", len(fixtures[t]["turns"]),
                  "prefix chars", len(prefixes[t]),
                  "all digests ok", all(m["digest_ok"] for m in blocks[t][1]),
                  "sources", [m["id"] for m in blocks[t][1]])
        print("model calls:", n_calls)
        return 0

    if args.plan:
        fp = json.loads((CELL / "envelopes/fingerprints.json").read_text())
        inspect = json.loads((CELL / "notes/container-inspect-2026-11-04.json").read_text())[0]
        env = {
            "schema": "consonance.run/1",
            "run_id": "HL-E5B-2026-11-04",
            "arm": "A,B,C-CONTEXT-DESIGN-V2B",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=WT,
                                      capture_output=True, text=True).stdout.strip(),
            "fixture_sha": {t: "sha256:" + fixtures[t]["_sha256"] for t in TASKS},
            "engine_image_digest": inspect["Image"],
            "engine_flags": inspect["Args"],
            "hardware": "gx10 / GB10, 128 GB unified",
            "quantization": "nvfp4 (modelopt_fp4)",
            "budgets": {"max_calls": 320, "max_cost_usd": 0},
            "generation": {"max_tokens": MAX_TOKENS, "temperature": 0.0, "seed": 7,
                           "thinking": True},
            "controls": {
                "stable_prefix_identity": "prefix sha256 recorded in every row; identical across arms",
                "same_turn_stream": True,
                "same_verifier": "one evaluator for all arms",
                "applicability_split": "checkpoint facts answerable-in-replay; "
                                       "'run the tests / report exit codes' pre-registered unavailable",
                "mismatched_tokenizer": "UNAVAILABLE",
            },
            "fingerprints": {k: fp[k] for k in (
                "model_fingerprint", "tokenizer_fingerprint",
                "renderer_fingerprint", "engine_fingerprint")},
            "tasks": TASKS,
            "arms": {"A": "append-only verbatim transcript",
                     "B": "typed append-only records with sha8 references",
                     "C": f"B plus masking of work turns older than {MASK_AFTER}"},
            "applicability": {
                t: {str(c.get("turn")): instruction_kind(fixtures[t], c.get("turn"))
                    for c in fixtures[t]["acceptance"]["checks"] if c.get("turn")}
                for t in TASKS},
            "supersedes": {"run_id": "HL-E4-2026-11-04", "envelope": "envelopes/E4.json",
                           "defects": ["thinking disabled + max_tokens 160 produced wrong "
                                       "arithmetic in every arm; probe shows 187 reasoning tokens "
                                       "then the correct (138, True)",
                                       "pointed line ranges only, so some checkpoint values were "
                                       "underivable from the prompt",
                                       "verify-turn checks cannot be answered without executing pytest"]},
            "order": list(TASKS), "arm_order": list(ARMS), "flushed_between_arms": True,
            "call_plan_count": n_calls,
            "sources": {t: blocks[t][1] for t in TASKS},
            "supersedes": {"run_id": "HL-E5-2026-11-04", "task": "LR-01",
                           "defects": ["the first LR-01 call spent all 1200 tokens reasoning and "
                                       "returned empty content (finish_reason=length), so every "
                                       "answer would have been blank",
                                       "two probe calls showed the ask string is what tips it: "
                                       "'Answer in one line. Do not deliberate.' still exhausted the "
                                       "budget; 'Output ONLY the answer line. No preamble, no "
                                       "deliberation.' returned content in 28 s"]},
            "user_ask": USER_ASK,
            "notes": ("Hypothesis: dense typed records (B) preserve every answerable checkpoint and "
                      "negative constraint while cutting cache-adjusted cost per verified success by "
                      ">= 10 %. Falsifier: any check or constraint worse than A, or no uncached-work "
                      "reduction. cached_tokens absent is null, never 0."),
        }
        ENVELOPE.write_text(json.dumps(env, indent=2) + "\n")
        print("frozen", ENVELOPE, "calls", n_calls)
        return 0

    env = json.loads(ENVELOPE.read_text())
    if env.get("retrospective"):
        raise SystemExit("retrospective envelope")
    cap = env["budgets"]["max_calls"]
    if n_calls > cap:
        raise SystemExit(f"{n_calls} exceeds cap {cap}")
    prefix_sha = {t: sha8(prefixes[t]) for t in TASKS}

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as lock:
        t0 = time.time()
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() - t0 > 300:
                    raise SystemExit("lock not free after 300s")
                time.sleep(1)
        print(f"lock acquired after {time.time() - t0:.1f}s")

        ROWS.parent.mkdir(parents=True, exist_ok=True)
        done = {}
        if ROWS.exists():
            for line in ROWS.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                key = (r.get("task"), r.get("arm"))
                done.setdefault(key, set()).add(r.get("turn"))
        fh = ROWS.open("a")
        adapter = Adapter()
        step_no = 0
        per_arm = {}

        for task in TASKS:
            fx = fixtures[task]
            turns = [dict(t) for t in fx["turns"]]
            for arm in ARMS:
                need = {t["turn"] for t in turns}
                if done.get((task, arm), set()) >= need:
                    print(f"{task} {arm}: complete on disk, skipping")
                    continue
                if done.get((task, arm)):
                    raise SystemExit(
                        f"{task} {arm}: partial rows on disk ({len(done[(task, arm)])}"
                        f"/{len(need)}); quarantine rows/e5b.jsonl before resuming")
                with httpx.Client(base_url=BASE, timeout=180.0) as hc:
                    hc.get("/flush_cache").raise_for_status()
                answers: dict[int, str] = {}
                rows_here = []
                for t in turns:
                    step_no += 1
                    if step_no > cap:
                        raise SystemExit(f"call cap {cap} exceeded")
                    n = t["turn"]
                    history = render_history(arm, turns, n - 1)
                    system = (prefixes[task] + history
                              + f"CURRENT TURN {n} [{t['kind']}]: {t['instruction']}\n")
                    extra = {"task": task, "turn": n, "kind": t["kind"],
                             "prefix_sha8": prefix_sha[task], "mask_after": MASK_AFTER}
                    msgs = [{"role": "system", "content": system},
                            {"role": "user", "content": USER_ASK}]
                    row = adapter.chat(
                        msgs, max_tokens=MAX_TOKENS, temperature=0.0, seed=7, thinking=True,
                        run_id=env["run_id"], arm=arm, task_id=f"{task}:T{n:02d}",
                        step=step_no, extra=dict(extra))
                    if row["status"] != 200 or row.get("prompt_tokens") is None:
                        # one counted retry; a retry is a request and is recorded as one
                        step_no += 1
                        if step_no > cap:
                            raise SystemExit(f"call cap {cap} exceeded")
                        print(f"  retry {task} {arm} T{n}: {row.get('error') or row['status']}")
                        fh.write(json.dumps({**row, "extra": extra, "retry_of": row["call_id"]},
                                            sort_keys=True) + "\n")
                        fh.flush()
                        row = adapter.chat(
                            msgs, max_tokens=MAX_TOKENS, temperature=0.0, seed=7, thinking=True,
                            run_id=env["run_id"], arm=arm, task_id=f"{task}:T{n:02d}",
                            step=step_no, extra=dict(extra, retried=True))
                    answers[n] = row.get("text") or ""
                    t["answer"] = answers[n]
                    unc = (row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"]
                           if row["cached_tokens"] is not None else row["prompt_tokens"])
                    row["uncached_for_analysis"] = unc
                    rows_here.append(row)
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
                    fh.flush()
                per_arm[(task, arm)] = {"rows": rows_here, "answers": answers,
                                        "score": eval_checks(fx, answers)}
                sc = per_arm[(task, arm)]["score"]
                print(f"{task} {arm}: strict={sc['strict_passed']}/{sc['graded']} "
                      f"lax={sc['lax_passed']}/{sc['graded']} "
                      f"neg={sc['negatives_survived']}/{len(sc['negative'])} "
                      f"uncached={sum(r['uncached_for_analysis'] for r in rows_here)}")
        fh.close()

    return analyse()


def analyse() -> int:
    """Rebuild the analysis from the rows on disk, so a resumed run analyses as one."""
    fixtures = {t: load_fixture(t) for t in TASKS}
    rows = [json.loads(l) for l in ROWS.read_text().splitlines() if l.strip()]
    per_arm: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        per_arm.setdefault((r["task"], r["arm"]), []).append(r)
    for key in per_arm:
        per_arm[key].sort(key=lambda r: r["turn"])

    analysis = {"schema": "typed-context-pilot.e5-analysis/1",
                "run_id": rows[0]["run_id"] if rows else "",
                "calls": len(rows), "tasks": {}, "gate": {}}
    for task in TASKS:
        analysis["tasks"][task] = {}
        base = None
        for arm in ARMS:
            rows_here = per_arm.get((task, arm))
            if not rows_here:
                continue
            good = [r for r in rows_here if r.get("prompt_tokens") is not None]
            answers = {r["turn"]: (r.get("text") or "") for r in good}
            score = eval_checks(fixtures[task], answers)
            unc = [r["uncached_for_analysis"] for r in good if "uncached_for_analysis" in r]
            checks = []
            for c in score["checks"]:
                item = dict(c)
                turn = c.get("turn")
                item["applicability"] = (instruction_kind(fixtures[task], turn)
                                         if turn is not None else "n/a")
                checks.append(item)
            analysis["tasks"][task][arm] = {
                "turns": len(good),
                "uncached_total": sum(unc),
                "prompt_total": sum(r["prompt_tokens"] for r in good),
                "cached_total": sum(r["cached_tokens"] or 0 for r in good),
                "completion_total": sum(r["completion_tokens"] or 0 for r in good),
                "reasoning_total": sum((r.get("usage_raw") or {}).get("reasoning_tokens") or 0
                                       for r in good),
                "errored_calls": len(rows_here) - len(good),
                "uncached_series": unc,
                "prompt_series": [r["prompt_tokens"] for r in good],
                "checks": checks,
                "negative": score["negative"],
                "score": score,
                "answers_at_checkpoints": {
                    str(c["turn"]): answers.get(c["turn"], "")[:160]
                    for c in fixtures[task]["checkpoints"]},
            }
            if arm == "A":
                base = analysis["tasks"][task]["A"]
        if base is None:
            continue
        summary = []
        for arm in ARMS:
            v = analysis["tasks"][task].get(arm)
            if not v:
                continue
            summary.append({
                "arm": arm,
                "strict_passed": v["score"]["strict_passed"],
                "lax_passed": v["score"]["lax_passed"],
                "graded": v["score"]["graded"],
                "negatives_survived": v["score"]["negatives_survived"],
                "uncached_total": v["uncached_total"],
                "prompt_total": v["prompt_total"],
                "uncached_delta_pct_vs_A": round(100 * (v["uncached_total"] / base["uncached_total"] - 1), 2)
                if base["uncached_total"] else None,
                "prompt_delta_pct_vs_A": round(100 * (v["prompt_total"] / base["prompt_total"] - 1), 2)
                if base["prompt_total"] else None,
            })
        analysis["tasks"][task]["summary"] = summary
        analysis["gate"][task] = {}
        for arm in ARMS[1:]:
            v = analysis["tasks"][task].get(arm)
            if not v:
                continue
            worse = [c["id"] for c, b in zip(v["checks"], base["checks"])
                     if "strict" in c and "strict" in b and c["strict"] < b["strict"]]
            analysis["gate"][task][arm] = {
                "checks_not_worse_than_A": not worse,
                "worse_checks": worse,
                "negatives_ok": v["score"]["negatives_survived"] == len(v["score"]["negative"]),
                "cost_10pct_lower": v["uncached_total"] <= 0.9 * base["uncached_total"],
                "passes": (not worse)
                and v["score"]["negatives_survived"] == len(v["score"]["negative"])
                and v["uncached_total"] <= 0.9 * base["uncached_total"],
            }
    ANALYSIS.write_text(json.dumps(analysis, indent=2) + "\n")
    print(json.dumps(analysis["gate"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
