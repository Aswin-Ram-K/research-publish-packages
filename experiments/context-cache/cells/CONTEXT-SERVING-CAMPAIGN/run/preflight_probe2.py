#!/usr/bin/env python3
"""Cache accounting probe 2: request shapes, repeats, mamba alignment, prompt sizes."""
import json, os, sys, time, uuid, subprocess, urllib.request, urllib.error
from pathlib import Path

CAMPAIGN = Path("/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN")
sys.path.insert(0, str(CAMPAIGN / "run"))
import driver

def corrected_chat(self, messages, *, max_tokens, temperature, seed, run_id=None,
        arm=None, task_id=None, turn=None, timeout=180, engine_fingerprint=None,
        store=None, extra_body=None, **kw):
    url = self.base_url + "/v1/chat/completions"
    payload = {"model": getattr(self, "model_name", "occamy-1.0"), "messages": messages,
               "max_tokens": max_tokens, "temperature": temperature, "seed": seed, "stream": False}
    # merge candidate fields
    for k in ("return_meta_info", "return_cached_tokens_details", "return_meta",
              "return_cached_tokens", "return_prompt_token_ids", "return_token_ids"):
        if k in kw:
            payload[k] = kw.pop(k)
    if extra_body:
        payload.update(extra_body)
    # any remaining kw
    payload.update(kw)
    t0 = time.time()
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    wall = (time.time() - t0) * 1000.0
    obj = json.loads(raw)
    choice = (obj.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    output = msg.get("content", "")
    finish_reason = choice.get("finish_reason", "stop")
    usage = obj.get("usage") or {}
    cached = usage.get("cached_tokens")
    if cached is None and isinstance(usage.get("prompt_tokens_details"), dict):
        cached = usage["prompt_tokens_details"].get("cached_tokens")
    meta = choice.get("meta_info")
    sglext = obj.get("sglext")
    return {"status": 200, "output": output, "text": output, "finish_reason": finish_reason,
            "usage": usage, "raw_usage": usage, "ttft_ms": wall, "wall_ms": wall,
            "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
            "cached_tokens": cached, "reasoning_tokens": usage.get("reasoning_tokens"),
            "meta_info": meta, "sglext": sglext, "raw_obj": obj}

driver.RealEngine.chat = corrected_chat

ENV_PATH = str(CAMPAIGN / "run/envelopes/CAMPAIGN.json")
env = driver.load_envelope(ENV_PATH)
LEDGER_DIR = str(CAMPAIGN / "ledger")
BASE_URL = env["endpoint"]["base_url"]
MODEL = env["endpoint"]["model"]

WATCHER_PATH = CAMPAIGN / "run/watcher/preflight.jsonl"
WATCHER_PATH.parent.mkdir(parents=True, exist_ok=True)
watcher_proc = subprocess.Popen(
    [sys.executable, str(CAMPAIGN / "tools/watcher.py"),
     "--envelope", ENV_PATH, "--phase", "preflight",
     "--driver-pid", str(os.getpid()), "--out", str(WATCHER_PATH), "--interval", "1"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
deadline = time.time() + 10
while time.time() < deadline:
    if WATCHER_PATH.exists():
        try:
            lines = [l for l in WATCHER_PATH.read_text().splitlines() if l.strip()]
            if lines:
                break
        except Exception:
            pass
    time.sleep(0.5)

engine = driver.RealEngine(BASE_URL, timeout=env["limits"]["request_timeout_s"])
engine.model_name = MODEL

def tokenize(text):
    data = json.dumps({"model": MODEL, "prompt": text}).encode()
    req = urllib.request.Request(BASE_URL + "/tokenize", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        obj = json.loads(resp.read())
    return int(obj.get("count", 0)), obj.get("tokens", [])

def metrics_snapshot():
    try:
        with urllib.request.urlopen(BASE_URL.replace("/v1","") + "/metrics" if False else "http://192.168.2.168:8012/metrics", timeout=10) as r:
            text = r.read().decode()
    except Exception as e:
        return {"error": str(e)}
    out = {"cache_hit_rate": None, "prefill_effective_tokens_total": {}, "uncached_prompt_tokens_histogram_count": None}
    for line in text.splitlines():
        if line.startswith("sglang:cache_hit_rate{") or line.startswith("sglang:cache_hit_rate "):
            try: out["cache_hit_rate"] = float(line.split()[-1])
            except: pass
        if line.startswith("sglang:prefill_effective_tokens_total{"):
            mode = None
            for part in line.split("{")[1].split("}")[0].split(","):
                if "mode=" in part:
                    mode = part.split("=")[1].strip('"')
            try: out["prefill_effective_tokens_total"][mode] = float(line.split()[-1])
            except: pass
        if line.startswith("sglang:uncached_prompt_tokens_histogram_count{"):
            try: out["uncached_prompt_tokens_histogram_count"] = float(line.split()[-1])
            except: pass
    return out

def build_prompt(target_tokens):
    # find a prompt whose total token count is a multiple of target_tokens's nearest? 
    # We want total count divisible by 256 and >= target_tokens.
    unit = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    suffix = "\n\nQuestion: What is 2+2? Answer with just the number."
    text = "You are a cache probe. Analyze the text and answer.\n\n"
    # grow
    while True:
        c, _ = tokenize(text + suffix)
        if c >= target_tokens:
            break
        text += unit
    # adjust down to exact multiple of 256 >= target_tokens
    target_mod = (target_tokens // 256) * 256
    if target_mod < 256:
        target_mod = 256
    # We want count divisible by 256 and >= target_tokens
    desired = target_tokens
    while desired % 256 != 0:
        desired += 1
    # grow/shrink
    # try removing units
    while True:
        c, _ = tokenize(text + suffix)
        if c <= desired:
            break
        # remove one unit from end of body
        idx = text.rfind(unit)
        if idx == -1:
            break
        text = text[:idx]
    # now grow by words until exact
    words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
    wi = 0
    guard = 0
    while True:
        c, _ = tokenize(text + suffix)
        if c == desired:
            break
        if c < desired:
            text += words[wi % len(words)] + " "
            wi += 1
        else:
            # overshoot: remove last added word
            # find last space
            ls = text.rfind(" ")
            if ls == -1:
                break
            text = text[:ls+1]
        guard += 1
        if guard > 5000:
            break
    final = text + suffix
    c, _ = tokenize(final)
    return final, c

def do_call(prompt, label, extra_fields=None, max_tokens=256):
    attempt_id = driver._ledger_reserve("preflight", label, dry_run=False, ledger_dir=LEDGER_DIR)
    intent = {"attempt_id": attempt_id, "phase": "preflight", "arm": "probe2",
              "task_id": "probe2", "seed": 42, "turn": None, "kind": "probe2",
              "salt": None, "started_utc": driver._now()}
    ipath = CAMPAIGN / "run/intents/preflight.jsonl"
    with open(ipath, "a") as f:
        f.write(json.dumps(intent) + "\n"); f.flush(); os.fsync(f.fileno())
    ok, msg = driver._watcher_ok(WATCHER_PATH)
    if not ok:
        print("WATCHER REFUSE:", msg, file=sys.stderr)
    kw = {"return_meta_info": True, "return_cached_tokens_details": True}
    if extra_fields:
        kw.update(extra_fields)
    messages = [{"role": "user", "content": prompt}]
    try:
        resp = engine.chat(messages, max_tokens=max_tokens,
                           temperature=env["limits"]["temperature"], seed=42,
                           run_id=env["run_id"], timeout=env["limits"]["request_timeout_s"],
                           engine_fingerprint=env["endpoint"]["fingerprint_sha256"], store=None,
                           extra_body=None, **kw)
        outcome = "ok"
        err = None
    except Exception as e:
        resp = None
        outcome = "failed"
        err = str(e)
        driver._ledger_record(attempt_id, "failed", usage=None, dry_run=False, ledger_dir=LEDGER_DIR)
        return attempt_id, None, err, None
    usage = resp.get("raw_usage") or resp.get("usage") or {}
    driver._ledger_record(attempt_id, outcome, usage=usage, dry_run=False, ledger_dir=LEDGER_DIR)
    try:
        row = {"schema": "cs.row/1", "attempt_id": attempt_id, "run_id": env["run_id"],
               "phase": "preflight", "task_id": "probe2", "arm": "probe2", "seed": 42,
               "rep": 1, "turn": None, "kind": "probe2", "salt": None,
               "prompt_sha256": None,
               "prompt_tokens": resp.get("prompt_tokens"),
               "cached_tokens": resp.get("cached_tokens"),
               "completion_tokens": resp.get("completion_tokens"),
               "reasoning_tokens": resp.get("reasoning_tokens"),
               "ttft_ms": resp.get("ttft_ms"),
               "wall_ms": resp.get("wall_ms"),
               "finish_reason": resp.get("finish_reason"),
               "raw_usage": (resp.get("raw_usage") if resp else None),
               "meta_info_cached_tokens": (resp.get("meta_info") or {}).get("cached_tokens") if resp else None,
               "sglext": resp.get("sglext"),
               "output": (resp.get("output") if resp else None)[:200],
               "grade": {"ok": None, "checks": []}}
        with open(CAMPAIGN / "run/rows/preflight.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n"); f.flush(); os.fsync(f.fileno())
    except Exception:
        pass
    return attempt_id, resp, None, None

results = []

# Hypothesis 2: 3 identical repeats, small prompt (reuse P1 style)
small_prompt = "You are a cache probe. Session: fixed-salt-abc\nQuestion: What is the sum of 17 and 25? Answer with just the number."
# H2 series
m_before = metrics_snapshot()
h2_metrics = [m_before]
h2_resps = []
for i in range(3):
    aid, resp, err, _ = do_call(small_prompt, f"probe2:H2_repeat_{i+1}",
                                extra_fields={"return_meta": True, "return_cached_tokens": True})
    time.sleep(0.5)
    ms = metrics_snapshot()
    h2_metrics.append(ms)
    h2_resps.append((aid, resp, err, ms))
    print(f"H2 repeat {i+1}: err={err} prompt_tokens={resp.get('prompt_tokens') if resp else None} "
          f"cached={resp.get('cached_tokens') if resp else None} meta_cached={(resp.get('meta_info') or {}).get('cached_tokens') if resp else None} "
          f"sglext={resp.get('sglext') if resp else None}")

# Hypothesis 3/4: exact multiple of 256, ~1200 and ~2600
for target in (1200, 2600):
    prompt, tokcount = build_prompt(target)
    print(f"Built prompt target~{target}: actual_tokens={tokcount}")
    # verify multiple
    assert tokcount % 256 == 0, f"not multiple: {tokcount}"
    m0 = metrics_snapshot()
    r1 = do_call(prompt, f"probe2:align_{tokcount}_cold")
    time.sleep(0.5)
    m1 = metrics_snapshot()
    r2 = do_call(prompt, f"probe2:align_{tokcount}_repeat")
    time.sleep(0.5)
    m2 = metrics_snapshot()
    results.append((tokcount, m0, r1, m1, r2, m2, prompt))
    print(f"align {tokcount}: cold cached={r1[1].get('cached_tokens') if r1[1] else None} "
          f"meta={(r1[1].get('meta_info') or {}).get('cached_tokens') if r1[1] else None}; "
          f"repeat cached={r2[1].get('cached_tokens') if r2[1] else None} "
          f"meta={(r2[1].get('meta_info') or {}).get('cached_tokens') if r2[1] else None}")

# save artifact
out = {
    "h2": {"metrics": h2_metrics, "resps": [
        {"attempt_id": a, "prompt_tokens": (r.get("prompt_tokens") if r else None),
         "cached_tokens": (r.get("cached_tokens") if r else None),
         "meta_cached": ((r.get("meta_info") or {}).get("cached_tokens") if r else None),
         "sglext": (r.get("sglext") if r else None),
         "finish_reason": (r.get("finish_reason") if r else None),
         "raw_usage": (r.get("raw_usage") if r else None),
         "error": e} for (a, r, e, ms) in h2_resps]},
    "align": [{"tokens": t, "cold_meta_cached": ((r1[1].get("meta_info") or {}).get("cached_tokens") if r1[1] else None),
               "repeat_meta_cached": ((r2[1].get("meta_info") or {}).get("cached_tokens") if r2[1] else None),
               "cold_cached": (r1[1].get("cached_tokens") if r1[1] else None),
               "repeat_cached": (r2[1].get("cached_tokens") if r2[1] else None),
               "metrics_before_cold": m0, "metrics_after_cold": m1, "metrics_after_repeat": m2,
               "prompt_head": prompt[:120]} for (t, m0, r1, m1, r2, m2, prompt) in results],
}
art = CAMPAIGN / "run/artifacts/preflight"
art.mkdir(parents=True, exist_ok=True)
(art / "probe2_results.json").write_text(json.dumps(out, indent=2))
print("\nSaved", art / "probe2_results.json")

watcher_proc.terminate()
try: watcher_proc.wait(timeout=5)
except Exception: watcher_proc.kill()
