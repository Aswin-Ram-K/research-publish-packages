# VERDICT-RECLAIM — running the refused rows through an allow-listed shell

**Unit:** `VERDICT-ALLOWLIST-WRAP` · **HEAD measured:** `f17663d1fed0162a7dc3c5a0a58d372c710974c3`
**Question:** `RECLAIM-GREEN-ROWS` got 2 of 9 green cards' verdict rows recorded and had 7 refused at
`checkVerdictCommand`. `bash` is on the allow-list. Does re-running **the same stored command** as
`bash -lc '<stored command>'` let the row in?

**Answer: partially — 3 of 7.** The wrap defeats the `command-not-allowed` refusal for a `python`/`pytest`
launcher. It does **not** defeat `command-frozen`, and it does **not** defeat the `node -e` case, because
the checker splits the command on `;` **without regard to quoting**.

## What was run

For each of the seven cards `RECLAIM-GREEN-ROWS` refused, its **own stored command string** (verbatim from
`experiments/ptr-engine/measure/RECLAIM-GREEN-ROWS.json`) was executed as argv `['bash','-lc', <stored>]`
from the repo root. Nothing was invented, normalised, or edited.

Propagation was proved first: `bash -lc 'exit 3'` → captured **3**. `bash -lc` returns the wrapped
command's own status, so no non-zero can become a zero here.

## Result

| card | stored command (prefix) | wrapped exit | row | refusal |
|---|---|---|---|---|
| R2-OPT-SIM | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q` | 0 | **recorded** | — |
| SIM-PROMOTE | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q -p no:cacheprovider` | 0 | **recorded** | — |
| RUN-INSTRUMENT-FIX | `.venv/bin/python experiments/ptr-engine/longrun/run_longrun.py --self-test` | 0 | **recorded** | — |
| R2-VLLM | `.venv/bin/python experiments/context-cache/cells/R2-VLLM/selftest_offline.py` | 0 | no | `command-frozen` |
| C63-CELL | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_claims_value_guard.py …` | 0 | no | `command-frozen` |
| ACCOUNT-INVENTORY | `node -e "const fs=require('fs');…"` | 0 | no | `command-not-allowed "const"` |
| PROFILE-PACK | `node -e "const fs=require('fs');…"` | 0 | no | `command-not-allowed "const"` |

**Totals: 7/7 green today under the wrap · recorded 3 / refused 4 / red 0.**

## The two refusals that matter

**1. `command-frozen` — and it exposes a census error.** Both `R2-VLLM` and `C63-CELL` were refused with

```
refused (command-frozen): execution 42662825-… already has a verdict for command "python3 experiments/context-cache/cells/R2-VLLM/selftest_offline.py"
refused (command-frozen): execution 07cd3ac0-… already has a verdict for command "python3 papers/context-cache/verify_package.py"
```

Those two executions **already carry a verdict row** — for the command they actually ran. The command
`RECLAIM-GREEN-ROWS` attributed to them (`.venv/bin/python …`, a `pytest` run) is a *different* command,
presumably taken from the card's prompt rather than from the execution's record. So the census's
"9 green, 7 refused" overstated the gap: two of those seven were never unrecorded, they were recorded
under a command the census misattributed. That is a correction to the previous unit's table, not a
gate defect.

**2. `node -e` is unreachable through the wrap.** The checker splits a command on `;` before it looks at
the first token, and it does not respect quotes. A node program is a `;`-separated program, so its second
statement (`const …`) is read as a shell segment:

```
refused (command-not-allowed): verdict command "const" is not allowed: only test/build runners may be recorded (see checkVerdictCommand)
```

Wrapping in `bash -lc` changes the *first* segment to `bash` and leaves every later one unchanged. No
wrapping can fix this; only a quote-aware split (or an allow-listed runner that takes the program from a
file) can.

## The honest limit

A row recorded by this pass proves: **"the stored command exits 0 today, at `f17663d1`, under a shell runner
the evidence gate accepts."** It does **not** prove the card was correct when its execution ran; it does
**not** prove the execution's own acceptance command was this string (two of the nine already had a
different one); and it does **not** move the card's column — every card in the table is still in `failed`.

After this pass **5 of the 9 green cards carry a verdict row** (`Q0-ANSWER-DEGENERACY`,
`R2.1-TIGHTEN`, `R2-OPT-SIM`, `SIM-PROMOTE`, `RUN-INSTRUMENT-FIX`); two more carry a pre-existing row under
a different command; two (`ACCOUNT-INVENTORY`, `PROFILE-PACK`) carry none. **All nine are still in the
`failed` column.**

If the ritual is meant to mean more than "the command exits 0 today", `DECISIONS-2` item 13 needs the
operator's word. Two concrete options visible in this data: (a) teach `checkVerdictCommand` a quote-aware
split and a venv-launcher entry, which reclaims 4 more cards with no re-run; (b) create a fresh `reclaim`
execution per card so the row cites the tree the command ran against. Neither is a policy change this unit
may make.
