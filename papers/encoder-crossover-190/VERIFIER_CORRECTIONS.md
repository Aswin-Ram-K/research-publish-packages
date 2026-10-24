# VERIFIER_CORRECTIONS.md — UFIX6, corrections applied from VERIFICATION_REPORT_4 (UVER4)

**Unit:** UFIX6. **Work order:** `strategy/VERIFICATION_REPORT_4.md` (verdict `pass-with-corrections`).
**Scope:** C1, C2, C3 only. `numbers_changed = 0` — **no measured value moved** (re-checked occurrence counts
against UVER4 §2 below). Nothing in §6.6, the κ-is-not-IAA framing, the withheld boundary, the dropped latency
claim, the novelty narrowing, or the declared primary baseline (0.6789) was touched.

**Target `the read-only target repository` READ ONLY:** HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`;
`git status --porcelain` before = after = the same 4 untracked paths (`?? .ci-trunk.txt`, `?? .relay/`,
`?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `?? docs/migration/`), pre-existing from the
unrelated concurrent session. No workspace unit under review wrote to the target. Only read verbs used
(`git rev-parse`, `git status`, `grep`, `sed`, `python3`).

---

## C1 — pseudo-key attributed to a file that does not contain it (FIXED, prose route)

**Defect (UVER4 §1/C1):** `harness_self_contained = partial` was cited to `repro/encoder-crossover-190/README.md`
§5, but the token occurs nowhere in the released subset; it exists only at
`orchestration/handoffs/UREPRO.json:16`. README §5's heading is prose. **Re-confirmed independently:**
`grep -rn "self_contained" repro/encoder-crossover-190/` → 0 hits; `README.md:136` =
`## 5. Is the harness genuinely self-contained? **Partial — precisely:**`.

**Fix chosen: drop the pseudo-key, state the limitation in prose** (as UVER4 preferred — a reviewer must not be
sent hunting a data field in a handoff file). The underlying limitation is unchanged and unweakened.

### C1a — `MANUSCRIPT.md` (was line 809)

**Before:**
```
`repro/encoder-crossover-190/README.md` §5 records `harness_self_contained = partial`. The six Python steps
```
**After:**
```
`repro/encoder-crossover-190/README.md` §5 states the limitation in prose (its own heading: "Is the harness
genuinely self-contained? **Partial — precisely:**"). The six Python steps
```

### C1b — `AVAILABILITY.md` (was lines 9–11)

**Before:**
```
**not fully self-contained** (`harness_self_contained = partial`): the six Python steps re-run from `harness/`
with its bundled `data/`, but steps 1–2 need the source repository's `tsx` runner and a repo-shaped checkout —
their outputs are shipped byte-identical and re-verified.
```
**After:**
```
**not fully self-contained** (`README.md` §5 heading: "Is the harness genuinely self-contained?
**Partial — precisely:**"): the six Python steps re-run from `harness/` with its bundled `data/`, but steps 1–2
need the source repository's `tsx` runner and a repo-shaped checkout — their outputs are shipped byte-identical
and re-verified.
```

**Source establishing the correct attribution:** `repro/encoder-crossover-190/README.md:136` (prose heading) and
`orchestration/handoffs/UREPRO.json:16` (`"harness_self_contained": "partial"` — the key's only origin).
**Residual-check:** `grep -c harness_self_contained` → 0 in both files. **Substance preserved:** "six Python
steps re-run; steps 1–2 need `scripts/run.sh`/`tsx` + repo-shaped checkout; outputs shipped byte-identical" —
README §5 and `harness/data/{fixture-190.json,lint-report.json}` support it fully. No number touched.

---

## C2 — count did not match its own enumeration (FIXED by adding the missing case; **true count = 14**)

**Verified from source, not assumed.** `experiments/second-labeller-190/RUN2.json`
`.disagreement_structure.shared_contested_core` lists exactly **14** ids:
`worker.class-023, context.package-004, capability.family-004, capability.family-009,
memory.admission-001, memory.admission-009, memory.admission-018, memory.admission-021,
memory.admission-027, topology-018, acquisition-007, acquisition-014, acquisition-019, acquisition-023`.
`RUN2.json` `.disagreement_structure.reading` says "*14-case shared contested core*" and names
`memory.admission-018` explicitly; `ROBUSTNESS.md:202` corroborates (`memory.admission-018 (DROP→EPISODIC)`).
**The true count is 14, so the missing case `memory.admission-018` was added** — the number was already right.
The manuscript's list previously named only 13 (4 acquisition + 1 + 2 + 1 + 1 + 4).

### C2 — `MANUSCRIPT.md` (was lines 620–625)

**Before:**
```
  is a **14-case shared contested core** — all four `acquisition` traps (`-007/-014/-019/-023`),
  `topology-018`, `capability.family-004/009`, `context.package-004`, `worker.class-023`, and the four
  `EPHEMERAL`/`DROP` cases above. The tails (12 B2-only, 4 UEXP-only) are scattered and read as
```
**After:**
```
  is a **14-case shared contested core** — all four `acquisition` traps (`-007/-014/-019/-023`),
  `topology-018`, `capability.family-004/009`, `context.package-004`, `worker.class-023`, the four
  `EPHEMERAL`/`DROP` cases above, and `memory.admission-018` (`DROP→EPISODIC`). The tails (12 B2-only,
  4 UEXP-only) are scattered and read as
```
**Enumeration now:** 4 acquisition + `topology-018` + 2 `capability.family` + `context.package-004` +
`worker.class-023` + 4 `EPHEMERAL`/`DROP` (001/009/021/027) + `memory.admission-018` = **14 = the count and
RUN2's set.** The neighbours (26 B2 / 18 UEXP disagreements, 12 B2-only / 4 UEXP-only tails, "not 26 defects")
are untouched and still correct.

---

## C3 — overstated JSON path (FIXED; values were already exact)

`reproducesAt3dp` / `absoluteDifference` sit at `.models["decider-4b-exp11-reproduction"].strata.instrument190`,
not at the model level; the **190-row** `.perCase` array *is* at the model level. Values
(`true`, `4.7368421052684795e-05`) unchanged.

### C3 — `AVAILABILITY.md` (was lines 28–30)

**Before:**
```
**Declared primary baseline.** **0.6789** — auditable from `results/baselines.json`
(`.models["decider-4b-exp11-reproduction"].perCase`, 190 rows; `reproducesAt3dp = true`,
`absoluteDifference = 4.7e−05`).
```
**After:**
```
**Declared primary baseline.** **0.6789** — auditable from `results/baselines.json`
(`.models["decider-4b-exp11-reproduction"].perCase`, 190 rows;
`.strata.instrument190.reproducesAt3dp = true`, `.strata.instrument190.absoluteDifference = 4.7e−05`).
```
**Source:** `repro/encoder-crossover-190/results/baselines.json`
`.models["decider-4b-exp11-reproduction"].strata.instrument190` = `{accuracy: 0.6789473684210526,
reproducesAt3dp: true, absoluteDifference: 4.7368421052684795e-05}`; `.perCase` = 190 rows. `0.6789` retained.

---

## U9 closure — "no total file count is claimed in the manuscript" (CONFIRMED)

UTS1 had this as UNVERIFIED item **U9**. UVER4 noted 43 files on disk vs 42 in `MANIFEST.json` (it
self-excludes) and that no total is claimed, so nothing is misstated. **Re-verified:**
`grep -nE "\b(4[0-4])\b[^\n]{0,20}file"` over `MANUSCRIPT.md` and `AVAILABILITY.md` → **no matches**; the only
`N files` claims are `18 harness files` (`MANUSCRIPT.md:820`, `AVAILABILITY.md:21,34`), which UVER4 verified
as `find repro/encoder-crossover-190/harness -type f` = 18. **`file_total_claimed_in_manuscript = no`** — U9
is **closed as a non-defect**; the manuscript was left alone on this.

---

## `numbers_changed = 0` — independent re-count after the edits

Occurrence counts in the edited `MANUSCRIPT.md`, compared with UVER4 §2 (all identical → no value moved):
`0.3474` 28→28, `0.4526` 13→13, `0.2911` 9→9, `0.6684` 22→22, `0.6789` 25→25, `0.9014` 4→4, `0.8577` 4→4,
`0.9125` 5→5, `0.1595` 3→3, `0.2316` 6→6, `0.2632` 8→8, `0.3316` 14→14, `0.3210` 10→10, `0.1053` 7→7,
`0.8837` 1→1, `0.9140` 1→1, `0.3526` 1→1, `0.3252` 2→2, `0.3421` 7→7. The only textual additions are the
**spelled-out** count words `14` (unchanged), `4 UEXP-only` (unchanged), and the new label string
`memory.admission-018` — an identifier, not a measured value.

Note 2026-10-16: this recount is the dated record of the verification as it stood then and is kept
byte-intact. The release tree's neutralisation has since moved two values in the list above: `0.3526`
(now 0.3684) and `0.3252` (now 0.3249, exact 0.3248813212427869); every other count is unchanged.

**Files edited:** `papers/encoder-crossover-190/MANUSCRIPT.md` (C1a, C2),
`papers/encoder-crossover-190/AVAILABILITY.md` (C1b, C3). No other path written.
