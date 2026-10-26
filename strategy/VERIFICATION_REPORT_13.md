# VERIFICATION REPORT 13 — independent re-derivation of `strategy/CPRIME_MEASUREMENT.md`

**Unit:** UVER13 (independent verifier; did not write the artifact under test).
**Target:** `strategy/CPRIME_MEASUREMENT.md` — 323 lines, 21,748 B, sha256
`13d0712ebecf77a086747115fcda7e21d989642aa8a001e5c17d7e015f338dcb`. **Hash recomputed and matched.**
**Author under test:** UNEUTRAL4. **Verdict: `pass`** — every headline number reproduced by my own
methods; 4 wordings and 1 citation are wrong and are listed in §5. The release call (ship `tree-stripped`)
rests on reproduced evidence.
**Bound:** ≤40 tool calls. Used: 29.
**Isolation respected:** I copied all trees into `scratch/uver13/` before any run; `scratch/uneutral3/**`,
`scratch/uneutral4/**`, `repro/encoder-crossover-190-SANITISED/` and `papers/**` were read only.

---

## 1. My own census (three trees, decoded values) — the contested number

Method `scratch/uver13/census_uver13.py`: identifiers = column 2 of `scratch/uagnostic1/census.tsv`
(184); per tree, (a) raw-line case-insensitive `re.findall`, (b) a recursive walk over **parsed JSON/JSONL**
counting occurrences inside string values, separately for object keys, with an inside-stimulus split on
`question`/`options`/`situation`.

| Tree | raw-line (my re-run) | U4 re-run | UNEUTRAL3 claim | decoded **values only** | decoded values + keys | inside stimulus |
|---|---|---|---|---|---|---|
| pinned | **26,344 / 99** | 26,344 / 99 | 26,344 / 99 | 12,042 / 71 | 15,417 / 99 | **2,171 / 30** |
| stripped | **9,247 / 99** | 9,247 / 99 | 9,247 / 99 | 6,476 / 71 | 7,851 / 99 | **2,171 / 30** |
| bij | **5,384 / 95** | 5,384 / 95 | **8,213 / 99** ✗ | 3,294 / 63 | 4,463 / 95 | **2,171 / 30** |

**The disagreement with UNEUTRAL3 is settled in U4's favour:** on-disk `tree-bij` really is 5,384 / 95
under the raw-line scanner, not 8,213 / 99. **But the claim that `8,213` "has no on-disk source" is
CONTRADICTED** — see §5.1.

### 1a. Escape artifact (claim 4) — REPRODUCED, with a 6-count correction

My mixed walk (decoded values+keys for the 19 JSON files, raw text for every non-JSON file) reproduces
U4's `floor.py` totals **exactly**: pinned **16,813** / stripped **9,247** / bij **5,384**, and
`raw − mixed` = **9,531**, composed of exactly three identifiers:

```
nKind       raw=3180  mixed=3  gap=3177
nCandidate  raw=3179  mixed=2  gap=3177
nSituation  raw=3178  mixed=1  gap=3177   →  gap total = 9,531
```

Raw `\n`+`Kind|Candidate|Situation` escape sequences: pinned 9,536 (7,743 in `train.jsonl` + 1,788 in
`dev.jsonl` + 5 in tooling), stripped **5**, bij **5**. So the surplus is real and disappears with
`texts`. **Correction:** U4 quotes the *raw* identifier hits (3,180 + 3,179 + 3,178 = 9,537) as the
artifact count; the artifact contribution is 3,177 each = **9,531** (the other 6 are genuine hits in
`.ts`/`.sh` tooling, counted in both methods). Difference is 0.06%.

## 2. Byte table and field list (claims 1, 2) — REPRODUCED

`wc -c`: live = pinned (train 2,205,127 / dev 484,922); stripped 509,453 / 118,444; bij 501,133 / 116,669.
Tree totals via `find -printf '%s'`: pinned 5,158,635 / stripped 3,096,483 / bij 3,057,949 (44 files each,
`find | sort` path diff empty). Strip saving **2,062,152 B**; bij −**38,534 B** (−1.24%). Per-field
`train.jsonl` bytes replicated exactly: `texts` 1,625,474 · `id` 13,600 · `familyId` 17,600 · `clanId`
15,200 · `stratum` 15,800.

Read-site audit, re-derived by `grep -n` on the live tree: `train.py` loads the split at `:429-430`
(`load_jsonl(train.jsonl/dev.jsonl)`). True reads: `options` 94, 312, 322, 373 · `kind` 311, 322 ·
`situation` 311, 322 · `goldIndex` 105, 169, 175, 315, 323, 376 · `gold` 367 · `texts` **none**.
`texts` is only *written* (`prepare.py:115`), re-derived at `train.py:103`, `evaluate.py:79`,
`tccommon.py:162`. `id`/`familyId`/`clanId`/`stratum` are written only (`tccommon.py:139-143`); their
readers are corpus/fixture/result consumers (`prepare.py:74-91`, `analyze.py:152,325`, `evaluate.py:142`
reads `r0` rows from `docs/research/EXP#11-evidence/*.jsonl`, `evaluate.py:322` reads
`fixture_case_to_example` output). **The dead-field verdict is correct.**

## 3. Reruns, digests, determinism (claims 3, 6, 8, 9) — REPRODUCED

`bash scratch/uneutral3/run_diags.sh <t> scratch/uver13/t/<t>` on fresh copies: all three exit 0,
`parse_fixture.py`/`compare.py`/`recompute-claims.py` exit 0, `compileall` exit 0. All metrics identical
across **live** (read from the live `metrics.json`), pinned, stripped, bij:

| Quantity | live = pinned = stripped = bij |
|---|---|
| routeA ties / agreement / kappa / exact / zero | 120 · 0.34210526315789475 · 0.32520740993294694 · 65 · 41 |
| routeB agreement / kappa / exact / n_dis | 0.9052631578947369 · 0.9013584840356494 · 172 · 18 |
| closed_subset / roster kappa | 0.8837023738280471 · 0.9139973672663448 |
| arms mbert/deberta/setfit/majority/shuffled/decider | 0.347368 · 0.347368 · 0.263158 · 0.452632 · 0.231579 · 0.678947 |
| 2×2 both/headOnly/deciderOnly/neither | 39 / 27 / 90 / 34 |

Fixture-correctness digest: pinned = stripped = `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a`;
bij = `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` — **exactly U4's value, and
UNEUTRAL3's `30b75581…` is contradicted.** JSONL parses: train 800 / dev 200 / disagreements 18, 0 bad.
`ALL CLAIM NUMBERS PRESERVED: True` printed on all three trees including bij. 308 tooling (.py/.sh)
occurrences in every shape.

**Determinism re-established independently:** I patch-copied `bij.py` (DST only) to
`scratch/uver13/bij_uver13.py`, ran it twice: runA ≡ runB, and runA ≡ on-disk `tree-bij` (`diff -rq` empty).
**Stale-build question settled by measurement:** `diff -rq tree-bij rt/bij` = 21 common files differ +
11 files only in `rt/bij` (32 diff lines); mtimes `tree-bij/.../fixture-190.json` 20:08:25 vs
`rt/bij/.../fixture-190.json` 20:06:56 vs `bij.py` 20:07:57 — exactly the superseding U4 describes.

## 4. In-stimulus floor (claim 5) — REPRODUCED independently

Decoded walk over `question`/`options`/`situation` **values** gives **2,171 occurrences of 30 distinct
identifiers in all three trees**, and my per-identifier list is identical to U4's (editor 398, reasoner
310, verifier 229, attached 181, fs.read 179, model.call 176, fs.write 164, test.run 157, net.fetch 131,
detached 75, topology 23, output-only 22, code-inspector 22, memory.write 15, memory-curator 14,
MATERIALISE 8, code-review 7, researcher 7, web.fetch 7, critic 7, policyHash 7, admit( 6, expanded[ 6,
broker 5, escalation 3, expiresAtEpoch 3, ToolCallIR 3, canRequestEscalation 2, reasonerCalls 2,
MutationProposal 2). Fixture questions carrying a live kind token: **23/190** (word-boundary alternation
over the 7 live kinds), same as UNEUTRAL3's and U4's figure. `prepare.py` refuses **exit 2** in all three
trees with the exact message `REFUSED: corpus digest mismatch — expected c78681d6…, got 58b09a3c…`;
corpus sha256 live `c78681d6…`, pinned = stripped `58b09a3c…`, bij `47fb4a50…`. `KIND_ALIAS` 4 keys vs
corpus kinds `K01,K02,K04,K05,K07,K08,K09,K10,context.package` → **0 of 9** in pinned and stripped (bij
only renames `context.package`→`N10`).

## 5. What is wrong with the report (carry-forward corrections)

**5.1 CONTRADICTED — "no on-disk source" (`CPRIME_MEASUREMENT.md:291`).** Verbatim: *"The claimed bij
census `8,213` / `99 of 184` has no on-disk source."* False: `scratch/uneutral3/census-tree-bij.txt`
(mtime 20:06, 11,663 B) contains `TOTAL OCCURRENCES: 8213` and `distinct identifiers hit: 99 of 184`,
alongside `census-tree-pinned.txt` (26,344) and `census-tree-stripped.txt` (9,247). What has no on-disk
source is a *scanner* under `scratch/uneutral3/` (true — the scanner is `scratch/uneutral2/census2.py`),
not the number. §10's artifact index also omits these three files. Correct wording: *"the on-disk census
file exists but is a superseded 20:06 build; no scanner under `scratch/uneutral3/` produced it."*

**5.2 CONTRADICTED — `situation` read-site citation (`:158`).** Verbatim row: *"| `situation` |
`harness/train.py:311`, `:316`, `:322`; `harness/tccommon.py:163` |"*. `train.py:316` is
`print(f"  fitting on {len(labels)} (situation, option) pairs")` — no field read. `grep -n '\["situation"\]'`
gives **311, 322** only (the pair list is built at `:313` from the `:311` render). Drop `:316`.

**5.3 OVERSTATED — the `recompute-claims.py` trap warning (`:9-12`).** Verbatim: *"`verify/recompute-claims.py`
prints `ALL CLAIM NUMBERS PRESERVED: True` **even on a tree where route A has moved**. It reads neither
JSONL and never recomputes route A."* The script **does** read `second-labeller/metrics.json`
(`:112-118`) and does compare its stored second-labeller numbers against frozen constants. I moved them
(one integer label in `labelsB.json["labels"]` → re-ran `compare.py`): `closed_subset` kappa
0.8837→0.8731172069825437, AB mutual 0.3526→0.3473684210526316, and `recompute-claims.py` printed
**`ALL CLAIM NUMBERS PRESERVED: False` and exited 1**. The demonstrated fact (True on bij, whose *digest*
moved) stands and the caution is sound, but the stated justification is not: the script is not blind to
movement in the stored numbers — it is blind only because it never *recomputes* route A from data.

**5.4 OVERSTATED — "the strip is one-way" (`:197-198`).** Verbatim: *"Consequence: **the released tree
cannot regenerate its own JSONL; the strip is one-way.**"* Red→green (§6) shows restoring the matching
corpus makes `prepare.py` exit 0 in **both** the pinned and the stripped tree and re-emit the **full
unstripped** pinned-shape `train.jsonl` (2,205,127 B) / `dev.jsonl` (484,922 B). Nothing about the strip
blocks regeneration; only the corpus-digest pin does. The strip is reversible by regeneration.

**5.5 OVERSTATED — `floor.py` method description (`:136`).** Verbatim: *"My value-level walk
(`scratch/uneutral4/floor.py`, case-insensitive over JSON values) totals pinned **16,813** …"*. Those
totals only appear under a **mixed** method: decoded values+keys for the 19 JSON files, raw text for
non-JSON files. A strict decoded walk gives pinned **15,417**, stripped **7,851**, bij **4,463**. (The
inside-stimulus split is unaffected.) The claimed cross-check — *"stripped and bij totals agree with
`census2.py` exactly, which validates the walk"* — is partly circular: they agree because the mixed walk
counts non-JSON files raw. The 9,531 escape-artifact finding is nevertheless independently confirmed (§1a).

**5.6 NOT REPRODUCED — "25 of 190 by lowercase substring" (`:235`).** My lowercase-substring alternation
over the 7 live kinds gives **23/190**, identical to the word-boundary count. Also the word-boundary
regex printed at `:235` is malformed (`(?<![A-Za-z0-9_.])k(?![A-Za-z0-9_])` — a bare `k`, not `kind`).
The load-bearing number (23/190) reproduces.

**5.7 Minor — "~20 differing data files" (`:110`).** Actually 21 common files differ (+11 only-in). Fine.

## 6. Red→green pair (required)

**Guard: `harness/prepare.py`'s corpus-digest refusal.** Exact commands and both outcomes:

```
$ (cd scratch/uver13/t/pinned && python3 harness/prepare.py); echo "exit=$?"
REFUSED: corpus digest mismatch — expected c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66, got 58b09a3cd84d3bef0e1a67abcd4445517d447709742991d8afbd56c89ff6df6a
exit=2                                            # RED
$ cp repro/encoder-crossover-190-SANITISED/harness/data/corpus.json scratch/uver13/rg-stripped/harness/data/corpus.json
$ (cd scratch/uver13/rg-stripped && python3 harness/prepare.py); echo "exit=$?"
  Candidate option: security
exit=0                                            # GREEN
```

Green also in `rg-pinned`, and regeneration re-emits the full 2,205,127 / 484,922-byte JSONL in both.
This both substantiates claim 7's mechanism (pin-induced) and corrects 5.4.

## 7. Verdict

- Claims **1, 3, 5, 6, 8, 9**: `reproduced` (numbers exact).
- Claim **2**: `reproduced` with one wrong citation (5.2).
- Claim **4**: `reproduced` in substance (`overstated` description, 5.5; 6-count slip, §1a).
- Claim **7**: `reproduced` for the refusal/exit/digests; `overstated` consequence (5.4).
- Claim **10** (ship `tree-stripped`): supported — the strip is provably dead-field, metric- and
  digest-preserving, byte-saving 39.97%, and the bij shape's own residual is 40.3% in-stimulus for 1.24%.
- No model was run by me either; every "preserved" statement above is metric recomputation from stored
  labels/results, **`unverified`** for retraining/re-rendering.
- **Read the report with §5 applied**; the hash of the file I verified is
  `13d0712ebecf77a086747115fcda7e21d989642aa8a001e5c17d7e015f338dcb` (unchanged — I did not edit it).
