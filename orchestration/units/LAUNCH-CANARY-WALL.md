# UNIT `LAUNCH-CANARY-WALL`

**Objective.** Lift the canary's wall above its own projection, and stop `--dry-run`
from reporting green while a gate says it would refuse. Offline: zero requests.

**Write paths.** `experiments/ptr-engine/tools/run_a_star.py`;
`tests/test_launcher_dryrun_refusal.py` (new); this file; the handoff; the journal.

## The two defects (quoted)

G2 — `experiments/ptr-engine/measure/PROJECTION.json` calibration 60.0 s/turn, billed by
`cell.py`'s `eval_gate_projection`, against the canary default wall
`experiments/ptr-engine/tools/run_a_star.py:365` (pre-change: `a.max_wall = 600 if
a.max_wall is None else a.max_wall`):

```
cell: 0/7 dry-run G2 WOULD-REFUSE computed=720 s limit=600 s (--max-wall) … turns=12 projected_requests=12 projected_wall~=720s (cap-per-turn 180s -> worst case 2160s) cap=600s projected-turn-wall=60.0s source=artefact-mode thinking=off
RUN-A DRY END cells=4 refused=0 requests=0 claim=smoke turns=12 max_wall=600 canary_arms=4 canary_requests=48   (rc 0)
```

(turns=12 and 12 × 60.0 s = 720 s > 600 s. The `CANARY-GATE-DRYRUN` handoff quotes the
same launcher line as `cells=1`; the launcher's real pre-change line said `cells=4` —
four canary arms, one cell each — which is why the refusal count is per arm.)

rc — the dry-run tally, pre-change `run_a_star.py` (`bad += rec["rc"] != 0`), could only
see `cell.py`'s exit code, and `cell.py:1964-1975` exits 0 on a would-refuse *by
contract* ("exit 0 means the PREVIEW ran, not that the gates allow"). Hence
`refused=0`, `rc 0` — a green surface over a blocked launch.

G3 was already correct and is untouched: `G3 allow … claim=none comparison_eligible=False
mode=smoke`, `min_n=0`.

## Fix 1 — the wall, not the arithmetic

`CANARY_MAX_WALL = 900` (`run_a_star.py`), used by the canary branch:
`a.max_wall = CANARY_MAX_WALL if a.max_wall is None else a.max_wall`.

**Why 900:** the floor is `12 × 60.0 s = 720 s` at the artefact-mode calibration
(`thinking=off`); 900 = that floor + 25 % headroom (75 s/turn), still far below the grid's
2880 s and below 12 × 180 s worst case. The projection, the 60.0 s calibration, G2's
formula and the grid's `--max-wall 2880` are **not** touched (grid argv diff empty).

## Fix 2 — a WOULD-REFUSE line is a refusal

`run_cell` now records `rec["would_refuse"]` (gate verdict lines matching
`_GATE_WOULD_REFUSE = re.compile(r"dry-run G[123] WOULD-REFUSE\b")` — the bare token is
not enough, because `cell.py`'s closing sentence *names* "WOULD-REFUSE verdict lines"
while allowing). The dry-run loop before/after:

```
before:  bad += rec["rc"] != 0
after:   bad += 1 if (rec["rc"] != 0 or refused) else 0
```

Exit code **1** — the launcher already documents 1 for "a dry run that saw a cell fail"
(`return 0 if not bad else 1`); **2** is `cell.py`'s preflight/G3 code
(`cell.py:14-15`, `exit_codes.EXIT_TABLE`) and is not the launcher's to reuse.

## Four states (dry run only, real binaries)

| state | G2 | launcher | rc |
|---|---|---|---|
| canary, new wall 900 | `G2 allow` (720 s of 900 s) | `refused=0 requests=0 … max_wall=900` | 0 |
| canary, old wall 600 | `G2 WOULD-REFUSE computed=720 s limit=600 s` | `refused=4 requests=0 … max_wall=600.0` | 1 |
| grid cell argv | — | identical: sha256 `ee7c2f9360179e3c` before and after, `diff` empty | — |
| grid cell, `--max-wall 60` | `G2 WOULD-REFUSE computed=2,880 s limit=60 s` | `refused=1 requests=0 … max_wall=60.0` | 1 |

`refused=4` on the canary is one refusal per arm (4 arms × 12 turns); each cell line
carries `WOULD-REFUSE=1`, and a single-cell vector reports `refused=1`.

## Red → green

Reverting only the tally (`bad += rec["rc"] != 0`) makes the blocked grid cell green
again: `refused=0 … max_wall=60.0`, **rc 0**, while its own G2 line still says
`WOULD-REFUSE computed=2,880 s limit=60 s`. With the fix: `refused=1`, rc 1.

## Requests a blocked canary would have burned

**Zero** — G2 refuses at stage 3b/7 projection, before the runner starts — so the price
was not spent quota but a permanently green gate: the dry run that said "ready to launch"
could never send request 1, and only a live launch would have discovered it.
