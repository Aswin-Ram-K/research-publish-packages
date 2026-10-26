# VERIFICATION_REPORT_PKG10 — independent check of UFIXPKG10

**Verifier:** UVERPKG10 (I authored none of the artifacts under review).
**Date of measurement:** 2026-10-16, ~18:1x–18:2x workspace time. All numbers below were measured by
me on disk in this session; none is quoted from UFIXPKG10's handoff.
**Bound:** 20 tool calls; used 13. **Writes:** this file, my card, my handoff, `scratch/uverpkg10/**` only.
**Concurrency:** `tools/package/README.md` was being rewritten by `UFIXPKG11` while I ran. I snapshotted
it at 18:11:33 to `scratch/uverpkg10/README.snapshot.md` (sha256
`1e0910a1dd7c4abd9e119b87c299cc7b79902ba2c01d9302e0dd15768da760ea`) and judge **that** state. The live
file has since changed (sha256 `5bd88bc9726580de1e5f1c37a2b2b0b1f5c7b8fd48a7becfb26b41674c0c8eba`,
mtime 18:12:34, i.e. UFIXPKG11's write); its current bytes are **not** the object of this verdict.

## Verdict: PASS (partial on attribution and on two sub-claims; see §5)

---

## 1. Claim A — the stale published digest

### 1.1 Ground truth (my own `stat`/`sha256sum`)
- `scratch/uneutral10/package/fixture/reflex-decisions.ts` — **81,439 B**, sha256
  `89e77a8e24a907f06345a45485c013799e08c806cc9d8f075db7709fbfd8e169` (mtime 18:00:35).
- `scratch/uneutral10/package/MANIFEST.json` entry for that file (`:72–:76`): `source_sha256`
  `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`, `.sha256`
  `89e77a8e24a907f06345a45485c013799e08c806cc9d8f075db7709fbfd8e169` (`:75`), `.bytes` `81439` (`:76`),
  `identical_to_source: false`, `kind: "copy"`.
- **The manifest entry agrees with the bytes on disk.** The handoff's `.sha256 :75` / `.bytes :76` line
  references are correct.

### 1.2 Published sites now match that truth
| site | what it now publishes | matches measured truth |
|---|---|---|
| `papers/encoder-crossover-190/CLAIMS.md:46` | `89e77a8e…e169`, 81,439 bytes (+ dated note quoting the old value) | yes |
| `papers/encoder-crossover-190/CLAIMS.md:47` | `89e77a8e…e169` (`MANIFEST.json .sha256 :75`; 81,439 bytes `:76`) | yes |
| `papers/encoder-crossover-190/MANUSCRIPT.md:802` | `89e77a8e…e169` | yes |
| `papers/encoder-crossover-190/submission/main.tex:408` | `89e77a8e…e169` | yes |

`CLAIMS.md:46`'s value column is still `076164ac…` — correct, because that row is about the **as-audited
instrument digest**; the shipped-copy digest lives in the parenthetical/note.

### 1.3 Every surviving occurrence of the old digest, classified
Workspace-wide literal sweep for `369159b0` (excluding `.venv`, `.git`, `node_modules`) found it in
**no shipped/paper publication** except one dated correction note, plus internal records:

- **Cited history (legitimate):** `papers/encoder-crossover-190/CLAIMS.md:46` — the explicit
  "published `369159b0…f78d` was stale … corrected 2026-10-16 (UFIXPKG10)" note. This is the only
  occurrence anywhere under `papers/`.
- **Internal dated build records / process artifacts (not paper publications; outside the unit's write
  paths, so un-fixable by it):** `strategy/RESIDUAL_TRIAGE_3.md:231,240`, `strategy/RELEASE_BUILD_3.md:315,321`,
  `orchestration/units/UFIXPAPER3.md:21`, `orchestration/handoffs/{UFIXPKG9.json:18,24, UFIXPAPER3.json:14,16, URESID3.json:21}`.
  **Caveat worth recording:** `strategy/RELEASE_BUILD_3.md:321` still says in the present tense that
  "`MANUSCRIPT.md:800-802` now pairs the shipped path with the shipped digest `369159b0…`" — that is now
  false, but it is a dated record of release-build job 3, not a live citation of the paper.
- **Concurrent-unit copy:** `scratch/ufixpkg11/pkgcopy/second-labeller/RUN.json:12` (also still says
  81,284 B — UFIXPKG11's in-flight copy, not a published site).
- **Historical scratch snapshots:** `scratch/urelease3/…`, `scratch/ufixtree1/…`, `scratch/ubuildall1/…`,
  `scratch/ufixpkg3/…`, `scratch/uverdriver1/…` (dated pre-fix trees).

So: **no live paper publication still carries the old digest; the one paper-tree occurrence is explicitly
labelled history.**

### 1.4 The near-miss — `AVAILABILITY.md:22` is correctly left alone
- `papers/encoder-crossover-190/AVAILABILITY.md:16` states "All paths below are under
  `repro/encoder-crossover-190/`"; `:22` cites `fixture/reflex-decisions.ts` sha256 `076164ac…`.
- I measured `repro/encoder-crossover-190/fixture/reflex-decisions.ts`: **145,031 B**,
  `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`.
- So `:22` resolves to the **as-audited source** under `repro/`, whose digest is `076164ac…`: the citation
  is correct for that path, and the section preamble justifies it. Leaving it unchanged is right.
  (Latent mismatch, pre-existing and out of scope: the row's label says "sealed 190-case fixture" while
  the digest is the instrument source's. Nothing to do with UFIXPKG10's two named defects.)

### 1.5 Generator re-run on a copy — byte-identical, exactly one line of drift
I patched only the `ROOT` constant of a **copy** of `scratch/uprep1/md2tex.py` to point at
`scratch/uverpkg10/mdrun/papers/encoder-crossover-190/` (holding copies of `MANUSCRIPT.md`,
`REFERENCES.bib`) and ran it twice:
- run 1 rc=0, run 2 rc=0; `cmp` → **runs byte-identical**.
- generated output `cmp` live `papers/encoder-crossover-190/submission/main.tex` → **byte-identical**
  (so the live file was not hand-patched).
- `diff scratch/ufixpkg10/main.before.tex <generated>` → **exactly one hunk, `408c408`**, changing only
  the shipped-instrument digest `369159b0…f78d` → `89e77a8e…e169`. `main.before.tex` independently
  carries the old digest at `:408`, so the "before" really is the pre-edit state.
- Live `main.tex` sha256 after my runs is still
  `90db2cd4e7fa6a63d4b91e2c0636c3879de54fc2a4e7f55fcbf2cce4197c9b86` (83,832 B) — **I disturbed nothing**.

### 1.6 Tarball — tested, not trusted
- `tar -tzf` → **exactly 1 member** (`main.tex`, 83,832 B).
- `tar -xzOf … | cmp - submission/main.tex` → **CMP_OK** (extracted bytes identical to on-disk source).
- tarball 28,569 B, sha256 `d5e49ad5a96c478d280579c79d5c6e542d3ca770146b62c7c0ae498a9783e795`.
- `BUILD_NOTES.md:143–149` independently states the new digest, the main.tex hash, and the one-member
  tarball; it also says earlier size/hash figures above are superseded, which disambiguates its own
  history. Consistent with my measurements.

---

## 2. Claim B — the stale test expectation

### 2.1 The expectation as shipped (`tests/test_package_tools.py:104–130`)
`test_census_reproduces_documented_totals_on_shipped_package` pins `files scanned: 29`,
`distinct identifiers hit: 15 of 184`, `TOTAL OCCURRENCES (decoded walk): 66`,
`inside stimulus …: 20  distinct=1`, `outside stimulus …: 46`, `JSON object keys: 0`, and the class
totals `data-jsonl-other 2 / json 35 / prose-md 12 / tooling 11 / ts 6`, on
`PKG = <ws>/scratch/uneutral10/package` (`:20`).

### 2.2 My own independent census (not UFIXPKG10's script)
`scratch/uverpkg10/census_mine.py` — written from the *definition* in `census.py`'s docstring
(in-stimulus = string values of `question`/`options`/`situation`; other string values outside; object
keys separate; `.json/.jsonl` decoded, everything else raw case-insensitive text), with my own TSV parse
of `scratch/uagnostic1/census.tsv` column 2 (184 ids), my own `os.walk` + string emitter. It reproduces
**all 12 quantities exactly**:

```
files scanned: 29        distinct identifiers hit: 15 of 184
TOTAL: 66                inside: 20 distinct=1
outside: 46              keys: 0
data-jsonl-other 2 | json 35 | prose-md 12 | tooling 11 | ts 6
```
`tools/package/census.py --package scratch/uneutral10/package` (rc=0) prints the identical block, so the
test's pinned strings match what the tool prints on the shipped tree. The earlier `18 of 184 / 75` was the
tree-before-the-payload-cleanup value; the current shipped tree genuinely contains 15 of the 184 census
identifiers in 66 occurrences.

### 2.3 Honesty question — documented, not merely bent
- The test carries an explicit dated note (`:110–117`): the totals "legitimately moved on 2026-10-16
  (UFIXPKG10)"; it names the mechanism (units removed identifiers from the shipped tree, five comments
  removed from `fixture/reflex-decisions.ts`); it states "**A further move is a real regression** unless
  another unit again changes the shipped tree, in which case the authoritative totals in
  `tools/package/README.md` must be updated in the same change."
- The README snapshot does carry the matching change: `README` `:89` (`15 of 184`, `TOTAL …: 66`) and a
  "Note 2026-10-16 (UFIXPKG10)" at `:96–100` recording the move and citing an independently written census
  (`scratch/ufixpkg10/independent_census.py`, 12/12 quantities). So the test's own precondition was met.
- The expectation is therefore pinned to a **derived quantity that I reproduced with a third method**,
  and it is falsifiable: my reverted copy (§4) fails. I judge this a real correction, not a test bent to
  whatever the tool prints. Residual caveat: UFIXPKG10's "independent" script was written by the same
  author as the test edit; that is why I re-derived it myself rather than crediting theirs.

### 2.4 Tests — how I ran them, and the collection failure
- `python3 -m pytest tests/test_package_tools.py -q` → **rc=4**, `ImportError while loading conftest
  tests/conftest.py:19: from resextract.llm import OccamyClient → ModuleNotFoundError: No module named
  'resextract'`. **The wider suite cannot collect here**; the conftest import is the blocker, as claimed.
- `python3 -m pytest tests/test_package_tools.py --noconftest -q` → **rc=0, 5 passed in 1.93s**.
- `python3 tests/test_package_tools.py` (direct) → **rc=0, Ran 5 tests … OK**.
- (The handoff also cites `python3 tests/test_ufixpkg8_tag_re.py` rc=0, but its captured output file
  `scratch/ufixpkg10/direct_tagre.out` is **0 bytes**; I did not re-run it, so that evidence line is
  unverifiable from the artifacts. It is not load-bearing for either claim.)

### 2.5 No other published number moved — the three payload tools, re-run on a byte-identical copy
I ran the payload's three tools in `scratch/uverpkg10/pkgcopy` (a `cp -a` copy of
`scratch/uneutral10/package`) so the shipped artifacts were not touched:

| tool | exit code | key output |
|---|---|---|
| `verify/recompute-claims.py` | **0** | `VERDICT: PASS`; `ALL PUBLISHED NUMBERS REPRODUCED: True`; route-A kappa published 0.3252 vs tree 0.3248813212427869 reproduced=True; A/B mutual agreement published 0.3684 vs tree 0.3684210526315789 reproduced=True; **fixture-correctness projection digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`** |
| `second-labeller/parse_fixture.py` | **0** | clean parse (empty `near_duplicate_questions` / `answer_outside_option_set` / `bad_option_arity`) |
| `second-labeller/compare.py` | **0** | route-B kappa **0.9013584840356494**, route-B agreement 0.9052631578947369, `AB_mutual_agreement` **0.3684210526315789**, n_disagreements 18 |

Route-B pairwise kappa, the A/B mutual agreement and the fixture-correctness projection digest are all
**unmoved** and consistent with the published values.

---

## 3. Red→green (non-vacuous)
1. **Digest fix.** Extracting the shipped-instrument digest from line 408 and comparing it with
   `sha256sum` of the shipped file: on `scratch/ufixpkg10/main.before.tex` → **RED**
   (`369159b0…` ≠ `89e77a8e…`); on the live `main.tex` → **GREEN** (equal). Non-vacuous because the
   pre-edit state exists on disk and genuinely fails the predicate; the check is a real content
   comparison, not a tautology.
2. **Census fix.** Copying the test to `scratch/uverpkg10/test_reverted.py` and reverting only the two
   pinned numbers to `18 of 184` / `75` → `pytest --noconftest` **rc=1, 5 failed**; the live file
   **rc=0, 5 passed**. Non-vacuous because the census tool output is fixed by the shipped tree, so the
   old expectation can no longer be satisfied — the test really does discriminate old from new.

---

## 4. Write-path containment (content + mtimes, attributed)
Non-scratch files with mtime in UFIXPKG10's working window (18:07 card → 18:10:50 handoff):

| time | file | inside declared write paths? |
|---|---|---|
| 18:07:21 | `orchestration/units/UFIXPKG10.md` | own card (required) |
| 18:09:33 | `papers/encoder-crossover-190/CLAIMS.md` | yes |
| 18:09:33 | `papers/encoder-crossover-190/MANUSCRIPT.md` | yes |
| 18:09:34 | `papers/encoder-crossover-190/submission/main.tex` | yes |
| 18:09:34 | `papers/encoder-crossover-190/submission/encoder-crossover-190.tar.gz` | yes |
| 18:09:57 | `tests/test_package_tools.py` | yes |
| 18:10:10 | `papers/encoder-crossover-190/submission/BUILD_NOTES.md` | yes |
| 18:10:50 | `orchestration/handoffs/UFIXPKG10.json` | yes |

**No file outside the declared paths was written by UFIXPKG10**, as far as mtime/content can establish.
Attribution of the surrounding churn:
- `tools/package/README.md` mtime **18:12:34** — *after* UFIXPKG10's handoff (18:10:50) and just before
  `orchestration/handoffs/UFIXPKG11.json` (18:12:43): that write is **UFIXPKG11's**. UFIXPKG10's README
  content is visible in my 18:11:33 snapshot, so its edit landed earlier in the same window; I cannot
  split the README's bytes between the two units by mtime alone. (No write-path clash was declared to me.)
- `tools/package/gate.sh` and `tests/test_ufixpkg8_tag_re.py` (both 18:06:09) and
  `tests/__pycache__/**` (18:05:39, 18:10:46) predate/parallel UFIXPKG10 and belong to other units or to
  generated bytecode, not to UFIXPKG10's edits.
- `strategy/LEAD_PACKAGE.md` (18:19), `strategy/OUTSIDE_TOKEN_REDACTION.md` (18:03): the separate
  concurrent session / earlier units. No `strategy/*.md` file has an mtime in UFIXPKG10's window, so its
  declared `strategy/…md` write path was **declared but not written**.
- I ran **no** command against `/home/zer0null/Duval`.

---

## 5. Reproduced / contradicted / not reproduced / unverified / overstated

**Reproduced (my own measurement):** shipped instrument 81,439 B / `89e77a8e…e169`; MANIFEST `:72–:76`
agreement; corrected citations at `CLAIMS.md:46,47`, `MANUSCRIPT.md:802`, `main.tex:408`; near-miss
`AVAILABILITY.md:22` = 145,031 B / `076164ac…` under `repro/`; md2tex twice byte-identical and
byte-identical to live, one-line diff at `408`; tarball 1 member / bytes equal / 28,569 B / `d5e49ad5…`;
independent census 12/12; three tools rc 0/0/0 with PASS and unmoved kappas and projection digest;
pytest rc=4 without `--noconftest` (conftest:19 `resextract`), rc=0 with `--noconftest`, direct run rc=0.

**Contradicted:** nothing material. One precision correction to the handoff's phrasing: the stale literal
`369159b0…` does survive in more places than "only … CLAIMS.md:46" — it is still present verbatim in
internal records `strategy/RELEASE_BUILD_3.md:315,321`, `strategy/RESIDUAL_TRIAGE_3.md:231,240`,
`orchestration/units/UFIXPAPER3.md:21` and four handoffs. None is a live paper publication (the handoff's
claim was scoped to the paper tree), but "ONLY inside the dated correction note in CLAIMS.md:46" is
over-broad if read workspace-wide.

**Not reproduced:** (a) the *mechanism* that the digest moved because five comments were removed from
`fixture/reflex-decisions.ts` — I verified the current bytes and MANIFEST but did not reconstruct the
prior file or the comment removal; (b) that the census-expectation edit was the **only** change to
`tests/test_package_tools.py` — no pre-edit copy of that test exists in the workspace, so I can only say
the file as shipped passes and pins the measured tree; (c) UFIXPKG10's `direct_tagre` rc=0 (empty
capture). The first two are sub-claims of the two corrections, not of the headline values, which I did
reproduce.

**Unverified:** the split of `tools/package/README.md` bytes between UFIXPKG10 and UFIXPKG11 (concurrent
writer); whether `scratch/ufixpkg10/main.before.tex` is identical to the true pre-edit file as of before
18:09 (it does carry the old digest at `:408`, which is strong but not conclusive provenance).

**Overstated:** minor — the "ONLY inside the dated correction note" scoping above, and a rc=0 evidence
line with zero captured output. No number was quoted from a document rather than measured that I could
catch; every headline figure I checked matched my own on-disk measurement.

**Honestly undetermined by UFIXPKG10:** it reported (in `other_stale_doc_finding`) that the README's
`regen_manifest` known-good block still carries `counts.bytes_total: 829422` / `manifest_self:
5acbb952a4deff08…` / MANIFEST sha `707dcf0b…`, while regenerating `scratch/uneutral10/package` yields
`bytes_total: 830893` (MANIFEST.json `:13`) and `manifest_self: 16ff23fe3ba7aba534adab0af6ce2067d36252394aef7e7e73416b91d5a0d21a` (`:270`).
I confirmed both halves in the snapshot (`README :136–137`) and on disk, and it correctly flagged that as
a possible third unit rather than silently claiming it fixed.

## 6. Main-session gate call
Both named corrections survive independent re-checking. **Gate: advance.** Open follow-ups (not blockers):
(1) the README `regen_manifest` known-good figures are internally inconsistent with the shipped MANIFEST
(`829422` vs `830893`) — UFIXPKG11 may already be on it; (2) `strategy/RELEASE_BUILD_3.md:321` retains a
now-false present-tense statement about `MANUSCRIPT.md`.
