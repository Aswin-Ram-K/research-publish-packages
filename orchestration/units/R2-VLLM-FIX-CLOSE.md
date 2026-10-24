# R2-VLLM-FIX-CLOSE — close the `R2-VLLM` card on the record

**Shape:** record unit (transposition, no measurement). **Status:** `done`. **Bound:** 12 tool calls — **used
12** (the final handoff write excluded, as the card specifies). **Offline:** 0 model requests, no ssh, no
docker, no lock. **Automated session:** `ask_user_question` never called (and is unavailable to a subagent).

## Purpose

The `R2-VLLM` instrument-repair batch is finished and verified; what remained was the *record* of it. This
unit appended the verifier's verdict to `orchestration/VERDICTS.md`, added the batch to
`orchestration/STATUS.md` in the same shape as §7.1 with a §7.3-style manuscript-safe block, and wrote the
atomic handoff. **No number was re-measured and nothing was invented** — every figure is transposed from the
seven handoffs, `state/logs/R2-VLLM-triage.json`, `state/logs/R2-VLLM-rerun-report.md`, and
`cells/R2-VLLM/logs/verify-dossier.json`, each read in this session.

## Inputs read (all, before any edit)

`orchestration/handoffs/` `R2-VLLM-REPAIR.json`, `R2-VLLM-REPAIR2.json`, `R2-VLLM-RERUN.json`,
`R2-VLLM-PREFLIGHT2.json`, `R2-VLLM-ANALYSE.json`, `V-R2-VLLM-RERUN.json`, `R2-VLLM-DOCCHECK.json`;
`state/logs/R2-VLLM-triage.json` (the 7-order plan); `state/logs/R2-VLLM-rerun-report.md`;
`experiments/context-cache/cells/R2-VLLM/logs/verify-dossier.json`; `orchestration/VERDICTS.md` (head + tail,
later the last 25 lines to satisfy read-before-edit); `orchestration/STATUS.md` (full).

## Procedure

1. Read every handoff; take the verifier's `C1–C9`, `overstated`, `unverified` and gate call as the spine.
2. **Append** the `V-R2-VLLM-RERUN` entry to `VERDICTS.md` — entry style matched (heading with date + bold
   verdict, then bolded bullet leads, `**Gate call:**` last). 3839 → 3908 lines; lines 1–3839 untouched.
3. **Add §8** to `STATUS.md`: 8.1 unit table (8 units; `Unit · Shape · What it settled (numbers) · Verifier
   ruling`), 8.2 manuscript-safe / do-not-print, 8.3 open items. Numbering **§8, not §7.4/§7.5** — §7 is spent
   on the context-cache batch — so the pre-existing `## 8. Next structural steps` heading became `## 9.`
   (heading line only; its body is unchanged). The one-line state paragraph was extended by two additive
   lines; nothing else in §§0–7 changed. 250 → 316 lines.
4. Write the handoff to `.tmp`, parse it, check the ten contracted keys, `mv` into place, re-parse the live file.

## What was recorded

- **Verdict `V-R2-VLLM-RERUN` = partial.** Every number reproduced (418 rows, sha `6f7f05fa…de0ad1`;
  `usage_has_details` 418/418; `cached_tokens == None` 0; 64/64 groups at 4 distinct `prefix_sha256`;
  `rep0` 0/64 on both configs; `rep1` OH1 **62/64**, A1 **0/64**; 20 `(config, arm)` cells × 7 fields
  re-derived byte-for-byte). One **guard weakness** — a mutation of `pmu16_cell.py:134` aborts the suite with
  `revert pattern drifted from the source: flag_dropped_from_OH1` instead of a named FAIL. Three
  **precision overstatements** — `ANALYSE` "one arm with a miss" (misses are A turn 1 and H turn 2, 15/16
  each), `REPAIR2` "worst 219" (236 rows on disk), `ANALYSE` "15/16" (16/16 now).
- **Gate line:** advance on the instrument; **A1's 0/128 battery miss is a finding, not an instrument
  defect.**
- **Manuscript-safe:** usage accounting live on all three configs; arm identity byte-observable 4/4 on 64/64
  groups; OH1 repeat-pass battery 62/64 vs A1 0/128. **Not printable:** any arm-policy contrast; any
  `--prefix-match-unit` validity claim (`2096 % 16 == 0`, `1056 % 16 == 0`, OH1L 0 rows); any causal
  explanation of A1's misses; A1's 27 probe hits read as battery hits.

## Statements corrected against the handoff evidence

- `R2-VLLM-RERUN`'s 54-row kill is attributed to the `extra` `TypeError`; **`arm cap reached for OH1:
  219/200` belongs to the earlier 02:35 run** (per `V-R2-VLLM-RERUN` C9(d)) and is recorded as history, not
  as the kill cause.
- `REPAIR2`'s "`httpx.Client` now RAISES on construction (attempts counter = 0)" was **not** transcribed: it
  contradicts its own R8, which drives the real `phase_battery` through a `FakeChatClient` for 128 client
  calls. The offline claim is stated as what actually proves it — 0 model requests, 0 ssh, 0 docker, no lock.
- `R2-VLLM-PREFLIGHT2` is recorded as what it measured (read-only host state, 0 mutating commands), not as
  containment of the batch.

## Deliverables

`orchestration/VERDICTS.md` (+69 lines, append only) · `orchestration/STATUS.md` (+66 lines, new §8, one
heading renumbered) · `orchestration/handoffs/R2-VLLM-FIX-CLOSE.json` (unit shape, parses, 10/10 keys) ·
this card.

## Blocker

None.

## Next

(i) An **A1-attribution** unit — 0/128 battery vs 27/27 probe hits in one launch; separate prefix-cache
eviction under `--gpu-memory-utilization 0.15` / `--max-num-seqs` from tokenizer prefix divergence for
`qwen3.5-9b`. (ii) A **`--prefix-match-unit` discrimination** test whose resolved block size is not divisible
by the flag value (the OH1L `2096 % 8 != 0` premise was false: 2096 = 2^4 × 131). Non-blocking third:
repair the drifted revert-guard so a future regression reads as a named FAIL.
