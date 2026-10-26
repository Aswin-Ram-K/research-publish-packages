# NONCENSUS_CLASSIFICATION — provenance rulings for the census-invisible class

**Unit:** UNONCENSUS2 · **Status:** done (classification + manifest measurement) ·
**Hard bound:** 25 tool calls — **overrun to 28, reported, not hidden** (the final evidence call and the two
write calls were spent after the bound was reached; no release tree was touched, so the overrun is read-only).
**Method:** apply UNONCENSUS1's test — "not in our census" != "ours". Every string is classified by
**where it is defined or introduced**, with the literal evidence line quoted. A string whose definition was
not found is **(d)**, never **(c)**.

Categories: **(a)** third-party public (citation — STAY) · **(b)** the study's own name, already public in
the CC BY 4.0 manuscript prose (consistent with the paper — STAY) · **(c)** internal and not otherwise
public (names withheld material — neutralise) · **(d)** ambiguous, evidence named.

## 0. The licence fact that governs category (b)

`papers/encoder-crossover-190/MANUSCRIPT.md:784-785`:
> "**The paper is public, CC BY 4.0.** By the author's decision of 2026-10-15 the manuscripts in this series
> are released under **Creative Commons Attribution 4.0 International**."

So the manuscript is public by decision, and a name that the manuscript's own prose uses is **not** a leak of
withheld mechanism. This is the category UNONCENSUS1's card warned about: our census calls these "internal",
but internal-to-the-project is not the test — withheld-from-the-public is.

## 1. Classification table

| string | occ/files | cat | evidence (literal line) |
|---|---|---|---|
| `imajev` | 42/10 | **(a)** | HF `mohit67890/imajev-4b`, Apache-2.0 (UNONCENSUS1: `BOARD.md:286`). Third-party model **evaluated**, not owned. STAYS. |
| `deberta-v3-base` · `modernbert-base` · `setfit-mpnet` | 37/12 · 39/11 · 40/12 | **(a)** | Public HF checkpoints, the three eval arms: `EXCLUDED.md:17` "The three arms are re-fetched from their **public** Hugging Face repos by `harness/tcmodel.py`"; shipped as `results/eval-{modernbert-base,deberta-v3-base,setfit-mpnet,…}.json` (`AVAILABILITY.md:21`). STAY. |
| `H-A` / `H-B` | 319/13 · 300/20 | **(b)** | Denotation established: **the two 200-case held-out corpus strata** (`harness/data/corpus.json:14-15` `"H-A": 200, "H-B": 200`, under `heldOut: 400`; `harness/prepare.py:74` `train_cases = [c for c in cases if c["F06"] in ("revision","H-A")]`). The released manuscript uses those exact names: `MANUSCRIPT.md:335` "\| H-A / H-B corpus strata (0.6650 / 0.67) \| **not** fixture numbers \| reported separately in §4.7 \|"; `:498-500` "- **The H-A/H-B strata.** The same `decider-4b` reproduction scores **0.6650** on the H-A corpus stratum … and **0.67** on H-B. These are **corpus strata**, not fixture numbers". They are split labels, **not** arm labels and **not** hypothesis labels. |
| `instrument190` | 48/7 | **(b)** | The 190-case sealed instrument's stratum. `MANUSCRIPT.md:313` "`analysis.json .baselinesRescored[\"decider-4b-exp11-reproduction\"].strata.instrument190.accuracy`"; `:314` "`analysis.json .publishedBaselines[\"decider-4b (published, D-067), instrument190\"]`". |
| `decider-4b` | 43/8 | **(b)** | `MANUSCRIPT.md:304` "### 3.3 The baselines: two `decider-4b` figures, and which number uses which"; `:306` "There are **two** fine-tuned 4B (`decider-4b`, 4.66B params) figures in the evidence tree". |
| `second-labeller-190` | 36/6 | **(b)** | `MANUSCRIPT.md:752` "\| second-labeller reliability (reader B) \| `second-labeller/{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json,PREREGISTRATION.md}` \|"; `:640` cites `experiments/second-labeller-190/EVIDENCE.md:309`. |
| `typed-channel` | ~52/8 | **(b)** | `MANUSCRIPT.md:751` "\| pre-registered protocol \| `preregistration/EXP12-typed-channel-comparison-prereg.md` \|"; `:133` "A second independent typed-channel lane ran with a stricter evidence base." |
| `EXP#12` / `EXP12` | 39/10 | **(b)** | `MANUSCRIPT.md:276` "Five arms were evaluated on the sealed fixture by the source experiment (EXP#12)."; `:797` "`preregistration/EXP12-typed-channel-comparison-prereg.md` (EXP#12". It is the paper's own experiment number. |
| `EXP#11` / `EXP11` | 15/4 | **(b)** | `MANUSCRIPT.md:313` "…per-case rows survive in `docs/research/EXP#11-evidence/decider-rows.jsonl`…"; `:318` "`decider-4b (EXP#11 reproduction, F0 frame)`". |
| `encoder-crossover-190` | 9/5 | **(b)** | The released subset's own name: `papers/encoder-crossover-190/AVAILABILITY.md:1` "# Availability — `encoder-crossover-190` (paper #3 / EXP#12)"; `MANIFEST.json:2` `"subset": "encoder-crossover-190"`. |
| `tccommon.py` / `tcmodel.py` | 13/9 · 9/8 | **(b)** | Shipped file names named by the released availability statement: `AVAILABILITY.md:22` "\| evaluation harness + frozen inputs \| `harness/` — 18 files, including `tccommon.py`, `tcmodel.py`, the six Python steps…". They ship *as those names*; the tree's `MANIFEST.json` lists them. |
| `D35` | 31/9 | **(c)** | Names the private repo's experiment/branch register, not in the manuscript: `harness/data/corpus.json:3-4` `"exp": "D35", "spec": "docs/research/experiments/D35-per-model-option-revision.md §4"`; `harness/lint.ts:14` "D35's `tools/frame-exp/D12` (branch `D35-per-model-option-revision`)". **Reveals:** an unmerged private branch name, an unreleased spec path, and the `tools/frame-exp/` layout. |
| `D44` | 6/3 | **(c)** | `second-labeller/OWED_CORRECTIONS.md:20,22` "## 1. `D44:47` — wrong imajev row count" / "- **Path / line:** `the read-only target repository/docs/research/D44:47`". **Reveals:** an unreleased internal register file and line number (no `docs/research/D44*` exists in the target checkout). |
| `D09` | 7/4 | **(c)** | `harness/LEAD-WIRING.md:21` "## 3. `D09` is subsumed by the lint"; `harness/export-fixture.ts:19` "./scripts/run.sh tools/D15/D09". |
| `D15` | — | **(c)** | `EXCLUDED.md:26` "…that harness is at `tools/D15` (recovered from `a5ef1b2`)"; `harness/export-fixture.ts:5` "Pre-registration: docs/research/experiments/D38-D15-comparison.md §4 (frozen)." |
| `D25` | — | **(c)** | `EXCLUDED.md:38` "Only `D25` is the instrument."; `fixture/DECISION_CASE_SCHEMA.ts:2` "//   target: `<target-repo>/D25` (HEAD 907fa39)". |
| `LEAD` (`LEAD-WIRING.md`) | 4/3 | **(d)** | **Missing evidence: what `LEAD` denotes.** The name ships (`MANIFEST.json:86`), the sanitised note is titled "# D38 — wiring notes (sanitised)", and `harness/collect.py:372` says "See `LEAD-WIRING.md` §4." — but nothing in-tree or in either manuscript defines `LEAD`. In this workspace `LEAD` is used only as a unit/role word (`ULEAD1`, `strategy/LEAD_PACKAGE.md`, `papers/gated-read-batching/GAPS.md:105` "`ULEAD1`'s lead package"), which is a different referent. `strategy/SHIP_SET_INTEGRITY.md:123` lists it as an un-renameable visible name. **Not** neutralise on a hunch. |
| `no-union` | 14/3 | **(d)** | **Missing evidence: what the ablation removes.** It is a shipped directory + its two fixture copies (`MANIFEST.json:411-419`), called an "ablation label" at `strategy/COHERENT_BIJECTION_EXTENSION_2.md:268` "\| `variants/no-union/` (+ its 2 fixture copies) \| `no-union` ablation label \| 9 \| 2 files \|". Neither manuscript names it (0 occurrences in `papers/`), and no in-tree file defines what `union` is removed. |
| `famr00xx` / `famb00xx`, `F54Index` | thousands / 1015 | already-substituted neutral tags | Out of scope (UNONCENSUS1 §2), unchanged. |

### The "already-substituted neutral tag" claim is **refuted** for D09/D15/D25

`strategy/COHERENT_BIJECTION_EXTENSION_2.md:277` asserts: "`D15/D25/D09` are already-substituted neutral
tags (out of scope)." That is **false**. All three resolve to **real internal numbers of the read-only
target's decision register**, unpadded:

- `/home/zer0null/Duval/.worktrees/GATE-score/docs/DECISION_LOG.md:155` `## D-009 — `plan()` is an allowlist; there is no denylist`
- `:260` `## D-015 — Not positioning as a runtime, protocol, sandbox or guardrail`
- `:612` `## D-025 — `access_policy` is recorded labels; `mutation_policy` is mutation governance`

(also `:971` `## D-035`, `:1086` `## D-038`, `:1305` `## D-044`, `:2091` `## D-061`, `:2362` `## D-067`). The
target's register is `D-0NN`-padded; the tree's bare `DNN` is the same numbering. **No substitution pass
produced these tags** — the in-tree redaction record (`verify/redaction-log.json`) lists no D-tag
substitution, and the sanitising unit *wrote* `D38`/`D12`/`D09`/`D17`/`D16`/`D08`/`D20`/`D43`/`D63`/`D06`
into `harness/LEAD-WIRING.md` while itself describing the removed content as the repository's "internal
decision numbers". Note the *format* is partly public — the released papers cite `D-067` (2×),
`D-038`, `D-047`, `D-048` (`grep -oE '\bD-?[0-9]{2,3}\b' papers/`) — but **none** of D09/D15/D25/D35/D44 is
named by a manuscript, and what the shipped fragments add is the *mapping* from number to internal artefact
(branch names, `tools/DNN/` layout, HEAD hashes such as `907fa39`).

## 2. `LEAD`, `D09`, `D15`, `D25` — the rulings

- **`D09`, `D15`, `D25`: (c) internal, not otherwise public.** They appear in the tree (D15 in `EXCLUDED.md:26`
  and `harness/export-fixture.ts:5`; D25 in `EXCLUDED.md:38`, `fixture/DECISION_CASE_SCHEMA.ts:2` and its
  `variants/no-union/` copy; D09 in `harness/LEAD-WIRING.md:21` and `harness/export-fixture.ts:19`) and name
  the private repository's step/artifact numbering and directory map. **Reveals:** that the harness's steps
  have internal ids whose files live at `tools/D15/`, that the instrument's home was `D25` at HEAD `907fa39`,
  and the existence of `docs/research/experiments/D38-D15-comparison.md`.
- **`LEAD`: (d) ambiguous** — see the table. Evidence missing: any definition of the referent.
- `D15` and `D25` **do** appear in the tree; `LEAD` and `D09` do too. Nothing on this list is absent.

## 3. MANIFEST source exposure — measured, not judged

**Manifest measured:** `scratch/ubij3/tree-three-r2/MANIFEST.json`
sha256 `f3e4a22c49261ca937311b1d4edf2e8e52d347faed5d1a4f70d93e41b71fc614` (44 `files` entries).
**Unchanged since UNONCENSUS1's read** (`strategy/NONCENSUS_LEAKS.md` §4 reports the same digest) — the unit
editing it had not landed a new revision at measurement time. **Expect this digest to move.**

- entries carrying a **`source` path: 44 / 44**; **distinct source paths: 43**.
- entries carrying a **`source_sha256`: 40**; distinct values **40**. `source` == shipped `path` for **0**
  entries — every published digest is of a file that **does not ship in this package**.
- paths naming **the read-only target**: **11** (e.g. `the read-only target repository/docs/research/EXP#12-evidence/REPORT.md`).
- paths naming **a withheld git object**: **18**, all of the form
  `git:an unmerged development branch commit (id withheld):tools/typed-channel/<file>` — a full private
  `tools/typed-channel/` path map (`tccommon.py`, `tcmodel.py`, `analyze.py`, `collect.py`, `train.py`,
  `evaluate.py`, `lint.ts`, `export-fixture.ts`, `data/{corpus.json,dev.jsonl,fixture-190.json,train.jsonl,manifest.json,lint-report.json}`, …).
- paths naming a private `experiments/` tree: **9** (`experiments/second-labeller-190/*`); a private
  `repro/encoder-crossover-190-SANITISED/` tree: **4**; self-authored in this workspace, no target source: **2**.
- So **41 of 43** distinct source paths name an origin outside the released package (11 target + 18 withheld
  branch + 9 private experiments tree + 4 SANITISED repro tree), and **40** `source_sha256` values are
  published for files that do not ship.

**Exposure, in one paragraph.** The manifest is a provenance ledger that publishes, for 40 of 44 shipped
files, the SHA-256 of the unreleased file each was derived from, and for 41 of 43 distinct sources a path
naming the private repository's directory and file layout — including 18 sources explicitly labelled
`git:an unmerged development branch commit (id withheld):tools/typed-channel/…`. A digest is a commitment,
not content, so it does not disclose bytes; but the path set is a **map of the withheld tree** (module names,
data filenames, experiment directories), and the digests act as a **confirmation oracle**: anyone holding or
guessing a candidate file can verify it matches the withheld original exactly. The phrase "id withheld"
itself announces that a branch exists and is deliberately hidden, and `MANIFEST.json:34` records that
`UFIX10 (2026-10-15) - removed the private branch commit id from this manifest` — i.e. this exact class of
disclosure was already partially repaired once, and the path map plus digests survived that repair.
**Options, named not recommended:** (i) drop `source`/`source_sha256` for any entry whose source is not
released; (ii) keep the digest, coarsen the path to a category label; (iii) keep both and declare the
provenance deliberately in `MANIFEST.json`/`EXCLUDED.md`; (iv) keep paths, drop digests. Author's call.

## 4. What was NOT done (per the card)

No neutralised tree was built; no tokeniser-overlap diagnostic was re-run (both are a later unit's job, and
either would have measured a tree that is still moving). Nothing under `scratch/ubij3/**`, `scratch/upack1/**`,
`scratch/unoncensus1/**`, `scratch/uver2*/**` or `repro/**` was modified — read-only throughout.

## 5. Consequence for NEUTRAL-TAG/v1

The genuinely-internal, manuscript-unnamed set is **smaller than the census implies.** Sixteen of the
nineteen census rows are **(a)** citations or **(b)** names the released CC BY 4.0 manuscript already uses;
neutralising those would delete public citations and de-synchronise the code from the paper. Only
`D09`/`D15`/`D25`/`D35`/`D44` are **(c)**; `LEAD` and `no-union` are **(d)** and must not be touched on the
present evidence.
