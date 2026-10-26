# V-RECORD-2 — second independent audit of experiments/ptr-engine/RECORD.md

Purpose: re-derive, from sources, every numeric claim in the release record whose five C-lines
(C1/C2/C3/C5/C8/C10) carry six adjudication layers written by six different units — two of them
transcribed from a fourth unit's draft. Read-only; nothing repaired.

Bound 20 tool calls (used 13). Hash pin: source and /tmp snapshot both sha256 `2421f92e...`
(140 lines, 34,281 bytes), source re-hashed identical at the end; the sandbox's per-call /tmp makes
the snapshot non-durable, so the hash equality is the pin.

## Verdict: partial — 43 claims, 30 confirmed, 7 wrong, 2 unsourceable, 4 not checked

Survived (re-derived): the whole C1 warm-cell arithmetic (cached = 64*floor(P1/64)
= 320/384/320 at P1 = 325/386/322, residues 5/2/2, uncached = residue+13 = 18/15/15); C3's
123 vs 7,087 = 57.6x; C10's `per_turn` [55,13,1] against request rows 10/53/11/20 with
refused_total 0; C8's partitions 304 cached_reported + 83 null-cache = 387, 66/17 residue split,
218 sglang + 85 vLLM + 1 vLLM, 379 null rows (377+2), 774 rows with 0 errors, the tail-21
composition, the 3 duplicate calib pairs; C9's 378 rows / 141 cached>0 / sha256 8147d195…;
the quality 115-row split and the 458-byte index hash.

## Three worst findings

1. **L11 — engine size is a stale P0.1 count presented as current.** Record: "9 modules, 1896
   engine lines + 1222 test lines; SPEC.md 260 lines". Disk now: 10 modules / 3,653 py lines,
   13 test files / 2,248 lines, `SPEC.md` 499 lines. Off by ~1.8-1.9x on every term.
2. **L130 — "303 exact at residual 0; 1 is off — vllm B Bprobe-400 rep 0, residual −1056".**
   Recomputed: 159 fit rows strictly at residual 0; 51 at +64, 6 at +128, 2 at +192 (sglang);
   the 85 vLLM rows carry the documented block delta (69 x 1,056, 16 x 2,112). The named
   "off" row is `role=prime`, outside the fit set; the fit-set vLLM `Bprobe-400` row is exact.
   Also L130's mechanism claim "exactly the set `L_app is None`" is false: `L_app` is null in
   0/387 fit rows, yet `L_res` is null in 27 and `hits_delta` in 290 (+11 absent).
3. **L118/L120/L97 — RESULTS.md citations no longer land.** `:248` carries no 32,401 (it is the
   retention bullet); the 49,594 and its 32,401 correction sit on the same line `:181`, not "two
   lines apart"; `:150` is the paragraph *asserting* the C rep2 T4 avalanche, not "0 avalanches"
   (that sentence is `:164`); and "this record is the only place the correction exists" is false —
   `RESULTS.md:174-181` already carries 32,401, the +17,193 residual and the 6-token completions.

## Unsourceable / contradiction
- "outlier 0 / law_gap 387 / defect 321" is cited to `orchestration/units/C8-FIT-GAP.md:16-29`,
  which was rewritten to 13 lines; its handoff now reads law_gap 0 / defect 21. The pair survives
  only inside RECORD.md — self-sourced — and the record's own C8-304 layer supersedes it.
- L89 licenses "33/33 named refusals" while L134 says `refused_total=0` means the 33
  `PTR_STORE_MISS` are not a refusal count. Same file, opposite readings.
- C1 is CLOSED in layer 1, reopened in layer 2, and the last layer ends "UNDECIDABLE … no row
  holds" without restating a status.

## Blocker

The 321 rows cannot be re-derived from any artefact on disk: the only source is inside RECORD.md,
withdrawn by a later layer. No repair performed — wrong sentences are findings, not edits.
