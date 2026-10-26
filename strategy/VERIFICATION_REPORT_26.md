# VERIFICATION_REPORT_26 — independent verification of UTOOL1's one-line tooling repair

**Verifier:** UVER26 (not the author). **Bound:** 25 tool calls; **used 23**. Workspace
`/home/zer0null/reserach extarctor`. Every number below was re-derived from the bytes on disk with my own
scripts under `scratch/uver26/**` (`snapshot.py`, `check_manifest.py`, `qdiff.py`, `leak_scan.py`) — the
author's `check_manifest6.py` was never run.

**Verdict: `pass`.** The edit changes *where* `parse_fixture.py` reads, not *what* it measures. All eight
UTOOL1 claims reproduce; one is cosmetically overstated (below). Nothing contradicted; nothing
not-reproduced.

## 1. The edit, confirmed against the pre-edit tree (`scratch/udtag1/tree-five`)

`diff -rq scratch/udtag1/tree-five scratch/utool1/tree-six` reports exactly two differing files:

- `second-labeller/parse_fixture.py:16` — one line, exactly as claimed:
  `-SRC = os.path.join(HERE, "reflex-decisions.sandbox.ts")`
  `+SRC = os.path.join(HERE, os.pardir, "fixture", "reflex-decisions.ts")  # UTOOL1: shipped fixture; was "reflex-decisions.sandbox.ts" (not in the ship set)`
- `MANIFEST.json` — necessarily regenerated, since it hashes the tool. Nothing else differs.

Post-edit tool sha256 `a6d83a5b989372504d8702cdc32a83d5a9fff119382acf10723d8efca13cb2fa`.
**Overstated (cosmetic):** UTOOL1.md's "only `second-labeller/parse_fixture.py` differs" is not literally
true at byte level — `MANIFEST.json` differs too; the same card discloses the regeneration elsewhere.
Non-material.

## 2. The three files (the justification for not widening the ship set)

| file | sha256 | bytes |
|---|---|---|
| withheld original `repro/encoder-crossover-190/fixture/reflex-decisions.ts` | `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` | 145,031 |
| SANITISED package copy `repro/encoder-crossover-190-SANITISED/fixture/reflex-decisions.ts` | `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae` | 90,738 |
| emitted-tree shipped fixture `scratch/utool1/tree-six/fixture/reflex-decisions.ts` | `ba810aa15c736a38512a98e5ed938edb6e51c640b15ca7ecc562a59aaf182fc5` | 85,044 |

- **Byte-identity (claim 3) holds for the emitted tree:** `scratch/ubij3/tree-three-run/fixture/reflex-decisions.ts`,
  `scratch/uver20/tree-run/fixture/reflex-decisions.ts` and `scratch/utool1/tree-six/fixture/reflex-decisions.ts`
  are all `ba810aa1…` / 85,044 B. The *staged* `second-labeller/reflex-decisions.sandbox.ts` in both earlier
  run trees is **also** `ba810aa1…` / 85,044 B — the file the earlier units actually opened is the shipped
  fixture under the old name, not the withheld original. The pristine emitted copy of that name exists nowhere
  in the ship set (35 staged copies exist across `scratch/**`; the leaky 145,031 B original survives only at
  `scratch/uver11/srcbase/experiments/second-labeller-190/reflex-decisions.sandbox.ts`).
- **The withheld original really is the leaky one.** All ten mechanism tokens are present in it and absent
  from the shipped fixture: `src/scope.ts`×3, `src/policy.ts`×3, `src/loop.ts`×2, `src/broker.ts`×1,
  `src/layer.ts`×1, `src/state.ts:256`×2, `materialiseGrants`×3, `grantKey`×2, `npm run scope`×2, `EXP#9a`×2;
  shipped fixture: 0 for every one.
- **47 of 190 question strings differ.** Re-parsed both fixtures with the tool's own `split_records`/`field`
  (imported from the post-edit file): 190 vs 190 records, 190 distinct each, 47 position-wise differences,
  47 only-in-original, 47 only-in-shipped.
- **E15 does withhold it deliberately** and its wording is false: `EXCLUDED.md:40` calls
  `reflex-decisions.sandbox.ts` "a **byte-identical duplicate** of the fixture (145,031 B)" — the shipped
  fixture is 85,044 B, so it is a duplicate of the *withheld* fixture only. UTOOL1 flagged this as the trap;
  the inaccuracy is pre-existing in the shipped `EXCLUDED.md`, not introduced by the repair.

**Correction to the instruction's framing:** "byte-identical to the shipped `fixture/reflex-decisions.ts`"
is true of the *emitted tree* (85,044 B) but not of the SANITISED package copy (90,738 B), which is a
different generation. UTOOL1's own card distinguishes the two correctly ("SANITISED fixture = 90,738 B sha
`751dc007…`; shipped fixture = 85,044 B sha `ba810aa1…`").

## 3. Both tools re-run in my own copy — values printed, not asserted

`cp -a scratch/utool1/tree-six scratch/uver26/tree-run`, then run inside it.

- `python3 second-labeller/parse_fixture.py` → **exit 0**, stderr empty. `records_found` 190,
  `cases_parsed` 190, `options_total` 721, `distinct_labels` 74, `parse_failures` 0, `bad_option_arity` 0,
  `answer_outside_option_set` 0, `near_duplicate_questions` 0.
- `python3 second-labeller/compare.py` → **exit 0**, stderr empty. routeA `kappa` 0.32520740993294694,
  `exact_index_matches` 65, `ties` 120, `zero_score_cases` 41; routeB `kappa` 0.9013584840356494,
  `exact_index_matches` 172, `n_disagreements` 18, `AB_mutual_agreement` 0.3526315789473684;
  closed_subset (`n`=106) `kappa` 0.8837023738280471; roster_and_bespoke_subset (`n`=84) `kappa`
  0.9139973672663448. Full stdout kept at `scratch/uver26/compare.out`.

## 4. Red → green (mandatory)

`scratch/uver26/tree-red` = copy of tree-six with line 16 reverted to `reflex-decisions.sandbox.ts`.

- **RED:** exit **1**, stderr `FileNotFoundError: [Errno 2] No such file or directory:
  '…/scratch/uver26/tree-red/second-labeller/reflex-decisions.sandbox.ts'`, raised from
  `parse_fixture.py:85` with the path bound at `:16`.
- **GREEN:** the unmodified post-edit line restored, same tree → exit **0**.

## 5. `metrics.json` before/after and run-output identity

- Emitted-file invariance: `scratch/udtag1/tree-five/second-labeller/metrics.json` =
  `scratch/utool1/tree-six/second-labeller/metrics.json` =
  `6bf39077261f00bed589a4ae8e9fe90324e2435fd28e42a4fc8de7684cba34bf` (byte-identical across the edit).
- Run output `5d05dd13c51b55465cee0f4ff4d3e016a45fad9ee1a2e9ff25b5e99fd0ddc726` is identical in my
  `scratch/uver26/tree-run`, `scratch/ubij3/tree-three-run` and `scratch/uver20/tree-run`. (Distinct from
  the shipped `metrics.json` `6bf39077…`, which carries UFIX4's added `limitation`/`_correction` keys.)

## 6. Invariants

- `python3 scratch/utool1/tree-six/verify/recompute-claims.py` → exit 0, line 26
  `ALL CLAIM NUMBERS PRESERVED: True`.
- `PYTHONHASHSEED=0 python3 scratch/ubij1/census_one.py` → exit 0 on both trees. tree-five: total 3354,
  inside **2171** / distinct **30**, outside 1105, 74/184 identifiers. tree-six: total 3356, inside **2171** /
  distinct **30**, outside 1107 (+2 = the provenance comment), 74/184.

## 7. Manifest — my own checker (`scratch/uver26/check_manifest.py`)

`MANIFEST.json` sha256 `0633a0a5cf1a1414400b3f6c9969109c53d9ba336c51083b1712289662ee172d`, 22,325 bytes,
443 lines. `files[]` 44 entries; files on disk excluding MANIFEST.json 44; listed == on-disk exactly (no
extras, none missing); **0 hash mismatches, 0 size mismatches**. `counts.files` 45 = 44 listed + the manifest
itself; `counts.bytes_total` 3,008,928 = 2,986,603 listed + 22,325 manifest bytes.
**Self-reference convention is stated, not implied:** top-level `manifest_self` says
"not listed (self-referential sha256 is impossible); MANIFEST.json is the only file in the tree absent from
`files[]`".

## 8. Idempotence

`diff -rq scratch/utool1/tree-six scratch/utool1/tree-six-b` → exit **0**, **0 lines**;
both `MANIFEST.json` = `0633a0a5…`. Two builds byte-identical.

## 9. Containment

- **Self-inflicted artifact, disclosed and remediated:** running `verify/recompute-claims.py` against
  `scratch/utool1/tree-six` wrote `second-labeller/__pycache__/parse_fixture.cpython-314.pyc`. I detected it
  by snapshot diff, deleted it, and re-verified: `scratch/uver26/tree-six.before.sha` ==
  `tree-six.final.sha`, 45 lines, diff exit 0. `scratch/utool1/tree-six` is now byte-for-byte as I found it.
  All reverting/re-running happened only in `scratch/uver26/tree-*` copies.
- No git command was run anywhere. `/home/zer0null/research-publish-packages` mtime
  2026-10-15 18:07:13, `/home/zer0null/Duval` mtime 2026-10-15 21:58:13 — both predate this session; neither
  was written. All my writes are `scratch/uver26/**` plus this report and the UVER26 card/handoff.

## 10. `source` / `source_sha256` exposure — decision, not defect

44 manifest entries; **40 carry a `source_sha256`** digest of a file that does not ship. Of those 40,
**11** name the read-only target repository and **18** name an unmerged/withheld branch (`git:an unmerged
development branch commit (id withheld):…`); **29** name one or the other — a majority (72.5%). No fix
proposed: this is the author's declared `policy` ("open paper, withheld implementation") and the convention
is explicit in the manifest's own `policy`/`manifest_self` fields.

## 11. Unverified / not re-derived

- Tree-five's `3,008,830` byte total: I verified only the two-tree `diff -rq` file-level difference, not the
  byte total.
- The withheld original's upstream provenance (that `repro/encoder-crossover-190/…` is the unsanitised
  source rather than a later reconstruction) follows from E15 and the uver11 staging copy; I did not
  re-derive it from the target.
- The `source_sha256` digests themselves: I confirmed their count and the non-shipping nature of the named
  sources, not each digest against a target file (the target is read-only and out of scope here).
- One transient: a first census invocation inside a `&&` chain printed `exit 1` because an earlier `cat`
  of an ephemeral `/tmp` file failed and short-circuited the chain — not a census failure; the clean re-run
  exited 0. `/tmp` is not shared between tool calls.
