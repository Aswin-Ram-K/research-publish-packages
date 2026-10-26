# VERIFICATION_REPORT_4.md — UVER4, independent verification of UPAPER1d + UPAPER1e

**Verdict: `pass-with-corrections`.** The two units' substantive work holds: `numbers_changed = 0` is
**true for every measured value**, the disclosure fixes are real, §6.6 is clean of second-pass content, the
second-labeller figures re-derive literally from `RUN2.json`/`ROBUSTNESS.md`, and the availability claim
survives a red→green test. Two **contradicted** items are recorded below, both narrow: a misattributed quoted
key and a one-case-short enumeration. Neither changes a number or a conclusion.

**Verified revision:** `papers/encoder-crossover-190/MANUSCRIPT.md` @ 2026-10-15 15:30 (857 lines, 65,875 B).
**Authors checked:** UPAPER1d (`DISCLOSURE_CHANGES.md`, `AVAILABILITY.md`), UPAPER1e (`LIMITATIONS_UPDATE.md`).

---

## 1. Contradicted — with replacement (fix these)

### C1 (moderate) — `harness_self_contained = partial` is attributed to a source that does not contain it

**Where:** `MANUSCRIPT.md:809` and `AVAILABILITY.md:9`.

**As written:** "*`repro/encoder-crossover-190/README.md` §5 records `harness_self_contained = partial`.*"

**Why it is wrong.** The literal token `harness_self_contained` occurs **nowhere** in the released subset.
`grep -rn "self_contained\|self-contained" repro/encoder-crossover-190/` returns only **prose** — the README's
§5 heading is `## 5. Is the harness genuinely self-contained? **Partial — precisely:**` — plus unrelated
fixture prose. The key/value pair `"harness_self_contained": "partial"` exists in exactly one place:
`orchestration/handoffs/UREPRO.json:16` (and it recurs only in the two changelogs/unit cards that copied it
from there). UPAPER1d's `DISCLOSURE_CHANGES.md:14,84` names UREPRO's README §5 as the driving finding; the
identifier actually came from UREPRO's **handoff**, not its README.

**Replacement (either):**

- `MANUSCRIPT.md:809` → "*`repro/encoder-crossover-190/README.md` §5 states the harness is **only partially**
  self-contained (its own heading: "Is the harness genuinely self-contained? **Partial — precisely:**").*"
  (drop the pseudo-key); **or** keep the key and attribute it correctly: "*UREPRO's handoff records
  `harness_self_contained = partial`; `README.md` §5 spells out what is missing.*"
- `AVAILABILITY.md:9` → same treatment.

**Substance is not in doubt — only the citation.** README §5 fully supports the claim: six Python steps run
from `harness/` with bundled `data/`; steps 1–2 need the target's `scripts/run.sh` (`tsx`/node) and a
repo-shaped checkout, **neither in the subset**; their outputs are shipped byte-identical
(`harness/data/fixture-190.json`, `harness/data/lint-report.json`) and re-verified by `prepare.py`. The
manuscript's "*We do not claim full self-containment*" is **accurate and not overclaimed**.

### C2 (minor) — §6.2's shared-contested-core enumeration is one case short of its own count

**Where:** `MANUSCRIPT.md:620-625`.

**As written:** "*the overlap is a **14-case shared contested core** — all four `acquisition` traps
(`-007/-014/-019/-023`), `topology-018`, `capability.family-004/009`, `context.package-004`,
`worker.class-023`, and the four `EPHEMERAL`/`DROP` cases above.*"

**Why it is wrong.** That appositive names **13** cases (4 + 1 + 2 + 1 + 1 + 4). The source set is **14**:
`RUN2.json .disagreement_structure.shared_contested_core` lists 14 ids, and `ROBUSTNESS.md:202` names the
missing one explicitly — "`memory.admission-018` (`DROP→EPISODIC`)". The neighbours on the same lines are
right (26/18 disagreements, 12 B2-only, 4 UEXP-only: `RUN2.json .disagreement_structure`), so only the
enumeration is incomplete, not the arithmetic.

**Replacement:** insert `memory.admission-018` into the list — e.g. "*…`worker.class-023`, the four
`EPHEMERAL`/`DROP` cases above, and `memory.admission-018` (`DROP→EPISODIC`).*"

**Attribution.** C2 is inside UPAPER1e's §6.2 rewrite (LIMITATIONS_UPDATE item 16). C1 is UPAPER1d's, and it
sits **on the seam** with UPAPER1e, which quoted the same key while extending the availability bullet — see §6.

---

## 2. `numbers_changed` — was it truly 0? **Yes, for every measured value.**

Every value below is present and correct against `CLAIMS.md` and its own primary source. Occurrence counts are
in the current file; the typographic-minus value was byte-verified (`E2 88 92` = U+2212), not ASCII-found.

| value | role | occ. | verified against | verdict |
|---|---|---|---|---|
| `0.3474` | best head (§3.2/§4.1) | 28 | `CLAIMS.md:47` = 0.3473684210526316 | present, correct |
| `0.4526` | majority-class control | 13 | `CLAIMS.md:52` = 0.45263157894736844 | present, correct |
| `0.2911` | chance floor (mean 1/K) | 9 | `CLAIMS.md:51` = 0.29105263157894734 | present, correct |
| `0.6684` | secondary/published baseline | 22 | `CLAIMS.md:62` | present, correct |
| **`0.6789`** | **declared primary** | 25 | `CLAIMS.md:61`; `baselines.json .strata.instrument190.accuracy` = 0.6789473684210526 | present, correct |
| `0.9014` | reader B κ | 4 | `CLAIMS.md:106` = 0.9013584840356494 | present, correct |
| `0.8577` | reader B2 κ | 4 | `RUN2.json .kappa` = 0.8576984012674637 | present, correct |
| `0.9125` | model-to-model κ | 5 | `RUN2.json .kappa_vs_UEXP` = 0.9124852462791836 | present, correct |
| `0.1595` | paired MDE | 3 | `CLAIMS.md:69` = 0.15949356562876219 | present, correct |
| `4.167e−09` | exact McNemar p | 5 | `CLAIMS.md:67` = 4.166817880507353e-09; **U+2212 confirmed** | present, correct |
| `39 + 27 + 90 + 34 = 190` | fixture arithmetic | 1 (`:771`) | `CLAIMS.md:66` | present, correct |
| `0.2316` / `0.2632` / `0.3316` / `0.3210` / `0.1053` | controls, Δ, margin | 6/8/14/10/7 | `CLAIMS.md:50,49,63,62,53` | present, correct |
| `0.8837` / `0.9140` / `0.3526` / `0.3252` / `0.3421` | UEXP first-pass stratified/routeA | 1/1/1/2/7 | `CLAIMS.md:111,112,109,108` | present, correct |

**No value changed, moved, or disappeared.** The edits **added** B2 figures (0.8632, 0.8577, 26, 0.9158,
0.9125, 0.5625, 0.7153, 0.7045, 0.8049, 14/12/4) that are absent from the earlier changelogs — additions, not
substitutions. `0.6789` gained one occurrence over `MANUSCRIPT_CHANGES.md`'s count of 24 (B2 prose), value
unchanged.

---

## 3. §6.6 (counter-case weakness) — untouched? **No second-pass content; literal byte-identity not provable**

`MANUSCRIPT.md:693-731` contains **zero** occurrences of `B2`, `mimo`, `0.86`, `0.8577`, `0.9125`, `26/190`,
or "second pass". Its five bounded bullets match `MANUSCRIPT_CHANGES.md` C11's authoring description
item-for-item, and its quoted reviewer objection ("*…scores 0.3474 and fails to beat a majority-class control
at 0.4526, while a real ModernBERT-large reached **0.892 F1**…*") matches C11's quote.

**But literal byte-identity is `not_reproduced`:** `MANUSCRIPT.md` is untracked in the workspace repo and
**no pre-edit copy exists anywhere** (`find . -name "MANUSCRIPT*"` → `MANUSCRIPT.md` and
`MANUSCRIPT_CHANGES.md` only; no snapshot in `archive/`, `state/logs/`, or a git object). There is therefore
no baseline against which "byte-identical" could be hashed. This is a **coverage limit, not an author
failure**, and the content-level check passes.

---

## 4. Disclosure fixes — all hold

| required check | evidence | verdict |
|---|---|---|
| zero `/home/zer0null` | `grep -E "/home/zer0null\|AGPL\|returned no file\|must still make\|is a \*\*mismatch\*\*" MANUSCRIPT.md` → **no matches** | ✅ |
| zero `AGPL` | same grep; `3.0`/`v3`/`2007` parenthetical gone | ✅ |
| reproduction statements point at `repro/encoder-crossover-190/` | §7 opener `:737`; table `:743-754`; availability `:787-806` — 7 subset pointers, 0 local paths | ✅ |
| `harness_self_contained = partial` stated, **not overclaimed** | `:808-815` states partial + "We do not claim full self-containment" | ✅ substance (citation defect = C1) |
| withheld boundary stated | `:824-832` — kernel/runtime (`src/**`, `kernel/**`) not released; **no weights**; three arms named **public** checkpoints with licences; 26-file tree withheld; boundary = `EXCLUDED.md` | ✅ |
| `EXCLUDED.md` "15 exclusion classes" | `grep -o "^| E[0-9]*"` → **15** (`E1`–`E15`) | ✅ |
| harness = 18 files | `find repro/encoder-crossover-190/harness -type f` → **18** | ✅ |
| target provenance (D4) | `merge-base --is-ancestor a5ef1b28 HEAD` → **NOT-ANCESTOR**; branches containing → `EXP#12-typed-channel-comparison` (+remote); `ls-tree HEAD -- tools/typed-channel/` → **0**; on `a5ef1b28` → **42**; commit subject matches; `docs/research/EXP#12-evidence` → **26** | ✅ all confirmed read-only |
| fixture sha256 | `sha256sum repro/.../fixture/reflex-decisions.ts` → `076164ac…b4796` | ✅ |

**Subset file count — clarification, not a defect.** The released subset holds **43 files on disk**;
`MANIFEST.json` lists **42** and states it is "the only file absent from its own list" (43 = 42 + MANIFEST).
Neither `MANUSCRIPT.md` nor `AVAILABILITY.md` claims a total, so nothing is misstated. (The unit card's
"42 files" is the MANIFEST/branch-path figure; the branch `tools/typed-channel/` count is also 42.)

---

## 5. Availability accuracy — `AVAILABILITY.md` and §7 describe what is actually there

**Every path named resolves.** All 5 distinct `repro/encoder-crossover-190/...` paths referenced across
`MANUSCRIPT.md` **and** `AVAILABILITY.md` exist on disk (0 missing); the wider availability tables resolve
too — `results/eval-*.json` (5), `results/baselines.json`, `results/REPORT.md`, `results/DEFECT-EVIDENCE.json`,
`harness/data/lint-report.json`, `harness/README.md`, `harness/LEAD-WIRING.md`, `tccommon.py`, `tcmodel.py`,
`fixture/{reflex-decisions.ts,DECISION_CASE_SCHEMA.ts}`, `preregistration/EXP12-….md`,
`second-labeller/PREREGISTRATION.md`, `LICENCE_TODO.md`, `EXCLUDED.md`, `INTEGRITY.md`, `MANIFEST.json`.

**Declared primary 0.6789 is auditable from the subset — true.** `results/baselines.json`
`.models["decider-4b-exp11-reproduction"].strata.instrument190` = `{accuracy: 0.6789473684210526,
reproducesAt3dp: true, absoluteDifference: 4.7368421052684795e-05}`, and `.perCase` holds exactly **190** rows.
*Precision note (→ §7 `overstated` list):* `AVAILABILITY.md:29-30`'s parenthetical reads
"(`.models[…].perCase`, 190 rows; `reproducesAt3dp = true`, `absoluteDifference = 4.7e−05`)", which can be read
as placing those two keys at the model level; they sit one level deeper at `.strata.instrument190`. Values are
correct.

**"B2 artifacts are NOT in the released subset" — TRUE, and verified.** `repro/encoder-crossover-190/second-labeller/`
holds 9 files (`RUN.json`, `EVIDENCE.md`, `disagreements.jsonl`, `labelsB.json`, `metrics.json`, `compare.py`,
`parse_fixture.py`, `PREREGISTRATION.md`, `OWED_CORRECTIONS.md`). **All six** B2 artifacts —
`RUN2.json`, `ROBUSTNESS.md`, `labelsB2.json`, `disagreementsB2.jsonl`, `metrics2.json`, `compare2.py` — are
**ABSENT**. The §7 row (`:752`) and the availability bullet (`:803-806`) both mark the row **"not in the
released subset"** and repoint it to `experiments/second-labeller-190/`, where all six exist. A reader is
therefore warned not to expect them. ✅

---

## 6. The seam between the two units

The units touched different sections (§7/availability vs §3.4/§6.2/§7 rows), but they **interleave in the
availability block**: UPAPER1d rewrote `Data and code availability` and §7; UPAPER1e then added the B2 row
(`:752`), the reader-B marker (`:751`) and the B2 paragraph (`:803-806`) inside that same block. The result
**composes without duplication or contradiction** — reader B on `second-labeller/…` (released), B2 on
`experiments/second-labeller-190/…` (not released), and both κ figures labelled machine reproducibility. The
one shared defect is C1: UPAPER1e inherited UPAPER1d's misattributed `harness_self_contained` token when it
quoted the limitation. No other seam defect found.

---

## 7. Claim-by-claim verdicts (UPAPER1e figures re-derived literally from source)

| # | claim in `MANUSCRIPT.md` | source re-read | verdict |
|---|---|---|---|
| 1 | B2 agreement **0.8632**, κ **0.8577**, **26**/190 (`:377`, `:584-585`) | `RUN2.json .agreement_detail_vs_fixture` = 0.8631578947368421 / 0.8576984012674637 / 26; `ROBUSTNESS.md:141` | ✅ correct |
| 2 | model-to-model **0.9158**, κ **0.9125** (`:378-379`, `:586-587`) | `RUN2.json .agreement_vs_UEXP_detail` = 0.9157894736842105 / 0.9124852462791836; `ROBUSTNESS.md:143` | ✅ correct |
| 3 | `memory.admission` **B2 κ 0.5625 / UEXP 0.7153** (`:601-602`) | `RUN2.json .stratified_kappa["memory.admission"]` | ✅ correct |
| 4 | `acquisition` **B2 0.7045 / UEXP 0.8049** (`:602`) | `RUN2.json .stratified_kappa["acquisition"]` | ✅ correct |
| 5 | other five kinds stronger for both (`:603-604`) | `RUN2.json .stratified_kappa` — every one > 0.7045 (B2) and > 0.8049 (UEXP) | ✅ correct |
| 6 | arity **0.970→0.722** (n = 33/54) and **1.000→0.815**, κ **0.950→0.684** / **1.000→0.791** (`:612-614`) | `RUN2.json .arity_detail` (0.9697/0.7222; 1.0/0.8148; 0.9498/0.6836; 1.0/0.7906) | ✅ correct |
| 7 | escalation stratum **30/30 (UEXP), 28/30 (B2)** (`:617`) | `RUN2.json .arity_effect`; `ROBUSTNESS.md:228-229` | ✅ correct |
| 8 | **4/4** replicated `EPHEMERAL`→`DROP` on `-001/-009/-021/-027` (`:607-611`) | `RUN2.json .memory_admission_convention_detail` | ✅ correct |
| 9 | shared contested core **14**, tails **12 / 4** (`:620-624`) | `RUN2.json .disagreement_structure` (14 / 12 / 4) | ✅ counts correct; **enumeration short by one (C2)** |
| 10 | **4.2 pp / 4.4 pp** degradation; band 2 on agreement, band 1 on κ (`:588-590`) | `ROBUSTNESS.md §3a,§7`; `RUN2.json .replication_detail` | ✅ correct |
| 11 | B2 *met κ threshold but not agreement*, at **0.863/0.858** (`:634-636`) | `RUN2.json .replication_detail` | ✅ correct |
| 12 | κ **0.9125 between two models is still not IAA and must never be cited as such** (`:640-641`) | `RUN2.json .limitation`; `ROBUSTNESS.md:257-262` | ✅ present, correct |
| 13 | §F.3 **not** discharged; second independent **human** labeller owed (`:638-645`) | `RUN2.json .limitation`; `PAPER_CANDIDATES.md §F.3` | ✅ present, correct |
| 14 | second pass is a **partial** replication, never "confirmed" (`:55-56`, `:107`, `:378`, `:590`) | `RUN2.json .replication = "partial"` | ✅ correct — `grep confirm` hits only the GLiClass bullet |
| 15 | §3.4's "*returned no file*" claim removed (`:376-382`) | `grep "returned no file\|was launched\|stood"` → **no matches**; replaced by the two-reader bullet | ✅ corrected, no stale survivor |
| 16 | §6.2 heading no longer names 0.9014 alone (`:581`) | file `:581` | ✅ correct |
| 17 | `EXCLUDED.md` = **15** classes; 26-file tree withheld | `EXCLUDED.md` E1–E15; `ls docs/research/EXP#12-evidence` = 26 | ✅ correct |
| 18 | B2 artifacts **not** in released subset | directory listings, 6/6 absent | ✅ true |

**`DISCLOSURE_CHANGES.md` spot-check (8 entries, ≥6 required):** D1 — the AGPL/mismatch sentence is gone and
the CC BY 4.0 replacement is at `:783-785` ✅. D2(a) — §7 opener now the released subset, `:737` ✅. D2(b) —
availability bullet list `:791-806` ✅. D2(c) — "The source repository was treated as strictly read-only",
`:774`, frozen HEAD kept ✅. D2(d) — table repointed, `:743-754` ✅. D4 — provenance row + paragraph,
`:753`, `:817-822`, independently re-verified against the target ✅. D5 — withheld boundary, `:824-832` ✅.
D6 — separate undecided code licence `:834-841` ✅. **D3 is where C1 lives**: "before" text matches what was
deleted, "after" text matches `:808-815`, but the quoted `harness_self_contained = partial` is not in the
README it cites.

---

## 8. The four lists

### `contradicted`
1. **C1 — `harness_self_contained = partial` attributed to `repro/encoder-crossover-190/README.md` §5.**
   The token occurs nowhere in the subset; README §5 states partiality in prose ("**Partial — precisely:**"),
   and the key lives only in `orchestration/handoffs/UREPRO.json:16`. Occurrences: `MANUSCRIPT.md:809`,
   `AVAILABILITY.md:9`. **Replacement:** drop the pseudo-key or attribute it to UREPRO's handoff. Substance
   (partial self-containment) is fully supported.
2. **C2 — §6.2's 14-case shared contested core enumerates only 13.** `memory.admission-018` omitted
   (`MANUSCRIPT.md:620-625`). **Replacement:** add `memory.admission-018` (`DROP→EPISODIC`), per
   `RUN2.json .disagreement_structure.shared_contested_core` and `ROBUSTNESS.md:202`.

### `overstated`
1. `AVAILABILITY.md:29-30` — the parenthetical implies `reproducesAt3dp` and `absoluteDifference` sit at
   `.models["decider-4b-exp11-reproduction"]`; they sit at `.models[…].strata.instrument190`. The **values**
   (`true`, `4.7368421052684795e-05`) and the **190-row** `.perCase` count are exact, so this is a path
   imprecision, not an inflated claim. Suggested tightening: name `.strata.instrument190` for the two keys.

*(No other overstated item found: "not fully self-contained" is weaker than the evidence, κ figures are never
promoted to IAA, and the second pass is never called a confirmation.)*

### `not_reproduced`
1. **Literal byte-identity of §6.6.** No pre-edit copy of `MANUSCRIPT.md` exists (untracked; no snapshot), so
   "byte-identical" cannot be hashed. Content-level check passes: `:693-731` carries no second-pass token and
   matches `MANUSCRIPT_CHANGES.md` C11 item-for-item. *Coverage limit.*
2. **The changelogs' literal "before" strings.** Both `*_CHANGES.md` files claim `numbers_changed = 0` and
   `sentences_changed = 20` / "prose sentences changed = 11". Each "after" string is confirmed present and
   each driving number reconfirmed, but the **pre-edit bytes are taken on the changelogs' word** — no baseline
   to diff. *Coverage limit; the numbers audit is fully independent and passes.*
3. **Recount of `sentences_changed = 20`.** The definition ("one row per sentence/bullet/heading/list-row
   edit") is stated but not machine-checkable without the before-state. *Coverage limit.*

### `unverified`
1. **Attribution of target-repo dirtiness.** HEAD before = after = `907fa39…` and `status --porcelain` is the
   same 4 untracked paths, but that the 8 in-window `.git/objects/` writes belong to the unrelated concurrent
   session is by exclusion/timestamp, not direct capture — as `RUN2.json`/`ROBUSTNESS.md §9` themselves state.
   Nothing in the two units under review made those writes; no write path of either unit touches the target.
2. **Novelty/priority boundary wording** (§2.1 "no priority for the direction") is a judgement call against a
   non-peer-reviewed blog post, outside this card's evidence scope. Recorded, not adjudicated.

---

## 9. RED → GREEN — reverting the disclosure fix breaks the claim it supports

Run on **copies only** in `/tmp/uver4/` (`green.md` = verbatim copy; `red.md` = `s/repro\/encoder-crossover-190\//\/home\/zer0null\/Duval\//g`
plus the §7 opener restored to "the target repository"). **`MANUSCRIPT.md` was never modified.**

**RED — the fix reverted:**
```
home/zer0null occurrences: 7
repro/ pointer occurrences: 0
§7 opener: "Everything in this paper is re-derivable from the target repository
            `/home/zer0null/Duval/` — the 190-case fixture and its schema, …"
```
The availability claim is now anchored to the **author's own home directory behind a private, read-only
repo**, with **no pointer to any released artifact** (0 `repro/` pointers). A reviewer cannot reach that root:
it is not shippable, not part of the subset, and the paper's `Everything … is re-derivable` statement becomes
an **unverifiable availability claim**. The disclosure guard also fails on its own terms (7 local-path
exposures). → **claim broken.**

**GREEN — the fix restored (the real file):**
```
home/zer0null occurrences: 0
repro/ pointer occurrences: 7
§7 opener: "Everything in this paper is re-derivable from the released reproducibility subset
            `repro/encoder-crossover-190/` — …"
subset paths referenced across MANUSCRIPT.md + AVAILABILITY.md: 5 distinct; missing: 0
```
→ **claim holds**, and every named artifact is present in the released subset. The guard is live in both
directions.

---

## 10. Containment

- **Target `/home/zer0null/Duval`: READ ONLY.** HEAD **before = after =**
  `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; `git status --porcelain` **before = after** = the same 4
  untracked paths (`?? .ci-trunk.txt`, `?? .relay/`, `?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`,
  `?? docs/migration/`) — pre-existing, attributed to the unrelated concurrent session, **not** to UVER4 or to
  either unit checked. `.worktrees/` bulk-timestamped checkouts are that session's, not this workspace's. No
  git state change, no writes, no hooks. UVER4 issued only read commands (`git rev-parse`, `git status`,
  `git merge-base`, `git branch`, `git ls-tree`, `git log`, `ls`, `sha256sum`).
- **Workspace HEAD:** `41ad35b68bcee486a67c434afbc84b0724d9f5b4`; `git status --porcelain` = **102** entries
  before and after (the repo is permanently dirty from concurrent sessions; `MANUSCRIPT.md` is untracked, so
  there is no diff baseline — the changelogs were used as the before/after record, edit by edit).
- **UVER4 wrote only:** `strategy/VERIFICATION_REPORT_4.md`, `orchestration/units/UVER4.md`,
  `orchestration/handoffs/UVER4.json`, plus scratch copies under `/tmp/uver4/`. The manuscript was **not**
  rewritten.
- **Tool calls:** 29 used of a bound of 50.

---

## 11. What would change my verdict

- **To `fail`:** any headline value found changed or missing (none); the availability claim shown to name an
  artifact absent from `repro/` (0 missing); §6.6 found carrying a second-pass figure or absent (it is
  present and clean).
- **C1 → non-blocking** if the intent is to quote UREPRO's handoff key and the README citation is reworded;
  **C1 → blocking** only if the README is being represented as containing a token a reviewer will fail to
  find, which is the case as written for a verbatim quote.
- **C2 → resolved** by adding `memory.admission-018`; it does not affect any count or conclusion.
- **A pre-edit copy of `MANUSCRIPT.md`** (git object, `state/logs/` snapshot, or an archived draft) would
  convert the §6.6 and `sentences_changed` items from `not_reproduced` to directly checkable, and could
  surface substitutions this pass could only bound by value-presence.
- **A published-home-path or `AGPL` string reappearing** in any later edit would re-break the RED case in §9.
- **Independent human labelling** would discharge §F.3; until then, any sentence promoting κ = 0.9125 to
  inter-annotator agreement must be treated as a contradiction of the record.
