#!/usr/bin/env python3
"""SYS-OPT round 1 (V1) — one optimised prompt version, measured on BOTH models.

Substrate: production `occamy-1.0` on SGLang `:8012` (config **O1**) and
`qwen3.5-9b` on vLLM `:8014` (config **O4**). No container is started, stopped
or restarted by this cell.

The prompt is ONE artefact: the same rendered bytes are sent to both models,
per (arm, turn). Only the served endpoint differs.

Arms (V1): P0 whole-context resend (reference), P1 pointer index + append-only
newest delta (HEADLINE, per Amendment A1/A2), P3 mid-context edit control
(reference). P2 is withdrawn (VERSIONS.md A1.2) and is not run.

V1's single change (VERSIONS.md Amendment A2): `pointer_block.quote_tokens`
0 -> 40. Every pointer entry gains a 40-token verbatim head of its span, so the
P1 form can quote span text instead of only stating span length + sha8.

Modes
    python3 sysopt_r1.py --freeze-quality   # write state/sys-opt-quality.json
    python3 sysopt_r1.py --round            # 2 models x 3 arms x 71 turns + quality
    python3 sysopt_r1.py --emit             # score + state/sys-opt-v1.json
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path("/home/zer0null/reserach extarctor")
HERE = Path(__file__).resolve().parent
RENDERER_PATH = REPO / "experiments" / "context-cache" / "cells" / "VLLM-CELL" / "vllm_cell.py"
R2P = REPO / "experiments" / "context-cache" / "cells" / "R2-PROMPT"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
STATE = REPO / "state"
QUALITY_PATH = STATE / "sys-opt-quality.json"

SALT = "sysopt-r1-20261024T12:30Z-a1"
VERSION = "V1"
QUOTE_TOKENS = 40
QUOTE_CHARS = QUOTE_TOKENS * 4          # ~40 tokens at the observed ~4 chars/token
TURNS = 71
ARMS = ("P0", "P1", "P3")
MAX_TOKENS = 8
EDIT_TURN = 40
EDIT_TARGET = 20
QUALITY_N = 20
QUALITY_MAX_TOKENS = 48
QUALITY_WINDOW = 32
COLD_RETRIES = 3
BOOTSTRAP_B = 10000
BOOTSTRAP_SEED = 20251024

MODELS = {
    "moe": {"setup": "O1", "url": "http://192.168.2.168:8012/v1", "model": "occamy-1.0",
            "engine": "sglang", "grid": 64},
    "dense": {"setup": "O4", "url": "http://192.168.2.168:8014/v1", "model": "qwen3.5-9b",
              "engine": "vllm", "grid": 1088},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# renderer: the frozen lineage renderer + the ONE V1 change
# --------------------------------------------------------------------------- #
def load_renderer():
    spec = importlib.util.spec_from_file_location("renderer_sysopt", RENDERER_PATH)
    rc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = rc
    spec.loader.exec_module(rc)
    # Fresh salt: a new sample, so no cache warmed by the R2-PROMPT pass can
    # replay. Content (delta stream, scaffold, questions) is unchanged.
    rc.SCAFFOLD = rc.SCAFFOLD + "RUN-SALT: %s\n" % SALT
    rc.SYSOPT_QUOTE_CHARS = QUOTE_CHARS

    def pointer_index(up_to_turn, compacted=False, quote_chars=QUOTE_CHARS):
        """`id | span | sha8 | summary | quote` — V1 adds the verbatim head."""
        lines = ["id | span | sha8 | summary | quote"]
        for t in range(1, up_to_turn + 1):
            block = rc.delta_block(t)
            if compacted and t % rc.SUMMARY_EVERY == 0:
                lines.append(rc.folded_summary(t, max(1, t - rc.SUMMARY_EVERY + 1)))
                continue
            row = "t%03d | %d | %s | %s" % (t, len(block), rc.sha8(block), rc.summarise(block))
            if quote_chars:
                row += " | q:" + " ".join(block.split())[:quote_chars]
            lines.append(row)
        return "\n".join(lines)

    rc.pointer_index = pointer_index
    return rc


def p0_text(rc, turn: int) -> str:
    return rc.render("R", turn)[0]["content"]


def p1_text(rc, turn: int) -> str:
    return rc.render("A", turn)[0]["content"]


def p3_text(rc, turn: int) -> str:
    base = p1_text(rc, turn)
    if turn < EDIT_TURN:
        return base + "\nMODE[edit-policy; revised=0]"
    lines = rc.pointer_index(turn - 1).splitlines()
    original = next(l for l in lines if l.startswith("t%03d |" % EDIT_TARGET))
    parts = original.split(" | ", 4)
    new = [parts[0], parts[1], rc.sha8("EDITED::" + parts[0]),
           "[rev2] " + (" ".join(parts[3].split()))[:80]]
    if len(parts) > 4:
        new.append(parts[4])
    if original not in base:
        raise SystemExit("P3 EDIT ANCHOR MISSING at turn %d" % turn)
    return base.replace(original, " | ".join(new), 1) + "\nMODE[edit-policy; revised=1]"


def arm_text(rc, arm: str, turn: int) -> str:
    if arm == "P0":
        return p0_text(rc, turn)
    if arm == "P1":
        return p1_text(rc, turn)
    if arm == "P3":
        return p3_text(rc, turn)
    raise ValueError("unknown arm %r" % (arm,))


def arm_messages(rc, arm: str, turn: int) -> list[dict]:
    return [{"role": "user", "content": arm_text(rc, arm, turn)}]


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def post(base_url: str, model: str, messages: list[dict], max_tokens: int = MAX_TOKENS) -> dict:
    payload = {"model": model, "messages": messages, "max_tokens": int(max_tokens),
               "temperature": 0.0, "chat_template_kwargs": {"enable_thinking": False},
               "stream": False}
    started = time.perf_counter()
    last = None
    for attempt in (1, 2):
        try:
            resp = requests.post(base_url.rstrip("/") + "/chat/completions", json=payload, timeout=240)
            wall_ms = (time.perf_counter() - started) * 1000.0
            try:
                body = resp.json()
            except Exception:
                body = None
            usage = (body or {}).get("usage") if isinstance(body, dict) else None
            details = (usage or {}).get("prompt_tokens_details") if isinstance(usage, dict) else None
            cached = details.get("cached_tokens") if isinstance(details, dict) else None
            prompt = usage.get("prompt_tokens") if isinstance(usage, dict) else None
            text = ""
            if isinstance(body, dict):
                choices = body.get("choices") or []
                if choices:
                    text = ((choices[0] or {}).get("message") or {}).get("content") or ""
            return {"http_status": int(resp.status_code),
                    "prompt_tokens": None if prompt is None else int(prompt),
                    "cached_tokens": None if cached is None else int(cached),
                    "details_present": isinstance(details, dict), "text": text,
                    "wall_ms": round(wall_ms, 3)}
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.0 + attempt)
    raise SystemExit("TRANSPORT FAILURE after 2 attempts: %r" % (last,))


def sample_prefix_hits(base_url: str) -> float | None:
    """vLLM prefix-cache hit counter, in token units (used only when details are null)."""
    try:
        text = requests.get(base_url.rstrip("/").rsplit("/v1", 1)[0] + "/metrics", timeout=20).text
    except Exception:
        return None
    total, found = 0.0, False
    for line in text.splitlines():
        if line.startswith("vllm:prefix_cache_hits_total"):
            try:
                total += float(line.split()[1])
                found = True
            except (IndexError, ValueError):
                continue
    return total if found else None


def measured_post(base_url: str, model: str, messages: list, counter_mode: bool) -> dict:
    before = sample_prefix_hits(base_url) if counter_mode else None
    res = post(base_url, model, messages)
    if counter_mode:
        after = sample_prefix_hits(base_url)
        if None not in (before, after):
            derived = int(round(after - before))
            res["cached_tokens"] = derived if derived >= 0 else None
            res["cached_source"] = "vllm:prefix_cache_hits_total delta"
        else:
            res["cached_source"] = "counter unavailable"
    else:
        res["cached_source"] = ("prompt_tokens_details.cached_tokens"
                                if res["details_present"] else "details absent")
    return res


def equalise_warmup(base_url: str, model: str, messages: list[dict]) -> dict:
    c1 = post(base_url, model, messages)
    c2 = post(base_url, model, messages)
    return {"call1_cached": c1["cached_tokens"], "call2_cached": c2["cached_tokens"],
            "prompt_tokens": c2["prompt_tokens"] or c1["prompt_tokens"]}


def acquire_lock(unit: str, timeout_s: float = 900.0):
    import fcntl
    handle = open(LOCK_PATH, "a+")
    deadline = time.time() + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            handle.seek(0)
            handle.truncate()
            handle.write("%s %s %s\n" % (unit, utc_now(), __import__("os").getpid()))
            handle.flush()
            return handle
        except BlockingIOError:
            if time.time() > deadline:
                raise SystemExit("LOCK TIMEOUT: %s held by another unit" % LOCK_PATH)
            time.sleep(2.0)


def release_lock(handle) -> None:
    import fcntl
    try:
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


# --------------------------------------------------------------------------- #
# quality: frozen 20 questions, keys and programmatic grader
# --------------------------------------------------------------------------- #
def quality_questions(rc) -> list[str]:
    return ["Q%02d: quote the span of delta t=%03d and state its sha8 prefix." % (t, t * 3)
            for t in range(1, QUALITY_N + 1)]


def quality_key(rc, t: int) -> dict:
    block = rc.delta_block(t)
    flat = " ".join(block.split())
    return {"t": t, "sha8": rc.sha8(block), "span_len": len(block), "flat_head": flat[:240]}


GRADER_SOURCE = '''\
def grade(answer_text, key):
    import json
    ans = answer_text
    try:
        obj = json.loads(answer_text[answer_text.index("{"): answer_text.rindex("}") + 1])
        ans = str(obj.get("answer", ""))
    except Exception:
        pass
    flat = " ".join(ans.split())
    sha_ok = key["sha8"].lower() in flat.lower()
    head = key["flat_head"]
    span_ok = False
    for n in (60, 40, 30):
        if any(head[i:i + n] in flat for i in range(0, max(1, len(head) - n))):
            span_ok = True
            break
    return {"sha8_ok": sha_ok, "span_ok": span_ok, "ok": bool(sha_ok and span_ok)}
'''


def grade_answer(answer_text: str, key: dict) -> dict:
    ans = answer_text
    try:
        obj = json.loads(answer_text[answer_text.index("{"): answer_text.rindex("}") + 1])
        ans = str(obj.get("answer", ""))
    except Exception:
        pass
    flat = " ".join(ans.split())
    sha_ok = key["sha8"].lower() in flat.lower()
    head = key["flat_head"]
    span_ok = False
    for n in (60, 40, 30):
        if any(head[i:i + n] in flat for i in range(0, max(1, len(head) - n))):
            span_ok = True
            break
    return {"sha8_ok": sha_ok, "span_ok": span_ok, "ok": bool(sha_ok and span_ok),
            "answer": flat[:300]}


def quality_form(rc, q: str, form: str, turn: int = TURNS) -> list[dict]:
    base = p0_text(rc, turn) if form == "P0" else p1_text(rc, turn)
    return [{"role": "user", "content": base.replace(rc.CANARY, q + "\n" + rc.CANARY)}]


def freeze_quality(rc) -> dict:
    qs = quality_questions(rc)
    payload = {
        "unit": "SYS-OPT", "version_frozen_for": VERSION, "frozen_at": utc_now(),
        "renderer": str(RENDERER_PATH.relative_to(REPO)), "renderer_sha256": sha256_file(RENDERER_PATH),
        "salt": SALT,
        "definition": "20 fixed questions, each asked in P0 form and P1 form (40 probes) on each "
                      "model. A probe mismatches when the frozen programmatic grader marks it wrong: "
                      "the answer must (a) contain the delta's sha8 prefix and (b) quote at least a "
                      "30-character contiguous run of the delta's flattened head.",
        "n_questions": QUALITY_N, "forms": ["P0", "P1"], "window": QUALITY_WINDOW,
        "grader": {"language": "python", "source": GRADER_SOURCE,
                   "note": "graded on the parsed 'answer' field when the completion is JSON; "
                           "on the raw text otherwise"},
        "questions": [{"id": "Q%02d" % i, "question": q, "key": quality_key(rc, i * 3)}
                      for i, q in enumerate(qs, start=1)],
    }
    body = json.dumps(payload, indent=2, sort_keys=True)
    payload["content_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    QUALITY_PATH.write_text(json.dumps(payload, indent=2))
    return {"path": str(QUALITY_PATH.relative_to(REPO)),
            "content_sha256": payload["content_sha256"],
            "file_sha256": sha256_file(QUALITY_PATH),
            "first_q": payload["questions"][0], "n": len(payload["questions"])}


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #
def bootstrap_mean_ci(vals: list[float], b: int = BOOTSTRAP_B, seed: int = BOOTSTRAP_SEED) -> list[float]:
    rnd = random.Random(seed)
    n = len(vals)
    stats = sorted(sum(vals[rnd.randrange(n)] for _ in range(n)) / n for _ in range(b))
    return [round(stats[int(0.025 * b)], 6), round(stats[int(0.975 * b) - 1], 6)]


def paired_delta_ci(a: dict[int, float], b: dict[int, float]) -> dict:
    turns = sorted(set(a) & set(b))
    diffs = {t: a[t] - b[t] for t in turns}
    vals = [diffs[t] for t in turns]
    rnd = random.Random(BOOTSTRAP_SEED)
    stats = sorted(sum(vals[rnd.randrange(len(vals))] for _ in range(len(vals))) / len(vals)
                   for _ in range(BOOTSTRAP_B))
    return {"n": len(turns), "mean": round(statistics.mean(vals), 6),
            "ci95": [round(stats[int(0.025 * BOOTSTRAP_B)], 6),
                     round(stats[int(0.975 * BOOTSTRAP_B) - 1], 6)],
            "excludes_zero": bool(stats[int(0.025 * BOOTSTRAP_B)] > 0
                                  or stats[int(0.975 * BOOTSTRAP_B) - 1] < 0)}


# --------------------------------------------------------------------------- #
# the round
# --------------------------------------------------------------------------- #
def tray(rows_path: Path, rows: list[dict], row: dict) -> None:
    rows.append(row)
    with rows_path.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def best_config_sha() -> dict:
    data = json.loads((REPO / "state" / "config" / "best-config.json").read_text())
    return {cid: data["setups"][cid]["config_sha256"] for cid in ("O1", "O2", "O3", "O4")}


def run_round(models: list[str], do_quality: bool = True) -> dict:
    rc = load_renderer()
    cfg_sha = best_config_sha()
    here = HERE
    here.mkdir(parents=True, exist_ok=True)
    handle = acquire_lock("SYS-OPT-R1B")
    used = 0
    out = {"unit": "SYS-OPT-R1B", "version": VERSION, "salt": SALT, "at": utc_now(),
           "arms": list(ARMS), "turns": TURNS, "quote_tokens": QUOTE_TOKENS, "models": {}}
    try:
        for name in models:
            host = MODELS[name]
            rows_path = here / ("rows-%s.jsonl" % name)
            if rows_path.exists():
                rows_path.unlink()
            rows: list[dict] = []
            g0 = equalise_warmup(host["url"], host["model"], arm_messages(rc, "P1", 20))
            used += 2
            counter_mode = False
            if not (isinstance(g0["call2_cached"], int) and g0["call2_cached"] > 0):
                counter_mode = True
                h0 = sample_prefix_hits(host["url"])
                post(host["url"], host["model"], arm_messages(rc, "P1", 20)); used += 1
                h1 = sample_prefix_hits(host["url"])
                post(host["url"], host["model"], arm_messages(rc, "P1", 20)); used += 1
                h2 = sample_prefix_hits(host["url"])
                g0 = {"call1_cached": None if None in (h0, h1) else int(round(h1 - h0)),
                      "call2_cached": None if None in (h1, h2) else int(round(h2 - h1)),
                      "prompt_tokens": post(host["url"], host["model"],
                                            arm_messages(rc, "P1", 20))["prompt_tokens"],
                      "cached_source": "vllm:prefix_cache_hits_total delta",
                      "hits_total": [h0, h1, h2]}
                used += 1
            if not (isinstance(g0["call2_cached"], int) and g0["call2_cached"] > 0):
                g0.update({"verdict": "GATE SKIP", "model": name, "at": utc_now()})
                (here / ("g0-%s.json" % name)).write_text(json.dumps(g0, indent=2))
                raise SystemExit("G0 GATE SKIP on %s: endpoint does not report cache hits" % name)
            g0.update({"verdict": "GATE OK", "model": name, "endpoint": host["url"],
                       "config_id": host["setup"], "counter_mode": counter_mode, "at": utc_now()})
            (here / ("g0-%s.json" % name)).write_text(json.dumps(g0, indent=2))
            print("[%s] G0 OK cached=%s counter_mode=%s" % (name, g0["call2_cached"], counter_mode),
                  flush=True)

            for arm in ARMS:
                warm = equalise_warmup(host["url"], host["model"], arm_messages(rc, arm, 1))
                used += 2
                t0 = time.time()
                for turn in range(1, TURNS + 1):
                    messages = arm_messages(rc, arm, turn)
                    res = measured_post(host["url"], host["model"], messages, counter_mode)
                    used += 1
                    retries = 0
                    while (not counter_mode and res["http_status"] == 200
                           and res["cached_tokens"] is None and not res["details_present"]
                           and turn > 1 and retries < COLD_RETRIES):
                        retries += 1
                        time.sleep(0.15)
                        res = measured_post(host["url"], host["model"], messages, counter_mode)
                        used += 1
                    if res["http_status"] != 200:
                        raise SystemExit("NON-200 %s %s turn %d -- no row" % (res["http_status"], arm, turn))
                    prompt, cached = res["prompt_tokens"], res["cached_tokens"]
                    uncached = (max(0, prompt - cached)
                                if isinstance(prompt, int) and isinstance(cached, int) else "unavailable")
                    row = {
                        "cell": "SYS-OPT", "version": VERSION, "salt": SALT, "model": name,
                        "model_id": host["model"], "setup": host["setup"], "engine": host["engine"],
                        "config_id": host["setup"], "config_sha256": cfg_sha[host["setup"]],
                        "arm": arm, "turn": turn,
                        "prompt_tokens": prompt if prompt is not None else "unavailable",
                        "cached_tokens": cached if cached is not None else "unavailable",
                        "uncached_tokens": uncached,
                        "quote_tokens": QUOTE_TOKENS,
                        "pad_tokens": 0,
                        "http_status": res["http_status"],
                        "prefix_sha256": sha256_text(messages[0]["content"]),
                        "prompt_sha256": sha256_text(json.dumps(messages, sort_keys=True)),
                        "cached_source": res.get("cached_source"),
                        "details_present": res["details_present"],
                        "requests_sent": 1 + retries,
                        "had_correction": bool(retries),
                        "corrections": 0,
                        "wall_ms": res["wall_ms"], "ts": utc_now(),
                    }
                    tray(rows_path, rows, row)
                print("[%s] %s done in %.1fs (%d rows)" % (name, arm, time.time() - t0, len(rows)), flush=True)

            qmath = None
            if do_quality:
                qfile = json.loads(QUALITY_PATH.read_text())
                keys = {q["key"]["t"]: q["key"] for q in qfile["questions"]}
                per_q, mutil, probes = [], 0, 0
                for q in qfile["questions"]:
                    key = keys[q["key"]["t"]]
                    forms = {}
                    for form in ("P0", "P1"):
                        res = post(host["url"], host["model"], quality_form(rc, q["question"], form),
                                   QUALITY_MAX_TOKENS)
                        used += 1
                        g = grade_answer(res["text"], key)
                        forms[form] = {"grader": g}
                        probes += 1
                        mutil += 0 if g["ok"] else 1
                    per_q.append({"id": q["id"], "question": q["question"], "t": q["key"]["t"],
                                  "forms": forms})
                qmath = {"n_probes": probes, "mismatches": mutil,
                         "mismatch_rate": round(mutil / probes, 6),
                         "p1_form": {"n": sum(1 for x in per_q),
                                     "mismatches": sum(0 if x["forms"]["P1"]["grader"]["ok"] else 1
                                                       for x in per_q)},
                         "per_question": per_q, "at": utc_now()}
                (here / ("quality-%s.json" % name)).write_text(json.dumps(qmath, indent=2))
                print("[%s] quality mismatch %d/%d" % (name, mutil, probes), flush=True)

            out["models"][name] = {"rows_path": str(rows_path.relative_to(REPO)),
                                   "n_rows": len(rows), "g0": g0, "quality": qmath and
                                   {k: v for k, v in qmath.items() if k != "per_question"}}
    finally:
        release_lock(handle)
    out["requests_used"] = used
    (here / "round-result.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"requests_used": used, "models": {k: v["n_rows"] for k, v in out["models"].items()}},
                     indent=2))
    return out


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
V0_SOURCES = {
    "moe": {"rows": R2P / "O1" / "rows.jsonl", "setup": "O1", "arm": "P1"},
    "dense": {"rows": R2P / "O4" / "rows.jsonl", "setup": "O4", "arm": "P1"},
}


def load_rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def score_model(name: str) -> dict:
    rows = load_rows(HERE / ("rows-%s.jsonl" % name))
    per_arm, unc_by_arm, hit_by_arm = {}, {}, {}
    for arm in ARMS:
        rs = sorted([r for r in rows if r["arm"] == arm], key=lambda r: int(r["turn"]))
        ok = [r for r in rs if r["http_status"] == 200
              and isinstance(r["prompt_tokens"], int) and isinstance(r["cached_tokens"], int)]
        unc = [float(r["prompt_tokens"] - r["cached_tokens"]) for r in ok]
        hits = [r["cached_tokens"] / r["prompt_tokens"] for r in ok if r["prompt_tokens"]]
        unc_by_arm[arm] = {int(r["turn"]): float(r["prompt_tokens"] - r["cached_tokens"]) for r in ok}
        hit_by_arm[arm] = {int(r["turn"]): r["cached_tokens"] / r["prompt_tokens"] for r in ok
                           if r["prompt_tokens"]}
        per_arm[arm] = {
            "n": len(ok), "n_rows": len(rs),
            "mean_uncached_per_turn": round(statistics.mean(unc), 6) if unc else None,
            "ci95_uncached_per_turn": bootstrap_mean_ci(unc) if unc else None,
            "hit_fraction": round(statistics.mean(hits), 6) if hits else None,
            "hit_fraction_pooled": (round(sum(r["cached_tokens"] for r in ok) /
                                          sum(r["prompt_tokens"] for r in ok), 6)
                                    if ok and sum(r["prompt_tokens"] for r in ok) else None),
            "distinct_prefix_sha256": len({r["prefix_sha256"] for r in ok}),
            "requests_sent_total": sum(int(r["requests_sent"]) for r in rs),
            "corrections_total": sum(int(r["corrections"]) for r in rs),
            "non_200": sum(1 for r in rs if r["http_status"] != 200),
        }
    src = V0_SOURCES[name]
    v0_rows = [r for r in load_rows(src["rows"]) if r["arm"] == src["arm"]]
    v0_unc = {int(r["turn"]): float(r["prompt_tokens"] - r["cached_tokens"]) for r in v0_rows
              if isinstance(r["prompt_tokens"], int) and isinstance(r["cached_tokens"], int)}
    v0_hit = {int(r["turn"]): r["cached_tokens"] / r["prompt_tokens"] for r in v0_rows
              if isinstance(r["prompt_tokens"], int) and isinstance(r["cached_tokens"], int)
              and r["prompt_tokens"]}
    delta = paired_delta_ci(unc_by_arm["P1"], v0_unc)
    hit_gain = (round(per_arm["P1"]["hit_fraction"] - statistics.mean(v0_hit.values()), 6)
                if per_arm["P1"]["hit_fraction"] and v0_hit else None)
    return {
        "model": name, "setup": MODELS[name]["setup"], "endpoint": MODELS[name]["url"],
        "per_arm": per_arm,
        "headline_arm": "P1",
        "v0": {"provenance": "%s rows %s arm %s" % (src["setup"], str(src["rows"].relative_to(REPO)),
                                                    src["arm"]),
               "rows_sha256": sha256_file(src["rows"]), "n": len(v0_unc),
               "mean_uncached_per_turn": round(statistics.mean(v0_unc.values()), 6),
               "hit_fraction": round(statistics.mean(v0_hit.values()), 6),
               "summary_unc": round(statistics.mean(v0_unc.values()), 2)},
        "improvement": {"metric": "P1 (headline), paired by turn vs V0",
                        "delta_unc": delta, "hit_gain": hit_gain,
                        "cost_ok": bool(delta["excludes_zero"] and delta["mean"] < 0),
                        "hit_ok": bool(hit_gain is not None and hit_gain >= 0.02),
                        "reader_note": "cost_ok needs the CI to exclude zero AND the mean to be "
                                       "negative; hit_ok needs >= +2.0 pp"},
    }


def emit() -> dict:
    qfile = json.loads(QUALITY_PATH.read_text())
    scores = {name: score_model(name) for name in MODELS}
    # prompt byte-identity across models
    digests = {}
    for name in MODELS:
        for r in load_rows(HERE / ("rows-%s.jsonl" % name)):
            digests.setdefault((r["arm"], r["turn"]), set()).add(r["prefix_sha256"])
    mismatched = [k for k, v in digests.items() if len(v) != 1]
    quality = {name: json.loads((HERE / ("quality-%s.json" % name)).read_text()) for name in MODELS}
    for name, q in quality.items():
        scores[name]["quality"] = {"n_probes": q["n_probes"], "mismatches": q["mismatches"],
                                   "mismatch_rate": q["mismatch_rate"],
                                   "p1_form_mismatches": q["p1_form"]["mismatches"],
                                   "p1_form_n": q["p1_form"]["n"]}
    improved = {n: bool(s["improvement"]["cost_ok"] and s["improvement"]["hit_ok"]) for n, s in scores.items()}
    verdict = ("improved_both" if all(improved.values()) else
               "one_sided" if any(improved.values()) else "no_signal")
    out = {"unit": "SYS-OPT-R1B", "version": VERSION,
           "generated": utc_now(), "quality_set": {"path": str(QUALITY_PATH.relative_to(REPO)),
                                                   "content_sha256": qfile["content_sha256"],
                                                   "file_sha256": sha256_file(QUALITY_PATH)},
           "protocol": {"models": list(MODELS), "arms": list(ARMS), "turns": TURNS,
                        "rows_expected": len(MODELS) * len(ARMS) * TURNS,
                        "rows_measured": sum(s["per_arm"][a]["n_rows"] for s in scores.values()
                                             for a in ARMS),
                        "quote_tokens": QUOTE_TOKENS, "salt": SALT,
                        "headline": "P1 per model (VERSIONS.md Amendments A1/A2)"},
           "prompt_byte_identity": {"pairs": len(digests), "mismatched": len(mismatched),
                                    "ok": not mismatched},
           "per_model": scores, "verdict": verdict, "improved": improved,
           "v0_baseline": {n: scores[n]["v0"] for n in scores}}
    (STATE / "sys-opt-v1.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"verdict": verdict,
                      "per_model": {n: {"p1_unc": scores[n]["per_arm"]["P1"]["mean_uncached_per_turn"],
                                        "p1_ci": scores[n]["per_arm"]["P1"]["ci95_uncached_per_turn"],
                                        "p1_hit": scores[n]["per_arm"]["P1"]["hit_fraction"],
                                        "v0_unc": scores[n]["v0"]["mean_uncached_per_turn"],
                                        "delta": scores[n]["improvement"]["delta_unc"],
                                        "hit_gain": scores[n]["improvement"]["hit_gain"],
                                        "quality": scores[n]["quality"]} for n in scores},
                      "byte_identity": out["prompt_byte_identity"]}, indent=2))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze-quality", action="store_true")
    ap.add_argument("--round", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--models", default="moe,dense")
    args = ap.parse_args(argv)
    rc = load_renderer()
    if args.freeze_quality:
        print(json.dumps(freeze_quality(rc), indent=2))
    if args.round:
        run_round([m.strip() for m in args.models.split(",") if m.strip()])
    if args.emit:
        emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
