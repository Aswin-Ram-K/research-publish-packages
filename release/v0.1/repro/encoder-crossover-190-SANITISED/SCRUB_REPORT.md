# SCRUB_REPORT.md — USCRUB1: disclosure scrub of the would-be-public package

**Unit:** USCRUB1 · **Written:** this session · **Subjects:**
`repro/encoder-crossover-190-SANITISED/`, `papers/encoder-crossover-190/`, `experiments/second-labeller-190/`

**Why this exists.** An exclusion gate over the would-be-public encoder-crossover package reported
**301 hard-fail hits** in three classes: **95** audit artefacts that should not ship (curation — not this
unit), **104** fixture/dataset instrument hits (`code/fixture/**`, `code/harness/data/**`,
`eval/results/**`, `disagreements*.jsonl` — under separate test by UTOK1, **not touched**), and **~102
scrubable references — this unit's job.** All three of this unit's defects were addressed. **No measured
number moved** (§4).

---

## 0. Masking convention — this report does not reintroduce what it removed

A report about disclosure leaks must not itself ship the leaked strings. The four disclosure patterns are
therefore written here **masked**, and the report is verified clean by the same scan it reports (§2).

| id | what it is | masked form used below |
|---|---|---|
| **P1** | the target's absolute path | `<user-home>/<target-repo>` |
| **P2** | the target repository name | `<target-repo>` |
| **P3** | the private-branch commit prefix (8 hex) | `<sha8>` |
| **P4** | the source repository name | `<source-repo>` |
| **P5** | the source account / owner name | `<source-account>` |
| **P6** | this workspace's absolute path | `<user-home>/<workspace>` |
| — | a foreign home-directory prefix, and the `~` shorthand | `<foreign-home-prefix>`, `<tilde-home-prefix>` |

The literals are recoverable, exactly, from **`verify/scrub-uscrub1.py`** — its rule table reassembles
them from string fragments (`"/ho" + "me/" + …`, `"Asw" + "in" + …`) precisely so that the tool itself
ships clean. Rule-table integrity was checked by reassembling and hashing each literal (§4, step 5).

The **mechanism vocabulary** patterns (`src/broker`, `StateClass`, `grantPolicy`, `admit(`, `expanded[`)
are written literally: they are not disclosure leaks this unit was asked to remove, they were named
literally in the unit card, and they are the irreducible instrument residue UTOK1 is testing.

---

## 1. Substitution rules

Applied by `verify/scrub-uscrub1.py` (`--apply`), ordered longest-match-first. **Substitution only — no
deletion of a provenance claim, no deletion of evidence content, no re-wording of a measured number.**

| # | pattern class | replacement | why it preserves meaning |
|---|---|---|---|
| R1 | P1 + subpath | `the read-only target repository/<subpath>` | the reader still knows the data came from a read-only source, and which file inside it |
| R2 | P6 + `/` | stripped → workspace-relative path | an absolute path becomes a relative one; the referent is unchanged |
| R3 | P6 bare | `this workspace` | same referent |
| R4 | residual `<user-home>/` | stripped | same referent |
| R5 | source-repo GitHub URL, 3 shapes (incl. `.git`) | `the source repository's GitHub URL` / `… GitHub API URL` | the 404-vs-public claim survives; the private repo name and account disappear |
| R6 | source-account public-listing API URL | `the source account's public repository-listing API URL` | the "no entry in the public listing" claim survives |
| R7 | author's public companion repository URL | `the author's public companion repository` | the public artefact is still identifiable as a repository |
| R8 | P5 | `the source account` | same referent |
| R9 | P3 (full id and truncated form) | `an unmerged development branch commit (id withheld)` | the provenance fact (unmerged branch) survives; the id does not |
| R10 | second unmerged commit id | `a second unmerged commit (id withheld)` | same |
| R11 | repo-derived BibTeX key | `source_decider_stack_2026` | a **neutral key**; all four uses renamed together; nothing in the package `\cite`s the old key |
| R12 | repo-derived session name | `2026-09-28-m0` | the date survives, the name does not |
| R13 | P4, all three case forms | `the source repository` | same referent |
| R14 | P2, both case forms | `the read-only target repository` | same referent |

**Deliberately not changed** (see §6 for the reasoning and the residuals): the target's **publicly
meaningless revision identity** (`907fa39…`, `ad301ae…`) — these are the read-only proof's anchors and
removing them would *weaken a checked claim*; the experiment name `EXP#12-typed-channel-comparison`
where it names the *experiment* rather than the *branch*.

---

## 2. Per-pattern before/after counts

Method: one count per matching **line**, literal substring, case-insensitive, over the whole tree
(`grep -rIiF` for the before column, a single-pass walk for the after column). "Before" was measured on
the tree as it stood before this unit's first edit.

### 2a. Released subset `repro/encoder-crossover-190-SANITISED/`

| pattern | before | after | verdict |
|---|---|---|---|
| P1 `<user-home>` | 75 | **5** | **not zero** — all 5 are in do-not-touch files (§6.1) |
| P2 `<target-repo>` (case-insens.) | 61 | **5** | **not zero** — same 5 lines |
| P3 `<sha8>` | 0 | **0** | already zero (UREDACT1 withheld it here); it survived in the paper — §3 |
| P4 `<source-repo>` (case-insens.) | 3 | **0** | **zero** |
| `src/broker` | 6 | 6 | untouched — fixture/dataset instrument |
| `StateClass` | 108 | 108 | untouched — instrument vocabulary (UTOK1) |
| `grantPolicy` | 79 | 79 | untouched — instrument vocabulary (UTOK1) |
| `admit(` | 43 | 43 | untouched — instrument vocabulary (UTOK1) |
| `expanded[` | 8 † | 53 † | untouched — instrument vocabulary (UTOK1) |
| `<sha8b>` | 0 | **0** | zero |
| `github.com/<source-account>` | 1 | **0** | **zero** |
| `<foreign-home-prefix>` | 0 | **0** | zero |
| `<tilde-home-prefix>` | 0 | **0** | zero |
| `EXCLUDED.md` (meta-doc name) | 19 | 19 | unchanged — denotes the subset's own shipped file |
| `LICENCE_TODO.md` (meta-doc name) | 9 | 9 | unchanged — denotes the subset's own shipped file |

† The before figure for `expanded[` was measured with the shell literal `expanded\[` (escaped), i.e. a
**different literal** from the unescaped `expanded[`. Re-measured consistently the count is **53 both
before and after** — this unit's rules cannot touch mechanism vocabulary. The discrepancy is a
measurement artefact of the before run, recorded here rather than smoothed over.

The **5 remaining P1/P2 lines are the only crude target leaks left in the released subset**, and they are
exactly the do-not-touch set: `fixture/DECISION_CASE_SCHEMA.ts:2`,
`variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:2`, `harness/data/manifest.json:5,10,15`.

### 2b. Paper `papers/encoder-crossover-190/`

| pattern | before | after | verdict |
|---|---|---|---|
| P1 `<user-home>` | 41 | **0** | **zero** |
| P2 `<target-repo>` (case-insens.) | 42 | **0** | **zero** |
| P3 `<sha8>` | 9 | **0** | **zero** |
| P4 `<source-repo>` (case-insens.) | 17 | **0** | **zero** |
| `github.com/<source-account>` | 8 | **0** | **zero** |
| `EXCLUDED.md` | 7 | 6 | one pointer removed — `MANUSCRIPT.md` (§3.1) |
| `LICENCE_TODO.md` | 6 | 5 | one pointer removed — `MANUSCRIPT.md` (§3.1) |

### 2c. Second-labeller experiment tree `experiments/second-labeller-190/`

| pattern | before | after | verdict |
|---|---|---|---|
| P1 `<user-home>` | 40 | **0** | **zero** |
| P2 `<target-repo>` (case-insens.) | 38 | **0** | **zero** |
| P3 `<sha8>` | 0 | **0** | zero |
| P4 `<source-repo>` (case-insens.) | 0 | **0** | zero (but 8 source-account hits were found and removed — §5) |

### 2d. `MANUSCRIPT.md` specifically (the unit card asked for this by name)

| pattern | before | after |
|---|---|---|
| P3 `<sha8>` | 2 | **0** |
| P1 `<user-home>` | 0 | **0** |
| P2 `<target-repo>` | 0 | **0** |
| P4 `<source-repo>` | 0 | **0** |

### 2e. Patterns driven to zero vs patterns remaining (plain statement)

**Driven to zero across all three trees:** P3 `<sha8>`, P4 `<source-repo>` (all case forms),
`github.com/<source-account>`, `<foreign-home-prefix>`, `<tilde-home-prefix>`, `<sha8b>`. **Zero in the paper and the experiment tree:**
P1 and P2 as well.

**Remaining, deliberately:**
* P1/P2 **5 lines** in the released subset — `code/fixture/**` (2 files) and `code/harness/data/**`, which
  the unit card marks ⛔ DO NOT TOUCH because the vocabulary there is under separate test by UTOK1.
* The **fixture/dataset instrument vocabulary** — `src/broker` 6, `StateClass` 108, `grantPolicy` 79,
  `admit(` 43, `expanded[` 53 in the subset, plus 3/97/88/11/17 in the experiment tree. These **cannot**
  be removed without changing the instrument's own question text and therefore every reported accuracy;
  they are a bounded, irreducible residue and **will remain**.
* The meta-doc names `EXCLUDED.md` / `LICENCE_TODO.md` outside `MANUSCRIPT.md`, where they denote files
  that ship *inside* the released subset — not a private boundary.

---

## 3. Files changed

Line numbers are **pre-edit** (i.e. as the gate and the audit reported them). Rule ids refer to §1.

### 3.1 `papers/encoder-crossover-190/MANUSCRIPT.md` — defect 1, by explicit edit (not blind substitution)

| line | what was there | what is there now |
|---|---|---|
| `:754` | branch `EXP#12-typed-channel-comparison`, `<sha40>`, path `tools/typed-channel/` | *"recovered from an unmerged development branch (name and commit withheld), path `tools/typed-channel/`"* |
| `:821` (block `:819–822`) | *"closed its branch unmerged at `<sha40>` (branch `EXP#12-typed-channel-comparison`, path `tools/typed-channel/`)"* | *"closed that branch unmerged (its name and commit are withheld), at path `tools/typed-channel/`"* (now `:820–821`) |
| `:832` | *"is named in `repro/encoder-crossover-190/EXCLUDED.md`"* | *"is enumerated in the subset's accompanying exclusion inventory"* (now `:831`) |
| `:842` | *"See `repro/encoder-crossover-190/LICENCE_TODO.md`; the subset should not be published under the code default before that decision is recorded."* | *"That licence decision is recorded separately from this paper, and the subset must not be published under the code default before it is recorded."* (now `:840`) |

The paper's own licence decision (CC BY 4.0), the withheld-boundary statement, the code-licence
openness, and every number in the "what reproduces exactly" block are **unchanged**.

### 3.2 Files changed by the rule engine (33 files, 184 rule-hits)

| file | hits | rules fired (line numbers, pre-edit) |
|---|---|---|
| `papers/encoder-crossover-190/AVAILABILITY.md` | 1 | R9 `:34` (+ explicit branch-name rewrite, §3.3) |
| `papers/encoder-crossover-190/CHECKLIST.md` | 9 | R1 `:4,:66,:100,:103,:198`; R5 `:93,:94,:104`; R13 `:95` |
| `papers/encoder-crossover-190/CLAIMS.md` | 1 | R1 `:5` |
| `papers/encoder-crossover-190/DISCLOSURE_CHANGES.md` | 10 | R1 `:49,:58,:61,:70`; R4 `:135`; R9 `:96,:102,:103,:105,:107,:136` |
| `papers/encoder-crossover-190/EVIDENCE_NOTES.md` | 11 | R1 `:3,:17,:52,:79,:142,:176,:211,:226,:305,:332`; R2 `:265` |
| `papers/encoder-crossover-190/LICENSE_ANALYSIS.md` | 25 | R1 `:185,:189,:190,:191,:193,:274,:384,:432,:448,:489`; R5 `:191,:192,:193,:194,:385`; R6 `:194,:272`; R13 `:195,:272,:462,:479,:500,:522` |
| `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md` | 1 | R11 `:204` |
| `papers/encoder-crossover-190/OPEN_QUESTIONS.md` | 4 | R1 `:57,:68`; R5 `:58`; R13 `:78` |
| `papers/encoder-crossover-190/REFERENCES.bib` | 3 | R1 `:4,:64`; R11 `:63` |
| `papers/encoder-crossover-190/REFS.md` | 1 | R1 `:4` |
| `papers/encoder-crossover-190/REFS_VERIFIED.md` | 2 | R1 `:3`; R11 `:79` |
| `papers/encoder-crossover-190/UNSOURCED_RETAINED.md` | 1 | R11 `:86` |
| `papers/encoder-crossover-190/VERIFIER_CORRECTIONS.md` | 1 | R1 `:8` |
| `repro/…-SANITISED/EXCLUDED.md` | 4 | R1 `:9,:18,:45` |
| `repro/…-SANITISED/INTEGRITY.md` | 1 | R1 `:116` |
| `repro/…-SANITISED/LICENCE_TODO.md` | 1 | R13 `:13` |
| `repro/…-SANITISED/MANIFEST.json` | 21 | R1 `:8,:86,:95,:266,:275,:284,:293,:302,:311,:320,:329,:338`; R2 `:347,:356,:365,:374,:383,:392,:401,:410,:419` |
| `repro/…-SANITISED/README.md` | 1 | R13 `:153` |
| `repro/…-SANITISED/REDACTION_REPORT.md` | 7 | R1 `:5,:385,:387,:389,:448`; R7 `:518`; R13 `:548` |
| `repro/…-SANITISED/harness/collect.py` | 1 | R12 `:394` |
| `repro/…-SANITISED/preregistration/EXP12-typed-channel-comparison-prereg.md` | 1 | R1 `:2` |
| `repro/…-SANITISED/second-labeller/EVIDENCE.md` | 11 | R1 `:5,:7,:30,:31,:33,:42,:258,:333,:336,:337,:349` |
| `repro/…-SANITISED/second-labeller/OWED_CORRECTIONS.md` | 11 | R1 `:4,:22,:26,:36,:49,:60,:74,:91,:115,:120,:123` |
| `repro/…-SANITISED/second-labeller/PREREGISTRATION.md` | 3 | R1 `:10`; R2 `:90,:97` |
| `repro/…-SANITISED/second-labeller/RUN.json` | 8 | R1 `:5,:107,:143,:144,:148,:149,:150,:155` |
| `repro/…-SANITISED/verify/redaction-log.json` | 1 | R2 `:3` |
| `experiments/second-labeller-190/EVIDENCE.md` | 11 | R1 `:5,:7,:30,:31,:33,:42,:259,:334,:337,:338,:350` |
| `experiments/second-labeller-190/OWED_CORRECTIONS.md` | 11 | R1 `:4,:22,:26,:36,:51,:64,:79,:98,:123,:128,:131` |
| `experiments/second-labeller-190/PREREGISTRATION.md` | 3 | R1 `:10`; R2 `:90,:97` |
| `experiments/second-labeller-190/ROBUSTNESS.md` | 6 | R1 `:4,:112,:114,:119,:121,:279` |
| `experiments/second-labeller-190/RUN.json` | 8 | R1 `:5,:107,:143,:144,:148,:149,:150,:155` |
| `experiments/second-labeller-190/RUN2.json` | 1 | R1 `:10` |

### 3.3 Files changed by explicit, hand-checked edit (outside the rule engine)

| file | change |
|---|---|
| `papers/encoder-crossover-190/MANUSCRIPT.md` | §3.1 (4 edits) |
| `papers/encoder-crossover-190/DISCLOSURE_CHANGES.md:72` | the recorded grep evidence *"the string `<P1>` no longer occurs"* → *"the (now-scrubbed) absolute home-path prefix no longer occurs"* — the generic R4 would have produced nonsense here |
| `papers/encoder-crossover-190/DISCLOSURE_CHANGES.md:135` | the recorded grep command's pattern → `<scrubbed absolute-path prefix>` |
| `papers/encoder-crossover-190/AVAILABILITY.md:33–35` | *"the branch `EXP#12-typed-channel-comparison` closed unmerged at `<sha40>`"* → *"recovered from an unmerged development branch (name and commit withheld)"* |
| `repro/…-SANITISED/verify/run-verification.sh:23,24,31–33,168` | header echoes made tree-relative; the two read-only `git -C <P1>` lines replaced by a `TARGET_REPO` environment variable with an explanatory fallback, **so the acceptance test still runs** |
| `repro/…-SANITISED/INTEGRITY.md` | hash table re-hashed for every file this unit changed; USCRUB1 amendment note added (§4, step 6) |
| `repro/…-SANITISED/MANIFEST.json` | `sha256`/`source_sha256`/`bytes` refreshed for every entry this unit changed; `counts.bytes_total 5393492 → 5383740`, `counts.hashes_verified_identical 40 → 37` |
| `repro/…-SANITISED/verify/scrub-uscrub1.py` | **new** — the reproducible scrub tool (fragment-assembled literals) |
| `repro/…-SANITISED/SCRUB_REPORT.md` | **new** — this report |

**35 existing files changed + 2 new.** Every change is a substitution; `grep` for the pre-edit
provenance claim returns it intact, expressed neutrally.

---

## 4. Reproduction re-run — `numbers_changed: 0`

Run, on the **scrubbed** tree, from `repro/encoder-crossover-190-SANITISED/`:

```
export TARGET_REPO=<P1>                      # supplied at run time only; not written to any file
bash verify/run-verification.sh              # exit 0   -> verify/VERIFICATION.txt
python3 verify/recompute-claims.py           # exit 0   -> verify/RECOMPUTE-CLAIMS.txt
```

### (1) The digests the unit card named — **identical**

```
scoring-projection (id,kind,question,options,correct) sha256 [orig] 57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300
scoring-projection (id,kind,question,options,correct) sha256 [san ] 57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300
24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09  …/orig/harness/data/train.jsonl
24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09  …/san/harness/data/train.jsonl
d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976  …/orig/harness/data/dev.jsonl
d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976  …/san/harness/data/dev.jsonl
```

### (2) The ten `CLAIMS.md` values — **unchanged**, `ALL CLAIM NUMBERS PRESERVED: True`

```
  0.3474  modernbert-base sealed-190 accuracy        recomputed=0.3473684210526316 OK
  0.4526  majority-class control accuracy            recomputed=0.45263157894736844 OK
  0.2911  chance floor (mean 1/k)                    recomputed=0.29105263157894734 OK
  0.6684  decider-4b published baseline              QUOTED CONSTANT … OK
  0.6789  decider-4b same-run reproduction           recomputed=0.6789473684210526 OK
  0.3252  second-labeller route-A kappa              shipped=0.32520740993294694 OK
  0.8837  second-labeller closed-vocabulary kappa    shipped=0.8837023738280471  OK
  0.9140  second-labeller roster+bespoke kappa       shipped=0.9139973672663448  OK
  0.3526  second-labeller A/B mutual agreement       shipped=0.3526315789473684  OK
  counts 39+27+90+34 = 190 (OK)          fixture correctness digest 8dd05ce6…106a (unchanged)
  orig-regenerated == san-regenerated : True      san-regenerated == shipped : True
  routeB kappa 0.9013584840356494   n_disagreements 18   AB mutual agreement 0.3526315789473684
```

**`numbers_changed = 0`. The declared primary baseline `0.6789` is intact. §6.6's counter-case, the
κ-is-not-IAA framing and the withheld boundary were not touched.**

### (3) Post-run cleanliness

`verify/VERIFICATION.txt` and `verify/RECOMPUTE-CLAIMS.txt` are **regenerated logs**, and both now scan
**clean (0 hits)** for every disclosure pattern — the header echoes were made tree-relative rather than
being masked after the fact.

### (4) Rule-table integrity

Each masked literal was reassembled from the shipped fragments and hashed (lengths 8/10/11/14/19/20/24/33 —
matching P3/P4/P5/P1/R12/P1+P2/R11/P6 respectively). The tool still resolves its 23-rule table and is
idempotent (`--audit` after `--apply`: `changed_files 0, hits 0`).

### (5) Metadata self-consistency after the scrub

* `INTEGRITY.md` §1: **45/45 rows verified** against the bytes on disk (`0 stale`).
* `MANIFEST.json`: every entry for a file this unit changed was recomputed. **6 entries remain stale and
  are pre-existing / structural, not USCRUB1's** — see §5.3.
* `verify/__pycache__/` build junk created by importing the tool was removed.

---

## 5. New findings beyond the known set

### 5.1 Crude leaks the strict list missed — the actual count, and where

The known set named **4 hits in `code/harness/**`** (`manifest.json`(3), `LEAD-WIRING.md`(2),
`export-fixture.ts`, `collect.py`). Measured on the tree as delivered to this unit, the crude-leak
position was **much larger than 4 in `harness/`** — the strict list never contained P1, P2, P5 or the
workspace path, so leaks had spread well past the harness:

| where | found | status |
|---|---|---|
| `harness/collect.py:394` — session name carried P2 | 1 | **fixed** (R12) |
| `harness/data/manifest.json:5,10,15` — P1 in `path`/`report` | 3 | **NOT fixed** — do-not-touch dataset (§6.1) |
| `harness/LEAD-WIRING.md`, `harness/export-fixture.ts` | **0** | already neutralised by UREDACT1; the "2 hits" in the known set were no longer present at delivery |
| `verify/VERIFICATION.txt:3,4,168` — **P6**, the *workspace* path, in a shipped log | 3 | **fixed** (script made tree-relative, log regenerated) |
| `verify/redaction-log.json:3` — P6 | 1 | **fixed** (R2) |
| `verify/run-verification.sh:31,33` — P1, live `git -C` invocations | 2 | **fixed** (editorial, still functional) |
| `MANIFEST.json:8,86,95,266,275,284,293,302,311,320,329,338` — P1 in `source` | 12 | **fixed** (R1) |
| `MANIFEST.json:347…419` — P6 in `source` | 9 | **fixed** (R2) |
| `preregistration/EXP12-…-prereg.md:2` — P1 | 1 | **fixed** (R1) |
| `EXCLUDED.md:9,18,45`, `INTEGRITY.md:116`, `LICENCE_TODO.md:13`, `README.md:153`, `REDACTION_REPORT.md:5,385,387,389,448,518,548` | 13 | **fixed** |
| `fixture/DECISION_CASE_SCHEMA.ts:2`, `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:2` | 2 | **NOT fixed** — do-not-touch fixture (§6.1) |
| **paper** — 12 files, **75 rule-hits** across P1/P2/P3/P4/P5/`github.com/<source-account>` | 75 | **fixed** |
| **eval tree** — 6 files, **40 rule-hits** (incl. `ROBUSTNESS.md` and `RUN2.json`, not named in the known set) | 40 | **fixed** |

The gate's narrower accounting for the same two trees was *paper 27, eval 71*; this unit's wider rule set
found **75** and **40** rule-hits respectively (the gate counted fewer pattern classes per line). Both are
now **0** for every disclosure pattern.

### 5.2 Patterns searched and confirmed absent everywhere (no new leak)

`<sha8b>` — **0 hits anywhere** in the package (the known set listed it; it is not present).
`<foreign-home-prefix>`, `<tilde-home-prefix>` — **0 hits**. the source-repository name, in all three case forms — **0 hits** after the scrub.
`github.com/<source-account>` — **0 hits**. The only `<foreign-home-prefix>`-shaped match found during the scan was a
**case-insensitive false positive** on the public GitHub API URL shape `api.github.com/us…` inside the
new scrub tool's rule table; the tool's own literals were hardened so even that is gone.

### 5.3 Metadata defects found (pre-existing, not caused by this unit)

1. **`MANIFEST.json` is stale for 5 files it lists** — `fixture/DECISION_CASE_SCHEMA.ts`,
   `fixture/reflex-decisions.ts`, `harness/README.md`, `harness/data/fixture-190.json`,
   `harness/export-fixture.ts`. Their `sha256`/`bytes` predate UREDACT1's redaction and the UVER5/UVER6
   amendment, so entries asserting **`"identical_to_source": true`** are **false** for the redacted
   fixture. `MANIFEST.json` was generated by UREPRO before the redaction; it was never re-hashed.
   **Not fixed** — correcting it would rewrite claims that belong to UREDACT1's report. *For a follow-up
   unit.*
2. **`MANIFEST.json` ↔ `INTEGRITY.md` hash cycle.** `MANIFEST.json` lists `INTEGRITY.md`'s hash and
   `INTEGRITY.md` lists `MANIFEST.json`'s hash. Exactly one direction can be exact; the tree resolves it
   by making the **integrity table** authoritative (45/45 correct) and `MANIFEST.json`'s entry for
   `INTEGRITY.md` one iteration behind. Structural, pre-existing.
3. **The redaction generator cannot reproduce this scrub.** `redact.py`'s `STRICT` list still contains none
   of P1/P2/P4/P5, so re-running it would rebuild the tree *without* the disclosure scrub. Its `STRICT`
   list was extended in place to include the missed terms (assembled from fragments so the file stays
   clean), but **no path-scrub stage was added** and `redact.py` was **not re-run**. *Recorded gap: a
   UREDACT2 must fold §1's rules into `redact.py` before anyone rebuilds the subset.*
4. **The target's revision identity is still shipped** (`907fa39…` 20× in the subset, 11× in the paper,
   10× in the eval tree; `ad301ae…` 15× in the paper). These are **not** the leaked private-branch id —
   they are the read-only proof's before/after anchors, and removing them would weaken a checked claim.
   Flagged for a curation decision, not removed.
5. `.worktrees/integration` remains as a path fragment (3× `harness/data/manifest.json`, once in
   `harness/collect.py:418`, once in `second-labeller/EVIDENCE.md:350`). It names no target and no
   repository; two of the five are in do-not-touch files. Reported, not removed.

6. **The target's HEAD is moving, so HEAD-dependent evidence is no longer re-verifiable.**
   `run-verification.sh`'s read-only `git -C <P1> rev-parse HEAD` printed
   **`3c3e2cedde5910980e99519b57b920ecd8093f88`** at run time, while the rest of the package records
   **`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`** (`EXCLUDED.md:9`, `INTEGRITY.md:118,119`,
   `MANIFEST.json:9,10`, `second-labeller/EVIDENCE.md:7,336,337`, `second-labeller/RUN.json:6,118,119`).
   A second direct probe read a **third** value minutes later: the target is being **actively committed to
   by another actor**. Consequences: (a) the regenerated log's HEAD line no longer matches the recorded
   read-only proof — **this is not a scrub effect and not an experiment number**; (b) the
   "HEAD before == HEAD after == `907fa39…`" invariant can no longer be re-demonstrated against this working
   tree; (c) **nothing in the target was written by USCRUB1** — the two `git` invocations are read-only
   (`rev-parse`, `status --porcelain`), and the three untracked paths (`.ci-trunk.txt`, `.relay/`,
   `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`) are the same pre-existing ones `README.md:162`
   already records. If `git status` refreshed the target's stat-cache, that is a byte-identical index
   refresh, not a content change. **For the parent: freeze the target, or have the verifier pin a target
   revision, before any further HEAD-dependent verification.**

---

## 6. Residuals, decisions and instruction conflicts

### 6.1 The one thing defect 2 asked for that this unit did **not** do

Defect 2 named `manifest.json`(3) among the harness leaks to fix; the ⛔ DO NOT TOUCH list names
**`code/harness/data/**`** as the fixture/dataset instrument under separate test by UTOK1. The 3 named
hits **are** `harness/data/manifest.json:5,10,15` — so the two instructions contradict each other on the
same three lines. **This unit honoured the ⛔ list**, because (a) it is marked as the stronger constraint,
(b) the stated reason for it is that editing invalidates UTOK1's in-flight test, and (c) the file carries a
recorded sha256 in `INTEGRITY.md` and is regenerated by `prepare.py`, so it is instrument, not prose.
**Result: `harness_leak_fixed = 1` (collect.py); 3 hits remain and are named above for UTOK1/curation to
decide.** The same reasoning was applied to the 2 fixture/schema hits.

### 6.2 The paper-side authority gap

The unit card declares one paper write path (`MANUSCRIPT.md`, in the ⚠️ header) but the declared-write-path
list at the foot of the card says `papers/encoder-crossover-190/MANUSCRIPT.md` **only** — while **defect 3
explicitly requires** neutral substitution in `paper/**` ("27 hits across nine files", naming
`EVIDENCE_NOTES.md`, `CHECKLIST.md`, `REFERENCES.bib`, `REFS_VERIFIED.md`, `UNSOURCED_RETAINED.md`,
`OPEN_QUESTIONS.md`). **This unit edited those paper files**, because defect 3 cannot otherwise be
satisfied and because neither `UTOK1` (token-substitution test) nor `ULEAD1` (`strategy/LEAD_PACKAGE.md`)
owns anything under `papers/**`, so no write clash is possible. **Flagged for the parent to ratify or
revert.**

### 6.3 Files this unit deliberately left alone

`code/fixture/**` · `code/harness/data/**` · `eval/results/**` · `disagreements*.jsonl` ·
`repro/encoder-crossover-190/**` (the raw tree — never written) · `strategy/**` · `code/verify/**` and the
audit artefacts `EVIDENCE.md` / `OWED_CORRECTIONS.md` **for the curation decision** — note the last two
*were* path-scrubbed, because defect 3 explicitly names the second-labeller evidence's read-only proof as
in scope; only their **inclusion/exclusion from the package** is left to curation.

### 6.4 The strongest claim this unit can make

No measured number changed (`numbers_changed = 0`, §4); the ten `CLAIMS.md` values, the
`57a29b4e…` scoring-projection digest and the `train`/`dev` digests are bit-identical before and after;
every disclosure pattern the unit card named is at **zero** in the paper and the experiment tree and at
**zero in the released subset except the 5 lines inside the ⛔ do-not-touch instrument**; the
target-relative revision anchors and the whole instrument vocabulary are still there, deliberately.

*Companion tools: `verify/scrub-uscrub1.py` (`--audit` to re-measure, `--apply` to re-apply).*
