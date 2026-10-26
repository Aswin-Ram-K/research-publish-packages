#!/usr/bin/env python3
"""ENGINE-R1 measurement: does residue quantisation pay on the live SGLang endpoint?

Four cells, 3 reps each, prime -> measure per rep, following ``experiments/miss-law/LAW.md``
section 2 exactly:

    round 1 (prime):   [system: NONCE + "\\n\\n" + <compiled index block>,
                        user:   "Reply with the single word OK."]
    round 2 (measure): same two messages + [assistant "OK.", user " the" * n]

* The 10-token NONCE is permuted per prime, so every prime is cold while ``P1`` stays
  fixed inside a cell.
* ``L`` is the MEASURED prompt delta, never ``n`` (the framing is 12 tokens).
* A PREDICTION row is appended and fsynced BEFORE each measure request: ``P1`` from
  the padding arithmetic, ``L`` from the pre-registered framing constant (LAW.md s2).
  A prediction recorded after the fact is worthless, so it is its own row.
* **The residue is verified on the wire before the measured append.** ``choose_padding``
  aligns ``token_len(system) + offset``; the offset is the user message plus the
  template's own framing, and a padded tail also merges with the template's trailing
  marker (+1 token, measured). So each rep primes, reads the ACTUAL ``prompt_tokens``,
  and re-aims with the measured correction -- up to 3 attempts, each on a fresh
  nonce. The attempt that lands is the one measured; every attempt is a row.
* ``rows.jsonl``: one row per request (plus one prediction row per rep), flushed and
  fsynced immediately -- a kill loses at most the request in flight.

Cells: A = index as ``worked_example.py`` compiles it, unpadded; B = same padded to
residue 2; C = same padded to residue 0 (the avalanche control); D = compact index
padded to residue 2.

    python3 experiments/ptr-engine/measure/run_cells.py --write-rows
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve()
ENGINE_ROOT = HERE.parents[1]              # experiments/ptr-engine
sys.path.insert(0, str(ENGINE_ROOT))
sys.path.insert(0, str(ENGINE_ROOT / "examples"))

import worked_example  # noqa: E402  (the corpus of record)

from ptr_engine import BodyStore, Ledger, build_prompt, compile_turn  # noqa: E402
from ptr_engine.quantise import (  # noqa: E402
    DEFAULT_TARGET_RESIDUE,
    Padding,
    ServerTokenizer,
    choose_padding,
    compact_index,
    cycle_bill,
    predict_billed,
    token_len,
)

ENDPOINT = "http://192.168.2.168:8012/v1"
MODEL = "occamy-1.0"
B = 64
REPS = 3
PAYLOAD_TOKENS = 1
#: Pre-registered framing of one append (LAW.md s2: L = n + 12). Predicted BEFORE
#: the request; the row also carries the measured delta.
PREDICTED_FRAMING = 12
USER_TEXT = "Reply with the single word OK."
BLOCK_SIZE = 64
REVISION = 1
SCOPE = "worked-example"   # the example's own scope constant: cell A is its exact artefact
ROWS = ENGINE_ROOT / "measure" / "rows.jsonl"
SUMMARY = ENGINE_ROOT / "measure" / "summary.json"
MAX_ATTEMPTS = 3

WORDS = (
    "north", "river", "amber", "quiet", "stone", "lamp", "field", "copper",
    "window", "orbit", "silver", "garden", "market", "harbour",
)
STEPS = (1, 3, 5, 9, 11, 13)


# --------------------------------------------------------------------------- io
def post(path: str, payload: dict, timeout: float = 180.0) -> dict:
    url = ENDPOINT.rstrip("/") + path
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def chat(system_text: str, payload: int | None = None) -> dict:
    """One request. ``payload=None`` is the PRIME; an int is the append round."""
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": USER_TEXT},
    ]
    if payload is not None:
        messages.append({"role": "assistant", "content": "OK."})
        messages.append({"role": "user", "content": " the" * payload})
    return post(
        "/chat/completions",
        {
            "model": MODEL,
            "messages": messages,
            "max_tokens": 1,
            "temperature": 0.0,
            "stream": False,
        },
    )


def nonce(seed: int, pool: tuple[str, ...]) -> str:
    """A permutation of ten one-token words: constant count, unique prefix.

    ``seed`` picks a stride and a start, so seeds 0..83 are 84 distinct orderings --
    enough that no prime in this run reuses a prefix, which is what keeps every
    prime cold.
    """
    step = STEPS[seed % len(STEPS)]
    start = (seed // len(STEPS)) % len(pool)
    return " ".join(pool[(start + i * step) % len(pool)] for i in range(10))


class Rows:
    def __init__(self, path: Path, enabled: bool) -> None:
        self.path = path
        self.enabled = enabled
        self.handle = None
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.handle = path.open("w", encoding="utf-8")
        self.count = 0

    def append(self, row: dict) -> None:
        self.count += 1
        row = {"seq": self.count, **row}
        if self.handle is None:
            print(json.dumps(row, sort_keys=True))
            return
        self.handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.handle.flush()                    # no buffering: a kill loses one row
        os.fsync(self.handle.fileno())

    def close(self) -> None:
        if self.handle is not None:
            self.handle.close()


# ------------------------------------------------------------------ index forms
def build_indexes(store: BodyStore, ledger: Ledger):
    """The worked example's 12 items / 30,000 chars, compiled twice: full, compact."""
    material = worked_example.corpus()
    assert len(material) == 12
    total_body = sum(len(item["body"].encode("utf-8")) for item in material)
    index = compile_turn(
        material, revision=REVISION, scope=SCOPE, block_size=BLOCK_SIZE, store=store
    )
    envelope = build_prompt(index, {}, ledger)
    compact = compact_index(index.index_text)
    compact_envelope = envelope.replace(index.index_text, compact.text)
    assert compact_envelope != envelope
    return {
        "index": index,
        "total_body": total_body,
        "full": {
            "envelope": envelope,
            "bytes": len(envelope.encode("utf-8")),
            "index_bytes": index.index_size,
            "per_line": index.index_size / len(index.lines),
            "sha256": hashlib.sha256(envelope.encode("utf-8")).hexdigest(),
        },
        "compact": {
            "envelope": compact_envelope,
            "bytes": len(compact_envelope.encode("utf-8")),
            "index_bytes": compact.bytes_len,
            "per_line": compact.per_line,
            "report": compact.as_dict(),
            "sha256": hashlib.sha256(compact_envelope.encode("utf-8")).hexdigest(),
        },
    }


# ------------------------------------------------------------------- the cells
CELLS = (
    {"cell": "A", "form": "full", "target": None,
     "note": "index exactly as worked_example.py compiles it, no padding"},
    {"cell": "B", "form": "full", "target": DEFAULT_TARGET_RESIDUE,
     "note": "same content, padded to residue 2"},
    {"cell": "C", "form": "full", "target": 0,
     "note": "same content, padded to residue 0 on purpose (the control)"},
    {"cell": "D", "form": "compact", "target": DEFAULT_TARGET_RESIDUE,
     "note": "compact index, padded to residue 2"},
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-rows", action="store_true", help="write measure/rows.jsonl")
    parser.add_argument("--cells", default="ABCD")
    args = parser.parse_args()

    tokenizer = ServerTokenizer(ENDPOINT)
    rows = Rows(ROWS, args.write_rows)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    seeds = itertools.count(0)

    # One-token words only: a permutation must not move P1 within a cell.
    with_space = {word: token_len(f" {word}", tokenizer) for word in WORDS}
    bare = {word: token_len(word, tokenizer) for word in WORDS}
    pool = tuple(w for w in WORDS if with_space[w] == 1 and bare[w] == 1)
    if len(pool) < 10:
        print(json.dumps({"fatal": "not enough one-token nonce words", "ok": len(pool)}))
        return 2

    tmp_root = Path(os.environ.get("PTR_TMP", "/var/tmp"))
    workdir = Path(tempfile.mkdtemp(prefix="ptr-engine-r1-", dir=str(tmp_root)))
    summary: dict = {
        "endpoint": ENDPOINT, "model": MODEL, "block_size": B, "reps": REPS,
        "payload_tokens": PAYLOAD_TOKENS, "predicted_framing": PREDICTED_FRAMING,
        "nonce_pool": list(pool), "started": stamp, "cells": {},
    }
    try:
        store = BodyStore(workdir / "warmpool")
        ledger = Ledger(workdir / "ledger.jsonl", block_size=BLOCK_SIZE)
        forms = build_indexes(store, ledger)
        summary["index"] = {
            "items": 12,
            "total_body_bytes": forms["total_body"],
            "full_bytes": forms["full"]["index_bytes"],
            "full_per_line": round(forms["full"]["per_line"], 2),
            "full_r": round(forms["total_body"] / forms["full"]["index_bytes"], 1),
            "compact_bytes": forms["compact"]["index_bytes"],
            "compact_per_line": round(forms["compact"]["per_line"], 2),
            "compact_r": round(forms["total_body"] / forms["compact"]["index_bytes"], 1),
            "compact_report": forms["compact"]["report"],
            "envelope_full_bytes": forms["full"]["bytes"],
            "envelope_compact_bytes": forms["compact"]["bytes"],
            "full_sha256": forms["full"]["sha256"],
            "compact_sha256": forms["compact"]["sha256"],
        }
        print(json.dumps({"index": summary["index"]}, sort_keys=True))

        for spec in CELLS:
            if spec["cell"] not in args.cells:
                continue
            form = forms[spec["form"]]
            envelope = form["envelope"]
            target = spec["target"]
            user_tokens = token_len(USER_TEXT, tokenizer)

            # --- calibration: what does the chat template add to the two texts?
            calib_nonce = nonce(next(seeds), pool)
            calib_system = f"{calib_nonce}\n\n{envelope}"
            calib_system_tokens = token_len(calib_system, tokenizer)
            calib = chat(calib_system)
            calib_p1 = int(calib["usage"]["prompt_tokens"])
            framing = calib_p1 - calib_system_tokens - user_tokens
            rows.append({
                "row": "calib", "cell": spec["cell"], "phase": "prime", "rep": None,
                "nonce": calib_nonce, "system_tokens": calib_system_tokens,
                "user_tokens": user_tokens, "prompt_tokens": calib_p1,
                "template_framing": framing, "observed_at": stamp,
            })

            cell_out = {"note": spec["note"], "form": spec["form"], "target": target,
                        "template_framing": framing, "reps": []}

            for rep in range(REPS):
                # ---- aim, then verify the residue on the wire ---------------
                correction = 0
                attempts = []
                settled = None
                for attempt in range(MAX_ATTEMPTS):
                    rep_nonce = nonce(next(seeds), pool)
                    base_system = f"{rep_nonce}\n\n{envelope}"
                    base_tokens = token_len(base_system, tokenizer)
                    offset = user_tokens + framing + correction
                    if target is None:
                        padding = Padding(
                            text=base_system, padding="", padding_tokens=0,
                            target_residue=(base_tokens + offset) % B, block_size=B,
                            base_tokens=base_tokens, padded_tokens=base_tokens,
                            residue_before=(base_tokens + offset) % B,
                            residue_after=(base_tokens + offset) % B,
                            token_source=ENDPOINT, offset_tokens=offset,
                        )
                    else:
                        padding = choose_padding(
                            base_system, target, B, tokenizer, offset_tokens=offset
                        )
                    predicted_p1 = padding.prompt_tokens
                    prime = chat(padding.text)
                    p1 = int(prime["usage"]["prompt_tokens"])
                    residue_obs = p1 % B
                    attempt_row = {
                        "row": "request", "cell": spec["cell"], "phase": "prime",
                        "rep": rep, "attempt": attempt, "nonce": rep_nonce,
                        "pad_tokens": padding.padding_tokens,
                        "offset_tokens": offset, "correction": correction,
                        "predicted_P1": predicted_p1,
                        "predicted_residue": predicted_p1 % B,
                        "prompt_tokens": p1, "P1": p1, "residue": residue_obs,
                        "residue_target": None if target is None else target,
                        "on_target": target is None or residue_obs == target,
                        "token_source": ENDPOINT,
                    }
                    rows.append(attempt_row)
                    attempts.append({
                        "attempt": attempt, "pad_tokens": padding.padding_tokens,
                        "correction": correction, "predicted_P1": predicted_p1,
                        "P1": p1, "residue": residue_obs,
                        "predicted_residue": predicted_p1 % B,
                        "on_target": attempt_row["on_target"],
                    })
                    print(json.dumps({"cell": spec["cell"], "rep": rep,
                                      "attempt": attempt, "pad": padding.padding_tokens,
                                      "predicted_P1": predicted_p1, "P1": p1,
                                      "residue": residue_obs, "target": target,
                                      "on_target": attempt_row["on_target"]},
                                     sort_keys=True), flush=True)
                    if attempt_row["on_target"]:
                        settled = (padding, p1, rep_nonce, attempt, residue_obs)
                        break
                    correction += p1 - predicted_p1
                if settled is None:                      # keep the last attempt, honestly
                    settled = (padding, p1, rep_nonce, MAX_ATTEMPTS - 1, residue_obs)
                padding, p1, rep_nonce, settled_attempt, residue_obs = settled

                # ---- PREDICTION FIRST (fsynced), then the measured append ----
                l_predicted = PAYLOAD_TOKENS + PREDICTED_FRAMING
                predicted_uncached, predicted_avalanche = predict_billed(
                    p1, l_predicted, B
                )
                bill = cycle_bill(p1, l_predicted, B, DEFAULT_TARGET_RESIDUE)
                rows.append({
                    "row": "prediction", "cell": spec["cell"], "phase": "measure",
                    "rep": rep, "attempt": settled_attempt, "nonce": rep_nonce,
                    "target_residue": target, "padding": padding.as_dict(),
                    "predicted_P1": p1, "predicted_L": l_predicted,
                    "predicted_uncached": predicted_uncached,
                    "predicted_avalanche": predicted_avalanche,
                    "predicted_cycle_bill": (
                        bill["padded_cycle"] if target is not None
                        else bill["unpadded_cycle"]
                    ),
                    "prediction_made_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                })

                measured = chat(padding.text, PAYLOAD_TOKENS)
                usage = measured["usage"]
                details = usage.get("prompt_tokens_details")
                cached_reported = details is not None and "cached_tokens" in (details or {})
                cached = int((details or {}).get("cached_tokens") or 0)
                p2 = int(usage["prompt_tokens"])
                measured_L = p2 - p1
                uncached = p2 - cached
                law_uncached, law_avalanche = predict_billed(p1, measured_L, B)
                aligned_cached = ((p1 - 2) // B) * B if not law_avalanche else 0
                rows.append({
                    "row": "request", "cell": spec["cell"], "phase": "measure",
                    "rep": rep, "attempt": settled_attempt, "nonce": rep_nonce,
                    "P1": p1, "residue": p1 % B, "residue_target": target,
                    "pad_tokens": padding.padding_tokens,
                    "prompt_tokens": p2, "L": measured_L,
                    "payload_tokens": PAYLOAD_TOKENS, "predicted_L": l_predicted,
                    "cached_tokens": cached if cached_reported else None,
                    "cached_reported": cached_reported,
                    "uncached_tokens": uncached,
                    "predicted_uncached": predicted_uncached,
                    "predicted_avalanche": predicted_avalanche,
                    "law_uncached_measured_L": law_uncached,
                    "law_avalanche_measured_L": law_avalanche,
                    "observed_minus_predicted": uncached - predicted_uncached,
                    "cached_shortfall_vs_alignment": aligned_cached - cached,
                    "token_source": ENDPOINT,
                })
                cell_out["reps"].append({
                    "rep": rep, "attempts": settled_attempt + 1,
                    "attempt_log": attempts,
                    "pad_tokens": padding.padding_tokens,
                    "P1": p1, "residue": p1 % B,
                    "on_target": (target is None or p1 % B == target),
                    "L": measured_L, "predicted_L": l_predicted,
                    "cached_tokens": cached if cached_reported else None,
                    "cached_reported": cached_reported,
                    "cached_shortfall_vs_alignment": aligned_cached - cached,
                    "uncached": uncached,
                    "predicted_uncached": predicted_uncached,
                    "predicted_avalanche": predicted_avalanche,
                    "law_uncached_measured_L": law_uncached,
                    "delta_vs_prediction": uncached - predicted_uncached,
                    "matches_law": uncached == law_uncached,
                    "cycle": bill,
                })
                print(json.dumps({
                    "cell": spec["cell"], "rep": rep, "P1": p1, "residue": p1 % B,
                    "pad": padding.padding_tokens, "L": measured_L,
                    "cached": (cached if cached_reported else None), "uncached": uncached,
                    "predicted": predicted_uncached, "avalanche": predicted_avalanche,
                    "match": uncached == law_uncached,
                    "shortfall": aligned_cached - cached,
                }, sort_keys=True), flush=True)

            summary["cells"][spec["cell"]] = cell_out
    finally:
        rows.close()

    summary["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": rows.count, "summary": str(SUMMARY)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
