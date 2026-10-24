# UTOOL1 — reconcile and repair the two unrunnable `second-labeller` tools

**Unit:** UTOOL1. **Status:** `done`. **Bound:** 30 tool calls; **used 25**. Workspace
`/home/zer0null/reserach extarctor`.

**Write paths (the only paths written):** `scratch/utool1/**`, `strategy/TOOLING_REPAIR.md`,
`orchestration/units/UTOOL1.md`, `orchestration/handoffs/UTOOL1.json`. Nothing in the forbidden set was
written (`scratch/ubij1|ubij2|ubij3|upack1|uver20|21|22|ufix25|26|uwire1|2|unoncensus1|2|udtag1|ugate1|uambig1|uneutral1..4`,
`repro/**`, `orchestration/units/UBUILD1.build.sh`, `tests/test_build_wiring.py`, `strategy/BUILD_WIRING.md`,
`/home/zer0null/research-publish-packages`); no git command was run; the ship set was never widened.

## Purpose
Two shipped tools cannot run: `second-labeller/parse_fixture.py` reads `reflex-decisions.sandbox.ts`
(absent from the ship set) and `second-labeller/compare.py` then cannot find `cases.json`. Diagnose,
reconcile UDTAG1's exit-1 against UBIJ3's/UVER20's exit-0, decide packaging-vs-tooling, fix in a new tree,
prove the measurement is unmoved, re-establish the invariants, regenerate the manifest and prove idempotence.

## What was found
- Literal failures reproduced in `scratch/utool1/diag`: `parse_fixture.py:85` `FileNotFoundError ...
  reflex-decisions.sandbox.ts` (path bound at `parse_fixture.py:16`), exit 1; `compare.py:49`
  `FileNotFoundError ... cases.json`, exit 1.
- **Reconciliation:** both earlier measurements are locally right but ran in different trees. UBIJ3 used
  `scratch/ubij3/tree-three-run` and UVER20 used `scratch/uver20/tree-run` — twins that carried a staged
  `reflex-decisions.sandbox.ts` of sha256 `ba810aa15c736a38…` (85,044 B, the neutralised fixture).
  UDTAG1 ran the pristine `scratch/udtag1/tree-five`, hence exit 1. The clean second build
  `scratch/ubij3/tree-three-b` has no such file, proving the builder never emitted it.
- **Root cause: the tool, not the packaging.** `repro/encoder-crossover-190-SANITISED/EXCLUDED.md` §3 E15
  deliberately excludes the sandbox file; the instrument that ships is `fixture/reflex-decisions.ts`.
- **The trap, measured:** E15's "byte-identical duplicate (145,031 B)" is false. Original = 145,031 B sha
  `076164ac…`; SANITISED fixture = 90,738 B sha `751dc007…`; shipped fixture = 85,044 B sha `ba810aa1…`.
  47 of 190 question strings differ between original and shipped. The original carries `src/scope.ts`,
  `src/policy.ts`, `src/loop.ts`, `src/broker.ts`, `src/layer.ts`, `src/state.ts:256`,
  `materialiseGrants`, `grantKey`, `npm run scope`, `EXP#9a` — withheld `src/**` mechanism vocabulary.
  It was **not** added to the ship set.

## The fix (one line, `second-labeller/parse_fixture.py:16`)
```diff
-SRC = os.path.join(HERE, "reflex-decisions.sandbox.ts")
+SRC = os.path.join(HERE, os.pardir, "fixture", "reflex-decisions.ts")  # UTOOL1: shipped fixture; was "reflex-decisions.sandbox.ts" (not in the ship set)
```
Not a rescue-rename: the earlier units' staged input was byte-identical to the shipped fixture, so the input
content is unchanged. Corrected file sha256
`a6d83a5b989372504d8702cdc32a83d5a9fff119382acf10723d8efca13cb2fa`.

## Results
- `scratch/utool1/tree-six` (the deliverable = `tree-five` + this one line; `tree-six-b` second build):
  45 files, 3,008,830 → 3,008,928 bytes; only `second-labeller/parse_fixture.py` differs.
- Tools in `scratch/utool1/tree-six-run` (sha-verified copy; the tools mutate the tree they run in):
  `parse_fixture.py` **exit 0** — 190 records / 190 cases / 721 options / 74 distinct labels / 0 parse
  failures / 0 bad arity / 0 out-of-set / 0 near-duplicates. `compare.py` **exit 0** — routeA kappa
  `0.32520740993294694` (exact 65, ties 120, zero 41); routeB kappa `0.9013584840356494` (exact 172,
  18 disagreements, AB `0.3526315789473684`); closed `0.8837023738280471` (n=106); roster
  `0.9139973672663448` (n=84).
- Run `metrics.json` sha256 `5d05dd13c51b5546…` is **byte-identical** to UBIJ3's `tree-three-run` and
  UVER20's `tree-run` — the same measurement, produced from the shipped fixture.
- **`second-labeller/metrics.json` in the emitted tree is byte-identical before and after**:
  `6bf39077261f00bed589a4ae8e9fe90324e2435fd28e42a4fc8de7684cba34bf`. (The run output differs from the
  shipped file only by UFIX4's hand-added `limitation`/`_correction` keys — VERIFICATION_REPORT_20.md §D4.)
- Invariants: `verify/recompute-claims.py` exit 0, `ALL CLAIM NUMBERS PRESERVED: True`; census inside
  stimulus 2,171 / 30 distinct keys unchanged (total 3,354→3,356, outside +2 from the provenance comment;
  74/184 identifiers hit both trees); `compileall` 0; JSONL 800/200/18 lines, 0 bad.
- Manifest regenerated from disk with the workspace procedure (`scratch/utool1/regen_manifest.py`, copied
  from `scratch/udtag1/regen_manifest.py` with only the tree root changed): **443 lines, 22,325 bytes,
  sha256 `0633a0a5cf1a1414400b3f6c9969109c53d9ba336c51083b1712289662ee172d`**; 44 `files[]` entries, only the
  `parse_fixture.py` entry changed. Independent checker `scratch/utool1/check_manifest6.py` → PASS (0 hash /
  0 size mismatches, 45 files on disk, bytes_total 3,008,928). Idempotence: `diff -r tree-six tree-six-b`
  exit 0, byte-identical including MANIFEST.json.
- Downstream reported, not edited: `orchestration/units/UBUILD1.build.sh:39,135`,
  `strategy/BUILD_WIRING.md:4,28,42,55,95,97,109,132,158,175`, `tests/test_build_wiring.py:12,51,106,164`
  all name `scratch/ubij3/tree-three-r2`. Promotion also imports UPACK1's manifest regen and UDTAG1's five
  D-number neutralisations. Manifest `source`/`source_sha256` exposure (44/44 entries) reported as an open
  author decision. Full analysis: `strategy/TOOLING_REPAIR.md`.

## Blocker
None technical. The promotion edit is outside this unit's write scope (build wiring / tests / BUILD_WIRING.md
are owned by another unit).

## Next unit hint
The build-wiring owner should repoint the three pins to `scratch/utool1/tree-six` and re-verify the wiring
test suite, `BUILD_WIRING.md`'s file count (45), delta A/B lists, inside-stimulus claim (2,171, delta 0) and
manifest identity note. A verifier (not this author) should re-run `scratch/utool1/build_six.py` into a fresh
tree, re-run both tools, re-derive the census and manifest with its own checker, and include a red→green
check: revert the one line and confirm `parse_fixture.py` exits 1 again.
