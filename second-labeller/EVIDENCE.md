# EVIDENCE — G46 (unit G33)

**Experiment:** a machine second-labelling pass and disagreement catalogue over the 190-case
hand-authored fixture `P05` in the read-only target
`the read-only target repository`, which four paper candidates (#3, #4, #5, #10) rest on.

**Target revision:** `the read-only target repository` @ `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`
(unchanged before and after).
**Run window:** 2026-10-15 14:20–14:36 CDT.
**Status:** `done`.

---

## ⚠ LIMITATION — read this before any number below

> **UNVERIFIED as inter-annotator agreement.** The second pass here is a **model**, not an
> independent human annotator. Agreement between a model and the fixture's hand-authored labels
> is **not** inter-annotator agreement in the sense a reviewer means, and κ below **must not** be
> reported as IAA. What this run licenses is narrower: a machine re-labelling baseline, a
> catalogue of the cases where an independent reader lands elsewhere, and mechanical checks that
> need no annotator at all. It does **not** discharge `G58` §F.3's call
> for "a second independent labeller or corpus for the 190-case fixture". A model pass cannot
> substitute for a second human. See §8.

---

## 1. Sandbox copy and hash proof (never wrote to the target)

```
$ sha256sum the read-only target repository's instrument source G46/D07.sandbox.ts
076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796  the read-only target repository's instrument source
076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796  G46/D07.sandbox.ts
$ cmp the read-only target repository's instrument source G46/D07.sandbox.ts && echo IDENTICAL
IDENTICAL
$ wc -lc D07.sandbox.ts
  2220 145031 D07.sandbox.ts
```

The sandbox copy stayed byte-identical to the target for the whole run:

```
$ cmp D07.sandbox.ts the read-only target repository's instrument source && echo SANDBOX_COPY_IDENTICAL
SANDBOX_COPY_IDENTICAL
```

`sha256` before = after = `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`.
The target fixture's mtime is still `2026-10-01 18:17:50 -0500`.

## 2. Parsing — and a parser defect this unit caught in itself (D-P1)

The file is TypeScript; records are object literals at 2-space indent with fields
`id, kind, question, options, correct, rationale, namespaces`. **`correct` is an index into
`options`**, not a label string.

```
$ python3 D01          # final run
records_found = 190      cases_parsed = 190     parse_failures = []
options_total = 721
options_per_case = {"2": 33, "3": 27, "4": 76, "5": 54}
distinct_labels = 74
answer_outside_option_set = []      bad_option_arity = []
duplicate_ids = []                  duplicate_questions_exact = {}
near_duplicate_questions = []       single_option_cases = []
```

**Parser defect D-P1 (self-caught, recorded because it nearly produced a false headline).** The
first parser used a non-greedy `options:\s*\[(.*?)\]`. Case `N10-014` has the option
string `"the EXPANDED_A ref list"`, whose `]` truncated the match, yielding `options: []` with
`correct: 0` — which the defect check then reported as **`answer ∉ option set`, the
`F-EXP11-11` defect class**. Verification against the raw text disproved it:

```
$ sed -n '567,573p' D07.sandbox.ts
    id: "N10-014",
    ...
    options: ["the EXPANDED_A ref list", "the token count alone", "the model's own account", "the manifest's mtime"],
    correct: 0,
```

`options` is bracket-matched with string-literal awareness in the final
`D01:extract_array`. The false positive is recorded rather than deleted: it is the
reason a raw-text check is load-bearing, and it is the reason the `answer ∉ option set` result
below is trustworthy.

**Independent parser validation.** The fixture header asserts an aggregate the parser does not
use: *"28 cases have G11 as the label"*. The parsed distribution gives
`G11 = 28` — an exact match, from an independent source. Options per case are 2–5, inside
the header's declared "2-8 (never more)". Parsing is deterministic (`cases.json` and
`blinded_cases.json` byte-identical on re-run).

## 3. Characterising the labels

```
cases                                   190   (header declares 190 — matches)
options_total                           721   (mean 3.79/case)
options per case  2:33  3:27  4:76  5:54
distinct labels                          74   (51 of them occur exactly once)
single-option (trivially labelable)       0
duplicate ids                             0
duplicate question text (exact)            0
near-duplicate questions (ratio >= 0.90)   0
duplicate option strings within a case     0
undeclared `kind` values                   0   (all 7 declared kinds used)
empty rationales                           0
no-namespace cases                         0
question length (chars) min 88 / median 199 / max 436
```

**The label vocabulary is not homogeneous, and this governs how agreement must be read.** Two
regimes coexist:

| Kind | n | distinct options across all its cases | regime |
|---|---|---|---|
| `K01` | 30 | 5 (2 labels used) | closed roster |
| `K04` | 22 | 4 | closed roster |
| `K07` | 28 | 5 | closed roster |
| `K03` | 26 | 5 | closed roster |
| `K02` | 30 | 33 (16 labels) | class roster |
| `K05` | 26 | 54 (15 labels) | bespoke strings |
| `N10` | 28 | 111 (28 labels — one per case) | bespoke strings |

Pooled κ over a 74-category vocabulary in which 51 categories occur once is close to
meaningless. All agreement figures below are therefore also given **stratified** (§5).

**Trivially labelable vs contested.** There are no single-option cases, but there is a trivial
F06: `K01` names its own answer in the question text (**30/30**). Across the other six
kinds only **6/160** questions contain the correct option string verbatim. So the fixture's
difficulty is not uniform by construction — as the header intends ("the set mixes easy and hard
on purpose") — but the *easy* band is identifiable and the *hard* band is 160 cases.

**`G11` availability:** offered in 56 cases (the 30 `K01` + 26 `K03`), chosen
in 28 — matching the header's "abstention is measured rather than assumed".

**ERRATA re-verified.** The header records three in-place corrections. All three check out in the
text: `N01-019` and `N09-006` now describe scope as a [redacted] boundary
mechanism ([withheld: the quoted rationale named internal file paths and an enforcement rule]), and `N09-022` uses
`kind:ref:scope`. The past labels were left visible in the rationale rather than silently
rewritten. This is a provenance positive, not a defect.

## 4. Pre-registration and the two labelling routes

`PREREGISTRATION.md` was written **before any per-case label was read** and frozen; it names the
one trailing record and the two header aggregates that structural inspection unavoidably exposed,
and fixes both routes, the metrics, the interpretation ladder, and the defect checks in advance.

- **Route A — deterministic, pre-registered** (`compare.py:route_a`): distinct-token overlap
  between each option and the question, `+0.5` for the option appearing as a substring, argmax,
  ties → lowest index.
- **Route B — blind model pass** (`labelsB.json`): a separate agent, fresh context, given
  `blinded_cases.json` — `id, kind, question, options` **only**; `correct` and `rationale` were
  stripped, because the rationale states why the recorded answer is right. The pass confirmed it
  opened no other file. A second distinct-model pass (`mimo-v2.6-flash`) was launched as a
  robustness check and was stood down when the primary pass delivered, for budget reasons; it
  returned no file, so `metrics.json` contains exactly one model pass.

## 5. Comparison

```
$ python3 compare.py
cases 190   options_total 721

Route A (deterministic lexical)   agreement 0.342105   kappa 0.325207   exact 65/190
                                  ties 120/190   zero-score cases 41/190

Route B (blind model, primary)    agreement 0.905263   kappa 0.901358   exact 172/190
                                  po 0.905263   pe 0.039584   18 disagreements

Route A vs Route B mutual agreement 0.3526
```

**Route A is a bad labeller, and the pre-registration said so before the number existed**
("A low Route A agreement is therefore **not** evidence that the recorded labels are wrong").
Route A and Route B agree with each other only 35% of the time while Route B agrees with the
record 90.5% of the time: on this fixture, lexical overlap measures the rule's weakness, not
label noise.

Stratified (post-hoc stratification, pre-registered metrics):

| Stratum | n | Route A agreement / κ | Route B agreement / κ |
|---|---|---|---|
| closed-vocabulary kinds (≤8 distinct options) | 106 | 0.264 / 0.211 | **0.896 / 0.884** |
| roster + bespoke kinds | 84 | 0.440 / 0.428 | **0.917 / 0.914** |
| `K01` | 30 | — | **1.000 / 1.000** |
| `K04` | 22 | — | 0.955 / 0.938 |
| `K02` | 30 | — | 0.933 / 0.923 |
| `N10` | 28 | — | 0.929 / 0.926 |
| `K05` | 26 | — | 0.885 / 0.872 |
| `K03` | 26 | — | 0.846 / 0.805 |
| `K07` | 28 | — | 0.786 / 0.715 |

Agreement is **high everywhere** and highest where the question names the answer. The two
lowest-scoring kinds are `K07` and `K03` — both closed rosters, i.e. the
disagreement is about *which* roster member applies, never about what the roster is.

## 6. Full disagreement catalogue (18) with adjudication

Primary = Route B. Records: `disagreements.jsonl` (one row per case, with both labels, the full
option set, the recorded rationale and the flags). Adjudication is by G33, which wrote the
pre-registration and therefore is **not** a blind judge for this step; the judgement column is a
reasoned reading, not a measurement.

Verdict codes: **REC** = recorded label clearly more defensible; **CONT** = genuinely contested,
both defensible; **GAP** = recorded label defensible only via an invariant the question does not
state; **TENSION** = recorded label in tension with its own stated rationale.

| # | id | recorded | Route B | verdict |
|---|---|---|---|---|
| 1 | `N01-018` | `none -- no path exists` | `G28 (G14, writes)` | REC — question says `F07` is false and asks which class a R05 may transition *to*; the structural answer is none. B flagged this itself as low-confidence. |
| 2 | `N01-023` | `G28 (G14, writes)` | `G16 (propose only)` | CONT — the premise ("keeps the class and adds a grant") is impossible under the fixture's own rule that grants come from `[redacted]`; B's status-quo reading is at least as defensible as the recorded reinterpretation. **Construction ambiguity.** |
| 3 | `N10-002` | `the body, on matching hash` | `the summary only` | CONT — the question's "Structural sharing is automatic" hints at content-hash reuse, but "names no part of that body" pulls the other way. |
| 4 | `N10-004` | `v2, the current head` | `v1, the candidate` | REC — the question states v2 *is* the current head for the claim; carrying the superseded pin is the tempting error. |
| 5 | `N09-004` | `model + context + tool` | `… + skill` | GAP — correct only if you know skills are not grants; the question does not state it. |
| 6 | `N09-009` | `model + context` | `model + context + tool` | CONT — the question does not distinguish "families constructed" from "families the tool plane may exercise". |
| 7 | `N09-010` | `model + context` | `model + context + tool` | **TENSION** — the recorded rationale (withheld in this sanitised release) implied a set *containing* `tool`; the recorded label omits it. Route B's answer follows the rationale. **Flagged, not asserted as a mislabel** — the intent may be "families the planner may spend". |
| 8 | `N08-001` | `G07` | `G31` | CONT — step-scoped scratch nobody re-reads: tier = named lifetime (record) vs "nothing will read it" (B). |
| 9 | `N08-008` | `G03` | `G02` | CONT — cross-run learning: "a method" vs "a persistent fact" is a convention the question does not fix. |
| 10 | `N08-009` | `G07` | `G31` | CONT — same convention as #8. |
| 11 | `N08-018` | `G31` | `G10` | CONT — verbatim model output "has nothing to recall it for" vs "it is what happened in a step". |
| 12 | `N08-021` | `G07` | `G31` | CONT — same convention as #8. |
| 13 | `N08-027` | `G07` | `G31` | CONT — same convention as #8. |
| 14 | `N02-018` | `G13(A,B)` | `G12(A,B)` | GAP — the question's own facts (disjoint paths, no dependency, both required, class R07) satisfy parallelism; the recorded answer needs "two-parent commits may only be minted by the Reducer", which the question never says. The rationale itself calls it "the hard version of the disjoint-paths trap". |
| 15 | `N06-007` | `G11` | `G19` | REC — an unorderable ref needs an authority; `G19` is the silent-judgement shortcut the rationale names. |
| 16 | `N06-014` | `G04` | `G21` | REC — B fell into exactly the "reaches for G21 by default" pattern the rationale names. |
| 17 | `N06-019` | `G11` | `G19` | REC — same shape as #15. |
| 18 | `N06-023` | `G11` | `G01` | REC — B fell into the named trap: a damaged head pointer is not a contradiction between two claims. |

**Tally: 6 REC, 9 CONT, 2 GAP, 1 TENSION.**

**The disagreements are not scattered — they cluster into four conventions**, which is the most
useful thing in the catalogue:

1. **`K07` tier boundary — 6 of 18 disagreements, 4 of them one single question**
   (does step-scoped scratch that is never re-read get `G07` or `G31`? recorded says
   `G07` four times, the blind reader says `G31` four times — a *systematic, consistent*
   difference, not noise). A second boundary, `G03` vs `G02` for cross-run
   learning, accounts for one more.
2. **`K05` family construction — 3 disagreements** (are skills families? does a
   scoped/zero-budget tool grant still emit `tool`?). The governing rule lives in the rationale,
   not in the question.
3. **`K03` escalate-vs-dispose — 4 disagreements**: three where the honest answer is
   `G11` but the tempting one is `G19`, plus the `G01` trap. This
   cluster is the fixture *working as designed* — it is catching a default-reaching classifier.
4. **`N10` reuse-by-hash — 2 disagreements**, one contested.

## 7. Defects found in the fixture (recorded, never fixed — the target is read-only)

**Mechanical defect classes (pre-registered §5): all five are empty.**

| Check | Result |
|---|---|
| `answer ∉ option set` (`correct` out of range) — the `F-EXP11-11` class | **0 / 190** |
| duplicate `id` | 0 |
| duplicate / near-duplicate `question` | 0 |
| malformed row, empty options, arity outside the declared 2–8 | 0 (all 190 parse; arity 2–5) |
| declared-vs-actual case count mismatch | none (header says 190; parser finds 190) |

This is a **related but distinct check**, not corroboration, of the corpus's own register.
`the read-only target repository's findings register:47` (F-EXP11-11) reads verbatim:

> | **F-EXP11-11** | **`answer ∉ option set` was 0.00 % at every round in both models** — the defect that partly justified the design **does not exist at baseline**, so the loop was built to repair something that was not broken. | confirmed | `answerInOptionSet` across all 4,090 decider rows and 3,590 imajev rows |

The `answer ∉ option set` class is absent here too, from an independent parser. The *specific*
defect worry the corpus already flagged is **not** present in this fixture.

**Semantic / construction items flagged (4).** These are *not* mechanical defects and are *not*
claimed as mislabels: `N09-010` (#7, label/rationale tension — the one item worth a
subject review), `N01-023` (#2, self-contradictory premise), and the two self-containment
gaps `N09-004` (#5) and `N02-018` (#14), where the recorded answer follows from
an invariant the question does not state. The header claims *"Every case ... states the facts its
answer follows from, so a reviewer can check the label against a rule without reading the rest of
the file"*; for those four cases a reviewer holding only the file still needs the rationale, and
for #5 and #14 the rationale itself names the missing rule. **The self-containment claim is
weaker than it reads, for the roster/bespoke kinds.**

**Corpus documentation defect (1, outside the fixture — an owed correction, not fixed here).**
`G56:46` records *"191 `id:` matches (190 cases + 1 container id)"*.
The count is right but the attribution is wrong: there is no container id. The one `id:` match that
is not a case id — the **first** by line order, at line 63 — is the `S02` **interface field
declaration** **[corrected by G34 per G35]**:

```
$ grep -n '^[[:space:]]*id:' D07.sandbox.ts | head -1
63:  id: string;
$ grep -c '^[[:space:]]*id:' D07.sandbox.ts
191
```

Line 63 is `  id: string;` inside the interface (2-space indent); the other 190 are record ids at
4-space indent. The fixture header's own count (190) is correct; only the corpus's explanation of
the 191st match is not.

## 8. Verdict and bound

**Result.** Against the pre-registered ladder this run lands in the **top band**: Route B
agreement **0.905** and **κ = 0.901** (≥ 0.90 / ≥ 0.85). Mechanically the fixture is clean: 0
defects across all five pre-registered classes, 190 cases, 721 options, arity 2–5, no duplicate
ids, no duplicate or near-duplicate questions, and the parser's counts independently reproduce the
header's own `G11 = 28`.

**What it licenses.** A blind reader given only the question and the option set reproduced 90.5%
of the hand-authored labels. That is genuine evidence *against* the hypothesis that the labels are
arbitrary or wholesale noise, and it *narrows* the external-validity caveat in one specific way:
the `F-EXP11-11` defect class — the one the corpus had already worried about — is measured absent
here.

**What it does not license.** All of the following would be overclaims:

- **It is not IAA.** One pass is a model. κ = 0.901 is *not* two-annotator agreement and must not
  be cited as such. `G58` §F.3 asks for "a second independent labeller or corpus
  for the 190-case fixture that underlies candidates #3, #4, #5 and #10", and records (G37,
  2026-10-14) that *"no second labeller, no external benchmark and no independent corpus was found
  anywhere outside the read-only target repository's documentation tree"*. **This run does not discharge that requirement** — it is a
  machine baseline standing where a human annotator is missing.
- **It does not establish that the labels are correct**, only that a competent reader usually
  reaches them. High agreement is also consistent with a shared reading convention that could
  still be wrong.
- **The pooled κ is weak on its own** and would be near-meaningless reported alone: 51 of 74
  labels occur once, so `pe` is tiny (0.040) and κ is dominated by `po`. The stratified figures in
  §5 are the defensible presentation.
- **The disagreement rate is not uniform noise.** It concentrates in four conventions (§6). The
  `K07` tier boundary is the largest single contributor and is the item most worth
  fixing in the fixture: a convention the questions do not state accounts for 6 of 18
  disagreements.

**Does it weaken or strengthen the external-validity caveat?** It **narrows it modestly and does
not remove it.** For a reviewer, the honest state is: the fixture is *mechanically sound* and
*reproducible by a blind machine reader at ~90%*, with a short, specific, enumerated list of
ambiguities to fix (7 items above). That is a real improvement over "one fixture, one author,
unverified" — and it is still **not** what §F.3 asked for. The answer to "is this enough for a
reviewer?" is **no**: it reduces one specific risk class and hands the subject a repair list; only
a second independent human labeller closes the caveat.

## 9. Read-only proof for `the read-only target repository` (twice, attributed)

```
before:  git -C the read-only target repository rev-parse HEAD -> 907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b
after:   git -C the read-only target repository rev-parse HEAD -> 907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b
status --porcelain (identical before and after, 4 entries):
 ?? .ci-trunk.txt
 ?? .relay/
 ?? G50
 ?? docs/migration/
fixture sha256 before == after == 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796
```

The repo is **permanently dirty from an unrelated concurrent session** (the four untracked paths
above, none of them mine). Attribution rather than counting, as required:

- `find the read-only target repository -newermt '-60 minutes'` at mid-run: **0 files**.
- `find ... -newermt '-3 hours'`: **2529** files, of which 2528 are under `G53/{IMPLMAP,
  COUPLING, AUTHFLOW,ASSUMPTIONS}` plus 1 under `docs/migration` — all modified **before this run
  began** (the sandbox copy is timestamped 14:24:57).
- The only files touched **inside** the run window (25 min) were **8 paths, every one under
  `.git/objects/`** (7 loose objects plus a `.pack`, all written at 14:28:31), i.e. object
  database / repack activity. `grep -c 'G51'` over those 8 paths: **0**.
- Residual uncertainty, stated rather than hidden: no command in this unit's transcript can write
  git objects (`git rev-parse`, `git status --porcelain`, `sha256sum`, `stat`, `find`, `sed`,
  `grep`, `ls`; everything else ran inside the workspace), and `.git/HEAD` and `.git/index` are
  timestamped 12:51:58 — before the run — so the new objects are attributed to the concurrent
  session. This is attribution by exclusion, not a direct proof of the writer's identity.
- **No tracked working-tree file changed; HEAD did not move.** The subject's repository content is
  untouched by this unit.

## 10. Artifact index (all under `G46/`)

| File | Purpose |
|---|---|
| `PREREGISTRATION.md` | frozen before labels were read: routes, metrics, ladder, defect checks, disclosures |
| `D07.sandbox.ts` | byte-identical sandbox copy (never modified) |
| `D01` | parser + pre-registered mechanical defect checks (re-runnable) |
| `compare.py` | Route A transcription + comparison, κ, stratification, `disagreements.jsonl` (re-runnable) |
| `characterise.py` | label/case characterisation |
| `cases.json` / `blinded_cases.json` | parsed cases / blind input (`correct`+`rationale` stripped) |
| `parse_summary.json` / `characterisation.json` / `metrics.json` | machine outputs, authoritative for the full 74-key label distribution |
| `labelsB.json` | Route B blind model pass |
| `disagreements.jsonl` | 18 rows, one per disagreement |
