# UPKG7B — gated-read-batching release package

**STATUS: done** (30-call bound; 27 used). Skeleton card written first, then this final card.

## Unit contract
- **One purpose:** build paper #7's release package in `scratch/upkg7b/package/`, prove the minimal
  closure by cutting, census, gate, red→green.
- **Bound:** 30 tool calls.
- **Write paths:** `scratch/upkg7b/**`, `orchestration/units/UPKG7B.md`, `orchestration/handoffs/UPKG7B.json`.
- **Read-only:** `papers/gated-read-batching/**`, `papers/encoder-crossover-190/**`, `/home/zer0null/Duval` (no git run).

## Step 1 — minimal closure by cutting (scratch/upkg7b/cuts/, log: scratch/upkg7b/cut-ladder.log)
| cut | contents | bytes | checker exit |
|---|---|---|---|
| c0-all4 | rows+summary+report+provenance | 2,327,290 | 0 (49/49) |
| c1-rsg | rows+summary+report | 2,295,611 | 0 (49/49) |
| c2-rs | rows+summary | 2,272,020 | 0 (49/49) |
| c3-r | **rows alone = minimal closure** | 2,267,742 | 0 (49/49) |
| c4-mincols | rows stripped to CLAIMS.md's named columns | 847,714 | **1 — first break** |
| c5-gateonly | rows trimmed to gate modes | 2,137,573 | 1 |

**First break literal** (`scratch/upkg7b/cuts/c4-mincols.log`):
`[FAIL] rows_sha256 published='5732766d67d533a2' recomputed='6d23b25538a0f037' CLAIMS.md R`
Same cut also breaks `calls[gate16_none]`: published=120, recomputed=None — `calls` is **not a row** but the
count of `(task, tag-prefix)` groups, so the `task`+`tag` columns are load-bearing although the CLAIMS.md
one-line rule never names them. c5 additionally breaks `rows_total` (9,260→9,000).

## Step 2 — package (`scratch/upkg7b/package/`, 10 files, 2,365,766 B incl MANIFEST)
`data/gated-read-rows.jsonl` (byte-identical, 2,267,742 B, md5 3aad1ae29e472ef9f5f54e179510faf5) ·
`results/{gated-read-summary.json, GATED_READ_2026.md, GATED_READ_PROVENANCE.md}` (byte-identical) ·
`verify/recompute-claims.py` (49 checks, every comparison folded into the exit code) ·
`README.md` (validity limitation G-25 stated prominently; sources pinned by md5+sha256; cut ladder) ·
`LICENSE`/`COMMERCIAL.md`/`CONTRIBUTING.md` (byte-identical to the template) ·
`MANIFEST.json` via `tools/package/regen_manifest.py` (hand-written seed header only; every digest/size/count from the tool).

Tool for provenance: the checker's source-path provenance note ("provenance not established") is the regen default for a
package with no prior manifest; the README pins each source digest instead.

## Step 3 — census
`census.py` exit 0; 8 files scanned; **0 in-stimulus occurrences**; 20 identifiers hit only as shipped corpus
file paths (outside stimulus). No neutralisation applied: it would rewrite `data/` and break the required
byte-identity with source, and it cannot move a published number. No vocabulary list was widened;
`make_data_vocab.py --mode full` was not used.

## Step 4 — proof
- `check_manifest.py --package <abs>` → `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0` / `VERDICT PASS` / exit 0.
- Clean extraction: checker exit 0 (49/49); manifest checker exit 0.
- Red→green: perturb `"ptok": 220`→`221` in one shipped record → exit 1 with `[FAIL] rows_sha256` and
  `[FAIL] prompt_tok[gate1_none] 631210→631211`; restore byte-identical → exit 0.

## Disagreements with the card (card is a claim, not evidence)
1. The card says the checker must re-derive "the **15.279×** token ratio" and "the **exposure 0/20**" from
   MANUSCRIPT.md. **Neither is in MANUSCRIPT.md.** `MANUSCRIPT.md:195` explicitly scopes the
   end-to-end/injection-exposure arm out; `15.279` is at `GATED_READ_2026.md:206` (errata "15.3× (21 872 / 1 432)")
   and `0/20` at `GATED_READ_2026.md:199`. They are enforced in the checker under a RUN-REPORT-ONLY label and
   stated as such in README.
2. The card's 120/127/130 gold figures and the rows md5 were re-measured and **match**.
