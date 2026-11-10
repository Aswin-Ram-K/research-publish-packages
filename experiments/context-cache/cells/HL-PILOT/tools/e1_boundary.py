#!/usr/bin/env python3
"""E1 CACHE-BOUNDARY-SWEEP on the frozen occamy prefix.

Pre-registration: ``envelopes/E1.json`` is written and frozen before the first
model call (``--plan`` does that; the run refuses to start without it).

The question (``handoff from consonance/EXPERIMENTS.md`` E1): with a frozen
system prefix ``P`` of ~8-12K tokens, does reuse fall monotonically as the first
rewritten offset moves earlier, and is there a boundary below which the request
is served effectively cold?

Controls, in the order the file prescribes (controls before primary runs):
  identical        the first send of ``P`` seeds the cache (cold epoch), two
                   identical repeats must hit >= 0.9 of ``P`` (warm epoch);
  append           ``P`` + 400-token tail must reuse >= ``P`` - k;
  never-sent       a prompt whose FIRST token differs must report no reuse;
  first-token      the shipped substitute for the "mismatched tokenizer" control:
                   a one-token change at the head. The literal mismatched-tokenizer
                   arm is UNAVAILABLE here - it needs a second tokenizer on the same
                   engine, which this image does not offer - and is labelled so
                   rather than claimed as passed.

Then the sweep: 9 rewrite offsets, tail to head, 3 repetitions each, order
alternating per repetition.

Token offsets are real tokenizer units: line boundaries are mapped with the
server's ``/tokenize`` endpoint, so no chars-per-token approximation is used.
``/tokenize`` is not a model request and is counted separately in the envelope.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import statistics
import time
from pathlib import Path

sys_path_root = Path(__file__).resolve().parents[5]
import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

import httpx  # noqa: E402
from adapter import Adapter  # noqa: E402

CELL = Path(__file__).resolve().parents[1]
WT = sys_path_root
LOCK = WT / "experiments/context-cache/.occamy.lock"
BASE = "http://192.168.2.168:8012"
MODEL = "occamy-1.0"
ENVELOPE = CELL / "envelopes/E1.json"
ROWS = CELL / "rows/e1.jsonl"
ANALYSIS = CELL / "notes/e1-analysis.json"
PREFIX_CACHE = CELL / "notes/e1-prefix.json"

SOURCES = [
    ("context/nodes.py", "src/resextract/context/nodes.py"),
    ("context/render.py", "src/resextract/context/render.py"),
    ("context/budget.py", "src/resextract/context/budget.py"),
    ("context/meter.py", "src/resextract/context/meter.py"),
    ("context/salt.py", "src/resextract/context/salt.py"),
    ("pointers.py", "src/resextract/pointers.py"),
]

# EXPERIMENTS.md E1 asks for a frozen prefix of ~8-12K tokens. The accumulation
# above is ~37K, so it is cut at a line boundary to land inside that band; the
# cut is measured with /tokenize, never estimated from characters.
TARGET_TOKENS = 10_000

HEADER = """FROZEN PROJECT PREFIX (E1 boundary sweep)
This block is a fixed, version-pinned snapshot of extractor sources. Every line
is numbered so that a single line can be rewritten in place while the rest of
the block stays byte-identical. Nothing here is a task; the request that follows
only asks for one word.

"""

INSTRUCTION = "Reply with the single word OK and nothing else."
TAIL_PAD = (
    "The appended control tail is deliberately dull: it adds tokens after the "
    "frozen prefix so that reuse of the prefix can be measured against a longer "
    "prompt. It is not an instruction and it is not evidence.\n"
) * 10


def tok_count(client: httpx.Client, text: str) -> int:
    r = client.post(
        "/tokenize", json={"model": MODEL, "prompt": text}, timeout=120.0
    )
    r.raise_for_status()
    return int(r.json()["count"])


def build_prefix() -> tuple[str, list[dict]]:
    """Deterministic numbered-line prefix from pinned sources."""
    rows: list[dict] = []
    body_parts: list[str] = [HEADER]
    n = 0
    for label, rel in SOURCES:
        path = WT / rel
        if not path.exists():
            continue
        body_parts.append(f"=== BEGIN {label} ({rel}) ===\n")
        for line in path.read_text(errors="replace").splitlines():
            n += 1
            rows.append({"n": n, "label": label, "text": line})
            body_parts.append(f"{n:05d}| {line}\n")
        body_parts.append(f"=== END {label} ===\n")
    return "".join(body_parts), rows


def trim_to(text: str, rows: list[dict], client: httpx.Client, target: int):
    """Cut at a line boundary so the prefix lands at or below ``target`` tokens."""
    offs = line_offsets(text, rows)
    lo, hi, best = 0, len(rows) - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if tok_count(client, text[: offs[mid]]) <= target:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    end = text.index("\n", offs[best]) + 1
    kept = text[:end] + "=== END FROZEN PREFIX ===\n"
    return kept, rows[: best + 1]


def line_offsets(text: str, rows: list[dict]) -> list[int]:
    """Char offset of each numbered line's first character."""
    out = []
    pos = text.index("00001|")
    for row in rows:
        token = f"{row['n']:05d}|"
        found = text.index(token, pos)
        out.append(found)
        pos = found + len(token)
    return out


def rot13(s: str) -> str:
    out = []
    for ch in s:
        if "a" <= ch <= "z" or "A" <= ch <= "Z":
            base = ord("a") if ch.islower() else ord("A")
            out.append(chr(base + (ord(ch) - base + 13) % 26))
        elif ch.isdigit():
            out.append(chr(ord("0") + (ord(ch) - ord("0") + 5) % 10))
        else:
            out.append(ch)
    return "".join(out)


def rewrite_at(prefix: str, rows: list[dict], offs: list[int], char_pos: int) -> tuple[str, dict]:
    """ROT13 exactly one numbered line body; everything else untouched."""
    import bisect

    idx = max(0, bisect.bisect_right(offs, char_pos) - 1)
    row = rows[idx]
    line_start = offs[idx]
    line_end = prefix.index("\n", line_start)
    line = prefix[line_start:line_end]
    marker, _, rest = line.partition("| ")
    new_line = marker + "| " + rot13(rest)
    assert len(new_line) == len(line), "rewrite must preserve byte length"
    out = prefix[:line_start] + new_line + prefix[line_end:]
    assert out[:line_start] == prefix[:line_start]
    return out, {"rewritten_line": row["n"], "line_char_offset": line_start}


def plan(prefix: str, rows: list[dict], offs: list[int], client: httpx.Client) -> dict:
    n_tokens = tok_count(client, prefix)
    n_instr = tok_count(client, INSTRUCTION)
    n_tail = tok_count(client, TAIL_PAD)
    ratios = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    offsets = []
    for r in ratios:
        target = int(r * n_tokens)
        lo, hi = 0, len(offs) - 1
        best = 0
        # binary search: largest line whose start is <= target tokens
        calls = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            calls += 1
            if tok_count(client, prefix[: offs[mid]]) <= target:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        tok_at = tok_count(client, prefix[: offs[best]])
        offsets.append(
            {
                "ratio": r,
                "token_offset": tok_at,
                "char_offset": offs[best],
                "line": rows[best]["n"],
                "byte_offset": len(prefix[: offs[best]].encode()),
            }
        )
    return {
        "prompt_tokens_of_prefix": n_tokens,
        "prompt_bytes_of_prefix": len(prefix.encode()),
        "instruction_tokens": n_instr,
        "tail_pad_tokens": n_tail,
        "lines": len(rows),
        "offsets": offsets,
        "tokenize_calls": 2 + sum(1 for _ in []) or None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="write and freeze the envelope")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, send nothing")
    args = ap.parse_args()

    with httpx.Client(base_url=BASE, timeout=120.0) as client:
        prefix, rows = build_prefix()
        prefix, rows = trim_to(prefix, rows, client, TARGET_TOKENS)
        offs = line_offsets(prefix, rows)
        p = plan(prefix, rows, offs, client)
        p["prefix_sha256"] = hashlib.sha256(prefix.encode()).hexdigest()
        p["call_plan"] = (
            ["cold", "identical", "identical", "append", "append", "append",
             "never_sent", "never_sent", "never_sent",
             "first_token", "first_token", "first_token"]
            + [f"sweep:{o['ratio']}" for o in p["offsets"] for _ in range(3)]
        )

    if args.dry_run:
        print(json.dumps({k: p[k] for k in ("prompt_tokens_of_prefix", "prompt_bytes_of_prefix",
                                            "instruction_tokens", "tail_pad_tokens", "lines",
                                            "prefix_sha256")}, indent=1))
        for o in p["offsets"]:
            print(f"ratio {o['ratio']:.1f} token {o['token_offset']:6d} byte {o['byte_offset']:7d} line {o['line']}")
        print("planned model calls:", len(p["call_plan"]))
        return 0

    if args.plan:
        fp = json.loads((CELL / "envelopes/fingerprints.json").read_text())
        inspect = json.loads((CELL / "notes/container-inspect-2026-11-04.json").read_text())[0]
        env = {
            "schema": "consonance.run/1",
            "run_id": "HL-E1-2026-11-04",
            "arm": "E1-CACHE-BOUNDARY-SWEEP",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_sha": __import__("subprocess").run(
                ["git", "rev-parse", "HEAD"], cwd=WT, capture_output=True, text=True
            ).stdout.strip(),
            "fixture_sha": "sha256:" + p["prefix_sha256"],
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
                "mismatched_tokenizer": "UNAVAILABLE - needs a second tokenizer on the same engine; "
                "substituted by the first-token rewrite and labelled, not claimed",
            },
            "fingerprints": {k: fp[k] for k in (
                "model_fingerprint", "tokenizer_fingerprint",
                "renderer_fingerprint", "engine_fingerprint")},
            "generation": {"max_tokens": 4, "temperature": 0.0, "seed": 7,
                           "chat_template_kwargs": {"enable_thinking": False}},
            "prefix": {k: p[k] for k in ("prompt_tokens_of_prefix", "prompt_bytes_of_prefix",
                                         "instruction_tokens", "tail_pad_tokens", "lines",
                                         "prefix_sha256")},
            "offsets": p["offsets"],
            "call_plan": p["call_plan"],
            "order": "controls first; sweep repetitions alternate tail-to-head, head-to-tail, tail-to-head",
            "counts_against_request_budget": True,
            "tokenize_calls_note": "/tokenize is used for offset mapping and is not a model request",
            "notes": (
                "Hypothesis: reuse falls monotonically as the first rewritten offset moves earlier. "
                "Falsifier: non-monotonic reuse, all-or-nothing reuse, or block-alignment-only dependence. "
                "cached_tokens absent is recorded as null (unknown), never 0. Expected cached ~ token offset "
                "of the rewritten line, quantised to the engine's cache block (identical repeat showed "
                "704/720, i.e. 64-token blocks)."
            ),
        }
        ENVELOPE.write_text(json.dumps(env, indent=2) + "\n")
        PREFIX_CACHE.write_text(json.dumps({"prefix": prefix, "rows": rows, "offsets": offs}) + "\n")
        print("frozen", ENVELOPE, "calls planned", len(env["call_plan"]))
        return 0

    env = json.loads(ENVELOPE.read_text())
    if env.get("retrospective"):
        raise SystemExit("envelope is retrospective; refusing")
    cap = env["budgets"]["max_calls"]
    if len(env["call_plan"]) > cap:
        raise SystemExit(f"plan {len(env['call_plan'])} exceeds cap {cap}")
    if not PREFIX_CACHE.exists():
        raise SystemExit("missing prefix cache; run --plan first")
    cached_prefix = json.loads(PREFIX_CACHE.read_text())
    if cached_prefix["prefix"] != prefix:
        raise SystemExit("prefix rebuild differs from the frozen prefix; refusing")

    ratios = [o["ratio"] for o in env["offsets"]]
    sweep = {r: [] for r in ratios}
    orders = [list(reversed(ratios)), list(ratios), list(reversed(ratios))]

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

        adapter = Adapter()
        rows_out: list[dict] = []
        salt = f"E1-{env['prefix']['prefix_sha256'][:10]}"
        step = 0

        def send(task_id: str, system: str, epoch: str, extra: dict, user: str = INSTRUCTION):
            nonlocal step
            step += 1
            msgs = [{"role": "system", "content": system},
                    {"role": "user", "content": user}]
            row = adapter.chat(msgs, max_tokens=4, temperature=0.0, seed=7,
                               run_id=env["run_id"], arm=env["arm"],
                               task_id=task_id, step=step,
                               extra={"epoch": epoch, **extra})
            rows_out.append(row)
            print(f"{step:3d} {task_id:16s} prompt={row['prompt_tokens']} "
                  f"cached={row['cached_tokens']} ttft={row['ttft_ms']}")
            return row

        # ---- controls ------------------------------------------------ #
        send("cold", prefix, "cold", {"salt": salt})
        send("identical", prefix, "warm", {"salt": salt})
        send("identical", prefix, "warm", {"salt": salt})
        send("append", prefix, "warm", {"salt": salt, "appended_tokens": env["prefix"]["tail_pad_tokens"]},
             user=INSTRUCTION + "\n\n" + TAIL_PAD)
        send("append", prefix, "warm", {"salt": salt, "appended_tokens": env["prefix"]["tail_pad_tokens"]},
             user=INSTRUCTION + "\n\n" + TAIL_PAD)
        send("append", prefix, "warm", {"salt": salt, "appended_tokens": env["prefix"]["tail_pad_tokens"]},
             user=INSTRUCTION + "\n\n" + TAIL_PAD)
        for i in range(3):
            send("never_sent", f"NEVER-SENT-{salt}-{i}\n" + prefix, "warm", {"salt": f"{salt}-{i}"})
        for i in range(3):
            send("first_token", "Z" + prefix[1:], "warm", {"salt": salt})

        # ---- sweep --------------------------------------------------- #
        by_ratio = {o["ratio"]: o for o in env["offsets"]}
        for rep, order in enumerate(orders, start=1):
            for r in order:
                o = by_ratio[r]
                rewritten, info = rewrite_at(prefix, cached_prefix["rows"],
                                            cached_prefix["offsets"], o["char_offset"])
                send(f"sweep:{r}", rewritten, "warm",
                     {**info, "ratio": r, "rep": rep,
                      "expected_token_offset": o["token_offset"]})

    ROWS.parent.mkdir(parents=True, exist_ok=True)
    with ROWS.open("w") as fh:
        for row in rows_out:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    # ---- analysis ---------------------------------------------------- #
    def get(task: str) -> list[dict]:
        return [r for r in rows_out if r["task_id"] == task]

    cold = get("cold")[0]
    ident = [cold] + get("identical")
    app = get("append")
    never = get("never_sent")
    first = get("first_token")
    p_tokens = env["prefix"]["prompt_tokens_of_prefix"]

    for r in ratios:
        sweep[r] = get(f"sweep:{r}")

    monotone_violations = []
    prev = None
    for r in sorted(ratios, reverse=True):
        vals = [x["cached_tokens"] for x in sweep[r]]
        med = statistics.median([v for v in vals if v is not None]) if any(
            v is not None for v in vals) else None
        if prev is not None and med is not None and prev is not None and med > prev:
            monotone_violations.append({"ratio": r, "median_cached": med, "earlier_offset_median": prev})
        prev = med

    analysis = {
        "schema": "typed-context-pilot.e1-analysis/2",
        "run_id": env["run_id"],
        "calls": len(rows_out),
        "prefix_tokens": p_tokens,
        "prefix_sha256": env["prefix"]["prefix_sha256"],
        "controls": {
            "identical": {
                "cached": [r["cached_tokens"] for r in ident],
                "prompt_tokens": [r["prompt_tokens"] for r in ident],
                "hits_at_least_0_9_of_prefix": [
                    (r["cached_tokens"] or 0) >= 0.9 * p_tokens for r in ident],
            },
            "append": {
                "cached": [r["cached_tokens"] for r in app],
                "prompt_tokens": [r["prompt_tokens"] for r in app],
                "appended_tokens": env["prefix"]["tail_pad_tokens"],
            },
            "never_sent": {
                "cached": [r["cached_tokens"] for r in never],
                "reported": [r["cache_usage_reported"] for r in never],
                "no_reuse": all(r["cached_tokens"] in (0, None) for r in never),
            },
            "first_token": {
                "cached": [r["cached_tokens"] for r in first],
                "no_reuse": all(r["cached_tokens"] in (0, None) for r in first),
            },
            "mismatched_tokenizer": "unavailable",
        },
        "sweep": {
            str(r): {
                "token_offset": next(o["token_offset"] for o in env["offsets"] if o["ratio"] == r),
                "byte_offset": next(o["byte_offset"] for o in env["offsets"] if o["ratio"] == r),
                "cached": [x["cached_tokens"] for x in sweep[r]],
                "prompt_tokens": [x["prompt_tokens"] for x in sweep[r]],
                "ttft_ms": [x["ttft_ms"] for x in sweep[r]],
                "median_cached": (statistics.median([x["cached_tokens"] for x in sweep[r]
                                                     if x["cached_tokens"] is not None])
                                  if any(x["cached_tokens"] is not None for x in sweep[r]) else None),
            }
            for r in ratios
        },
        "monotone_violations": monotone_violations,
        "falsifier_fired": bool(monotone_violations) or all(
            (s["median_cached"] in (None, 0)) for s in
            [{"median_cached": (statistics.median([x["cached_tokens"] for x in sweep[r]
                                                  if x["cached_tokens"] is not None])
                               if any(x["cached_tokens"] is not None for x in sweep[r]) else None)}
             for r in ratios]),
    }
    ANALYSIS.write_text(json.dumps(analysis, indent=2, sort_keys=False) + "\n")
    print(json.dumps({"calls": analysis["calls"],
                      "controls": analysis["controls"],
                      "violations": monotone_violations}, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
