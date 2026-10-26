#!/usr/bin/env python3
"""BILL-AUDIT replay: re-send QUALITY-ARM's own arm-A conversation and read the
server's cached_tokens per turn, alongside the law's prediction from its rows.

Faithful to quality/runner.py:
  * same index text (from quality/rows.jsonl row "corpus")
  * same resolved bodies (from the surviving body store /tmp/ptr-quality-A-r0-3222ek3v)
  * same conversation construction (system message grows by appending; user turn appended)
  * same turn plan (TURN_PLAN from quality/runner.py)
Difference, declared: the resolution ledger is rebuilt locally, so a fresh NONCE is
not injected -- the prefix will be WARM after the first rep. That is the point:
this is the WARM regime QUALITY-ARM's own turns live in.
"""

import json
import os
import random
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

BASE = "http://192.168.2.168:8012"
B = 64
FRAMING = 12
HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(HERE, "rows.jsonl")

from ptr_engine.adapter import INDEX_CLOSE, INDEX_OPEN, build_prompt  # noqa: E402
from ptr_engine.compile import compile_turn  # noqa: E402

QUESTION = (
    "Each knowledge item records one calibration constant's audit code. Naming one "
    "constant is meaningful only if its own audit code is known. Which audit code "
    "is recorded for the constant named "
)
TURN_PLAN = [
    (1, ["@knowledge:k12@1"],
     "Begin. The system message is a pointer index: each line names one item's "
     "reference, a short digest and its body size in bytes. Read @knowledge:k12@1 "
     "and reply with the single word OK."),
    (2, ["@knowledge:k10@1"], "Now read @knowledge:k10@1 and reply with the single word OK."),
    (3, ["@knowledge:k08@1", "@knowledge:k02@1"],
     "Now read @knowledge:k08@1 and also read @knowledge:k02@1, then reply with the "
     "single word OK."),
    (4, [], "READ_ALL"),
]


def emit(row):
    with open(ROWS, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def post(path, payload, timeout=300.0):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), time.time() - t0, None
    except Exception as e:  # a failed request is a row
        return None, time.time() - t0, str(e)[:500]


def predict(p1, L):
    r = p1 % B
    if r in (0, 1):
        return p1 + L, r, True
    return r + L, r, False


def main():
    qrows = [json.loads(l) for l in open(
        os.path.join(HERE, "..", "quality", "rows.jsonl"))]
    corpus = [r for r in qrows if r["row"] == "corpus"][0]
    qreq = [r for r in qrows if r["row"] == "request" and r["arm"] == "A" and r["rep"] == 0]
    root = corpus["run_root"]

    # Rebuild the TurnIndex object from the stored index text via a real compile so
    # that build_prompt's hash-contract checks pass.
    bodies = {}
    for line in corpus["index_text"].splitlines():
        line = line.strip()
        if not line.startswith("- @"):
            continue
        ref, digest, size = line[2:].split()
        bodies[ref] = (digest, int(size))
    material = []
    for ref, (digest, size) in bodies.items():
        kind, rest = ref.lstrip("@").split(":", 1)
        ident, ptr = rest.split("@")
        base = os.path.join(root, "warmpool", digest[:2])
        fname = [f for f in os.listdir(base) if f.startswith(digest)]
        body = open(os.path.join(base, fname[0]), "rb").read()
        material.append({"kind": kind, "id": ident, "body": body.decode()})
    index = compile_turn(material, revision=1, scope="quality", block_size=B)
    if index.index_text.strip() != corpus["index_text"].strip():
        print("WARNING: rebuilt index text differs from the recorded one")

    body_by_ref = {}
    for ref, (digest, size) in bodies.items():
        base = os.path.join(root, "warmpool", digest[:2])
        fname = sorted(f for f in os.listdir(base) if f.startswith(digest))[0]
        body_by_ref[ref] = open(os.path.join(base, fname), "rb").read().decode()

    conversation = [{"role": "system", "content": ""}]
    for turn_no, plan_refs, user_text in TURN_PLAN:
        sys_add = build_prompt(index, {r: body_by_ref[r] for r in plan_refs})
        asked = user_text if user_text != "READ_ALL" else qreq[3]["user_text"]
        conversation[0]["content"] += "\n\n" + sys_add
        conversation.append({"role": "user", "content": asked})

        tok, _, err = post("/v1/tokenize", {"model": "occamy", "messages": conversation})
        p1 = int(tok["count"])
        L = p1 + FRAMING
        law_unc, residue, avalanche = predict(p1, L)
        # Prediction row first, exactly as QUALITY-ARM does.
        emit({"row": "replay_prediction", "arm": "A-replay", "turn": turn_no,
              "P1": p1, "residue": residue, "avalanche": avalanche, "L": L,
              "law_predicted": {"uncached": law_unc},
              "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})

        resp, el, err = post("/v1/chat/completions", {
            "model": "occamy", "messages": conversation, "max_tokens": 300,
            "temperature": 0.0, "chat_template_kwargs": {"enable_thinking": False}})
        if err or resp is None:
            emit({"row": "replay_measure", "arm": "A-replay", "turn": turn_no,
                  "error": err, "law_predicted": {"uncached": law_unc}})
            continue
        usage = resp.get("usage") or {}
        det = usage.get("prompt_tokens_details")
        rep = isinstance(det, dict) and "cached_tokens" in det
        cached = int(det["cached_tokens"]) if rep else None
        p2 = int(usage.get("prompt_tokens") or p1)
        server_unc = (p2 - cached) if rep else None
        delta = (server_unc - law_unc) if rep else None
        agree = ("server-null" if not rep else
                 ("exact" if delta == 0 else "off-by-k"))
        emit({"row": "replay_measure", "arm": "A-replay", "turn": turn_no,
              "P1": p1, "P2": p2, "residue": residue, "L": L,
              "avalanche_predicted": avalanche,
              "law_predicted": {"uncached": law_unc},
              "server_reported": {"cached_tokens": cached, "reported": rep,
                                  "prompt_tokens": p2, "uncached": server_unc,
                                  "keys": ["usage.prompt_tokens_details.cached_tokens"],
                                  "usage_full": usage},
              "delta": delta, "agreement": agree,
              "elapsed_s": round(el, 4),
              "answer": ((resp.get("choices") or [{}])[0].get("message") or {}).get("content", "")[:80],
              "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        print(f"  turn{turn_no} P1={p1} res={residue} L={L} law={law_unc} "
              f"server_unc={server_unc} delta={delta} {agree}", flush=True)
        conversation.append({"role": "assistant",
                             "content": ((resp.get("choices") or [{}])[0].get("message") or {}).get("content", "")})


if __name__ == "__main__":
    main()
