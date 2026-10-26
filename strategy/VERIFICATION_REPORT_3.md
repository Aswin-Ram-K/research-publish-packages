# VERIFICATION REPORT 3 — independent re-run of `second-labeller-190` (unit UEXP)

**Verifier:** UVER3 (not the author of any artifact under check).
**Subject:** `experiments/second-labeller-190/` — UEXP's blind second-labelling experiment over the
190-case fixture `evals/fixtures/reflex-decisions.ts` in the read-only target `/home/zer0null/Duval`.
**Date of this verification:** 2026-10-15 14:39–14:45 CDT. **Tool calls used:** 21 of a 55 bound.
**Verdict: `pass-with-corrections`.**

No claim in the subject is **contradicted** — every number and every flagged item I could re-derive
came back identical. Three claims are **overstated** (two substantive, one a wording slip) and two
observations are **not reproducible** from my run. All of them are corrections of *wording or
completeness*, not of measurement.

## Called out at the top (no `contradicted` item; these are the corrections I most want acted on)

> **C1. `RUN.json:104` and `EVIDENCE.md:258` — "independently corroborating".** The 0/190 result is
> **true and verified**, but it does **not** corroborate `FINDINGS_REGISTER.md:47`. Different
> referents: the register measured `answerInOptionSet` over **model-emitted answers** in EXP#11 runs
> (4,090 decider + 3,590 imajev rows, `FINDINGS_REGISTER.md:47`), whereas UEXP measured whether the
> **fixture's own authored `correct` index** lies inside its own `options` array. Both are 0, but one
> is a property of a model's output and the other of a human author's fixture. **Replacement wording:**
> "the same defect class is separately measured absent from the fixture's authored labels (0/190);
> this is an additional, independent measurement, not corroboration of the model-run register entry."
>
> **C2. `metrics.json:22–25` carries `kappa: 0.9013584840356494` with no limitation.** UEXP's own
> frozen rule (`PREREGISTRATION.md:12–16`) says *"Every artifact this unit writes must carry this
> limitation in the `UNVERIFIED` register; a bare 'kappa = X' presented as IAA would be an overclaim
> and is forbidden here."* `EVIDENCE.md` (§0, §8) and `RUN.json:124` carry it; **`metrics.json` — the
> machine-readable artifact a downstream consumer is most likely to grep — does not.** The value is
> correct; the qualifier the author required is missing from the one artifact that carries the number
> bare. Add a `limitation` key to `metrics.json`.

Minor, non-blocking: `EVIDENCE.md:278` says *"The 191st match is the `DecisionCase` interface field
declaration"* and then demonstrates it with `grep … | head -1` → `63:  id: string;`. Line 63 is the
**first** `id:` match by line order, not the 191st. The correct statement is "the one `id:` match that
is not a case id, at line 63". The substance of the owed correction is unaffected.

---

## What I did (method, and its independence from UEXP's code)

1. Re-hashed and byte-compared the target fixture myself; re-read target HEAD, porcelain, reflog.
2. Copied the whole experiment directory to `/tmp/uver3b/exp`, re-ran `parse_fixture.py`,
   `characterise.py`, `compare.py` there, and diffed the six regenerated artifacts against UEXP's
   originals — so **UEXP's artifacts were never rewritten** by this verification.
3. Wrote my **own** independent parser of the raw fixture text, deliberately not UEXP's method:
   locate `  {`…`  },` blocks, convert each TypeScript object literal to JSON by quoting keys and
   dropping trailing commas, then `json.loads`. This has **no bracket-matching regex at all**, so it
   is immune to the D-P1 failure mode by construction. I also cross-checked its 190 records
   field-for-field against UEXP's `cases.json`.
4. Reproduced the D-P1 defect by running the naive non-greedy regex `options:\s*\[(.*?)\]` over all
   190 blocks and counting the false `answer ∉ option set` hits it produces.
5. Recomputed pooled and per-kind agreement/κ from `labelsB.json` and my own reading of the fixture
   labels, with the standard `po`/`pe` formula and no shared code with `compare.py`.
6. Opened each of the four flagged fixture cases and the owed documentation correction in the raw
   target/corpus text.

## Claim-by-claim

| # | Claim | Artifact + line | What I measured | Classification |
|---|---|---|---|---|
| 1 | `fixture_sha256` before = after = sandbox = `076164ac…4796`; sandbox byte-identical to target | `RUN.json:8–10`; `EVIDENCE.md:29–46` | `sha256sum` target = `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`; sandbox identical; `cmp` → IDENTICAL; target mode/size 145,031 B | **verified** |
| 1b | Target fixture not modified | `EVIDENCE.md:47` | Target fixture mtime still `2026-10-01 18:17:50 -0500` (12 days before the run); `git status --porcelain -- evals/fixtures/reflex-decisions.ts` empty; last commit touching it `b015b719…` | **verified** |
| 2 | Parser yields 190 cases / 721 options / arity 2–5 | `RUN.json:12–14`; `EVIDENCE.md:56–59` | Re-ran parser in a `/tmp` copy: `cases_parsed=190`, `options_total=721`, `options_per_case={2:33,3:27,4:76,5:54}`, `parse_failures=[]`; my independent parser gives the identical `{2:33,3:27,4:76,5:54}` | **verified** |
| 2b | Parser's ESCALATE = 28 matches the fixture header's own claim | `RUN.json:26,111`; `EVIDENCE.md:86–89`; `parse_summary.json:14` | Header line 48 of the fixture states "28 cases have ESCALATE as the label". Parser `distribution` ESCALATE = 28; my independent parse = 28; distribution sums to 190. `parse_fixture.py` never reads the header (it parses per-record `correct` → option string), so **the regression is not fitted to the header** | **verified** |
| 2c | Parsing deterministic; re-run reproduces artifacts byte-for-byte | `RUN.json:113` | `cases.json`, `blinded_cases.json`, `parse_summary.json`, `metrics.json`, `characterisation.json`, `disagreements.jsonl` — **all six byte-identical** to UEXP's originals after re-running the three scripts in a copy | **verified** |
| 3 | D-P1 is documented and recorded, not deleted | `RUN.json:107–112`; `EVIDENCE.md:66–83`; `parse_fixture.py:47–51` | Present in all three, with the mechanism named and the case id (`context.package-014`) | **verified** |
| 3b | The non-greedy regex really truncates there | `EVIDENCE.md:66–78` | I ran the naive regex over all 190 blocks: it produces exactly **one** false `answer ∉ option set` — `context.package-014`. Cause confirmed: its option string is `"the expanded[] ref list"`, whose `]` closes the match | **verified** |
| 3c | The final 0/190 is **not** an artifact of that same regex | `EVIDENCE.md:80–83,252` | My independent parser (JSON-transform, **no bracket regex**) yields 0/190, and agrees with `cases.json` on `id`/`kind`/`correct`/`options` for all 190 records | **verified** |
| 4 | 0 cases with answer outside its own option set; 0 duplicate ids; 0 malformed rows | `RUN.json:61–68`; `EVIDENCE.md:250–256` | Independently re-derived from raw text: `answer_outside_set=[]`, `duplicate_ids=[]`, `malformed_rows=0`, `arity_outside_2_8=[]`, 190/190 parsed, duplicate questions 0, near-duplicates (ratio ≥ 0.90) 0, 74 distinct labels / 51 singletons | **verified** |
| 4b | This "independently corroborates" `FINDINGS_REGISTER.md:47` (`F-EXP11-11`) | `RUN.json:103–105`; `EVIDENCE.md:258–264` | Register line 47 is exactly the quoted row and its evidence column is `answerInOptionSet` across **4,090 decider + 3,590 imajev rows** — a property of **model-emitted answers in EXP#11**. UEXP's 0/190 is a property of the **fixture's authored `correct` fields**. Same defect-class *name*, different measured object | **overstated** (see C1) |
| 5 | Agreement 0.905263 / κ 0.901358 / 172 of 190 | `RUN.json:30–39`; `metrics.json:22–25` | Recomputed from `labelsB.json` + my own fixture labels: `po=0.905263157894737`, `pe=0.039584487534626`, `κ=0.901358484035649`, exact 172/190 — matches to 1e-15. `pe` is the standard product-of-marginals term (`compare.py:44`), which I re-implemented independently | **verified** |
| 5b | Stratified κ (post-hoc): escalation 1.000, topology 0.955/κ 0.938, worker.class 0.933/κ 0.923, context.package 0.929/κ 0.926, capability.family 0.885/κ 0.872, acquisition 0.846/κ 0.805, memory.admission 0.786/κ 0.715 | `RUN.json:57–64`; `EVIDENCE.md:182–190` | Recomputed **all seven** from scratch, not just three — every agreement and κ matched to 1e-6, incl. escalation pe=0.608889. Kind counts 30/22/30/28/26/26/28 = 190 | **verified** (7 of 7, exceeds the required 3) |
| 5c | Pooled κ caveat: 51 of 74 labels occur once, `pe=0.040` | `RUN.json:65–66,124`; `EVIDENCE.md:317–319` | 74 distinct labels, 51 with count 1 — confirmed exactly | **verified** |
| 6 | §6 adjudication is unblinded judgement, disclosed as such | `EVIDENCE.md:196–228` | `EVIDENCE.md:199–201`: *"Adjudication is by UEXP, which wrote the pre-registration and therefore is **not** a blind judge for this step; the judgement column is a reasoned reading, not a measurement."* See ruling below | **verified** — no artifact presents it as measurement |
| 7 | HEAD unchanged `907fa39…`; porcelain identical; attribution by exclusion | `RUN.json:114–123`; `EVIDENCE.md:333–362` | HEAD now `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; porcelain = the same 4 untracked entries; `.git/logs/HEAD` shows no HEAD move since the 12:51:58 checkout (stronger than a before/after pair). UEXP's own sentence *"This is attribution by exclusion, not a direct proof of the writer's identity"* (`EVIDENCE.md:360`) is correct and I endorse it — **attribution by exclusion cannot identify the writer** | **verified** |
| 7b | The only in-window writes were 8 paths, all under `.git/objects/` (7 loose + 1 pack), **written 14:28:31** | `RUN.json:120`; `EVIDENCE.md:353–355` | The **shape reproduces exactly**: 8 files, all under `.git/objects/`, 7 loose + 1 existing-name pack, 0 under `evals/fixtures`, 0 tracked files, 0 under `.worktrees/`. The **timestamp does not**: I find the batch at **14:38:30**, not 14:28:31 — i.e. *after* UEXP's declared 14:20–14:36 window | **not_reproduced** (see below) |
| 8a | `capability.family-010` label in tension with its own rationale | `RUN.json:76`; `EVIDENCE.md:215,267` | Opened the raw case: label = `model + context` (`correct: 0`); rationale = *"a class with declared tools still constructs its tool grants"* → implies a set containing `tool`. Tension is real and correctly flagged as a flag, not a mislabel | **verified** |
| 8b | `worker.class-023` self-contradictory premise | `RUN.json:77`; `EVIDENCE.md:210` | Opened: question says the transition *"keeps the class and adds an fs.write grant to it"*, while the fixture's own rule (stated in this case's rationale, and at fixture lines 80–105) is that the grant set is constructed from `grantPolicy`, so no transition can widen a role in place. Premise is impossible as written; option 2 (`reasoner with an added grant`) is offered as a distractor | **verified** |
| 8c | `capability.family-004` self-containment gap | `RUN.json:78`; `EVIDENCE.md:213,268–274` | Opened: recorded `model + context + tool`; the answer requires knowing a skill is not a grant *unless the policy emits one*, a rule the question does not state. Gap real | **verified** |
| 8d | `topology-018` self-containment gap | `RUN.json:78`; `EVIDENCE.md:222,268–274` | Opened: recorded `SEQUENCE(A,B)`; question states disjoint paths, no dependency, both required, class attached — all of which satisfy `PARALLEL(A,B)`. The recorded answer needs *"two-parent commits may only be minted by the Reducer"*, which the question never states and only the rationale supplies | **verified** |
| 8e | Owed correction: `strategy/PUBLICATION_STRATEGY.md:46` says "191 `id:` matches (190 cases + 1 container id)"; there is no container id — the extra match is the `DecisionCase` interface field at line 63 | `RUN.json:79–82`; `EVIDENCE.md:276–290` | Line 46 verified verbatim; `grep -c '^[[:space:]]*id:'` = 191; first match line 63 = `  id: string;` inside `export interface DecisionCase {` (line 62); the other 190 are record ids at 4-space indent; no `id:` occurs before line 63. Count right, attribution wrong — the correction is **valid and owed**. (Also note line 404, `S28`, repeats the 191 count *without* the wrong attribution, so only line 46 needs the edit.) | **verified** (substance), wording slip on "191st" |
| 9 | The limitation ("a model is not an independent human annotator; κ is **not** IAA") | `EVIDENCE.md:14–23,306–313`; `RUN.json:124`; `PREREGISTRATION.md:12–16` | Present and prominent in those three. **Absent from `metrics.json`** (the artifact that carries κ), and from `labelsB.json` / `disagreements.jsonl` (neither carries the number). `compare.py` prints it with no caveat, and UEXP's rule binds written artifacts | **overstated** (see C2) |

## The four lists, explicitly separated

**`contradicted` — none.** I found no claim in `RUN.json`, `EVIDENCE.md`, `metrics.json`,
`parse_summary.json`, `characterisation.json`, `disagreements.jsonl`, or the three scripts that my
measurements falsify. Every number I could re-derive came back identical.

**`overstated` — 3**
1. `RUN.json:104` / `EVIDENCE.md:258` — "independently corroborating the corpus's own register":
   different referents (fixture authoring vs model answers during EXP#11). Downgrade to "a separate,
   independent measurement of the same-named defect class". *(replacement wording given in C1)*
2. `metrics.json:22–25` — κ 0.9014 carried with no limitation, contrary to `PREREGISTRATION.md:12–16`.
   Add the limitation key. *(C2)*
3. `EVIDENCE.md:278` — "The 191st match": line 63 is the **first** `id:` match by line order (the one
   non-case match). Say "the one `id:` match that is not a case id, at line 63". *(cosmetic)*

**`not_reproduced` — 2** (coverage limits, not author failures)
1. `RUN.json:120` / `EVIDENCE.md:354` — the **14:28:31** timestamp on the 8 `.git/objects/` writes. I
   reproduce the set (8 paths, 7 loose + 1 pack, all under `.git/objects/`, none under
   `evals/fixtures`), but at **14:38:30**. Two explanations remain open and I cannot separate them
   from disk state alone: (a) the observation was taken at a different moment than reported, or
   (b) a concurrent process rewrote the same paths after UEXP's observation (plausible — the pack
   `pack-5eb3f8d7….pack` carries a 14:38:30 mtime while its `.idx` is from 2026-10-12 20:49, and
   `.git/index`/`.git/HEAD` still sit at 12:51:58, untouched even by my own `git status`). Either
   way the *content* claim survives: no tracked file and no fixture file was touched.
2. The `_before` half of the read-only proof (`fixture_sha256_before`, `target_head_before`,
   `git_status_porcelain_before`) is not re-observable after the fact. I verified the *after* side
   plus the independent corroborators (fixture mtime 12 days old, `.git/logs/HEAD` showing no move
   since 12:51:58, last fixture commit `b015b719…`).

**`unverified` — 2**
1. **Route B's blindness.** `labelsB.json` exists and is complete (190 ids, all in range, no extras),
   and the blinded input genuinely strips `correct` and `rationale` (`blinded_cases.json` has only
   `id`/`kind`/`question`/`options`). But the pass's own report that it "opened no other file" is a
   self-report from a session I did not observe, and no transcript is in the artifact set. The
   *result* is checkable; the *blindness* is not.
2. The stood-down second model pass (`mimo-v2.6-flash`) returned no file (`RUN.json:126–128`), so
   there is nothing to check; `metrics.json` contains exactly one pass, which I confirmed
   (`passes` has one key).

## Ruling on §6 (the 18-case adjudication)

UEXP's adjudication **is** unblinded judgement — it was made by the unit that wrote the
pre-registration, with the recorded label, the recorded rationale, and the blind label all in front
of it. The question the card asks is whether any artifact presents it as measurement. **It does
not.**
- `EVIDENCE.md:199–201` states the disqualification in the plainest terms and labels the judgement
  column *"a reasoned reading, not a measurement."*
- The verdicts are confined to `EVIDENCE.md` §6. The machine artifacts are clean: `metrics.json`
  contains **no** adjudication field at all (keys: `cases`, `options_total`, `routeA`, `passes`,
  `stratification`, `routeB_primary`, `disagreements_count_routeB`, `disagreement_kinds`,
  `disagreements_where_routeA_backs_record`), and `disagreements.jsonl` rows carry no verdict code —
  they are evidence rows (`id`, both indices/labels, options, rationale, line). The only judgement
  codes outside §6 are the four bare counts at `RUN.json:71–75`, which sum to 18 and match §6's tally.
- Residual, non-blocking: `RUN.json:71–75` `disagreement_tally` carries those counts with no adjacent
  caveat, while the sibling `disagreement_clusters` key does carry a `_note`. A machine reader that
  greps only `RUN.json` could read the tally as measured classification. One `_note` line there
  would close the gap; I do **not** count this as presenting judgement as measurement, because §6 of
  the companion artifact and `RUN.json`'s own `limitation` key both deny it.

This is the distinction the corpus itself enforces, and UEXP enforced it against itself. **Pass on
claim 6.**

## Limitation coverage (explicit, as required)

| Artifact | Carries κ/agreement? | Carries the "not IAA / model ≠ human annotator" limitation? |
|---|---|---|
| `EVIDENCE.md` | yes (`:166`, `:295`) | **yes** (`:14–23` LIMITATION block, `:306–313`) |
| `RUN.json` | yes (`:30–31`) | **yes** (`:124` `limitation` key) |
| `metrics.json` | yes (`:22–25`) | **NO** — no caveat key anywhere |
| `PREREGISTRATION.md` | no (frozen pre-run; cites the metric definition) | **yes** (`:12–16`), and it is the file that *mandates* the caveat everywhere |
| `compare.py` | prints κ to stdout | no (a script, not an artifact) |
| `labelsB.json`, `disagreements.jsonl`, `parse_summary.json`, `characterisations*.json` | no | n/a |

So the answer is **only some**: two of the three artifacts that carry the number carry the limitation,
and the missing one is `metrics.json`. UEXP's own pre-registration makes that a defect, which is why
C2 is a correction rather than a note.

## What would change my verdict

- **To `fail`:** any of the following. (a) UEXP's artifacts not reproducing byte-for-byte on a re-run
  — they did, all six, so the experiment is reproducible as claimed. (b) A second independent method
  finding even one `answer ∉ option set`, duplicate id, or malformed row — mine found none of the 190
  via a non-regex parser. (c) κ or agreement differing from the recorded values — they matched to
  1e-15 pooled and 1e-6 for all seven strata. (d) Evidence that UEXP's unit wrote inside
  `/home/zer0null/Duval` — I found no tracked-file, fixture, HEAD or index change, and the reflog
  shows HEAD never moved after 12:51:58.
- **To `pass` (from `pass-with-corrections`):** the two substantive corrections being applied —
  restate the `F-EXP11-11` relation at `RUN.json:104` / `EVIDENCE.md:258` as a separate measurement
  rather than corroboration, and add the limitation key to `metrics.json`. (I do not own those files
  and did not edit them; the target and the corpus are read-only for this unit, and I wrote only my
  own report, card and handoff.)
- **To a stronger verdict on external validity: nothing I can do.** The cardinal limit stands
  untouched: this is a **model** pass, so κ = 0.9014 is **not inter-annotator agreement** and does not
  discharge `strategy/PAPER_CANDIDATES.md` §F.3's call for a second independent human labeller. UEXP
  says this itself in every artifact that carries the number except `metrics.json`; where it says it,
  it is right.

## Provenance of this verification

- Wrote only: `strategy/VERIFICATION_REPORT_3.md`, `orchestration/units/UVER3.md`,
  `orchestration/handoffs/UVER3.json`.
- UEXP's artifacts were **not modified**: the pipeline re-run happened in `/tmp/uver3b/exp`, a copy.
- Target was never written by me: only `sha256sum`, `cmp`, `stat`, `wc`, `find`, `awk`, `sed`, `grep`,
  `tail`, `ls`, `git rev-parse`, `git status --porcelain`, `git log`, and `git config --get-regexp`
  were run against `/home/zer0null/Duval`. HEAD is still `907fa39…`; the fixture is still
  `076164ac…4796` at its original mtime; `.git/HEAD` and `.git/index` are still stamped 12:51:58.
