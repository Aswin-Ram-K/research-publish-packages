# UNIT `VERDICT-ALLOWLIST-WRAP`

**Purpose.** `RECLAIM-GREEN-ROWS` (board #992) left 7 of 9 green cards without a verdict row because
`checkVerdictCommand` refused their stored commands: `.venv/bin/python` (5 cards) and `node -e` split at
`;` (2 cards). `bash` *is* on the allow-list. Run each refused card's **own stored command** as
`bash -lc '<stored command>'` and record a row for the ones that exit 0.

**Hard bound.** 24 tool calls. Zero inference requests, zero network. Never `ask_user_question`.
Recording only — no edit to any card's handoff/journal, `cell.py`, `run_longrun.py`, rows/grade files,
`WITHDRAWN.json`, `PARM-1`, or the verdict allow-list code.

**Stored commands are taken verbatim** from `experiments/ptr-engine/measure/RECLAIM-GREEN-ROWS.json`
(rows where `exit_today == 0` and `row_recorded == false`). Nothing invented.

**Rows.** `command = bash -lc '<stored>'`, `exitCode` measured, `sha = f17663d1…` (HEAD re-read and
confirmed before recording). A row is recorded only for a measured exit 0; a non-zero exits the card as a
red with nothing recorded. A refusal is kept verbatim and the card's attempt stops.

**Deliverables.** `experiments/ptr-engine/measure/VERDICT-RECLAIM.json` · `docs/VERDICT-RECLAIM.md` ·
`orchestration/units/VERDICT-ALLOWLIST-WRAP.md` · `orchestration/handoffs/VERDICT-ALLOWLIST-WRAP.json` ·
`orchestration/journals/VERDICT-ALLOWLIST-WRAP.jsonl` · one board report line.

**Exit code propagation proof.** `bash -lc 'exit 3'` → captured 3 (run before any card command, so the
wrap demonstrably cannot launder a failure into a pass).

**Result.** 7/7 green under the wrap; **recorded 3 / refused 4 / red 0**.
- Recorded: `R2-OPT-SIM`, `SIM-PROMOTE`, `RUN-INSTRUMENT-FIX`.
- Refused `command-frozen` ×2: `R2-VLLM`, `C63-CELL` — **their executions already carry a verdict row**,
  for a *different* command than the census attributed. Census correction, not a gate defect.
- Refused `command-not-allowed "const"` ×2: `ACCOUNT-INVENTORY`, `PROFILE-PACK` — the checker splits on
  `;` quote-unaware, so the node program's second statement is read as the runner. The wrap cannot fix it.

**Honest limit (the line the record must carry).** A row proves *"the stored command exits 0 today under a
shell runner"*. It does **not** prove the card was correct when it ran, and it does **not** move the card's
column. After this pass **5 of 9** green cards carry a row and **all nine are still in `failed`**.

**Next hint.** `DECISIONS-2` item 13 needs the operator: either a quote-aware split plus a venv-launcher
entry in `checkVerdictCommand` (reclaims 4 without a re-run), or one fresh `reclaim` execution per card so
the row cites the tree it ran against. This unit does neither — it only measures.
