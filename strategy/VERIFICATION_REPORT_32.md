# VERIFICATION REPORT 32 — UVER32 vs UNEUTRAL9 (`strategy/WHOLE_CLASS_NEUTRALISATION.md`)

Verifier: UVER32 (independent; not the author). Bound 25 tool calls. Method: my own scripts in `scratch/uver32/`
(`tokscan.py`, `mfcheck.py`), the author's tree copied to `scratch/uver32/{before,after}` before any run.
No file outside my write paths was modified.

**OVERALL: partial.** Every number in the report's two diagnostic tables that I re-derived reproduced exactly,
and the exit-code claim reproduces exactly (and correctly contradicts UNEUTRAL8). Three claims do not survive
as written: the residual-0 claim, the "only MATERIALISE is left in stimulus" claim, and the paper-delta list,
which misses the actual submission sources.

## 1. Rename set — REPRODUCED except the residual

Independent scan for the 32 named tokens (`scratch/uver32/tokscan.py`: identifier-boundary, case-sensitive
regex; literal match for `expanded[` / `admit(`):

| tree | total occurrences | files with hits |
|---|---|---|
| `scratch/uneutral8/package` | **6177** | **17 of 29** (exactly the report's file set) |
| `scratch/uneutral9/package` | **1** | 1 |

- 32 tokens, 6177 occurrences, 17/29 files: **exact match.** The 12 untouched files include `LICENSE`,
  `CONTRIBUTING.md`, `COMMERCIAL.md` as stated.
- **Residual is 1, not 0.** The survivor is `ANSWER` in the author's own new comment:
  `verify/recompute-claims.py:117` — `# e.g. ANSWER/answer and changes the distinct-token overlap). Both are checked below against`.
  It is a meta-reference, not a live identifier, but the claim "residual count 0 for those 32 tokens" is false.
- The mapping is genuinely not shipped: `scratch/uneutral9/rename.py` stays in `scratch/`, no tag→token table
  appears in the package (only the `Gnn` tags themselves, as expected).

## 2. Exit codes — REPRODUCED exactly; UNEUTRAL8's counter-claim contradicted on its own tree

All three run in `scratch/uver32/before` and `scratch/uver32/after` copies:

```
verify/recompute-claims.py        before exit=1   after exit=0
second-labeller/parse_fixture.py  before exit=0   after exit=0
second-labeller/compare.py        before exit=0   after exit=0
```

before: `0.3526 second-labeller A/B mutual agreement shipped=0.3473684210526316 MISMATCH` /
`ALL CLAIM NUMBERS PRESERVED: False`; after: `A/B mutual agreement: published=0.3526 tree=0.3684210526315789
reproduced=False cite=papers/encoder-crossover-190/CLAIMS.md:109` / `ALL CLAIM NUMBERS PRESERVED: True`.

**On UNEUTRAL8.** The two units are **not** measuring different things: `scratch/uneutral8/package` is
byte-identical to `scratch/uneutral9/before_pkg` (verified), so UNEUTRAL8's handoff line
`"recompute": "exit 0 both; ALL CLAIM NUMBERS PRESERVED: True"` is **contradicted on the tree it shipped**.
The failure is static, not run-order-dependent: `verify/recompute-claims.py:38-41` hard-codes the published
table `0.3252 / 0.3526`, while the same tree's `second-labeller/metrics.json` holds routeA kappa
`0.31988636363636364` and `AB_mutual_agreement 0.3473684210526316`. UNEUTRAL9's diagnosis of UNEUTRAL8
(overstated) is **correct**.

## 3. Moved diagnostics — ALL 7 REPRODUCED

From `scratch/uver32/*/second-labeller/metrics.json`, with kappa independently re-derived as
`(agreement - pe)/(1 - pe)` (matches reported kappa to 1e-16 in both trees and both routes):

| diagnostic | before | after | claim |
|---|---|---|---|
| route A kappa | 0.31988636363636364 | 0.3248813212427869 | ok |
| route A agreement | 0.3368421052631579 | 0.34210526315789475 | ok |
| route A pe | 0.024930747922437674 | 0.025512465373961218 | ok |
| route A exact_index | 64 | 65 | ok |
| route A ties | 121 | 141 | ok |
| route A zero_score | 41 | 89 | ok |
| route B AB_mutual_agreement | 0.3473684210526316 | 0.3684210526315789 | ok |

**Unreported moved value:** `passes["labelsB.json"].disagreements_where_routeA_backs_record` also moves,
**5 → 4** (`compare.py` prints it). It is absent from the report's "All values measured" table. Small, but the
table is presented as exhaustive.

## 4. Unchanged diagnostics — ALL REPRODUCED

route B kappa `0.9013584840356494`; agreement `0.9052631578947369`; pe `0.03958448753462604`; exact_index 172;
18 disagreements; closed-vocabulary kappa `0.8837023738280471`; roster+bespoke kappa `0.9139973672663448`;
parse 190 records / 190 cases / 721 options / 74 distinct labels / `parse_failures []`; fixture-correctness
digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` — the same digest prints for the
before tree too (so it is a genuine rename-invariant projection, not an after-only artifact).

## 5. Census split — REPRODUCED exactly, but the report names only 1 of its own 2 survivors

`scratch/ubij1/census_one.py` (the scanner the report cites) re-run on both copies:

| | before | after |
|---|---|---|
| TOTAL | 1390 | 83 |
| inside stimulus | 1083 (distinct 13) | 26 (**distinct 2**) |
| outside | 265 | 57 |
| JSON keys | 42 | 0 |

by class before `json 1066/39/42 · ts 0/192 · data-jsonl 17/7 · prose-md 14 · tooling 13`; after
`json 24/30/0 · ts 0/8 · data-jsonl 2/0 · prose-md 7 · tooling 12`. **All exact.**

**The 2 surviving distinct in-stimulus tokens are `MATERIALISE` (inside 20 / outside 6) and `broker`
(inside 6 / outside 2)** — the latter is the substring match inside `Broker` ("an in-process Broker", a
stimulus value in `fixture/fixture-190.json`). The report's prose says "The only identifier-shaped string left
inside the stimulus is `MATERIALISE`", contradicting its own table row (`distinct 2`). A case-sensitive
rename deliberately did not touch `Broker`.

## 6. MANIFEST — REPRODUCED (own re-hash script)

`scratch/uver32/mfcheck.py` re-hashes from disk and never trusts the manifest digests:
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`. `counts.files 29` (28 in `files`
+ `MANIFEST.json`), `bytes_total 829435` = sum of the 28 listed files, disk 29 files.
`manifest_self` recomputes to `9656d35aa5eaf39693e8ee3a2cba4794b52d5ba1a1cbd8a93c9a65f1b953d47a` under the
stated convention (blank `generated_utc`, `manifest_self` key removed before hashing) — **genuine**.
Idempotence: the author's `scratch/uneutral9/manifest.py` run twice into fresh copies produces identical
`files`, `counts`, and `manifest_self`; the printed `bytes_total` (841304) includes the manifest's own size,
the stored one does not — internally consistent, and the report quotes the stored value.

## 7. Paper citations — the cited lines are right; the list MISSES the submission source

Quoted verbatim:
- `papers/encoder-crossover-190/CLAIMS.md:108` — `| deterministic lexical route (routeA) κ | 0.3252 | metrics.json | .routeA.kappa = 0.32520740993294694, agreement 0.3421 | yes | this is a **rule**, not a labeller |`
- `CLAIMS.md:109` — `| AB mutual agreement | 0.3526 | metrics.json | .passes["labelsB.json"].AB_mutual_agreement | yes | |`
- `MANUSCRIPT.md:381` — `deterministic lexical route (routeA) is not a labeller at all: it is a **rule**, and its κ = 0.3252 is`
- `MANUSCRIPT.md:633` — `**0.3526**; the deterministic lexical rule (routeA — a **rule**, not a labeller) reaches only κ = **0.3252**`
- `LIMITATIONS_UPDATE.md:245` — `(0.9053 / 0.9014 / 18 / stratified 0.8837 / 0.9140 / 0.3526 / 0.3252 / 0.3421) are byte-identical.`
- `VERIFIER_CORRECTIONS.md:139` — `` `0.8837` 1→1, `0.9140` 1→1, `0.3526` 1→1, `0.3252` 2→2, `0.3421` 7→7. ``

**MISSED citations (the check that matters):**
- **`papers/encoder-crossover-190/submission/main.tex:194`** — `it is a \textbf{rule}, and its $\kappa$ = 0.3252 is the floor a rule-only`
- **`papers/encoder-crossover-190/submission/main.tex:334`** — `... \textbf{0.9140}; AB mutual agreement \textbf{0.3526}; the deterministic lexic` and on the same line `a labeller) reaches only $\kappa$ = \textbf{0.3252} (agreement 0.3421)`
  So both stale numbers appear twice in the **actual `.tex` submission source** — the highest-consequence omission.
- `GAPS.md:19` — `| deterministic lexical route κ | 0.3252 | metrics.json .routeA.kappa |`
- `DISCLOSURE_CHANGES.md:143` — `κ 0.9014/0.9053, 0.3252/0.8837/0.9140/0.3526, 4.167e−09, ...`
- `EVIDENCE_NOTES.md:279-280` — `... AB_mutual_agreement ...` and `routeA kappa 0.32520740993294694 agreement 0.34210526315789475`
  (the only place the **full-precision** stale route-A kappa and its agreement are quoted).

Per-file hit counts for the two stale values: `CLAIMS.md` 2, `MANUSCRIPT.md` 2, `main.tex` 2,
`EVIDENCE_NOTES.md` 2, `LIMITATIONS_UPDATE.md` 1, `VERIFIER_CORRECTIONS.md` 1, `GAPS.md` 1,
`DISCLOSURE_CHANGES.md` 1. The report's list covers 8 of these 12 occurrences and 4 of the 8 files.

## 8. Stated mechanism — SUPPORTED at code level, and still latent in the emitted tree

- `second-labeller/compare.py:16` `TOKEN = re.compile(r"[a-z0-9]+")`; `:21` `return WS.sub(" ", s.strip().lower())`;
  `:27` `tq = set(TOKEN.findall(question.lower()))`; `:31` `ot = set(TOKEN.findall(o.lower()))`. Route A is
  case-insensitive, so a case-sensitive rename can split a pre-existing case-variant pair. **Explanation supported.**
- Isolation: in the **before** stimulus, 9 uppercase enums co-occur with their lowercase twin in stimulus
  values — `ESCALATE` 56/31, `ANSWER` 30/5, `DROP` 29/2, `SINGLE` 22/1, `SEQUENCE` 22/2, `RETURN` 22/2,
  `GRANT` 1/45, `REPLAY` 1/2, `STEP` 1/158 (uppercase/lowercase). Tokenizer demo:
  `re.findall(r"[a-z0-9]+", "ANSWER answer") == ["answer"]` (one distinct token) but after the rename
  `"G07 answer"` yields `["07","answer"]` (two) — the distinct-token overlap can only fall, consistent with
  `zero_score` 41→89 and `ties` 121→141.
- Caveat: the same effect the report describes is **still latent** — `GRANT` (1) and `STEP` (1) were barely
  colliding pre-rename, while the big colliders were ESCALATE/ANSWER/DROP.

## ALSO REPORT — residual system vocabulary (not fixed)

Case-insensitive identifier-boundary scan of all 29 emitted files for the 32-token class finds **16 distinct
surviving surface forms, ~1,400 occurrences**, including **in-stimulus** occurrences (same `question/options/
situation` rule as the census):

- in stimulus after: `step` 471, `grant` 131, `escalate` 90, **`Answer` 87**, `Step` 15, `answer` 15,
  `Broker` 6, `sequence` 6, `replay` 6, `return` 6, `single` 3, `drop` 3 (**839 total, 12 forms**; before: 1097)
- outside after: `step` 181, `answer` 42, `escalate` 33, `Answer` 29, `single` 17, `return` 17, `grant` 57,
  `Step` 5, `continue` 4, `drop` 3, `Broker` 2, `sequence` 2, `replay` 2, `persistent` 1, `Return` 1,
  `Discard` 1, plus the single `ANSWER` in `verify/recompute-claims.py:117`.

Judgement: the lowercase twins (`step`, `grant`, `escalate`, `drop`, `answer`) are defensible as ordinary
English, but they are exactly the case-variants of the author's own renamed enums, so an automatic reader
still sees the same words; `Answer` (87) and `Broker` (6) are title-case forms of an action enum and a census
role sitting inside stimulus values, and the report's "only MATERIALISE" sentence does not acknowledge them.
The package also still carries the released filenames/paths the census flags (`fixture-190.json`,
`reflex-decisions.ts`, `DECISION_CASE_SCHEMA.ts`, `tools/typed-channel`, `EXP#12`, `DecisionCase`,
`DecisionKind`, `nKind`) — those are shipped-artifact names, as the report argues.

## RED→GREEN (my method is non-vacuous)

- Census scanner: injecting ` editor` into one stimulus `question` and `broker broker` into `README.md` of a
  copy moves the scanner from `TOTAL 83 / inside 26 distinct 2 / outside 57` to
  `TOTAL 86 / inside 27 distinct 3 / outside 59`. It is not a constant.
- Exit-code method: the same command distinguishes the failing tree (before, exit 1,
  `ALL CLAIM NUMBERS PRESERVED: False`) from the passing tree (after, exit 0, `True`).
- Manifest method: my re-hash reports mismatches if a listed hash changes (mfcheck validates real stored
  digests, not the manifest's claims).

## Bottom line

Reproduced: rename counts (6177/17-of-29), all 7 moved diagnostics, all 10 unchanged diagnostics, the census
split, the manifest and its self-exemption, the exit codes, and the mechanism. Contradicted/overstated:
residual is 1 not 0; the in-stimulus residual is 2 distinct not 1; the paper-delta list misses 4 files, most
importantly `submission/main.tex:194,334`. UNEUTRAL8's "exit 0 / ALL CLAIM NUMBERS PRESERVED: True" does not
survive re-checking on the tree it shipped.
