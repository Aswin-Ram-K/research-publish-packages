# UFIXPKG5 — genericise the released payload's residual provenance references

**Purpose.** Orchestrator-decided policy: the parent project is referenced *generically only*, never by
its own names or paths. Earlier units genericised most of `scratch/uneutral10/package`; this unit closes
the residual class (exact private-tree paths, the tail document ids `D50`/`D51`/`D38-P03-comparison.md`,
private relative links) and adjudicates the two verbatim quotations.

**Write paths (declared).** `scratch/uneutral10/package/**`, `papers/encoder-crossover-190/**`,
`strategy/RELEASE_BUILD_3.md`, `orchestration/units/UFIXPKG5.md`,
`orchestration/handoffs/UFIXPKG5.json`, `scratch/ufixpkg5/**`.
**Hard bound:** 25 tool calls. **Backup:** `scratch/ufixpkg5/before/package/` (taken first).

## What changed (before → after, every anchor count-asserted before writing)

33 substitution anchors over 8 files; second-pass fixes were 4 more (count asserted = 1 each).
Tag/descriptor vocabulary used is the payload's own — existing tags `G46`/`G47`/`G48`/`G51`/`G52` and
coarse kind-descriptors already phrased in-payload ("the read-only target repository", "the authoritative
sanitised copy"). **No new tag was minted.** Proposed-only (not used): `G59` for the `tools/P03/` tool tree,
`G60` for the generated-corpus note (`P04`) — both need orchestrator approval.

| file | bytes before → after | substitutions |
|---|---|---|
| `MANIFEST.json` | 11213 → (regen) | 8: `tools/typed-channel/...` path dropped; 5× `repository/G52/eval-*.json` + `G52/REPORT.md` → `the read-only target G52 (<kind>)`; `EXP#12-…md` path → repo; `G52/baselines.json` → `G52 (evidence directory, item withheld)` |
| `preregistration/EXP12-typed-channel-comparison-prereg.md` | 8975 → 8997 | 6: `D38` header/H1 dropped; `docs/research/experiments/D38-P03-comparison.md` → repo; `D38-P03-comparison` branch → "the pre-registration branch"; `[…](../../D51)`/`[…](../../D42)` → generic kind-descriptors |
| `second-labeller/EVIDENCE.md` | 22398 → 22500 | 6: 4× `repository/P05` → "…'s instrument source"; `docs/research/P01:47` → "…'s findings register:47"; `` outside `docs/research/` `` → "…'s documentation tree" |
| `second-labeller/OWED_CORRECTIONS.md` | 9185 → 9716 | 24: `repository/P05`/`…/P05` ×8; `docs/research/P01:47` ×2 + bare `P01:47` ×1; `D50:279–281` ×3; `../D43 section 5` ×10 |
| `second-labeller/RUN.json` | 12309 → 12351 | 4: `register_quote` attribution; 2× `repository/P05`; `strategy/` → "the strategy tree"; then bare `P01:47` |
| `results/REPORT.md` | 28050 → 28424 | 14: `docs/research/P04-evidence/decider-rows.jsonl` ×3, `docs/research/l1-head-to-head.jsonl` ×1, `docs/research/D49` ×2, `tools/P03/` ×8 → "…'s tool tree/"; then H1 `# D38 — results` → `# P03 results` |
| `results/baselines.json` | 57319 → 57339 | 2: `docs/research/…` ×2 |
| `fixture/DECISION_CASE_SCHEMA.ts` | (comment-only) | 2: `<target-repo>/P05 (HEAD 907fa39)` → repo; dangling `fixture/D02` → "the shipped fixture data" |

Before/after digests for every touched file: `scratch/ufixpkg5/apply_edits.log.json` (per-edit old/new and
per-file sha256/bytes), written by `scratch/ufixpkg5/apply.py` (two-pass: validate all anchors, then write;
a first run failed closed on `../D43 section 5` = 10 not 8 and wrote nothing).

**No new number introduced.** Every replacement removes a name/id/path or restores a coarse phrase; each
kind-descriptor was read from `scratch/ufixpkg3/neutralise.py`'s existing mapping (G46/G47/G48/G51/G52,
held outside the payload) or quoted from the payload's own text.

## Job 2 — the quotations, adjudicated

* **(a) keep, generic attribution — `second-labeller/RUN.json:109` `register_quote`.** The quoted text is
  the finding itself (`"F-EXP11-11 | answer not in option set was 0.00 % at every round in both models …
  does not exist at baseline"`), a measured statistic already published, quoted to show that the two
  checks are *distinct* (fixture authoring vs model-emitted answers). Methodology, not mechanism. The
  quote's **words are unchanged**; only the attribution changed:
  `docs/research/P01:47` → `the read-only target repository's findings register:47`.
* **(a) keep, generic attribution — `results/REPORT.md:121` (and `:269`).** On inspection this is a
  *citation*, not a verbatim quotation: `"The primary is \`probabilities[choice]\`, on three grounds:
  \`docs/research/D49\` defines it verbatim; …"`. The reasoning (which calibration convention is native and
  which reproduces the published ECE figures) is methodology and is the package's own published argument.
  Kept verbatim; only the cited-document reference was genericised to
  `the read-only target repository's scoring-convention note`. **Close call → safer option taken**: the
  sentence reveals no mechanism detail beyond the convention already named in the same file.
* **(b) neutralised — `second-labeller/OWED_CORRECTIONS.md`, 10×** `[withheld rationale quote — see
  ../D43 section 5]`. The rationale text is *already withheld*; the only leak was the relative path into the
  private tree. → `the withheld rationale note, section 5`. No content dropped.
* **(c) already removed, unchanged** — `fixture/*.ts` `/** Withheld in this sanitised release. */`,
  `EVIDENCE.md:214` "the recorded rationale (withheld in this sanitised release)".
* **(a) = ordinary English, KEPT — `verify/recompute-claims.py:2` `SANITISED`.** It is an adjective for the
  tree, names no directory, document id or filename, and the same sense already occurs in-payload as
  `staged from G47 (the authoritative sanitised copy)` and `the shipped sanitised metrics.json`. It is also
  the only MANIFEST entry with `identical_to_source: true`, so editing that file would falsify the entry.

## Proof (measured)

* **No published number moved.** `verify/recompute-claims.py`, `second-labeller/parse_fixture.py`,
  `second-labeller/compare.py`, run from both `scratch/ufixpkg5/before/package/` and the edited tree,
  before and after: **6/6 EXIT=0**. `recompute-claims.py` printed its verdict line both times:
  `ALL PUBLISHED NUMBERS REPRODUCED: True` / `VERDICT: PASS`, with the fixture-correctness digest
  `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` unchanged.
* **`MANIFEST.json` regenerated** by the package's documented procedure
  (`python3 scratch/ufixpkg3/rebuild_manifest.py`, which replays `scratch/urecut1/build.py:94-137` and
  preserves each entry's `source`): `files_on_disk: 29`, `counts.files: 29`, `files[]: 28`,
  `entries_with_source: 28`, `entries_with_source_sha256: 20`, **`counts.bytes_total: 830738`**.
  Generator's own `INDEPENDENT CHECK: PASS`; my independent check agrees — path-set equality
  (disk == entries + self) `True`, `sum(files[].bytes) == counts.bytes_total` `True`, 0 sha256/bytes
  mismatches, `manifest_self` recomputed by the generator.
  **No published number depends on the byte total:** `grep -rn 'bytes_total\|829574\|830665\|830738\|841687'`
  over `papers/encoder-crossover-190/` → **0 hits**.
* **`submission/main.tex` is generated, not hand-edited.** `python3 scratch/uprep1/md2tex.py` run twice
  (both EXIT=0); run1 vs run2 **BYTE_IDENTICAL**, and both equal the pre-existing `main.tex`
  (`PRE_vs_RUN1=BYTE_IDENTICAL`, 83826 B) — the paper text was not changed by this unit.
* **Residual scan, all forms: 0 leak-class hits.** Whole token, bare/unprefixed form, case variants
  (`docs/research`/`Docs/Research`/`DOCS/RESEARCH`), regex fragments (`D3x`,`D4x`,`D5x`,`P0x`,`S0x`,`Fxx`,`Gxx`),
  `G52/`, `EXP#12`, `EXP#11`, `../D4`, `../../D`, `<target-repo>`, `fixture/D02`, `strategy/`,
  `tools/typed-channel`, `l1-head-to-head`, `decider-rows`, `UNEUTRAL`, `urecut1`, `worktrees`.
  The scan was run *after* each edit round, and caught three of my own misses (a bare `D38` in
  `results/REPORT.md:1`, a bare `P01:47` in `second-labeller/RUN.json:107`, and
  `G52/baselines.json` in `MANIFEST.json`) plus one hidden behind the generator's redaction display.

### What this method would **not** catch (measured boundary)

1. **Bare internal labels with no directory component**, deliberately retained: `P04` ×10, `P05` ×7,
   `P01` ×1, `D-067` ×5, `D01`–`D19`, `D42`, `D43`, `D48`, `D14`, `S02/S04/S07`, `F01`–`F56`, `G01`–`G58`
   (e.g. `F54` ×1333, `G11` ×703). They are the payload's own tool/instrument/case names and deleting
   them needs tags that do not exist on disk; the card forbids quietly minting one. **`P04` and `P05` are
   the two provenance-shaped survivors** and are proposed for `G60`/reuse of `G51` respectively.
2. **Names split, re-cased, escaped or paraphrased** — a token scan sees tokens. A leak that says
   "our earlier comparison note" without reusing any name is invisible to it.
3. **Legitimate shipped paths that look like leaks** (`fixture/fixture-190.json`, `results/eval-*.json`,
   `second-labeller/labelsB.json`) — indistinguishable by string search, deliberately kept (the manifest
   is fail-closed over them).
4. **The paper tree's own 21 `docs/research/...` occurrences** (in `REFS.md`, `CLAIMS.md`, `MANUSCRIPT.md:301`,
   `EVIDENCE_NOTES.md`, `CHECKLIST.md`, `LICENSE_ANALYSIS.md`, `DISCLOSURE_CHANGES.md`, `GAPS.md`, and the
   generated `submission/main.tex:146`) — outside this unit's payload scope; `LICENSE_ANALYSIS.md`
   documents some of them as deliberate disclosure decisions. **Reported, not edited.**

## Inferred / not determined

* **Inferred:** the remaining bare `D0x`/`P0x` labels are accepted payload vocabulary, because
  `scratch/ufixpkg3/neutralise.py` (the prior sweep's mapping, held outside the payload) maps only
  path-shaped and unit-name tokens, never a bare `D0x`/`P0x`.
* **Not determined:** whether the orchestrator wants those bare labels removed too — that is a policy
  call beyond this card, and it needs the new tags proposed above.
