# PRECONDITION-10-SCOPE — judge each arm on its own treatment

**Unit** PRECONDITION-10-SCOPE · **date** 2026-10-26 · **offline** (zero model requests) ·
**owner of the defect** `experiments/ptr-engine/tools/run_a_star.py:796-805` (pre-fix).

## 1. The defect

The live era-B canary (CANARY-ERA-B-3) stopped after three of four cells:

    RUN-A STOP precondition 10: transcript-compact cell 1 no mechanism {'evicted_turns': 0, 'digest_rows': 0, 'lease_ge2_turns': 0}

The guard built ONE readiness expression for EVERY arm out of three markers, two of which
belong to other arms, and hard-coded `"pointer-stable": True`:

    need = {"transcript-grow": m.get("evicted_turns", 0) > 0,
            "transcript-compact": m.get("digest_rows", 0) > 0,
            "lease-reopen": m.get("lease_ge2_turns", 0) > 0,
            "pointer-stable": True}[arm]

A compact cell cannot have `evicted_turns` (the grow treatment) or `lease_ge2_turns` (the
lease treatment), so the check fired on the absence of **other arms'** treatments. Cell 15
(`lease-reopen`) was never measured: 12 of 48 priced requests unspent, `shape_unknown`.
Precondition 10 is right to refuse a cell whose own treatment never fired; it was wrong to
ask one arm to prove another arm's mechanism.

## 2. The fix — data, not `if`s

`ARM_TREATMENT` in `experiments/ptr-engine/tools/run_a_star.py` is the whole contract. A cell
is judged only on its own row; other arms' markers are reported but never consulted.

| arm | own marker (row-counted) | threshold | due when |
|---|---|---|---|
| `pointer-stable` | `prompt_change_turns` | ≥ 1 | ≥ 2 turns carry a prompt identity |
| `transcript-grow` | `evicted_turns` | ≥ 1 | the cell's `prompt_tokens_max` ≥ the arm's wall |
| `transcript-compact` | `digest_rows` | ≥ 1 | the cell's `prompt_tokens_max` ≥ the arm's wall |
| `lease-reopen` | `lease_ge2_turns` | ≥ 2 | `turn_last` ≥ the first declared `lease_reopen_turns` entry |

`precondition10(arm, stats)` returns one of three verdicts, and only one of them stops:

- **fired** — own marker ≥ own threshold; the cell proceeds.
- **not-due** — the cell's own horizon made the arm's treatment impossible (a 12-turn cell
  cannot reach a wall declared for turn 23); its absence is not evidence about the label, so
  the cell proceeds with a NOTE (`precondition10_not_due` in the journal).
- **missing** — the treatment was DUE inside this cell and its own marker is below its own
  threshold. **STOP**, naming the arm and its own marker.

`due` fails CLOSED: an unreadable fixture makes every treatment "due", so a missing fixture
can never talk the guard out of stopping. The wall and lease turns are read offline from the
declared fixture through `run_longrun.fixture_for_arm` (the planner that owns them).

**Scope caveat, stated not hidden.** `pointer-stable`'s defining field `prefix_sha256` is
computed by the runner (`run_longrun.py:1165`) but is not in `make_row`'s dict — 0 of 788 rows
carry it (`docs/ARM-INTEGRITY.md` §3). The row that exists does carry `prompt_sha256`, so the
witness is *prompt identity change*: a cell whose prompt identity never changes has no prefix
dynamics to be stable against. This is a proxy for the arm's own treatment, not the digest the
planner knows; when `prefix_sha256` reaches the rows, `rows_stats` should count it directly and
this row of `ARM_TREATMENT` changes — a data edit.

## 3. Red → green, on the real canary's rows

Rows replayed: `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T202040Z.jsonl`,
`…-transcript-grow-20261026T202444Z.jsonl`, `…-transcript-compact-20261026T203733Z.jsonl` —
the three cells the live canary actually wrote.

| step | old expression | scoped rule |
|---|---|---|
| cell 1 `pointer-stable` | `True` (no check) | **fired** — `prompt_change_turns` 11 |
| cell 7 `transcript-grow` | fires — `evicted_turns` 10 | **fired** — 10 ≥ 1 |
| cell 13 `transcript-compact` | **STOP** — all three markers 0, `digest_rows` 0 | **not-due** — max prompt 5586 < wall 10616, so no digest was owed at 12 turns |
| cell 15 `lease-reopen` | never reached | **not-due** at 12 turns (declared reopen turns 23, 40) → cell runs, 12 rows measured |

The compact arm's own `digest_rows: 0` remains a **real finding about that arm at 12 turns**
(it is recorded in the cell's stamp as a zero-marker cell); what it is not is a reason to halt
the canary before a different arm's cell. The guard still stops when the digest was owed.

## 4. Not weakened — one test per arm

`experiments/ptr-engine/tests/test_precondition10_scope.py` (11 tests, offline):

- compact own `digest_rows` 0 while grow AND lease markers are nonzero ⇒ **missing**;
- grow own `evicted_turns` 0 ⇒ **missing**;
- lease own `lease_ge2_turns` 1 (< threshold 2) ⇒ **missing**;
- pointer own `prompt_change_turns` 0 (identity present) ⇒ **missing**;
- every arm with only the OTHER arms' markers at zero ⇒ **proceeds** (the card's distinction);
- real three-cell replay: old expression stops at 13, scoped rule reaches 15.

Offline shape unchanged: `--canary --dry-run` → `DRY END cells=4 refused=0 requests=0 …
canary_arms=4 canary_requests=48`, exit 0; grid plan → `DRY END cells=16 refused=0
requests=0`; zero spawn, zero socket (recorder reused from
`experiments/ptr-engine/tests/test_launcher_pin_and_cells.py`).

Run: `/usr/bin/python3 -m pytest experiments/ptr-engine/tests/test_precondition10_scope.py -q`
→ `11 passed`.

## 5. The grid's stop rule 10

**No unintended change.** A complete 48-turn grid cell reaches every arm's trigger — wall
10616 is passed by grow/compact inside the grid window, `lease_reopen_turns` 23/40 are inside
48 turns, and pointer's prompt identity changes by turn 2 — so `treatment_due` is true for all
four arms and the scoped rule reduces exactly to the old rule, with one INTENDED tightening:
`lease-reopen` now needs `lease_ge2_turns ≥ 2` instead of `> 0`, which is this card's own data
edit, not drift. For a short/aborted cell the rule no longer stops at 10; that is the intended
scoping and the existing guards (rule 7 on `rc`, the zero-marker stamp) still exclude it, so
`RUN-A-STAR-2`'s card and the grid card need no update.

## 6. Environment note

While this card ran, `measure/REQUEST-LEDGER.json` carried `remaining` 3144 against the frozen
baseline's 3192, so `run_a_star.py:229` refused the launch by name (correctly — it will not
pick between two ledger figures). That refusal is the ledger owner's, not this guard's; the new
tests pin both records to the pair the canary's own launch read (3192 / cap 4320), which is
exactly what isolates the scope change. Five neighbouring launcher dry-run tests currently
fail on the same refusal, before the cell loop, and are unchanged by this card.
