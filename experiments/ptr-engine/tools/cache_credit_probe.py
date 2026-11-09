#!/usr/bin/env python3
"""CACHE-CREDIT-CHAT — can per-request cache credit be measured on the endpoint the
runner actually calls?

The unit exists because `measure/ENDPOINT-STATE.json` probed `/v1/completions` and
concluded "no cached_tokens field, no cumulative counter".  `longrun/client.py:661`
posts to `/v1/chat/completions`.  A missing field on one endpoint is not a missing
capability on the other.

This probe spends at most 4 inference requests (2 non-stream, then 2 stream only if
the non-stream pair showed nothing), reads only free `/metrics` around each, and
journals every request as it is spent.

Usage:  python3 experiments/ptr-engine/tools/cache_credit_probe.py
"""
import json
import os
import sys
import time
import urllib.request

BASE = "http://192.168.2.168:8012"
CHAT = BASE + "/v1/chat/completions"
METRICS = BASE + "/metrics"
MODEL = "occamy-1.0"
MAX_REQUESTS = 4
HERE = os.path.dirname(os.path.abspath(__file__))
PTR = os.path.dirname(HERE)
OUT_JSON = os.path.join(PTR, "measure", "CACHE-CREDIT-CHAT.json")
JOURNAL = os.path.join(PTR, "..", "..", "orchestration", "journals",
                       "CACHE-CREDIT-CHAT.jsonl")

# Metrics that can carry cache credit, and how to fold repeated label series.
KEYS = ("sglang:cached_tokens_total", "sglang:cache_hit_rate",
        "sglang:uncached_prompt_tokens_histogram_sum",
        "sglang:uncached_prompt_tokens_histogram_count",
        "sglang:realtime_tokens_total")

requests_used = 0


def journal(event, **kw):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
           "unit": "CACHE-CREDIT-CHAT", "event": event}
    rec.update(kw)
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    with open(JOURNAL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def scrape():
    raw = urllib.request.urlopen(METRICS, timeout=20).read().decode("utf-8")
    out, lines = {}, {}
    for line in raw.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name = line.split("{", 1)[0].split(" ", 1)[0]
        if name in KEYS:
            lines.setdefault(name, []).append(line)
            try:
                out[name] = out.get(name, 0.0) + float(line.rsplit(" ", 1)[1])
            except ValueError:
                pass
    return {"folded": out, "raw_lines": {k: v for k, v in lines.items()},
            "bytes": len(raw)}


def post(body):
    global requests_used
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(CHAT, data=data,
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            http_status = resp.status
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # noqa: F821
        http_status = exc.code
        payload = {"error": exc.read().decode("utf-8", "replace")[:2000]}
    elapsed = round(time.time() - t0, 3)
    requests_used += 1
    journal("request", n=requests_used, stream=bool(body.get("stream")),
            http_status=http_status, elapsed_s=elapsed,
            usage=payload.get("usage"),
            prompt_chars=len(body["messages"][0]["content"]))
    return {"n": requests_used, "http_status": http_status, "elapsed_s": elapsed,
            "request_body_sha256_len": len(data), "payload": payload,
            "usage": payload.get("usage")}


def build_prompt(token_target=1400):
    # Unique nonce first so request 1 cannot be warm from any earlier probe.
    nonce = "CACHE-CREDIT-CHAT-%d" % int(time.time())
    para = ("The pointer-stable arm keeps a transcript of every resolved reference and "
            "re-sends it byte-identically each turn, so the prefix is stable across turns "
            "and the server's radix cache can credit the unchanged prefix. ")
    words, i = [], 0
    while len(" ".join(words).split()) < token_target:
        words.append(para + "segment %05d. " % i)
        i += 1
    return nonce + ". " + " ".join(words)


def pair(stream):
    prompt = build_prompt()
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4, "temperature": 0, "stream": stream}
    if stream:
        body["stream_options"] = {"include_usage": True}
    rows = []
    for i in range(2):
        before = scrape()
        r = post(body)
        after = scrape()
        delta = {}
        for k in KEYS:
            b = before["folded"].get(k)
            a = after["folded"].get(k)
            delta[k] = None if (b is None or a is None) else round(a - b, 3)
        rows.append({"which": "request1" if i == 0 else "request2",
                     "usage_verbatim": r["usage"],
                     "http_status": r["http_status"], "elapsed_s": r["elapsed_s"],
                     "metrics_before": before["folded"],
                     "metrics_after": after["folded"],
                     "metrics_delta": delta,
                     "cache_hit_rate_gauge_raw":
                         after["raw_lines"].get("sglang:cache_hit_rate"),
                     "content_sha_length": len(prompt)})
    return rows


def cached_of(usage):
    if not isinstance(usage, dict):
        return None
    d = usage.get("prompt_tokens_details")
    if isinstance(d, dict) and d.get("cached_tokens") is not None:
        return int(d["cached_tokens"])
    if usage.get("cached_tokens") is not None:
        return int(usage["cached_tokens"])
    return None


def main():
    journal("start", endpoint=BASE, cap=MAX_REQUESTS)
    result = {"unit": "CACHE-CREDIT-CHAT",
              "sampled_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "endpoint_under_test": BASE + "/v1",
              "model": MODEL,
              "request_cap": MAX_REQUESTS,
              "method": {"path": "/v1/chat/completions",
                         "prompt_tokens_target": 1400,
                         "max_tokens": 4, "temperature": 0,
                         "pair": "two byte-identical sends, same body object",
                         "stop_rule": "stop as soon as a cached count appears"},

              "nonstream": None, "stream": None}
    try:
        ns = pair(False)
        result["nonstream"] = ns
        got = [cached_of(r["usage_verbatim"]) for r in ns]
        delta2 = ns[1]["metrics_delta"].get("sglang:cached_tokens_total")
        if (got[1] or 0) > 0 or (delta2 or 0) > 0:
            result["stream"] = None
            result["stream_skipped_because"] = (
                "non-stream pair already showed credit: response no.2 cached_tokens=%r, "
                "cached_tokens_total delta=%r" % (got[1], delta2))
        else:
            st = pair(True)
            result["stream"] = st
    finally:
        result["requests_used"] = requests_used
        result["stopped_at"] = "cap" if requests_used >= MAX_REQUESTS else "answer"
        # Reproducibility of the published 0.8523 straight from TVS's own numerator.
        try:
            result["tvs_0_8523_recomputed"] = {
                "cached_tokens": 93568, "prompt_tokens": 109780,
                "ratio": round(93568 / 109780, 6),
                "matches_published_0_8523": round(93568 / 109780, 4) == 0.8523}
        except Exception as exc:  # pragma: no cover
            result["tvs_0_8523_recomputed"] = {"error": str(exc)}
        result["provenance_from_code"] = [
            "longrun/client.py:604 usage_cached_tokens() -> usage.prompt_tokens_details"
            ".cached_tokens (top-level cached_tokens not read; None, never 0, when absent)",
            "longrun/client.py:661 url = cfg.base_url.rstrip('/') + '/chat/completions'",
            "longrun/client.py:339-340 stream_options={'include_usage': True} when streaming",
            "longrun/run_longrun.py:1755-1757 row keys prompt_tokens / cached_tokens / "
            "uncached_tokens (uncached = prompt - cached, None when either is None)",
            "longrun/run_longrun.py:1699 cached = resp.get('cached_tokens')",
            "measure/TVS.json definition.cached_share = sum(cached_tokens)/sum(prompt_tokens) "
            "over rows whose cached_tokens is non-null",
        ]
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        tmp = OUT_JSON + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1, sort_keys=False)
            fh.write("\n")
        os.replace(tmp, OUT_JSON)
        journal("end", requests_used=requests_used, out=OUT_JSON)

    # compact console report
    for name in ("nonstream", "stream"):
        rows = result.get(name)
        if not rows:
            continue
        print("==", name)
        for r in rows:
            print(" ", r["which"], "http", r["http_status"],
                  "usage", json.dumps(r["usage_verbatim"]),
                  "d(cached_tokens_total)=",
                  r["metrics_delta"].get("sglang:cached_tokens_total"),
                  "d(hit_rate_gauge)=",
                  r["metrics_delta"].get("sglang:cache_hit_rate"))
    print("requests_used:", requests_used)
    return 0


if __name__ == "__main__":
    sys.exit(main())
