# E4C — `e4-record-correction`: apply VE4 + VE24 (E4 half) wording repairs

**Status:** done · **Kind:** record repair, **not** a re-measurement
**Bound:** ≤12 tool calls used **10**; ≤10 min · **0 live requests**, no `.occamy.lock`, no `git`
**Write paths (only these, all four written):** `orchestration/units/E4C.md`, `orchestration/handoffs/E4C.json`, `orchestration/units/E4.md`, `orchestration/handoffs/E4.json`.

## Purpose (one)

E4 (`boundary-n20`, G9) passed **both** independent verifiers on every measurement — VE4 `overall=pass` with `not_reproduced: []`, VE24's E4 half (`c6`–`c10`) reproduced from the pinned rows. Only the **words** were wrong. This unit applies the five agreed wording corrections so no later unit cites a sentence the rows do not license. Additive: E4's original text stands verbatim; the repair is a new top section plus a `verifier_corrections` array.

## Inputs read

`orchestration/handoffs/VE4.json`, `orchestration/units/VE4.md`, `orchestration/handoffs/VE24.json` (E4 half), `orchestration/units/VE24.md`, `orchestration/handoffs/E4.json`, `orchestration/units/E4.md` (74 lines), and read-only `experiments/context-cache/cells/E4/e4_report.json` + `e4_rows.jsonl`. Pinned sha confirmed on disk: **`5f10b3160a8c7b394512b841a991e5f1cc5956d2c6c252aaa1645d0fae8a2560`**; report sha `f3a341c3…`, `pooled.fisher_two_sided_p = 3.4646074215706565e-25`.

## Corrections applied (both verifiers agree)

| # | Before (as written, retained verbatim) | After (licensed sentence in the new section) | Ruling |
|---|---|---|---|
| 1 | `E4.md:42` "The miss is deterministic, not a race with a distribution."; `:47` "It is deterministic at n=20, not a 1-in-k race" | rep-1 `cached == 0` in **45/45** boundary rows (**40/40** at 1024+1088), **CP95 lower 0.9213**, no intermediate value, no TTFT variance — **description only**; a ~7.9 % escape race is not excluded, no rep-3, two lengths, one endpoint | overstated as inference |
| 2 | `E4.md:48` "only at `64*floor((L-1)/64) = L - 64`"; `:49` "The (L-1) form is the right ceiling rule at the boundary" | **steady-state (rep-2) ceiling**: 40/40 at `L−64`, 0/40 at `L`; **not** a rep-1 ceiling (rep-1 predicts `L−64`, observed 0); **refuted as the miss rule in both directions** — 1025 → 0/20, 1024/1088 → 20/20 | scope corrected |
| 3 | `E4.md:48` "a permanent 64-token (one whole block) shortfall on every later repeat" | a multiple pays a full first-repeat prefill **and a one-repeat 64-token lag at rep-2**; **unmeasured at rep-3** (`E4.md:58` already conceded this) | overstated → "permanent" dropped |
| 4 | `E4.md:49` tax law "0/20 at 1024 and 0/20 at 1088" / "wrong there"; `E4.json` `tax_law_fails_at_multiples` | **falsified as an equality at the multiples only** (40/40 rep-1, 40/40 rep-2; 960 0/5 = spot-check); **upper bound `cached <= L` survives**; general law away from the boundary = **"not observed at n=20"** | scope narrowed |
| 5 | `E4.md:26`/`:71` A1 drop order | departed from the card: kept **960 at n=5**, dropped the real control **1008**; final rows **220 = 85 cold + 85 rep1 + 40 rep2 + 10 cal**, exactly at the 220 cap, zero headroom | disclosure carried, not a defect |

**Numbers unchanged** (reproduced by both verifiers from the pinned sha; untouched in `E4.json`): 960 5/5, 1023 0/20, 1024 20/20, 1025 0/20, 1088 20/20; pooled **45/45 vs 0/40**; Fisher two-sided **3.46e-25**; rep-2 **40/40** at `L−64`.

## What was done, mechanically

1. **Probe (read-only):** re-hashed `e4_rows.jsonl` → `5f10b316…`; re-read `e4_report.json` → pooled CP95 `[0.9213,1.0]` / `[0.0,0.0881]`, Fisher `3.4646…e-25`. No POST, no lock, no `e4_analyze.py` rerun (both verifiers already reran it byte-identically; a third run adds nothing).
2. **`E4.md`:** inserted `## Corrections (VE4 + VE24, applied by E4C)` after the H1, before `**Status:**`. **Zero existing lines edited or deleted.**
3. **`E4.json`:** added `verifier_corrections` (5 entries, each `claim`/`as_written`/`corrected_to`/`ruling`/`verifier`/`applied:true`) and a `corrections_note`. Written to `E4.json.tmp-e4c` → parsed → checked the 7 contracted keys + 5 entries + `applied` all true → `os.replace` (atomic same-directory move), temp gone.

## Evidence

- **Before/after per correction:** table above; each `as_written` is quoted from the retained original line, each `corrected_to` is the sentence now at the top of `E4.md` and duplicated as machine-readable text in `E4.json.verifier_corrections[i].corrected_to`.
- **Originals intact:** all five quoted originals re-checked in `E4.md` after the insert — **5/5 present**
  with markdown `**`bold stripped and source-line wrapping collapsed (two spans are bold and wrapped);
  byte-exact is **3/5** for that reason only. Per-sentence booleans and both counts in
  `E4C.json.evidence.originals_intact`.
- **`E4.json` still parses with its original keys:** before `['unit','status','artifacts','evidence','blocker','next_unit_hint','write_paths','assumptions']` → after the same **8 keys in the same order**, plus `verifier_corrections` and `corrections_note`; contracted-key check **7/7 true**; `evidence` still 22 keys, `artifacts` still 7, `unit/status` = `E4/done`; numbers spot-check identical (`5/5, 0/20, 20/20, 0/20, 20/20`; `45/45 CP95 [0.9213,1.0]`; `3.46e-25`).
- **Containment:** only the four declared paths written; `cells/E4/*`, `src/`, `tests/`, `VERDICTS.md` and every other unit's files untouched (no write path outside the four; `cells/E4` read-only).

## Assumptions

- **A1** — "additive only" is honoured literally: corrected claims stay in place as written, and each `as_written` quotes them with their line number, so a reader can see which sentence the ruling governs. The section says so explicitly ("stands verbatim", "no number changes").
- **A2** — `verifier: "VE4 + VE24 (agree)"` only where both handoffs carry the same ruling; where VE24 was more specific (80/80 attainment, "first repeat, five lengths, one endpoint") that phrasing is used in `corrected_to`.
- **A3** — the A1 deviation is recorded as a **disclosure**, not converted into a defect: both verifiers passed it, and the rows' composition (220 = 85+85+40+10) is verified arithmetic, not inference.
- **A4** — no re-analysis: the pinned `e4_report.json` is used as the verifier-reproduced value rather than rerunning `e4_analyze.py`, because both verifiers reran it byte-identically on the same sha.
