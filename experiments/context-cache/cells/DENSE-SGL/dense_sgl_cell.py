#!/usr/bin/env python3
"""DENSE-SGL — live battery on the SGLang variant currently holding :8014.

This is the missing cell of the 2x2 model/engine matrix: qwen3.5-9b-nvfp4 under
the SGLang engine.  The measurement code is a clone of win_vllm_cell.py (same
corpus, same renderer, same salts 3201..3204, same four arms R/A/C/H, same
request cap discipline), so the rows are comparable row-for-row against both
the vLLM qwen9b rows (WIN-VLLM V1/V2) and the SGLang occamy rows (G3 / WIN-SGL).

Two depths:
  32k   G3's 74-turn schedule at budget 32768 -- the shared comparison band
        against WIN-VLLM's 32k battery (max_model_len 32768 was their launch
        invariant; ours is a launch choice at 65536).
  64k   G3's 148-turn schedule at budget 65536 -- available because this SGLang
        launch sets --context-length 65536, so prompts beyond 32768 are servable.

Phases (all under experiments/context-cache/.occamy.lock, one request in flight):
  gate     two identical requests; the second must report cached_tokens > 0
           (the G0 instrument gate).  Also yields the /tokenize offset.
  grid     exact-length prompts straddling a block boundary, cold + repeats.
  probe    64-grid discrimination at 1100/1164/1228/1292 (cold, rep1, rep2).
  battery  the four-arm R/A/C/H battery at 32k then 64k, truncation computed
           offline from /tokenize, no request wasted on an unservable turn.

Usage: .venv/bin/python dense_sgl_cell.py --config P1 [--phase all|gate|grid|probe|battery]
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

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
from resextract.context.render import canonical_bytes  # noqa: E402

import launch_dense_sgl as launch_variant  # noqa: E402

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
LOGS = CELL_DIR / "logs"

TOTAL_REQUEST_CAP = 950  # gate 2 + grid 22 + probe 12 + 32k ~284 + 64k 592 ~= 912
MAX_TOKENS = 4
KEEP_LAST = 2
SUMMARY_CHARS = 750
LOCK_TIMEOUT_S = 900.0

# 64-grid discrimination probe targets (from WIN-SGL) -- cached multiple of 64
# vs multiple of 128 predict different values at these lengths.
PROBE_TARGETS = (1100, 1164, 1228, 1292)

DEPTHS = (
    {"depth": "32k", "budget": 32768, "planned_turns": 74, "prompt_limit": 32736},
    {"depth": "64k", "budget": 65536, "planned_turns": 148, "prompt_limit": 65472},
)

ARMS = (
    {"arm": "R", "policy": "summarise_in_place", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3201},
    {"arm": "A", "policy": "append_note", "compaction": CompactionPolicy.APPEND_NOTE, "seed": 3202},
    {"arm": "C", "policy": "none", "compaction": None, "seed": 3203},
    {"arm": "H", "policy": "hybrid", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3204},
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def load_turns(n: int):
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = (scenario["turns"] * ((n // len(scenario["turns"])) + 1))[:n]
    assert len(turns) == n, (len(turns), n)
    return scenario["preamble"], turns


def compaction_schedule(preamble, turns, budget):
    chain = [StateNode.create(preamble, "invariant")]
    schedule = []
    for turn_no, turn in enumerate(turns, 1):
        chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
        if needs_compaction(chain, budget_tokens=budget, est_tokens=default_est_tokens):
            schedule.append(turn_no)
            chain, _ = compact(chain, CompactionPolicy.SUMMARISE_IN_PLACE, keep_last=KEEP_LAST,
                               summarizer=summarise, est_tokens=default_est_tokens)
    return schedule


def digest_prefix(messages, keep=2):
    return hashlib.sha256(canonical_bytes(messages[:keep])).hexdigest()


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_densesgl", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


HTTP = None


def get_http():
    global HTTP
    if HTTP is None:
        import httpx
        HTTP = httpx.Client(base_url=launch_variant.BASE_URL, timeout=60.0,
                            headers={"Authorization": "Bearer EMPTY"})
    return HTTP


def count_tokens(messages) -> int | None:
    try:
        r = get_http().post("/tokenize",
                            json={"model": "qwen3.5-9b", "messages": messages})
        if r.status_code != 200:
            return None
        return int(r.json()["count"])
    except Exception:
        return None


def acquire_lock(path: Path, timeout_s: float, note: str):
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
                raise TimeoutError(f"lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "DENSE-SGL", "pid": os.getpid(), "note": note,
               "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, time.monotonic() - started


def release_lock(handle, note: str) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "DENSE-SGL", "pid": os.getpid(), "note": note,
                   "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def write_json_atomic(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def make_grid_messages(target_L: int, salt: str, browser) -> list:
    """Build a 2-message prompt whose served length is ~target_L tokens."""
    sys_txt = (f"[grid {salt}] Prefix-cache boundary probe. Target prompt length {target_L} "
               f"tokens. Reply with the single word ok.")
    filler_words = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
                    "tempor incididunt ut labore et dolore magna aliqua").split()

    def build(n_words: int):
        body = " ".join(filler_words[i % len(filler_words)] for i in range(n_words))
        return [{"role": "system", "content": sys_txt},
                {"role": "user", "content": f"{salt}\n{body}"}]

    words = max(1, int((target_L - 30) * 1.3))
    msgs = build(words)
    for _ in range(12):
        count = count_tokens(msgs)
        if count is None:
            return msgs
        delta = target_L - count
        if delta == 0:
            return msgs
        if abs(delta) > 3:
            words = max(1, words + int(delta * 1.05))
            msgs = build(words)
            continue
        body = msgs[1]["content"]
        for _ in range(64):
            count = count_tokens(msgs)
            if count is None or count == target_L:
                break
            if count > target_L:
                body = body[:-1] if len(body) > 1 else body
            else:
                body = body + " x"
            msgs = [msgs[0], {"role": "user", "content": body}]
    return msgs


class Runner:
    def __init__(self, spec: dict):
        self.spec = spec
        self.client = load_chat_client().ChatClient(
            base_url=launch_variant.BASE_URL + "/v1", model=spec["served_model"])
        self.requests = 0
        self.resolved_page = resolved_page_size(spec["config_id"])
        self.existing = self._load_existing()

    def _load_existing(self) -> set:
        out = set()
        if not ROWS_PATH.exists():
            return out
        for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.add((row.get("config_id"), row.get("phase"), row.get("arm"),
                     row.get("depth"), row.get("turn"), row.get("target_L"), row.get("rep")))
        return out

    def n_rows(self) -> int:
        if not ROWS_PATH.exists():
            return 0
        return sum(1 for line in ROWS_PATH.read_text(encoding="utf-8").splitlines() if line.strip())

    def append(self, row: dict) -> None:
        with ROWS_PATH.open("a", encoding="utf-8") as h:
            h.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            h.flush()
            os.fsync(h.fileno())

    def send(self, phase: str, messages, *, salt: str, depth=None, budget=None,
             target_L=None, arm=None, turn=None, policy=None, rep=0, note="") -> dict:
        if self.n_rows() >= TOTAL_REQUEST_CAP:
            raise RuntimeError(f"request cap reached: {self.n_rows()}/{TOTAL_REQUEST_CAP}")
        prompt, cached, completion, ttft, wall, status, text = self.client.chat(
            messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=240.0)
        self.requests += 1
        spec = self.spec
        row = {
            "unit": "DENSE-SGL",
            "cell": f"DENSE-SGL/{spec['config_id']}/{phase}",
            "phase": phase,
            "depth": depth,
            "budget_tokens": budget,
            "arm": arm,
            "policy": policy,
            "turn": turn,
            "salt": salt,
            "target_L": target_L,
            "rep": rep,
            "prompt_tokens": prompt,
            "cached_tokens": cached,
            "uncached": max(0, prompt - cached),
            "completion_tokens": completion,
            "ttft_ms": round(ttft, 3),
            "wall_ms": round(wall, 3),
            "status": status,
            "response_chars": len(text or ""),
            "prefix_sha256": digest_prefix(messages, keep=2),
            "messages": len(messages),
            "chars": sum(len(str(m.get("content") or "")) for m in messages),
            "request_index": self.n_rows() + 1,
            "ts_utc": utc_now(),
            "note": note,
            "stack": spec["stack"],
            "config_id": spec["config_id"],
            "config_sha256": spec["config_sha256"],
            "quant": spec["quantization"],
            "served_model": spec["served_model"],
            "context_length": spec["context_length"],
        }
        self.append(row)
        print(f"ROW {phase} cfg={spec['config_id']} arm={arm} turn={turn} L={prompt} "
              f"cached={cached} uncached={row['uncached']} rep={rep} status={status} "
              f"wall={row['wall_ms']}ms total={self.n_rows()}", flush=True)
        if status != 200:
            row["error"] = (text or "")[:400]
        return row


def resolved_page_size(config_id: str) -> int:
    # launch.json records server_info_path; the actual page_size lives there.
    data = json.loads((LOGS / f"{config_id}-launch.json").read_text())
    si_path = data.get("server_info_path") or data.get("server_info")
    server_info: dict = {}
    if isinstance(si_path, str):
        p = Path(si_path)
        if not p.is_absolute():
            p = REPO / p
        if p.exists():
            try:
                server_info = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                server_info = {}
    elif isinstance(si_path, dict):
        server_info = si_path
    ps = server_info.get("page_size")
    if isinstance(ps, int):
        return ps
    text = json.dumps(server_info)
    m = re.search(r'"page_size"\s*:\s*(\d+)', text)
    if m:
        return int(m.group(1))
    # fallback: SGLang default page size
    return 64


def phase_probe(runner: Runner) -> list:
    out = []
    for idx, target in enumerate(PROBE_TARGETS):
        salt = make_salt(7400 + idx)
        msgs = make_grid_messages(target, salt, None)
        cold = runner.send("grid", msgs, salt=salt, target_L=target, rep=0, note="probe-cold")
        rep1 = runner.send("grid", msgs, salt=salt, target_L=target, rep=1, note="probe-rep1")
        rep2 = runner.send("grid", msgs, salt=salt, target_L=target, rep=2, note="probe-rep2")
        out.append({"target_L": target, "L": cold["prompt_tokens"],
                    "cold_cached": cold["cached_tokens"],
                    "rep1_cached": rep1["cached_tokens"],
                    "rep2_cached": rep2["cached_tokens"]})
    return out


def build_battery_plan(offset: int, budget: int, planned_turns: int, prompt_limit: int) -> dict:
    preamble, turns = load_turns(planned_turns)
    schedule = compaction_schedule(preamble, turns, budget)
    salts = {s["arm"]: make_salt(int(s["seed"])) for s in ARMS}
    per_arm = {}
    per_turn_L = {}
    for spec in ARMS:
        arm = str(spec["arm"])
        base = spec["compaction"]
        salt = salts[arm]
        chain = [StateNode.create(preamble, "invariant")]
        crossed = False
        msgs_by_turn = []
        lens = []
        for turn_no, turn in enumerate(turns, 1):
            chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
            scheduled = bool(base is not None and turn_no in schedule)
            if arm == "H" and scheduled:
                crossed = True
            if arm == "A" and scheduled:
                pol = CompactionPolicy.APPEND_NOTE
            elif arm == "H":
                pol = CompactionPolicy.APPEND_NOTE if not crossed else CompactionPolicy.SUMMARISE_IN_PLACE
            else:
                pol = base
            if scheduled and pol is not None:
                chain, _ = compact(chain, pol, keep_last=KEEP_LAST, summarizer=summarise,
                                   est_tokens=default_est_tokens)
            messages = render(RenderPolicy.NAIVE_APPEND, chain, preamble=preamble,
                              volatile={}, salt=salt)
            msgs_by_turn.append(messages)
            lens.append(count_tokens(messages))
        per_arm[arm] = {"lens": lens, "messages": msgs_by_turn, "salt": salt}
        per_turn_L[arm] = lens
    ok_turns = []
    for t in range(planned_turns):
        vals = [per_turn_L[a][t] for a in per_turn_L]
        if any(v is None for v in vals):
            ok_turns.append(None)
        else:
            ok_turns.append(max(vals) + offset)
    n_servable = 0
    for t, L in enumerate(ok_turns, 1):
        if L is not None and L <= prompt_limit:
            n_servable = t
        else:
            break
    plan = {
        "unit": "DENSE-SGL",
        "planned_turns": planned_turns,
        "servable_turns": n_servable,
        "prompt_limit": prompt_limit,
        "context_length": 65536,
        "budget": budget,
        "offset": offset,
        "per_turn_max_L": ok_turns,
        "schedule": schedule,
        "salts": salts,
        "reason": (f"turns {n_servable + 1}..{planned_turns} dropped: rendered prompt would "
                   f"exceed prompt_limit {prompt_limit}"),
    }
    write_json_atomic(LOGS / f"battery-plan-{budget}.json", plan)
    print(f"battery plan budget={budget}: servable_turns={n_servable}/{planned_turns} "
          f"L@N={ok_turns[n_servable - 1] if n_servable else None}", flush=True)
    return {"plan": plan, "per_arm": per_arm, "turns": turns, "preamble": preamble}


def phase_battery(runner: Runner, offset: int) -> list:
    plans = []
    for depth in DEPTHS:
        built = build_battery_plan(offset, depth["budget"], depth["planned_turns"],
                                   depth["prompt_limit"])
        plan = built["plan"]
        n = plan["servable_turns"]
        for spec in ARMS:
            arm = str(spec["arm"])
            msgs_by_turn = built["per_arm"][arm]["messages"]
            salt = built["per_arm"][arm]["salt"]
            for turn_no in range(1, n + 1):
                messages = msgs_by_turn[turn_no - 1]
                row = runner.send("battery", messages, salt=salt, arm=arm, turn=turn_no,
                                  policy=str(spec["policy"]), rep=0, depth=depth["depth"],
                                  budget=depth["budget"], note=f"turns_total={n}")
                if row["status"] != 200:
                    print(f"BATTERY ERROR arm={arm} turn={turn_no} status={row['status']} "
                          f"{row.get('error', '')[:200]}", flush=True)
                    if row["status"] in (400, 404):
                        break
        plans.append({"depth": depth["depth"], "budget": depth["budget"],
                      "servable_turns": n, "planned_turns": depth["planned_turns"],
                      "schedule_len": len(plan["schedule"])})
    return plans


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, choices=sorted(launch_variant.CONFIGS))
    ap.add_argument("--phase", default="all",
                    choices=["all", "gate", "grid", "probe", "battery"])
    args = ap.parse_args()

    spec = launch_variant.CONFIGS[args.config].copy()
    spec["config_sha256"] = hashlib.sha256(
        json.dumps(launch_variant.variant_overrides(spec), sort_keys=True).encode()).hexdigest()
    spec["stack"] = "sglang"

    launch_log = LOGS / f"{args.config}-launch.json"
    if not launch_log.exists():
        print(f"REFUSE: no launch record at {launch_log}", flush=True)
        return 4
    launched = json.loads(launch_log.read_text())
    if not launched.get("health", {}).get("ok"):
        print(f"REFUSE: {args.config} did not launch (health={launched.get('health')})",
              flush=True)
        return 4

    gate_messages = [
        {"role": "system", "content": "You are a cache-probe assistant. Answer in one word."},
        {"role": "user", "content": " ".join(["retention"] * 3100)},
    ]
    runner = Runner(spec)
    started = time.monotonic()
    handle = None
    try:
        handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S, f"{args.config} {args.phase}")
        print(f"lock: acquired after {waited:.1f}s", flush=True)
        summary = {"unit": "DENSE-SGL", "config_id": args.config, "phase": args.phase,
                   "lock_wait_s": round(waited, 1), "started_utc": utc_now()}

        if args.phase in ("all", "gate"):
            tok = count_tokens(gate_messages)
            r1 = runner.send("gate", gate_messages, salt="gate-dense-sgl", rep=0,
                             note="identical-1")
            offset = (r1["prompt_tokens"] - tok) if tok else 0
            r2 = runner.send("gate", gate_messages, salt="gate-dense-sgl", rep=1,
                             note="identical-2")
            gate = {"gate_pass": bool(r2["cached_tokens"] > 0), "tokenize_count": tok,
                    "served_prompt_tokens": r1["prompt_tokens"], "offset": offset,
                    "rep0_cached": r1["cached_tokens"], "rep1_cached": r2["cached_tokens"]}
            summary["gate"] = gate
            summary["offset"] = offset
            print(f"GATE {args.config}: pass={gate['gate_pass']} offset={offset} "
                  f"rep1_cached={gate['rep1_cached']}", flush=True)
            if not gate["gate_pass"]:
                summary["verdict"] = "instrument-unavailable"
                write_json_atomic(LOGS / f"{args.config}-gate.json", summary)
                return 0
        else:
            gate_file = LOGS / f"{args.config}-gate.json"
            if gate_file.exists():
                offset = json.loads(gate_file.read_text()).get("offset", 0)
            else:
                offset = 0

        if args.phase in ("all", "grid"):
            # SGLang 64-grid boundary probes (from WIN-SGL run_sgl_cell)
            targets = (500, 1000, 63, 64, 65, 127, 128, 129, 191, 192, 193)
            out = []
            for idx, target in enumerate(targets):
                salt = make_salt(7100 + idx)
                msgs = make_grid_messages(target, salt, None)
                cold = runner.send("grid", msgs, salt=salt, target_L=target, rep=0, note="cold")
                rep = runner.send("grid", msgs, salt=salt, target_L=target, rep=1, note="repeat-1")
                out.append({"target_L": target, "L": cold["prompt_tokens"],
                            "cold_cached": cold["cached_tokens"], "cached": rep["cached_tokens"],
                            "status": rep["status"]})
            summary["grid"] = out

        if args.phase in ("all", "probe"):
            summary["probe"] = phase_probe(runner)

        if args.phase in ("all", "battery"):
            summary["battery_plans"] = phase_battery(runner, offset)

        summary["requests_this_run"] = runner.requests
        summary["rows_total"] = runner.n_rows()
        summary["elapsed_s"] = round(time.monotonic() - started, 1)
        summary["finished_utc"] = utc_now()
        write_json_atomic(LOGS / f"{args.config}-summary.json", summary)
        print(f"DONE {args.config} phase={args.phase} requests={runner.requests} "
              f"rows={runner.n_rows()} elapsed={summary['elapsed_s']}s", flush=True)
        return 0
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
        return 1
    finally:
        if handle is not None:
            release_lock(handle, f"{args.config} {args.phase}")


if __name__ == "__main__":
    raise SystemExit(main())
