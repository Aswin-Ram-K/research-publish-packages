# UNPINNED_MEASUREMENT — REDACT_PINS=0, measured (unit UNEUTRAL2)

Date: this unit's run. Parent: session-c3d61727-8af8-4c19-b1b9-5922c347a11a.
Supersedes the digest-invariance clause of the UNEUTRAL1 card (parent declared it superseded).
Invariant of record: **no published CLAIM NUMBER may move.**

## 0. Generator + command

`repro/encoder-crossover-190-SANITISED/redact.py` was **NOT modified** (before == after; no edit was
required to run the unpinned branch). The pinned default is untouched:

    repro/encoder-crossover-190-SANITISED/redact.py:925
    NEUTRAL_PINS = os.environ.get("REDACT_PINS", "1") != "0"

Command that produced the unpinned tree:

    cd "/home/zer0null/reserach extarctor/repro/encoder-crossover-190-SANITISED"
    REDACT_PINS=0 python3 redact.py --out "/home/zer0null/reserach extarctor/scratch/uneutral2/tree-full"

exit 0. Live-tree sha256 sweep before vs after: `diff` clean → **LIVE TREE UNCHANGED**.
`M` was never written or logged; `verify/redaction-log.json` carries `"map_shipped": false`.

## 1. Residual census (scanner: `scratch/uneutral2/census2.py`)

Same identifier source and matching method as UNEUTRAL1's `scratch/uneutral1/scan.py`: column 2 of
`scratch/uagnostic1/census.tsv`, case-insensitive literal scan, `.git`/`node_modules`/`__pycache__`
pruned. census2.py adds per-file / per-class / per-line attribution.

| tree | files | distinct ids hit | occurrences |
|---|---|---|---|
| `scratch/uneutral1/tree` (pinned) | 45 | 99 of 184 | **26,351** |
| `scratch/uneutral2/tree-full` (unpinned, as generated) | 44 | 16 of 184 | **29** |
| `scratch/uneutral2/tree-full` + verifier copied in | 45 | 19 of 184 | **36** |
| `scratch/uneutral2/tree-stripped` (dead JSONL fields removed, pins kept) | 45 | 99 of 184 | **9,254** |

**The unpinned tree does NOT reach 0.** All 29 residual occurrences are in exactly one file:
`verify/redaction-log.json`, 16 identifiers:

    GrantPolicy 3, INTEGRITY.md 3, REDACTION_REPORT.md 3, grantPolicy 3,
    DECISION_CASE_SCHEMA.ts 2, RESIDUALS.md 2, SCRUB_REPORT.md 2, reflex-decisions 2,
    reflex-decisions.ts 2, LEAD-WIRING.md 1, LICENCE_TODO.md 1, WIRING.md 1, broker 1,
    editor 1, export-fixture.ts 1, fixture-190.json 1

File:line classes: `verify/redaction-log.json:45` `"file": "fixture/DECISION_CASE_SCHEMA.ts"`,
`:75` `` "`grantPolicy`": 1 ``. **Mechanism (structurally irreducible under the current ordering):**
`stage_e_neutral_tags(generated)` runs *before* the final `write_log()`, and
`verify/redaction-log.json` is itself in `generated` — so the log is rewritten *after* stage E and
re-emits the file names and census-token keys. Fixing it needs a stage-order change or a neutraliser
inside `write_log()`, not a pin.

Pinned residual drivers (for contrast): `harness/data/train.jsonl` 17,025 + `harness/data/dev.jsonl`
3,562 = **20,587 = 78.2 %**; then `harness/data/corpus.json` 623, `results/baselines.json` 564,
`fixture/reflex-decisions.ts` 519, `variants/no-union/files/fixture/reflex-decisions.ts` 518,
`harness/data/fixture-190.json` 517, `results/eval-*.json` 467/452/451/449/446,
`second-labeller/labelsB.json` 190, `MANIFEST.json` 103, `.py`/`.sh` tooling 338.

## 2. Two defects that make REDACT_PINS=0 as-implemented unshippable

**(a) JSON escape collision — the JSONL is CORRUPTED.** Census field names `nCandidate`
(`scratch/uagnostic1/census.tsv:64`), `nKind` (`:65`), `nSituation` (`:66`) match the characters
`n`+`Kind`/`Situation`/`Candidate` inside the JSON escape `\n`, because the census entry `nKind` is
the literal substring of `\nKind`. Result: the escape becomes `\` + tag (`\F32`, …).

    scratch/uneutral2/tree-full/harness/data/train.jsonl:1
    ... option the situation selects.\F32: routin...     (6 x "\F" in record 1)

    json.decoder.JSONDecodeError: Invalid \escape: line 1 column 755 (char 754)

**Every** record fails: train 800/800 bad, dev 200/200 bad. The pinned and live trees: 0 bad.
`harness/train.py:65-72 load_jsonl` would raise on record 1.

**(b) Shipped tooling is retagged and breaks.** Unpinned lifts `PIN_SKIP_EXT = {".py", ".sh", ".bash"}`.
The filename identifier `reflex-decisions` → tag `D07`, so:

    scratch/uneutral2/tree-full/second-labeller/parse_fixture.py:16
    SRC = os.path.join(HERE, "D07.sandbox.ts")          # pristine: "reflex-decisions.sandbox.ts"

    FileNotFoundError: [Errno 2] No such file or directory:
    '.../second-labeller/D07.sandbox.ts'

So `parse_fixture.py`/`compare.py` **cannot run inside the unpinned tree as generated** — requirement 3's
diagnostics are not obtainable from it unmodified (see §3 for how they were obtained).

## 3. Claim numbers — MEASURED, and one MOVES

`verify/recompute-claims.py` run inside `scratch/uneutral2/tree-full` (verifier copied in from the live
tree; it was not present at generation time, so it was not retagged). Verbatim tail:

      ALL CLAIM NUMBERS PRESERVED: True
      fixture correctness digest: 9997da6263840017dba05fff5ea64b8264c6b8107a152e782ba292a4198d61d0

exit 0; all 9 numeric checks OK. **Caveat that matters:** this script does not read
`train.jsonl`/`dev.jsonl` (grep: none), and its `SECOND-LABELLER NUMBERS` section compares
hard-coded constants against the shipped `results/metrics.json` — it does **not** recompute route A.
Its `True` therefore does **not** prove route A's published kappa survives.

Route A, re-run (`parse_fixture.py` + `compare.py`). Pinned tree = live tree. The unpinned column was
obtained by copying the **pristine** `parse_fixture.py`/`compare.py` onto the unpinned tree and running
them on its own retagged fixture + its own retagged `labelsB.json` (with pristine `labelsB.json` the
join fails: `compare.py:42 in kappa`).

| metric | live | pinned tree | unpinned tree |
|---|---|---|---|
| routeA `ties` | 120 | 120 | **121** |
| `agreement` | 0.34210526315789475 | 0.34210526315789475 | **0.3368421052631579** |
| `kappa` | 0.32520740993294694 | 0.32520740993294694 | **0.31988636363636364** |
| `exact_index_matches` | 65 | 65 | **64** |
| `zero_score_cases` | 41 | 41 | 41 |
| `AB_mutual_agreement` | 0.3526315789473684 | 0.3526315789473684 | **0.3473684210526316** |

**Five of six move.** `0.3252` route-A kappa is an asserted claim (it is printed as such by
`recompute-claims.py`). The cause is structural: route A is a tokeniser-overlap scorer over the
fixture's *verbatim* `question`/`options`/`id` strings, and unpinned lifts `PIN_LITERAL_KEYS`.
**REDACT_PINS=0 violates the invariant that matters.**

## 4. Digests (old vs new; manuscript must cite the released column)

| artifact | live (pinned default) | pinned emitted `scratch/uneutral1/tree` | unpinned `scratch/uneutral2/tree-full` |
|---|---|---|---|
| `fixture/reflex-decisions.ts` sha256 | `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae` | `f0a2abceed6a2be2e892ec9cb234eafe665e77a001573971042aef7ce151bc37` | `e5112bc7aa1cdae170acc9d9d60883d3cb6e0011d029e88a1471eb64bf40d44a` |
| `harness/data/train.jsonl` sha256 | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` | same as live | `0f53cc39066ad561bc789e3deb1f61b5bc5c8b937d96adb0658c21bee0dc6cd4` |
| `harness/data/dev.jsonl` sha256 | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` | same as live | `36319e01c4a5044ee2922c382971cf5690ffc41cb48dcd1941742b8c6d45e1e6` |
| fixture-correctness digest | `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a` | same as live | `9997da6263840017dba05fff5ea64b8264c6b8107a152e782ba292a4198d61d0` |
| scoring-projection digest | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` | `f549a2bdcf0a7dea9ec1da8ad2e68dbca376045cb38f507b7e18a611df0e34e5` | `78838399b361ab7dc345eaef5cb43d7b83366a0ae75d8797b5277354ba5c2be6` |

Recipes. fixture-correctness = `verify/recompute-claims.py:126-128`:
`hashlib.sha256(json.dumps([[c["id"], c["correct"], len(c["options"])] for c in fixture], separators=(",", ":")).encode()).hexdigest()`.
scoring-projection = `parse_fixture.py` then
`sha256(json.dumps([{k:c[k] for k in ('id','kind','question','options','correct')} for c in cases], sort_keys=True, separators=(',',':'), ensure_ascii=False))`;
validated: it reproduces `57a29b4e…` on the live tree and `f549a2bd…` on the pinned tree.
Stripped train/dev sha256: `0866fe7c8681a35b2d6da8c274cfc6fd3ace17e3db5d73e0d03bacc80a3c3d53` /
`7e09344c40ef51832f40249c62efccf09b0fb773ddb5645e9c87f3440750ca69`.

## 5. Requirement 4 — consumed vs dead fields in train.jsonl / dev.jsonl

Record keys: `['clanId','familyId','gold','goldIndex','id','kind','options','situation','stratum','texts']`.
Loaded at `train.py:429` `train_ex = load_jsonl(tc.DATA / "train.jsonl")` and `train.py:430`
`dev_ex = load_jsonl(tc.DATA / "dev.jsonl")` (`load_jsonl` at `train.py:65-72`).

CONSUMED:
- `options` — `train.py:94` `k_max = max(len(e["options"]) for e in examples)`; `train.py:312`, `:322`, `:373`; `tccommon.py:167`
- `kind` — `tccommon.py:167`; `train.py:311` `s = tc.render_context(e["kind"], e["situation"])`; `train.py:322`
- `situation` — `tccommon.py:167`; `train.py:311`; `train.py:322`
- `goldIndex` — `train.py:105` `gold[i] = e["goldIndex"]`; `train.py:169`, `:175`, `:315`, `:323`, `:376`
- `gold` — `train.py:367` `counts[e["gold"]] = counts.get(e["gold"], 0) + 1` (majority-class arm only)

DEAD WEIGHT:
- `texts` — **0 read-sites**; the pre-rendered text is re-derived by `tccommon.py:165-167`
  `texts_for_example` → `render(example["kind"], example["situation"], o) for o in example["options"]`.
  It is 1,627,074 B of train.jsonl + 350,078 B of dev.jsonl = **1,977,152 B (73.8 % / 72.2 %)**.
- `id` 15,200 + 3,800 B · `familyId` 19,200 + 4,800 · `clanId` 16,800 + 4,200 · `stratum` 17,400 + 3,600
  — read only by `harness/prepare.py:79-91`, which *builds* the split, never by training.

Measured byte saving (valid pinned pair): train 2,205,127 → 509,453 (**−1,695,674 B, −76.90 %**);
dev 484,922 → 118,444 (**−366,478 B, −75.57 %**); total **−2,062,152 B (−76.7 %)**.
`recompute-claims.py` reads neither jsonl (grep: none) → **stripping moves no claim number.**
It does move `train`/`dev` sha256 and `defect-probe.py:110 devSplitSha256`.
Census of the stripped tree: 26,351 → **9,254** occurrences; the JSONL share falls 20,587 → 3,490,
and with `texts` gone the `\nKind`/`\nSituation`/`\nCandidate` escape collisions vanish (the remaining
`kind` values carry no escapes, so retagging them is safe).

**Strip vs retag:** retagging the field names is what corrupted the file and what it is meant to fix;
stripping removes the vocabulary *and* 2.06 MB, and is strictly superior for the fields training never
reads. Recommendation: **strip `texts`, `id`, `familyId`, `clanId`, `stratum`; retag nothing in JSONL.**

## 6. Idempotence

Two consecutive unpinned runs, `tree-full` and `tree-full-run2`:

    diff -r scratch/uneutral2/tree-full scratch/uneutral2/tree-full-run2
    Only in scratch/uneutral2/tree-full/verify: recompute-claims.py

i.e. byte-identical except the verifier this unit copied in after generation.
`gen-run1.log` sha256 == `gen-run2.log` sha256 == `0496d7328bbba7f806ce4f378b6a42282d9ca898bb365a5c8c470cc0e82cd692`.
Whole-tree hashes: run1 `6085313101dbfb3cfa76fd508dfd02c24940f78836af6d961c91cc013fd87a77`,
run2 `b8c0718cddd7f7deadceb66e08952368ab6ed351f7bfa07b58d25d5f1faded05` (differ only by that file).
**The generator is byte-idempotent.**

## 7. Recommendation

- **(A) keep the pinned tree — ship now.** Valid, all claim numbers preserved; route A identical to
  live. Cost: 26,351 residual occurrences of 99 identifiers; 20,587 (78.2 %) are the train/dev JSONL
  vocabulary. **No claim number moves.**
- **(B) ship the unpinned tree — REJECT.** Corrupts all 1,000 JSONL records (invalid JSON), breaks the
  shipped `parse_fixture.py`, **moves 5 of 6 route-A published numbers** (kappa 0.325207 → 0.319886,
  ties 120 → 121, exact 65 → 64, AB 0.352632 → 0.347368), and still leaves 29 residual occurrences.
  It fails the only invariant that matters. Cost: an unshippable artifact plus a re-learned baseline.
- **(C) stripped-and-unpinned.** *As literally defined* (REDACT_PINS=0 + strip) it inherits (B)'s claim
  movement. The version that works is **C′ = (A) + strip the five dead JSONL fields + selectively retag
  the non-fixture material**, keeping `PIN_LITERAL_KEYS` (`id`/`question`/`options`) and the tooling
  pins — because route A is a function of those verbatim strings, and retagging `.py`/`.sh` breaks the
  shipped verifiers.
  Cost: one stage-E change + one strip stage + a census re-run. **No claim number moves** (stripping is
  invisible to `recompute-claims.py`); saving −2.06 MB (−76.7 %); JSONL residual 20,587 → 3,490;
  total residual ≈ 9,254 measured, floor ≈ 5,764 after the JSONL share is retagged.

**Recommendation: ship (A) now; commission (C′) as the release-policy path. Do not ship (B).**
