# UGATE2 — wire the corrected (scoped) exclusion gate into the build

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a · **Date:** 2026-10-16
**Status:** DONE — wired, measured, red→green and fail-closed shown

**One purpose.** Port UGATE1's corrected positive-vocabulary checker
(`scratch/ugate1/gate_scoped.sh`) into the gate heredoc of
`orchestration/units/UBUILD1.build.sh`, without weakening the gate's real job:
prose and source keep the strict rule; data files may use the released format's
*declared* vocabulary; the offender listing is uncapped; the checker does not
scan its own `vocabulary/` directory; the gate stays fail-closed.

**Hard bound:** 25 tool calls. Work in small increments; never `cat` a large file.

**Write paths (nothing else):**
`orchestration/units/UBUILD1.build.sh`, `strategy/GATE_VOCABULARY_ANALYSIS.md`
(append a dated section only), `orchestration/units/UGATE2.md`,
`orchestration/handoffs/UGATE2.json`, `scratch/ugate2/**`.

**Read-only:** `/home/zer0null/Duval`, `/home/zer0null/research-publish-packages`.
No bare `git status` against a target. Do not use `make_data_vocab.py --mode full`.

## Plan
1. Read `scratch/ugate1/gate_scoped.sh` + `strategy/GATE_VOCABULARY_ANALYSIS.md`. ✓
2. Port the checker into the `cat > "$DEST/gate.sh" <<'GATE_EOF'` heredoc,
   preserving heredoc shape, `chmod +x`, invocation, `GATE_RC=$?`, `exit "$GATE_RC"`.
3. Add fail-closed derivation of `vocabulary/data.txt` (**keys mode only**) from
   the staged tree, with an empty-input FATAL.
4. Fix the uncapped offender listing; fix the `vocabulary/` self-scan.
5. Build into `scratch/ugate2/dest/research-publish-packages`; report
   staged/kept/dropped, file count, new gate count, residual by class.
6. RED→GREEN with a real mechanism identifier; fail-closed test for a
   missing/empty vocabulary file.
7. Finish the handoff; re-parse it as JSON.

## Report (appended as work proceeds)

- Tool call 1–6: read `scratch/ugate1/gate_scoped.sh` (152 lines), the 256-line
  analysis, `UBUILD1.build.sh` header/heredoc/tail, `scratch/ugate1/make_data_vocab.py`.
- **Latent defect found in UGATE1's checker before porting:** `gate_scoped.sh:121`
  reads `if rel.split(os.sep)[0] == VOCAB_DIR or os.path.dirname(rel) == VOCAB_DIR`
  — `VOCAB_DIR` is an **absolute** path (`os.path.join(ROOT, "vocabulary")`) while
  `rel` is relative, so the self-scan guard **never fires**. UGATE1's claimed
  "no longer scans its own vocabulary/" fix was not in effect in the artifact it
  shipped. UGATE2 fixes it to compare against the *relative* vocabulary dir name.

### Final measurements (all reproducible from scratch/ugate2/**)

| item | value |
|---|---|
| staged / kept / dropped | 29 / 29 / 0 |
| emitted files (excl. `.git`) | 39 |
| **old shipped gate**, identical tree | **1,740** (listing capped at 400) |
| **new scoped gate** | **1,398** (listing complete: 1,398 lines) |
| `gate.sh` self-offenders | 0 |
| `vocabulary/data.txt` | 501 keys / 32 parsed documents, **keys mode** |
| red injection | 1,399, names `packages/exp12-encoder-crossover/README.md:32: tccommon` |
| green (injection removed) | 1,398; `redtest` identical to the built tree |
| missing `data.txt` | `exit 2` — `FATAL: cannot read vocabulary file: …` |
| empty `data.txt` | `exit 2` — `FATAL: vocabulary file has no declared terms: …` |
| empty derivation input | `exit 1` — `FATAL: derived an EMPTY data vocabulary`; no file written |

**Status:** DONE — the corrected checker is wired in and measured; the gate still
FAILS on 1,398 genuine residual tokens, which §3 (below) reports as a result, not a
regression. No vocabulary was widened to make the number pass.
