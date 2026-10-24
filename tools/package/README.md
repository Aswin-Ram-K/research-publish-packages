# `tools/package/` — the publication-package pipeline

Seven parameterised, idempotent commands replacing the throwaway scripts that were copied into
~100 `scratch/` directories with hard-coded absolute paths.  Every command takes
**`--package <slug>`**: a slug naming a directory under `papers/`, or an explicit path
(`--package scratch/uneutral10/package` reproduces the shipped known-good numbers below).

Run everything from the workspace root (`/home/zer0null/reserach extarctor`).

## Provenance (read this before trusting a number)

| tool | structural source | behaviour source |
|---|---|---|
| `neutralise.py` `--scheme neutral-tag` | `scratch/uneutral9/rename.py` | same (byte-identical output) |
| `neutralise.py` `--scheme bij` | `scratch/ubij1/bij_one.py` | same (byte-identical output) |
| `census.py --mode decoded` | `scratch/ubij1/census_one.py` | same |
| `census.py --mode raw` | `scratch/uneutral1/scan.py` | same |
| `classify.py` | `scratch/ugate1/classify_oov.py` | same (`--legacy-names` byte-identical) |
| `scan_markers.py` | ad-hoc greps in `scratch/` | generalised |
| `regen_manifest.py` | `scratch/udtag1/regen_manifest.py` (+ copy `scratch/utool1/regen_manifest.py`) | **`scratch/uneutral10/manifest.py`** for the counts/self convention |
| `check_manifest.py` | `scratch/utool1/check_manifest6.py` + `scratch/uver24/` | `check_manifest_uver24.py` for the five-count shape |
| `gate.sh` | `scratch/ugate1/gate_scoped.sh` | **`scratch/ugate2/gate_scoped_v2.sh`** (the corrected gate) |

**Missing named source, reported not improvised:** the task named `scratch/ugate2/gate.sh`.  That
path does **not exist**.  `scratch/ugate2/` holds `datavocab_block.sh`, `gate_old.sh`,
`gate_scoped_v2.sh` (6986 bytes, sha256 `5c4e3aa9b13982c7e1aec9fa5d63468955a2e3d5bdde2ce43b6d93b012cd2aab`,
whose own header names it `gate.sh`); a same-named copy at
`scratch/ugate2/dest/research-publish-packages/gate.sh` has a different sha256
(`cccacbe903332c72479ca4aabc9533107909c7efb985ef1f033215f051594992`).  `gate.sh` here was built from
the two named-plus-present corrected sources above; `scratch/ugate2/gate_scoped_v2.sh` output is
reproduced byte-for-byte.

### The two id lists — quoting the wrong one is a known error

* **mechanism authority = the 184 ids** in `scratch/uagnostic1/census.tsv` column 2 (its `cat`
  values are `field/filename/kind/kind-dotted/path/pointer/role/symbol/tool-cap`; the file contains
  **no** literal `c-mechanism` string).  `classify.py` labels these `mechanism-*`.
* **the 33-token class** = the NEUTRAL-TAG/v1 list (10 roles + 20 enums + 2 fragments + `MATERIALISE`)
  used by `neutralise.py --scheme neutral-tag`.  It is **not** the mechanism authority.

`classify.py` class sources, stated because they differ:

| class (canonical) | `--legacy-names` | rule source |
|---|---|---|
| `released-schema` | `a-schema` | `scratch/ugate1/classify_oov.py` (data key, id grammar, or `public.txt`) |
| `third-party/incidental` | `b-thirdparty` | `classify_oov.py` **else-branch** |
| `mechanism-stimulus` / `mechanism-outside` | `c-mechanism-stimulus` / `c-mechanism-outside` | the 184-id census, split by the 30-token stimulus list |
| `encoding-artefact` | `d-artifact` | `classify_oov.py` (all-digit or 6+ hex) |
| `unclassified` | (none) | **declared but unreachable** — `classify_oov.py`'s else-branch is `b-thirdparty`; preserved exactly |

### The `bytes_total` self-exemption convention

`counts.files` **includes** `MANIFEST.json` (`len(files[]) + 1`), while `counts.bytes_total`
**excludes** the manifest's own bytes.  `manifest_self` is
`sha256(json.dumps(body, indent=2, sort_keys=True))` with `generated_utc` blanked and
`manifest_self` dropped.  Two units have already mis-stated `bytes_total`; `regen_manifest.py`
writes the note into the manifest itself (`manifest_self_note`) and `--no-note` omits it.
`scratch/udtag1/regen_manifest.py` instead converges to an **inclusive** `bytes_total`; that is the
one divergence from it, and it is why `check_manifest_uver24.py` FAILS the shipped package.

### `gate.sh` is not a leak detector

Its number counts tokens **missing from a general English word list**.  It is a vocabulary-coverage
acceptance test, not a confidential-content finding.  No denylist is carried.

## Commands

### `neutralise.py`
Injective, case-sensitive, longest-first token→tag rename.  **The token→tag map is held in memory
only** — never written, never logged, never shipped; only aggregate counts are printed.
Flags: `--package` (required), `--scheme {neutral-tag,bij}` (default `neutral-tag`), `--out`
(default `<package>-neutralised`; must differ from `--package`), `--tokens FILE`,
`--fixture REL` (repeatable, bij), `--live DIR`, `--src DIR` (bij; default `--package`), `--salt`.
`--diagnostic CMD` (repeatable) runs a command with `cwd=<tree>` before and after; if its
`(rc, stdout, stderr)` moves the rename is **reported and not applied**.
Exit: `0` ok · `2` bad args / `--out` == `--package` · `3` prose-integrity rejection (bij) ·
`4` a diagnostic moved.
Known-good: `neutral-tag` on `scratch/uneutral9/before_pkg` → `renamed_tokens: 32`,
`renamed_occurrences: 6177`, `files_changed: 17` (byte-identical to `scratch/uneutral9/rename.py`).
`bij` on `scratch/uneutral3/tree-stripped` → 10 kinds, 1639 pinned prose values, 1774 mask needles,
24 files changed (ts 3, tooling 2, data 15, prose 4), `prose-integrity failures: none`
(byte-identical to `scratch/ubij1/bij_one.py`).

### `census.py`
Identifier census over a tree.  In-stimulus = the values of the fixture's
`question`/`options`/`situation`.  Flags: `--package` (required), `--mode {decoded,raw}`
(default `decoded` = `census_one.py` walk; `raw` = `scan.py`).  Exit `0`.
Known-good on `scratch/uneutral10/package` (**this 29-file shipped package tree**):
`files scanned: 29`, `distinct identifiers hit: 15 of 184`, `TOTAL OCCURRENCES (decoded walk): 66`,
`inside stimulus … 20  distinct=1`, `outside … 46`, `JSON object keys: 0`; by class
`data-jsonl-other` 2 · `json` 35 · `prose-md` 12 · `tooling` 11 · `ts` 6.
These are the **authoritative totals** pinned by
`tests/test_package_tools.py::PackageTools::test_census_reproduces_documented_totals_on_shipped_package`;
the test asserts this block, so the test checks a documented quantity and not a magic number.

**Note 2026-10-16 (UFIXPKG10)** — the totals moved from `18 of 184` / `75` (with `json` 48 ·
`prose-md` 7 · `tooling` 12) because recent units removed identifiers from the shipped tree, and
five comments were removed from `fixture/reflex-decisions.ts`; the reduction was re-derived by a
second, independently written census over the same 29 files
(`scratch/ufixpkg10/independent_census.py`, 12/12 quantities matching `census.py`) and is not a
tool regression.  `inside` (20, distinct=1), `JSON object keys` (0), `data-jsonl-other` (2) and
`ts` (6) are unchanged.
The figure `inside 2,171` belongs to a **45-file** tree and must not be quoted for this one.
Intended difference: the `-- by identifier` section is sorted by `(-total, identifier)`, so it is
deterministic; `census_one.py` leaves ties in Python set order and is **not** reproducible run to
run.  `--mode raw` differs only in printing the resolved absolute `tree:` path.

### `classify.py`
Classes the census/OOV identifiers.  Flags: `--package` (required, the emit tree carrying
`vocabulary/`), `--oov FILE` (required), `--out FILE`, `--legacy-names`.
Exit `0` · `2` missing/empty vocabulary file.  Known-good with `--legacy-names` on
`scratch/ugate1/emit/research-publish-packages` + `scratch/ugate1/oov_tokens.tsv`: stdout and the
classified TSV are byte-identical to `scratch/ugate1/classify_oov.py` — `distinct tokens: 1464`;
`a-schema 268/19576`, `b-thirdparty 1156/9924`, `c-mechanism-outside 27/88`,
`c-mechanism-stimulus 10/332`, `d-artifact 3/16`; `data_json_keys_distinct: 740`,
`data_string_values_distinct: 5998`, `declared public.txt: 17`.

### `scan_markers.py`
Regex marker scan.  Flags: `--package` (required), `--marker REGEX` (repeatable), `--config FILE`
(one regex per line), `--no-defaults`.  Defaults: `encoder-crossover-190`,
`(?i)CONSONANCE`, `U[A-Z]+[0-9]+`.  Exit `0` no hit · `1` at least one hit · `2` bad input.
Known-good on `scratch/uneutral10/package`: 4 + 0 + 0 = **4 hits**, exit 1
(`encoder-crossover-190` 4, `CONSONANCE` 0, unit-ID 0); with
`--no-defaults --marker ZZZ_NO_SUCH_MARKER_ZZZ` → 0 hits, exit 0.

**Note 2026-10-16 (UFIXPKG11).**  This line previously read `6 + 0 + 39 = 45 hits`
(`encoder-crossover-190` 6, unit-ID 39), a **historical transcript** of a past state of the same
tree — recent units removed the identifiers the unit-ID regex matched.  Hit counts are
**payload-volatile**: re-run `scan_markers.py --package scratch/uneutral10/package` before citing
them rather than re-pinning the number here.

### `regen_manifest.py`
Regenerates `MANIFEST.json` from disk: `path`, `sha256`, `bytes`, `source`, `source_sha256`,
`counts.files`, `counts.bytes_total`, `manifest_self`, `generated_utc`.  `source`,
`source_sha256`, `identical_to_source` and `kind` are **preserved**, never recomputed (this is what
`scratch/uneutral10/manifest.py:24-26` does; one shipped entry, `verify/recompute-claims.py`,
carries `identical_to_source: true` with an empty `source_sha256` — recomputing would flip it).
Flags: `--package` (required), `--generated-utc TS` (pin it to make the output byte-idempotent),
`--no-note` (omit `manifest_self_note`).  Exit `0`.
**These figures are payload-volatile — re-derive before citing; do not quote this block forward.**
`counts.bytes_total`, `manifest_self` and the shipped `MANIFEST.json`'s own sha256 are the
sum/digest of one byte-state of one payload, so **any** edit to **any** shipped file's text, name or
presence moves all three.  That has already happened three times in one session (dated transcript
below), which is why the durable claim here is the **re-derivation command**, not the number.  The
command regenerates the manifest on a *copy* and `cmp`s its bytes against the shipped file:

```sh
TREE=scratch/uneutral10/package
STAMP=$(python3 -c "import json;print(json.load(open('$TREE/MANIFEST.json'))['generated_utc'])")
rm -rf /tmp/regen-check && cp -r "$TREE" /tmp/regen-check
python3 tools/package/regen_manifest.py --package /tmp/regen-check \
    --generated-utc "$STAMP" --no-note
cmp "$TREE/MANIFEST.json" /tmp/regen-check/MANIFEST.json && echo BYTE-IDENTICAL
```

`--no-note` omits `manifest_self_note` and reproduces the shipped key set exactly (the default adds
only that key).  `--generated-utc` is part of the byte-identity claim, not decoration: feed it the
manifest's own `generated_utc` (or any fixed stamp) or the bytes will differ for the timestamp alone.
`source`, `source_sha256`, `identical_to_source` and `kind` are **preserved**, never recomputed.

**Known-good as measured 2026-10-16 by UFIXPKG13** (true only for that payload byte-state; superseded
by the next shipped-file edit): `counts.files: 29`, `counts.bytes_total: 831768`,
`manifest_self: 24021f40b26a03ea79fd706704b78b756ced3b03373f6bda8ef1914db774edc5`,
shipped-`MANIFEST.json` sha256
`55956b90af723070479629581784751b1170125a760da56109a684a36f59a58a`, at pinned
`generated_utc: 2026-10-16T22:51:23Z`.

**Dated historical transcript** (earlier byte-states of the same package — NOT current):
* *2026-10-16 (pre-UFIXPKG13; the value this block replaced)*: `bytes_total: 830893`,
  `manifest_self: 16ff23fe3ba7aba534adab0af6ce2067d36252394aef7e7e73416b91d5a0d21a`,
  shipped-`MANIFEST.json` sha256
  `3fea08cc4a55c93d549b0829fa85090bd79a82ee5038dcab9fdae595842ac9c8`.
* *2026-10-16 (UFIXPKG11, earlier still)*: `bytes_total: 829422`,
  `manifest_self: 5acbb952a4deff08…`, shipped-`MANIFEST.json` sha256
  `707dcf0b1c591c4817a4bd98c19c8a9e1f07b18a4bd7f6a9faaebe8fbedda0dd`.

The same command pinned to the *older* `generated_utc 2026-10-16T18:56:15Z` reproduces every count
and the same `manifest_self` but **not** the shipped bytes (that run yields sha256
`b6f66e9bb24fc982706a5c55e985b2e82da6e79c34b60cc3c8bb7f35c1da5aa5`).

### `check_manifest.py`
Independent re-hash of every listed file plus a tree walk for omissions.  Flags: `--package`
(required).  Prints exactly
`missing= hash_mismatch= size_mismatch= unlisted= listed_but_absent=` and exits non-zero if any is
non-zero.  `manifest_self_recomputes` is **information only** and does not drive the exit status
(therefore the tool is convention-agnostic).  Exit `0` pass · `1` a count is non-zero · `2` no
manifest.
Known-good on `scratch/uneutral10/package`: `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0
listed_but_absent=0`, `VERDICT PASS`, exit 0.  Append 1 byte to `results/REPORT.md` →
`hash_mismatch=1 size_mismatch=1`, `VERDICT FAIL`, exit 1.  Delete `LICENSE` and add
`NEWFILE.txt` → `missing=1 unlisted=1 listed_but_absent=1`, exit 1.
Intended difference from `scratch/uver24/check_manifest_uver24.py`: that script additionally
asserts the **inclusive** `counts.bytes_total == entries_sum + len(manifest)` and so reports
`VERDICT FAIL` (exit 1) on the shipped, exclusive-convention package; the five counts are identical.

### `gate.sh`
Positive-vocabulary acceptance gate.  A token passes only if it is a declared member of the tree's
own vocabulary: prose/source against `vocabulary/{english,code,public}.txt`; data
(`.json`/`.jsonl`) additionally against `vocabulary/data.txt`, which holds JSON object **keys
only** (keys mode).  The offender listing is **complete** (no cap); the checker never scans its own
`vocabulary/`; the load is **fail-closed**.
Flag: `--package` (required).  Environment: `GATE_JSON=1` emits a JSON summary line.
Exit `0` pass · `1` out-of-vocabulary tokens · `2` fail-closed (`FATAL:` on a missing **or empty**
vocabulary file) · `3` `--package` could not be resolved.
Known-good on `scratch/ugate2/dest/research-publish-packages`:
`flagged tokens: 1398` / `out-of-vocabulary token lines shown: 1398` / `GATE RESULT: FAIL`, exit 1 —
**byte-identical to** `scratch/ugate2/gate_scoped_v2.sh` when that is given the absolute root.  The
only intended difference is that this tool resolves `--package` to an absolute path.
`scratch/uneutral10/package` has no `vocabulary/` → exit 2 `FATAL: cannot read vocabulary file: …`.
Empty `vocabulary/english.txt` → exit 2 `FATAL: vocabulary file has no declared terms: …` (the
un-corrected `scratch/ugate1/gate_scoped.sh` instead reports 35405 OOV tokens and blames the tree).

### `md2tex.py`
One Markdown→LaTeX converter for every paper, replacing the per-paper copies that had drifted:
`scratch/uprep1/md2tex.py` (paper #3, 368 lines, sha256 `e4594f1727cf40e1de7388a2b892b16acc0e3fa4b134c9656e82f79afa107f50`,
consumed `papers/encoder-crossover-190/`) and `scratch/uprep7/md2tex.py` (paper #7, 429 lines, sha256
`ccad301dfd1b6dc1ac320dfdb34267ec03e5ab77c70b70a9653051ac404ceb2e`, consumed `papers/gated-read-batching/`);
my `diff -u` between them is 544 lines.  The two were **not** near-identical: they differ in bibliography
strategy (`.bib` file vs the numbered list inside the manuscript's own `## References`), in an optional
sanitisation stage (unit-id removal, markdown-link flattening, footnote-asterisk sentinel), in the unicode
map (by exactly two entries), in the citation-anchor table (13 vs 14) and in the guard set.

Flag: `--package` (required; one of the keys of the `PACKAGES` table).  Also `--paper-root`, `--outdir`,
`--quiet`, `--repo-root`.  Exit `0` wrote the outputs · `1` a guard fired (`SystemExit`) — the citation
guard always, plus where configured the unmapped/residual-non-ascii, expected-bibitem-count,
balanced-brace, drafting-artefact and author-slot guards · `2` unknown `--package` (argparse `choices`).

**Config.**  Per-paper values are the `PACKAGES` dict inside `md2tex.py`: one pure-data registry keyed by
slug, the single source of truth for anchors, unicode map, bibliography strategy, sanitisation rules and
guard settings.  Intended difference from the unit card: it asked for a TOML under `orchestration/packages/`,
but that path is outside this tool's declared write paths **and** `orchestration/packages/<slug>.toml` are
UBUILD1's own `schema = 1` build manifests consumed by `check_manifest.py` — adding md2tex keys there would
be an undeclared write and a foreign schema edit.  Migration path: lift `PACKAGES` verbatim into
`orchestration/packages/<slug>/md2tex.toml` and load it with `tomllib`; every value is already data.

**Known-good byte-identity** (measured: each regeneration is `cmp`-identical, `cmp` exit 0, to the shipped
artefact, and the `sha256` pairs are equal — this is the load-bearing result):

| package | output | shipped sha256 = regenerated sha256 |
|---|---|---|
| `encoder-crossover-190` | `papers/encoder-crossover-190/submission/main.tex` (83832 B) | `90db2cd4e7fa6a63d4b91e2c0636c3879de54fc2a4e7f55fcbf2cce4197c9b86` |
| `gated-read-batching` | `papers/gated-read-batching/submission/main.tex` (37291 B) | `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4` |
| `gated-read-batching` | `papers/gated-read-batching/submission/ABSTRACT.txt` | `59ef6d55d64d6a3c3b500ffb653e8f85c11fca9e841b1ff37fc8b43c0ef1a6e9` |
| `gated-read-batching` | `papers/gated-read-batching/submission/ABSTRACT_METADATA.txt` | `05ce7038056235b3bd52dd1f3dac3c048698701eac35cd779b3198192c88e962` |

Reproduce with `python3 tools/package/md2tex.py --package <slug> --outdir <tmp>` then
`cmp <tmp>/main.tex papers/<slug>/submission/main.tex` (add `ABSTRACT.txt`/`ABSTRACT_METADATA.txt` for
`gated-read-batching`); `tests/test_md2tex.py` re-checks all four pairs against the files on disk.

**Payload-volatile values.**  The four digests above describe one byte-state of two payloads: they are
**payload-volatile** — if a manuscript is edited the digest moves, and the correct response is to re-measure,
not to re-pin the old number.  The `PACKAGES` literals (the two anchor tables, the two unicode maps,
`ABSTRACT_METADATA.txt`, the `\renewcommand{\refname}` line, the two `\date{}` comment strings) are
**payload-volatile by construction**: each reproduces a specific corpus value, so they are carried verbatim
rather than rewritten and move only when the corpus moves.  The tool's own digest,
`c62feb657a14aa957f0ca2296435ce3820750af98d457acb0a4ac187d97867ec` (31714 B), is **source-volatile**:
any edit to the tool invalidates it.  **Note (UMDTEX1), 2026-10-16 UTC:** that digest and the `diff -u` line
count are the values measured at this append.

**Guard kept.**  The bidirectional citation guard — a `\bibitem` that is never cited, or a `\cite` with no
`\bibitem` — fails loudly for **both** strategies.  `tests/test_md2tex.py` proves it red→green end-to-end by
appending a genuinely uncited `.bib` entry to a copy of the paper (exit 1, key named) and removing it again
(exit 0, shipped bytes reproduced).  No paper file is touched by the test.

## Tests

`python3 tests/test_package_tools.py -v` (writes only under `scratch/upipe1/testtmp/`).


## Addendum --- third package `replay-record-not-decision` (unit UPAYLOAD2)

`PACKAGES` now holds three entries.  Measured with the current converter, regenerating each package
to a scratch outdir and comparing to the shipped file (`cmp`, byte-identical in every case):

| package | shipped `main.tex` | bytes | sha256 |
|---|---|---|---|
| `encoder-crossover-190` | `papers/encoder-crossover-190/submission/main.tex` | 84,358 | `4efa575442b2878037d625bc604e2ae7aab7e1faf9d9515bd9c9747ebf28885a` |
| `gated-read-batching` | `papers/gated-read-batching/submission/main.tex` | 37,291 | `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4` |
| `replay-record-not-decision` | `papers/replay-record-not-decision/submission/main.tex` | 20,631 | `0520d2059734f8381227fdf0bff51fd006bb88b46635419b7dbc07ddd5bdd0d5` |

**Correction:** the `encoder-crossover-190` row above is stale --- it recorded 83832 B /
`90db2cd4...`; the shipped file measures 84,358 B / `4efa5754...`, and that is what the current
converter reproduces.

Zero-bibliography papers: a package may set `cite_anchors=()`, `expected_bib_count=0` and
`bib_source="none"`; `expect_zero_bib` then asserts the output contains no citation apparatus at all,
and the pre-existing bidirectional `cite`/`bibitem` check stays active (it is non-vacuous even with
zero bib keys --- it rejects a `\\cite` with no entry).  A package may also set `author_line=None` to
ship no author block; a positive guard aborts if `\\author` appears anyway.  Targeted prose
de-naming is expressed as per-package `dename_rules` (literal old -> new), not as a blanket stripper;
a rule that matches nothing aborts the run.  The tarball remains a separate manual step: exactly one
member, `main.tex`.
