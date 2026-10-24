# VAUDIT — post-repair licensed-text audit (offline, 0 live requests, no lock)

**Why:** every repair (`E2C`, `E3C`, `E4C`, `E4C3`, `LMC`, `E4RC`) landed **after** its verifier ruled, so the
repaired wording was never checked against the verifier's licensed text. This unit closes that loop.
**Scope:** repaired files `orchestration/units/{E2,E3,E4,E4R,LIVE-MEAS}.md` + `orchestration/handoffs/{E2,E3,E4,E4R,LIVE-MEAS}.json`;
verifier verdicts `VE24, VE2, VE13, VE4, VE4R, VLIVE`; `orchestration/STATUS.md` §7.
**Method:** scripted offline reads (`scratch/vaudit/audit.py`, `scratch/vaudit/audit_results.json`); normalisation
strips `**`/`*`/backticks, collapses whitespace and folds typographic dashes/minus to ASCII only for matching.
**Bound:** 22/24 tool calls, ~18 min, 0 live requests, no lock, **no write to any repaired file**.

## Check 1 — licensed-text fidelity: present in all five

Key licensed sentence per file, searched in the **current** file after emphasis/whitespace folding:

| File | Verifier → repair | Licensed sentence | Result |
|---|---|---|---|
| `E2.md` | VE24+VE2 → E2C | "a warm epoch is necessary … which this design does not isolate" | **emphasis-only** (`:15-16`) |
| `E3.md` | VE13 → E3C | "G7 hypothesis NOT ESTABLISHED (mamba checkpoint eviction)" | **verbatim** (`:4`) |
| `E4.md` | VE4+VE24 → E4C/E4C3 | "reproduced in 45/45 (CP95 lower 0.9213, no variance observed)"; VE4R sentence at `:15` | **emphasis-only** (`:7`, `:15`) |
| `E4R.md` | VE4R → E4RC | "persistent through repeat 3" | **emphasis-only** (`:74-77`, `:93-94`) |
| `LIVE-MEAS.md` | VLIVE → LMC | "R/A = 1.30x over 80 turns / 4 folds … 1.700x is a 40-turn figure" | **emphasis-only** (`:24`) |

**MISSING: none.** Caveat: the `verifier_corrections[].corrected_to` **machine strings** are condensed rewrites
(0/6 E2, 0/4 E3, 1/6 E4, 0/4 E4R, 0/6 LIVE-MEAS are byte-identical to the md prose), so the human record and the
JSON record carry the same correction in different words — a consistency gap, not a lost claim.

## Check 2 — unlicensed survivors: **4 of 5 files fail**

"Quoted" means inside a `>` blockquote or an explicit as-written quotation in a corrections table.

| File:line | Text | Standing? |
|---|---|---|
| `E2.md:159` | "the depth is a cache-epoch property, not a fork-policy property" | **LIVE** (retracted deflation) |
| `E2.md:160` | "reproduced **R's** depth instead" | **LIVE** (`reproduced R's depth`, retracted) |
| `E3.md:160` | `residual == L - 64*floor(L_prev/64) - L%64` | **LIVE** (retracted identity form) |
| `E3.md:167` | "across all 43 snapshots" | **LIVE** (retracted count; 44 on disk) |
| `E3.md:172` | "the mamba/checkpoint hypothesis **fails**" | **LIVE** ("fails" ≈ the retracted headline) |
| `E4.md:24` | "boundary-specific, deterministic, mechanism not established" | **LIVE** (`deterministic` retracted as inference) |
| `E4.md:63` | "The miss is deterministic, not a race…" | **LIVE** |
| `E4.md:68` | "**It is deterministic at n=20**" | **LIVE** |
| `E4.md:69` | "a permanent **64-token … shortfall** on every later repeat" | **LIVE** (unscoped) |
| `E4.md:70` | "The (L-1) form is the right ceiling rule at the boundary" | **LIVE** (scoped to rep-2) |
| `LIVE-MEAS.md:73` | "U15's 1.700 is **confirmed inside its own window**" | **LIVE** |
| `LIVE-MEAS.md:75` | "A overtakes R after ~40 turns" | **LIVE** |
| `LIVE-MEAS.md:81` | "81 unexplained ambient misses" | **LIVE** (`ambient` retracted) |
| `LIVE-MEAS.md:83` | "prompt and cached identical across all four arms" | **LIVE** (prompts differ in e2) |
| `LIVE-MEAS.md:46` | "a permanent 64-token shortfall" (E4 mechanism recap) | **LIVE** (unscoped) |

Properly quoted survivors (pass): `E2.md:13/:24` (as-written quotes), `E4.md:9/:13` (`> original`),
`E4R.md:12-13/:54` (table as-written), `LIVE-MEAS.md:15-19` (six-row as-written table). `E4R.md` is the only
file with **no** live survivor (`permanent` at `:93` is the scoped quotation; `one-repeat lag` at `:21` is the
research question, not a claim).

**Root cause:** the repairs were run under an *additive-only* rule, so the retracted sentences were left in the
body as live prose and only overridden by a top corrections section. The check demanded `superseded_text`-style
quotation; only `E2.json`, `E4R.json`, `LIVE-MEAS.json` carry that key (`E3.json`, `E4.json` do not).

## Check 3 — no datum lost: PASS

`json.load` OK for all five; contracted 7 keys all present; extra keys are the additive repair records.
Pinned rows shas unchanged (match the handoffs): E2 `47980b49…`/`250dcf04…`, E3 `7d123dd4…`/`b9969992…`,
E4 `5f10b316…` (`e4_report.json` still `f3a341c3…`), E4R `05a59f28…`, LIVE-MEAS `6150e534…`.
Payload re-checked: E2 decomposition `1658.9 = 456.7 + 30.2 + 1172.0` (JSON stores rounded strings; exact
`1,658.9375/456.6875/30.25` survive in `E2.md:56`); E3 `31/35` + `70/70` identity + stored `{−1728:1}` series;
E4 `45/45` vs `0/40`, Fisher `3.4646074215706565e-25` (full precision in `e4_report.json`; handoff stores
`3.46e-25`); E4R `180/180`, `40/40` at `L−64`, `0/40` at `L`; LIVE-MEAS `960`, `1.2988`, `113166 = 5081 + 108085`.
No number moved; the JSON roundings are the author's, not the repairs'.

## Check 4 — STATUS §7: one wrong number, one drifted count

Checked 20+ values against the handoff/report that owns them: 1.2988 ✓, 1.7046/1.7682/1.7195 ✓,
0.9508/1.0296/1.0561 ✓, hit rates .7791/.7667/.7653 & .9532/.9529/.9527 ✓, F/A 1.0661 ✓, R/F 1.2187 ✓,
t95 [1.2147,1.3828] ✓, +4,774.25 & CI [193.5,4868.25] ✓, 15/18 ✓, 116/120 ✓, 180/180 ✓, 40/40 at `L−64` ✓,
4 folds `[18,35,53,71]` ✓, 960/960 ✓, 45/45 vs 0/40 ✓, Fisher full precision ✓ (in `e4_report.json`),
e4 report sha `f3a341c3…` ✓, 19-row table ✓.

- **FAIL `STATUS.md:163`: "pad-adj 1.2964"** — source `handoffs/LIVE-MEAS.json` `pad_adjusted_R_over_A_pooled = 1.2963`
  (analysis mean 1.2962747633 → 1.2963); the card itself says 1.296. Off by 1 in the 4th decimal.
- **DRIFT §3: "617 parseable handoffs and 599 unit cards" / "623 entries"** — disk now holds **619 `.json` + 6 `.md`
  = 625 entries**, **600** unit cards. 617/599 is exactly the pre-`STATUS-E`/pre-`U6-R` set (both wrote at
  16:20–16:21, after the sweep), so this is a dated count, not a fabrication — but it no longer matches disk.

## Check 5 — red→green: the audit can fail

1. Copy `scratch/vaudit/E4_mut.md`: licensed `reproduced in 45/45 (CP95 lower 0.9213, no variance observed)`
   → `deterministic`. Audit flips that check **PRESENT → MISSING** while `deterministic` becomes visible.
2. Copy `scratch/vaudit/STATUS_mut.md`: `1.2988 → 1.2999`. Audit reports `1.2988` absent; the real
   `LIVE-MEAS.json` still carries it. Real files untouched (`E4.md` unchanged).

## Check 6 — containment: PASS

Per-run mtimes: E2 cells 15:48–15:49 < E2C 15:59; E3 cells 15:44–15:45 < E3C; E4 cells 15:45–15:49 < E4C 16:00;
E4R cells 16:12 < E4RC 16:17; LIVE-MEAS cells 16:07–16:12 < LMC 16:15. Shared modules `client.py`/`runner.py`/
`analyze.py` predate every repair. `VERDICTS.md` was appended once by `VLIVE` (16:15) and not touched by any
repair (all repair write-paths exclude it); tail is the `VE4R` ruling. No `cells/**` write, no `VERDICTS.md` rewrite.

## Ruling

`partial` — all five licensed headlines survived repair and every datum/sha is intact, but the retracted wording
still stands as **live prose** in 4 of 5 repaired files (E2, E3, E4, LIVE-MEAS), and one STATUS §7 number is
wrong. The record is citable **only through the top corrections sections**; the bodies remain pre-ruling text.
