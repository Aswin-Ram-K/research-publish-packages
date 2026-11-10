# Quarantine of synthetic stub spend

## What happened
The campaign driver was run with `--engine stub` (a deterministic in-process fake)
against the production campaign ledger. 318 reserve+record pairs were appended to
`ledger/journal.jsonl` with labels `preflight:...`, `context:...`, `serving:...`,
`holdout:...`, `prompt_format:...`. Intents landed 70-90 ms apart in bursts; every
row carried `usage.prompt_tokens=101, cached_tokens=40, completion_tokens=10`.
`run/rows/{serving,prompt_format,holdout}.jsonl` held 11 rows whose `engine` block
claimed `http://192.168.2.168:8012` although no socket was opened. Phase counters
were preflight 48/48, context 196, serving 64, holdout 8, prompt_format 2 -- all fake.

Zero real model requests had been dispatched at that point. (Two unrelated vLLM
residue smoke requests on port 8013 are real and remain counted.)

## Selection predicate
The void set is FROZEN and explicit: `ledger/voided-attempt-ids.txt` (one id per
line, 318 ids). It MUST NOT be re-derived by regex; the old regex
`^(preflight|context|prompt_format|serving|holdout):` is unsafe because it now
also matches real post-quarantine attempts. Count = 318. The `ledger.py` guard
refuses `void --label-prefix` for any attempt not already in the void set whose
label is not synthetic-marked, so re-running the documented command is a no-op.

## Counts
- Before: total_reserved=320, total_spent=320, voided=0.
  per_phase spent: preflight 48, context 196, serving 66, holdout 8,
  prompt_format 2, contingency 0.
- After: total_reserved=2, total_spent=2, voided=318.
  per_phase spent: preflight 0, context 0, serving 2, holdout 0,
  prompt_format 0, contingency 0.

## Row files
The 11 stub row files moved to `run/rows-quarantine/` with NOTE.md. `run/rows/`
left empty for real data.
