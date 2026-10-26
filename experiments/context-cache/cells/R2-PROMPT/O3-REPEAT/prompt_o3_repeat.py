#!/usr/bin/env python3
"""R2-PROMPT — the P0/P1/P2/P3 prompt factorial on the OPTIMISED setups.

One script, one setup per run.  Substrate is `state/config/best-config.json`
ONLY (never the card's prose table, never a Round-1 config).

    ARMS (identical task content in every arm so cost is comparable)
      P0  whole-context resend      -- == renderer arm "R": scaffold + HISTORY
                                       (every delta verbatim, re-sent each turn)
      P1  pointer + append-only     -- == renderer arm "A": scaffold + pointer
                                       index (id | byte-span | sha8 | summary)
                                       + exactly one trailing newest-delta block
      P2  pointer + grid-aligned tail -- P1 with the trailing block padded, by
                                       the MEASURED chars->tokens ratio, so the
                                       request length lands on the setup grid.
                                       Pad is inert newlines, recorded pad_tokens.
      P3  mid-context edit control  -- P1 with ONE earlier index line (t020)
                                       rewritten once at turn 40 and thereafter.
                                       The cached prefix must collapse.

The four arm bodies are NOT re-invented here: `R` and `A` come verbatim from the
renderer frozen in ``cells/VLLM-CELL/vllm_cell.py`` -- the same renderer the
Round-2 predecessors (PROMPT-O1, PROMPT-O2-EXTRA, PROMPT-O4B) used -- so the
prefix digests are the lineage's own.  P2/P3 are derived from P1's bytes, so
the only difference between arms is the mechanism under test.

Invariants (each enforced in code, not asserted in prose):
  * an absent `prompt_tokens_details`/`cached_tokens` yields ``"unavailable"``,
    never 0; a measured 0 is written as 0
  * a non-200 response writes no row and aborts the arm
  * the four arms must render DIFFERENT bytes (ARMS_IDENTICAL otherwise) --
    the guard inherited from R2-VLLM-FIX
  * prompts are deterministic: no clock, no randomness, no hash seeding

Usage
    python3 prompt_r2prompt_cell.py --setup O1
    python3 prompt_r2prompt_cell.py --setup O4 --quality
    python3 prompt_r2prompt_cell.py --setup O1 --dry      # render-only proof
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path("/home/zer0null/reserach extarctor")
HERE = Path(__file__).resolve().parent
SALT = "o3-repeat-20261024T11:05Z-a1"
OBSERVED_GRID = 16   # gcd of cached_tokens over the 284-row O3 run; best-config declares 48
RENDERER_PATH = REPO / "experiments" / "context-cache" / "cells" / "VLLM-CELL" / "vllm_cell.py"
BEST_CONFIG = REPO / "state" / "config" / "best-config.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
PROGRESS_LOG = REPO / "state" / "logs" / "O3-P2-REPEAT-progress.log"

ARMS = ("P0", "P1", "P2", "P3")
TURNS = 71
BUDGET_TOKENS = 32768
MAX_TOKENS = 8
EDIT_TURN = 40      # P3 rewrites one earlier block once, from here on
EDIT_TARGET = 20    # the block that gets rewritten (t020)
QUALITY_N = 20
QUALITY_MAX_TOKENS = 48
QUALITY_WINDOW = 32
COLD_RETRIES = 3

BASE_URL = {
    "O1": os.environ.get("RESEXTRACT_R2PROMPT_O1_URL", "http://192.168.2.168:8012/v1"),
    "O2": os.environ.get("RESEXTRACT_R2PROMPT_O2_URL", "http://192.168.2.168:8017/v1"),
    "O3": os.environ.get("RESEXTRACT_R2PROMPT_O3_URL", "http://192.168.2.168:8018/v1"),
    "O4": os.environ.get("RESEXTRACT_R2PROMPT_O4_URL", "http://192.168.2.168:8014/v1"),
}


# --------------------------------------------------------------------------- #
# small utilities
# --------------------------------------------------------------------------- #
def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_renderer():
    import importlib.util

    spec = importlib.util.spec_from_file_location("vllm_cell_r2prompt", RENDERER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    # FRESH SALT: every rendered byte differs from the R2-PROMPT/O3 run, so the
    # repeat is an independent sample and cannot replay a cache warmed by it.
    mod.SCAFFOLD = mod.SCAFFOLD + "RUN-SALT: %s\n" % SALT
    return mod


def load_setup(config_id: str) -> dict:
    data = json.loads(BEST_CONFIG.read_text())
    setups = data.get("setups", {})
    if config_id not in setups:
        raise SystemExit("SETUP ABSENT: %s not in best-config.json" % config_id)
    s = setups[config_id]
    if "argv" not in s:
        raise SystemExit("SETUP UNAVAILABLE: %s -> %s" % (config_id, s.get("reason")))
    s["_best_config_sha256"] = hashlib.sha256(BEST_CONFIG.read_bytes()).hexdigest()
    return s


# --------------------------------------------------------------------------- #
# arm rendering
# --------------------------------------------------------------------------- #
def p1_text(renderer, turn: int) -> str:
    """P1 == renderer arm A verbatim: scaffold + pointer index + newest delta."""
    return renderer.render("A", turn)[0]["content"]


def p0_text(renderer, turn: int) -> str:
    """P0 == renderer arm R verbatim: scaffold + whole evolving state re-sent."""
    return renderer.render("R", turn)[0]["content"]


FILLER = " PAD"


def p2_text(renderer, turn: int, grid: int, ratio: float,
            state: dict | None = None) -> tuple[str, int]:
    """P1 with the trailing block padded to the setup grid. Returns (text, pad_tokens).

    Two measured facts shaped this, both from the O1 v1/v2 runs:
      * a whitespace pad is STRIPPED by the chat template -- v1 sent 71/71 rows
        with prompt_tokens identical to P1, i.e. the arm was a byte-identical
        replay of P1 (those rows are archived as rows.p2-v1-*.jsonl);
      * the pad must therefore be CONTENT and its length must be converted from
        tokens to characters by a MEASURED slope (calibrate_filler), not by the
        generic chars->tokens ratio.
    The pad target is computed from P1's OWN measured prompt_tokens for this
    turn when that row exists, so the alignment does not depend on an estimate.
    """
    state = state if state is not None else {"slope": ratio, "err": 0.0}
    base = p1_text(renderer, turn)
    base_tokens = (state.get("base_tokens") or {}).get(turn)
    if base_tokens is None:
        est = int(round(len(base) * ratio))
        pad_target = int(round((-(est + state.get("err", 0.0))) % grid))
    else:
        pad_target = int((-int(base_tokens)) % grid)
    if pad_target < 64:      # a tax smaller than one block would still eat real bytes
        pad_target += grid
    slope = max(float(state.get("slope") or ratio), 1e-6)
    chars = max(1, int(round(pad_target / slope)))
    filler = FILLER * max(1, int(math.ceil(chars / len(FILLER))))
    state["pad_target"] = pad_target
    state["filler_chars"] = len(filler)
    return base + filler, pad_target


def _edited_index_line(renderer, turn: int) -> tuple[str, str]:
    """The t020 index line as rendered at `turn`, and its single-rewrite form."""
    lines = renderer.pointer_index(turn - 1).splitlines()
    original = next(l for l in lines if l.startswith("t%03d |" % EDIT_TARGET))
    parts = original.split(" | ", 3)
    rewritten = " | ".join([
        parts[0], parts[1], renderer.sha8("EDITED::" + parts[0]),
        "[rev2] " + (" ".join(parts[3].split()))[:80],
    ])
    return original, rewritten


def p3_text(renderer, turn: int) -> str:
    """P1 with one earlier block rewritten once -- live from EDIT_TURN on.

    The policy marker rides at the TAIL (after the canary), the way arm H's
    unconditional marker does: it makes P3 a distinct arm from turn 1 without
    moving the divergence point into the middle of the prefix.  Pre-edit the
    bytes up to the marker are P1's own, so P3 starts from P1's hit and the only
    mid-context change in the whole arm is the turn-40 rewrite.
    """
    base = p1_text(renderer, turn)
    if turn < EDIT_TURN:
        return base + "\nMODE[edit-policy; revised=0]"
    original, rewritten = _edited_index_line(renderer, turn)
    if original not in base:
        raise SystemExit("P3 EDIT ANCHOR MISSING at turn %d" % turn)
    return base.replace(original, rewritten, 1) + "\nMODE[edit-policy; revised=1]"


def arm_text(renderer, arm: str, turn: int, grid: int, ratio: float,
             state: dict | None = None) -> tuple[str, int]:
    if arm == "P0":
        return p0_text(renderer, turn), 0
    if arm == "P1":
        return p1_text(renderer, turn), 0
    if arm == "P2":
        return p2_text(renderer, turn, grid, ratio, state)
    if arm == "P3":
        return p3_text(renderer, turn), 0
    raise ValueError("unknown arm %r" % (arm,))


def arm_messages(renderer, arm: str, turn: int, grid: int, ratio: float,
                 state: dict | None = None) -> tuple[list[dict], int]:
    text, pad = arm_text(renderer, arm, turn, grid, ratio, state)
    return [{"role": "user", "content": text}], pad


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def post(base_url: str, model: str, messages: list[dict], max_tokens: int = MAX_TOKENS) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": int(max_tokens),
        "temperature": 0.0,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    started = time.perf_counter()
    last = None
    for attempt in (1, 2):
        try:
            resp = requests.post(base_url.rstrip("/") + "/chat/completions",
                                 json=payload, timeout=240)
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
            return {
                "http_status": int(resp.status_code),
                "prompt_tokens": None if prompt is None else int(prompt),
                "cached_tokens": None if cached is None else int(cached),
                "details_present": isinstance(details, dict),
                "text": text,
                "wall_ms": round(wall_ms, 3),
            }
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.0 + attempt)
    raise SystemExit("TRANSPORT FAILURE after 2 attempts: %r" % (last,))


def sample_prefix_hits(base_url: str) -> float | None:
    """The server's OWN prefix-cache hit counter (vLLM 0.27.1 token units).

    Used only when the endpoint answers with ``prompt_tokens_details: null``
    (the per-request accounting is off because ``--enable-prompt-tokens-details``
    is absent).  This is measurement, not inference: the counter increments by
    the number of prompt tokens served from cache on each request (R2-VLLM-
    DOCCHECK pinned the names on v0.27.1: vllm:prefix_cache_hits_total /
    vllm:prefix_cache_queries_total).
    """
    try:
        text = requests.get(base_url.rstrip("/").rsplit("/v1", 1)[0] + "/metrics",
                            timeout=20).text
    except Exception:
        return None
    total = 0.0
    found = False
    for line in text.splitlines():
        if line.startswith("vllm:prefix_cache_hits_total"):
            try:
                total += float(line.split()[1])
                found = True
            except (IndexError, ValueError):
                continue
    return total if found else None


def measured_post(base_url: str, model: str, messages: list, counter_mode: bool) -> dict:
    """POST once, attaching cached_tokens from the response or the server counter.

    Every POST that can contribute a row MUST go through here: the P2 correction
    resend and the cold retry also replace ``res``, and an earlier version lost
    the counter-derived value exactly that way (O4 P2 landed `unavailable` on 27
    rows while P0/P1 were fine -- the resend path bypassed the sampler).
    """
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


def equalise_arm_warmup(base_url: str, model: str, messages: list[dict]) -> dict:
    """Two identical calls before a measured arm; the 2nd is the warm one."""
    c1 = post(base_url, model, messages)
    c2 = post(base_url, model, messages)
    return {"call1_cached": c1["cached_tokens"], "call2_cached": c2["cached_tokens"],
            "prompt_tokens": c2["prompt_tokens"] or c1["prompt_tokens"]}


# --------------------------------------------------------------------------- #
# lock
# --------------------------------------------------------------------------- #
def acquire_lock(unit: str, timeout_s: float = 900.0):
    import fcntl

    handle = open(LOCK_PATH, "a+")
    deadline = time.time() + timeout_s
    waited = 0.0
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.time() > deadline:
                handle.close()
                raise SystemExit("LOCK BUSY after %.0fs" % timeout_s)
            time.sleep(2.0)
            waited += 2.0
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": unit, "pid": os.getpid(), "acquired_utc": utc_now(),
               "scope": "R2-PROMPT factorial"}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, waited


def release_lock(handle) -> None:
    import fcntl

    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "R2-PROMPT", "pid": os.getpid(), "released_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    handle.close()


# --------------------------------------------------------------------------- #
# statistics (t intervals, paired deltas)
# --------------------------------------------------------------------------- #
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    x = df / (df + t * t)
    p = 0.5 * _betai(df / 2.0, 0.5, x)
    return 1.0 - p if t > 0 else p


def t_ppf(p: float, df: float) -> float:
    lo, hi = 0.0, 60.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def mean_ci(values: list[float]) -> dict:
    n = len(values)
    if n < 2:
        return {"n": n, "mean": (values[0] if values else None), "sd": None, "se": None,
                "df": None, "t": None, "ci95": None}
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    se = sd / math.sqrt(n)
    tcrit = t_ppf(0.975, n - 1)
    return {"n": n, "mean": round(mean, 6), "sd": round(sd, 6), "se": round(se, 6),
            "df": n - 1, "t": round(tcrit, 6),
            "ci95": [round(mean - tcrit * se, 6), round(mean + tcrit * se, 6)]}


def paired_delta(a: dict[int, float], b: dict[int, float]) -> dict:
    turns = sorted(set(a) & set(b))
    diffs = [a[t] - b[t] for t in turns]
    if len(diffs) < 2:
        return {"n": len(diffs), "mean": None, "ci95": None, "excludes_zero": None}
    est = mean_ci(diffs)
    lo, hi = est["ci95"]
    return {"n": est["n"], "mean": est["mean"], "sd": est["sd"], "se": est["se"],
            "df": est["df"], "ci95": est["ci95"], "excludes_zero": (lo > 0 or hi < 0),
            "direction": ("a larger" if est["mean"] > 0 else "b larger")}


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def row_key(arm: str, turn: int) -> str:
    return "%s:%d" % (arm, turn)


def load_existing(path: Path) -> tuple[list[dict], set[str]]:
    rows, done = [], set()
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            rows.append(r)
            if r.get("http_status") == 200 and r.get("arm") and r.get("turn"):
                done.add(row_key(r["arm"], int(r["turn"])))
    return rows, done


def append_row(path: Path, row: dict) -> None:
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def progress(line: str) -> None:
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a") as fh:
        fh.write("%s %s\n" % (utc_now(), line))
        fh.flush()


def render_distinct_proof(renderer, grid: int, ratio: float) -> dict:
    proof = {}
    for turn in (1, 20, 41, 71):
        texts = {a: arm_text(renderer, a, turn, grid, ratio)[0] for a in ARMS}
        shas = {a: sha256_text(t) for a, t in texts.items()}
        if len(set(shas.values())) != len(ARMS):
            raise SystemExit("ARMS_IDENTICAL at turn %d: %s" % (turn, shas))
        proof[str(turn)] = shas
    # P1 vs P3 must be byte-identical before the edit and differ from it on/after
    # P1 vs P3: identical up to the tail marker before the edit, and the edit
    # must diverge INSIDE the index (not in the tail marker) on/after it.
    if not p3_text(renderer, 39).startswith(p1_text(renderer, 39)):
        raise SystemExit("P3 rewrites the shared prefix BEFORE the edit turn -- control broken")
    a, b = p1_text(renderer, 41), p3_text(renderer, 41)
    if a == b:
        raise SystemExit("P3 identical to P1 AFTER the edit turn -- the rewrite did not land")
    pos = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
    if pos is None or pos > a.index(renderer.CANARY):
        raise SystemExit("P3 edit diverges in the tail marker, not mid-context (pos=%r)" % (pos,))
    proof["p3_divergence_byte_offset"] = pos
    return proof


def quality_questions(renderer) -> list[str]:
    """20 fixed questions, deterministic, drawn from the same 71-turn body."""
    qs = []
    for t in range(1, QUALITY_N + 1):
        qs.append("Q%02d: quote the span of delta t=%03d and state its sha8 prefix." % (t, t * 3))
    return qs


def quality_form(renderer, q: str, form: str, turn: int = 71) -> list[dict]:
    if form == "P0":
        return [{"role": "user", "content": p0_text(renderer, turn).replace(
            renderer.CANARY, q + "\n" + renderer.CANARY)}]
    return [{"role": "user", "content": p1_text(renderer, turn).replace(
        renderer.CANARY, q + "\n" + renderer.CANARY)}]


def first_tokens(text: str, n: int = QUALITY_WINDOW) -> list[str]:
    return " ".join(text.split()).split(" ")[:n]


def calibrate_filler(base_url: str, model: str, renderer) -> dict:
    """Measure tokens-per-filler-character so the pad length is a measurement.

    Three filler lengths on one fixed base text; slope fitted through the origin
    on (chars, measured_tokens_delta).  Costs 4 requests, once per cell.
    """
    base = p1_text(renderer, 1)
    base_res = post(base_url, model, [{"role": "user", "content": base}])
    base_tokens = base_res["prompt_tokens"]
    samples, num, den = [], 0.0, 0.0
    for chars in (200, 400, 800):
        text = base + FILLER * (chars // len(FILLER))
        res = post(base_url, model, [{"role": "user", "content": text}])
        delta = res["prompt_tokens"] - base_tokens
        samples.append({"filler_chars": len(FILLER) * (chars // len(FILLER)),
                        "measured_token_delta": delta})
        num += delta * samples[-1]["filler_chars"]
        den += samples[-1]["filler_chars"] ** 2
    slope = (num / den) if den else 0.25
    return {"base_prompt_tokens": base_tokens, "samples": samples,
            "tokens_per_filler_char": round(slope, 8),
            "requests": 1 + len(samples)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", required=True, choices=sorted(BASE_URL))
    ap.add_argument("--arms", default="P0,P1,P2")
    ap.add_argument("--turns", type=int, default=TURNS)
    ap.add_argument("--quality", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--cached-from-metrics", action="store_true",
                    help="derive cached_tokens from vllm:prefix_cache_hits_total deltas "
                         "when the endpoint reports prompt_tokens_details: null")
    args = ap.parse_args(argv)

    setup = load_setup(args.setup)
    base_url = BASE_URL[args.setup]
    model = setup["model"]
    grid = OBSERVED_GRID                    # the OBSERVED unit, not the declared one
    declared_grid = int(setup.get("grid_unit") or 0)
    if grid <= 0:
        raise SystemExit("SETUP %s has no grid_unit -- refuse to guess" % args.setup)
    cell_dir = HERE                          # this cell IS O3-REPEAT
    cell_dir.mkdir(parents=True, exist_ok=True)
    rows_path = cell_dir / "rows.jsonl"

    renderer = load_renderer()
    arms = tuple(a.strip() for a in args.arms.split(",") if a.strip())
    ratio = 0.25  # chars->tokens; replaced by the measured ratio after the warm-up

    proof = render_distinct_proof(renderer, grid, ratio)
    if args.dry:
        print(json.dumps({"setup": args.setup, "grid": grid, "arms_distinct_at": proof,
                          "p3_edit_turn": EDIT_TURN, "p3_target": EDIT_TARGET}, indent=2))
        return 0

    # --- G0: the endpoint must report cached_tokens at all ------------------ #
    warm_text = renderer.SCAFFOLD + "HISTORY:\n" + renderer.body_upto(20) + "\n" + renderer.CANARY
    warm_msgs = [{"role": "user", "content": warm_text}]
    if args.cached_from_metrics:
        h0 = sample_prefix_hits(base_url)
        post(base_url, model, warm_msgs)
        h1 = sample_prefix_hits(base_url)
        post(base_url, model, warm_msgs)
        h2 = sample_prefix_hits(base_url)
        d1 = None if None in (h0, h1) else int(round(h1 - h0))
        d2 = None if None in (h1, h2) else int(round(h2 - h1))
        g0 = {"call1_cached": d1, "call2_cached": d2,
              "prompt_tokens": post(base_url, model, warm_msgs)["prompt_tokens"],
              "cached_source": "vllm:prefix_cache_hits_total delta",
              "hits_total": [h0, h1, h2]}
    else:
        g0 = equalise_arm_warmup(base_url, model, warm_msgs)
    if not (isinstance(g0["call2_cached"], int) and g0["call2_cached"] > 0):
        g0.update({"verdict": "GATE SKIP: the endpoint does not report a cache hit on an "
                               "identical repeat", "at": utc_now(), "setup": args.setup})
        (cell_dir / "g0.json").write_text(json.dumps(g0, indent=2))
        progress("%s %s GATE SKIP %s" % (args.setup, "G0", g0["call2_cached"]))
        print(json.dumps(g0, indent=2))
        return 3
    if g0.get("prompt_tokens"):
        ratio = float(g0["prompt_tokens"]) / float(len(warm_text))
    g0.update({"setup": args.setup, "verdict": "GATE OK", "at": utc_now(),
               "token_ratio_chars": round(ratio, 8)})
    (cell_dir / "g0.json").write_text(json.dumps(g0, indent=2))
    progress("%s G0 OK call2_cached=%s ratio=%.6f" % (args.setup, g0["call2_cached"], ratio))

    if args.analyse_only:
        rows, _ = load_existing(rows_path)
        g0_path = cell_dir / "g0.json"
        g0_prev = json.loads(g0_path.read_text()) if g0_path.exists() else {}
        analysis = analyse(rows, args.setup, setup, grid, ratio, g0_prev, [])
        (cell_dir / "analysis.json").write_text(json.dumps(analysis, indent=2))
        print(json.dumps({"setup": args.setup, "analyse_only": True, "n_rows": len(rows),
                          "observed_cached_gcd": analysis["observed_cached_gcd"]}, indent=2))
        return 0

    handle, waited = acquire_lock("O3-P2-REPEAT/%s" % args.setup)
    started = utc_now()
    requests_used = 0
    warm_rows = []
    try:
        rows, done = load_existing(rows_path)
        p1_len = {int(r["turn"]): int(r["prompt_tokens"]) for r in rows
                  if r["arm"] == "P1" and isinstance(r["prompt_tokens"], int)}
        p2_calib = None
        if "P2" in arms:
            p2_calib = calibrate_filler(base_url, model, renderer)
            requests_used += p2_calib["requests"]
            p2_calib["at"] = utc_now()
            (cell_dir / "p2_calibration.json").write_text(json.dumps(p2_calib, indent=2))
            progress("%s P2 filler calibration slope=%.6f tokens/char from %d requests"
                     % (args.setup, p2_calib["tokens_per_filler_char"], p2_calib["requests"]))
        row = None
        for arm in arms:
            p2_state = {"err": 0.0}
            warm = equalise_arm_warmup(base_url, model,
                                       arm_messages(renderer, arm, 1, grid, ratio, p2_state)[0])
            requests_used += 2
            warm["arm"] = arm
            warm_rows.append(warm)
            for turn in range(1, args.turns + 1):
                key = row_key(arm, turn)
                if key in done:
                    continue
                p2_state["base_tokens"] = p1_len
                if p2_calib:
                    p2_state["slope"] = p2_calib["tokens_per_filler_char"]
                messages, pad = arm_messages(renderer, arm, turn, grid, ratio, p2_state)
                res = measured_post(base_url, model, messages, args.cached_from_metrics)
                requests_used += 1
                corrections = 0
                # exact alignment: the server reports the true length, so correct
                # the filler and resend until prompt_tokens is ON the grid.
                while (arm == "P2" and isinstance(res["prompt_tokens"], int)
                       and res["prompt_tokens"] % grid != 0 and corrections < 3):
                    got = int(res["prompt_tokens"])
                    delta = (-got) % grid
                    if delta > grid // 2:
                        delta -= grid
                    slope = max(float(p2_state.get("slope") or ratio), 1e-6)
                    new_chars = max(1, int(p2_state["filler_chars"]) + int(round(delta / slope)))
                    text = p1_text(renderer, turn) + FILLER * max(1, int(math.ceil(new_chars / len(FILLER))))
                    messages = [{"role": "user", "content": text}]
                    res = measured_post(base_url, model, messages, args.cached_from_metrics)
                    requests_used += 1
                    corrections += 1
                    pad = int(p2_state.get("pad_target") or 0) + delta
                tries = 0
                while (not args.cached_from_metrics and res["http_status"] == 200
                       and res["cached_tokens"] is None
                       and not res["details_present"] and turn > 1 and tries < COLD_RETRIES):
                    tries += 1
                    time.sleep(0.15)
                    res = measured_post(base_url, model, messages, args.cached_from_metrics)
                    requests_used += 1
                if res["http_status"] != 200:
                    raise SystemExit("NON-200 %s at %s turn %d -- no row written"
                                     % (res["http_status"], arm, turn))
                prompt_tokens = res["prompt_tokens"]
                cached = res["cached_tokens"]
                if arm == "P2" and isinstance(prompt_tokens, int):
                    p2_state["err"] = float(prompt_tokens) - float(p2_state.get("predicted", 0) or 0)
                if isinstance(prompt_tokens, int) and isinstance(cached, int):
                    uncached = max(0, prompt_tokens - cached)
                else:
                    uncached = "unavailable"
                row = {
                    "setup": args.setup,
                    "cell": "O3-REPEAT",
                    "salt": SALT,
                    "stack": "%s/%s" % (setup["engine"], model),
                    "model": model,
                    "config_id": setup["config_id"],
                    "config_sha256": setup["config_sha256"],
                    "arm": arm,
                    "turn": turn,
                    "prompt_tokens": prompt_tokens if prompt_tokens is not None else "unavailable",
                    "cached_tokens": cached if cached is not None else "unavailable",
                    "uncached_tokens": uncached,
                    "pad_tokens": pad,
                    "http_status": res["http_status"],
                    "prefix_sha256": sha256_text(messages[0]["content"]),
                    "prompt_sha256": sha256_text(json.dumps(messages, sort_keys=True)),
                    "details_present": res["details_present"],
                    "null_retries": tries,
                    "cached_source": res.get("cached_source"),
                    "pad_corrections": corrections,
                    "pad_aligned": (isinstance(res["prompt_tokens"], int)
                                    and res["prompt_tokens"] % grid == 0),
                    "wall_ms": res["wall_ms"],
                    "ts": utc_now(),
                }
                append_row(rows_path, row)
                rows.append(row)
            if row is not None:
                    progress("%s %s done: %d rows, last prompt_tokens=%s cached=%s pad=%s"
                     % (args.setup, arm, sum(1 for r in rows_path.read_text().splitlines() if r.strip()),
                        row["prompt_tokens"], row["cached_tokens"], row["pad_tokens"]))

        analysis = analyse(rows, args.setup, setup, grid, ratio, g0, warm_rows)
        analysis["salt"] = SALT
        analysis["grid_used"] = grid
        analysis["grid_declared_in_best_config"] = declared_grid
        analysis["endpoint"] = base_url
        analysis["warm_rows"] = warm_rows
        analysis["cell"] = "O3-REPEAT"
        (cell_dir / "analysis.json").write_text(json.dumps(analysis, indent=2))
        progress("%s ANALYSIS written: %s" % (args.setup, ", ".join(
            "%s unc=%s hit=%s" % (a, analysis["per_arm"][a]["mean_uncached_per_turn"],
                                  analysis["per_arm"][a]["hit_fraction_weighted"])
            for a in analysis["arms"] if a in analysis["per_arm"])))

        if args.quality:
            qpath = cell_dir / "quality.json"
            q = run_quality(renderer, base_url, model, grid, ratio)
            qpath.write_text(json.dumps(q, indent=2))
            progress("%s QUALITY mismatch=%s" % (args.setup, q["mismatch_rate"]))
    finally:
        release_lock(handle)

    print(json.dumps({"setup": args.setup, "cells_written": str(cell_dir), "requests": requests_used,
                      "lock_wait_s": waited, "started": started, "ended": utc_now(),
                      "base_url": base_url, "grid_unit": grid}, indent=2))
    return 0


def run_quality(renderer, base_url: str, model: str, grid: int, ratio: float) -> dict:
    qs = quality_questions(renderer)
    per_q, mismatched = [], 0
    for q in qs:
        outs, texts = {}, {}
        for form in ("P0", "P1"):
            res = post(base_url, model, quality_form(renderer, q, form), QUALITY_MAX_TOKENS)
            texts[form] = res["text"]
            outs[form] = first_tokens(res["text"], QUALITY_WINDOW)
        shortest = min(len(outs["P0"]), len(outs["P1"]))
        diff = sum(1 for i in range(shortest) if outs["P0"][i] != outs["P1"][i])
        rate = (diff / shortest) if shortest else None
        bad = (rate is not None and rate > 0)
        mismatched += 1 if bad else 0
        per_q.append({"q": q, "n_compared": shortest, "positional_diff": diff,
                      "positional_mismatch_rate": None if rate is None else round(rate, 6),
                      "first_32_mismatch": bad,
                      "first32": {"P0": outs["P0"], "P1": outs["P1"]},
                      "text": texts})
    return {
        "unit": "R2-PROMPT", "definition":
            "first-32-token mismatch: whitespace tokens of the completion, P0 form vs P1 form, "
            "same question, same model; a position counts as a mismatch when it differs",
        "n_questions": len(qs), "window": QUALITY_WINDOW,
        "questions_mismatched": mismatched,
        "mismatch_rate": round(mismatched / len(qs), 6) if qs else None,
        "per_question": per_q, "at": utc_now(),
    }


def analyse(rows, setup_id, setup, grid, ratio, g0, warm_rows) -> dict:
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]
    per_arm, unc_by_arm, cached_by_arm = {}, {}, {}
    for arm in arms:
        rs = sorted([r for r in rows if r["arm"] == arm], key=lambda r: int(r["turn"]))
        unc = [float(r["uncached_tokens"]) for r in rs
               if isinstance(r["uncached_tokens"], (int, float))]
        unc_by_arm[arm] = {int(r["turn"]): float(r["uncached_tokens"]) for r in rs
                           if isinstance(r["uncached_tokens"], (int, float))}
        cached_by_arm[arm] = {int(r["turn"]): int(r["cached_tokens"]) for r in rs
                              if isinstance(r["cached_tokens"], int)}
        ci = mean_ci(unc)
        pt = sum(int(r["prompt_tokens"]) for r in rs if isinstance(r["prompt_tokens"], int))
        ct = sum(int(r["cached_tokens"]) for r in rs if isinstance(r["cached_tokens"], int))
        residues = {}
        for r in rs:
            if isinstance(r["prompt_tokens"], int):
                residues[str(r["prompt_tokens"] % grid)] = \
                    residues.get(str(r["prompt_tokens"] % grid), 0) + 1
        per_arm[arm] = {
            "n_rows": len(rs), "n_measured": len(unc),
            "mean_uncached_per_turn": ci["mean"], "sd": ci["sd"], "se": ci["se"],
            "df": ci["df"], "ci95_uncached_per_turn": ci["ci95"],
            "hit_fraction_weighted": (round(ct / pt, 6) if pt else None),
            "prompt_tokens_total": pt, "cached_tokens_total": ct,
            "n_cached_gt_0": sum(1 for r in rs if isinstance(r["cached_tokens"], int)
                                 and r["cached_tokens"] > 0),
            "n_unavailable_cached": sum(1 for r in rs if not isinstance(r["cached_tokens"], int)),
            "n_non_200": sum(1 for r in rs if r.get("http_status") != 200),
            "pad_tokens_total": sum(int(r.get("pad_tokens") or 0) for r in rs),
            "grid_aligned_rows": sum(1 for r in rs if isinstance(r["prompt_tokens"], int)
                                     and r["prompt_tokens"] % grid == 0),
            "prompt_token_residues_mod_grid": dict(sorted(residues.items(),
                                                          key=lambda kv: -kv[1])[:6]),
            "distinct_prefix_sha256": len({r["prefix_sha256"] for r in rs}),
        }

    deltas = {}
    for a, b, label in (("P1", "P0", "P1/P0"), ("P2", "P0", "P2/P0"),
                        ("P3", "P1", "P3/P1")):
        if a in unc_by_arm and b in unc_by_arm:
            d = paired_delta(unc_by_arm[a], unc_by_arm[b])
            d["ratio_of_means"] = (
                round(per_arm[a]["mean_uncached_per_turn"] / per_arm[b]["mean_uncached_per_turn"], 6)
                if per_arm[b]["mean_uncached_per_turn"] else None)
            deltas[label] = d

    # P3 survival: the ONE-TIME collapse at the edit turn (the point of the arm)
    survival = None
    if "P3" in cached_by_arm and "P1" in cached_by_arm:
        p3c, p1c = cached_by_arm["P3"], cached_by_arm["P1"]
        t = EDIT_TURN
        pre, post, p1_post = p3c.get(t - 1), p3c.get(t), p1c.get(t)
        later = [x for x in p3c if x > t and x in p1c]
        rebuilt = (sum(p3c[x] for x in later) / len(later)) if later else None
        rebuilt_p1 = (sum(p1c[x] for x in later) / len(later)) if later else None
        # A collapse is attributable to the edit only when the CONTROL arm still
        # shows its cached prefix at the same turn.  If P1 is 0 there too, neither
        # arm was cached on that turn, so the fraction has no denominator: it is
        # `unmeasurable`, never 1.0 (this is O3/O4's case).
        attributable = bool(pre) and post is not None and bool(p1_post)
        survival = {
            "edit_turn": t, "edit_target_index_line": "t%03d" % EDIT_TARGET,
            "p3_cached_turn_before": pre, "p3_cached_at_edit_turn": post,
            "p1_cached_at_edit_turn": p1_post,
            "collapse_fraction": (None if not attributable
                                  else round(1.0 - post / pre, 6)),
            "surviving_fraction_of_pre_edit_cached": (None if not attributable
                                                      else round(post / pre, 6)),
            "p3_over_p1_at_edit_turn": (None if not p1_post else round(post / p1_post, 6)),
            "rebuilt_mean_cached_after_edit": None if rebuilt is None else round(rebuilt, 3),
            "p1_mean_cached_same_later_turns": None if rebuilt_p1 is None else round(rebuilt_p1, 3),
            "verdict": (("unmeasurable: cached is 0 at the edit turn in BOTH P1 and P3, "
                         "so the collapse fraction has no denominator")
                        if not attributable
                        else ("collapsed" if (post < 0.8 * pre and post < p1_post)
                              else "no collapse: the edit turn kept its prefix")),
        }

    # P2: is the pad real? measured delta vs P1 on the same turn, and alignment
    p2_alignment = None
    if "P1" in arms and "P2" in arms:
        p1pt = {int(r["turn"]): r["prompt_tokens"] for r in rows
                if r["arm"] == "P1" and isinstance(r["prompt_tokens"], int)}
        p2rows = sorted([r for r in rows if r["arm"] == "P2"], key=lambda r: int(r["turn"]))
        dd = [r["prompt_tokens"] - p1pt[int(r["turn"])] for r in p2rows
              if isinstance(r["prompt_tokens"], int) and int(r["turn"]) in p1pt]
        aligned = sum(1 for r in p2rows if isinstance(r["prompt_tokens"], int)
                      and r["prompt_tokens"] % grid == 0)
        p2_alignment = {
            "measured_pad_delta_tokens_mean": (round(sum(dd) / len(dd), 3) if dd else None),
            "measured_pad_delta_min": (min(dd) if dd else None),
            "measured_pad_delta_max": (max(dd) if dd else None),
            "predicted_pad_tokens_total": per_arm.get("P2", {}).get("pad_tokens_total"),
            "aligned_rows": aligned, "n_rows": len(p2rows),
            "aligned_fraction": (round(aligned / len(p2rows), 6) if p2rows else None),
            "note": "pad is real iff measured_pad_delta_tokens_mean > 0; a whitespace pad "
                    "is stripped by the chat template and reads as 0 (measured on O1 v1)",
        }

    # observed grid: the gcd of the cached values is the resolved cache unit
    from math import gcd as _gcd
    cached_vals = [int(r["cached_tokens"]) for r in rows
                   if isinstance(r["cached_tokens"], int) and int(r["cached_tokens"]) > 0]
    observed = 0
    for v in cached_vals:
        observed = _gcd(observed, v)

    return {
        "unit": "R2-PROMPT", "setup": setup_id, "config_id": setup["config_id"],
        "observed_cached_gcd": observed, "n_cached_vals": len(cached_vals),
        "config_sha256": setup["config_sha256"], "optimised_from": setup.get("optimised_from"),
        "best_config_sha256": setup.get("_best_config_sha256"),
        "model": setup["model"], "engine": setup["engine"], "grid_unit": grid,
        "token_ratio_chars": round(ratio, 8), "turns": TURNS, "budget_tokens": BUDGET_TOKENS,
        "arm_definitions": {"P0": "whole-context resend (renderer R)",
                            "P1": "pointer index + append-only newest delta (renderer A)",
                            "P2": "P1 + trailing-block grid alignment",
                            "P3": "P1 + one earlier index line rewritten once at turn %d" % EDIT_TURN},
        "g0": g0, "warmups": warm_rows, "arms": list(arms),
        "per_arm": per_arm, "deltas": deltas, "p3_survival": survival,
        "p2_alignment": p2_alignment,
        "n_rows": len(rows), "at": utc_now(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
