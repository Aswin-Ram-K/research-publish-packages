# WITHDRAWN — every number this batch withdrew, with what replaces it

**Register:** `experiments/ptr-engine/measure/WITHDRAWN.json` · **15 entries** (8 seeded + 7 found by sweep) · generated 2026-10-26 · unit `WITHDRAWN-INDEX`

Eight published numbers were retracted or superseded after measurement, and each correction lived in a
different board post and a different card document. This is the machine-readable register beside those
documents — **not** an edit of them. Every historical file, board post and cell report is byte-identical.

## Screen a document before publishing it

```bash
python3 experiments/ptr-engine/tools/withdrawn_index.py --check docs/SOMETHING.md
# exit 1 = a withdrawn claim is quoted without its correction attached (ids printed on stdout)
# exit 0 = clean
python3 experiments/ptr-engine/tools/withdrawn_index.py --self-test
# exit 0 = every decided_by handoff exists and every superseded_by artefact opens
```

A hit is not an error in the register: it means the document quotes a withdrawn number and the correction
is more than 400 characters away (or absent). Attach the correction, or cite the superseding artefact instead.

## Counts

| | |
|---|---|
| entries | 15 |
| seeded / found by sweep | 8 / 7 |
| `none — no replacement exists` | 1 |
| seeds the artefact did not support (discrepancy recorded) | 3 |
| kind `wrong_unit` | 1 |
| kind `unsound_rule` | 1 |
| kind `wrong_denominator` | 3 |
| kind `retracted_finding` | 8 |
| kind `overstated_mechanism` | 2 |
| status `withdrawn` | 9 |
| status `superseded` | 6 |

## The register

| id | claim | kind | status | superseded by | citable |
|---|---|---|---|---|---|
| `WI-001` | ≈466 of 4,320 requests used | wrong_unit | withdrawn | `REQUEST-LEDGER.json` → 1,101 requests used (raw); 3,219 remaining of 4,320 | never |
| `WI-002` | requests 1,071 · remaining 3,249 | unsound_rule | superseded | `REQUEST-LEDGER.json` → 1,101 requests used · 3,219 remaining (both already present  | only with the correction attached |
| `WI-003` | accuracy 55/64 wilson95 n=64 0.8594 [0.7538, 0.9242] (undecidable: 0) | wrong_denominator | superseded | `cell-transcript-grow-20261026T144452Z.grade-v5.json` → checkpoint_accuracy 3/3 (decidable 3) | only with the correction attached |
| `WI-004` | p95 318.14 [235.00, 526.41] n=68  (G7 V4-TOOLS pointer-stable) | retracted_finding | withdrawn | none — no replacement exists | never |
| `WI-005` | 5/43 mixes grader eras | retracted_finding | withdrawn | `QUALITY-ERAS.json` → 5/43 reproduced identically under det_verify.py sha256 12ccc | never |
| `WI-006` | pointer-stable grows like a transcript … reaches 217k at turn 48 | retracted_finding | withdrawn | `ARM-RECONCILE.json` → max prompt_tokens on any arm/grid = 34,279; pointer-stable t | never |
| `WI-007` | 0 of 66 are wrong values | overstated_mechanism | superseded | `NEVER-ANSWERED-ROOT.json` → 0 of 66 on the ANSWER: line only; 5 cells assert a value in  | only with the correction attached |
| `WI-008` | the gate chain has no surviving hole  (the V-GATE-CHAIN-3 closure PASS) | retracted_finding | superseded | `V-GATE-CHAIN-3.json` → overall: fail — 6 bypasses survive; 0 of 3 decision expressi | never |
| `WI-009` | starts at 1,867 tokens | retracted_finding | withdrawn | `ARM-RECONCILE.json` → pointer-stable G4 turn 1 = 967 prompt tokens | never |
| `WI-010` | a slope of 1.21x per turn (r = 0.9799) | retracted_finding | withdrawn | `ARM-RECONCILE.json` → 1.017614x/turn, i.e. 4.4433 tok/turn; OLS r = 0.3265 (log-li | never |
| `WI-011` | pointer-stable's p50 advantage is explained by 98.7 % prefix cache hit | overstated_mechanism | withdrawn | `ARM-RECONCILE.json` → measured cached share 0.871157 (not 0.987) | never |
| `WI-012` | run_longrun.py:436 reset at 6,000 vs :441 reset at 8,000 | retracted_finding | withdrawn | `ARM-RECONCILE.json` → 0 resets exist: :436 is `value = int(raw)` and :441 a CapUsa | never |
| `WI-013` | transcript-grow 0.85x/turn, reaching ~620k | retracted_finding | withdrawn | `ARM-RECONCILE.json` → 1.061068x/turn (676.9636 tok/turn), 2,114 -> 34,279; the 901 | never |
| `WI-014` | accuracy 3/27 = 11.1 % (the stored grade_v5 headline) | wrong_denominator | superseded | `QUALITY-ERAS.json` → 3/25 current (pointer-stable 3/10 after the one drifted grid | only with the correction attached |
| `WI-015` | accuracy  55/64  wilson95 n=64  0.8594 [0.7538, 0.9242]  (undecidable: 0) | wrong_denominator | superseded | `cell-transcript-grow-20261026T144540Z.grade-v5.json` → 3/3 (decidable implied by grade-v5) | only with the correction attached |

## Detail

### `WI-001` — withdrawn

- **claim (as published):** `≈466 of 4,320 requests used`
- **where:** docs/REQUEST-LEDGER.md:9 (six rounds of status lines); retired at docs/OPERATOR-BRIEF.md:131-133
- **kind:** `wrong_unit`
- **superseded_by:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` → **1,101 requests used (raw); 3,219 remaining of 4,320**
- **decided_by:** card `REQUEST-LEDGER` · `orchestration/handoffs/V-DUPLICATE-RULE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** 466 counted turn rows only, not requests: the turn-row count is 801 and the artefact has no row set that yields 466. Measured understatement 2.36x (1,101/466).

### `WI-002` — superseded

- **claim (as published):** `requests 1,071 · remaining 3,249`
- **where:** experiments/ptr-engine/measure/REQUEST-LEDGER.json (requests_deduplicated 1071, remaining_deduplicated 3249); propagated to docs/REQUEST-LEDGER.md:9ff
- **kind:** `unsound_rule`
- **superseded_by:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` → **1,101 requests used · 3,219 remaining (both already present as requests_raw / remaining_raw)**
- **decided_by:** card `V-DUPLICATE-RULE` · `orchestration/handoffs/V-DUPLICATE-RULE.json`
- **date:** 2026-10-26 · **still_citable:** only with the correction attached
- **why:** The 30-row deduction is visible but NOT applied: deduction.applied false, deducted_requests 0. The rule is unsound because content_sha256 hashes the assistant response, not the request.
- **DISCREPANCY (seed vs artefact):** SEED CITES run_longrun.py:1493; the artefact does NOT say that. REQUEST-LEDGER.json evidence_note records that the card's line number drifted and the assignment is run_longrun.py:1555 (`"content_sha256": (sha256_text(recorded_content)`), re-measured 869/869 rows. The live line number is 1555, not 1493.

### `WI-003` — superseded

- **claim (as published):** `accuracy 55/64 wilson95 n=64 0.8594 [0.7538, 0.9242] (undecidable: 0)`
- **where:** experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.md:36 (registered as PN-001 at docs/PUBLISHED-NUMBERS.md:57)
- **kind:** `wrong_denominator`
- **superseded_by:** `experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.grade-v5.json` → **checkpoint_accuracy 3/3 (decidable 3)**
- **decided_by:** card `PUBLISHED-NUMBER-AUDIT` · `orchestration/handoffs/PUBLISHED-NUMBER-AUDIT.json`
- **date:** 2026-10-26 · **still_citable:** only with the correction attached
- **why:** 55/64 is a proportion over the run transcript's 64 TURN ROWS, printed as if it were checkpoint accuracy. The instrument grades checkpoints, of which 3 are decidable in this fixture.

### `WI-004` — withdrawn

- **claim (as published):** `p95 318.14 [235.00, 526.41] n=68  (G7 V4-TOOLS pointer-stable)`
- **where:** docs/LATENCY-REPORT.md:45 (still worded '…… stands'); withdrawn at docs/LATENCY-REPORT.md:35, :90, :100, :153 and in measure/LATENCY-REPORT.json p95_withheld
- **kind:** `retracted_finding`
- **superseded_by:** `none — no replacement exists` → **none — no replacement exists**
- **decided_by:** card `LATENCY-UNDER-DISPUTE` · `orchestration/handoffs/LATENCY-UNDER-DISPUTE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** Withdrawn on two independent grounds: the de-duplicated sample is 51 < the n>=60 order-statistic floor for p95 (n*(1-q)=2.6 < 3), and dedupe rule R is disputed by V-DUPLICATE-RULE. G7 is single-arm, so no comparison exists to publish in its place.
- **DISCREPANCY (seed vs artefact):** SEED SAYS WITHDRAWN; docs/LATENCY-REPORT.md:45 still reads '`318.14 [235.00, 526.41]` **stands**.' — a stale remnant contradicted by :35/:90/:100/:153 of the same file. Not edited here (additive register); recorded as a live inconsistency in that document.

### `WI-005` — withdrawn

- **claim (as published):** `5/43 mixes grader eras`
- **where:** the era-mixing charge against docs/OPERATOR-BRIEF.md:45; answered at docs/QUALITY-ERAS.md:14 ('is **not** era-mixed') and :69-72
- **kind:** `retracted_finding`
- **superseded_by:** `experiments/ptr-engine/measure/QUALITY-ERAS.json` → **5/43 reproduced identically under det_verify.py sha256 12ccc74e… (pass 5, fail 38, missing 36, undecidable 13)**
- **decided_by:** card `QUALITY-ERA-TABLE` · `orchestration/handoffs/QUALITY-ERA-TABLE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** The charge is false: 5/43 is det_verify's PARTIAL-GRID figure and re-derives identically. What survives is a labelling demand, not a number change - the 5/43 must be published WITH its instrument name and sha.
- **DISCREPANCY (seed vs artefact):** The charge itself is false, not merely unproven: no artefact supports 'mixes grader eras'. The number 5/43 is NOT withdrawn; only the accusation is. A reader may cite 5/43 only with the det_verify sha attached (caveat recorded in 'caveat').
- **caveat:** 5/43 = 11.6% is citable as det_verify.py sha256 12ccc74e… on a partial grid (missing 36, undecidable 13 of 92 declared cells). Era table: docs/QUALITY-ERAS.md.

### `WI-006` — withdrawn

- **claim (as published):** `pointer-stable grows like a transcript … reaches 217k at turn 48`
- **where:** board ws:78cead56-384a-4d9c-b974-02b454c6d3d5 seq 891 (ARM-INTEGRITY 2ae53b51 mid-run F0); retracted by board seq 893
- **kind:** `retracted_finding`
- **superseded_by:** `experiments/ptr-engine/measure/ARM-RECONCILE.json` → **max prompt_tokens on any arm/grid = 34,279; pointer-stable turn 48 = 2,197; G4 pointer-stable slope 4.4433 tok/turn**
- **decided_by:** card `V-ARM-RECONCILE` · `orchestration/handoffs/V-ARM-RECONCILE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** 216,951 is not an endpoint: it is the SUM of 68 turn rows of a DIFFERENT arm in a DIFFERENT grid (G7 V4-TOOLS). No arm reaches 217k; corpus-wide max is 51,216.

### `WI-007` — superseded

- **claim (as published):** `0 of 66 are wrong values`
- **where:** docs/QUALITY-REASON-MIX.md:125-126 ('63 of 66 non-passes (95.5 %) are never_answered; 0 of 66 are wrong values')
- **kind:** `overstated_mechanism`
- **superseded_by:** `experiments/ptr-engine/measure/NEVER-ANSWERED-ROOT.json` → **0 of 66 on the ANSWER: line only; 5 cells assert a value in prose, 4 of them wrong (asserted_wrong 4, asserted_right 1)**
- **decided_by:** card `NEVER-ANSWERED-ROOT-2` · `orchestration/handoffs/NEVER-ANSWERED-ROOT-2.json`
- **date:** 2026-10-26 · **still_citable:** only with the correction attached
- **why:** True only of the graded ANSWER: line. The widened asserted_value extractor finds five prose cells stating a value; four are wrong. The claim's scope, not its arithmetic, is the error.

### `WI-008` — superseded

- **claim (as published):** `the gate chain has no surviving hole  (the V-GATE-CHAIN-3 closure PASS)`
- **where:** closure PASS of card 4e7e8017 / exec 0884f187, resting on the attack script embedded in orchestration/units/V-GATE-CHAIN-3.md; adjudicated at experiments/ptr-engine/measure/VERDICT-DISPUTE.md:63-75
- **kind:** `retracted_finding`
- **superseded_by:** `orchestration/handoffs/V-GATE-CHAIN-3.json` → **overall: fail — 6 bypasses survive; 0 of 3 decision expressions fully validated**
- **decided_by:** card `VERDICT-DISPUTE` · `orchestration/handoffs/VERDICT-DISPUTE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** 6 of 26 assertions encoded the bypasses as their pass condition, so a green run is compatible with the holes surviving (it demands they survive). PASS is supportable only as 'the attack script ran green'.

### `WI-009` — withdrawn

- **claim (as published):** `starts at 1,867 tokens`
- **where:** board seq 891 / experiments/ptr-engine/measure/ARM-RECONCILE.md:47
- **kind:** `retracted_finding`
- **superseded_by:** `experiments/ptr-engine/measure/ARM-RECONCILE.json` → **pointer-stable G4 turn 1 = 967 prompt tokens**
- **decided_by:** card `V-ARM-RECONCILE` · `orchestration/handoffs/V-ARM-RECONCILE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** No row on disk has prompt_tokens 1,867. Nearest are 1,864 (1 row) and 1,870 (13 rows), all G1 transcript-compact/transcript-grow turn 1.

### `WI-010` — withdrawn

- **claim (as published):** `a slope of 1.21x per turn (r = 0.9799)`
- **where:** board seq 891 / experiments/ptr-engine/measure/ARM-RECONCILE.md:49-50
- **kind:** `retracted_finding`
- **superseded_by:** `experiments/ptr-engine/measure/ARM-RECONCILE.json` → **1.017614x/turn, i.e. 4.4433 tok/turn; OLS r = 0.3265 (log-linear 0.3113)**
- **decided_by:** card `V-ARM-RECONCILE` · `orchestration/handoffs/V-ARM-RECONCILE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** Self-inconsistent as well: 1,867->217,000 implies 1.1065x/turn at n=48 and 1.2297x at n=24, so 1.21x only coheres at n~23 intervals.

### `WI-011` — withdrawn

- **claim (as published):** `pointer-stable's p50 advantage is explained by 98.7 % prefix cache hit`
- **where:** board seq 891 / experiments/ptr-engine/measure/ARM-RECONCILE.md:44
- **kind:** `overstated_mechanism`
- **superseded_by:** `experiments/ptr-engine/measure/ARM-RECONCILE.json` → **measured cached share 0.871157 (not 0.987)**
- **decided_by:** card `V-ARM-RECONCILE` · `orchestration/handoffs/V-ARM-RECONCILE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** Unsupported rather than arithmetically wrong: the arm's cached share measures 0.871157, so 98.7 % is not a rounding of it.

### `WI-012` — withdrawn

- **claim (as published):** `run_longrun.py:436 reset at 6,000 vs :441 reset at 8,000`
- **where:** board seq 891 / experiments/ptr-engine/measure/ARM-RECONCILE.md:51
- **kind:** `retracted_finding`
- **superseded_by:** `experiments/ptr-engine/measure/ARM-RECONCILE.json` → **0 resets exist: :436 is `value = int(raw)` and :441 a CapUsageError line, both in allocation_for(); the only 8000 is TOOL_READ_CAP_CHARS at :209, and wall_tokens is 65536 from the fixture**
- **decided_by:** card `V-ARM-RECONCILE` · `orchestration/handoffs/V-ARM-RECONCILE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** A false code citation, so the 9,000-token compaction span it claimed does not exist. Not edited in the source file; recorded here.

### `WI-013` — withdrawn

- **claim (as published):** `transcript-grow 0.85x/turn, reaching ~620k`
- **where:** board seq 891 / experiments/ptr-engine/measure/ARM-RECONCILE.md:52
- **kind:** `retracted_finding`
- **superseded_by:** `experiments/ptr-engine/measure/ARM-RECONCILE.json` → **1.061068x/turn (676.9636 tok/turn), 2,114 -> 34,279; the 901,109 figure is a 48-turn SUM (mean 18,773.1), not a prompt size**
- **decided_by:** card `V-ARM-RECONCILE` · `orchestration/handoffs/V-ARM-RECONCILE.json`
- **date:** 2026-10-26 · **still_citable:** never
- **why:** Same unit error as WI-006: a column sum read as an endpoint.

### `WI-014` — superseded

- **claim (as published):** `accuracy 3/27 = 11.1 % (the stored grade_v5 headline)`
- **where:** docs/QUALITY-ERAS.md:74 ('the stored **3/27 = 11.1 %** form is withdrawn')
- **kind:** `wrong_denominator`
- **superseded_by:** `experiments/ptr-engine/measure/QUALITY-ERAS.json` → **3/25 current (pointer-stable 3/10 after the one drifted grid); as-recorded form was 3/27 with pointer-stable 3/12**
- **decided_by:** card `V-ARM-RECONCILE` · `orchestration/handoffs/V-ARM-RECONCILE.json`
- **date:** 2026-10-26 · **still_citable:** only with the correction attached
- **why:** One grid of 23 regraded pairs drifted (cell-pointer-stable-20261026T145722Z.grade-v5.json, 22 paths, 2 cells moved), so two cells left the decidable population.

### `WI-015` — superseded

- **claim (as published):** `accuracy  55/64  wilson95 n=64  0.8594 [0.7538, 0.9242]  (undecidable: 0)`
- **where:** experiments/ptr-engine/measure/cell-transcript-grow-20261026T144540Z.md:36
- **kind:** `wrong_denominator`
- **superseded_by:** `experiments/ptr-engine/measure/cell-transcript-grow-20261026T144540Z.grade-v5.json` → **3/3 (decidable implied by grade-v5)**
- **decided_by:** card `PUBLISHED-NUMBER-AUDIT` · `orchestration/handoffs/PUBLISHED-NUMBER-AUDIT.json`
- **date:** 2026-10-26 · **still_citable:** only with the correction attached
- **why:** Row proportion (64 rows) published as checkpoint accuracy; registered in PUBLISHED-NUMBERS.json as PN-002. arm transcript-grow

## What this register does not do

- It does not edit, banner or strike through any historical document, post or cell report.
- It does not re-derive a number: every replacement is copied from a cited artefact, never computed here.
- A `none — no replacement exists` row is an examined outcome, not a gap: no measurement replaces it.
- Card ids are the unit ids the artefacts record; only `WI-008`'s deciding card carries an execution id (`4e7e8017` / exec `0884f187`).

## Register changes

- **2026-10-26** (card `WITHDRAWN-REGISTER-FIX`): **WI-011's quote narrowed from `98.7` to
  `98.7 % prefix`** (false positives on citable p50s — `198.72`, `198.7230`, `198.74`). The
  withdrawn claim is the prefix-cache *mechanism*; the measured cached share is **0.871157**, not
  0.987, so the phrase is what the guard must match. **`--strict` added for published pages**: the
  window is the enclosing blank-line-delimited paragraph instead of 400 characters, so a stale
  sentence cannot be excused by a correction marker in a neighbouring paragraph. Six inline
  `WI-011 guard note` comments in `docs/LATENCY-REPORT.md` and four `no_correction_needed` rows in
  `WITHDRAWN-SCREEN.json` existed only to silence the false positive and were removed. No
  withdrawn figure was deleted from any page.
- **2026-10-26** (same card): short-quote audit — `WI-001` (`≈466`, retired: the raw count is
  **1,101** requests used) and `WI-006` (`217k`, retracted: no arm reaches it, corpus max
  **34,279** prompt tokens) remain under 5 characters. Neither fires on a correct number in
  this corpus; both are flagged in `orchestration/units/WITHDRAWN-REGISTER-FIX.md`.
