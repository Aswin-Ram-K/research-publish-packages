# RESIDUAL_TRIAGE_3 — URESID3 diagnosis

Scope: paper #3's emitted tree. Diagnosis only; nothing fixed, nothing shipped. Unit card
`orchestration/units/URESID3.md`; handoff `orchestration/handoffs/URESID3.json`.
All work under `scratch/uresid3/**`. `/home/zer0null/Duval` untouched (no read, no git).

## 0. The emitted tree and the gate (measured)

- Payload: `scratch/uneutral10/package` — 29 files (`find … -type f | wc -l`).
- Emitted tree: `scratch/urelease3/dest/research-publish-packages` — **39 non-.git files**
  (`find … -type f -not -path "*/.git/*" | wc -l` → 39). Package body = 29;
  frame adds `COMMERCIAL.md CONTRIBUTING.md LICENSE README.md .gitignore gate.sh vocabulary/`
  (5 flagged frame files + gate).
- The exclusion gate is `scratch/urelease3/dest/research-publish-packages/gate.sh` (POSITIVE
  vocabulary allowlist; `english.txt code.txt public.txt` for prose/source, `data.txt` added for
  `.json/.jsonl`). Its output is **`scratch/urelease3/gate.json`** (1,146 lines).
- Command that produced it: `scratch/urelease3/gate.json:1145`
  `GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s).`
  and `:1144` `{"flagged": 1133, "printed": 1133, "by_class": {"prose-source": 774, "data": 359}, …}`.
- **Measured, exact:** the gate prints every counted token with `file:line`. Parsing all
  `file:line: token  [reason]` lines in `scratch/urelease3/gate.json` gives
  **1,133 flagged lines over 303 distinct token strings** (saved, with every `file:line`, in
  `scratch/uresid3/flagged.json`). This is the accounting below — not a keyword pass.

## Part A — the residual's true composition

### A.1 Top 60 by occurrence count, each placed

Bucket key: **(a)** ours/should not ship · **(b)** mechanism vocabulary · **(c)** released-schema
vocabulary · **(d)** ordinary English / third-party.

| n | token | bucket | note |
|---|---|---|---|
| 56 | `workspace` | d | stimulus/third-party prose |
| 44 | `ECE` | b | metric name (Expected Calibration Error) |
| 38 | `locator` | d | third-party stimulus term |
| 32 | `redacted` | d | ordinary English |
| 28 | `pre-registered` | d | ordinary English |
| 24 | `licensor` | d | package-frame legal |
| 23 | `kappa` | b | statistic |
| 21 | `pre-registration` | d | ordinary English |
| 20 | `MCP` | d | third-party (Model Context Protocol) |
| 19 | `UEXP` | **a** | internal unit name |
| 17 | `decider` | b | mechanism |
| 17 | `UFIX4` | **a** | internal unit name |
| 17 | `UVER3` | **a** | internal unit name |
| 14 | `decider-4b` | b | mechanism/baseline name |
| 12 | `fh` | d | tool-source local variable |
| 12 | `workspace.` | d | stimulus + punctuation |
| 12 | `relist` | d | ordinary English |
| 12 | `mtime` | b | machinery term |
| 10 | `URECUT1` | **a** | internal unit name |
| 10 | `labelsB.json` | c | shipped record file name |
| 10 | `uncompacted` | b | machinery state term |
| 10 | `unscoped` | b | machinery state term |
| 10 | `kk` | ? | could not place (see A.4) |
| 9 | `psi` | b | McNemar statistic |
| 9 | `argmax` | b | machinery |
| 9 | `acc` | b | machinery |
| 8 | `workspace/MODULE_4` | d | stimulus |
| 8 | `src/` | d | stimulus |
| 8 | `typecheck` | d | stimulus |
| 8 | `locator.` | d | stimulus + punctuation |
| 8 | `softmax` | b | machinery |
| 8 | `REC` | ? | could not place |
| 7 | `MDE` | b | machinery (min detectable effect) |
| 7 | `imajev-4b` | b | baseline/codename |
| 7 | `imajev` | b | codename |
| 6 | `substring` | b | code |
| 6 | `unescape` | b | code |
| 6 | `predict_proba` | b | code |
| 5 | `recomputed` | b | tool output word |
| 5 | `McNemar` | b | statistic |
| 5 | `jload` | b | code |
| 5 | `routeA` | c | schema key |
| 5 | `bwrap` | d | third-party (bubblewrap) |
| 5 | `workspace/src/x.ts` | d | stimulus |
| 5 | `workspace/src/y.ts.` | d | stimulus |
| 5 | `deciders` | b | mechanism |
| 5 | `arity` | b | machinery |
| 5 | `routeB-blind-model` | c | schema/record value |
| 5 | `cuda` | d | third-party |
| 4 | `//github.com/Aswin-Ram-K/research-publish-packages` | d | third-party URL |
| 4 | `Aswin-Ram-K` | d | third-party (author) |
| 4 | `//polyformproject.org/licenses/noncommercial/1.0.0` | d | third-party licence URL |
| 4 | `perCase` | c | schema key |
| 4 | `pmf` | b | code |
| 4 | `rec` | b | code |
| 4 | `decider-4b-exp11-reproduction` | c | `baselines.json` key |
| 4 | `workspace/MODULE_1` | d | stimulus |
| 4 | `workspace/MODULE_7` | d | stimulus |
| 4 | `semanticCalls` | c | schema key |
| 4 | `workspace/package.json` | d | stimulus |

**Bucket counts over the top 60 (measured, arithmetic closes):**
- **(a)** 4 distinct / **63** occurrences
- **(b)** 26 distinct / **255** occurrences
- **(c)** 6 distinct / **32** occurrences
- **(d)** 24 distinct / **331** occurrences
- could-not-place 2 distinct / **18** occurrences (`kk` 10, `REC` 8)
- 63+255+32+331+18 = **681** = the top-60 total. The 243-token tail (ranks 61–303) carries the
  remaining **452** occurrences.

### A.2 Bucket (a) enumerated exactly across all 1,133 (measured)

Unit / handoff names — **80 occurrences, 17 distinct**:
`UEXP` 19, `UEXP.` 1, `UFIX4` 17, `UFIX4.` 1, `UVER3` 17, `URECUT1` 10, `UCORR1` 3, `UCORR3` 3,
`UCORR3.` 1, `UVER2/UCORR2` 2, `UVER2` 1, `UCORR2` 1, `UTOOL1` 1, `UNEUTRAL10` 1, `UNEUTRAL9` 1,
`UTS1/papers` 1, `scratch/urecut1/build.py` 1.

Working-directory artefacts — **29 occurrences, 20 distinct**:
`docs/research/P04-evidence/imajev-rows.jsonl` 4, `imajev-rows.jsonl` 2,
`repository/docs/research/P04-evidence/imajev-rows.jsonl` 1,
`experiments/second-labeller-190/labelsB.json` 3, `second-labeller/labelsB.json` 1,
`packages/exp12-encoder-crossover/README.md` 1, `repro/encoder-crossover-190` 1,
`repro/encoder-crossover-190-SANITISED/` 1,
`repro/encoder-crossover-190-SANITISED/verify/recompute-claims.py` 1,
`docs/evidence/selfbuild/relay-outbound-2026-10-13.txt` 3, `evals/fixtures` 1, `evals/fixtures.` 1,
`repository/evals/fixtures/reflex-decisions.ts` 2, `12-evidence/eval-deberta-v3-base.json` 1,
`12-evidence/eval-modernbert-base.json` 1, `12-evidence/eval-setfit-mpnet.json` 1,
`results/eval-deberta-v3-base.json` 1, `results/eval-modernbert-base.json` 1,
`results/eval-setfit-mpnet.json` 1, `.worktrees/` 1.

**Bucket (a) total = 109 occurrences, 37 distinct.**

Every `file:line` and its surrounding line for the 17 unit-name tokens (measured, from the emitted
package; the two reading-relevant surfaces):

- `MANIFEST.json:3` `"purpose": "reduced public package cut by URECUT1",`
- `MANIFEST.json:5` `"generated_by": "URECUT1 build.py (scratch/urecut1/build.py)",`
- `MANIFEST.json:9` `"amended_by": "URECUT1 (2026-10-16): … UNEUTRAL10 (2026-10-16): title-case component name folded onto its existing generic tag; MANIFEST regenerated from disk.",`
- `MANIFEST.json:19,28,37,46,190,199,253` `"source": "authored by the URECUT1 build (no target source)",`
- `verify/recompute-claims.py:4` `ONE PURPOSE: show that the numbers UTS1/papers list are still there after the redaction, computed`
- `verify/recompute-claims.py:115` `# UNEUTRAL9: replacing the last system identifiers with Gnn tags moved two published`
- `second-labeller/EVIDENCE.md:1` `# EVIDENCE — second-labeller-190 (unit UEXP)`
- `second-labeller/EVIDENCE.md:198` `option set, the recorded rationale and the flags). Adjudication is by UEXP, which wrote the`
- `second-labeller/EVIDENCE.md:279` `declaration** **[corrected by UFIX4 per UVER3]**:`
- `second-labeller/EVIDENCE.md:310` `for the 190-case fixture that underlies candidates #3, #4, #5 and #10", and records (UCORR1,`
- `second-labeller/parse_fixture.py:2` `"""UEXP step 2-3: parse the reflex-decisions fixture into cases.json + blinded_cases.json`
- `second-labeller/parse_fixture.py:16` `SRC = os.path.join(HERE, os.pardir, "fixture", "reflex-decisions.ts")  # UTOOL1: shipped fixture; was "reflex-decisions.sandbox.ts" (not in the ship set)`
- `second-labeller/OWED_CORRECTIONS.md:7` `**Compiled by:** UFIX4, 2026-10-15, from the UVER3 work order (`strategy/D59_3.md`) and`
- `OWED_CORRECTIONS.md:8` `the prior units named per item (UVER2/UCORR2, UEXP, UCORR1).`
- `OWED_CORRECTIONS.md:10` `**Verification rule used.** Each item was **re-opened in the raw corpus text by UFIX4** and re-measured`
- `OWED_CORRECTIONS.md:13` `refuted.** (Item 6 was appended by UCORR3, 2026-10-15, re-verified raw; items 1–5 were verified by UFIX4.)`
- `OWED_CORRECTIONS.md:16` `by UFIX4 per UVER3, marked `[corrected by UFIX4 per UVER3]`.)`
- `OWED_CORRECTIONS.md:25` `- **Established by:** UVER2 / UCORR2 (per the UVER3 work order). **Re-verified by UFIX4:**`
- `OWED_CORRECTIONS.md:43,55,69,82,86` `**Established by:** UEXP (…)` … `by UVER3 (report item 8a–8d)`
- `OWED_CORRECTIONS.md:44` `by UVER3 (report item 8a, line 78); **re-verified raw by UFIX4** (text quoted above read directly from`
- `OWED_CORRECTIONS.md:56,70,87` `by UVER3 (report item 8b/8c/8d, line 79/80/81); **re-verified raw by UFIX4**.`
- `OWED_CORRECTIONS.md:101` `- **Established by:** UCORR3. **Re-verified raw:** `DEFECT-EVIDENCE.json``
- `OWED_CORRECTIONS.md:106` `carried in the workspace at `strategy/D60` A3 and §E, which UCORR3 **did** correct in`
- `OWED_CORRECTIONS.md:113` `| # | Corpus path:line | Defect | Correct value | Established by | UFIX4 re-verified |`
- `OWED_CORRECTIONS.md:115,116,117,118,119,120` table rows `| 1 | … | UVER2/UCORR2 | …`, `| 2–5 | … | UEXP; UVER3 8a–8d | …`, `| 6 | … | UCORR3 | …`
- `second-labeller/RUN.json:3` `"_unit": "UEXP",`
- `RUN.json:100,104,116` `… [corrected by UFIX4 per UVER3] …` (three keys: corpus_documentation_detail, _corrected, reproducibility)
- `RUN.json:108` `… imajev-rows.jsonl holds 3,690 valid rows (verified by UFIX4)."`
- `RUN.json:127` `… that the corpus recorded as absent (UCORR1, 2026-10-14). …`

Also in bucket (a): `parse_fixture.py:16` cites `reflex-decisions.sandbox.ts`; `OWED_CORRECTIONS.md`
cites `strategy/D59_3.md`, `strategy/D60`, `strategy/D52:46`, `the read-only target repository/…`
(those path tokens are further bucket-(a) artefacts not all separately counted by the gate's
tokeniser).

### A.3 Buckets (b)/(c)/(d) — what I can state exactly

- **(b) mechanism vocabulary** — top-60 slice 26 distinct / 255 occurrences (A.1). Full-tree tokens
  clearly of this class include `ECE`, `kappa`, `psi`, `MDE`, `McNemar`, `softmax`, `argmax`,
  `predict_proba`, `decider*`, `imajev*`, `mtime`, `uncompacted`, `unscoped`, `recomputed`.
- **(c) released-schema vocabulary** — top-60 slice 6 distinct / 32 occurrences; further named:
  `requestedCapabilities` 4, `answerInOptionSet` 3, `routeA_agrees_with_record` 2,
  `bad_option_arity` 2, `bad_arity` 2, `dup_ids` 2, `dup_q_exact` 2, `rec_lbl` 4, `instr` 4,
  `strat` 4, `case_logits` 1, `setfitRefitNote` 1, `routeB_primary` 1, `routeA_agrees_with_routeB` 1,
  `agrees_with_routeB` 1, `disagreements_count_routeB` 1, `disagreements_where_routeA_backs_record` 1,
  `labelsB` 2. Partial total ≈ 60–70.
- **(d) ordinary English / third-party** — the largest class by both tokens and occurrences
  (top-60 slice 331 occurrences). Includes the licence/attribution strings (`Aswin-Ram-K`,
  the two URLs), third-party tool words (`MCP`, `bwrap`, `cuda`, `Yoyodyne`, `GLiNER`, `GSM8K`,
  `answerdotai/ModernBERT-base`, `sentence-transformers/all-mpnet-base-v2`,
  `microsoft/deberta-v3-base`), and the stimulus text (`workspace/…`, `locator`, `typecheck`).

### A.4 Could not place (named)

`kk` (10, all in one file), `REC` (8, one file), `fh` (12 — Python file-handle local),
`relist` (12 — reads as the English verb but appears in code context), `imajev` (7) vs
`imajev-4b` (7) — codename vs published baseline name cannot be separated without the source tree.
**Not determined:** a full per-bucket partition of the 243-token tail (452 occurrences); it is
enumerated token-by-token in `scratch/uresid3/flagged.json` but not individually adjudicated.

## Part B — is (a) removable? **Yes, free for every checked number (measured).**

Method: copy the emitted package to `scratch/uresid3/copy/package` (baseline) and
`scratch/uresid3/after` (mutated). Mutation = 12 literal string replacements covering every
unit/handoff name in A.2 plus `scratch/urecut1/build.py` → `PROCESSLAMBDA` and
`UTS1/papers` → `PROCESSMU` (`URECUT1`,`UNEUTRAL10`,`UNEUTRAL9`,`UFIX4`,`UVER3`,`UVER2`,
`UCORR1`,`UCORR2`,`UCORR3`,`UTOOL1` → `PROCESS*`; longest-first so prefixes cannot mis-match).
Then re-ran the three tools in both trees and diffed.

| tool | baseline exit | mutated exit | stdout |
|---|---|---|---|
| `verify/recompute-claims.py` | **0** | **0** | `diff` → **IDENTICAL** |
| `second-labeller/parse_fixture.py` | **0** | **0** | `diff` → **IDENTICAL** |
| `second-labeller/compare.py` | **0** | **0** | `diff` → **IDENTICAL** |

Commands: `python3 verify/recompute-claims.py`, `python3 second-labeller/parse_fixture.py`,
`python3 second-labeller/compare.py`, each run from the package root, stdout+stderr captured to
`scratch/uresid3/{base,after}.*.txt`; `diff scratch/uresid3/copy/base.*.txt scratch/uresid3/after.*.txt`.

**Statement: the change is free.** No published value moves — the internal identifiers sit in
prose, in `MANIFEST.json` metadata, and in code comments/docstrings that no shipped tool reads.
**Caveat (inferred, not measured):** editing those files invalidates their recorded
`sha256`/`bytes` in `MANIFEST.json` (the manifest is a fail-closed listing of on-disk files), and
the gate would still fail — after removing bucket (a) it would flag roughly 1,133 − 109 = **1,024**
tokens (not re-run here).

## Part C — the two discrepancies

### C.1 The three digests (measured)

| digest | what it actually is | path | size |
|---|---|---|---|
| `a15224bada6950ad27f693acd2287dec564134419061baa475f6716d2db3852e` | **the shipped JSON fixture** — and the only one of the three that is "the fixture" | `scratch/uneutral10/package/fixture/fixture-190.json` and `scratch/urelease3/dest/research-publish-packages/packages/encoder-crossover-190/fixture/fixture-190.json` (identical bytes) | see MANIFEST / measured below |
| `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` | **the as-audited INSTRUMENT source**, not the fixture: the pre-sanitisation `reflex-decisions.ts` | `repro/encoder-crossover-190/fixture/reflex-decisions.ts` | 145,031 bytes |
| `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` | **not a file digest at all** — a digest over the fixture's *correctness projection* `[[id, correct, len(options)], …]` | computed at runtime, stored nowhere | n/a |

Evidence:
- `sha256sum fixture/fixture-190.json` → `a15224ba…52e` (run in both the payload and the emitted package).
- `sha256sum repro/encoder-crossover-190/fixture/reflex-decisions.ts` → `076164ac…b4796`.
  `repro/encoder-crossover-190-SANITISED/fixture/reflex-decisions.ts` → `751dc007…` (the redacted
  copy — matches `repro/encoder-crossover-190-SANITISED/INTEGRITY.md:92`).
- The **shipped** instrument is a third value: `scratch/uneutral10/package/fixture/reflex-decisions.ts`
  and the emitted tree both → `369159b03aa67f1571517ea2a9c3c460d218ee832d00e8ddd4928e5e6da0f78d`.
  *(Dated record, measured at report time: UFIXPKG10 later removed five comments from the shipped instrument,
  so it is now `89e77a8e…e169`, 81,439 B — `scratch/uneutral10/package/MANIFEST.json:75-76`.)*
  So **no file in the shipped package hashes to `076164ac…`**.
- `c7696edc…` is printed by `verify/recompute-claims.py:140-142`:
  `hashlib.sha256(json.dumps([[c["id"], c["correct"], len(c["options"])] for c in fixture], separators=(",", ":")).encode()).hexdigest()`
  — i.e. a digest of the *trimmed per-case correctness triples*, not bytes. `grep -rn c7696edc`
  over the whole workspace (excluding `.venv`) → **zero hits**; it exists only in the tool's stdout.
- **Which digest a package reader should be given:** `a15224ba…52e` for
  `fixture/fixture-190.json`. `076164ac…b4796` must be labelled **instrument
  (`reflex-decisions.ts`, as-audited) sha256**, and the package must not carry it as "the fixture
  sha256" because the shipped instrument is now `89e77a8e…e169` (81,439 B); the pre-clean-up value was
  `369159b0…` (81,284 B) — corrected 2026-10-16 by UFIXPKG10 (`scratch/uneutral10/package/MANIFEST.json:75-76`).
- **The document currently giving the wrong one:** `papers/encoder-crossover-190/CLAIMS.md`
  - `:39` `| fixture sha256 unchanged by the second labeller | before = after = `076164ac…b4796`; sandbox copy identical to target |`
  - `:46` `| fixture sha256 | `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` | `analysis.json` | `.instrument.instrument190Sha256` |`
  Both rows label it "fixture sha256"; `:46`'s own source column (`.instrument.instrument190Sha256`)
  betrays that the value is the **instrument** digest. `076164ac` is also carried by
  `second-labeller/RUN.json:8-10` (`fixture_sha256_before/after`, `sandbox_sha256`),
  `preregistration/EXP12-…-prereg.md:56`, and `results/REPORT.md:5` — same mislabel.
  *(Dated note, UFIXPKG12 2026-10-16: the `CLAIMS.md` rows quoted above are report-time snapshots. UFIXPAPER3
  re-labelled `:46` to `instrument sha256` (noting `label corrected 2026-10-16`), UFIXPKG4 renamed the
  `second-labeller/RUN.json` keys to `instrument_sha256_*` (see `strategy/RELEASE_BUILD_3.md`), and UFIXPKG10 replaced
  the shipped-copy digest with `89e77a8e…e169` (81,439 B).)*

### C.2 Why a failed row does not produce a non-zero exit (measured, code-quoted)

Constants: `verify/recompute-claims.py:41` `0.3526: "second-labeller A/B mutual agreement"` (in
`CLAIMS`), and `:122` `0.3526: ("A/B mutual agreement", "papers/encoder-crossover-190/CLAIMS.md:109",`
inside `PUBLISHED_STALE`.

Exit decision: **`:143` `sys.exit(0 if ok else 1)`**. `ok` is touched in exactly two places:
- `:105-106` `hit = abs(have - want) <= 5e-4` / `ok &= hit` (loop over `CLAIMS`, guarded by
  `:103` `if want in got:` — `got` is built at `:95` with keys `0.3474, 0.4526, 0.2911, 0.6684, 0.6789` only);
- `:132-133` `hit = abs(have - want) <= 5e-4` / `ok &= hit` (loop over `CLAIMS`, guarded by
  `:130` `if want in sb:` where `sb` at `:124-127` is keyed by the **tree** values, e.g.
  `met["passes"]["labelsB.json"]["AB_mutual_agreement"]`, which is `0.3684210526315789` — so the
  published key `0.3526` is **not in `sb`** and is skipped).

The reporting loop that prints `reproduced=False` is `:135-138`:
`for pub, (lab, cite, tree_v) in PUBLISHED_STALE.items():` / `hit = abs(tree_v - pub) <= 5e-4` /
`print(f"    {lab}: published={pub:<8} tree={tree_v!r:<22} reproduced={hit} cite={cite}")`.
**It contains no `ok &=` and no `sys.exit`** — `hit` is used only in the print.

**Therefore: both.** The A/B row is *by construction outside* the "preserved" set (it is only ever
read from `PUBLISHED_STALE`, and `sb` is keyed on the tree value, so neither `ok`-bearing loop can
compare `0.3526`), **and** the guard does not cover `PUBLISHED_STALE` at all. It is not a
comparison bug — the design is "published deltas are declared, not enforced" (`:118-119` comments).
The defect is the *message*: `:139` prints
`ALL CLAIM NUMBERS PRESERVED: True` while `:138` prints
`A/B mutual agreement: published=0.3526   tree=0.3684210526315789     reproduced=False`, and
`:143` exits 0 — so "preserved" silently means "all *recomputed-when-possible* claims preserved".
Measured drift: published `0.3526` vs tree `0.3684210526315789` = 67/190 vs 70/190, i.e. 3 cases,
caused by the rename changing route-A tokenisation (`:115-119`).

## Measured vs inferred vs not determined

- **Measured:** 39-file emitted tree; 1,133 flagged lines / 303 distinct tokens; top-60 partition
  (a 4/63, b 26/255, c 6/32, d 24/331, unplaced 2/18); bucket (a) = 109 occurrences / 37 distinct
  with all `file:line`; Part B exit codes 0/0/0 and byte-identical stdout; all three digests and
  their paths/sizes; `recompute-claims.py` exit logic lines.
- **Inferred:** `MANIFEST.json` sha256/bytes go stale after an (a) edit; gate would still flag
  ≈1,024; bucket (c) full count ≈60–70.
- **Could not determine:** `kk`, `REC` (and less confidently `fh`, `relist`, `imajev`); a complete
  per-bucket partition of the 243-token tail.
