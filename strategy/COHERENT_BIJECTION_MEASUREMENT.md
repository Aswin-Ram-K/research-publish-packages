# COHERENT BIJECTION — MEASUREMENT (UBIJ1)

**Question.** `tree-bij` (`strategy/CPRIME_MEASUREMENT.md`) was *not* recommended because it is
incoherent: `scratch/uneutral3/bij.py` deliberately skips `.py` / `.sh` / `.bash` and `verify/**`, so the
data speaks the new vocabulary while the tooling speaks the old one and looks the data up by names it no
longer uses (308 tooling occurrences). This unit asks whether the **coherent** shape — tooling renamed in
lockstep with the data and the `.ts` sources — is achievable, and measures it.

## 0. Verdict

**Ship-able: YES.** The one-vocabulary tree (`scratch/ubij1/tree-one`) builds, is byte-for-byte
idempotent, runs the shipped tooling with the same exit codes as `tree-bij`, and reproduces **every**
published number exactly — while being **smaller** than `tree-bij` and **materially below** both
comparators:

| shape | bytes (44-file set) | decoded residual (184-id census) | + short code layer | complete decoded total |
|---|---|---|---|---|
| `tree-stripped` | 3,096,483 | 9,247 | 3,676 | 12,923 |
| `tree-bij` | 3,057,949 | 5,384 | 3,676 | 9,060 |
| **`tree-one` (coherent)** | **3,057,815** | **5,364** | **3,676** | **9,040** |

Residual movement: **−20** on the frozen census (`5,384 → 5,364`), **−20** on the complete decoded total
(`9,060 → 9,040`), **−134 bytes** vs `tree-bij`. The in-stimulus floor (**2,171**) is unchanged, as
required. Every `tree-one` figure is taken from the pristine build `scratch/ubij1/tree-one-r2` (the second
of the two byte-identical builds), **not** from the working copy that `run_diags.sh` later instrumented —
see §7 for why that distinction matters.

**One scope caveat, stated up front.** The frozen census method cannot see the *short* kind-code layer
(`K01…K10`): the identifier list `scratch/uagnostic1/census.tsv` contains **no** K-codes
(`grep -cE '(^|\t)K0[1-9](\t|$)' scratch/uagnostic1/census.tsv` → `0`), yet 3,676 such occurrences exist
in **every** shape, identical in `tree-stripped` and `tree-bij`. They are **entirely outside the
stimulus** (0 inside, in all three trees) and are opaque codes, not project identifiers. So the coherent
tree is one-vocabulary with respect to the *renamed* (project-identifier) vocabulary; the pre-existing,
already-neutral code layer is shared identically by data, `.ts` and tooling. This is measured and
reported in §6 rather than hidden.

**Precise statement if a stricter reading is required:** if "one vocabulary" is taken to mean the short
code layer must also be folded into the new namespace, that is **not** done and is **not** blocked by
anything mechanical — it is out of the bijection's rename set by construction. What must then be accepted
today is a residual of **5,364** census occurrences (**9,040** including the code layer), versus 9,247 for
the shipped `tree-stripped`.

## 1. What was built

`scratch/ubij1/bij_one.py` — a self-contained coherent bijection. It re-implements `bij.py`'s rename
(discovery of the live taxonomy names, `sha256("BIJ/v1\0"+name)` ordering → `N01…N10`, word-bounded
substitution with JSON/JSONL prose masking so route A's stimulus is never rewritten) and **removes the
skip list**: the same substitution is applied to the tooling in the same single pass, so every name a
script uses to look something up is renamed together with the name it looks up.

Two mechanisms protect coherence:

1. **Prose masking.** 1,639 pinned prose values (1,774 mask needles, one per JSON representation found in
   the tree) are replaced by sentinels before substitution and restored after, so a taxonomy name that
   occurs inside a `question` / `options` / `situation` value is never touched.
2. **Prose-integrity check.** Every masked prose value is compared before/after; the build aborts if any
   byte moved. Result: `prose-integrity failures: none`.

Exact build command (exit 0):

```
python3 scratch/ubij1/bij_one.py scratch/ubij1/tree-one
```

Build output (verbatim):

```
tree:   scratch/ubij1/tree-one
kinds discovered from the live corpus: 10 -> N01..N10
pinned prose values masked: 1639 (1774 needles)
files changed by class: {'ts': 3, 'tooling': 2, 'data': 15, 'prose': 4}
prose-integrity failures: none
map_shipped: false
```

File counts: the emitted tree holds the **same 44 text files** as `tree-stripped` / `tree-bij` (that is
the comparison set used everywhere below; verified `44/44` present by `kcensus.py`). Renaming touched
**24** of them: 3 `.ts` (2 copies of the fixture `.ts` + the schema), 2 tooling
(`harness/tccommon.py`, `second-labeller/parse_fixture.py`), 15 data, 4 prose.

`diff -rq scratch/uneutral3/tree-bij scratch/ubij1/tree-one` → **exactly 4 files differ**:
`fixture/reflex-decisions.ts`, `variants/no-union/files/fixture/reflex-decisions.ts`,
`harness/tccommon.py`, `second-labeller/parse_fixture.py`. **Every JSON/JSONL data file is byte-identical
to `tree-bij`.** The tooling edits:

* `harness/tccommon.py` — the alias table is the only place the tooling stores taxonomy names: its two
  docstring examples and its 4 alias entries are renamed on both sides where both sides are mapped names,
  so the alias relation is preserved under the same mapping. One entry keeps a bare, unmapped value (see
  §8, row `routing`).
* `second-labeller/parse_fixture.py:49` — one docstring example string.
* each `.ts` fixture copy, line 377 — one explanatory comment.

## 2. Proof by running (not by argument)

All commands run **inside** `scratch/ubij1/tree-one` unless stated. Driver:
`bash scratch/uneutral3/run_diags.sh one scratch/ubij1/tree-one` (exit 0) with full log at
`scratch/ubij1/diags-tree-one.log`.

| # | command | exit | output |
|---|---|---|---|
| 1 | `python3 -m compileall -q harness second-labeller verify` | **0** | (silent) |
| 2 | `python3 -c "import json; ..."` over `harness/data/train.jsonl`, `dev.jsonl`, `second-labeller/disagreements.jsonl` | **0** | `train.jsonl: 800 records, 0 bad; sha256 e81baca922b0b44e` · `dev.jsonl: 200 records, 0 bad; sha256 4162971988fb8c35` · `disagreements.jsonl: 18 records, 0 bad; sha256 fa83ee3ff4b4a842` |
| 3 | `python3 second-labeller/parse_fixture.py` | **0** | `stderr=[]`; `ids_missing: []`, `ids_extra: []`, `labelable: 190`, `duplicate_ids: []`, `bad_option_arity: []` |
| 4 | `python3 second-labeller/compare.py` | **0** | `stderr=[]`; routeA + routeB blocks below |
| 5 | `python3 verify/recompute-claims.py` | **0** | arms table + `CLAIMS CHECK (tolerance 5e-4)` |
| 6 | `python3 harness/prepare.py` | **2** | `REFUSED: corpus digest mismatch — expected c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66, got 47fb4a509843aef4d1732d16bb503df97b2fa6cb9e06575c99a013742e301a0d` |

**Nothing failed.** No tool was blocked by the rename. `prepare.py` exits **2 in every shape including
`tree-stripped`** — it is the pre-existing corpus-digest pin, explicitly out of scope for this unit, and
**unchanged** by the rename (its own digest is computed from pinned data, which is byte-identical).

## 3. Metrics — measured, not expected

Every column below is reproduced from the run in §2; the "known" column is the card's/CPRIME's published
value. **No value moved.**

| metric | source command | known | measured in `tree-one` | ✓ |
|---|---|---|---|---|
| routeA ties | `parse_fixture.py` + `compare.py` | 120 | 120 | ✓ |
| routeA agreement | `compare.py` | 0.34210526315789475 | 0.34210526315789475 | ✓ |
| routeA kappa | `compare.py` | 0.32520740993294694 | 0.32520740993294694 | ✓ |
| routeA exact_index | `compare.py` | 65 | 65 | ✓ |
| routeA zero_score | `compare.py` | 41 | 41 | ✓ |
| routeB agreement | `compare.py` / `metrics.json routeB_primary` | 0.9052631578947369 | 0.9052631578947369 | ✓ |
| routeB kappa | idem | 0.9013584840356494 | 0.9013584840356494 | ✓ |
| routeB exact_index | idem | 172 | 172 | ✓ |
| routeB disagreements | idem | 18 | 18 | ✓ |
| AB mutual agreement | idem | 0.3526315789473684 | 0.3526315789473684 | ✓ |
| arm modernbert-base | `verify/recompute-claims.py` | 0.347368 | 0.347368 (recomputed 0.347368) | ✓ |
| arm deberta-v3-base | idem | 0.347368 | 0.347368 (recomputed 0.347368) | ✓ |
| arm setfit-mpnet | idem | 0.263158 | 0.263158 (recomputed 0.263158) | ✓ |
| arm majority-class | idem | 0.452632 | 0.452632 (recomputed 0.452632) | ✓ |
| arm shuffled-label | idem | 0.231579 | 0.231579 (recomputed 0.231579) | ✓ |
| arm decider-4b-repro | idem | 0.678947 | 0.678947 | ✓ |
| closed-vocabulary kappa | `metrics.json stratification.closed_subset.labelsB.kappa` | 0.8837… | 0.8837023738280471 | ✓ |
| roster kappa | `metrics.json …roster_and_bespoke_subset.labelsB.kappa` | 0.9140… | 0.9139973672663448 | ✓ |
| 2×2 | `verify/recompute-claims.py` | 39 / 27 / 90 / 34 | `both=39 headOnly=27 deciderOnly=90 neither=34 sum=190` | ✓ |

Two further identity checks, both new evidence for this unit:

* `scoring-projection sha256 = 620e4a07f8add8c5c8073017d4148d1fa542bea1c711a02f9f98fd9193e8e50b` —
  **identical** on `tree-one` and on a read-only copy of `tree-bij` (`scratch/ubij1/bij-ref`). The
  projected stimulus is bit-identical across the two shapes.
* `second-labeller/cases.json` sha256 = `9c0ca33869037a2bb2bf8507b5df8ec575a4d3e6e6f26f54b592c4cd3ba9c96d`
  — **identical** in both trees (`190` cases). The derived labeller corpus did not move.
* `fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`.

**Deliberately not cited as proof:** `recompute-claims.py` prints `ALL CLAIM NUMBERS PRESERVED: True`, but
per the unit card that script does **not** recompute route A. Route A was re-established by re-running
`parse_fixture.py` + `compare.py` (rows 1–5 of the table).

## 4. Census — same method that produced 16,813 / 9,247 / 5,384

Decoded-value walk (`scratch/ubij1/census_one.py`), **not** a raw-line scanner. Method fidelity is
demonstrated by reproducing the two published comparator numbers exactly:

```
python3 scratch/ubij1/census_one.py scratch/uneutral3/tree-stripped   -> TOTAL 9247   (inside 2171 / outside 5701 / keys 1375)
python3 scratch/ubij1/census_one.py scratch/uneutral3/tree-bij        -> TOTAL 5384   (inside 2171 / outside 2044 / keys 1169)
python3 scratch/ubij1/census_one.py scratch/ubij1/tree-one            -> TOTAL 5364   (inside 2171 / outside 2024 / keys 1169)
```

`tree-one` class table (inside / outside / keys / class total):

| class | inside | outside | keys | total |
|---|---|---|---|---|
| `data-jsonl` (`harness/data/*.jsonl`) | 1,221 | 164 | 1,000 | 2,385 |
| `data-jsonl-other` | 18 | 7 | 0 | 25 |
| `json` | 932 | 952 | 169 | 2,053 |
| `prose-md` | 0 | 13 | 0 | 13 |
| `tooling` (`.py`/`.sh`/`.bash`) | 0 | **290** | 0 | 290 |
| `ts` | 0 | 598 | 0 | 598 |
| **total** | **2,171** | **2,024** | **1,169** | **5,364** |

Distinct identifiers hit: **90 of 184** in `tree-one` (95 in `tree-bij`).
The tooling class fell **308 → 290** and `ts` **600 → 598**.

Per-identifier movement `tree-bij → tree-one` (counts only; the name→tag map is never written):

| identifier | bij (in/out/keys) | one (in/out/keys) | Δ outside |
|---|---|---|---|
| `acquisition` | 0/4/0 | 0/0/0 | −4 |
| `acquisition.path` | 0/2/0 | 0/0/0 | −2 |
| `context.package` | 0/3/1 | 0/0/1 | −3 |
| `escalation` | 3/10/0 | 3/6/0 | −4 |
| `escalation.decision` | 0/2/0 | 0/0/0 | −2 |
| `routing.team` | 0/2/0 | 0/0/0 | −2 |
| `topology` | 23/46/0 | 23/44/0 | −2 |
| `topology.shape` | 0/1/0 | 0/0/0 | −1 |
| **net** | | | **−20** |

Note the two rows that are **not** reduced inside: `escalation` (3 inside) and `topology` (23 inside)
are in-stimulus occurrences — the latter is exactly the 23 questions that name their own kind. They are
part of the irreducible 2,171 and were correctly left alone by both bijections.

## 5. Idempotence

Two consecutive builds (before any tool ran inside the tree, so no `__pycache__` noise):

```
python3 scratch/ubij1/bij_one.py scratch/ubij1/tree-one
python3 scratch/ubij1/bij_one.py scratch/ubij1/tree-one-r2
find … -type f ! -path '*/__pycache__/*' ! -name '*.pyc' | sort | xargs sha256sum   > run1.sha256 / run2.sha256
diff -r scratch/ubij1/tree-one scratch/ubij1/tree-one-r2        -> empty
sha256sum run1.sha256  =  b5527acb679c50d6bfb80dd090600daa6a4e1a840c7fb802723f2511ab9dea92
sha256sum run2.sha256  =  b5527acb679c50d6bfb80dd090600daa6a4e1a840c7fb802723f2511ab9dea92
```

**Two consecutive builds are byte-identical.**

## 6. Residual accounting: inside vs outside the stimulus, by class

### 6a. Inside the stimulus — 2,171 occurrences / 30 identifiers (IRREDUCIBLE)

Identical in `tree-stripped`, `tree-bij` and `tree-one`. These are values of `question` / `options` /
`situation`, i.e. the model's actual input: 23 of the 190 questions carry a real taxonomy token, and the
option strings do too. Removing them would change the numbers the artifact exists to validate. **0 of
these are a packaging defect**; they are the measured floor (`strategy/CPRIME_MEASUREMENT.md`).

### 6b. Outside the stimulus — 2,024 values + 1,169 keys (packaging surface)

Named by class, with the classes that carry them:

| class | count | what it is | defect? |
|---|---|---|---|
| role / tool vocabulary in JSON (`data-jsonl` out 164 + `json` out 952) | ~950 | the fixture's own field vocabulary — worker roles, tool names, layer names, request/proposal type names, plus the `.ts` schema names appearing inside JSON doc strings | **No** — this vocabulary is *shared* by data, `.ts` and tooling in both shapes; it was never in the rename set (it is not project-identifying beyond the fixture's own schema) |
| metric / schema JSON **keys** | 1,169 | `goldIndex` (1,000 of them), plus metric and schema keys | **No** — keys, not names; renaming them would be a schema break |
| provenance strings in JSON (`EXP#…`, file names, doc names) | ~100 | cross-references to the experiment's own documents and results files | **No** — self-reference inside the artifact |
| `.ts` sources | 598 | type unions, schema literals, comments (incl. duplicated stimulus prose: e.g. `topology` 44 in `.ts` vs 23 in JSON) | **No** — a *duplicate* of the same shared vocabulary; the `.ts` copy of a stimulus sentence must stay verbatim |
| `.py`/`.sh`/`.bash` tooling | **290** | docstring examples, alias tables, metric-key literals | **No, and now coherent** — was 308 in `tree-bij`; the 18 removed were exactly the tooling occurrences of renamed names. The remaining 290 are the shared role/tool/metric vocabulary the tooling legitimately uses |
| `prose-md` | 13 | prose in shipped markdown (`AGENTS.md`-style text, reports) | **No** |

**One genuine leftover worth naming** (outside the stimulus, ~1 occurrence + 3 compound-name artefacts):
`context.package` survives as a *substring inside longer identifiers* because the substitution is
word-bounded — `second-labeller/RUN.json:81` (a JSON key of the form
`<kind>_reuse_by_hash`), and the two alias entries at `harness/tccommon.py:74` and
`harness/data/manifest.json:28` whose *values* are bare unmapped names. Word-bounding is what keeps the
23 in-stimulus questions intact, so this is a deliberate trade, not an oversight; it costs ≤4
occurrences.

### 6c. The short code layer — measured, and not visible to the frozen census

`scratch/ubij1/kcensus.py` (decoded walk over the **same 44-file set**, so all shapes are comparable):

| tree | K-code occurrences | inside stimulus | outside values | keys |
|---|---|---|---|---|
| `tree-stripped` | 3,676 | **0** | 3,586 | 90 |
| `tree-bij` | 3,676 | **0** | 3,586 | 90 |
| `tree-one` | 3,676 | **0** | 3,586 | 90 |

By class in `tree-one`: `json` 3,193 out + 90 keys; `ts` 346; `prose-md` 28; `data-jsonl-other` 19.

Reading: the bijection neither creates nor removes this layer — it is **3,676 in all three shapes**, and
**0 of those occurrences are inside the stimulus** in any of them. It never appears in `question` /
`options` / `situation`, so it is **not** part of the irreducible floor. It is opaque, so it carries no
project identifier. But it **is** a second namespace living alongside the renamed one, and a reader who
counts it must add 3,676 to the 5,364.

**Complete decoded accounting** (frozen census + code layer, 44-file set):

* `tree-stripped` 9,247 + 3,676 = **12,923**
* `tree-bij` 5,384 + 3,676 = **9,060**
* `tree-one` 5,364 + 3,676 = **9,040**

## 7. Byte accounting

Over the identical 44-file set (measured by `kcensus.py`):

| tree | bytes |
|---|---|
| `tree-stripped` | 3,096,483 |
| `tree-bij` | 3,057,949 |
| **`tree-one`** (pristine, `tree-one-r2`) | **3,057,815** |

`tree-one` is **134 bytes smaller** than `tree-bij` (the only edits are short renamed references inside
already-short alias tables, docstrings and comments) and **38,668 bytes smaller** than `tree-stripped`.

**Measurement trap, stated so nobody re-measures it wrong.** `tree-one` as it sits on disk is no longer
the raw build: `run_diags.sh` wrote 10 diagnostics outputs into it **and regenerated two of the 44 files**
(`second-labeller/disagreements.jsonl` 14,661 → 10,807 bytes; `second-labeller/metrics.json`
7,346 → 5,278 bytes), and `compileall` added `__pycache__` (`64` files total). Measuring that instrumented
working copy naively gives `3,314,637` bytes and a census of **6,433** (54 files, inflated by the
diagnostics' own copies of ids) — both wrong for release purposes. The pristine emitted tree is the
idempotence twin `scratch/ubij1/tree-one-r2`: **44 files, 3,057,815 bytes, census 5,364, code layer 3,676**,
and it is the artefact all `tree-one` figures in this report come from.

## 8. What I could not verify

1. **No TypeScript type-check.** The emitted tree ships no `package.json` / `node_modules` and the
   workspace has no TS toolchain, so `tsc` was not run. The `.ts` edits are string-literal renames
   (3 files, one comment plus id/kind literals); the renamed `.ts` union member is the one the fixture's
   rewritten `kind` values now use, so the union still describes its data — but this is argued from the
   diff, **not** compiler-verified.
2. **No model training/evaluation.** `harness/train.py`, `evaluate.py` etc. were not run (no deps/GPU in
   this unit); the arm accuracies are verified only through `verify/recompute-claims.py`, which recomputes
   them from the shipped result files (all ✓).
3. **`harness/prepare.py` fails (exit 2) in all shapes** — pre-existing corpus-digest pin, out of scope,
   identical before and after the rename.
4. **The short code layer is not renamed** (by design; see §6c). If a reviewer requires that, it is
   additional work, not a defect of this build.
5. The 4 compound-name leftovers in §6b are deliberate consequences of word-bounded substitution; I did
   not attempt a longer-token rule because the same rule is what protects the 23 in-stimulus questions.
6. **Census-scope caveat:** this measurement inherits the frozen method's blind spot (§6c) — the headline
   `5,384 → 5,364` is a *method-relative* number, and I have stated the complete-decode figure alongside
   it rather than only the favourable one.

## 9. Recommendation

Promote `scratch/ubij1/tree-one` **above `tree-bij`** as the bijected candidate: it is smaller, coherent
(no script looks data up by a name the data no longer uses), runs identically, and is idempotent. It does
**not** displace `tree-stripped` on cost alone for a releaser who does not want the extra risk — but the
risk here is measurable and was measured: the only behavioural difference from `tree-bij` is 20 renamed
tooling occurrences and 4 fewer bytes per copy of the fixture, with `cases.json`, the scoring projection
and every metric bit-identical.

**Open objective carried by this unit:** the author's code-agnostic release policy is satisfied by
`tree-one` for the project-identifier vocabulary; the residual that must be **accepted** is **5,364**
(method-relative) / **9,040** (complete decode), of which **2,171 inside the stimulus are irreducible**.

## Appendix — artefacts and commands

| artefact | what it is |
|---|---|
| `scratch/ubij1/bij_one.py` | the coherent bijection (167 lines; same map derivation as `bij.py`, no skip list, prose masking + integrity check) |
| `scratch/ubij1/census_one.py` | frozen-method decoded-value census (self-validates against 9,247 / 5,384) |
| `scratch/ubij1/kcensus.py` | decoded-value census of the short code layer, 44-file set, all three shapes |
| `scratch/ubij1/census-tree-{stripped,bij,one}.txt` | full per-class / per-identifier census output |
| `scratch/ubij1/diags-tree-one.log` | `run_diags.sh` transcript: every exit code and metric |
| `scratch/ubij1/run[12].sha256` | per-file manifest hashes of the two builds |
| `scratch/ubij1/tree-one-r2` | the pristine emitted coherent tree (all `tree-one` numbers in this report) |
| `scratch/ubij1/tree-one` | the same build, subsequently instrumented by `run_diags.sh` (not the release artefact) |
| `scratch/ubij1/bij-ref` | read-only re-run of the `tree-bij` shape, used for the projection/`cases.json` identity proof |

Driver: `bash scratch/uneutral3/run_diags.sh one scratch/ubij1/tree-one` (exit 0).
The tag↔original map is derived in-memory by `bij_one.py` and is **never written to disk or logged**.
