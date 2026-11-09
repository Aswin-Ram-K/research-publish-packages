# TRANCH1-DRYRUN — the ten-cell grid rehearsed offline

**Unit:** `TRANCH1-DRYRUN` · **Offline:** zero requests, zero spawns, zero sockets · **Stamp:** `stamped`
**Grid:** `RUN-A*` — 10 cells x 48 turns (pair at 3 reps, context at 2), `tasks-v6/LR-01.v8.json`,
`--thinking off`, `--max-tokens 4096`, `--max-wall 2880`, `--turn-wall-cap 180`,
`--runaway-turns 2`, per-cell cap 900. **Decision: HELD.**
**Measurement:** [`../experiments/ptr-engine/measure/TRANCH1-DRYRUN.json`](../experiments/ptr-engine/measure/TRANCH1-DRYRUN.json)
· **check:** `python3 experiments/ptr-engine/tools/tranch1_dryrun.py --check`

## The ten cells

| cell | G1 computed (cumulative) | G1 spent / turns / allowance | G1 | G2 projected s (ratio, source) | G2 | G3 n (source) | G3 | treatments fire |
|---|---|---|---|---|---|---|---|---|
| `pointer-stable r1` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=None compact=None lease=None prefix=2 |
| `pointer-stable r2` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=None compact=None lease=None prefix=2 |
| `pointer-stable r3` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=None compact=None lease=None prefix=2 |
| `transcript-grow r1` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=21 compact=None lease=None prefix=None |
| `transcript-grow r2` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=21 compact=None lease=None prefix=None |
| `transcript-grow r3` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=21 compact=None lease=None prefix=None |
| `transcript-compact r1` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=None compact=21 lease=None prefix=None |
| `transcript-compact r2` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=None compact=21 lease=None prefix=None |
| `lease-reopen r1` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=None compact=None lease=23 prefix=None |
| `lease-reopen r2` | 1154 | 1101 / 48 / 5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 (`flag:--hypothesis (hypothesis)`) | refused | grow=None compact=None lease=23 prefix=None |

Every cell is one `cell.py --dry-run` invocation (`--turns 48 --reps 1 --hypothesis H1`) with its
own manifest (`experiments/ptr-engine/measure/dryrun-t1-<arm>-r<rep>.json`); no two share a
filename. `all_ten_allowed = False`. Total marginal cost **530 requests** (48 + ceil(48x68/801) = 53
per cell); the sum of G1's cumulative displays is 11540.

**The grid is HELD, and the reason is a pincer that no flag change can open.** G1 allows every
cell. G2 allows every cell at exactly its ceiling. G3 refuses every cell, because one 48-turn
cell is `n = 48 < 60`. The only shape whose `n` satisfies H1 (declare the arm's pooled reps)
is refused by G2 instead — see the second table.

### G1 — the ledger brake (all ten allow)

G1 prints cumulative spend: `spent + turns + allowance`, with `turns = 48 x arms x reps` and
`allowance = ceil(turns x 68/801)`. Already spent is **1101** against a ledger cap of **4,320**
(headroom 3,219), so every cell prints `1,101 + 48 + 5 = 1,154` and its marginal spend is 53
requests — nowhere near the 900 cap.

### G2 — the mode-aware per-turn wall (all ten allow, at exactly 1.0000 of the ceiling)

`--projected-from` defaults to none, so `projected_turn_wall` comes from the calibrated
projection's `projected_turn_wall_s_by_mode["off"]` — the retained conservative **60 s**, source
`artefact-mode`. It is *not* the 180 s abort cap (`--turn-wall-cap`) and *not* the pooled
218.2 s figure (that is the thinking on/auto value). `48 x 60 = 2,880 s` against `--max-wall
2880`: ratio **1.0000**, allowed because the gate compares `<=`. The measured `thinking=off` p90
of 38.1 s exists in the same artefact but is only used when `--projected-from p90` is passed;
it is not the default and was not used.

### G3 — the pincer (all ten refuse, verbatim)

H1 needs `n >= 60` (`analyze_stats.min_n_for(q=0.95)`), and `n = turns x reps = 48 x 1`. Every
cell's G3 line reads `n=48 < 60`; the verdict text is quoted verbatim in the measurement JSON
(`cells[].g3.refusal`). `--hypothesis H2`/`smoke` was **not** used to get through — that would
have bought a pass with a claim the grid does not make.

| the other horn: arm | reps declared | G1 computed | G2 projected s / max wall | G2 | G3 n | G3 |
|---|---|---|---|---|---|---|
| `lease-reopen` | 2 | 1206 | 5760 / 2880.0 | refused | 96 | allow |
| `pointer-stable` | 3 | 1258 | 8640 / 2880.0 | refused | 144 | allow |
| `transcript-compact` | 2 | 1206 | 5760 / 2880.0 | refused | 96 | allow |
| `transcript-grow` | 3 | 1258 | 8640 / 2880.0 | refused | 144 | allow |

So: 48 turns at reps=1 -> G3 refuses (n=48). 48 turns at the arm's pooled reps -> G3 allows
(n=144 / 96) but G2 projects `144 x 60 = 8,640 s` (pair) and `96 x 60 = 5,760 s` (context)
against `--max-wall 2880` and refuses. **No invocation shape of this grid passes G2 and G3 at
the pinned flags.** Opening it needs a card decision — `--max-wall >= 8640`, a per-rep launch
(which cannot claim H1), or an H2 claim — never a lowered cap, wall, horizon or n-floor.

### Treatments fire inside the horizon

Read from `wall_tokens_by_arm` = **10,616**, never the top-level `wall_tokens` 3,838:
`transcript-grow` first FIFO eviction **TNone**, `transcript-compact` first wall **TNone**,
`lease-reopen` first lease step **TNone**, `pointer-stable` first prefix change **T2** — all at
or below 48. The v8 trap is why this matters: 3,838 sits below v8's own first prompt (3,848), so
a path falling back to it fires the wall near T2 and collapses both transcript arms into one
another. `design_cap_tokens` reads **10,616** in all ten manifests.

### Zero network, zero spawn

Every invocation ran under a `sitecustomize.py` `sys.addaudithook` injected on `PYTHONPATH`
(`cell.py` unedited), recording `socket.*`, `urllib.*`, `http.client`, `subprocess.*`, `os.exec*`,
`os.fork*`, `os.posix_spawn*`. Events per cell: **0 network, 0 spawn**, and every run printed
"0 requests sent, no endpoint contacted". `unshare -n` is unavailable here, so the audit hook
plus the tool's own line is the primitive. The per-arm 8-token warm-up lives inside
`run_longrun.py`'s own allocation; **it is not in cell.py's G1 arithmetic** (`would_spend =
turns_total + allowance` only) and is declared here as deliberately *not* projected rather than
silently omitted.

## What would stop the grid

Each condition was checked by the rehearsal; the live run must still not violate it.

1. **A gate refusal on any cell** — live exits are 4 (G1), 8 (G2), 12 (G3). This rehearsal's ten
   cells are held on G3 (`n=48 < 60`); a G3 refusal is a finding, never something to route
   around with `--hypothesis H2` or `smoke`.
2. **`projected_wall > --max-wall`** — the ceiling is exact (2,880 s at 60 s/turn for 48 turns);
   any larger per-turn wall, or any reps>1 declaration, refuses. The pooled 218.2 s figure would
   refuse a 48-turn cell outright.
3. **A treatment that never fires inside 48 turns** — grow with no FIFO eviction, compact with no
   digest request, lease with no step, or pointer with no prefix change makes the arm
   indistinguishable from its control.
4. **`design_cap_tokens` reading 3,838 (or 65,536) for any arm** — the runner must read
   `wall_tokens_by_arm[arm]` (10,616); the top-level value is below v8's first prompt.
5. **A spawn or a socket during a dry run** — a dry run that would have spawned or connected is
   a defect in `cell.py`, and the launch stops there.
6. **Two cells sharing a manifest filename** — one cell, one manifest, unique per (arm, rep).
7. **Any pinned file moving between the first and last invocation** — the rehearsal is then
   `unstamped`, not a pass, and must be re-run on the settled tree.

## Pinning

`sha256` recorded before and after the ten runs for `cell.py`, `run_longrun.py`, `client.py`,
`exit_codes.py`, `tasks-v6/LR-01.v8.json`, `analyze_stats.py`: **stamped (no file moved)**.
