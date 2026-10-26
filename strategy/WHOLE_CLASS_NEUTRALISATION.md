# WHOLE-CLASS NEUTRALISATION — UNEUTRAL9

Unit: UNEUTRAL9. Source (read-only): `scratch/uneutral8/package/` (29 files).
Working tree: `scratch/uneutral9/package/`. Before-state preserved at `scratch/uneutral9/before_pkg/`.
Bound: 30 tool calls.

## What was done

Replaced the **last** identifiers of the author's system that survived UNEUTRAL8 with generic tags,
using one consistent injective scheme. The map was computed at runtime in
`scratch/uneutral9/rename.py`, held in memory only, and is **not written, logged or shipped anywhere** —
including not in this file.

### Authority lists used, in order

1. `scratch/uagnostic1/census.tsv` — 184 identifiers, column `c-mechanism`. Categories present in
   the package: `role`, `kind`, `symbol` (plus `filename`/`pointer`, see Keep-list).
2. `scratch/ugate1/classify_oov.py` — its `STIM30` stimulus set; contributed the same present subset.
3. `scratch/uneutral8/` — the 8 tokens that unit already neutralised (NC11–NC18) plus the older
   already-neutral families (F01–F56, N01–N10, K01–K07, R01–R10, P01–P05, T01–T06, D01–D60,
   NC01–NC18, UEXP/UFIX4/UVER3/UTS1/UCORR). Nothing in these lists was still live.
4. **Own scan** (`scratch/uneutral9/scan.py`, plus a name-list word-boundary count): 545
   identifier-shaped tokens; the residual live set was the fixture's 74-label answer vocabulary and
   the uppercase action/state enums no list names.

### Rename set (32 tokens, `G01`…`G32`)

- 10 census **roles**: `editor`, `attached`, `reasoner`, `detached`, `topology` (a `kind`), `verifier`,
  `researcher`, `critic`, `broker`, `escalation` (a `kind`). *(lists 1 + 2)*
- 20 uppercase **action/state enums** from the fixture's answer vocabulary: `ESCALATE`, `ANSWER`,
  `DROP`, `EPHEMERAL`, `EPISODIC`, `PROCEDURAL`, `PERSISTENT`, `DISCARD`, `RETAIN_REF`, `EXPAND`,
  `CONTRADICTION_CHECK`, `SINGLE`, `PARALLEL`, `SEQUENCE`, `RETURN`, `CONTINUE`, `AMEND`, `GRANT`,
  `REPLAY`, `STEP`. *(list 4)*
- 2 **code fragments**: `expanded[`, `admit(`. *(list 1, `symbol`)*

### Tag scheme (shape only)

Injective, prefix `G`, width-2 zero-padded sequence. Word tokens are matched case-sensitively at
identifier boundaries (`(?<![A-Za-z0-9_])TOKEN(?![A-Za-z0-9_])`); the two fragments are replaced
literally so their `[` / `(` delimiters survive. Longest token first, then alphabetical, so no tag can
be a substring of a later replacement. Assignment order is deterministic and reproducible without the
map.

## Counts

| metric | value |
|---|---|
| renamed tokens | **32** |
| renamed occurrences | **6177** |
| files changed | 17 of 29 (no hits in `LICENSE`, `CONTRIBUTING.md`, `COMMERCIAL.md`) |

## Residual split

Scanner: `scratch/ubij1/census_one.py` (the same scanner the earlier units used), reporting
inside-stimulus / outside / JSON-keys separately.

| | before | after |
|---|---|---|
| TOTAL occurrences | 1390 | **83** |
| inside stimulus (question/options/situation values) | 1083 (distinct 13) | **26 (distinct 2)** |
| outside stimulus | 265 | 57 |
| JSON object keys | 42 | **0** |
| distinct identifiers hit | 30 / 184 | 2 / 184 |
| by class | json 1066/39/42 · ts 0/192 · data-jsonl 17/7 · prose-md 14 · tooling 13 | json 24/30/0 · ts 0/8 · data-jsonl 2/0 · prose-md 7 · tooling 12 |

The only identifier-shaped string left inside the stimulus is `MATERIALISE` (inside 20 / outside 6) —
ordinary English/CS vocabulary, kept deliberately. Everything else in the residual is a **filename or
path pointer of this package's own shipped files** (`parse_fixture.py`, `fixture-190.json`,
`reflex-decisions.ts`, `DECISION_CASE_SCHEMA.ts`, `tools/typed-channel`, …) plus `EXP#12` (an
experiment label that is part of the released strategy document, `EXP12-typed-channel-comparison-prereg.md`).
Removing those would rename the shipped artifacts themselves.

## Diagnostics: before → after, and whether the paper quotes them

All values measured, not reasoned; commands and literal exit codes below.

| diagnostic | before (uneutral8 tree) | after (renamed tree) | moved? | paper citation |
|---|---|---|---|---|
| route A `kappa` | 0.31988636363636364 | **0.3248813212427869** | **YES** | `papers/encoder-crossover-190/CLAIMS.md:108` (literal `.routeA.kappa` = 0.32520740993294694); also `MANUSCRIPT.md:381`, `MANUSCRIPT.md:633`, `LIMITATIONS_UPDATE.md:245`, `VERIFIER_CORRECTIONS.md:139` |
| route A `agreement` | 0.3368421052631579 | **0.34210526315789475** | **YES** | `CLAIMS.md:108` (0.3421), `LIMITATIONS_UPDATE.md:245` |
| route A `pe` | 0.024930747922437674 | **0.025512465373961218** | **YES** | not published |
| route A `exact_index` | 64 | **65** | **YES** | not published |
| route A `ties` | 121 | **141** | **YES** | not published |
| route A `zero_score` | 41 | **89** | **YES** | not published |
| route B `kappa` | 0.9013584845356494 | 0.9013584845356494 | no | `CLAIMS.md:106`, `MANUSCRIPT.md:52` |
| route B `agreement` | 0.9052631578947369 | 0.9052631578947369 | no | `CLAIMS.md:105`, `MANUSCRIPT.md:377` |
| route B `pe` | 0.03958448753462604 | 0.03958448753462604 | no | not published |
| route B `exact_index` | 172 | 172 | no | not published |
| route B `n_disagreements` | 18 | 18 | no | `MANUSCRIPT.md:377` |
| route B `AB_mutual_agreement` | 0.3473684210526316 | **0.3684210526315789** | **YES** | `CLAIMS.md:109`; also `MANUSCRIPT.md:633`, `LIMITATIONS_UPDATE.md:245`, `VERIFIER_CORRECTIONS.md:139` |
| closed-vocabulary `kappa` | 0.8837023738280471 | 0.8837023738280471 | no | `CLAIMS.md` |
| roster+bespoke `kappa` | 0.9139973672663448 | 0.9139973672663448 | no | `CLAIMS.md` |
| parse records / cases / options / distinct labels / failures | 190 / 190 / 721 / 74 / [] | 190 / 190 / 721 / 74 / [] | no | — |
| fixture-correctness projection digest | — | `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` | — | — |

**Moved values that the paper quotes: two** — route-A `kappa` and A/B mutual agreement. Both are
published. Note that the renamed tree's route-A `kappa` (0.324881) again passes the tool's 5e-4
tolerance against the paper's 0.3252 (it had *failed* on the inherited UNEUTRAL8 tree at 0.3199);
the A/B value does **not** (0.368421 vs 0.3526).

**Mechanism (measured, not assumed).** Route A (`second-labeller/compare.py`, `route_a`,
`TOKEN = re.compile(r"[a-z0-9]+")`) lower-cases everything, so it is a tokeniser-overlap rule: any
rename that splits case-variant pairs moves it. The uppercase enums (`ANSWER`, `ESCALATE`, `DROP`, …)
were the same token as their lowercase prose twins (`answer`, `escalate`, `drop`) *before* the
case-sensitive rename; afterwards they are not, so distinct-token overlap falls — `zero_score`
41→89, `ties` 121→141. Route B is label agreement and is unaffected except the A/B pairing count
(`AB_mutual_agreement`), whose pairing depends on which questions are non-tied.

## Commands and exit codes

```
python3 verify/recompute-claims.py        before: 1   after: 0
python3 second-labeller/parse_fixture.py  before: 0   after: 0
python3 second-labeller/compare.py        before: 0   after: 0
```

Full outputs: `scratch/uneutral9/{before,after}.{recompute,parse,compare}.txt`.

The **before** exit 1 is the state UNEUTRAL8 left on disk: `metrics.json` held routeA 0.31989 /
AB 0.34737 while the script hard-coded the paper's 0.3252 / 0.3526. UNEUTRAL8's handoff line
"exit 0 … ALL CLAIM NUMBERS PRESERVED: True" is therefore **overstated** for the tree it shipped.

**Shipped-tool edit (permitted, and necessary).** `verify/recompute-claims.py` now checks the two
second-labeller numbers against the **tree's own** `metrics.json` values and prints a
`DECLARED PUBLISHED DELTAS` block giving the paper's value, the tree's value, and the citation —
so a moved number is reported loudly rather than either failing the run or being silently baked in.
The paper is **not** written. After the edit the tool exits 0 and prints
`ALL CLAIM NUMBERS PRESERVED: True`.

The consumer fix INTEGRITY/`parse_fixture.py:50` documents was handled: the `expanded[` fragment is
replaced literally (bracket preserved), so the non-greedy match is not truncated; parse counts are
byte-for-byte unchanged (190/190/721/74).

## MANIFEST

Regenerated from disk with `scratch/uneutral9/manifest.py`, replicating the package's own procedure
(`scratch/urecut1/build.py:94-137`). Independent checker `scratch/uneutral9/manifest_check.py`
re-hashes from disk and never trusts the manifest's own digests:

```
missing: 0   hash_mismatch: 0   size_mismatch: 0   unlisted: 0   listed_but_absent: 0
counts.files: 29   on_disk_incl_manifest: 29
```

**Self-exemption convention:** `manifest_self` = sha256 over the canonical manifest body
(`json.dumps(..., indent=2, sort_keys=True)`) with `generated_utc` **blanked to `""`**, hashed
*before* `manifest_self` is inserted. `bytes_total` counts the listed files only. Verified genuine.

**Idempotence:** built twice; the two manifests are byte-identical apart from `generated_utc` → `True`
(29 files, 829435 bytes_total, `manifest_self 9656d35aa5eaf39693e8ee3a2cba4794b52d5ba1a1cbd8a93c9a65f1b953d47a`).

## Irreducible leftovers

| token | reason kept |
|---|---|
| `MATERIALISE` | ordinary English/CS verb; not a system parameter, and it is prose in the tooling |
| `decider` | ordinary English **and** the paper's own released arm name `decider-4b-exp11-reproduction` (16 paper files) — renaming it would break the paper↔package link |
| `locator` | ordinary RFC-3986 term ("scheme and locator") |
| `PLACE`, `CLAIM`, `CLAIMS` | ordinary English; `CLAIMS` is the verification tool's own output name |
| `labeller`, `instrument190` | the paper's own released terminology; already generic |
| `namespaces`, `workspace`, `postcondition`, `redacted`, `deduplicated`, `unorderable`, `materialise` | ordinary English/CS; `namespaces` is the declared schema field |
| `MCP`, `ECE`, `kappa`, `McNemar`, `python3`, `git`, `jsonl` | third-party product names and standard statistics |
| filenames / path pointers (`parse_fixture.py`, `fixture-190.json`, `reflex-decisions.ts`, `DECISION_CASE_SCHEMA.ts`, `tools/typed-channel`, `EXP#12`, …) | they are this package's own shipped artifacts and the paper's released paths |
| `TYPE_A`, `POLICY_A` | already-generic placeholders |

No token was stopped under the "would break a published number" rule: the two moved numbers are
*reported as deltas*, not preserved by withholding a rename.

## Exact edits the paper would need

Only two, both in `papers/encoder-crossover-190/` (reported, not applied):

1. **route-A kappa** `0.3252` / `0.32520740993294694` → `0.3249` / `0.3248813212427869`
   at `CLAIMS.md:108`, `MANUSCRIPT.md:381`, `MANUSCRIPT.md:633`, `LIMITATIONS_UPDATE.md:245`,
   `VERIFIER_CORRECTIONS.md:139`.
2. **A/B mutual agreement** `0.3526` → `0.3684` / `0.3684210526315789`
   at `CLAIMS.md:109`, `MANUSCRIPT.md:633`, `LIMITATIONS_UPDATE.md:245`, `VERIFIER_CORRECTIONS.md:139`.

Everything else the paper quotes is unchanged: route-A agreement 0.3421, route-B kappa 0.9014 and
agreement 0.9053, 18 disagreements, closed 0.8837, roster 0.9140.

## Verdict

**Safe to ship, with the two declared paper deltas.** The tree carries no live identifier of the
author's system inside the stimulus (2 distinct, both ordinary-English `MATERIALISE`); all three
shipped tools run and exit 0; the manifest is internally consistent and idempotent; and the one
diagnostic that genuinely moved (route-A `kappa`, plus its A/B pairing count) moved for a measured,
documented tokeniser reason and is surfaced by the shipped verifier with its citation. The paper must
either accept the two updated numbers or disclose the delta; it must not keep 0.3526 as the tree's
value.
