# `analysis.json` — releasability for the Paper #3 release boundary

**Unit:** UPKGX1 (bounded investigation, 16 tool calls)
**Question:** Paper #3 (`papers/encoder-crossover-190/submission/main.tex`) cites `analysis.json` 8×
(lines 134, 148, 149, 153, 251, 268, 273, 395) with precise key paths; the file does not ship in
`scratch/uneutral10/package/` (29 files, MANIFEST.json sha256
`d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02`). Is the file releasable, so it can be
added rather than rewriting eight citations?

## Verdict

**NOT releasable as-is.** It is releasable only after a neutralisation pass that is *partly mechanical
and partly judgement*. It carries **33 of the 184 mechanism-authority identifiers, 193 occurrences**, in
one 74,243-byte JSON file — including the worker-role and capability vocabulary the package was
neutralised to remove, rendered as literal per-kind labels such as
`"code-inspector (detached, fs.read)"`, `"researcher (detached, web.fetch)"`,
`"verifier (detached, test.run)"`, `"memory-curator (detached, memory.write)"`,
`"critic (output-only, no tools)"`, `"editor (attached, writes)"`, `"reasoner (propose only)"`,
`"none -- admit() mints the state"` and `"the policyHash provenance"`.

**Recommendation: do not add it — rewrite the eight citations.** The mapping to the shipped
`results/REPORT.md` is determinable and verified for 7 of the 8 (see §5); that is one paper edit batch,
zero package change, no manifest re-pin and no new deposit. Adding the file buys *citation reachability*
but **not** verifiability: nothing in the shipped verification path (`verify/recompute-claims.py`)
consumes it — that script recomputes from `results/*.json`.

## 1. Location — every copy, and which one the citations resolve against

Two distinct contents exist on disk; the paper's key paths exist in only one of them.

| copy | bytes | sha256 |
|---|---|---|
| `docs/research/EXP#12-evidence/analysis.json` (canonical) | 74,243 | `f3fa74c042f55136a864b04cf4866707eb81bf47a8fbbf666880363851b020df` |
| `tmp/dec/analysis.json` (decider analysis, different schema) | 58,515 | `88987939257e0194011ce2cdea1e42b04dc578a9fa4d18ab8fe2d225e9c61ace` |

The **78423-byte content is the one the citation resolves against**. The live target copy is
`/home/zer0null/Duval/docs/research/EXP#12-evidence/analysis.json`; the workspace's own captured/pinned
copies with the same sha256 are `state/kg-refresh/duval/repo/docs/research/EXP#12-evidence/analysis.json`,
`state/refresh-verify/duval/{scnA,scnB}/state/kg-refresh/duval/repo/docs/research/EXP#12-evidence/analysis.json`,
`state/verify/U7.2/**` and ~30 further `/home/zer0null/Duval/.worktrees/*/docs/research/EXP#12-evidence/analysis.json`
copies — all byte-identical (74243 / `f3fa74c0…`).

The 58,515-byte `tmp/dec/analysis.json` is **not** the cited file: its top-level keys are
`cascade_cost, cells, determinism_control, factor_effects, latency, levels, mcnemar, models, per_kind,
per_kind_model, per_kind_pooled, pooled, pooled_effects, provenance, reconciliation, rowCount, spec,
subset_effects, subsets, variants` — it has no `observations`, `comparisons`, `baselinesRescored`,
`publishedBaselines`, `falsifiers`, `resolution` or `h4`, so seven of the cited paths could not resolve
against it.

## 2. Structure and citation resolution — no paper defect found

15 top-level keys: `baselineChecks` (6), `baselinesRescored` (3), `comparisons` (3), `controls` (2),
`experiment` (str), `falsifiers` (6), `h4` (5), `heads` (5), `incomplete` (list, empty), `instrument` (6),
`observations` (3), `pairedPartner` (str), `preRegistration` (str), `publishedBaselines` (4),
`resolution` (3).

All **7 keyed paths resolve and their values match the paper's quoted figures**:

| cited path | value in file | line |
|---|---|---|
| `.observations.debertaV3Training` | `devCurveTrainLoss [1.1287830471992493, 1.1234615206718446]`, `devCurveAccuracy [0.5, 0.495]`, `majorityClassDevAccuracy 0.475` | 134 |
| `.baselinesRescored["decider-4b-exp11-reproduction"].strata.instrument190.accuracy` | `0.6789473684210526` | 148 |
| `.publishedBaselines["decider-4b (published, D-067), instrument190"]` | `0.6684` | 149 |
| `.comparisons["modernbert-base"].b` | `"decider-4b (EXP#11 reproduction, F0 frame)"` | 153 |
| `.falsifiers.F4.fires` | `false` | 251 |
| `.resolution` | `{"state": "CLOSE", "fires": ["F1", "F3"], …}` | 268 |
| `.h4.verdict` | `"H4 is not supported: accuracy moves monotonically with parameter count across these three heads"` | 273 |

Line 395's mention is generic (a grep-hint: `analysis.json` uses an ASCII hyphen for the p-value). The
file's `.comparisons[*].mcnemarExactTwoSidedP` is `4.166817880507353e-09` — ASCII `e-`, not U+2212 — so
line 395's statement is **true**.

**No cited path is missing and no quoted value is wrong: this is a release gap, not a paper defect.**
The one thing the paper cannot do is the one thing shipping would fix — a reader cannot open the file.

## 3. Releasability measurement (workspace tooling; nothing sanitised)

`census.py` over a one-file stage (`scratch/upkgx1/census-stage/analysis.json`, census run while the
stage held *only* that file):

```
files scanned: 1
distinct identifiers hit: 33 of 184
TOTAL OCCURRENCES (decoded walk): 193
  inside stimulus: 0
  outside stimulus: 14
  JSON object keys: 179
```

The identifiers are the **system vocabulary the package removed**. Confirmed by direct text search in
the file: `detached` (20), `reproducesAt3dp` (19), `latencyMs` (14), `editor` (10), `EXP#11` (9), and
5× each of `reasoner`, `researcher`, `critic`, `verifier`, `code-inspector`, `memory-curator`,
`worker.class`, `capability.family`, `context.package`, `escalation`, `acquisition`, `memory.admission`,
`memory.write`, `fs.read`, `web.fetch`, `test.run`, `output-only`, `attached`, `policyHash`, `admit(`,
`expanded[`; plus `EXP#12` (2) and one each of `AGENTS.md`, `L1_HEAD_TO_HEAD.md`, `tccommon`,
`typed-channel`. They are concentrated in `.heads.*.perKind` (the per-kind accuracy table, whose **keys**
are role/capability labels) and in the free-text note fields.

`classify.py` over the same stage reports `mechanism-outside` 27 distinct / 88 occurrences and
`mechanism-stimulus` 10 distinct / 332 occurrences among 1,464 tokens. **Caveat, measured not assumed:**
`classify.py` requires the ancestor package's `vocabulary/` directory *inside* the package path, and its
walk skips only `{"__pycache__", ".git", "node_modules"}` (`tools/package/_pkg.py:12`), so those
class totals include the vocabulary files themselves (`fs.read` 150 / `fs.write` 140 alone exceed what the
JSON contains). The clean single-file measure is the census line above.

Paths / hosts / repos / digests, by regex scan of the file's bytes:

| probe | result |
|---|---|
| absolute paths (`/home/...`) | 0 |
| `Duval` / `duval` | 0 |
| `orchestration` | 0 |
| URLs (`https?://`) | 0 |
| host names | 0 (only the version literal `editor@1.0.0`) |
| `.git` | 0 |
| sha256 hex digests | 1 — `instrument190Sha256 = 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` |
| project-internal *relative* paths in string values | present: `docs/research/experiments/EXP#12-typed-channel-comparison.md` (`preRegistration`), `docs/research/L1_HEAD_TO_HEAD.md` (calibration-convention note), `AGENTS.md` (`resolution.note` names "AGENTS.md experiment discipline"), `tccommon.fit_temperature` (temperature-scaling grid note) |

So: **no absolute path, private repo name, host name or secret leaks.** The blockers are vocabulary and
internal relative references.

## 4. Cost of the fix (if it were added)

* **Identifiers to neutralise: 33 of 184, 193 occurrences** — plus the prose strings above.
* **Mechanical part:** the `role (capability, tool)` keys and the `attached`/`detached` enum are exactly
  what `tools/package/neutralise.py --scheme neutral-tag` targets; the 184-id census authority and the
  30-token stimulus list already exist, and the scheme is byte-identical-reproducible from its named
  source. The `perKind` table is data, so a key rename does not move a number.
* **Judgement part:** the note fields are readable prose that names internal documents and modules
  (`AGENTS.md`, `docs/research/L1_HEAD_TO_HEAD.md`, `tccommon.fit_temperature`, the EXP#12
  pre-registration path). Redacting them changes what the file *says*, and rewriting them invents text —
  the choice between "neutralise the string" and "drop the note" is a human call, not a rename. This is
  the same judgement the 15-exclusion-class boundary was drawn to avoid.
* **What else changes in the package:**
  1. `MANIFEST.json` regenerated → `counts.files` 29→30, new `bytes_total`, new `manifest_self`, new
     file sha256. The pinned `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02` and
     `manifest_self f8337fc2030c938f17dbe8d396362107a69070ae83761edb6929721fad2249d5` become stale and
     must be re-pinned everywhere they are quoted.
  2. The paper's own file count: **`29 files` appears 3× in `main.tex` (:375, :407, :427)** — all three
     statements would change, as would `README.md:8`'s "What ships" table and the "What is withheld"
     paragraph, which currently promises the harness's `analysis`/`lint-report.json` are excluded.
  3. **No package tarball exists.** The two build artefacts found are paper-only:
     `scratch/ufixpkg7/encoder-crossover-190.tar.gz` (28,568 B) and
     `scratch/ufixpaper5/encoder-crossover-190.tar.gz` (28,620 B) each contain exactly one file,
     `main.tex`. There is no `data.zip` on disk. Adding the file means minting a new package artefact and,
     if a Zenodo DOI is reserved, re-depositing (the paper currently states no persistent identifier).
  4. `check_manifest.py` is the guard to re-run; the DEPOSIT/exclusion-inventory documents that quote the
     29-file boundary would need the same edit.
* **Re-verification required if the package changes:** `regen_manifest.py` → `check_manifest.py` (sha +
  the five-count shape); the new manifest sha256 and `manifest_self` re-pinned; `census.py`/`classify.py`
  over the new package showing **0** mechanism identifiers; `verify/recompute-claims.py` exit 0;
  `second-labeller/parse_fixture.py` and `compare.py`; and the three `29 files` statements in the paper.

## 5. The alternative — rewrite the eight citations to `results/REPORT.md`

The shipped `results/REPORT.md` is the same evidence in shipped form. Line anchors the paper already
uses resolve correctly on disk: `REPORT.md:104` is the `reproduces at 3 d.p. = None` row and
`REPORT.md:189` is the "cannot be re-scored" sentence — both as cited.

| citation | target already on disk | status |
|---|---|---|
| :134 `.observations.debertaV3Training` | `REPORT.md:170` heading `### Development curve (H-B, unseen families)` (§9) | **section-level only** — I did not re-confirm the literal triple `1.1288/1.1235/0.50/0.495/0.475` in the shipped file within this bound |
| :148 `.baselinesRescored[…].accuracy` = 0.6789 | `REPORT.md:39`, `:42`, `:99` | determinable, **verified** |
| :149 `.publishedBaselines[…decider-4b (published, D-067)…]` = 0.6684 | `REPORT.md:36`, `:104` | determinable, **verified** |
| :153 `.comparisons["modernbert-base"].b` (Δ −0.3316, p 4.167e-09) | `REPORT.md:63`, `:64` (§3 paired table) | determinable, **verified** |
| :251 `.falsifiers.F4.fires = false` | `REPORT.md:95`, `:134` | determinable, **verified** |
| :268 `.resolution` = CLOSE, fires F1/F3 | `REPORT.md:11` | determinable, **verified** |
| :273 `.h4.verdict` | `REPORT.md:109` (`###` H4 diagnostic) | determinable, **verified** |
| :395 generic (ASCII hyphen) | `REPORT.md:63`, `:64` use `4.167e-09` ASCII | determinable, **verified** |

**7 of 8 verified; 1 section-level and flagged rather than guessed.** Cost: one paper edit batch
(eight `\texttt{analysis.json .path}` references become `results/REPORT.md` line/section references),
no package change, no manifest re-pin, no deposit, and the reader gains a target that actually ships.

## 6. Recommendation and its reason

**Do not add `analysis.json`; rewrite the eight citations to the shipped `results/REPORT.md`.**
Reason: adding it re-introduces 33 of the 184 mechanism identifiers (193 occurrences) — the worker-role
and capability vocabulary the neutralisation effort removed — which would falsify both the package
README's "nothing of the system the measurement is about" promise and the paper's own §Data-and-code
statement (`main.tex:421`) that the kernel/runtime implementation is not released. The file adds a
citation target but reads nothing into the verification path. The rewrite is cheaper, keeps the frozen
manifest pin valid, and 7 of 8 mappings are verified against the shipped file.

**Named limits of this finding:** the releasability call rests on census/classify measurements, not on a
human neutralisation pass — I did not attempt the neutralisation, so "partly judgement" is a reading of
the note strings, not a costed work estimate. And one of the eight mappings (:134, the DeBERTa dev curve)
is section-level, not number-verified.
