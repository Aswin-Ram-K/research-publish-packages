# VERIFICATION REPORT 22 (UVER22)

**Verdict: `pass`** — every UPACK1 claim I was asked to check reproduced, with three narrow qualifications
listed under *overstated* / *not_reproduced*. I wrote none of the checked work; my checker
(`scratch/uver22/rehash22.py`) is my own and was red→green tested.

Target: `scratch/ubij3/tree-three-r2` (release candidate), repaired by UPACK1 (`scratch/upack1/`).
Bound: 25 tool calls. Method: my own re-hash from disk, my own packaging count, an independent pre-image
search; the author's scripts were re-run only for comparison.

## 1. Manifest after — reproduced independently (my checker, not theirs)

`python3 scratch/uver22/rehash22.py` (literal output in `scratch/uver22/red-green.log`, GREEN section):

- `real files: 45`; `real bytes (all files, manifest included): 3008378`; `MANIFEST.json own size: 21873`.
- `manifest counts.files=45 (real 45)`; `counts.bytes_total=3008378`.
- `files[] entries: 44`; `listed-but-absent (0): []`; `present-but-unlisted, excluding MANIFEST.json (0): []`.
- `stale sha256 (0): []`; `size mismatches (0): []` → `VERDICT: PASS`, exit 0.
- MANIFEST.json sha256 = `f3e4a22c49261ca937311b1d4edf2e8e52d347faed5d1a4f70d93e41b71fc614` — matches the
  claimed `f3e4a22c…`.
- UPACK1's `scratch/upack1/check_manifest.py` re-run: byte-for-byte the output they quote
  (`tree: 45 files, 3008378 bytes` … `VERDICT: PASS`), exit 0. My checker and theirs agree on every figure.

## 2. Manifest before — reproduced independently, because a pre-image still exists

The pre-repair twin is still on disk: `scratch/ubij3/tree-three-b` (and `tree-three-run`) carry the old
manifest. `sha256sum scratch/ubij3/tree-three-b/MANIFEST.json` =
`0553ea51672cb7f8ffa743300e8ee30470b6880870f397db85e6fe66cc993d8c` — exactly the claimed before-hash.
My checker (not UPACK1's) against it reproduces every before-fact, plus one unclaimed:

```
manifest counts.files=42 (real 45)   counts.bytes_total=5070428   files[] entries: 42
listed-but-absent (2): ['INTEGRITY.md', 'README.md']
present-but-unlisted, excluding MANIFEST.json (4):
  ['variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts',
   'variants/no-union/files/fixture/reflex-decisions.ts',
   'verify/recompute-claims.py', 'verify/redaction-log.json']
stale sha256 (34): [...]   size mismatches (34): [...]   VERDICT: FAIL (exit 1)
```

42 entries / 34 stale / 2 phantom / 4 omitted / 5,070,428 bytes all reproduce from disk. (5,070,428
describes neither the pre-repair tree — inclusive 3,006,637 — nor the shipped one; it is the as-audited
figure carried in from `uneutral4`/`ubij1`, as the manifest's own `amended_by` note says.)

## 3. Fixed-point `bytes_total` ruling — coherent, and it must include the manifest

`bytes_total = 3,008,378` equals the total **including** `MANIFEST.json` (21,873 B), not excluding it:

- inclusive total = 3,008,378 → **MATCH**; exclusive total = 2,986,505 → DIFFER;
- identity `2,986,505 + 21,873 = 3,008,378` holds exactly.

A genuine self-consistent fixed point: an exclusive total (2,986,505, 7 digits) cannot satisfy the identity,
because the manifest carrying it still occupies 21,873 bytes. The inclusive reading is the only one whose
recorded digits describe the file that carries them. Coherent, not a defect.

## 4. Packaging surface — shipped procedure reproduces its own figures

`python3 scratch/upack1/packaging_surface.py` prints `file entries: 45`, `file basenames: 43 distinct
(45 files, 2 duplicate-basename pairs)`, `directory entries: 12 (including root '.')`, `directory names:
10 distinct (excluding root)`, and explicitly `UNREPRODUCED (no shipped procedure; not re-derived here):
309 raw / 240 de-overlapped / 187 in non-JSON text`. My own `find`/`sort -u` count of the same surface gave
**45 / 43 / 12 / 11 / 10** — matching. "11 directory entries excluding root" is the 12-including-root
figure read correctly; the 2 duplicate basenames are `DECISION_CASE_SCHEMA.ts` and `reflex-decisions.ts`
(`fixture/` and `variants/no-union/files/fixture/`). The retraction of 309/240/187 and the withdrawal of
"44 file names" are supported by a shipped, runnable procedure.

## 5. `measure.sh` removal — nothing orphaned in the tree; two dangling doc references survive

- Emitted tree: `grep -rn "measure\.sh" scratch/ubij3/tree-three-r2/` → **0 hits**.
- `strategy/SHIP_SET_INTEGRITY.md:65,67,74,153` and `strategy/VERIFICATION_REPORT_20.md:99,101,102` are the
  removal record itself (they describe/bypass the removal) — not orphans. UBIJ3.md's own §Next unit hint /
  §Reproduce references are covered by the appended note ("Also superseded: … was removed").
- **Still dangling, un-annotated:** `strategy/COHERENT_BIJECTION_EXTENSION_2.md:358` — the *Reproduce*
  section still instructs `bash scratch/ubij3/measure.sh`; `strategy/VERIFICATION_REPORT_19.md:10` — a
  checklist item `- [ ] measure.sh reproduces UBIJ3 numbers`. Neither resolves now.

## 6. `orchestration/units/UBIJ3.md` — note appended, original text intact (structurally)

180 lines; original headings in order (`Purpose` :8, `Write paths` :15, `What was built` :27, `Results` :85,
`Packaging surface` :113, `Verdict` :125, `Blocker` :133, `Next unit hint` :140), then
`## Dated correction note — 2026-10-16 (UPACK1)` at :150. Every original number the note narrows is still
present verbatim (45 files / 3,006,637 bytes; 309/240/187; "44 file names and 11 directory names";
`26c5ddcb…`; the Fix-2 "byte-identical to the baseline" sentence; the results table). **No pre-appendix
snapshot of this file exists anywhere on disk** (searched `state/logs/` and the tree), so survival is
verified structurally — note is last, after a `---` separator, no original section missing or reordered —
not by diff. Recorded under *unverified*.

## 7. Containment — established more strongly than UPACK1's own mtime argument

- `diff -rq scratch/ubij3/tree-three-r2 scratch/ubij3/tree-three-b` → only
  `Files …/MANIFEST.json and …/MANIFEST.json differ` (exit 1, one line).
- Byte totals: both trees 45 files; exclusive-of-manifest totals **identical at 2,986,505**.
- Growth: 3,006,637 → 3,008,378 = **+1,741** = `21,873 − 20,132` (new vs old manifest size).
- In the shipped tree only `MANIFEST.json` has a post-build mtime (21:39:05); all others 21:21 or earlier.

Established: the 44 non-manifest files shipped now are byte-identical to the pre-repair twin whose manifest
carries `0553ea51…` — the manifest UVER20 verified the defects in. **Not** established: `tree-three-b` is
not an authenticated snapshot of what UVER20 read, so "UVER20 saw exactly these 44 files" is a strong
inference from the matching pre-repair manifest hash, not a proof; no earlier pre-image exists on disk.
Consequently `MANIFEST.json`'s own sha256 has changed since UVER20 (`0553ea51…` → `f3e4a22c…`): UVER20's
verification of the manifest file itself is superseded, while its verification of the other 44 files stands.

## 8. Red→green (my checker can fail)

```
### GREEN - my checker on the real shipped tree (scratch/ubij3/tree-three-r2)
tree root: /home/zer0null/reserach extarctor/scratch/ubij3/tree-three-r2
real files: 45
real bytes (all files, manifest included): 3008378
real bytes (excluding MANIFEST.json): 2986505
MANIFEST.json own size: 21873
manifest counts.files=45 (real 45)
manifest counts.bytes_total=3008378
self-reference: bytes_total vs inclusive total -> MATCH
self-reference: bytes_total vs exclusive total -> DIFFER
self-reference check: exclusive_total + manifest_size = 3008378
files[] entries: 44
listed-but-absent (0): []
present-but-unlisted, excluding MANIFEST.json (0): []
stale sha256 (0): []
size mismatches (0): []
summary: 0 missing, 0 hash mismatches, 0 size mismatches
VERDICT: PASS
[exit code: 0]

### RED - same checker on scratch/uver22/redtree (one file byte-flipped in place + one manifest
### entry's recorded sha256 altered in place; both edits length-preserving, so no size or
### self-reference fault is introduced)
tree root: scratch/uver22/redtree
real files: 45
real bytes (all files, manifest included): 3008378
real bytes (excluding MANIFEST.json): 2986505
MANIFEST.json own size: 21873
manifest counts.files=45 (real 45)
manifest counts.bytes_total=3008378
self-reference: bytes_total vs inclusive total -> MATCH
self-reference: bytes_total vs exclusive total -> DIFFER
self-reference check: exclusive_total + manifest_size = 3008378
files[] entries: 44
listed-but-absent (0): []
present-but-unlisted, excluding MANIFEST.json (0): []
stale sha256 (2): ['EXCLUDED.md', 'verify/redaction-log.json']
size mismatches (0): []
summary: 0 missing, 2 hash mismatches, 0 size mismatches
VERDICT: FAIL
[exit code: 1]
```

The perturbed copy fails with exactly the two injected faults — 2 stale sha256, 0 missing, 0 size
mismatches — with the self-reference identity still MATCHing, so the failure is attributable to the injected
content faults alone; the real tree passes. A checker that cannot fail proves nothing; this one can.

## 9. Findings beyond the six claims

- **`not_reproduced` — the appended note's "78 differing lines" for `harness/tccommon.py`.** No baseline or
  metric I tried yields 78. Against `repro/encoder-crossover-190-SANITISED/harness/tccommon.py`
  (byte-identical to `scratch/uneutral3/tree-stripped/harness/tccommon.py`): 26 changed line-pairs, 84
  default-`diff` output lines, 129 unified-diff lines, 8 hunks. The same baseline gives `prepare.py`
  **exactly 44 default-`diff` lines** (13 changed line-pairs) — the note's second figure — so the likely
  metric is "default diff output lines" and the `tccommon.py` figure is 6 lines off, or was measured on an
  unnamed revision. The *direction* of the narrowing is fully corroborated: the files as wholes do differ.
  The exact line-identity claims also hold — `harness/tccommon.py:118` and `harness/prepare.py:148` are
  textually identical to the baseline.
- The pre-repair manifest also had **34 size mismatches** (unclaimed, consistent with 34 stale hashes).

## Verdict lists

- **contradicted:** (none)
- **overstated:** (1) "removing `measure.sh` orphaned nothing" — true of the emitted tree (0 refs), but two
  strategy docs still dangle (§5). (2) UPACK1's containment evidence as stated is an mtime window, weaker
  than what the disk supports (§7); the claim itself is confirmed.
- **not_reproduced:** (1) the appended note's "`tccommon.py` 78 diff lines" (§9).
- **unverified:** (1) the restated invariant "byte-identity across 1,001 records / 2,380 fields with
  inside-stimulus delta 0" (carried from UVER20, not re-derived under this bound); (2) stimulus-only digest
  `26c5ddcb…` (the note itself marks it unreproduced); (3) projection digest `620e4a07…` (needs the
  unshipped `second-labeller/cases.json`); (4) UBIJ3.md's original text by diff — no pre-appendix snapshot
  exists, so only structural survival was provable.
