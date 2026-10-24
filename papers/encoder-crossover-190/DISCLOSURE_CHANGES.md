# DISCLOSURE_CHANGES.md — what unit UPAPER1d changed in `MANUSCRIPT.md`, and why

**Scope.** This unit changed **availability and licence statements only**. No measured value, statistic,
figure, or claim about the results was altered: **`numbers_changed = 0`**. The scientific content named in the
unit card — the narrowed novelty claims, §6.6's counter-case weakness, the dropped latency claim, the
κ-is-not-IAA framing, the M12 correction and the declared primary baseline **0.6789** — is untouched.

**Definitions used for the verifier.** *Prose sentences changed* = 11 (a sentence replaced, split, or
rewritten). *Table rows repointed* = 9 (1 header + 8 data rows in §7). Line numbers are **post-edit**; the
pre-edit numbers seen by ULIC (`:562–563`, `:604–608`) had drifted because other units added §6.4–§6.6 before
this unit ran, so the pre-edit anchors are also given.

**Driving findings.** ULIC's `LICENSE_ANALYSIS.md` §8.1 items 1–4 (§8.2/§8.3 recommended the subset and the
honest reviewer-facing sentence); UREPRO's `repro/encoder-crossover-190/README.md` §5 (`harness_self_contained
= partial`), `EXCLUDED.md`, `LICENCE_TODO.md`, and `MANIFEST.json`/branch inspection.

---

## D1 — the factually wrong licence sentence (ULIC §8.1 item 4)

**Where.** `## Data and code availability`, pre-edit `:733–736`; post-edit `:732–790` (rewritten wholesale).

**From (deleted):**

> That repository is licensed **AGPL-3.0** (root `LICENSE`, GNU Affero GPL v3, 19 November 2007). **⚠ The
> paper's own licence is a separate, deliberate choice that a human must still make** — releasing the
> manuscript under a permissive licence while its supporting code and evidence are AGPL-3.0 is a
> **mismatch** that must be resolved explicitly rather than by default (`CHECKLIST.md`,
> `OPEN_QUESTIONS.md`).

**To (added, `:734–736`):**

> **The paper is public, CC BY 4.0.** By the author's decision of 2026-10-15 the manuscripts in this series are
> released under **Creative Commons Attribution 4.0 International**. The paper's own licence is therefore
> settled, and it is **not** a separate open question awaiting a human decision.

**Why.** ULIC §8.1 item 4 and §10 D1: the licence decision was **made** (CC BY 4.0, 2026-10-15). The old
sentence was *factually wrong*. The AGPL framing is **removed**, not resolved: the repo is private and the
code is not released, so there is no paper/code licence mismatch. The source repository's own `LICENSE` is
now cross-referenced as a separate, private question (`:784–788`) and **not** restated or resolved here.
Note for the verifier: the string `AGPL` no longer occurs anywhere in `MANUSCRIPT.md`, so the tokens `3.0`,
`v3`, `19` and `2007` from that parenthetical are gone. Those are licence identifiers/dates, not measured
values.

## D2 — the local-path exposure (ULIC §8.1 items 1 and 3) — the damaging one

**Where (a).** `## 7. Reproduction` opener, pre-edit `:689–692`; post-edit `:689–694`.

**From:** "Everything in this paper is re-derivable from the target repository `the read-only target repository`
(read-only) plus this workspace." — **To:** "Everything in this paper is re-derivable from the released
reproducibility subset `repro/encoder-crossover-190/` — the 190-case fixture and its schema, the evaluation
harness with its frozen inputs, the pre-registered protocols, the per-arm result records, and the
second-labeller evidence."

**Where (b).** `## Data and code availability`, pre-edit `:731–732`; post-edit `:732–752`.

**From:** "The decision fixture (`evals/fixtures/reflex-decisions.ts`), the experiment record and the 26-file
evidence tree live in the target repository `the read-only target repository`." — **To:** the released-subset bullet list
(`:740–752`): instrument + schema, harness + commands, pre-registrations, results, second-labeller evidence.

**Where (c).** §7 `Read-only discipline`, pre-edit `:722`; post-edit `:725–728`. "`the read-only target repository` was
treated as strictly read-only by this unit" → "The source repository was treated as strictly read-only".
The frozen HEAD `907fa39…36b` is kept (provenance, not a machine path).

**Where (d).** §7 source table, pre-edit `:694–703`; post-edit `:696–706`. The eight private-repository paths
were repointed to released-subset paths (`results/eval-*.json`, `harness/analyze.py`, `results/REPORT.md`,
`harness/data/lint-report.json`, `preregistration/…`, `second-labeller/{…}`). The literature-claim row keeps
its source-repository pointer and is explicitly marked "source repository, not released".

**Why.** ULIC §8.1 items 1 and 3 call this "the single strongest conflict": `the read-only target repository` is a path
on the author's own machine behind a private repo, so a reviewer concludes the work is unreproducible.
**Grep evidence:** the (now-scrubbed) absolute home-path prefix no longer occurs in `MANUSCRIPT.md`.

## D3 — §7 / Data-and-code availability rewritten to the actual subset

**Where.** §7 opener + table (`:689–706`); `## Data and code availability` (`:732–790`).

**Added:** the subset's contents by category (fixture + schema; harness + frozen `data/` + commands;
pre-registered protocols; results including per-case rows in `results/baselines.json`; second-labeller
evidence); the **honest limitation**; the provenance fact (D4); the withheld boundary (D5); and the separate,
undecided code licence (below).

**The limitation, stated accurately** (`:756–764`): `repro/encoder-crossover-190/README.md` §5 records
`harness_self_contained = partial`. The six Python steps (`prepare.py`, `train.py`, `evaluate.py`,
`analyze.py`, `defect-probe.py`, `collect.py`) **re-run from `harness/` with its bundled `data/`**; **steps
1–2** (`export-fixture.ts`, `lint.ts`) need the source repository's `scripts/run.sh` runner (`tsx`) and a
repo-shaped checkout — neither is in the subset — **but their outputs are included byte-identical**
(`harness/data/fixture-190.json`, `harness/data/lint-report.json`) and re-verified by `prepare.py`. The
manuscript now says "We do not claim full self-containment." No claim of full self-containment appears.

## D4 — harness provenance: not on trunk (UREPRO finding)

**Where.** §7 table row `:704` and `Data and code availability` `:766–771`. **New** in both.

**Statement:** the EXP#12 harness is **not on the source repository's default branch**; the experiment closed
its branch unmerged at `an unmerged development branch commit (id withheld)` (branch `EXP#12-typed-channel-comparison`,
path `tools/typed-channel/`), and that path does not exist on trunk. The **18 harness files** in the subset
were recovered **read-only from the git object store** via `git cat-file blob`.

**Verified by this unit, independently of UREPRO** (target repo, read-only):

- `git merge-base --is-ancestor an unmerged development branch commit (id withheld) HEAD` → **NOT ANCESTOR**
- `git branch -a --contains an unmerged development branch commit (id withheld)` → `EXP#12-typed-channel-comparison`, `remotes/origin/EXP#12-typed-channel-comparison`
- `git ls-tree -r --name-only HEAD -- tools/typed-channel/ | wc -l` → **0** (not on trunk)
- `git ls-tree -r --name-only an unmerged development branch commit (id withheld) -- tools/typed-channel/ | wc -l` → 42 (full branch path; the
  released harness is the 18-file Python/TS subset)
- `git log -1 --format='%s' an unmerged development branch commit (id withheld)` → `exp(EXP#12): CLOSE - the typed-channel comparison, method preserved on the closed branch`
- `find repro/encoder-crossover-190/harness -type f | wc -l` → **18**

## D5 — withheld by policy

**Where.** `Data and code availability` `:772–781`.

**States plainly:** the **agent-state kernel / runtime** (`src/**`, `kernel/**`) is not released; **no model
weights** are released (the three arms are **public** checkpoints fetched at run time — `answerdotai/ModernBERT-base`
Apache-2.0, `microsoft/deberta-v3-base` MIT, `sentence-transformers/all-mpnet-base-v2` Apache-2.0 — and no
weight file exists in the source tree); the source repository's 26-file evidence tree is not released; the
full boundary is `repro/encoder-crossover-190/EXCLUDED.md` — **15 exclusion classes** (summarised, not
reproduced). Reproduction needs the fixture and the harness, not the kernel, weights, or training pipeline.

## D6 — the code licence is separate and undecided (do **not** re-litigate)

**Where.** `Data and code availability` `:782–790`. **New** paragraph.

**States:** the **content** (fixture and paper material) is CC BY 4.0; the **code** licence is a *different*
question, intended to be source-available under a separate, not-yet-chosen licence (commercial use paid,
personal/hobby use free) whose terms are to be disclosed in pieces. It is **not** the paper's licence and
**not** the source repository's `LICENSE`. Pointer given to `repro/encoder-crossover-190/LICENCE_TODO.md`, and
publication of the code is flagged as gated on that decision. **No licence was chosen or decided here.**

---

## Verification actually run (commands and results)

- `grep -n "<scrubbed absolute-path prefix>\|AGPL\|must still make\|is a \*\*mismatch\*\*" MANUSCRIPT.md` → **NONE**
- `grep -n "released reproducibility subset\|an unmerged development branch commit (id withheld)\|harness_self_contained\|EXCLUDED.md\|LICENCE_TODO"` →
  hits at `:689`, `:704`, `:757`, `:767`, `:778`, `:788`
- target HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; `git status --porcelain` identical
  before and after (4 untracked paths, attributed to the unrelated concurrent session, per `EXCLUDED.md` §5)
- `ls "docs/research/EXP#12-evidence" | wc -l` (in the target) → **26**, so the retained "26-file" count is
  accurate
- all headline numerics re-present in the edited file (0.3474, 0.4526, 0.2911, 0.6684, **0.6789**,
  κ 0.9014/0.9053, 0.3252/0.8837/0.9140/0.3526, 4.167e−09, 0.1595, 0.616/27/90, `39+27+90+34=190`)
  Note 2026-10-16: this disclosure list is the dated record of that pass and is kept as written. The release
  tree's neutralisation has since moved two of its entries — routeA κ 0.3252 → 0.3249 (exact
  0.3248813212427869) and AB mutual agreement 0.3526 → 0.3684; the remaining numerics are unchanged.

**Residual recorded gap (not fixed by this unit).** A few remaining source-repository identifiers survive in
the manuscript as provenance (not as reproducibility pointers): `docs/DECIDER_STACK_DECISION.md` §11.6 and
commit `ad301ae1a5472fa7bd27807fdc7bb15d35f81988` (§6.4 and the §7 table row marked "not released"), and the
unqualified `REPORT.md:104`/`:189` citations, which now resolve against `repro/encoder-crossover-190/results/REPORT.md`.
