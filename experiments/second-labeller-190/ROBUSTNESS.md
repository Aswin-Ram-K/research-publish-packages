# ROBUSTNESS — second-labeller-190, second model pass (unit UEXP2)

**Experiment:** re-run of unit UEXP's pre-registered blind Route B labelling over the 190-case
fixture `evals/fixtures/reflex-decisions.ts` (target `the read-only target repository`, READ-ONLY) with a
**different model** as the blind reader, then a three-way comparison.
**Model:** `mimo-v2.6-flash` (exact id `keyring/mimo-v2.6-flash`).
**Date:** 2026-10-15 (pass executed 2026-10-15 ~14:41–14:45 CDT / 19:41–19:45 UTC).
**Status:** `done`.
**Target revision:** `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` (HEAD unchanged before and after).

---

## ⚠ LIMITATION — travels with every number below

> **A model is not an independent human annotator.** Even the model-to-model κ = 0.9125 reported
> here is **not** inter-annotator agreement and **must never be cited as such** — not in a paper,
> not in a register, not in a footnote-only way. What this run bounds is *machine* reproducibility
> of the fixture's hand-authored labels: two different blind machine readers land on κ ≈ 0.86–0.90
> against the record and κ ≈ 0.91 against each other. That is a statement about models, not about
> people, and it does **not** discharge `PAPER_CANDIDATES.md` §F.3's call for a second independent
> human labeller. Every artifact from this unit (this file, `RUN2.json`, `labelsB2.json`,
> `disagreementsB2.jsonl`, `orchestration/handoffs/UEXP2.json`) repeats this limitation.

---

## 1. Method — identical protocol, one changed variable

- **Inputs reused, not re-derived.** The same `blinded_cases.json` (`id, kind, question, options`
  only; `correct` and `rationale` stripped) that UEXP used. The blinding was NOT re-derived.
- **Same pre-registration.** `PREREGISTRATION.md` (UEXP's, frozen) governs; Route B's verbatim
  prompt was used with the minimum necessary change (output path `labelsB.json` →
  `labelsB2.json`, because `labelsB.json` is UEXP's frozen record and must not be overwritten).
- **Blind reader:** a **fresh-context subagent** on `keyring/mimo-v2.6-flash`, instructed per the
  pre-registered prompt to read nothing but `blinded_cases.json`.

### Why UEXP2 itself did not label the cases (blinding, stated honestly)

UEXP2's own session was required by its unit card to read `EVIDENCE.md` / `RUN.json` first, which
contain the full 18-case disagreement catalogue. Labelling from that context would have been
contaminated knowledge, not a blind pass. Blindness was therefore preserved **structurally**,
exactly as UEXP designed it: the labelling was delegated to a child agent with fresh context that
was told to open no other file. UEXP2 did the comparison, never the labelling.

### Which model, and why it is a *different* model than UEXP used

`labelsB.json` does **not** record its model id (its `labeller` string is just
`"routeB-blind-model"`). The distinctness claim rests on UEXP's own contemporaneous record:
`RUN.json .notes[0]`, `orchestration/units/UEXP.md:68` and the `UEXP.json` handoff all describe
the stood-down `labelsB2.json` pass as **"a second distinct-model pass (`mimo-v2.6-flash`)"** —
i.e. UEXP itself designated `mimo-v2.6-flash` as the model *other than* the one that produced
`labelsB.json`. This run completes exactly that stood-down slot. **Ambiguity recorded, not
silently resolved:** the primary pass's model id is unrecorded anywhere; distinctness is an
assumption supported by UEXP's own note, not a proven fact.

### Deviations from the pre-registered prompt, all recorded (none touch label content)

1. **Output path** `labelsB.json` → `labelsB2.json` (protects UEXP's frozen artifact).
2. **Retry after failure:** the first labelling attempt (same prompt, same model) **hit the
   subagent's token limit before writing any file** (`labelsB2.json` confirmed absent
   afterwards). The retry used the same prompt plus one **operational** line: build the JSON with
   a short shell/python command instead of printing it. That line carries zero label information.
3. **Ambiguities the pre-registration leaves open** (recorded per the unit card's rule):
   the protocol fixes no model id for the reader, no retry rule for a failed reader run, and no
   batching rule. No batching was needed — one agent labeled all 190 cases in one pass.

## 2. Verbatim command output

```
$ python3 compare2.py
=== compare2.py summary ===
cases 190  B2 labeller-string 'routeB-blind-model'
vs_fixture                   n=190 agreement=0.863158 po=0.863158 pe=0.038366 kappa=0.857698 exact=164
vs_UEXP_labelsB              n=190 agreement=0.915789 po=0.915789 pe=0.037756 kappa=0.912485 exact=174
UEXP_vs_fixture_recomputed   n=190 agreement=0.905263 po=0.905263 pe=0.039584 kappa=0.901358 exact=-

-- stratified kappa vs fixture (B2 = this run, B = UEXP) --
acquisition        n= 26  B2 agr=0.7692 k=0.7045   UEXP agr=0.8462 k=0.8049
capability.family  n= 26  B2 agr=0.9231 k=0.9142   UEXP agr=0.8846 k=0.8717
context.package    n= 28  B2 agr=0.8929 k=0.8893   UEXP agr=0.9286 k=0.9261
escalation         n= 30  B2 agr=0.9333 k=0.8454   UEXP agr=1.0000 k=1.0000
memory.admission   n= 28  B2 agr=0.6786 k=0.5625   UEXP agr=0.7857 k=0.7153
topology           n= 22  B2 agr=0.9545 k=0.9384   UEXP agr=0.9545 k=0.9384
worker.class       n= 30  B2 agr=0.9000 k=0.8862   UEXP agr=0.9333 k=0.9226

-- arity test (agreement vs fixture) --
arity_2    n= 33  B2 agr=0.9697 k=0.9498   UEXP agr=1.0000 k=1.0000
arity_3    n= 27  B2 agr=0.8519 k=0.8405   UEXP agr=0.9259 k=0.9187
arity_4    n= 76  B2 agr=0.9211 k=0.9179   UEXP agr=0.9211 k=0.9179
arity_5    n= 54  B2 agr=0.7222 k=0.6836   UEXP agr=0.8148 k=0.7906
stratum_escalation_names_answer    n= 30  B2 agr=0.9333 k=0.8454   UEXP agr=1.0000 k=1.0000
stratum_all_other_kinds            n=160  B2 agr=0.8500 k=0.8459   UEXP agr=0.8875 k=0.8844

-- disagreement structure --
B2 disagreements 26 ; UEXP disagreements 18 ; overlap both=14 B2-only=12 UEXP-only=4 jaccard=0.4667
  memory.admission_tier_boundary   ['memory.admission-001', 'memory.admission-009', 'memory.admission-018', 'memory.admission-021', 'memory.admission-027']
  capability.family_construction   ['capability.family-004', 'capability.family-009']
  acquisition_escalate_vs_dispose  ['acquisition-007', 'acquisition-014', 'acquisition-019', 'acquisition-023']
  context.package_reuse_by_hash    ['context.package-004']
  unclustered_in_UEXP              ['topology-018', 'worker.class-023']

-- memory.admission convention test (recorded EPHEMERAL vs blind DROP) --
  memory.admission-001   recorded=EPHEMERAL  UEXP=DROP   B2=DROP    replicated=True
  memory.admission-009   recorded=EPHEMERAL  UEXP=DROP   B2=DROP    replicated=True
  memory.admission-021   recorded=EPHEMERAL  UEXP=DROP   B2=DROP    replicated=True
  memory.admission-027   recorded=EPHEMERAL  UEXP=DROP   B2=DROP    replicated=True
replicated 4/4 -> True

wrote metrics2.json and disagreementsB2.jsonl (26 rows)
```

```
$ git -C the read-only target repository rev-parse HEAD      # before AND after
907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b
$ git -C the read-only target repository status --porcelain  # identical before and after, 4 entries
?? .ci-trunk.txt
?? .relay/
?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt
?? docs/migration/
$ sha256sum the read-only target repository/evals/fixtures/reflex-decisions.ts
076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796  (matches UEXP's before/after)
$ find the read-only target repository -newermt '-45 minutes' -type f | wc -l
8      # ALL 8 under .git/objects/ (7 loose + 1 pack), mtime 2026-10-15 14:38:30 CDT,
       # i.e. ~1 minute BEFORE UEXP2's first command (~14:41 CDT); 0 under evals/
```

**Read-only proof, attributed (not merely counted).** The repo is **permanently dirty from an
unrelated concurrent session** (the four untracked paths above, none of mine; UEXP measured the
same four). The only in-window target files are 8 git-object-database paths written at
14:38:30 CDT — before UEXP2 ran a single command, and after UEXP's own run had ended (14:36) —
so they are attributed to the concurrent session, not to UEXP2. `.git/HEAD` and `.git/index` are
still timestamped 12:51:58. No tracked working-tree file changed; HEAD did not move; the fixture
sha256 is unchanged. UEXP2's only commands against the target were `git rev-parse`,
`git status --porcelain`, `find`, `stat`, `sha256sum` — none can write git objects. Residual
uncertainty, stated: attribution is by exclusion and timestamp, not a direct capture of the
writer.

## 3. The three-way comparison

| Comparison | n | agreement | κ | exact index matches |
|---|---|---|---|---|
| **B2 (mimo-v2.6-flash) vs fixture's recorded labels** | 190 | **0.8632** | **0.8577** | 164 |
| UEXP (labelsB) vs fixture — recomputed by UEXP2 (sanity check; matches `RUN.json` exactly: 0.905263 / 0.901358) | 190 | 0.9053 | 0.9014 | 172 |
| **B2 vs UEXP (model-to-model — a genuinely new quantity)** | 190 | **0.9158** | **0.9125** | 174 |

**a. Does κ ≈ 0.901 replicate? Partially.** A second, different blind model lands at
**agreement 0.863, κ = 0.858** — 4.2 pp / 4.4 pp below UEXP's reader. Against the pre-registered
ladder this is **band 2 on agreement** (0.75 ≤ agr < 0.90) but still **above the band-1 κ
threshold** (κ ≥ 0.85). The *magnitude* replicates (both readers are high-agreement); the exact
headline "0.90" does **not** — it is reader-dependent at the ±0.04 level.

**b. Model-to-model κ (new quantity): 0.9125.** The two blind readers agree with each other
*more* than either agrees with the record (0.9158 > 0.8632 and > 0.9053). Both readers make the
same systematic moves on the same cases (see §4–5): that is evidence the shared divergence
reflects the *fixture's* conventions, not one model's noise.

**c. Per-dimension stratified κ — the same dimensions are weak for both readers.**

| Kind | n | B2 agr / κ | UEXP agr / κ | weakest for both? |
|---|---|---|---|---|
| `escalation` | 30 | 0.933 / 0.845 | 1.000 / 1.000 | UEXP-perfect; B2 missed 2 of the 30 |
| `topology` | 22 | 0.955 / 0.938 | 0.955 / 0.938 | no (strong, identical) |
| `worker.class` | 30 | 0.900 / 0.886 | 0.933 / 0.923 | no |
| `context.package` | 28 | 0.893 / 0.889 | 0.929 / 0.926 | no |
| `capability.family` | 26 | 0.923 / 0.914 | 0.885 / 0.872 | no |
| `acquisition` | 26 | 0.769 / 0.705 | 0.846 / 0.805 | **yes — second-weakest for both** |
| `memory.admission` | 28 | 0.679 / **0.563** | 0.786 / 0.715 | **yes — weakest for both** |

The weak dimensions replicate direction-for-direction: `memory.admission` and `acquisition` are
the two worst kinds for **both** readers. Label soundness is **dimension-dependent**, and the
dependence is a property of the fixture, not of a model.

## 4. UEXP's systematic finding, tested directly — REPLICATED 4/4

UEXP reported: 6 of 18 disagreements are the `memory.admission` tier boundary, and 4 of those are
**one single convention** — step-scoped scratch that nobody ever re-reads: recorded `EPHEMERAL`
(4×) while the blind reader says `DROP` (4×). **The second model makes the same choice on the
same 4 cases, 4 out of 4:**

| id | recorded | UEXP | B2 (mimo) |
|---|---|---|---|
| `memory.admission-001` | `EPHEMERAL` | `DROP` | **`DROP`** |
| `memory.admission-009` | `EPHEMERAL` | `DROP` | **`DROP`** |
| `memory.admission-021` | `EPHEMERAL` | `DROP` | **`DROP`** |
| `memory.admission-027` | `EPHEMERAL` | `DROP` | **`DROP`** |

**Reported as such: this is a real, systematic ambiguity at the `memory.admission` tier
boundary** — two independent machine readers applying the same blind protocol both read
"never re-read" as `DROP`, against the record's `EPHEMERAL`. That is not annotation noise; it is
a convention the questions do not state. B2 additionally pushes the same reading one step
further than UEXP (it also says `DROP` on `-015` where UEXP sided with the record, and flips
three `EPISODIC` cases to `EPHEMERAL`), which is why `memory.admission` κ falls to 0.563 — the
whole tier is soft, and the tier boundary is the single most repair-worthy item in the fixture.

## 5. Disagreement structure compared

- B2: **26** disagreements vs fixture; UEXP: **18**. Overlap **14**; B2-only 12; UEXP-only 4
  (Jaccard 0.467).
- **The contested core replicates.** 14 of UEXP's 18 are also B2's, including *every* UEXP-cluster
  item except `capability.family-010`, `memory.admission-008`, `context.package-002`,
  `worker.class-018`: all four `acquisition` trap cases (−007/−014/−019/−023), the four
  `EPHEMERAL→DROP` cases, `memory.admission-018` (`DROP→EPISODIC`), `topology-018`
  (`SEQUENCE→PARALLEL`), `capability.family-004/009`, `context.package-004`, `worker.class-023`.
- **The tails are reader-specific.** The 12 B2-only items are scattered (`acquisition-005`,
  `acquisition-017`, `context.package-005/007`, `escalation-007/019`, `memory.admission-002/012/015/023`,
  `worker.class-003/029`) and are the plausible per-reader noise band; the 4 UEXP-only items are
  likewise scattered. A second pass therefore **adds** ~12 items to the repair catalogue rather
  than confirming UEXP's tail — the honest read is "14 shared contested + two small
  reader-specific tails", not "26 defects".

## 6. Arity test — does accuracy track option count?

| Options per case | n | B2 agreement / κ | UEXP agreement / κ |
|---|---|---|---|
| 2 | 33 | 0.970 / 0.950 | 1.000 / 1.000 |
| 3 | 27 | 0.852 / 0.841 | 0.926 / 0.919 |
| 4 | 76 | 0.921 / 0.918 | 0.921 / 0.918 |
| 5 | 54 | **0.722 / 0.684** | 0.815 / 0.791 |

**Yes, there is an arity gradient — for both readers, in the same direction.** But it is
**confounded with kind**: the 5-option cases are dominated by the closed-roster kinds
`memory.admission` and `acquisition`, which are the two hardest kinds for independent semantic
reasons (§3). Three checks against the "pure surface exploitation" reading:

1. A reader matching on option wording/position alone would show *flat or chance* agreement; both
   readers reach κ = 0.86–0.90 overall and **model-to-model κ = 0.9125** on case-by-case semantic
   choices across bespoke 4-option kinds (`context.package`, `capability.family`) where surface
   cues are weakest.
2. On the stratum where the correct answer is *named in the question* (30 `escalation` cases),
   UEXP got 30/30 but B2 got 28/30 — a surface-cue matcher would be ≥ the record here, not below.
3. Both readers fail on the *same* hard kinds, not on the same arity per se.

**Honest verdict on the test:** the arity effect is **real and must be reported** — it weakens
any blanket "the labels are sound" reading, because soundness is measurably lower in the
high-arity closed-roster strata (worst cell: 5-option cases, second reader, κ = 0.684;
`memory.admission` κ = 0.563). It does **not** look like option-wording exploitation; it looks
like genuine difficulty concentrated in roster-boundary kinds. Reported either way, as the card
requires.

## 7. Verdict, with its explicit bound

**Verdict: PARTIAL replication.**

- **Replicates:** high blind-machine agreement with the record (κ = 0.858 vs UEXP's 0.901 — both
  ≥ 0.85), the *same* weak dimensions (`memory.admission`, `acquisition`), the *same contested
  core* (14 shared disagreements), and the specific systematic finding **4/4**: both blind
  readers call never-re-read step scratch `DROP` where the record says `EPHEMERAL`. Model-to-model
  κ = 0.9125 says the two readers are measuring the same thing.
- **Does not replicate:** the exact headline "agreement ≈ 0.90" — the second reader lands 4.2 pp
  lower, and the pre-registered ladder would put this pass in band 2 (0.75–0.90) on agreement
  while band-1 on κ. `memory.admission` κ degrades to 0.563. "The fixture's labels are robust
  across models" is therefore licensed only as "**robust for 6 of 7 kinds, soft for
  `memory.admission` and degraded-but-fair for `acquisition`**" — not as a blanket claim.
- **What this licenses:** the 0.90 figure is not a quirk of one model; label quality is
  dimension-dependent and the weak dimensions are properties of the fixture; the
  `EPHEMERAL/DROP` tier boundary is a **real systematic ambiguity**, now demonstrated with two
  different blind readers, and is the top repair item.
- **What this never licenses:** **κ = 0.9125 between two models is NOT inter-annotator agreement
  and must never be cited as such.** This run bounds *machine* reproducibility of the labels for
  exactly two models on exactly one fixture. It does not discharge `PAPER_CANDIDATES.md` §F.3;
  only a second independent **human** labeller does that. A high model-model κ is also
  consistent with two models sharing a wrong convention — replication of a divergence is
  evidence of ambiguity, not proof of error in either direction.

## 8. Artifact index (all under `experiments/second-labeller-190/`, new files only)

| File | Purpose |
|---|---|
| `labelsB2.json` | second blind model pass (`mimo-v2.6-flash`), 190 labels |
| `compare2.py` | three-way comparison, κ, stratification, arity test, convention test (re-runnable) |
| `metrics2.json` | full machine output of `compare2.py` |
| `disagreementsB2.jsonl` | 26 rows, one per B2 disagreement, with both other labels + recorded rationale |
| `RUN2.json` | run record with the limitation in-band |
| `ROBUSTNESS.md` | this file |

UEXP's artifacts (`PREREGISTRATION.md`, `labelsB.json`, `metrics.json`, `disagreements.jsonl`,
`EVIDENCE.md`, `RUN.json`) were **read, never modified**. `compare.py` was deliberately **not**
re-run because it overwrites `metrics.json`/`disagreements.jsonl`, which are UEXP's record;
`compare2.py` writes only `metrics2.json`/`disagreementsB2.jsonl`. No writes to
`the read-only target repository`, `journal/`, `strategy/`, or `jobs/`.

## 9. Concurrent-session activity INSIDE the sandbox (observed, attributed, harmless to this run)

While UEXP2's labeller subagent was running, a **concurrent session** modified files in this
sandbox: `EVIDENCE.md` (14:47:33 CDT), `metrics.json` and `RUN.json` (both 14:48:12 CDT), and
added `OWED_CORRECTIONS.md` (14:57:25 CDT). None of these were UEXP2's doing — UEXP2's only
writes were `labelsB2.json` (15:09:56), `compare2.py`, `metrics2.json`, `disagreementsB2.jsonl`,
`ROBUSTNESS.md`, `RUN2.json`. Attribution is by mtime: all four concurrent changes predate
`labelsB2.json`, so no comparison in this file depends on them. Verified after the fact: the
UEXP numbers UEXP2 cites (`agreement 0.9052631578947369`, `kappa 0.9013584840356494`, route B
`exact 172/190`) are **unchanged** in the post-modification `metrics.json`/`RUN.json`/`EVIDENCE.md`,
and `labelsB.json` (14:34:02) and `disagreements.jsonl` (14:35:46) were not touched at all.
Residual uncertainty stated: the concurrent session may re-run `compare.py` later, which would
fold `labelsB2.json` into UEXP's `metrics.json` — that is the concurrent session's action, not
this run's.
