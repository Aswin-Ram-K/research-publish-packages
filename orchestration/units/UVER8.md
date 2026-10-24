# UVER8 — independent re-verification of UREDACT1 (`repro/encoder-crossover-190-SANITISED/`)

**Bound:** 50 tool calls · **used: 22** · **status: done** · **date:** 2026-10-15
**Verdict:** `pass-with-corrections`

## What this unit is for

UREDACT1 overran its own bound (53/50) and explicitly asked for an independent re-run. This unit is a
**different** agent: it re-ran the author's acceptance test on a **fresh copy**, recomputed every
`CLAIMS.md` value with its own code, forced the check **red→green**, re-measured the leak, re-verified the
fresh-export rule, and settled from the public internet the claim UREDACT1 could only attribute.

## Write paths (declared, and the only ones touched)

`strategy/VERIFICATION_REPORT_8.md`, `orchestration/units/UVER8.md`, `orchestration/handoffs/UVER8.json`.
Scratch copy `.uver8-scratch/` created inside the workspace and removed on completion. `repro/**` untouched.

## Method and result

1. **Fresh copy** (`.uver8-scratch/`, 98 files) → `bash verify/run-verification.sh` exit 0 (9.7 s) and
   `python3 verify/recompute-claims.py` exit 0. Output identical to the shipped logs except paths, the
   timestamp, and the `head -40` ordering in step 8 (readdir order, not content).
2. **Independent recompute** (my own script, no import of theirs): all nine recomputable values match,
   `39+27+90+34=190`, `p=4.166817880507353e-09`, MDE `0.15949356562876219`, projection digest
   `57a29b4e…` identical before/after, `train.jsonl`/`dev.jsonl` byte-identical. **0 numbers moved.**
3. **Red→green:** flipped one `perCase.correct` and `+0.01` on `routeA.kappa` in the **copy** → two
   `MISMATCH`, `ALL CLAIM NUMBERS PRESERVED: False`, **exit 1**; restored → exit 0, restored hashes equal
   the real tree. The check is falsifiable.
4. **Leak:** as-audited 210 reproduced exactly. Sanitised = **154 only under the instrument-only scope**;
   over the exclusion the report *states* (`verify/`, `variants/`) it is **212** (+2); whole tree 327.
   `README.md` has 8 strict hits (the report records it as clean / "once"). `src/*.ts` residue = 10 in the
   fixture, 22 in instrument files, all inside question text. `Dag`/`CommitRecord` = 0.
5. **Fresh export:** `analyze/tccommon/train.py` hash-object == blobs at `a5ef1b28:tools/typed-channel/…`
   (all three MATCH); `a5ef1b28` NOT an ancestor of HEAD; **0** `.git`/packfile/`.idx`/bundle. But
   `MANIFEST.json` ships the closed-branch SHA 20× as `git:a5ef1b28…:tools/typed-channel/…`.
6. **As-audited subset:** own MANIFEST re-verified **42/42 OK, 0 mismatch, 0 missing**.
7. **Priority 3:** I fetched
   `https://raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/main/findings/PAPER-DERIVATION.md`
   (HTTP 200, 46636 bytes) and computed **`d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`**
   — byte-identical to `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`. UVER6's claim is
   **independently confirmed**; GitHub blob sha `7842e48c591343dff09cd8cbcf5931382e534493`, size 46636.
8. **Containment:** Duval HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` before = after; same four
   pre-existing untracked paths; no `git` state change; no write to Duval or `repro/**`.

## Corrections demanded (details in the report)

- **C1 (contradicted):** sanitised `README.md` row "–" / "names `DecisionKind` once" → **8** strict hits.
- **C2 (contradicted):** §7(d) "no residual occurrence … outside (a) and (b)" → true for the instrument,
  false for the shipped tree (`REDACTION_REPORT.md` 32, `redact.py` 18, `README.md` 8).
- **O1–O6 (overstated):** `210→154` scope; "no history is present"; "9 `src/` mentions"; "ten values"
  (nine); `LEAD-WIRING.md` 142→43 (141→42); `DecisionKind` 4 lines (5).

## What would change the verdict

`fail` on any value failing to reproduce, a digest/split change, a harness blob mismatch, or a `.git`
object. Plain `pass` after the six count/scope corrections — no re-run needed for those.
