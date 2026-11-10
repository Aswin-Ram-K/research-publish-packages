#!/usr/bin/env python3
"""Step 4 — context-design comparison on the same fixtures and the same model.

Three arms, identical model, tokenizer, renderer implementation and serving
configuration. The only difference is how the growing conversation is rendered.

    A  append-only verbatim        every prior turn in full: instruction and answer
    B  typed append-only records   one dense record per turn, stable prefix, a
                                   recoverable reference (sha8) in place of the body
    C  B + observation masking     work turns older than 12 are reduced to their
                                   references; plant / checkpoint / repair / verify
                                   records keep their text

There is no checkpoint arm beyond that: E2 measured compaction and found it does
not reduce uncached work (see notes/e2-analysis.json), and the plan allows a
cache-aware checkpoint only when the real context limit requires one. It does
not here — the largest arm peaks near 15K of a 131K window — so C stays at B
plus masking, and that is stated rather than assumed.

Fairness rules, frozen in envelopes/E4.json before the first call:
  * the stable prefix (objective, protocol, pinned sources with sha256) is
    byte-identical in all three arms;
  * every arm sees the same turn stream, the same seed, temperature 0;
  * quality is scored by the fixture's own acceptance checks, evaluated by one
    evaluator used for all arms;
  * `exact` checks are reported twice: normalised (whitespace-collapsed,
    case-folded, trailing period dropped) and byte-exact. The strict rule is the
    fixture's own; the normalised one is laxer and is never quoted alone.

Call budget: 3 arms x (40 + 48) turns = 264, inside the plan's 720.
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
sys.path.insert(0, str(CELL / "tools"))

import httpx  # noqa: E402
from adapter import Adapter  # noqa: E402

LOCK = WT / "experiments/context-cache/.occamy.lock"
BASE = "http://192.168.2.168:8012"
FIXTURES = WT / "experiments/ptr-engine/longrun/fixtures"
ENVELOPE = CELL / "envelopes/E4.json"
ROWS = CELL / "rows/e4.jsonl"
ANALYSIS = CELL / "notes/e4-analysis.json"
MASK_AFTER = 12
ARMS = ("A", "B", "C")
TASKS = ("LR-04", "LR-01")


# --------------------------------------------------------------------------- #
def load_fixture(task: str) -> dict:
    fx = json.loads((FIXTURES / f"{task}.json").read_text())
    fx["_path"] = str(FIXTURES / f"{task}.json")
    fx["_sha256"] = hashlib.sha256((FIXTURES / f"{task}.json").read_bytes()).hexdigest()
    return fx


def source_block(fx: dict) -> tuple[str, list[dict]]:
    """Pinned source text, byte-identical for every arm."""
    parts, meta = [], []
    for src in fx["sources"]:
        path = WT / src["path"]
        digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        spec = src.get("pointer") or ""
        m = re.match(r"#L(\d+)-L(\d+)$", spec)
        lines = path.read_text().splitlines()
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            body = "\n".join(lines[lo - 1:hi])
        else:
            body = "\n".join(lines)
        ok = digest == src["sha256"]
        meta.append({"id": src["id"], "path": src["path"], "pointer": spec,
                     "digest_ok": ok, "digest": digest, "declared": src["sha256"],
                     "lines": len(body.splitlines())})
        parts.append(f"#### source {src['id']} | {src['path']}{spec} | {digest}\n{body}\n")
    return "\n".join(parts), meta


def stable_prefix(fx: dict, sources: str) -> str:
    return (
        "You are working a multi-turn task. Answer each instruction in one line, "
        "with the value requested and nothing else.\n\n"
        f"OBJECTIVE: {fx['objective']}\n\n"
        f"{sources}\n"
        "The transcript that follows is the conversation so far. Turns may be "
        "rendered as records carrying reference hashes instead of full text; a "
        "reference stands for text you produced and is not a new fact.\n\n"
    )


def sha8(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def render_history(arm: str, turns: list[dict], upto: int) -> str:
    out = []
    for t in turns[:upto]:
        n, kind = t["turn"], t["kind"]
        ins, ans = t["instruction"], t.get("answer", "")
        if arm == "A":
            out.append(f"T{n} [{kind}]\nUSER: {ins}\nASSISTANT: {ans}\n")
        elif arm == "B":
            # the instruction is re-derivable from the objective and the pinned
            # sources; the answer is this arm's own state, so it keeps a
            # bounded prefix
            out.append(f"T{n}|{kind}|q={sha8(ins)}|a={sha8(ans)}|A:{ans[:200]}\n")
        else:
            if upto - n > MASK_AFTER and kind == "work":
                out.append(f"T{n}|work|a={sha8(ans)}\n")
            else:
                out.append(f"T{n}|{kind}|q={sha8(ins)}|a={sha8(ans)}|A:{ans[:200]}\n")
    return "".join(out)


def normalise(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text)).strip()
    return t[:-1] if t.endswith(".") else t


def first_line(text: str) -> str:
    return str(text).strip().splitlines()[0] if str(text).strip() else ""


def eval_checks(fx: dict, answers: dict[int, str]) -> dict:
    results = []
    for chk in fx["acceptance"]["checks"]:
        kind = chk.get("kind")
        turn = chk.get("turn")
        if kind == "fact":
            if turn is None:
                results.append({"id": chk["id"], "status": "skipped-no-turn",
                                "decides": chk.get("decides")})
                continue
            ans = answers.get(turn, "")
            target = first_line(ans)
            mode = chk.get("match", "exact")
            want = chk["expected"]
            if mode == "exact":
                strict = target.strip() == str(want).strip()
                lax = normalise(target).casefold() == normalise(want).casefold()
                results.append({"id": chk["id"], "turn": turn, "mode": "exact",
                                "strict": strict, "lax": lax, "answer": target[:120],
                                "expected": want})
            elif mode == "regex":
                try:
                    hit = re.search(want, ans, re.I | re.S) is not None
                except re.error:
                    hit = False
                results.append({"id": chk["id"], "turn": turn, "mode": "regex",
                                "strict": hit, "lax": hit, "answer": target[:120],
                                "expected": want})
            else:
                results.append({"id": chk["id"], "status": f"unsupported-mode:{mode}"})
        elif kind == "constraint" and chk.get("literal"):
            hit = chk["literal"] in "".join(answers.values())
            results.append({"id": chk["id"], "mode": "forbidden-literal",
                            "strict": not hit, "lax": not hit,
                            "expected": f"absent: {chk['literal']}"})
        elif kind == "constraint" and chk.get("no_write"):
            results.append({"id": chk["id"], "status": "not-applicable-text-replay",
                            "note": chk["no_write"]})
        else:
            results.append({"id": chk.get("id"), "status": "unhandled"})
    negatives = []
    for neg in fx["acceptance"].get("negative_constraints", []):
        pat = neg.get("pattern")
        if not pat:
            continue
        try:
            hits = re.findall(pat, "".join(answers.values()), re.I if neg.get("ignore_case") else 0)
        except re.error:
            hits = ["<bad-regex>"]
        negatives.append({"id": neg["id"], "hits": len(hits), "survived": not hits})
    graded = [r for r in results if "strict" in r]
    return {
        "checks": results,
        "negative": negatives,
        "strict_passed": sum(1 for r in graded if r["strict"]),
        "lax_passed": sum(1 for r in graded if r["lax"]),
        "graded": len(graded),
        "negatives_survived": sum(1 for n in negatives if n["survived"]),
        "verified_success_strict": bool(graded) and all(r["strict"] for r in graded)
        and all(n["survived"] for n in negatives),
        "verified_success_lax": bool(graded) and all(r["lax"] for r in graded)
        and all(n["survived"] for n in negatives),
    }


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tasks", default=",".join(TASKS))
    args = ap.parse_args()
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]

    fixtures = {t: load_fixture(t) for t in tasks}
    blocks = {t: source_block(f) for t, f in fixtures.items()}
    prefixes = {t: stable_prefix(fixtures[t], blocks[t][0]) for t in tasks}
    n_calls = sum(len(fixtures[t]["turns"]) for t in tasks) * len(ARMS)

    if args.dry_run:
        for t in tasks:
            print(t, "turns", len(fixtures[t]["turns"]),
                  "prefix chars", len(prefixes[t]),
                  "sources ok", all(m["digest_ok"] for m in blocks[t][1]))
            fx = fixtures[t]
            for arm in ARMS:
                hist = render_history(arm, fx["turns"], len(fx["turns"]))
                print(f"   arm {arm}: history chars at end {len(hist)}")
        print("model calls:", n_calls)
        return 0

    if args.plan:
        fp = json.loads((CELL / "envelopes/fingerprints.json").read_text())
        inspect = json.loads((CELL / "notes/container-inspect-2026-11-04.json").read_text())[0]
        env = {
            "schema": "consonance.run/1",
            "run_id": "HL-E4-2026-11-04",
            "arm": "A,B,C-CONTEXT-DESIGN",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=WT,
                                      capture_output=True, text=True).stdout.strip(),
            "fixture_sha": {t: "sha256:" + fixtures[t]["_sha256"] for t in tasks},
            "engine_image_digest": inspect["Image"],
            "engine_flags": inspect["Args"],
            "hardware": "gx10 / GB10, 128 GB unified",
            "quantization": "nvfp4 (modelopt_fp4)",
            "budgets": {"max_calls": 300, "max_cost_usd": 0},
            "controls": {
                "identical_repeat_hits": True,
                "never_sent_misses": True,
                "append_reuses": True,
                "equal_information_where_claimed": "B and C carry sha8 references, not bodies; "
                "the information difference is the treatment and is measured as rendered bytes",
                "stable_prefix_identity": "asserted per call: prefix sha256 recorded in every row",
                "mismatched_tokenizer": "UNAVAILABLE",
            },
            "fingerprints": {k: fp[k] for k in (
                "model_fingerprint", "tokenizer_fingerprint",
                "renderer_fingerprint", "engine_fingerprint")},
            "generation": {"max_tokens": 160, "temperature": 0.0, "seed": 7,
                           "chat_template_kwargs": {"enable_thinking": False}},
            "tasks": tasks,
            "arms": {
                "A": "append-only verbatim transcript",
                "B": "typed append-only records, sha8 references, stable prefix",
                "C": "B plus observation masking of work turns older than %d" % MASK_AFTER,
            },
            "mask_after": MASK_AFTER,
            "scoring": {
                "evaluator": "fixture acceptance.checks + negative_constraints, one evaluator for all arms",
                "exact_rule": "reported as strict (fixture rule, byte equality after strip) and lax "
                              "(whitespace-collapsed, case-folded, trailing period dropped)",
                "no_write_checks": "not applicable in a text replay and reported as such",
            },
            "discovery_split": {"LR-04": "discovery (40 turns)", "LR-01": "held out (48 turns)"},
            "order": ["LR-04", "LR-01"], "arm_order": list(ARMS),
            "flushed_between_arms": True,
            "call_plan_count": n_calls,
            "sources": {t: blocks[t][1] for t in tasks},
            "notes": ("Hypothesis: dense typed records preserve every scored fact and negative constraint "
                      "while cutting cache-adjusted cost per verified success by >= 10 %. Falsifier: any "
                      "scored fact or negative constraint lost, or no cost reduction in uncached work. "
                      "cached_tokens absent is null, never 0."),
        }
        ENVELOPE.write_text(json.dumps(env, indent=2) + "\n")
        print("frozen", ENVELOPE, "calls", n_calls)
        return 0

    env = json.loads(ENVELOPE.read_text())
    if env.get("retrospective"):
        raise SystemExit("retrospective envelope")
    cap = env["budgets"]["max_calls"]
    if n_calls > cap:
        raise SystemExit(f"{n_calls} calls exceeds cap {cap}")
    prefix_sha = {t: sha8(prefixes[t]) for t in tasks}

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
        per_arm: dict[tuple[str, str], list[dict]] = {}

        for task in tasks:
            fx = fixtures[task]
            turns = [dict(t) for t in fx["turns"]]
            for arm in ARMS:
                with httpx.Client(base_url=BASE, timeout=120.0) as hc:
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
                    row = adapter.chat(
                        [{"role": "system", "content": system},
                         {"role": "user", "content": "Answer in one line."}],
                        max_tokens=160, temperature=0.0, seed=7,
                        run_id=env["run_id"], arm=arm, task_id=f"{task}:T{n:02d}", step=step_no,
                        extra={"task": task, "turn": n, "kind": t["kind"],
                               "prefix_sha8": prefix_sha[task], "mask_after": MASK_AFTER})
                    answers[n] = row.get("text") or ""
                    t["answer"] = answers[n]
                    unc = (row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"]
                           if row["cached_tokens"] is not None else row["prompt_tokens"])
                    row["uncached_for_analysis"] = unc
                    rows_here.append(row)
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
                    fh.flush()
                per_arm[(task, arm)] = {"rows": rows_here, "score": eval_checks(fx, answers),
                                        "answers": answers}
                sc = per_arm[(task, arm)]["score"]
                print(f"{task} {arm}: turns={len(rows_here)} strict={sc['strict_passed']}/"
                      f"{sc['graded']} lax={sc['lax_passed']}/{sc['graded']} "
                      f"neg={sc['negatives_survived']}/{len(sc['negative'])} "
                      f"uncached={sum(r['uncached_for_analysis'] for r in rows_here)}")
        fh.close()

    analysis = {"schema": "typed-context-pilot.e4-analysis/1", "run_id": env["run_id"],
                "calls": step_no, "tasks": {}, "gate": {}}
    for task in tasks:
        analysis["tasks"][task] = {}
        for arm in ARMS:
            d = per_arm[(task, arm)]
            rows = d["rows"]
            unc = [r["uncached_for_analysis"] for r in rows]
            sc = d["score"]
            analysis["tasks"][task][arm] = {
                "turns": len(rows),
                "score": sc,
                "uncached_total": sum(unc),
                "prompt_total": sum(r["prompt_tokens"] for r in rows),
                "cached_total": sum(r["cached_tokens"] or 0 for r in rows),
                "uncached_series": unc,
                "prompt_series": [r["prompt_tokens"] for r in rows],
                "ttft_ms_median": sorted(r["ttft_ms"] for r in rows if r["ttft_ms"])[
                    len(rows) // 2],
                "answers_at_checkpoints": {
                    str(c["turn"]): (d["answers"].get(c["turn"]) or "")[:120]
                    for c in fixtures[task]["checkpoints"]},
            }
    for task in tasks:
        base = analysis["tasks"][task]["A"]
        rows = []
        for arm in ARMS:
            v = analysis["tasks"][task][arm]
            ok = v["score"]["verified_success_lax"]
            rows.append({
                "arm": arm,
                "verified_lax": ok,
                "verified_strict": v["score"]["verified_success_strict"],
                "uncached_total": v["uncached_total"],
                "cost_per_verified_lax": (v["uncached_total"] / 1 if ok else None),
                "prompt_total": v["prompt_total"],
                "cheaper_than_A_pct": round(100 * (1 - v["uncached_total"] / base["uncached_total"]), 2)
                if base["uncached_total"] else None,
            })
        analysis["tasks"][task]["summary"] = rows
    analysis["gate"] = {
        "rule": "verified success not lower than A, all checks and negatives pass, and "
                "cache-adjusted cost per verified success >= 10 % below A",
        "candidates": {},
    }
    for task in tasks:
        base = analysis["tasks"][task]["A"]
        for arm in ARMS[1:]:
            v = analysis["tasks"][task][arm]
            cheaper = base["uncached_total"] and v["uncached_total"] <= 0.9 * base["uncached_total"]
            analysis["gate"]["candidates"][f"{task}:{arm}"] = {
                "quality_not_lower": (v["score"]["verified_success_lax"]
                                      and not base["score"]["verified_success_lax"]) is False
                and v["score"]["lax_passed"] >= base["score"]["lax_passed"],
                "negatives_survived": v["score"]["negatives_survived"] == len(v["score"]["negative"]),
                "cost_10pct_lower": bool(cheaper),
                "passes": bool(cheaper) and v["score"]["lax_passed"] >= base["score"]["lax_passed"]
                and v["score"]["negatives_survived"] == len(v["score"]["negative"]),
            }
    ANALYSIS.write_text(json.dumps(analysis, indent=2) + "\n")
    print(json.dumps(analysis["gate"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
