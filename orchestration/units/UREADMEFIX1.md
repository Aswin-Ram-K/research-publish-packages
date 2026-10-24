# UREADMEFIX1 — fix reader-unactionable paths on the deposit front page

**Purpose.** The Zenodo upload artifact `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`
had one remaining defect: its front page `README_DEPOSIT.md` told readers to use paths they cannot have
(`scratch/uneutral10/package/`, four times) and a tool that does not ship (`tools/package/check_manifest.py`,
three times). Find every reader-unactionable reference, rewrite only those, change no number, regenerate
the manifest with the project tool, rebuild the archive deterministically, re-verify.

**Bound.** 30 tool calls. Used **22**.

**Declared write paths (card).** `scratch/uneutral10/package/README_DEPOSIT.md`,
`scratch/uneutral10/package/MANIFEST.json` (via `regen_manifest.py` only), the rebuilt tarball,
`scratch/ureadamefix1/**`, own card, own handoff.

## Card-vs-disk disagreement (reported, not silently worked around)

The card says to rewrite `scratch/uneutral10/package/README_DEPOSIT.md`. **That file does not exist**
(`ls` → exit 2, "No such file or directory"); the package tree is the 29 files
`COMMERCIAL.md CONTRIBUTING.md LICENSE MANIFEST.json README.md fixture/ preregistration/ results/
second-labeller/ verify/`. The shipped front page is
`papers/encoder-crossover-190/released/README_DEPOSIT.md` — sha256
`503751f19ad71f6efa4d42217449948178b164521d4acc37ca9ddc4834970085`, byte-identical to the archive
member, and the `$FRONT` input of `scratch/ufixman1/build_archive.sh:29`. That is the file edited. It is
**not** one of the 29 package files (it is one of the two deposit extras), so adding it to the package
would have broken the 29-file invariant and `build_archive.sh`'s `n=29` check; it was not added.

Other card claim that disagreed: the literal `regen_manifest.py --package scratch/uneutral10/package
--no-note` has no `--generated-utc`, so it would rewrite `generated_utc` and change the package
`MANIFEST.json` bytes, contradicting "the only difference … is your edited README and the manifest line
for it". It was run with `--generated-utc 2026-10-18T08:05:47Z` (the pinned build epoch, same tool,
never by hand) and reproduced the package manifest **byte-for-byte** (`cmp` exit 0).

## Complete sweep (every member of the extracted archive)

Command: `grep -rn -E 'scratch/|tools/package|orchestration/|reserach extarctor|…' .`

| file:line | reference | class |
|---|---|---|
| `README_DEPOSIT.md:132` | `` `scratch/uneutral10/package/` `` table row | (b) unactionable path → **rewritten** |
| `README_DEPOSIT.md:147` | "a checkout of `scratch/uneutral10/package/`" | (b) broken instruction → **rewritten** |
| `README_DEPOSIT.md:186` | `` `tools/package/check_manifest.py` `` | (b) non-shipped tool → **rewritten** |
| `README_DEPOSIT.md:193` | `python3 tools/package/check_manifest.py --package <extracted-archive-root>` | (b) broken command → **rewritten** |
| `README_DEPOSIT.md:202` | `python3 tools/package/check_manifest.py --package scratch/uneutral10/package` | (b) broken command → **rewritten** |
| `README_DEPOSIT.md:209` | `` `scratch/uneutral10/package/` `` in assembly prose | (b) unactionable path → **rewritten** |
| `README_DEPOSIT.md:215` | `` `tools/package/regen_manifest.py` `` in assembly prose | (c) historical prose naming a non-shipped tool → **rewritten** |
| `results/REPORT.md:194` | `` tools/trace.ts append `` | (c) historical prose, author-side tool — **reported, not edited** (out of scope) |
| `second-labeller/RUN.json:158` | `journal/`, `strategy tree`, `units' jobs/` | (c) historical prose, internal vocabulary — **reported, not edited** (out of scope) |
| `fixture/reflex-decisions.ts:780,945`; `fixture/fixture-190.json:879,1089`; `second-labeller/blinded_cases.json:684,849`; `second-labeller/cases.json:944,1169` | `tools/list` (MCP method) | (c) harmless — domain term, **not a path** |

Shipped reader-runnable tools are exactly `verify/recompute-claims.py`, `second-labeller/parse_fixture.py`,
`second-labeller/compare.py`; the inline `MANIFEST.json` re-hash heredocs also ship. The rewritten text
uses only those.

## Evidence

- Numeric-literal multiset (regex `\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b`): BEFORE 90 tokens / 38 distinct;
  AFTER 90 / 38; difference **EMPTY**; `MULTISET IDENTICAL: True`.
- `regen_manifest.py … --generated-utc 2026-10-18T08:05:47Z`: `files_on_disk: 29 bytes_total: 832286`;
  `files[] entries: 28`; `added: [] changed: 0`; sha256 `fecdc1fb…`; `cmp` vs backup exit 0.
- Build: two `tar|gzip` runs `cmp` exit 0. New archive **159,014 B**, sha256
  `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7`, md5
  `4066c3428c1e4836d200909c6a2db6b0`, members 37.
- Archive `MANIFEST.json`: listed 30, `counts.files` 31, `counts.bytes_total` 844,708, `manifest_self`
  `a4d6767c…`.
- `check_manifest.py --package <extracted archive root>`:
  `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `manifest_self_recomputes=True`,
  `VERDICT PASS`, exit **0** — identical before and after the shipped tools ran.
- `verify/recompute-claims.py` exit **0**, `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`,
  fixture digest `c7696edc…`. `second-labeller/parse_fixture.py` exit **0**. `second-labeller/compare.py`
  exit **0**.
- `diff -rq` PRE-EDIT extraction vs REBUILT extraction: only `MANIFEST.json` and `README_DEPOSIT.md`
  differ; the only moved manifest entry is `README_DEPOSIT.md` (10,477 B `503751f1…` → 10,585 B
  `71f76e60…`); `counts.bytes_total` 844,600 → 844,708.
- `grep -rn -E 'scratch/|tools/package'` over the extracted rebuilt archive → **(none)**.

## Superseded

Old archive 158,956 B sha256 `bcdbf75e…` (card and `strategy/DEPOSIT_ARCHIVE.md`) is superseded.
