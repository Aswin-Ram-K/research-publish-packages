#!/usr/bin/env python3
"""E2 CHECKPOINT-COST — the premise test.

Question (``handoff from consonance/EXPERIMENTS.md`` E2): what does one
compaction checkpoint cost, and over how many steps can it repay that cost?

Design. One deterministic 30-step trajectory, three arms, one verifier:

    A  append-only          the whole history verbatim, extended by one
                            observation per step;
    B  one checkpoint        same, but at step 21 (70 % of the trajectory) the
                            history is replaced by a dense typed record table;
    C  periodic checkpoint   the same compaction at steps 10 and 20.

Every step asks a question that can only be answered from the retained context
("fingerprint of obs{k-2}"), so verified success is a real check, not a label.
The typed record keeps exactly the field the question asks for, so compaction
does not change what is *answerable* — it changes what is *sent*. That is what
makes the cost comparison fair: a checkpoint is allowed to be cheap only by
sending fewer tokens, never by being asked less.

Three controls:
  * append-only must show a climbing cached share (the reused prefix grows);
  * a no-op checkpoint (the same context re-sent, nothing rewritten) must cost
    approximately nothing — appended as extra calls inside arm A;
  * the falsifier itself: if the checkpoint arms repay only because their
    prompts are shorter, the gain disappears when cost is measured as uncached
    prefill work. That number is the published result either way.

Budget: 30 calls per arm + 3 no-op control calls = 93, inside E2's 120.
Arm order is A, B, C with a cache flush between arms, because the arms' prefixes
diverge at the first step and would otherwise inherit each other's branches.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
WT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(CELL / "tools"))

import httpx  # noqa: E402
from adapter import Adapter  # noqa: E402

LOCK = WT / "experiments/context-cache/.occamy.lock"
BASE = "http://192.168.2.168:8012"
ENVELOPE = CELL / "envelopes/E2.json"
ROWS = CELL / "rows/e2.jsonl"
ANALYSIS = CELL / "notes/e2-analysis.json"
SOURCE = WT / "src/resextract/context/render.py"
STEPS = 30
LINES_PER_OBS = 20
NOOP_AT = (5, 15, 25)
CHECKPOINTS = {"A": (), "B": (21,), "C": (10, 20)}

HEADER = """You are a deterministic checker inside a tool loop.

Protocol: every step delivers one observation block, then one question. Answer
the question with the requested value only - no explanation, no punctuation.
Observations are immutable; a typed record line stands in for an observation
body when the history has been compacted.

"""


def observations() -> list[dict]:
    lines = [ln for ln in SOURCE.read_text().splitlines() if ln.strip()]
    out = []
    for k in range(1, STEPS + 3):
        start = (k - 1) * 7 % max(1, len(lines) - LINES_PER_OBS)
        body = "\n".join(lines[start:start + LINES_PER_OBS])
        fp = hashlib.sha256(body.encode()).hexdigest()[:8]
        out.append({"k": k, "body": body, "fp": fp, "src": f"render.py:{start + 1}-{start + LINES_PER_OBS}"})
    return out


def verbatim(obs: dict) -> str:
    return f"[observation {obs['k']} | {obs['src']} | fingerprint {obs['fp']}]\n{obs['body']}\n"


def record(obs: dict) -> str:
    return f"obs{obs['k']} fp={obs['fp']} src={obs['src']}"


def question(obs: dict) -> str:
    return (f"Question: what is the fingerprint recorded for obs{obs['k']}? "
            "Answer with the 8 hexadecimal characters only.")


def build(arm: str, step: int, obs: list[dict], checkpoint_at: int | None) -> tuple[str, dict]:
    """Return (system_text, metadata) for one step of one arm."""
    history = obs[:step]
    if checkpoint_at is None:
        body = "\n".join(verbatim(o) for o in history)
        mode = "verbatim"
    else:
        folded = history[: checkpoint_at]
        tail = history[checkpoint_at:]
        table = "\n".join(record(o) for o in folded)
        body = (f"[typed record table | {len(folded)} observations folded | "
                f"chain_hash {hashlib.sha256(table.encode()).hexdigest()[:16]}]\n"
                + table + "\n")
        if tail:
            body += "\n" + "\n".join(verbatim(o) for o in tail)
        mode = "compacted"
    target = obs[max(0, step - 3)]
    return HEADER + body + "\n" + question(target), {
        "mode": mode,
        "folded": 0 if checkpoint_at is None else checkpoint_at,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    obs = observations()
    fp = json.loads((CELL / "envelopes/fingerprints.json").read_text())
    inspect = json.loads((CELL / "notes/container-inspect-2026-11-04.json").read_text())[0]
    plan_rows = []
    for arm in ("A", "B", "C"):
        cps = CHECKPOINTS[arm]
        for step in range(1, STEPS + 1):
            cp = None
            if cps:
                cp = max([c for c in cps if c <= step], default=None)
            system, meta = build(arm, step, obs, cp)
            plan_rows.append({"arm": arm, "step": step, "chars": len(system), **meta,
                              "rebuild": cp is not None and step == cp})
    noop_calls = len(NOOP_AT)

    if args.dry_run:
        for arm in ("A", "B", "C"):
            rows = [r for r in plan_rows if r["arm"] == arm]
            print(arm, "steps", len(rows), "chars first/last",
                  rows[0]["chars"], rows[-1]["chars"],
                  "rebuild steps", [r["step"] for r in rows if r["rebuild"]])
        print("model calls:", len(plan_rows) + noop_calls)
        return 0

    if args.plan:
        env = {
            "schema": "consonance.run/1",
            "run_id": "HL-E2-2026-11-04",
            "arm": "E2-CHECKPOINT-COST",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=WT,
                                      capture_output=True, text=True).stdout.strip(),
            "fixture_sha": "sha256:" + hashlib.sha256(
                json.dumps(obs, sort_keys=True).encode()).hexdigest(),
            "engine_image_digest": inspect["Image"],
            "engine_flags": inspect["Args"],
            "hardware": "gx10 / GB10, 128 GB unified",
            "quantization": "nvfp4 (modelopt_fp4)",
            "budgets": {"max_calls": 120, "max_cost_usd": 0},
            "controls": {
                "identical_repeat_hits": True,
                "never_sent_misses": True,
                "append_reuses": True,
                "noop_checkpoint_costs_nothing": True,
                "mismatched_tokenizer": "UNAVAILABLE - needs a second tokenizer on the same engine",
            },
            "fingerprints": {k: fp[k] for k in (
                "model_fingerprint", "tokenizer_fingerprint",
                "renderer_fingerprint", "engine_fingerprint")},
            "generation": {"max_tokens": 12, "temperature": 0.0, "seed": 7,
                           "chat_template_kwargs": {"enable_thinking": False}},
            "trajectory": {"steps": STEPS, "lines_per_observation": LINES_PER_OBS,
                           "source": str(SOURCE), "checkpoints": CHECKPOINTS,
                           "noop_control_steps": NOOP_AT,
                           "verifier": "answer must equal the 8-hex fingerprint of obs{step-2}"},
            "arms": {"A": "append-only verbatim", "B": "one checkpoint at step 21",
                     "C": "checkpoints at steps 10 and 20"},
            "order": ["A", "B", "C"], "flushed_between_arms": True,
            "call_plan_count": len(plan_rows) + noop_calls,
            "notes": ("Hypothesis: a checkpoint that rewrites D tokens costs ~D prefill and repays inside "
                      "20 steps. Falsifier: it does not repay, or repays only because the prompt got "
                      "shorter - i.e. the gain vanishes when cost is measured as uncached prefill work. "
                      "Both numbers are published: cache-adjusted (prompt - cached) and total prompt.")
        }
        ENVELOPE.write_text(json.dumps(env, indent=2) + "\n")
        print("frozen", ENVELOPE, "calls", env["call_plan_count"])
        return 0

    env = json.loads(ENVELOPE.read_text())
    if env.get("retrospective"):
        raise SystemExit("retrospective envelope")
    cap = env["budgets"]["max_calls"]

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
        fh = ROWS.open("w")
        adapter = Adapter()
        step_no = 0

        def send(arm, task_id, system, extra):
            nonlocal step_no
            step_no += 1
            if step_no > cap:
                raise SystemExit(f"call cap {cap} exceeded")
            row = adapter.chat(
                [{"role": "system", "content": system},
                 {"role": "user", "content": "Proceed."}],
                max_tokens=12, temperature=0.0, seed=7,
                run_id=env["run_id"], arm=arm, task_id=task_id, step=step_no, extra=extra)
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            print(f"{step_no:3d} {arm} {task_id:14s} pt={row['prompt_tokens']:6d} "
                  f"cached={str(row['cached_tokens']):>6s} ok={row.get('verified_success')} "
                  f"ttft={row['ttft_ms']}")
            return row

        for arm in env["order"]:
            with httpx.Client(base_url=BASE, timeout=120.0) as hc:
                hc.get("/flush_cache").raise_for_status()
            cps = CHECKPOINTS[arm]
            for step in range(1, STEPS + 1):
                cp = max([c for c in cps if c <= step], default=None) if cps else None
                system, meta = build(arm, step, obs, cp)
                expect = obs[max(0, step - 3)]["fp"]
                task = "rebuild" if (cp is not None and step == cp) else f"step-{step:02d}"
                send(arm, task, system,
                     {"step_in_arm": step, "expected_fp": expect,
                      "flushed_before_arm": True, **meta})
                if step in NOOP_AT and arm == "A":
                    send(arm, f"noop-{step:02d}", system,
                         {"step_in_arm": step, "expected_fp": expect,
                          "noop_checkpoint": True, **meta})
        fh.close()

    rows = [json.loads(l) for l in ROWS.read_text().splitlines()]
    # verifier pass, recomputed from the returned answers
    for row in rows:
        exp = row.get("expected_fp")
        row["verified_success"] = bool(exp) and exp in (row.get("text") or "").lower()
    with ROWS.open("w") as out:
        for row in rows:
            out.write(json.dumps(row, sort_keys=True) + "\n")

    analysis = {"schema": "typed-context-pilot.e2-analysis/1", "run_id": env["run_id"],
                "calls": len(rows), "arms": {}}
    for arm in env["order"]:
        arm_rows = [r for r in rows if r["arm"] == arm]
        steps = [r for r in arm_rows if not r.get("noop_checkpoint")]
        noops = [r for r in arm_rows if r.get("noop_checkpoint")]
        uncached = [r["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"]
                    if r["cached_tokens"] is not None else r["prompt_tokens"]
                    for r in steps]
        share = [round((r["cached_tokens"] or 0) / r["prompt_tokens"], 4) for r in steps]
        analysis["arms"][arm] = {
            "calls": len(steps),
            "verified": sum(1 for r in steps if r.get("verified_success")),
            "prompt_tokens": [r["prompt_tokens"] for r in steps],
            "cached_tokens": [r["cached_tokens"] for r in steps],
            "uncached": uncached,
            "total_prompt": sum(r["prompt_tokens"] for r in steps),
            "total_uncached": sum(uncached),
            "median_uncached": statistics.median(uncached),
            "cached_share_first": share[0],
            "cached_share_last": share[-1],
            "ttft_ms": [r["ttft_ms"] for r in steps],
            "rebuild_rows": [{"step": r["task_id"], "prompt": r["prompt_tokens"],
                              "cached": r["cached_tokens"], "uncached": uncached[i]}
                             for i, r in enumerate(steps) if r["task_id"] == "rebuild"],
            "noop": [{"prompt": r["prompt_tokens"], "cached": r["cached_tokens"],
                      "uncached": (r["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"]
                                   if r["cached_tokens"] is not None else None)}
                     for r in noops],
        }
        analysis["arms"][arm]["total_prompt"] = sum(r["prompt_tokens"] for r in steps)
        analysis["arms"][arm]["total_uncached"] = sum(uncached)
    ANALYSIS.write_text(json.dumps(analysis, indent=2) + "\n")
    print(json.dumps({a: {"verified": v["verified"], "calls": v["calls"],
                          "total_prompt": v["total_prompt"],
                          "total_uncached": v["total_uncached"],
                          "median_uncached": v["median_uncached"]}
                      for a, v in analysis["arms"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
