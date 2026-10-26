"""AVALANCHE-INSERT probe: characterise the residue-{0,1} insertion avalanche on vLLM :8014, B=1056.

Instrument: delta of vllm:prompt_tokens_cached_total across ONE serialized request (sole writer).
Second, independent instrument: client TTFT and server TTFT histogram delta.
Cold state: unique NONCE per rep (permutation of 10 one-token words) -> constant 10 tokens.
No /flush_cache, no restart.
"""
from __future__ import annotations
import http.client, importlib.util, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "rows.jsonl")
LOG = os.path.join(HERE, "log.txt")
HOST, PORT = "192.168.2.168", 8014
BASE = f"http://{HOST}:{PORT}"
MODEL = "qwen3.5-9b"
B = 1056
BLOCKFRAME = 64          # OBSERVED conservative min (160th token of block k+1 differs -> loose block
                         # <=159 tokens); see REPORT.md "block size" note. Used only for the H* model.

_spec = importlib.util.spec_from_file_location("ml_run", os.path.join(ROOT, "run.py"))
ml = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ml)
CFG = ml.SERVERS["vllm"]
LBL = 'engine="0",model_name="qwen3.5-9b"'
K_CACHED = "vllm:prompt_tokens_cached_total{%s}" % LBL
K_HITS = "vllm:prefix_cache_hits_total{%s}" % LBL
K_QUER = "vllm:prefix_cache_queries_total{%s}" % LBL
K_PTOT = "vllm:prompt_tokens_total{%s}" % LBL
K_KV = "vllm:request_prefill_kv_computed_tokens"
K_TTFT = "vllm:time_to_first_token_seconds"
HS = "_sum{" + LBL + "}"; HC = "_count{" + LBL + "}"
FILLER_CACHE = os.path.join(HERE, "_filler.json")

def snap():
    with urllib.request.urlopen(BASE + "/metrics", timeout=60) as r:
        txt = r.read().decode()
    out = {}
    for line in txt.splitlines():
        if not line or line[0] == "#": continue
        i = line.rfind(" ")
        try: out[line[:i]] = float(line[i+1:])
        except ValueError: pass
    return out

def dd(p, q, k): return q.get(k, 0.0) - p.get(k, 0.0)

def chat_stream(messages, max_tokens=1):
    body = json.dumps({"model": MODEL, "messages": messages, "max_tokens": max_tokens,
                       "temperature": 0.0, "stream": True,
                       "stream_options": {"include_usage": True}}).encode()
    usage, first, err = None, None, None
    conn = http.client.HTTPConnection(HOST, PORT, timeout=900)
    t = time.time()
    tbytes = None
    try:
        conn.request("POST", "/v1/chat/completions", body, {"Content-Type": "application/json"})
        r = conn.getresponse()
        tbytes = time.time() - t
        if r.status != 200:
            err = "HTTP %d: %s" % (r.status, r.read()[:200].decode("utf-8", "replace"))
        else:
            while True:
                line = r.readline()
                if not line: break
                s = line.strip()
                if not s.startswith(b"data:"): continue
                p = s[5:].strip()
                if p == b"[DONE]": break
                try: obj = json.loads(p)
                except Exception: continue
                if obj.get("usage"): usage = obj["usage"]
                for ch in obj.get("choices") or []:
                    d = ch.get("delta") or {}
                    if first is None and (d.get("content") or d.get("reasoning_content")):
                        first = time.time() - t
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:250]}"
    finally:
        conn.close()
    ttft = first if first is not None else tbytes
    return usage, ttft, time.time() - t, err

def tok_count(cfg, text):
    """Uncached token count: this unit varies the tail of every filler, so the parent's cached
    builder would report a stale count for a new string of the same cache key."""
    j = ml.http_json(cfg["base"] + cfg["tok_path"], {"model": cfg["model"], "prompt": text})
    n = j.get("count")
    return int(n if n is not None else len(j.get("tokens") or j.get("token_ids") or []))

_FC = json.load(open(FILLER_CACHE)) if os.path.exists(FILLER_CACHE) else {}
def gen_filler(n):
    """A filler string of EXACTLY n tokens, verified on the server: one sentence per line plus
    ' the' padding, then repaired by whole-' the' nudges (never by touching the newline tail)."""
    k = str(n)
    if k not in _FC:
        txt = ml.build_filler(n, CFG) + " the the" * (1 + len(_FC) % 3)
        for _ in range(200):
            got = tok_count(CFG, txt)
            if got == n:
                break
            if got < n:
                txt = txt + " the" * (n - got)
            else:
                trimmed = txt.rstrip()
                if "\n" in txt[len(trimmed):] or trimmed.endswith("the") is False:
                    txt = trimmed
                else:
                    txt = trimmed[:-4] if trimmed.endswith(" the") else trimmed
        assert tok_count(CFG, txt) == n, (n, tok_count(CFG, txt))
        _FC[k] = txt
        json.dump(_FC, open(FILLER_CACHE, "w"))
    return _FC[k]

FRAME = 53   # pinned empirically: system+user message frame is 53 tokens on this build

def prime_msgs(tok):
    """Prime whose prompt_tokens is EXACTLY `tok`; NONCE is a unique 10-token permutation."""
    nonce = ml.make_nonce("av-%d-%d" % (tok, time.time_ns() % 10**9), len(USED), USED)
    msgs = [{"role": "system",
             "content": nonce + "\n\n" + gen_filler(tok - FRAME) + "\n\n" + ml.QUESTION},
            {"role": "user", "content": "Reply with the single word OK."}]
    return msgs

USED = set()

def app(msgs, n):
    return msgs + [{"role": "assistant", "content": "OK."}, {"role": "user", "content": " the" * n}]

def Hstar(n, Bp=BLOCKFRAME):
    """Predicted number of FULL hash-chain blocks creatable from a prefix of n tokens."""
    if n < Bp: return 0
    return 1 + (n - Bp) // Bp

def req(fd, log, *, arm, pair_id, role, idx, msgs, target_P1, n_payload=0, rep=0, extra=None,
        pre=None):
    pre = pre if pre is not None else snap()
    usage, ttft, tot, err = chat_stream(msgs)
    post = snap()
    usage = usage or {}
    pt = usage.get("prompt_tokens")
    kvc = int(round(dd(pre, post, K_KV + HS))); kvn = int(round(dd(pre, post, K_KV + HC)))
    ttfs = dd(pre, post, K_TTFT + HS); ttfn = int(round(dd(pre, post, K_TTFT + HC)))
    cached = int(round(dd(pre, post, K_CACHED)))
    if role in ("prime", "ident_resend") and target_P1 is not None and pt != target_P1:
        err = (err or "") + " | LENGTH-MISMATCH pt=%s target=%s" % (pt, target_P1)
    P1 = target_P1 if target_P1 is not None else pt
    row = {
        "arm": arm, "pair_id": pair_id, "role": role, "idx": idx, "rep": rep,
        "P1": P1, "P1_measured": pt, "L": (None if None in (pt, P1) else pt - P1),
        "n_payload": n_payload,
        "residue": (None if P1 is None else P1 % B),
        "ceil_P1_over_B": (None if P1 is None else -(-P1 // B)),
        "last_block_full": (None if P1 is None else P1 % B == 0),
        "cached": cached, "uncached": (None if pt is None else pt - cached),
        "uncached_kvcomp": (kvc if kvn == 1 else None),
        "ttft_ms": (None if ttft is None else round(ttft * 1000, 1)),
        "ttft_server_ms": (round(1000 * ttfs / ttfn, 1) if ttfn else None),
        "kvcomp_count_delta": kvn, "ttft_count_delta": ttfn,
        "Hstar_prime": Hstar(P1), "Hstar_full_B": (P1 // B),
        "cached_minus_P1_over_B": (None if P1 is None else cached - (-(-P1 // B)) * B),
        "C_minus_Hstar": (None if P1 is None else cached - B * Hstar(P1)),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "error": err,
    }
    if extra: row.update(extra)
    os.write(fd, (json.dumps(row, sort_keys=True) + "\n").encode()); os.fsync(fd)
    log("%-26s %-9s idx=%-2s P1=%-5s res=%-4s cached=%-6s unc=%-6s ttft=%sms %s" % (
        pair_id, role, idx, P1, row["residue"], cached, row["uncached"], row["ttft_ms"],
        ("ERR " + err) if err else ""))
    return row

def say(s):
    print(s, flush=True)

def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    lf = open(LOG, "a")
    def log(t):
        lf.write(t + "\n"); lf.flush(); os.fsync(lf.fileno())

    def cell(arm, P_, rep, tag=""):
        """MISS-LAW-2's exact G6 cell shape: prime(P_) -> byte-identical re-send of the prime
        -> append of ONE token (" the") after the identical re-send. 3 requests per cell."""
        m = prime_msgs(P_)
        pid = "%s|%s|P%d|r%d" % (arm, tag, P_, rep)
        r0 = req(fd, log, arm=arm, pair_id=pid, role="prime", idx=0, msgs=m, target_P1=P_, rep=rep)
        r1 = req(fd, log, arm=arm, pair_id=pid, role="ident_resend", idx=1, msgs=m,
                 target_P1=P_, rep=rep)
        r2 = req(fd, log, arm=arm, pair_id=pid, role="append", idx=2, msgs=app(m, 1),
                 target_P1=P_, rep=rep, n_payload=1)
        return r0, r1, r2

    if stage in ("all", "window"):
        for baseP, tag in ((6336, "6B"), (1056, "1B")):
            for off in (0, 1, 2, 3, 4, -1, -2):
                for rep in range(reps):
                    cell("WINDOW", baseP + off, rep, tag)

    if stage in ("all", "ceil"):
        for mult in (1, 2, 3, 4, 5, 7):
            for off in (0, 2):
                for rep in range(reps):
                    cell("CEIL", mult * B + off, rep, "%dB" % mult)

    if stage in ("all", "recover"):
        for baseP, tag in ((6336, "6B"), (2112, "2B"), (1056, "1B")):
            for rep in range(reps):
                m = prime_msgs(baseP)
                pid = "RECOVER|%s|P%d|r%d" % (tag, baseP, rep)
                r0 = req(fd, log, arm="RECOVER", pair_id=pid, role="prime", idx=0, msgs=m,
                         target_P1=baseP, rep=rep)
                cur = m
                for k in range(1, 7):
                    n = 4
                    msgs = app(cur, n)
                    rk = req(fd, log, arm="RECOVER", pair_id=pid, role="append_k", idx=k,
                             msgs=msgs, target_P1=baseP, rep=rep, n_payload=n, extra={"k": k})
                    cur = msgs
        for rep in range(reps):
            baseP = 6338
            m = prime_msgs(baseP)
            pid = "RECOVER-CTRL|6B|P6338|r%d" % rep
            req(fd, log, arm="RECOVER-CTRL", pair_id=pid, role="prime", idx=0, msgs=m,
                target_P1=baseP, rep=rep)
            cur = m
            for k in range(1, 5):
                n = 4
                msgs = app(cur, n)
                req(fd, log, arm="RECOVER-CTRL", pair_id=pid, role="append_k", idx=k,
                    msgs=msgs, target_P1=baseP, rep=rep, n_payload=n, extra={"k": k})
                cur = msgs

    if stage in ("all", "minimal"):
        for P_ in (B, B + 1, B + 2, 2 * B, 2 * B + 1, 2 * B + 2):
            for rep in range(reps):
                m = prime_msgs(P_)
                pid = "MINIMAL|P%d|r%d" % (P_, rep)
                req(fd, log, arm="MINIMAL", pair_id=pid, role="prime", idx=0, msgs=m,
                    target_P1=P_, rep=rep)
                req(fd, log, arm="MINIMAL", pair_id=pid, role="ident_resend", idx=1, msgs=m,
                    target_P1=P_, rep=rep)

    if stage in ("all", "pp"):
        # PRECEDING-A-NEW-PRIME: n1 (a FRESH prefix of length P0) then n2 = [n1's tokens] + P_ new.
        # Isolates the condition of the PRECEDING request: n2 pays T(n2) iff n1 == u*A + E_u.
        for P0 in (5000, 5001, 5002, 5003, 5004):
            for rep in range(reps):
                m1 = prime_msgs(P0)
                pid = "PP|P0%d|r%d" % (P0, rep)
                r0 = req(fd, log, arm="PP", pair_id=pid, role="fresh_n1", idx=0, msgs=m1,
                         target_P1=P0, rep=rep)
                PLAIN1 = gen_filler(3 + (P0 % 977))
                n2 = app(m1, P0)
                r1 = req(fd, log, arm="PP", pair_id=pid, role="pp_n2", idx=1, msgs=n2,
                         target_P1=P0, rep=rep)

    os.close(fd); lf.close()
    say("done stage=%s reps=%d" % (stage, reps))
    return 0

if __name__ == "__main__":
    sys.exit(main())
