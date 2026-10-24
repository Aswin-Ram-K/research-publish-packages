# UPUBLIST1 — publication checklist

**Status:** done. **Bound:** 30 tool calls (used 30). **Wrote:** `strategy/PUBLICATION_CHECKLIST.md` (31,919 B, 208 table rows).

## Purpose
One document the author works from: grouped by experiment, complete file inventory with exact size+sha256 measured from disk, ordered steps to public + peer review with the done ones marked.

## What was established
- EXP#12 = `papers/encoder-crossover-190/`; EXP#7 = `papers/replay-record-not-decision/`.
- `papers/gated-read-batching/` has **no** EXP number: provenance is a closed 2026-09-30 run, branch `measure/gated-read`, harness `tools/gated-read/bench.py` (GATED_READ_2026.md:3-9). Its "7" is candidate rank #7, not EXP#7.
- Only DOI on disk: concept `10.5281/zenodo.23463944` (encoder). Replay and gated carry no DOI.
- Numbering hazard mapped: candidate #3/#2/#7 (encoder/replay/gated) vs alternate #1/#3/#2.

## Verified
- All sizes/digests measured with `os.path.getsize`/`hashlib.sha256` in-unit; payload counts 31/10/12 files, 856,779 / 1,313,090 / 2,383,883 B.
- Encoder archive volatility recorded: 159,185 -> 159,182 B inside this session, mtime 13:23:32 -0500 — concurrent rebuild; digest `dbbf7b1a…9b1877` is timestamped, not final.

## Not done (deliberately)
- Repaired nothing, modified no artifact. Gated paper's missing `AVAILABILITY.md`/root `METADATA.md`/`REFERENCES.bib` recorded in §4, not created.
- `send_message` to the parent not sent: the 30-call bound was reached; this card + the handoff JSON carry the report.
