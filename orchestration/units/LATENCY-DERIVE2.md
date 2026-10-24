# LATENCY-DERIVE2 — what service latency the existing rows support (streaming only)

*Card type:* executable, `automated`, `workspace-write`. No human present: **no `ask_user_question`**.
*Supersedes:* `LATENCY-DERIVE` (that attempt died mid-turn; nothing was persisted from it — checked, no
`orchestration/handoffs/LATENCY*` existed when this unit started).

## 1. Objective

Answer one question from data already on disk: **what service latency can be computed from the rows we
have, and what honestly cannot?** Every derivable quantity is computed; every non-derivable one is refused
with the *specific missing field* named. A refused metric is a result, not a failure.

## 2. Hard bound and kill condition

- **Tool-call bound: 60.** Stop condition: if a quantity cannot be bounded or refused within the streaming
  pass, record it in `not_computable` with the reason and stop deriving it.
- **0 live requests. No `.occamy.lock`. No server start or stop. No target-repo access.** If any step would
  need the endpoint, it is out of scope by construction.

## 3. Streaming rule (the reason this unit exists)

Rows are never loaded whole and never printed whole. `derive_latency.py` opens each `rows.jsonl` and iterates
it **line by line** (`for line in fh`), accumulating counters only. The selfcheck asserts that no bulk read
(`read_text()`, `readlines()`, `json.load(fh)`) appears in the derivation script.

## 4. Declared write paths

```
state/logs/LATENCY-DERIVE2/derive_latency.py     (derivation, read-only over cells)
state/logs/LATENCY-DERIVE2/selfcheck.py          (containment + refusal + red->green)
state/logs/LATENCY-DERIVE2/summary.json          (machine-readable summary)
state/logs/LATENCY-DERIVE2/run.txt               (stdout of the derivation)
state/logs/LATENCY-DERIVE2/redgreen.txt          (green + red capture)
state/logs/LATENCY-DERIVE2.md                    (the report)
orchestration/units/LATENCY-DERIVE2.md           (this card)
orchestration/handoffs/LATENCY-DERIVE2.json      (handoff)
```

Nothing else is written. `experiments/`, `papers/`, `src/` and every target repo are untouched.

## 5. Deliverable shape

Report sections: (1) what the rows contain, field by field, with coverage counts; (2) **D1–D5**, the
derivable quantities, each with its number and its exact computation; (3) the refusal table, each row naming
the missing field; (4) the reproduce commands with their green and red outputs; (5) traps found.

## 6. What this unit is NOT allowed to claim

- No queue factor, no decode rate, no network latency, no harness queue delay — the rows carry no server
  clock and no per-chunk timestamps.
- `wall_ms − ttft_ms` is *never* called "decode time"; it is a span that includes close and overhead.
- No live number may be quoted as measured here: this unit made **0 requests**.

## 7. Gate

A verifier (`V-LATENCY-DERIVE2`, a different agent) must (a) re-run both scripts, (b) re-derive at least
D1 and D5 from the row files with its own reader, (c) force the red on the counter check, and (d) confirm
**0** live requests (no lock file mtime change, no new row-file lines).
