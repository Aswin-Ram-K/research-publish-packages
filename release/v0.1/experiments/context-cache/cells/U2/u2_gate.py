"""U2 instrument-gate + E2 64-token-tax sweep against live Occamy.

Uses the unit-owned instrument verbatim:
  * experiments/context-cache/client.py : ChatClient.chat  (HTTP, streaming)
  * src/resextract/context/            : make_salt, normalise_cache, CacheRow

Raw usage capture: client.py imports ``normalise_cache`` into its own module
namespace, so we patch that name with a recorder that stores the *raw* usage
dict (or None) appended to ``normalise_cache(usage)`` and then delegates.  The
HTTP request itself is still made by the instrument's client.

Never calls /flush_cache.  Cold isolation = fresh per-cell salt.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from resextract.context import CacheRow, CacheMeter, make_salt, normalise_cache  # noqa: E402
from resextract.context.meter import rows_from_jsonl  # noqa: E402

BASE_URL = "http://serving-host"
CELL_DIR = Path(__file__).resolve().parent
EXP_DIR = CELL_DIR.parents[1]
LOCK_PATH = EXP_DIR / ".occamy.lock"
ROWS_PATH = CELL_DIR / "u2_rows.jsonl"
REPORT_PATH = CELL_DIR / "u2_report.json"
CONFIG_PATH = CELL_DIR / "server_config.json"
RAW_PATH = CELL_DIR / "u2_raw_usage.jsonl"

MODEL = "occamy-1.0"
MAX_TOKENS = 8
REQUEST_BUDGET = 200
LOCK_WAIT_S = 1800


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_client_module():
    spec = importlib.util.spec_from_file_location(
        "ctx_client", EXP_DIR / "client.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # dataclasses resolve annotations via sys.modules[cls.__module__]
    sys.modules["ctx_client"] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# Lock + server archive
# --------------------------------------------------------------------------- #
def acquire_lock() -> tuple[int, float]:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_RDWR, 0o644)
    started = time.time()
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd, time.time() - started
        except BlockingIOError:
            if time.time() - started > LOCK_WAIT_S:
                os.close(fd)
                raise TimeoutError("could not acquire .occamy.lock within 1800s")
            time.sleep(1.0)


def archive_server_config() -> dict:
    import httpx

    out: dict = {"captured_utc": utcnow(), "base_url": BASE_URL}
    with httpx.Client(timeout=30.0) as http:
        for name, path in (("server_info", "/server_info"), ("get_model_info", "/get_model_info")):
            resp = http.get(BASE_URL + path)
            raw = resp.content
            out[name] = {
                "url": BASE_URL + path,
                "http_status": resp.status_code,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "body": json.loads(raw.decode("utf-8")),
            }
    CONFIG_PATH.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
WORDS = (
    "alpha bravo cedar delta ember fjord gamma harbor indigo juniper kestrel lantern "
    "meadow nectar onyx prairie quartz raven saffron tundra umber violet willow xenon "
    "yarrow zephyr amber basalt cobalt dune elder flint garnet hazel iris jade kelp "
    "larch moss nickel opal pine quill reed slate thistle ultramarine verdigris wheat "
    "yew zinc acorn birch cinder dogwood elm fern grove heath ivy linden maple olive "
    "pebble rowan spruce tamarack vine walnut aspen willowherb cactus bramble"
).split()

INSTRUCTION = (
    "You are a precise assistant used for a metering experiment. "
    "Read the notes below and reply with the single word OK."
)


def build_messages(salt_seed: int, n_sentences: int, seed: int) -> list[dict[str, str]]:
    salt = make_salt(salt_seed)
    rng = random.Random(seed)
    sentences = []
    for _ in range(n_sentences):
        words = [rng.choice(WORDS) for _ in range(rng.randint(12, 18))]
        sentences.append(" ".join(words) + ".")
    system = f"[cell-{salt}]\n{INSTRUCTION}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": " ".join(sentences)},
    ]


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    t_start = time.time()
    lock_fd, lock_wait = acquire_lock()
    requests_made = 0
    coerced = 0
    raw_events: list[dict] = []
    failures_in_a_row = 0

    client_mod = load_client_module()
    client = client_mod.ChatClient()

    orig_normalise = client_mod.normalise_cache

    def recorder(usage):
        nonlocal coerced
        raw = None if usage is None else dict(usage)
        raw_events.append({"utc": utcnow(), "usage": raw})
        if usage is None:
            coerced += 1
        else:
            details = usage.get("prompt_tokens_details")
            if details is None:
                coerced += 1
        return orig_normalise(usage)

    client_mod.normalise_cache = recorder

    def send(messages, tag: str, salt: str, n_sentences: int):
        """One live request; returns dict.  Counts budget, retries once via client."""
        nonlocal requests_made, failures_in_a_row
        if requests_made >= REQUEST_BUDGET:
            raise RuntimeError(f"request budget {REQUEST_BUDGET} exhausted at tag={tag}")
        requests_made += 1
        before = len(raw_events)
        try:
            (prompt, cached, completion, ttft, wall, status, text) = client.chat(
                messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=120.0
            )
            failures_in_a_row = 0
        except Exception as exc:  # noqa: BLE001
            failures_in_a_row += 1
            raw_events.append({"utc": utcnow(), "usage": None, "error": str(exc), "tag": tag})
            if failures_in_a_row >= 3:
                raise RuntimeError(f"STOP: 3 consecutive failures; last={exc!r}") from exc
            raise
        raw_usage = raw_events[before]["usage"] if len(raw_events) > before else None
        return {
            "tag": tag,
            "salt": salt,
            "n_sentences": n_sentences,
            "prompt_tokens": prompt,
            "cached_tokens": cached,
            "uncached": prompt - cached,
            "residual": (prompt - cached) - (prompt % 64),
            "ttft_ms": ttft,
            "wall_ms": wall,
            "completion_tokens": completion,
            "status": status,
            "text": text,
            "raw_usage": raw_usage,
            "details_present": bool(
                isinstance(raw_usage, dict) and raw_usage.get("prompt_tokens_details") is not None
            ),
        }

    def write_rows(rows: list[dict], path: Path) -> None:
        with path.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")

    print(f"[lock] acquired after {lock_wait:.2f}s -> {LOCK_PATH}", flush=True)
    cfg = archive_server_config()
    print(f"[archive] {CONFIG_PATH} sha256(server_info)={cfg['server_info']['sha256']}", flush=True)
    si = cfg["server_info"]["body"]
    print(
        f"[archive] page_size={si.get('page_size')} chunked_prefill={si.get('chunked_prefill_size')} "
        f"max_total={si.get('max_total_num_tokens')} max_running={si.get('max_running_requests')}",
        flush=True,
    )

    results: dict = {"utc_start": utcnow(), "base_url": BASE_URL, "model": MODEL}
    g0: dict = {}

    # ---------------- G0 ----------------
    g0_seed = 90001
    g0_msgs = build_messages(g0_seed, 30, seed=1)
    cold = send(g0_msgs, "G0-cold", make_salt(g0_seed), 30)
    print(f"[G0] cold L={cold['prompt_tokens']} cached={cold['cached_tokens']} "
          f"details_present={cold['details_present']}", flush=True)

    repeats = []
    for i in range(3):
        r = send(g0_msgs, f"G0-rep{i+1}", make_salt(g0_seed), 30)
        repeats.append(r)
        print(f"[G0] rep{i+1} L={r['prompt_tokens']} cached={r['cached_tokens']} "
              f"ttft={r['ttft_ms']:.1f}ms", flush=True)

    g0["cold"] = {k: cold[k] for k in ("prompt_tokens", "cached_tokens", "uncached", "raw_usage",
                                       "details_present", "status", "ttft_ms")}
    g0["repeat_cached"] = [r["cached_tokens"] for r in repeats]
    g0["repeat_prompt"] = [r["prompt_tokens"] for r in repeats]
    g0["ttft_ms"] = [round(r["ttft_ms"], 3) for r in repeats]
    g0["checks"] = {
        "cold_details_absent": (cold["raw_usage"] is None)
        or (cold["raw_usage"].get("prompt_tokens_details") is None),
        "cold_cached_zero": cold["cached_tokens"] == 0,
        "repeat_cached_positive": all(r["cached_tokens"] > 0 for r in repeats),
        "repeat_cached_le_prompt": all(r["cached_tokens"] <= r["prompt_tokens"] for r in repeats),
        "stream_single_pass_ttft_and_cache": all(r["ttft_ms"] > 0 and r["cached_tokens"] > 0
                                                 for r in repeats),
        "deterministic": len(set(g0["repeat_cached"])) == 1,
    }
    results["G0"] = g0
    print(f"[G0] checks={json.dumps(g0['checks'])}", flush=True)

    g0_ok = all(g0["checks"].values())
    if not g0_ok:
        results["verdict"] = {"G0": "FAIL", "E2": "not run"}
        results["utc_end"] = utcnow()
        results["requests_made"] = requests_made
        results["raw_coercions"] = coerced
        REPORT_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_rows([cold] + repeats, ROWS_PATH)
        with RAW_PATH.open("w", encoding="utf-8") as fh:
            for ev in raw_events:
                fh.write(json.dumps(ev, sort_keys=True) + "\n")
        print("[G0] FAIL -> E2 sweep NOT run", flush=True)
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
        return 0

    # ---------------- Short-prompt boundary (<64 tokens) ----------------
    short_seed = 91001
    short_msgs = [
        {"role": "system", "content": f"[cell-{make_salt(short_seed)}]\nReply OK."},
        {"role": "user", "content": "Say OK."},
    ]
    short1 = send(short_msgs, "BOUND-short-1", make_salt(short_seed), 0)
    short2 = send(short_msgs, "BOUND-short-2", make_salt(short_seed), 0)
    g0["short_boundary"] = {
        "prompt_tokens": [short1["prompt_tokens"], short2["prompt_tokens"]],
        "cached_tokens": [short1["cached_tokens"], short2["cached_tokens"]],
        "under_64": short1["prompt_tokens"] < 64,
        "cached_gt_zero": short1["cached_tokens"] > 0 or short2["cached_tokens"] > 0,
    }
    print(f"[bound] L={g0['short_boundary']['prompt_tokens']} cached={g0['short_boundary']['cached_tokens']}",
          flush=True)

    # ---------------- Calibration ----------------
    cal = send(build_messages(92001, 20, seed=2), "CAL", make_salt(92001), 20)
    per_sentence = max(1.0, (cal["prompt_tokens"] - 60) / 20.0)
    print(f"[cal] L(20 sentences)={cal['prompt_tokens']} -> ~{per_sentence:.2f} tok/sentence",
          flush=True)

    # ---------------- E2 sweep ----------------
    n_lo, n_hi = 10, 53  # 44 lengths, ~15 tok apart
    sweep: list[dict] = []
    rows: list[CacheRow] = []
    salts = iter(range(100000, 200000))
    for n in range(n_lo, n_hi + 1):
        salt_seed = next(salts)
        msgs = build_messages(salt_seed, n, seed=1000 + n)
        csalt = msgs[0]["content"][6:22]
        assert csalt == make_salt(salt_seed)
        cold_r = send(msgs, f"E2-{n}-cold", csalt, n)
        warm_r = send(msgs, f"E2-{n}-warm", csalt, n)
        for i, r in enumerate((cold_r, warm_r)):
            rows.append(CacheRow(
                cell="U2-E2", arm="cold" if i == 0 else "warm", policy="salted-fresh",
                case_id=f"n{n}", turn=i, rep=n, salt=csalt,
                prompt_tokens=r["prompt_tokens"], cached_tokens=r["cached_tokens"],
                uncached=r["uncached"], ttft_ms=r["ttft_ms"], wall_ms=r["wall_ms"],
                completion_tokens=r["completion_tokens"], status=r["status"],
                evicted=False, prefix_sha256=hashlib.sha256(
                    json.dumps(msgs, sort_keys=True).encode()).hexdigest(),
            ))
        sweep.append({
            "n": n, "salt": csalt,
            "L": warm_r["prompt_tokens"],
            "cold_cached": cold_r["cached_tokens"],
            "cold_uncached": cold_r["uncached"],
            "cached": warm_r["cached_tokens"],
            "uncached": warm_r["uncached"],
            "residual": warm_r["residual"],
            "resid_mod64": warm_r["prompt_tokens"] % 64,
            "ttft_ms": round(warm_r["ttft_ms"], 2),
            "status": [cold_r["status"], warm_r["status"]],
            "raw_usage_warm": warm_r["raw_usage"],
        })
        print(f"[E2] n={n:2d} L={warm_r['prompt_tokens']:4d} coldC={cold_r['cached_tokens']:4d} "
              f"cached={warm_r['cached_tokens']:4d} unc={warm_r['uncached']:3d} "
              f"resid={warm_r['residual']:+3d}", flush=True)

    # ---------------- Chunked-prefill boundary (>8192 tokens) ----------------
    chunk_n = 580  # ~15-18 tok/sentence -> ~9k tokens, past the 8192 chunk
    long_msgs = build_messages(93001, chunk_n, seed=3)
    long_cold = send(long_msgs, "LONG-cold", make_salt(93001), chunk_n)
    long_warm = send(long_msgs, "LONG-warm", make_salt(93001), chunk_n)
    chunk_probe = {
        "n_sentences": chunk_n,
        "prompt_tokens": long_warm["prompt_tokens"],
        "cached": long_warm["cached_tokens"],
        "uncached": long_warm["uncached"],
        "residual": long_warm["residual"],
        "cold_cached": long_cold["cached_tokens"],
        "exceeds_chunked_prefill_8192": long_warm["prompt_tokens"] > 8192,
    }
    print(f"[chunk] L={long_warm['prompt_tokens']} cached={long_warm['cached_tokens']} "
          f"unc={long_warm['uncached']} resid={long_warm['residual']:+d}", flush=True)

    # ---------------- Analysis ----------------
    residuals = [r["residual"] for r in sweep]
    res_mod = [r["resid_mod64"] for r in sweep]
    lengths = [r["L"] for r in sweep]
    sweep_pass = [r for r in sweep if r["cold_cached"] == 0]
    residual_pass = [r["residual"] for r in sweep_pass]
    big = [r for r in sweep_pass if abs(r["residual"]) > 32]

    e2 = {
        "lengths_tested": len(sweep),
        "distinct_residues_mod64": len(set(res_mod)),
        "residues_mod64": sorted(set(res_mod)),
        "length_min": min(lengths),
        "length_max": max(lengths),
        "lengths_ge_512": sum(1 for L in lengths if L >= 512),
        "distinct_cached_values": len({r["cached"] for r in sweep}),
        "residual_values": residuals,
        "residual_histogram": {str(v): residuals.count(v) for v in sorted(set(residuals))},
        "residual_mean": sum(residuals) / len(residuals),
        "residual_max_abs": max(abs(v) for v in residuals),
        "n_residual_zero": sum(1 for v in residuals if v == 0),
        "n_abs_residual_gt_32": len(big),
        "residual_pass_only_max_abs": max(abs(v) for v in residual_pass),
        "n_residual_zero_pass_only": sum(1 for v in residual_pass if v == 0),
        "cold_cached_nonzero": [r["n"] for r in sweep if r["cold_cached"] != 0],
        "chunked_prefill_probe": chunk_probe,
        "tax_law_verdict": "REFUTED" if len(big) >= 2 else "CONFIRMED",
        "note_chunked_prefill": (
            "all sweep L < 8192 so chunked prefill never splits a prompt; "
            f"single >8192 probe residual={chunk_probe['residual']:+d}"
        ),
    }
    results["E2"] = e2
    results["verdict"] = {
        "G0": "PASS" if g0_ok else "FAIL",
        "E2_tax_law": e2["tax_law_verdict"],
    }
    results["utc_end"] = utcnow()
    results["wall_seconds"] = round(time.time() - t_start, 2)
    results["requests_made"] = requests_made
    results["raw_coercions_null_to_zero"] = coerced
    results["raw_usage_events"] = len(raw_events)
    results["lock_wait_seconds"] = round(lock_wait, 3)

    REPORT_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_rows(sweep, ROWS_PATH)
    meter = CacheMeter()
    for row in rows:
        meter.record(row)
    meter.to_jsonl(CELL_DIR / "u2_cache_rows.jsonl")
    with RAW_PATH.open("w", encoding="utf-8") as fh:
        for ev in raw_events:
            fh.write(json.dumps(ev, sort_keys=True) + "\n")

    print(f"[done] requests={requests_made} coercions={coerced} wall={results['wall_seconds']}s",
          flush=True)
    print(f"[done] E2 verdict={e2['tax_law_verdict']} max|resid|={e2['residual_max_abs']}", flush=True)

    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
