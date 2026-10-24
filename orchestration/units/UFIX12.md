# UFIX12 — four corrections established by UVER11 and UREDACT3

**Status:** done (4/4 applied, verified). **Bound:** 20 tool calls; used 17 (15 before this card + 2 writes).
**Write paths (only these):** `strategy/PUBLISH_PACKAGE_MANIFEST.md`,
`papers/gated-read-batching/REFS.md`, `orchestration/units/UFIX12.md`,
`orchestration/handoffs/UFIX12.json`.

**Constraints honoured:** `/home/zer0null/Duval` and all registered targets untouched;
`repro/encoder-crossover-190-SANITISED/redact.py` **not edited, not run**; no build script run; no file under
`repro/**` modified. Note: `git status --porcelain` reports **both** `papers/` and `strategy/` as untracked
(`?? papers/`, `?? strategy/`) — so *every* edit below is git-unrecoverable, not just the `papers/` one;
verbatim before/after for all five edits is carried in `orchestration/handoffs/UFIX12.json`.

## Verified citation targets (opened before editing)

`orchestration/units/UBUILD1.build.sh`:
- HARD heredoc `cat >"$HARD_FILE" <<'PATTERNS_HARD'` at **:612**, body 613–636 (24 patterns), terminator **:637**.
- REVIEW heredoc `cat >"$REVIEW_FILE" <<'PATTERNS_REVIEW'` at **:640**, body 641–646 (6 patterns), terminator **:647**.

> **Superseded 2026-10-16 (UFIX22, dated record left unrewritten):** the `PATTERNS_HARD` / `PATTERNS_REVIEW` heredocs cited here were removed by unit ULICENCE3 and no longer exist. `orchestration/units/UBUILD1.build.sh` is now **1,019 lines**, sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`; its gate is the positive vocabulary checker whose heredoc opens `cat > "$DEST/gate.sh" <<'GATE_EOF'` (currently `:771`, closing `:896`, `chmod +x` `:897`), fed by `vocabulary/{english,code,public}.txt` (currently `:691`, `:695-743`, `:748-769`) and invoked at `bash "$DEST/gate.sh"` (currently `:1005`). Verify the anchors before relying on the numbers.

`papers/gated-read-batching/CLAIMS.md:10-15` declares the full legend table G/R/S/P:
**G** = `docs/research/GATED_READ_2026.md` (run report, 340 lines); P = `GATED_READ_PROVENANCE.md`.
`REFS.md:11-13` declared only **P**, while `REFS.md:66` cites `G:49-51`.

> **Superseded 2026-10-16 (UFIX22, dated record left unrewritten):** the `REFS.md` reading above is wrong. `papers/gated-read-batching/REFS.md:66` uses **`P:246`**, not a `G:` locator; the only `G:` locator is `REFS.md:68` (`G:49-51`); and the `G:` legend already exists at `REFS.md:15` (`P:` at `:11`), so the recommendation to add a legend line is moot.

## The four corrections

1. **Contradicted number, manifest §8 baseline (lines 284–288).** `218` untransformed → **`156`**, paired with
   `152` after the three path rules, plus the build's own neutralise log line `4 occurrence(s) in 2 file(s)`.
   The "incomparable numbers" framing removed/softened: 156 and 158 differ by 2. Headline **152 unchanged**.
2. **Wrong citation, manifest (2 occurrences).** `UBUILD1.build.sh:423–458` → `:612–637` (HARD), REVIEW
   `:640–647` (lines 423–458 of that script are README prose).
3. **REFS.md `G:` legend gap.** One legend line added after `REFS.md:13`, matching the existing P-declaration
   wording, sourced from `CLAIMS.md:12`. File not restructured (96 → 98 lines).
4. **Recorded, not fixed.** New §12.5 in the manifest records UREDACT3's stage-D defect
   (`redact.py:873–883`, helper `:625`): source digest written into `sha256` while `identical_to_source: true`
   stays set; 6 stale identity rows (card said 5), 4 fixed by stage D, 2 open (`README.md`, `INTEGRITY.md`).

## Out-of-scope wrong citations found (NOT edited — outside write paths)

- `orchestration/units/UCURATE1.md:37` — `UBUILD1.build.sh:423–458`
- `orchestration/units/UTOK1.md:36` — `orchestration/units/UBUILD1.build.sh:423-458`
- `experiments/token-substitution-test/REPORT.md:168` — `orchestration/units/UBUILD1.build.sh:423-458`

(`repro/**` and `scratch/**` copies of REDACT3_REPORT.md:296 already carry the corrected range.)
