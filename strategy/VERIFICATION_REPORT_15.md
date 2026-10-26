# VERIFICATION_REPORT_15 — independent verification of UFIX15

Verifier: UVER15. Author: UFIX15. Bound 30 tool calls. Nothing below is inherited
from UFIX15 unless explicitly marked.

## A. Gate re-derivation (INDEPENDENT)
- `sha256sum orchestration/units/UBUILD1.build.sh` = `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`, `wc -l` = 1019. Matches UFIX15 post-edit claim.
- Anchors confirmed by my own grep: `:771` `cat > "$DEST/gate.sh" <<'GATE_EOF'`; `:897` `chmod +x`; `:1005` `bash "$DEST/gate.sh"`. Heredoc body terminates `GATE_EOF` at `:896`.
- Word lists: `CODE_VOCAB_EOF` :695–743, `PUBLIC_VOCAB_EOF` :748–769; the vocabulary section begins ~:685. UFIX15's ":685-770" is a fair outer bound (not line-exact). `819-` not applicable.

## B. Citations repaired? (MIXED)
Five named places all now carry the named anchor `cat > "$DEST/gate.sh" <<'GATE_EOF'` + `:771–897`:
`PUBLISH_PACKAGE_MANIFEST.md:8`, `:252`, `UCURATE1.md:37`, `UTOK1.md:36`, `REPORT.md:168`. VERIFIED.
- BUT a workspace-wide grep does NOT come back empty. Live, un-repaired stale citations remain:
  - `strategy/REGEN_ASSESSMENT.md:23`: "The pattern lists are the gate's own heredoc, `orchestration/units/UBUILD1.build.sh:612-637`" — presented as current fact.
  - `repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md:296`: `PATTERNS_HARD` heredoc + "lines 612–637".
  - `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md:40` (`:640–647`), `:589` (comment); `experiments/token-substitution-test/gate-scan.sh:5,30,31,38` (its own `PATTERNS_HARD`/`PATTERNS_REVIEW`); `strategy/VERIFICATION_REPORT_11.md:19,268,269` (historical).
- Scope correction: of the four documents, only PUBLISH_PACKAGE_MANIFEST.md cited `612-637`/`640-647`. UCURATE1.md, UTOK1.md and REPORT.md cited `423-458` and STILL show it (annotated with the anchor). The "four documents used to cite 612-637" framing is not supported by UFIX15's own edits.

## C. Before/after record faithful? (YES — strongest check)
`scratch/ufix15/edits.json` holds 12 regions. For all 12, the "after" text occurs exactly once in the live file and the "before" text occurs zero times. Reverting both build-script after→before in a scratch copy reproduces the claimed PRE identity EXACTLY: sha256 `5c837c8deba0c33b568a7206872a1fbd7117b503a346903d36f4f47a78815a35`, 1019 lines. Line-count neutrality holds for every edited file (BS 1019; MANIFEST 519; UCURATE1 161; UTOK1 67; REPORT 283).

## D. Behaviour unchanged? (YES) — red→green
- Full build to `scratch/uver15/research-publish-packages`: reaches the gate, `flagged tokens: 95606`, `GATE RESULT: FAIL -- 95606 out-of-vocabulary token(s).`, `BUILD COMPLETE — the exclusion gate FAILED (exit 1).`
- Red→green on a minimal staged tree (gate.sh + vocabulary only): baseline `flagged tokens: 0 / GATE RESULT: PASS` exit 0; adding `probe.txt` with `zzqxwvplugh` → `probe.txt:1: zzqxwvplugh  [word not in the declared vocabulary]`, `FAIL -- 1` exit 1; removing it → `PASS` exit 0.

## E. The 95606 figure (REPRODUCED)
My own run of the current script measured **95606** — exact match to UFIX15. Not manufactured; 95,597 is superseded.

## F. Self-disclosed remainder — "framed as superseded" (PARTLY true)
`:258-259` ("Superseded denylist gate — per HARD pattern … ULICENCE3 deleted this denylist"), `:292` ("Under the superseded denylist …"), `:392` ("Under the now-superseded denylist …") DO frame supersession.
But `:131` (inside §4, lines 128–132) states the 152-line measurement with NO superseded marker at or near it, and calls it "the measurement". Its supersession marker is 125 lines later at :255/:258. A reader at :131 can take 152 as current → OVERSTATED.

## G. §12.5 vs VERIFICATION_REPORT_12.md (FAITHFUL)
UVER12 Q2 says `redact.py:855-895` re-derives `flag = (sh == h)` and repairs stale rows; regenerated MANIFEST 25 flag-True / 0 contradictions; shipped 8 contradictions = UREGEN1's 6 + 2 pre-existing source-level (`fixture/DECISION_CASE_SCHEMA.ts`, `preregistration/EXP12-typed-channel-comparison-prereg.md`). §12.5 states exactly this. Independent re-derivation of the shipped MANIFEST finds 8 rows with `sha256 != source_sha256` (6 with `identical_to_source: true` — EXCLUDED.md, INTEGRITY.md, LICENCE_TODO.md, README.md, harness/LEAD-WIRING.md, harness/collect.py — plus those same 2 with the flag absent), the pristine source 2, the regenerated tree 0 with 25 True. UREGEN1's six names confirmed present in `orchestration/handoffs/UREGEN1.json`. Note: UVER12's "flag-True" counts treat an absent flag as True (42/39); under strict `is True` it is 40/37. The substance is unchanged.

## Verdict
`partial`. UFIX15's own repairs are faithful, line-neutral and behaviour-neutral, and its 95606 and pre-edit identity reproduce exactly. The overstatements are about scope/framing, not about the gate.
