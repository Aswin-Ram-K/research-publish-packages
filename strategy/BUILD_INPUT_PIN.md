# BUILD_INPUT_PIN.md — what can and cannot be pinned about the build's input

**Unit:** UGATE1 · **Date:** 2026-10-16 · **Subject:** the provenance of the release build's default
input tree, `scratch/ubij3/tree-three-r2`, and of the staged bytes it was re-tagged from.

**Headline:** the input's identity **cannot be pinned retroactively** — `MANIFEST.json` records no digest
of the tree it was derived from. What *can* be pinned is recorded below, and it is enough to say that
**no staged byte can have changed since derivation, by the available evidence**. That is a weaker claim
than "frozen", and the staged bytes **must never be called frozen.**

---

## 1. The two trees, and which one the build consumes

| tree | files | role |
|---|---|---|
| `repro/encoder-crossover-190-SANITISED/` | **59** = **46 staged** + **13 non-staged** | the sanitised source; the staged buckets are what everything derives from |
| `scratch/ubij3/tree-three-r2/` | **45** | the re-tagged tree — the release build's **default input** (`strategy/BUILD_WIRING.md`) |

The 59/46/13 split attributed in the literature to the build's input is in fact the **sanitised** tree's
split; `tree-three-r2` holds the 45 re-tagged staged paths. The 13 non-staged files are the mutable
top-level documents — `EXCLUDED.md`, `INTEGRITY.md`, `LICENCE_TODO.md`, `MANIFEST.json`, `README.md`,
`REDACT3_REPORT.md`, `REDACTION_REPORT.md`, `RESIDUALS.md`, `SCRUB_REPORT.md`, `redact.py`, and
`variants/no-union/{README.md, files/fixture/DECISION_CASE_SCHEMA.ts, files/fixture/reflex-decisions.ts}`.
`REDACT3_REPORT.md` was added mid-batch by a concurrent unit — **that is why the sanitised source tree
is not frozen.**

## 2. Staged aggregate digest — reproduced independently

```
0b79908422a3f79785ee5ec4640498e302a913bfb3bd97007d86b4f6717a25a5
```

**Definition (this is the convention that reproduces it, verified 2026-10-16):** sha256 of the
newline-joined, **sorted-by-path** `"<file sha256>  <path relative to repro/encoder-crossover-190-SANITISED>"` lines
over the **46 staged files** (buckets `fixture/ harness/ verify/ preregistration/ results/ second-labeller/`),
with a trailing newline. Earlier attempts that sorted the joined *lines* rather than the *paths* do not
reproduce it — record the convention, not just the value.

## 3. Staged bytes vs `INTEGRITY.md` — re-hashed, 0 mismatches

Recomputed from disk, not copied from a report:

| result | count |
|---|---|
| staged files with an `INTEGRITY.md` sha256 row that **matches** | **38** |
| staged files with a row that **mismatches** | **0** |
| staged files with **no** `INTEGRITY.md` row | **8** |

The 8 without a row are exactly the `verify/*` files:

```
verify/RECOMPUTE-CLAIMS.txt   verify/RESIDUAL-SCAN.txt   verify/VERIFICATION.txt
verify/integrity-table.md     verify/recompute-claims.py verify/redaction-log.json
verify/run-verification.sh    verify/scrub-uscrub1.py
```

They are covered instead by the record of the 8 per-file digests in the UWIRE2 handoff.

## 4. Times

| what | mtime (UTC) |
|---|---|
| newest **staged** file — `verify/scrub-uscrub1.py` | **2026-10-15T23:30:14Z** |
| `repro/encoder-crossover-190-SANITISED/INTEGRITY.md` | 2026-10-16T00:02:10Z |
| `scratch/ubij3/tree-three-r2/MANIFEST.json` | 2026-10-16T02:39:05Z (the tree's newest mtime) |

The newest staged byte **predates** both the integrity instrument and the derivation, which is what
supports the "unchanged since derivation" claim. (UWIRE2 records `18:30:14` for the same file — that is
local time, UTC+5.)

## 5. The input tree itself — a digest this unit computed

`scratch/ubij3/tree-three-r2/MANIFEST.json` reports `counts.files = 45`, `counts.bytes_total = 3,008,378`,
and a `digests` object holding **only**:

```
instrument_sha256   = 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796
exp11_corpus_sha256 = c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66
```

**There is no digest of the tree this one was derived from.** The input's identity therefore cannot be
pinned retroactively — the best available binding is the aggregate digest of the tree *as it now stands*,
computed here for future comparison (same convention as §2, paths relative to `tree-three-r2`):

```
64137bfc1936d2f634bb1a6ad1a561e2b1d136d52d936ff3dfa69601c406b9ae
```

This is a **pin on the current bytes, not on their provenance**: it can detect a later edit, and it
cannot prove what the tree was before `MANIFEST.json` was written at 2026-10-16T02:39:05Z.

## 6. The honest statement to carry forward

* The **staged** bytes (the 46) are unchanged **by the available evidence** — 38 of 38 recorded digests
  match, 0 mismatch, and the newest staged mtime predates the integrity instrument and the derivation.
* The **tree as a whole**, including its mutable top level (13 non-staged files, and `MANIFEST.json`
  which is itself the newest file in the tree), is **not frozen**. Adding `REDACT3_REPORT.md` mid-batch
  is the demonstration.
* **Do not write the word "frozen" next to `tree-three-r2`.** Use *"unchanged by the available
  evidence, identity not retroactively pinable."*
* Nothing inside `scratch/ubij3/tree-three-r2/` was modified by this unit — those exact bytes were
  verified by two independent units and any edit invalidates that verification.

## 7. Containment

Read-only. No file under `scratch/ubij3/**` or `repro/**` was written; this pin is a record, and the
only file this unit created about the input is this one. No git command was run against
`/home/zer0null/Duval`.
