# EVID-FRESH — citation freshness check (2026-10-23)

**Objective.** Verify every (path, sha256/size) citation in `papers/context-cache/EVIDENCE.md` and
`papers/context-cache/RUN.json` still resolves — file exists, digest matches current bytes — and run
the reverse check: is every `cells/*/rows.jsonl` digest cited somewhere, and does it match the cell's
own run.json?

**Constraint honoured.** Read-only over all cited artefacts; this unit wrote nothing outside its two
contracted paths. No git invoked against any target. No live requests. Bound 20 tool calls; used 10.

## Method

Two throwaway scripts under `.scratch/` (allowed scratch area): `evid_fresh_check.py` (pass 1,
root-relative resolution — produced false MISSING rows because citations are cell-relative) then
`evid_fresh_pass2.py` (resolves each cited path against the real citation-root trees:
`experiments/context-cache/`, `orchestration/handoffs/`, `papers/context-cache/`, `strategy/`).
Every MATCH below is sha256 over current file bytes == the cited digest; every prefix citation is
`startswith`. Targeted `sed`/`grep` reads confirmed each surviving mismatch by exact line.

## Results

| Check | Count |
|---|---|
| Cited (path, digest) pairs verified | 41 |
| MATCH | 35 (+1 orphan resolved to a real path) |
| MISMATCH | 3 |
| MISSING / unresolvable | 0 |

Reverse: 16 cells have a `rows.jsonl`; 6 digests appear in RUN.json (G1, G3-LIMIT-V2, G5, M4, U15,
U4b); 10 are cited nowhere (CROSS-HTTP, E2, G3, LIVE-MEAS, M1-M, TUNED, U3, U6, WIN-SGL,
WIN-VLLM); 12 cells have no `rows.jsonl` at all — their rows live under cell-specific names
(`u2_cache_rows.jsonl`, `e4_rows.jsonl`, `u5_raw.jsonl`, …). TUNED's own run.json records a
rows_sha256 that matches its file.

## Mismatches found (all three are EVIDENCE/RUN internal-consistency defects, not lost files)

1. **EVIDENCE.md:272** cites `papers/context-cache/recompute.py` as
   `63a4f0e6644ba788e6c38d102ed39687e78d0b4d9a8ba5ba808a5556a4a0623d`; the file currently hashes
   `85917e480d1aea24d0d5b85ab75ab0464cd2b950ff6d7622ed093be09716abcc`.
2. **RUN.json `verification.synthesis_recompute`** carries `85917e480d1aea24…` (correct) for the
   same file — so the two documents disagree with each other about recompute.py.
3. **RUN.json `pins.u4_sessions_payload_sha256_claimed`** = `78b725cbe281d55d…`, which is not
   `experiments/context-cache/cells/U4/u4_sessions.json`'s digest (`0ca987d910bdbb9f…`, the value in
   the sibling `u4_sessions_payload_sha256` field). RUN.json's own repair note says the claimed value
   is the *payload* digest recorded inside the file, not the file's own digest.

A fourth value — `4184c9321b9a9406`, cited at EVIDENCE.md:257 and RUN.json
`pins.u5_render_py_sha8` as render.py's digest — **cannot be confirmed**: the current
`src/resextract/context/render.py` hashes `807e52c641dd2dcb…`, and RUN.json's repair note states it
was not re-hashed. Recorded as unverified rather than mismatched, since the original bytes are gone.

All four are already flagged in RUN.json by the FIX-RUN-R2 repair pass; EVIDENCE.md has not been
brought in line. Fixing that is an author-side edit outside this unit's write scope.

## Failure modes hit

- Pass 1's naive root-relative path resolution produced 23 false "MISSING" rows (cell-relative
  citations like `cells/U2/u2_cache_rows.jsonl` and `handoffs/U2.json`). Resolving against the
  citation-root trees instead reduced that to 0 real misses. Any future citation check here must do
  the same, or it will report mass false breakage.
- A digest on a table row does not necessarily belong to the path on that same row (EVIDENCE.md:246
  `16640c1ba1e2c79e` is `handoffs/U5.json`'s digest, not `cells/U5/u5_raw.jsonl`'s). Path and digest
  must be matched by proximity in prose or by direct re-hash of the named file, never by row layout.
