# UFIX20 — two/three-site dated-pointer repair in VERIFICATION_REPORT_11.md

**Unit:** UFIX20 (bounded repair unit). **Hard bound:** 8 tool calls, two-site edit.
**Date of pointer text:** 2026-10-16.

## Why
`strategy/VERIFICATION_REPORT_11.md` cites the dead `PATTERNS_HARD` (612–637, patterns 613–636) and
`PATTERNS_REVIEW` (640–647) heredoc ranges as present fact. ULICENCE3 deleted those heredocs and
replaced the gate with a positive vocabulary checker. Six earlier units chased stale citations; these
are the last two known sites.

## What
Add a **dated inline blockquote pointer** at each stale site, retaining all original text, numbers and
ranges (frozen historical record — verdict dated 2026-10-15 era; do not rewrite). Precedent:
`repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md:296`.

Sites (in `strategy/VERIFICATION_REPORT_11.md`):
- `:23` — method sentence citing `UBUILD1.build.sh:612–637` (patterns 613–636).
- `:272-273` — defect 2 citing `:423–458` reading as the HARD heredoc location; HARD at `:612–637`, REVIEW at `:640–647`.
- sweep hit `:263` — "All `cat >` sites (lines 327, 398, 499, 523, 547, 577, 612, 640)" — 612/640 cited as current `cat >` sites.

## Pointer substance
Superseded 2026-10-16: PATTERNS_HARD / PATTERNS_REVIEW heredocs removed by ULICENCE3, no longer
exist. Gate is now the positive vocabulary checker, heredoc `cat > "$DEST/gate.sh" <<'GATE_EOF'`
(currently :771, closing :896, `chmod +x` :897), fed by `vocabulary/{english,code,public}.txt`
(currently :691, :695–743, :748–769), invoked `bash "$DEST/gate.sh"` (currently :1005).

## Rules
- Write only: `strategy/VERIFICATION_REPORT_11.md`, `scratch/ufix20/**`, `orchestration/units/UFIX20.md`,
  `orchestration/handoffs/UFIX20.json`.
- Never write `/home/zer0null/research-publish-packages`; never git against `/home/zer0null/Duval`.
- Do not touch concurrently-edited files (list in card).

## Report
`orchestration/units/UFIX20.md` + `orchestration/handoffs/UFIX20.json`, seven contracted keys.
