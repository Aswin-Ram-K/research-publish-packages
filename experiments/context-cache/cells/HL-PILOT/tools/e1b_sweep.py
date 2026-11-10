#!/usr/bin/env python3
"""E1 v2 — CACHE-BOUNDARY-SWEEP with per-cell isolation.

Why a second envelope: the first E1 run (``envelopes/E1.json``, rows in
``rows/e1.jsonl``) had three defects, all mine, all visible in its own rows:

1. **Rep invariance.** ``rewrite_at`` is deterministic in the offset, so
   repetitions 2 and 3 were byte-identical to repetition 1 and therefore full
   cache hits by construction (cached 10,048 = whole prompt). Only rep 1 was
   informative; the sweep's "3 repetitions" measured repeats, not variants.
2. **Silent no-op rewrites.** Offsets 0.9 (line 561) and 0.7 (line 436) landed
   on lines with no alphanumeric characters, so ROT13 changed nothing: the
   prompt was byte-identical to the frozen prefix (prompt_tokens 10,048, cached
   9,984). Those cells were not rewrites at all.
3. **Branch thrash.** Every variant adds a fresh ~10K branch. With
   ``--max-mamba-cache-size 64`` and a 256-token tracking interval, ~39 mamba
   states per branch means roughly one and a half branches fit; later cells were
   measured against a cache whose earlier branches had been evicted. The first
   run's non-monotonicity (0.7 and 0.2 reporting full-prompt reuse) is explained
   by (1) and (2) before it is explained by the engine.

v2 fixes all three: each repetition applies a *different* rotation, target lines
are required to contain alphanumerics and the prompt bytes are asserted to
change, and every cell is isolated by ``GET /flush_cache`` followed by a fresh
seed of the frozen prefix. A flushed cell is a cold-seeded cell: the seed's own
row is recorded as evidence that the prefix is resident again.

Budget: 12 control calls + 9 offsets x (1 flush + 1 seed + 3 measurements) = 57
model calls, inside E1's 60-call budget. ``/flush_cache`` and ``/tokenize`` are
not model requests and are counted separately.
"""
from __future__ import annotations

import argparse
import fcntl
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
import e1_boundary as e1  # noqa: E402

LOCK = WT / "experiments/context-cache/.occamy.lock"
BASE = "http://192.168.2.168:8012"
ENVELOPE = CELL / "envelopes/E1C.json"
ROWS = CELL / "rows/e1c.jsonl"
ANALYSIS = CELL / "notes/e1c-analysis.json"
PREFIX_CACHE = CELL / "notes/e1c-prefix.json"
RATIOS = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]


def alnum_count(s: str) -> int:
    return sum(1 for ch in s if ch.isalnum())


def build_plan(client: httpx.Client):
    prefix, rows = e1.build_prefix()
    prefix, rows = e1.trim_to(prefix, rows, client, e1.TARGET_TOKENS)
    offs = e1.line_offsets(prefix, rows)
    n_tokens = e1.tok_count(client, prefix)

    import bisect

    cells = []
    for r in RATIOS:
        target = int(r * n_tokens)
        start = max(0, bisect.bisect_right(offs, _char_for(prefix, offs, rows, target, client)) - 1)
        idx = start
        # a rewrite must land on a line with real content, otherwise it is a no-op
        while idx < len(rows) and alnum_count(rows[idx]["text"]) < 8:
            idx += 1
        if idx >= len(rows):
            raise SystemExit(f"no rewritable line near ratio {r}")
        tok_at = e1.tok_count(client, prefix[: offs[idx]])
        cells.append(
            {
                "ratio": r,
                "line": rows[idx]["n"],
                "index": idx,
                "char_offset": offs[idx],
                "byte_offset": len(prefix[: offs[idx]].encode()),
                "token_offset": tok_at,
            }
        )
    return prefix, rows, offs, cells, n_tokens


def _char_for(prefix, offs, rows, target_tokens, client):
    lo, hi, best = 0, len(offs) - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if e1.tok_count(client, prefix[: offs[mid]]) <= target_tokens:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return offs[best]


def rewrite(prefix: str, offs: list[int], index: int, shift: int) -> tuple[str, int]:
    """Rotate exactly one line, by a shift that differs per repetition."""
    line_start = offs[index]
    line_end = prefix.index("\n", line_start)
    line = prefix[line_start:line_end]
    marker, _, rest = line.partition("| ")
    rotated = "".join(
        chr(ord("a") + (ord(ch) - ord("a") + shift) % 26) if ch.islower()
        else chr(ord("A") + (ord(ch) - ord("A") + shift) % 26) if ch.isupper()
        else chr(ord("0") + (ord(ch) - ord("0") + shift) % 10) if ch.isdigit()
        else ch
        for ch in rest
    )
    out = prefix[:line_start] + marker + "| " + rotated + prefix[line_end:]
    assert len(out) == len(prefix)
    return out, line_start


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with httpx.Client(base_url=BASE, timeout=120.0) as client:
        prefix, rows, offs, cells, n_tokens = build_plan(client)
        n_instr = e1.tok_count(client, e1.INSTRUCTION)
        n_tail = e1.tok_count(client, e1.TAIL_PAD)
        prefix_sha = __import__("hashlib").sha256(prefix.encode()).hexdigest()

    if args.dry_run:
        print(f"prefix tokens={n_tokens} bytes={len(prefix.encode())} lines={len(rows)} sha={prefix_sha[:16]}")
        for c in cells:
            print(f"ratio {c['ratio']:.1f} token {c['token_offset']:6d} line {c['line']} text={rows[c['index']]['text'][:48]!r}")
        print("planned model calls:", 12 + len(cells) * 5)
        return 0

    if args.plan:
        fp = json.loads((CELL / "envelopes/fingerprints.json").read_text())
        inspect = json.loads((CELL / "notes/container-inspect-2026-11-04.json").read_text())[0]
        env = {
            "schema": "consonance.run/1",
            "run_id": "HL-E1C-2026-11-04",
            "arm": "E1-CACHE-BOUNDARY-SWEEP-V3",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=WT,
                                      capture_output=True, text=True).stdout.strip(),
            "fixture_sha": "sha256:" + prefix_sha,
            "engine_image_digest": inspect["Image"],
            "engine_flags": inspect["Args"],
            "hardware": "gx10 / GB10, 128 GB unified",
            "quantization": "nvfp4 (modelopt_fp4)",
            "budgets": {"max_calls": 60, "max_cost_usd": 0},
            "controls": {
                "identical_repeat_hits": True,
                "never_sent_misses": True,
                "append_reuses": True,
                "rewrite_registers": True,
                "mismatched_tokenizer": "UNAVAILABLE - needs a second tokenizer on the same engine",
                "cell_isolation": "GET /flush_cache + fresh seed of the frozen prefix before every cell; "
                                  "the seed row is recorded so residency can be checked",
            },
            "fingerprints": {k: fp[k] for k in (
                "model_fingerprint", "tokenizer_fingerprint",
                "renderer_fingerprint", "engine_fingerprint")},
            "generation": {"max_tokens": 4, "temperature": 0.0, "seed": 7,
                           "chat_template_kwargs": {"enable_thinking": False}},
            "prefix": {"tokens": n_tokens, "bytes": len(prefix.encode()), "lines": len(rows),
                       "sha256": prefix_sha, "instruction_tokens": n_instr,
                       "tail_pad_tokens": n_tail},
            "cells": cells,
            "call_plan": ["cold", "identical", "identical", "append", "append", "append",
                          "never_sent", "never_sent", "never_sent",
                          "first_token", "first_token", "first_token"]
            + [x for c in cells for x in (f"seed:{c['ratio']}",
                                          f"measure:{c['ratio']}:1",
                                          f"measure:{c['ratio']}:2",
                                          f"measure:{c['ratio']}:3")]
            + [f"flush:{c['ratio']}" for c in cells],
            "supersedes": {"run_id": "HL-E1B-2026-11-04", "envelope": "envelopes/E1B.json",
                           "defects": ["the frozen prefix was still resident from run E1, so the 'cold' "
                                       "control and the first-line mutation were warm hits (cached 9984); "
                                       "run v3 flushes before the control block",
                                       "rotation shift 26 is the identity on letters, so rep 2 of ratio "
                                       "0.9 was a byte-identical no-op; v3 uses shifts 5/11/17 and asserts "
                                       "the prompt changes",
                                       "aborted runs wrote no rows; v3 appends each row as it is made"]},
            "also_supersedes": {"run_id": "HL-E1-2026-11-04", "envelope": "envelopes/E1.json"},
            "notes": (
                "Hypothesis: reuse falls monotonically as the first rewritten offset moves earlier. "
                "Falsifier: non-monotonic reuse, all-or-nothing reuse, or block-alignment-only dependence. "
                "cached_tokens absent is null (unknown), never 0. Residual delta = token_offset - cached is "
                "reported per cell: a constant delta means the engine drops a fixed span before the "
                "divergence point rather than being unable to reuse it."
            ),
        }
        ENVELOPE.write_text(json.dumps(env, indent=2) + "\n")
        PREFIX_CACHE.write_text(json.dumps({"prefix": prefix, "rows": rows, "offsets": offs}) + "\n")
        print("frozen", ENVELOPE, "model calls", len(env["call_plan"]) - len(cells))
        return 0

    env = json.loads(ENVELOPE.read_text())
    if env.get("retrospective"):
        raise SystemExit("retrospective envelope; refusing")
    stored = json.loads(PREFIX_CACHE.read_text())
    if stored["prefix"] != prefix:
        raise SystemExit("prefix rebuild differs from the frozen prefix; refusing")
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
        if env["budgets"]["max_calls"] < 12 + len(env["cells"]) * 5:
            raise SystemExit("call plan exceeds cap")

        adapter = Adapter()
        out: list[dict] = []
        step = 0

        def send(task_id, system, epoch, extra, user=e1.INSTRUCTION):
            nonlocal step
            step += 1
            if step > cap:
                raise SystemExit(f"call cap {cap} exceeded")
            row = adapter.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=4, temperature=0.0, seed=7,
                run_id=env["run_id"], arm=env["arm"], task_id=task_id, step=step,
                extra={"epoch": epoch, **extra},
            )
            out.append(row)
            print(f"{step:3d} {task_id:20s} pt={row['prompt_tokens']} cached={row['cached_tokens']} "
                  f"ttft={row['ttft_ms']}")
            return row

        salt = f"E1C-{prefix_sha[:10]}"
        with httpx.Client(base_url=BASE, timeout=120.0) as hc:
            flushed = hc.get("/flush_cache")
            flushed.raise_for_status()
        print("flushed cache before the control block")
        ROWS.parent.mkdir(parents=True, exist_ok=True)
        fh = ROWS.open("w")
        orig_send = send

        def send(task_id, system, epoch, extra, user=e1.INSTRUCTION):
            row = orig_send(task_id, system, epoch, extra, user)
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            return row

        send("cold", prefix, "cold", {"salt": salt, "flushed_before": True})
        send("identical", prefix, "warm", {"salt": salt})
        send("identical", prefix, "warm", {"salt": salt})
        for i in range(3):
            send("append", prefix, "warm",
                 {"salt": salt, "appended_tokens": n_tail, "rep": i + 1},
                 user=e1.INSTRUCTION + "\n\n" + e1.TAIL_PAD + f"rep-{i + 1} unique tail marker.\n")
        for i in range(3):
            send("never_sent", f"NEVER-SENT-{salt}-{i}\n" + prefix, "warm", {"salt": f"{salt}-{i}"})
        for i, pos in enumerate((0, 3, 7)):
            mutated = prefix[:pos] + ("Z" if prefix[pos] != "Z" else "Q") + prefix[pos + 1:]
            send("first_token", mutated, "warm", {"salt": salt, "mutated_at": pos})

        for cell_no, c in enumerate(env["cells"]):
            with httpx.Client(base_url=BASE, timeout=120.0) as hc:
                r = hc.get("/flush_cache")
                r.raise_for_status()
            seeded = send(f"seed:{c['ratio']}", prefix, "warm",
                          {"salt": salt, "cell": cell_no, "flushed_before": True})
            for rep in (1, 2, 3):
                shift = (5, 11, 17)[rep - 1]
                rewritten, _ = rewrite(prefix, stored["offsets"], c["index"], shift=shift)
                if rewritten == prefix:
                    raise SystemExit(f"no-op rewrite at ratio {c['ratio']} rep {rep}")
                send(f"measure:{c['ratio']}:{rep}", rewritten, "warm",
                     {"salt": salt, "cell": cell_no, "rep": rep, "flushed_before": True,
                      "ratio": c["ratio"], "rewritten_line": c["line"],
                      "expected_token_offset": c["token_offset"], "shift": shift,
                      "seed_prompt_tokens": seeded["prompt_tokens"],
                      "seed_cached_tokens": seeded["cached_tokens"]})

    fh.close()

    def sel(prefix_task: str) -> list[dict]:
        return [r for r in out if r["task_id"].startswith(prefix_task)]

    cold = sel("cold")[0]
    cells_out = {}
    deltas = []
    for c in env["cells"]:
        meas = sel(f"measure:{c['ratio']}:")
        cached = [m["cached_tokens"] for m in meas]
        residual = [None if m["cached_tokens"] is None
                    else c["token_offset"] - m["cached_tokens"] for m in meas]
        valid = [x for x in residual if x is not None]
        if valid:
            deltas.extend(valid)
        cells_out[str(c["ratio"])] = {
            "token_offset": c["token_offset"],
            "byte_offset": c["byte_offset"],
            "cached": cached,
            "residual_token_offset_minus_cached": residual,
            "ttft_ms": [m["ttft_ms"] for m in meas],
            "prompt_tokens": [m["prompt_tokens"] for m in meas],
            "seed_cached": [m.get("seed_cached_tokens") for m in meas],
        }

    # monotonicity on the median residual (a constant residual is not a violation)
    medians = {float(r): (statistics.median([x for x in v["residual_token_offset_minus_cached"]
                                             if x is not None])
                          if any(x is not None for x in v["residual_token_offset_minus_cached"])
                          else None)
               for r, v in cells_out.items()}
    violations = []
    prev = None
    for r in sorted(medians, reverse=True):
        m = medians[r]
        if m is not None and prev is not None and abs(m - prev) > 128:
            violations.append({"ratio": r, "median_residual": m, "previous": prev})
        if m is not None:
            prev = m

    analysis = {
        "schema": "typed-context-pilot.e1-analysis/3",
        "run_id": env["run_id"],
        "calls": len(out),
        "prefix": env["prefix"],
        "controls": {
            "identical": {"cached": [cold["cached_tokens"]] + [
                r["cached_tokens"] for r in sel("identical")],
                "prompt_tokens": [r["prompt_tokens"] for r in [cold] + sel("identical")]},
            "append": {"cached": [r["cached_tokens"] for r in sel("append")],
                       "prompt_tokens": [r["prompt_tokens"] for r in sel("append")],
                       "appended_tokens": env["prefix"]["tail_pad_tokens"]},
            "never_sent": {"cached": [r["cached_tokens"] for r in sel("never_sent")],
                           "no_reuse": all(r["cached_tokens"] in (0, None) for r in sel("never_sent"))},
            "first_token": {"cached": [r["cached_tokens"] for r in sel("first_token")],
                            "no_reuse": all(r["cached_tokens"] in (0, None) for r in sel("first_token"))},
            "mismatched_tokenizer": "unavailable",
        },
        "cells": cells_out,
        "median_residual_overall": statistics.median(deltas) if deltas else None,
        "residual_spread": (max(deltas) - min(deltas)) if deltas else None,
        "monotonicity_violations_gt_128_tokens": violations,
    }
    ANALYSIS.write_text(json.dumps(analysis, indent=2) + "\n")
    print(json.dumps({"calls": analysis["calls"],
                      "median_residual": analysis["median_residual_overall"],
                      "spread": analysis["residual_spread"],
                      "violations": violations,
                      "controls": analysis["controls"]}, indent=1)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
