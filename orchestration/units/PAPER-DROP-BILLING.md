# Unit PAPER-DROP-BILLING

**Workspace:** `/home/zer0null/reserach extarctor` · **Automated:** no questions, no waiting · **Bound:** 16 tool calls (used 12)
**Declared write paths:** `papers/context-cache/MANUSCRIPT.md`, `papers/context-cache/CLAIMS.md`,
`orchestration/units/PAPER-DROP-BILLING.md`, `orchestration/handoffs/PAPER-DROP-BILLING.json`.

## Purpose

Execute parked DECISION `0b9eb7f7` Q5 default: the quality arm gets **no live re-run**, and the paper keeps
only the recoverability/discrimination result — every billing sentence goes, because per-turn
`usage.prompt_tokens_details.cached_tokens` was never persisted in that arm (`runner.py:585-596` reads it,
never writes it to `rows.jsonl`; `billed_tokens_measured` is a recomputation at `runner.py:688`). A number
cannot be repaired by re-running it after the fact.

## Sources read

- `papers/context-cache/MANUSCRIPT.md` (1214 lines), `papers/context-cache/CLAIMS.md` (313 lines)
- `experiments/ptr-engine/quality/RESULTS.md` §4.1 (the A-vs-C cost paragraph, `:162-180`) and its
  **"Corrections (2026-10-25)"** note (`:244-272`) — read only, not edited (another unit owns it)
- `orchestration/handoffs/V-QUALITY-ARM.json` (overall **partial**)

## Census — sites resting on the billed-token identity

**sites_count = 0. Nothing deleted, nothing rewritten.** Neither paper file mentions the quality arm at all,
so no billing sentence from that arm can exist in the paper. Proof by greps (all run from
`papers/context-cache/`, against `MANUSCRIPT.md CLAIMS.md`):

| grep | hits |
|---|---|
| `49.?594` (49,594 / 49594 / 49 594) | **0** |
| `sum(prompt_tokens)+12·(R−1)`, `telescop`, `12·` | **0** |
| `billed`, `billing` (`grep -c -i`) | **0 / 0** |
| `34,372` / `34,374` / `34[ ,]37[24]` / `17,193` / `34,390` / `34,275` / `32,401` | **0** |
| `k01`, `k12`, `lumen`, `AUD-4417`, `756741be`, `9,000-byte`/`9000` | **0** |
| `PTR_STORE_MISS`, `withheld`, `no-body`, `old body`, `reference resolv`, `index-only` | **0** |
| `server-reported`, `server bill`, `matches the server`, `invoice`, `charge`, `dollar`, `price` | **0** |
| `reconcil` | 2 hits, both internal consistency, **not** billing: `MANUSCRIPT.md:647` (TUNED grid reconciled against `_mamba_cache_chunk_size` 64) and `MANUSCRIPT.md:1208` (`recompute_r2.py EVIDENCE` reconciles a cell's stored summary against its rows) |
| `CLAIMS.md` row ids | `C01…C69`; **no** quality-arm row exists |

The 0 sites are not a proof of silence by absence alone — the identity's own figures were searched for
individually (residuals A +151/+110/+106, B +117/+150/+127, C +159/+111/+17,193, D +100×3, and the
`34,275 ≠ 34,390` next clause): none appears anywhere in the two paper files.

## Every surviving use of the word "bill", examined and kept

The paper uses "bill" 16 times as a **metonym for measured uncached tokens per turn**, never as a
server-side charge and never as a telescoping identity. `MANUSCRIPT.md:107` fixes the meaning in the
limitations: *"Every figure in this paper is an uncached-token count or a time-to-first-token taken from a
request log"*. The counter behind each one is the main runner's own persisted `prompt_tokens` /
`cached_tokens`, which is a different code path from the quality arm's defect.

| site | text fragment | verdict |
|---|---|---|
| `MANUSCRIPT.md:56` | "The bill is a reuse bill, not prompt volume" | kept — interpretation of measured `cached_tokens` 31,616→30,656 |
| `MANUSCRIPT.md:72` | "the **engine** sets the per-turn uncached bill" | kept — §9b engine effect, measured |
| `MANUSCRIPT.md:80` | "2,096 MoE) sets its own bill (C63)" | kept — C63, measured |
| `MANUSCRIPT.md:86` | "grid *halves* the per-turn bill" | kept — already the withdrawn-padding sentence |
| `MANUSCRIPT.md:520` | "a 3.9 % increase on a bill of 528.64" | kept — 528.64 is a mean of measured uncached tokens (C64) |
| `MANUSCRIPT.md:525` | "per-turn bill (a 51.5 % reduction …)" | kept — states why the −51.5 % was void (same-turn self-hit) |
| `MANUSCRIPT.md:651` | heading "the engine sets the bill …" | kept — section title, C63 |
| `MANUSCRIPT.md:671` | "per-turn bill follows (Section 9a)" | kept |
| `MANUSCRIPT.md:706` | "so a per-turn bill" | kept |
| `MANUSCRIPT.md:756` | "in the direction of a cheaper bill" | kept |
| `MANUSCRIPT.md:763` | heading "what actually moves the bill" | kept — section title, C67 |
| `MANUSCRIPT.md:795` | "the largest bill (1,664.35 uncached tokens per turn on P1)" | kept — figure named as uncached tokens |
| `MANUSCRIPT.md:852` | "The bill is a lost prefix, not a boundary" | kept |
| `MANUSCRIPT.md:903` | "the *storage* block sets the bill" | kept |
| `CLAIMS.md:229,265` (C63/C65) | "sets the per-turn uncached bill" | kept — pinned claims, measured uncached/turn |
| `MANUSCRIPT.md:1144` | "read from the server's own counters rather than from a clock" | kept — true for the main cells, which persist `cached_tokens`; the two rows without a counter are already excluded and counted in C64 |

Why no rewrite: the mandated distinction is *measured tokens* vs *arithmetic-on-prefixes presented as a
server bill*. None of the 16 crosses it, and rewriting a heading or a pinned claim's title would touch a
verified claim to change nothing measured — rule 3 forbids that, and rule 2 prefers deletion over hedging,
not renaming over correctness.

## Verified set — untouched (rule 3)

No write was made to either paper file. Recorded mtimes at start of this unit:

```
papers/context-cache/MANUSCRIPT.md  mtime=2026-10-24 21:39:10 -0500  size=93021
papers/context-cache/CLAIMS.md      mtime=2026-10-24 13:48:51 -0500  size=45465
```

So these survive exactly as verified by `orchestration/handoffs/V-QUALITY-ARM.json` and are **not** billing
claims: 115 rows (48 request + 48 prediction + 12 rep + 4 corpus + 3 compaction); discrimination
A 3/3, B 0/3, C 3/3, D 0/3; arm D resolves 0 of 5 withheld bodies and answers `756741be`; index 458 B,
sha256 `e81ba025cfb484a8460022dedffa8cb8e7ffe09a53b365f9b84227eb105531d5`; the fact lives in `k01` only;
the corpus guard bites.

## Note for the next unit

The billing comparison (`34,372` vs `34,374` billed tokens, the five residual rows, the telescoping
identity) exists **only** in `experiments/ptr-engine/quality/RESULTS.md` §4.1, already annotated by that
file's own "Corrections (2026-10-25)" note. It must not be lifted into `MANUSCRIPT.md`/`CLAIMS.md` in any
form, and `C4` stays OPEN.

## Status

`done` — job was find-and-remove; the finding is that the paper never carried the billing result, evidenced
by the greps above. No source file required an edit.
