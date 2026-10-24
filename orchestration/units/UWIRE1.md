# UWIRE1 — wire the chosen release tree into UBUILD1's build (override, not replacement)

**Status:** `done` — override wired, both paths run, guards red→green, ship list reconciled with **no edit needed**.
**Bound:** 35 tool calls; used ~24. **Write paths:** `orchestration/units/UBUILD1.build.sh`,
`strategy/BUILD_WIRING.md`, `scratch/uwire1/**`, `orchestration/units/UWIRE1.md`,
`orchestration/handoffs/UWIRE1.json`.

## Defect
`UBUILD1.build.sh` pinned `SAN_SRC="$SRC/repro/encoder-crossover-190-SANITISED"` — the **original**,
least-processed sanitised tree. `scratch/ubij3/tree-three-r2` (verified by UVER20, metadata-repaired by
UPACK1) was never wired in, so the release pipeline shipped every re-tagging result as absent.

## What was done
1. **Mapped** every `$SAN_SRC` consumer: assignment, the `fixture/→code/` + `preregistration/→eval/` staged
   copy, `SHIP_STAGED` (52 names), `NEVER_SHIP` (17 names), licence plumbing, and the positive-vocabulary gate.
2. **Reconciled file sets both ways.** Sanitised 59 (card says 58 — see card 3), `tree-three-r2` 45.
   Delta A = 14 sanitised-only files, **all process documents**; of the seven `verify/*` ones only
   `verify/recompute-claims.py` is in `SHIP_STAGED` and it **exists** in the new tree. **Delta B = 0 files**
   — the re-tagging renamed nothing inside the staged buckets. Operationally: `SHIP_STAGED` has 40
   `code/`+`eval/` entries, 2 of which come from `LAB_SRC`, leaving **38 from `SAN_SRC`** — and both trees
   stage-and-keep the **same 38 paths**. Zero missing → no `FATAL`; zero unlisted → no fail-closed surprise.
   **The ship list reconciles cleanly; no edit was needed and no judgement call was deferred.**
3. **Wired an override, not a replacement:**
   `SAN_SRC="${SAN_SRC_OVERRIDE:-$SRC/repro/encoder-crossover-190-SANITISED}"`, plus a documented header
   block. Default is byte-identical to before; the swap is one environment variable and fully reversible.
4. **Ran both paths** into scratch destinations and measured everything (§ Evidence in the handoff).
5. **Censused both emitted trees** with the workspace convention (`scratch/ubij1/census_one.py` + the
   184-identifier `scratch/uagnostic1/census.tsv`), inside-stimulus reported separately.
6. **Red→green on all three fail-closed guards.**
7. **`strategy/BUILD_WIRING.md`** written.

## Result
| | default | override |
|---|---|---|
| staged → kept/dropped | 66 → 52/14 | 60 → **52/8** |
| ship-list / never-ship | 52 present / 17 absent | 52 present / 17 absent |
| emitted tree | 64 files, 7.6M | **64 files, 5.3M** |
| gate verdict | `FAIL -- 95606 out-of-vocabulary token(s).` | `FAIL -- 29936 out-of-vocabulary token(s).` |
| exit | 1 (gate) | 1 (gate) |

Census over the emitted packages: **44,056 → 3,317** total occurrences (−40,739, 12.4×);
inside-stimulus **2,722 → 2,171** (−551, and equal to `tree-three-r2`'s own baseline, delta 0 — the property
UVER20 verified); keys 23,292 → 83; distinct identifiers 163 → 84 of 184.
Both runs fail **only at the gate**, never at the ship list.

Red→green: inject an unlisted `code/harness/INJECTED_UNLISTED.txt` → dropped, absent from the emitted tree
(8→9 drops); remove it → proceeds (60 staged, 52 kept, 8 dropped). Remove a **listed** file
(`code/harness/lint.ts`) → `FATAL: ship-list names a file the package does not have: …`, exit 1, **before**
the gate; restore → proceeds and reaches the gate. Wrong `DEST` → exit 2
(`FATAL: refusing to rm -rf … — DEST must end in /research-publish-packages`) with a sentinel file intact,
proving no `rm -rf` ran.

## Remains to be decided (not blocking this unit)
1. **Promote or keep the override?** The chosen artifact is still not the default; nothing warns you if the
   wrong bytes ship. Promoting `tree-three-r2` into `repro/` (or flipping the default) is a separate call.
2. **The gate fails on both paths** (95,606 / 29,936) — by design, but it must be settled separately.
3. **The sanitised tree is not frozen:** `repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md`
   (mtime 2026-10-15 21:04:58) was added by a concurrent unit during this batch, 58 → 59. Top-level, so
   never staged — no effect on the build, but the card's 58 is stale.
4. **No regression test** guards the wiring.

## Constraints honoured
Wrote only the five declared paths. Never wrote inside `scratch/ubij1|ubij2|ubij3/**`, `scratch/upack1/**`,
`scratch/unoncensus*`, `scratch/uver2*`, `scratch/ufix25/**`, `repro/**`, or
`/home/zer0null/research-publish-packages` (the sandbox refused the real destination with
`Read-only file system`, which the build treated as a hard stop). No git command was run.
`orchestration/units/UBUILD1.build.sh` is **untracked by git** — the verbatim before/after of both hunks is
carried in `orchestration/handoffs/UWIRE1.json` under `evidence.edit_diff` and the pre-edit copy is
preserved at `scratch/uwire1/UBUILD1.build.sh.orig`.
