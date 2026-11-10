#!/usr/bin/env python3
"""Preflight cache probes P1-P4 for the context-serving campaign."""
import json, os, sys, time, uuid, subprocess, urllib.request
from pathlib import Path

CAMPAIGN = Path("/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN")
sys.path.insert(0, str(CAMPAIGN / "run"))
import driver

# corrected engine
def corrected_chat(self, messages, *, max_tokens, temperature, seed, run_id=None,
        arm=None, task_id=None, turn=None, timeout=180, engine_fingerprint=None,
        store=None, **kw):
    url = self.base_url + "/v1/chat/completions"
    payload = {"model": getattr(self, "model_name", "occamy-1.0"), "messages": messages,
               "max_tokens": max_tokens, "temperature": temperature, "seed": seed, "stream": False}
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
    return {"status": 200, "output": output, "text": output, "finish_reason": finish_reason,
            "usage": usage, "raw_usage": usage, "ttft_ms": wall, "wall_ms": wall,
            "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
            "cached_tokens": cached, "reasoning_tokens": usage.get("reasoning_tokens")}

driver.RealEngine.chat = corrected_chat

ENV_PATH = str(CAMPAIGN / "run/envelopes/CAMPAIGN.json")
env = driver.load_envelope(ENV_PATH)
LEDGER_DIR = str(CAMPAIGN / "ledger")
WATCHER_PATH = CAMPAIGN / "run/watcher/preflight.jsonl"
WATCHER_PATH.parent.mkdir(parents=True, exist_ok=True)

# start watcher
watcher_proc = subprocess.Popen(
    [sys.executable, str(CAMPAIGN / "tools/watcher.py"),
     "--envelope", ENV_PATH, "--phase", "preflight",
     "--driver-pid", str(os.getpid()), "--out", str(WATCHER_PATH), "--interval", "1"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
# wait for first event
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

engine = driver.RealEngine(env["endpoint"]["base_url"], timeout=env["limits"]["request_timeout_s"])
engine.model_name = env["endpoint"]["model"]

def metrics_snapshot():
    try:
        with urllib.request.urlopen("http://192.168.2.168:8012/metrics", timeout=10) as r:
            text = r.read().decode()
    except Exception as e:
        return {"error": str(e)}
    out = {}
    for line in text.splitlines():
        if line.startswith("sglang:cache_hit_rate{"):
            out["cache_hit_rate"] = float(line.split()[-1])
        if line.startswith("sglang:prefill_effective_tokens_total{"):
            # key by mode
            mode = None
            for part in line.split("{")[1].split("}")[0].split(","):
                if "mode=" in part:
                    mode = part.split("=")[1].strip('"')
            val = float(line.split()[-1])
            out.setdefault("prefill_effective_tokens_total", {})[mode] = val
        if line.startswith("sglang:uncached_prompt_tokens_histogram_count{"):
            out["uncached_prompt_tokens_histogram_count"] = float(line.split()[-1])
    return out

def do_call(prompt, label):
    # reserve
    attempt_id = driver._ledger_reserve("preflight", label, dry_run=False, ledger_dir=LEDGER_DIR)
    intent = {"attempt_id": attempt_id, "phase": "preflight", "arm": "probe",
              "task_id": "probe", "seed": None, "turn": None, "kind": "probe",
              "salt": None, "started_utc": driver._now()}
    # write intent to a probe intents file (not driver's)
    ipath = CAMPAIGN / "run/intents/preflight.probe.jsonl"
    with open(ipath, "a") as f:
        f.write(json.dumps(intent) + "\n"); f.flush(); os.fsync(f.fileno())
    with open(CAMPAIGN / "run/intents/preflight.jsonl", "a") as f:
        f.write(json.dumps(intent) + "\n"); f.flush(); os.fsync(f.fileno())
    # watcher check
    ok, msg = driver._watcher_ok(WATCHER_PATH)
    if not ok:
        print("WATCHER REFUSE:", msg, file=sys.stderr)
    # dispatch
    messages = [{"role": "user", "content": prompt}]
    try:
        resp = engine.chat(messages, max_tokens=env["limits"]["max_tokens"],
                           temperature=env["limits"]["temperature"], seed=42,
                           run_id=env["run_id"], timeout=env["limits"]["request_timeout_s"],
                           engine_fingerprint=env["endpoint"]["fingerprint_sha256"], store=None)
        outcome = "ok"
    except Exception as e:
        resp = None
        outcome = "failed"
        driver._ledger_record(attempt_id, "failed", usage=None, dry_run=False, ledger_dir=LEDGER_DIR)
        return attempt_id, None, str(e)
    usage = resp.get("raw_usage") or resp.get("usage") or {}
    driver._ledger_record(attempt_id, outcome, usage=usage, dry_run=False, ledger_dir=LEDGER_DIR)
    try:
        row = {"schema": "cs.row/1", "attempt_id": attempt_id, "run_id": env["run_id"],
               "phase": "preflight", "task_id": "probe", "arm": "probe", "seed": None,
               "rep": 1, "turn": None, "kind": "probe", "salt": None,
               "prompt_sha256": None,
               "prompt_tokens": resp.get("prompt_tokens") if resp else None,
               "cached_tokens": resp.get("cached_tokens") if resp else None,
               "completion_tokens": resp.get("completion_tokens") if resp else None,
               "reasoning_tokens": resp.get("reasoning_tokens") if resp else None,
               "ttft_ms": resp.get("ttft_ms") if resp else None,
               "wall_ms": resp.get("wall_ms") if resp else None,
               "finish_reason": resp.get("finish_reason") if resp else None,
               "raw_usage": (resp.get("raw_usage") if resp else None),
               "output": (resp.get("output") if resp else None),
               "grade": {"ok": None, "checks": []}}
        with open(CAMPAIGN / "run/rows/preflight.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n"); f.flush(); os.fsync(f.fileno())
    except Exception:
        pass
    return attempt_id, resp, None

SALT = "probe-salt-" + uuid.uuid4().hex[:8]
base_prompt = "You are a cache probe. Session: {salt}\nQuestion: What is the sum of 17 and 25? Answer with just the number."

# P1 COLD
p1_prompt = base_prompt.format(salt=SALT)
# warm? P1 is cold send
m_before_p2 = None
results = []

# P1
aid, resp, err = do_call(p1_prompt, "preflight:probe:P1_cold")
results.append(("P1 COLD", SALT, resp, err, aid))
time.sleep(0.5)

# P2 REPEAT x2
metrics_before = metrics_snapshot()
p2_cached = []
for i in range(2):
    aid, resp, err = do_call(p1_prompt, f"preflight:probe:P2_repeat_{i+1}")
    results.append((f"P2 REPEAT {i+1}", SALT, resp, err, aid))
    if resp is not None:
        p2_cached.append(resp.get("cached_tokens"))
    time.sleep(0.5)
metrics_after = metrics_snapshot()

# P3 SALT DIVERGENCE: same content, different salt early
salt2 = "probe-salt-" + uuid.uuid4().hex[:8]
p3_prompt = base_prompt.format(salt=salt2)
aid, resp, err = do_call(p3_prompt, "preflight:probe:P3_saltdiv")
results.append(("P3 SALT DIVERGENCE", salt2, resp, err, aid))
time.sleep(0.5)

# P4 FIRST-BYTE DIVERGENCE: change first byte
p4_prompt = "X" + base_prompt.format(salt=SALT)[1:]
aid, resp, err = do_call(p4_prompt, "preflight:probe:P4_firstbyte")
results.append(("P4 FIRST-BYTE DIVERGENCE", SALT, resp, err, aid))

# print table
print("\n=== PREFLIGHT PROBE TABLE ===")
print(f"{'Probe':28s} {'prompt_tokens':>14s} {'cached_tokens':>14s} {'completion':>11s} {'finish':>8s} {'ttft_ms':>10s}")
for name, salt, resp, err, aid in results:
    if err:
        print(f"{name:28s} ERROR: {err}")
        continue
    u = resp.get("raw_usage") or {}
    pt = resp.get("prompt_tokens")
    ct = resp.get("cached_tokens")
    comp = resp.get("completion_tokens")
    fr = resp.get("finish_reason")
    ttft = resp.get("ttft_ms")
    print(f"{name:28s} {str(pt):>14s} {str(ct):>14s} {str(comp):>11s} {str(fr):>8s} {ttft:>10.1f}")

print("\n=== SERVER METRICS ===")
print("before P2:", json.dumps(metrics_before))
print("after  P2:", json.dumps(metrics_after))
# delta
def delta(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        out = {}
        for k in set(a) | set(b):
            if isinstance(a.get(k), dict) or isinstance(b.get(k), dict):
                out[k] = delta(a.get(k, {}), b.get(k, {}))
            else:
                out[k] = (b.get(k, 0) or 0) - (a.get(k, 0) or 0)
        return out
    return None
print("delta:", json.dumps(delta(metrics_before, metrics_after)))

# save results
out = {
    "results": [{"name": n, "salt": s,
                 "prompt_tokens": (r.get("prompt_tokens") if r else None),
                 "cached_tokens": (r.get("cached_tokens") if r else None),
                 "completion_tokens": (r.get("completion_tokens") if r else None),
                 "finish_reason": (r.get("finish_reason") if r else None),
                 "ttft_ms": (r.get("ttft_ms") if r else None),
                 "attempt_id": a, "error": e} for (n, s, r, e, a) in results],
    "metrics_before": metrics_before,
    "metrics_after": metrics_after,
    "metrics_delta": delta(metrics_before, metrics_after),
}
art = CAMPAIGN / "run/artifacts/preflight"
art.mkdir(parents=True, exist_ok=True)
(art / "probe_results.json").write_text(json.dumps(out, indent=2))
print("\nSaved", art / "probe_results.json")

# terminate watcher
watcher_proc.terminate()
try:
    watcher_proc.wait(timeout=5)
except Exception:
    watcher_proc.kill()
