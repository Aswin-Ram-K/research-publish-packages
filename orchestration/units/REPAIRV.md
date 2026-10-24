# REPAIRV — `vaudit-remediation` (record repair only: 0 live requests, no lock, no new analysis)

**Why:** verifier `VAUDIT` (`handoffs/VAUDIT.json`, verdict **partial**) found the repaired records still carried the
retracted wording as **live prose** in 4 of 5 files (15 spots) and one wrong STATUS number with a drifted count.
**Scope:** `units/{E2,E3,E4,LIVE-MEAS}.md`, `handoffs/{E3,E4}.json`, `STATUS.md:163` and `STATUS.md` §3.
**Bound:** ≤18 tool calls / ≤15 min. **Used 20 calls** (bound exceeded by 2: two anchor failures in the first apply
needed retries); 0 live requests, no `.occamy.lock`, no re-analysis, no number changed, no `cells/**` write.

## Method

Each retracted sentence was replaced by its **licensed replacement** (taken from the same file's `## Corrections`
section — VE24/VE2, VE13, VE4/VE24/E4C3, VLIVE) and the exact former text was placed **immediately beside it** as
`> original (superseded): "<former text>"`. Mechanical checks in `scratch/repairv/run.py`:
`apply` (anchored span edits, each anchor asserted unique), `check` (survivor hunt), `redgreen`.
The survivor hunt joins lines, strips **only** `**`/backticks (never a bare `*`, so `64*floor(...)` survives — the
E4C2 lesson), collapses whitespace, and classifies a hit **PASS** only inside a `>` blockquote, a top-corrections
section, or an as-written table cell; anything else is **LIVE = FAIL**.

**Corrections-header claims were made true, not left contradicted:** E2's "nothing beneath it was edited", E4's "the
text of every later section stands verbatim as written", LIVE-MEAS's "retained verbatim in the Result section" now
say the retracted sentences sit as `> original (superseded)` quotations. E4's `E4.md:58` self-cite (stale after
earlier insertions) was converted to a named-bullet reference so the reflow cannot break it.

## Proof 1 — survivor hunt: 15/15 now quoted, 0 live

`python3 scratch/repairv/run.py check` (full log `scratch/repairv/check.log`):

| File | Retracted string (emphasis-stripped) | Now quoted at |
|---|---|---|
| E2.md | the depth is a cache-epoch property, not a fork-policy property | :14 (corrections) + :168 (`> original`) |
| E2.md | reproduced R's depth instead | :168 (`> original`) |
| E3.md | residual == L - 64*floor(L_prev/64) - L%64 | :43 (corrections) + :173 (`> original`) |
| E3.md | across all 43 snapshots | :174 (`> original`) |
| E3.md | the mamba/checkpoint hypothesis fails | :181 (`> original`) |
| E4.md | boundary-specific, deterministic, mechanism not established | :26 (`> original`) |
| E4.md | The miss is deterministic, not a race with a distribution. | :67 (`> original`) |
| E4.md | It is deterministic at n=20, not a 1-in-k race | :9 (restored) + :71 (`> original`) |
| E4.md | a permanent 64-token (one whole block) shortfall | :13 (restored) + :75 (`> original`) |
| E4.md | The (L-1) form is the right ceiling rule at the boundary | :80 (`> original`) |
| LIVE-MEAS.md | a permanent 64-token shortfall | :50 (`> original`) |
| LIVE-MEAS.md | U15's 1.700 is confirmed inside its own window | :16 (table) + :82 (`> original`) |
| LIVE-MEAS.md | A overtakes R after ~40 turns | :15 (table) + :82 (`> original`) |
| LIVE-MEAS.md | 81 unexplained ambient misses | :19 (table) + :91 (`> original`) |
| LIVE-MEAS.md | prompt and cached identical across all four arms at t10/t17 | :17 (table) + :96 (`> original`) |

```
SPOTS: 15/15 quoted, 0 live
```

## Proof 2 — corrected sentence still stands as live prose

| File:line | Licensed sentence now live |
|---|---|
| E2.md:161 | a warm epoch is necessary for this comparison … the arm still contributes (an interaction) which this design does not isolate |
| E3.md:45 | `tail_term = L - 64*floor(L_prev/64) - L%64` (`residual = tail_term + deficit`) |
| E3.md:170 | across all **44** snapshots |
| E3.md:177 | the mamba/checkpoint hypothesis is **NOT ESTABLISHED** as the explanation of the deviation universally |
| E4.md:7, :65, :72 | reproduced in 45/45 (CP95 lower 0.9213, no variance observed) |
| E4.md:15, :76 | **persistent one-block (64-token) tax** on every later repeat measured (rep-3 40/40 at L−64, 0/40 at L) |
| E4.md:78 | (L−1) is the steady-state (rep-2) ceiling at the boundary, not a rep-1 rule |
| LIVE-MEAS.md:46 | persistent one-block (64-token) tax (rep-3 40/40, 0/40; repeats 2–3 of 3) |
| LIVE-MEAS.md:77 | consistent within 0.3–4.0 % (U15's 1.700) |
| LIVE-MEAS.md:80 | at **parity** (e2/e3) with one epoch reversing |
| LIVE-MEAS.md:89 | 81 unexplained **unattributed** misses (54/81 within 2 turns of a fold) |
| LIVE-MEAS.md:94 | **prompts** identical in **e3 only** |

Data preserved: E4 45/45 vs 0/40, Fisher 3.46e-25, all table cells, every `cells/**` sha untouched.

## Proof 3 — handoffs: `superseded_text` added, payload unchanged

```
E3: parse=OK contracted=7/7 superseded_text=True payload={'31/35': True, '70/70': True}
E4: parse=OK contracted=7/7 superseded_text=True payload={'45/45': True, '0/40': True, '3.46e-25': True}
```
`apply_json` writes temp → re-parses → asserts the 7 contracted keys, `superseded_text`, and that the **rest of the
document is byte-identical** (`json.dumps(..., sort_keys=True)` with only the two added keys removed) before `mv`.

## Proof 4 — STATUS

- `STATUS.md:163` now reads **`pad-adj 1.2963`**; `1.2964` occurs **0** times (source: `handoffs/LIVE-MEAS.json`
  `pad_adjusted_R_over_A_pooled = 1.2963`; analysis mean 1.2962747633).
- §3 re-swept by `scratch/repairv/run.py`'s sweep at **2026-10-21T16:29-05:00** (America/Chicago) — **625 `.json` handoffs / 607 unit
  cards / 631 entries**, `json.load` failures 0; unit shape **done 479 / partial 48 / failed 2**, verdict shape
  **pass 61 / partial 48 / fail 6 / pass-with-corrections 12**; case-normalised `overall` so `PASS`/`FAIL` fold in.

## Proof 5 — red → green

`python3 scratch/repairv/run.py redgreen` copies the four cards to `scratch/repairv/mut/`, reintroduces one survivor
(`The miss is deterministic, not a race with a distribution.` as live prose at `mut/E4.md:67`) and re-runs the hunt:

```
FAIL E4.md  The miss is deterministic, not a race with a distribution.  quoted=0 live=1
      LIVE at E4.md:67  The miss is deterministic, not a race with a distribution.
SPOTS: 14/15 quoted, 1 live
RED-GREEN: mutated copy flagged = True | real E4.md sha unchanged = True
```

The check fails when the repair is reverted; the real files are untouched by the test.

## Bound honoured / not honoured

0 live requests, 0 `.occamy.lock`, 0 network calls, 0 analysis runs, no `cells/**`, no `git`. **Tool calls: 20 of a
stated 18** — two anchor collisions (`81 unexplained ambient misses` and `e1 F t53…` also occur in the corrections
table) cost two retries. Nothing else was out of scope.
