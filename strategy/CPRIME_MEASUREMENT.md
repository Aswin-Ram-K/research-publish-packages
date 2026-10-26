# C′ MEASUREMENT — verification report on UNEUTRAL3's release option C′

**Unit:** UNEUTRAL4 (independent verifier + reporter). **Author of the artifacts under test:** UNEUTRAL3,
which died before writing this file; its card/handoff are left untouched as the record of the failed unit.
**Workspace:** `/home/zer0null/reserach extarctor`. **Date of run:** the UNEUTRAL4 session that wrote this file.

Reader's warning, stated up front because it is the single most dangerous artifact in this workspace:

> `verify/recompute-claims.py` prints `ALL CLAIM NUMBERS PRESERVED: True` **even on a tree where route A has
> moved**. It reads no JSONL and never recomputes route A from the data — but it is **not vacuous**: it does
> read `second-labeller/metrics.json` (`:112-118`) and compares the stored second-labeller numbers against
> frozen constants, so moving a stored `labelsB` number makes it print `ALL CLAIM NUMBERS PRESERVED: False`
> and **exit 1**. It is a **consistency check between the claimed numbers and the stored metrics/labels**, not
> a recomputation. That `True` was reproduced by me on all three trees — including `tree-bij`, whose
> fixture-correctness digest is *not* the one UNEUTRAL3 claimed. **Do not cite that `True` as evidence that no
> number moved.**

Every number below is labelled **[U4]** (measured by me, command given) or **[U3]** (UNEUTRAL3's claim).
[U3] numbers I reproduced are labelled **[U3≡U4]**; contradicted ones **[U3✗U4]**.

---

## 1. Trees, provenance, and exact build commands

All three trees contain **44 files, identical file sets** (`find . -type f | sort` diff empty between each
pair). They are built in a chain, each stage reading the previous tree:

| Tree | Path | Built by |
|---|---|---|
| pinned | `scratch/uneutral3/tree-pinned` | UNEUTRAL1 (tree A) |
| stripped | `scratch/uneutral3/tree-stripped` | `python3 scratch/uneutral3/strip.py` (SRC=`tree-pinned` → DST=`tree-stripped`) |
| bij | `scratch/uneutral3/tree-bij` | `python3 scratch/uneutral3/bij.py` (SRC=`tree-stripped` → DST=`tree-bij`; LIVE=`repro/encoder-crossover-190-SANITISED` is read only for kind discovery) |

Diagnostics for all trees were produced by:

```
bash scratch/uneutral3/run_diags.sh <tag> <tree>      # tag ∈ {pinned,stripped,bij}
python3 verify/recompute-claims.py                    # inside each tree
```

- `strip.py` constant facts [U4, read of `scratch/uneutral3/strip.py:25-28`]: `SRC=…/tree-pinned`,
  `DST=…/tree-stripped`, `DEAD=("texts","id","familyId","clanId","stratum")`.
- `bij.py` constant facts [U4, read of `scratch/uneutral3/bij.py:32-39`]: `LIVE=repro/encoder-crossover-190-SANITISED`,
  `SRC=…/tree-stripped`, `DST=…/tree-bij`, `SKIP_EXT={".py",".sh",".bash"}`, `PROSE_KEYS={question,options,situation,state,instructions,criteria,…}`;
  the map is never written to disk (`map_shipped:false`).
- The pinned tree's own build log `scratch/uneutral3/gen-pinned.log` records steps (R0 copy of 41 files;
  R1–R3 fixture rewrite `076164ac…` → `751dc007…`; redaction log under `verify/`) but **not a command line**
  — the pinned generator's invocation is **UNVERIFIED** (see §9).
- `bij.py` was **re-executed by me** through a DST-parametrized copy (`scratch/uneutral4/bij_det.py`
  → `scratch/uneutral4/bij-run`). Two runs are byte-identical, and the rebuild is byte-identical to the
  on-disk `tree-bij` (`diff -r` empty) — so the bij build is deterministic and its stated command is exact.

Diagnostic copies with the recorded outputs live at `scratch/uneutral3/rt/{pinned,stripped,bij}/`, and my
verbatim working copies at `scratch/uneutral4/t/{pinned,stripped,bij}/`. Note: `rt/bij` is a **superseded
build** (see §6).

---

## 2. Byte table [U4]

| File | live | pinned | stripped | bij |
|---|---|---|---|---|
| `harness/data/train.jsonl` | 2,205,127 | 2,205,127 | 509,453 | 501,133 |
| `harness/data/dev.jsonl` | 484,922 | 484,922 | 118,444 | 116,669 |
| **two data files** | 2,690,049 | 2,690,049 | 627,897 | 617,802 |
| **whole tree (data byte total)** | 5,611,497 (59 files) | 5,158,635 | 3,096,483 | 3,057,949 |

- strip saving vs pinned: `1,695,674 + 366,478 = 2,062,152 B` on the two data files; tree total −2,062,152 B
  (−39.97%). **[U3≡U4]** (UNEUTRAL3 claimed −2,062,152 B total: exact).
- bij additional saving vs stripped: **−38,534 B (−1.24%)** tree-wide. **[U3]** claimed no byte figure for bij
  beyond "moves no metric"; this is my measurement.
- Per-field train/dev bytes removed by the strip [U4]: `texts` 1,625,474 / 349,678 · `id` 13,600 / 3,400 ·
  `familyId` 17,600 / 4,400 · `clanId` 15,200 / 3,800 · `stratum` 15,800 / 3,200.

Commands: `wc -c` on each file; tree totals by `find <tree> -type f -printf '%s\n' | awk '{s+=$1} END{print s}'`.

---

## 3. Full number-movement table [U4, all columns re-run by me]

Produced by `bash scratch/uneutral3/run_diags.sh <tag> scratch/uneutral4/t/<tag>`; every invocation exited 0.
The `live` column is the reference as published in the sanitised tree.

| Quantity | live | pinned | stripped | bij |
|---|---|---|---|---|
| routeA `ties` | 120 | 120 | 120 | 120 |
| routeA `agreement` | 0.34210526315789475 | = | = | = |
| routeA `kappa` | 0.32520740993294694 | = | = | = |
| routeA `exact_index_matches` | 65 | 65 | 65 | 65 |
| routeA `zero_score_cases` | 41 | 41 | 41 | 41 |
| routeB_primary `agreement` | 0.9052631578947369 | = | = | = |
| routeB_primary `kappa` | 0.9013584840356494 | = | = | = |
| routeB_primary `exact_index_matches` | 172 | 172 | 172 | 172 |
| routeB_primary `n_disagreements` | 18 | 18 | 18 | 18 |
| `AB_mutual_agreement` | 0.3526315789473684 | = | = | = |
| kappa, `closed_subset` (labelsB) | 0.8837023738280471 | = | = | = |
| kappa, `roster_and_bespoke_subset` | 0.9139973672663448 | = | = | = |
| arm `modernbert-base` | 0.347368 | = | = | = |
| arm `deberta-v3-base` | 0.347368 | = | = | = |
| arm `setfit-mpnet` | 0.263158 | = | = | = |
| arm `majority-class` | 0.452632 | = | = | = |
| arm `shuffled-label` | 0.231579 | = | = | = |
| arm `decider-4b-repro` | 0.678947 | = | = | = |
| 2×2 `both/headOnly/deciderOnly/neither` | 39/27/90/34 | = | = | = |
| **fixture-correctness digest** | `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a` | `8dd05ce6…` | `8dd05ce6…` | **`c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`** |

So: **the strip moves no number, including the digest [U3≡U4]**; **the bijection moves no metric but does move
the fixture-correctness digest [U3≡U4]**. The digest is `sha256` over `[[id, correct, len(options)]]` for the
fixture ([U4] read of `verify/recompute-claims.py:126-128`).

**The bij digest claim is a trap.** UNEUTRAL3 says the digest moves `8dd05ce6…` → `30b75581…`. That value is
what `scratch/uneutral3/rt/bij` yields — but `rt/bij` is a **superseded 20:06 build**: the on-disk
`tree-bij/harness/data/fixture-190.json` is 20:08:25, `rt/bij/…` is 20:06:56, and `bij.py` was last edited
20:07:57; `diff -rq tree-bij rt/bij` shows 21 common files differing (plus 11 files only in `rt/bij`). The on-disk `tree-bij`, my two fresh
rebuilds, and the current `bij.py` all give **`c7696edc…`**. So the *phenomenon* (digest moves) is reproduced,
but the *value* `30b75581…` is **[U3✗U4]** — a number from a build that no longer exists on disk.

---

## 4. Census [U4 re-runs]

Scanner: **`scratch/uneutral2/census2.py`** ([U4] — no census scanner exists anywhere under
`scratch/uneutral3/`; only `strip.py`, `bij.py`, `run_diags.sh`). Identifier source:
**`scratch/uagnostic1/census.tsv`**, column 2, 184 identifiers (header `cat id count files locations`).
Counting method: per line, case-insensitive `re.findall` over raw file bytes.

| Tree | UNEUTRAL3 claim | my re-run (`scratch/uneutral4/census-rerun-*.txt`) | verdict |
|---|---|---|---|
| pinned | TOTAL 26,344 · 99 of 184 | **TOTAL 26,344 · 99 of 184** | **[U3≡U4]** exact |
| stripped | TOTAL 9,247 · 99 of 184 | **TOTAL 9,247 · 99 of 184** | **[U3≡U4]** exact |
| bij | TOTAL 8,213 · 99 of 184 | **TOTAL 5,384 · 95 of 184** | **[U3✗U4]** contradicted |
| `rt/bij` (superseded build) | — | TOTAL 9,768 · 99 of 184 (54 files, includes diagnostic outputs) | — |

Per-class occurrences [U4]: pinned — data-jsonl 20,587 · json 4,316 · ts 1,038 · tooling 308 · prose-md 50 ·
data-jsonl-other 45. stripped — json 4,316 · data-jsonl 3,490 · ts 1,038 · tooling 308 · prose-md 50 ·
data-jsonl-other 45. bij — data-jsonl 2,385 · json 2,053 · ts 600 · tooling 308 · data-jsonl-other 25 ·
prose-md 13.

**Why the pinned raw-line count (26,344) differs from a decoded-value count (16,813).** `floor.py` is a **MIXED**
walk: decoded values+keys for the 19 JSON files, raw text for every non-JSON file. Under that mixed method it
totals pinned **16,813**, stripped **9,247**, bij **5,384**; a strict decoded-only walk gives pinned **15,417**,
stripped **7,851**, bij **4,463** (inside-stimulus 2,171 / 30 is unaffected). The stripped and bij totals agree
with `census2.py` *exactly* only because the mixed walk counts non-JSON files raw — that cross-check is partly
circular, not an independent validation (the first version of the walk undercounted because it used
`low.count(i)` without `i.lower()`; fixed). The pinned
gap of 9,531 is a **scanner artifact**: the raw-line scanner matches across JSON escape sequences, counting
`"\nKind"`, `"\nCandidate"`, `"\nSituation"` as the identifiers `nKind` / `nCandidate` / `nSituation`
(3,177 + 3,177 + 3,177 = 9,531 — the raw identifier hits 3,180 / 3,179 / 3,178 include 6 genuine `.ts`/`.sh`
hits counted by both methods). Those characters do not exist in the decoded data, and they
vanish with `texts`. Consequence: **~36% of the pinned census number is not project vocabulary at all.**

---

## 5. Field audit — consumed vs dead, with read-sites [U4]

Read of `harness/train.py` and `harness/tccommon.py`. The strip removed `texts`, `id`, `familyId`, `clanId`,
`stratum` from `train.jsonl` + `dev.jsonl` only (not from `corpus.json`, correctly: `prepare.py:79-91` reads
`familyId`/`clanId`/`stratum` from the **corpus**, which the strip never touches).

**Consumed from a loaded JSONL example** — read-site lines:

| Field | Read-sites |
|---|---|
| `options` | `harness/train.py:94`, `:312`, `:322`, `:373`; `harness/tccommon.py:145-146`, `:156`, `:158`, `:163` |
| `kind` | `harness/train.py:311`, `:322`; `harness/tccommon.py:163` |
| `situation` | `harness/train.py:311`, `:322` (the `:316` hit is a print statement, not a field use); `harness/tccommon.py:163` |
| `goldIndex` | `harness/train.py:105`, `:169`, `:175`, `:315`, `:323`, `:376` |
| `gold` | `harness/train.py:367` |

**Dead** — grep for a reader of a *loaded JSONL example* is empty in each case:

| Field | Evidence it is dead |
|---|---|
| `texts` | only **written** at `harness/prepare.py:115` (`out["texts"]=tc.texts_for_example(ex)`); the local variables named `texts` in `train.py:103`, `evaluate.py:79`, `tcmodel.py:117` are **re-derived** via `tc.texts_for_example(...)`. `grep -n 'e\["texts"\]\|ex\["texts"\]\|example\["texts"\]\|rec\["texts"\]'` → **empty**. |
| `id` | written at `harness/tccommon.py:139` (`"id": case["caseId"]`). Readers are fixture-side only: `analyze.py:152` (fixture), `evaluate.py:322` (`"id": ex["id"]`, where `examples` come from `evaluate.py:282` `tc.fixture_case_to_example(c)`, not from JSONL), `tccommon.py:153` (writes a fixture example). |
| `familyId`, `clanId`, `stratum` | reads are of **corpus** cases (`prepare.py:74-91` from `tc.load_corpus()`; `analyze.py:325` reads `baselines["checks"]`); writes at `tccommon.py:140-143`. `grep -n 'e\["familyId"\]\|ex\[…\]\|example\[…\]\|rec\[…\]'` returns **only the tccommon.py write lines**. |

**Verdict: the strip's field list is correct.** Nothing loads a stripped field from the JSONL. (This matches
UNEUTRAL3's own audit; I re-derived it independently.)

---

## 6. Parseability and tooling checks [U4]

| Check | live | pinned | stripped | bij |
|---|---|---|---|---|
| `json.loads` every line of `train.jsonl` | n/a (not re-run) | 800 records, 0 bad | 800, 0 bad | 800, 0 bad |
| `json.loads` every line of `dev.jsonl` | n/a | 200, 0 bad | 200, 0 bad | 200, 0 bad |
| `disagreements.jsonl` | n/a | 18, 0 bad | 18, 0 bad | 18, 0 bad |
| `second-labeller/parse_fixture.py` | exit 0 | exit 0 | exit 0 | exit 0 |
| `second-labeller/compare.py` | exit 0 | exit 0 | exit 0 | exit 0 |
| `verify/recompute-claims.py` | printed True | printed True | printed True | printed True ← see the warning at the top |
| `python3 -m compileall harness/ second-labeller/` | — | OK | OK | OK |

**`prepare.py` refuses in every tree, and it is not the strip's fault.** [U4] In `tree-pinned`,
`tree-stripped` and `tree-bij`, `harness/prepare.py` exits **2** with:

```
REFUSED: corpus digest mismatch — expected c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66, got 58b09a3c…
```

(`prepare.py:43-45`, constant `tccommon.py:64 CORPUS_SHA256`.) The **live** `corpus.json` sha256 *is*
`c78681d6…` (matches the frozen constant); `tree-pinned` = `tree-stripped` = `58b09a3c…`; `tree-bij` =
`47fb4a50…`. The refusal is **pin-induced and pre-existing** — the same in `tree-pinned`, before the strip
ever ran. Consequence: **the released tree cannot regenerate its own JSONL under its pinned corpus — but the
strip is not one-way.** Red→green [UVER13]: restoring the live corpus (digest `c78681d6…`) makes
`harness/prepare.py` **exit 0 in both the pinned and the stripped copies**, and it re-emits the **FULL
unstripped** JSONL — 2,205,127 B train / 484,922 B dev. So the refusal is caused by the **corpus-digest pin**
alone, not by the strip; regeneration is blocked by that pin alone, and a reader who restored the pinned corpus
would regenerate the *pre-strip* artifact. (`tree-bij` differs because the bijection renamed data in
`corpus.json` too.)

**KIND_ALIAS is already broken before the bijection** [U4]. `tccommon.py`'s `KIND_ALIAS` has 4 keys
(`acquisition.path`, `escalation.decision`, `routing.team`, `topology.shape`); the corpus kinds in
`tree-pinned` are `K01,K02,K04,K05,K07,K08,K09,K10,context.package` → **0 of 9 resolve**. Same 0 in
`tree-stripped`, and the same 0 in `tree-bij` (which renamed only the residual `context.package`→`N10`). So
the bijection introduces **no new** alias break. (This killed my initial hypothesis that the bijection breaks
prompt rendering via the alias table; it does not, because the alias table is already inert in the pinned tree.)

---

## 7. Residual classes and the irreducible floor [U4]

Measured by `scratch/uneutral4/floor.py` (case-insensitive, per identifier, over decoded JSON values *and*
JSON keys; full table in `scratch/uneutral4/residual-floor.txt`). "Inside stimulus" = occurrences inside the
**values** of `question` / `options` / `situation` — i.e. the text the model actually reads; "outside" =
occurrences in other values; "keys" = occurrences as JSON object keys.

| Tree | inside stimulus | outside values | JSON keys | total (walk) |
|---|---|---|---|---|
| pinned | 2,171 | 11,267 | 3,375 | 16,813 |
| stripped | 2,171 | 5,701 | 1,375 | 9,247 |
| bij | 2,171 | 2,044 | 1,169 | 5,384 |

**The inside-stimulus figure is identical in all three trees — 2,171 occurrences of 30 distinct identifiers.**
That is the **irreducible floor**: the prose is the model's input, and the bijection masks it (restores it
verbatim on purpose). In `tree-bij`, those 2,171 are **40.3%** of all remaining occurrences.

The residual identifiers *inside the stimulus* in `tree-bij` (count): `editor` 398, `reasoner` 310,
`verifier` 229, `attached` 181, `fs.read` 179, `model.call` 176, `fs.write` 164, `test.run` 157,
`net.fetch` 131, `detached` 75, `topology` 23, `output-only` 22, `code-inspector` 22, `memory.write` 15,
`memory-curator` 14, `MATERIALISE` 8, `web.fetch` 7, `researcher` 7, `policyHash` 7, `critic` 7,
`code-review` 7, `expanded[` 6, `admit(` 6, `broker` 5, `expiresAtEpoch` 3, `escalation` 3, `ToolCallIR` 3,
`reasonerCalls` 2, `canRequestEscalation` 2, `MutationProposal` 2 (30 identifiers; totals per tree in
`residual-floor.txt`).

**Fixture questions containing a real kind token: 23 of 190 [U3≡U4]** by the word-boundary regex
`(?<![A-Za-z0-9_.])k(?![A-Za-z0-9_])`; UVER13's lowercase-substring alternation over the 7 live kinds also
gives **23/190** — the earlier "25 of 190 by lowercase substring" did **not** reproduce; 75 of 190 questions contain *some*
census identifier by substring (85 by word boundary). UNEUTRAL3's "23" is reproduced. The live kind
vocabulary is 7: `acquisition`, `capability.family`, `context.package`, `escalation`, `memory.admission`,
`topology`, `worker.class`.

### The decisive question — is zero project vocabulary reachable while keeping the published numbers?

**No, not from here.** Any substitution that removed the remaining in-stimulus tokens would rewrite the
`question` / `options` / `situation` prose — the exact bytes the model reads — and the published route-A and
route-B numbers are functions of that stimulus plus stored labels. So the floor stands at **2,171 occurrences
of 30 identifiers inside the stimulus** (23 fixture questions naming their own kind among them). Reaching zero
would require a further, *behaviour-preserving* rewrite of the prose whose preservation could only be shown by
re-rendering and re-running the models — which nothing in this workspace has done (§9). What is achievable
without touching the stimulus is bounded by the outside/key classes, which the bijection already reduced to
2,044 + 1,169.

---

## 8. Plain verdict

**What a reader of the released artifact still sees.** Taking the recommended shape (`tree-stripped`), a
reader of the released tree still sees **9,247 occurrences of 99 of the original 184 identifiers**, of which
**2,171 occurrences / 30 identifiers sit inside the model's own input** (`question`/`options`/`situation`),
including **23 fixture questions that name their own decision kind in prose**. The kind axis itself is already
opaque (`K01…K10` tags; the shipped `KIND_ALIAS` resolves 0 of them, before and after any our work), but the
residual vocabulary — role names (`editor`, `reasoner`, `verifier`, `critic`, `researcher`), tool/interface
names (`fs.read`, `fs.write`, `model.call`, `test.run`, `net.fetch`, `ToolApi`-style types) — is fully
readable, and **308 occurrences remain in the shipped tooling** (`.py`/`.sh`) in *every* shape, because C′
deliberately pins the tooling. The dead metadata (`texts`, `id`, `familyId`, `clanId`, `stratum`) is gone from
the JSONL; the byte cost of the release drops by 39.97%.

**Which shape I would ship: `tree-stripped`.**

1. It is the only shape whose reduction is *provable*: every removed field has zero read-sites on a loaded
   JSONL example (§5), and the removal moves no number *including* the fixture-correctness digest (§3).
2. Every check I ran passes on it: JSONL parses, `parse_fixture.py`/`compare.py`/`recompute-claims.py` exit 0,
   all Python byte-compiles (§6).
3. `tree-bij` buys **−38,534 B (−1.24%)** and −3,863 occurrences over the strip, but it is a
   **two-vocabulary artifact**: the data files are renamed while the shipped `.py`/`.sh`/`verify/**` pins
   (which C′ keeps by design) still name the original vocabulary, so a reader gets renamed ids in the data and
   original names in the tooling with no bridge. Its own residual is 40% in-stimulus and unfixable, so it does
   not reach the neutralisation goal either.
4. Ship `tree-bij` only if the release goal is explicitly "minimise residual identifier *occurrences*", and
   accept the two-vocabulary artifact knowingly; the 1.24% byte gain alone does not justify it. If the goal is
   reaching the floor, the honest next step is a *consistent* re-tag (data **and** pinned tooling, plus
   `KIND_ALIAS`) followed by a full re-render/re-run — not this bijection.
5. Do **not** ship `tree-pinned`: it carries 1.97 MB of dead `texts` and cannot regenerate its own JSONL
   (`prepare.py` refuses, §6).

---

## 9. UNVERIFIED list

1. **No model was run.** `torch`/`transformers` were not exercised; "numbers preserved" is verified only for
   *metric recomputation from stored labels and result JSONs*, not for re-training or re-rendering a prompt.
   A reader who retrains on any of these trees is untested.
2. **The claimed bij census `8,213` / `99 of 184` has a printed on-disk source, but no scanner behind it.**
   `scratch/uneutral3/census-tree-bij.txt` (11,663 B, written 20:06) contains exactly `TOTAL OCCURRENCES: 8213`
   and `distinct identifiers hit: 99 of 184`, with siblings `census-tree-pinned.txt` (26,344) and
   `census-tree-stripped.txt` (9,247). What is missing is the **scanner**, not the number: no census script
   exists under `scratch/uneutral3/` (the scanner is `scratch/uneutral2/census2.py`), so the claim cannot be
   regenerated in place. The file is a **superseded 20:06 build** — the same build that yields the `rt/bij`
   diagnostics and the stale `30b75581…` digest. Re-measured on the on-disk tree: `tree-bij` → 5,384/95; my
   deterministic rebuild → 5,384/95; `rt/bij` (superseded) → 9,768/99.
3. **The claimed digest `30b75581…` belongs to a build that no longer exists on disk** (`rt/bij`, 20:06);
   the on-disk `tree-bij` and fresh rebuilds give `c7696edc…`. The earlier `bij.py` revision could not be
   recovered. `tree-bij` + current `bij.py` is deterministic (two runs byte-identical, `diff -r` empty vs disk).
4. **Pinned generator invocation** is not recorded (only step counts in `gen-pinned.log`); I did not re-run
   UNEUTRAL1's build.
5. **`prepare.py` regeneration was not run to completion in any tree** — it refuses at exit 2 in
   pinned/stripped/bij (pre-existing, §6). I did not run it against the live tree (forbidden).
6. **`harness/train.py` / `evaluate.py` were read and byte-compiled, not executed** (no torch/GPU run), so
   "the shipped tooling still runs" is verified for `parse_fixture.py`, `compare.py`, `recompute-claims.py`
   (exit 0 each) and for compilation of the rest.
7. **The pinned 9,531 raw-line surplus** is attributed to `\n`-escape artifacts (nKind/nCandidate/nSituation
   = 3,180/3,179/3,178) by arithmetic and spot-checks, but I did not enumerate the artifact hits line by line.
8. **The map M** was never written to disk or logged by me; `bij.py` prints `map_shipped:false`, and all three
   trees have identical file sets (44 files), so no map artifact is shipped — but I did not run an exhaustive
   content search for a mapping table.

---

## 10. Reproduce-everything index

| Artifact | What it shows |
|---|---|
| `scratch/uneutral4/census-rerun-{pinned,stripped,bij}.txt` | my census re-runs (scanner `scratch/uneutral2/census2.py`) |
| `scratch/uneutral4/residual-floor.txt` | per-identifier inside/outside/key counts, all three trees |
| `scratch/uneutral4/floor.py`, `audit.py` | the walkers that produced the floor table |
| `scratch/uneutral4/bij_det.py`, `bij-run1/`, `bij-run2/` | bijection determinism + byte-identical rebuild of `tree-bij` |
| `scratch/uneutral4/t/{pinned,stripped,bij}/` | verbatim copies on which every diagnostic column was re-run |
| `scratch/uneutral4/prepare-stripped.out` | the `prepare.py` refusal in the stripped tree |
| `scratch/uneutral3/rt/<t>/{recompute-<t>.out,second-labeller/{parse-<t>.out,compare-<t>.out,metrics.json}}` | UNEUTRAL3's own diagnostic outputs (read-only record) |
| `scratch/uneutral3/{strip.py,bij.py,run_diags.sh,gen-pinned.log,strip-report.json}` | the builders under test |
| `scratch/uneutral3/census-tree-{pinned,stripped,bij}.txt` | the 20:06 census outputs (26,344 / 9,247 / 8,213); no scanner under `scratch/uneutral3/` writes them |

---

## Corrections applied

**Date:** 2026-10-15. Four statements corrected against the independent verifier [`strategy/VERIFICATION_REPORT_13.md`](VERIFICATION_REPORT_13.md)
(unit **UVER13**, verdict `pass`, 29 tool calls, its §5). **No number UVER13 reproduced was changed.**

1. **§9.2 / §10 — "no on-disk source" (was `:291`).** False: `scratch/uneutral3/census-tree-bij.txt` (11,663 B, 20:06)
   prints exactly `TOTAL OCCURRENCES: 8213` and `distinct identifiers hit: 99 of 184`. The missing artifact is the
   **scanner**, not the number; the file is a superseded 20:06 build — the same build that yields the `rt/bij`
   diagnostics and the stale `30b75581…` digest. §10 now lists the three census files.
2. **§5 — `situation` read-site `:158`.** `train.py:316` is a `print(...)` statement, not a field use; the true
   read-sites are `train.py:311` and `:322` (plus `tccommon.py:163`). The field is still consumed.
3. **§6 — "the strip is one-way" (was `:197`).** Overstated. UVER13's red→green: restoring the live corpus
   (digest `c78681d6…`) makes `harness/prepare.py` **exit 0 in both** the pinned and the stripped copies and re-emit
   the **FULL unstripped** JSONL (2,205,127 B train / 484,922 B dev). Only the **corpus-digest pin** blocks
   regeneration — and a reader who restored the pinned corpus would regenerate the *pre-strip* artifact.
4. **Reader's warning — the `recompute-claims.py` trap (`:9-12`), plus three figures.** The script is not vacuous:
   it reads `second-labeller/metrics.json` and prints `ALL CLAIM NUMBERS PRESERVED: False` with **exit 1** when a
   stored `labelsB` number moves — a consistency check between the claimed numbers and the stored metrics/labels,
   not a recomputation. Also: `floor.py`'s totals come from a **mixed** walk (strict decoded-only is
   `15,417 / 7,851 / 4,463`, not `16,813 / 9,247 / 5,384`); the escape gap is **9,531**, not 9,537; the stale-build
   difference is **21** common files, not "~20". UVER13's count of kind-token questions is **23/190**, and the
   "25 of 190 by lowercase substring" variant did **not** reproduce.
