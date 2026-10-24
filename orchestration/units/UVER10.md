# UVER10 — independent verification of UPAPER7 (`papers/gated-read-batching/`)

**Unit type:** verifier (not the author). **Bound:** max 55 tool calls — used 32. **Status:** done.
**Verdict:** `pass-with-corrections`.

## Purpose

Re-check UPAPER7's new manuscript package for lead #7 (batching binary gate decisions at
`effort=none`): re-derive the headline numbers from the raw rows, spot-check `CLAIMS.md` locators,
resolve every reference identifier, re-count words / grep placeholders, judge the framing of the newly
authored §1/§2/§5/§6/§7, run a red→green check on a workspace copy, and grep for disclosure leaks.

## Write paths (declared, nothing else touched)

- `strategy/VERIFICATION_REPORT_10.md`
- `orchestration/units/UVER10.md`
- `orchestration/handoffs/UVER10.json`

Target `/home/zer0null/Duval` was read-only throughout (no writes, no `git`); `papers/**` was not edited;
`repro/encoder-crossover-190-SANITISED/**` (UREDACT2) untouched. The real `MANUSCRIPT.md` is byte-identical
after the red→green run (md5 `f9118b2f9ada553d3c9df6e7b440e23f`).

## Method / evidence

- `scratch/ver10/rederive.py` — read-only pass over `/home/zer0null/Duval/docs/research/gated-read-rows.jsonl`
  (9,260 rows), summing `prompt_tok`/`completion_tok` and counting `tp/fp/fn/tn` per `mode`.
- `scratch/ver10/check_manuscript.py` — parses the manuscript's §4.1/§4.3 tables and operating-point
  sentence, diffs them against the re-derived values. `rc=0` PASS on the unmodified file; `rc=1` FAIL on
  a workspace copy with the bs16 row altered (`270 K`→`27 K`, `0.227`→`0.927`).
- Line-by-line reads of `GATED_READ_2026.md`, `GATED_READ_PROVENANCE.md`, `gated-read-summary.json`.
- One `web_fetch` of the arXiv Atom API `id_list` covering all 13 cited identifiers (HTTP 200, 2026-10-15 UTC).

## Findings

- Headline table reproduces exactly: calls 1,800/120/20; prompt tokens 631,210/269,614/261,090; F1
  0.2176/0.2268/0.21053; admitted pairs 73/268/146. Only defect: bs90 `none` F1 displayed as 0.210 where the
  exact value is 0.2105 (0.211 at 3 dp) — a truncation inherited from the source.
- 13/13 identifiers resolve; 11/11 "verified-in-source-only" resolve. Ref 10's title is wrong
  (`arXiv:2604.03515` is "…Taxonomy of Coding Agent Architectures", not "…of 13 Coding-Agent Scaffolds") and
  the same wrong title is at source `GATED_READ_PROVENANCE.md:47` — carried, not invented.
- `CLAIMS.md` C48 and C65 have off-line locators (numeral at `GATED_READ_2026.md:313` and
  `GATED_READ_PROVENANCE.md:254-256`); all other opened rows land on the exact line.
- 5,193 words, 8/8 prose sections, 0 placeholder hits, disclosure grep clean.
- The "10×" source error is correctly diagnosed in GAPS G-01 (8.87× completion / 2.06× total) but the
  manuscript text still says "ten times the completion tokens" — the correction was not carried.

Full detail, tables and the "what would change my verdict" note are in
[`../strategy/VERIFICATION_REPORT_10.md`](../strategy/VERIFICATION_REPORT_10.md). Machine-readable verdict:
[`../orchestration/handoffs/UVER10.json`](../orchestration/handoffs/UVER10.json).
