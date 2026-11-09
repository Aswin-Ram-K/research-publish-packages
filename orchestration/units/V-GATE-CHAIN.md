# V-GATE-CHAIN — adversarial verification of the preflight gate chain

**Verifier, not author. I fixed nothing.** Ran after `WIRE-GATES` settled `done`.
Offline: zero inference requests, no network, no `git`. Every mutation in a `/tmp` copy.

## Pinned artefact (the target moved under me)

| file | sha256 |
|---|---|
| `experiments/ptr-engine/longrun/cell.py` | `f387c4abbb835f2e28dc641f6ba2ee962dc5b0ee29a25514ac94cdb338a89fc2` (65,374 B, 1334 lines) |
| `experiments/ptr-engine/longrun/tests/test_cell_gates.py` | `47eab81913d19f692334a9bbf4c498479ea1f32e5d78f2d68f87e46d5209dfcf` |
| `experiments/ptr-engine/longrun/exit_codes.py` | `f75e2649ea4345241635b6360b6ade9305c8fdb9138cd37c3e744bc9ca2b0c32` |
| `docs/GATE-CHAIN.md` | `1ec5aca9ac3d295faa1045c6604e1fcfa2f02d717a6cfd3c60d81e6366f3f70f` |

`cell.py` was 1313 lines at 10:58 and 1334 lines at 10:59:10 — **a concurrent unit (the
exit-code table work, `exit_codes.py` mtime 10:57, `test_exit_codes.py` 10:58) rewrote it
mid-verification.** All attacks below ran against the pinned `f387c4ab`; the repo bytes were
unchanged by me (sha identical before and after my runs).

## Method

A `/tmp` copy of `experiments/` + `docs/`, a fake runner (`CELL_RUNNER_PATH`) that writes a
marker instead of opening a socket, and a fake ledger (`CELL_LEDGER_ARTEFACT`). Attack inputs
are my own numbers, not the unit's fixtures. Gate verdicts are read from the printed
`0/7 dry-run <GATE> allow|WOULD-REFUSE` line and from live-mode exit codes; refusals abort
before `stage_run`, so no case that could send ever reached a runner.

## Results

### A. Fabricated headroom — **chain holds**
Ledger artefact `{"budget":{"cap":11,"reserve":0},"files":[]}`, cell needs 11 requests
(10 turns + ceil(10×68/801)=1 follow-up):
- `cap=11` → `3a/7 G1 ledger gate ok G1 11/11 requests`, runner invoked, rc after gates 10.
- `cap=5` → `EXIT 4`, `G1 ledger-cap REFUSED: computed 11 requests | limit 5 requests
  (cap 5 - reserve 0 - spent 0) | artefact ledger-5.json (sha256 91dab2ac…)` — names the shortfall.
The cap is read from `doc["budget"]["cap"]` **only**; two values of the same artefact flipped
the verdict, and the counting is delegated to `request_ledger.build_report`.

### B. Projection — **one named defect**
`turns=10`, requests=10, calibrated 60 s → projected 600 s; worst case printed 1800 s.
- 601 s → allow, runner invoked (rc 10). 600 s → allow.
- 599 s → **EXIT 8** `3b/7 projection … projected_wall~=600s … cap=599s`.
- 700 s → **allow**, rc 10: no silent fallback to the 180 s/turn worst case (1800 s). The
  `PROJECTION-CALIBRATION` regression is genuinely gone; `source=artefact` is in the line.
- **DEFECT B1: `--max-wall 0` → allow (rc 10, runner invoked). `--max-wall -1` → allow
  (rc 10).** `eval_gate_projection` computes `"ok": not (max_wall > 0 and projected > max_wall)`,
  so a non-positive ceiling disables G2 while the refusal condition (`projected 600 > 0`)
  holds. A live cell can defeat the projection gate by passing `--max-wall 0`.

### C. Silent claim — **DEFECT C1, contract claim 6 is false**
- `--turns 48 --hypothesis H1` → EXIT 2, `G3 prereg REFUSED: computed n=48 | limit n >= 60`.
- `--hypothesis none` → EXIT 2, `silence is not a claim`.
- `--hypothesis H9` → EXIT 2, `PARM-1 does not define H9`.
- `--turns 10 --hypothesis H2` → allow (correct: H2 decidable at its frozen threshold).
- **`--turns 48` with NO `--hypothesis` flag → allow, rc 10, runner invoked**, printed as
  `claim H2 … source=default`. `_declared_hypothesis` falls through to `"H2",
  "default:built-in (PARM-1 primary)"`, so the "no hypothesis" branch is unreachable by
  silence — it can only be reached by typing `none`. **Silence is a pass, not a refusal.**

### D. Gate skip — **DEFECT D1, otherwise holds**
- Unknown flag → rc 2, no runner. `--dry-run` → rc 0, all three gates printed, no runner, no row file.
- `--offline` → rc 2 on a missing row file; it skips all gates but sends nothing.
- `--turns 0` → rc 2 at G3, not a 0 exit.
- No route returns 0 with a gate refusing, and no route reaches a request with **no** gate verdict.
- **DEFECT D1 (same as B1): `--max-wall 0` reaches a request with G2's refusal condition true.**
- **AUDIT SURFACE: `CELL_LEDGER_ARTEFACT` / `CELL_PROJECTION_ARTEFACT` / `CELL_PREREG_ARTEFACT`
  env vars let the caller choose the limit.** I used them to make cap 5 vs 11 change the
  verdict; a live cell can point G1 at an artefact with a cap of its own choosing. Documented
  as a test seam, but live-reachable and unrecorded in the refusal.

### E. Exit codes — **collision at 2, by design**
Induced: **2** (bad fixture), **2** (bad prereg artefact), **2** (H1@48), **2** (explicit none),
**2** (unknown flag), **3** (budget=1), **4** (cap=5), **8** (max-wall 599), **10** (fake runner →
grade). **Not induced without a live request: 1, 5, 6, 7, 9, 11.**
Two distinct conditions share code 2: *fixture/harness preflight* and *G3 prereg refusal* (and
argparse usage errors, and an unreadable gate artefact). `exit_codes.py` documents this
(`EXIT_PREFLIGHT` covers "G3 prereg" and argparse), but the card's table gives G3 no code of its
own, so "distinct and pinned" holds for 3/4/5/6/7/8 and not for G3. Code 4 is shared by G1 and the
runner's propagated ledger refusal — same condition, acceptable.

### F. Digest phantom — **chain holds**
`eval_gate_ledger` returned `artefact_sha256` equal to the sha256 of the artefact bytes at read
time (`07add6778ad1b940…`); appending one byte to the same path changed the sha to
`58709559156cf685…`, so the recorded digest is of bytes, not of a name, and would detect the
mutation. `write_gate_manifest` writes `artefact_digests` and is called at `cell.py:1204`,
before `stage_run` at `cell.py:1212`.

## Independent red→green (mine, not the unit's)

Each gate neutered by a one-line edit in a `/tmp` copy, dry-run so no network:

| gate | intact | neutered | restored |
|---|---|---|---|
| G1 (`"ok": bool(b["within_budget"])` → `True`) | REFUSE | ALLOW | byte-identical |
| G2 (`"ok": not (max_wall > 0 and projected > max_wall)` → `True`) | REFUSE | ALLOW | byte-identical |
| G3 (`ok = n >= min_n` → `True`, H1 branch) | REFUSE | ALLOW | byte-identical |

All three are independently load-bearing; none is a gate nobody verified.

## Honesty: the unit's own test counts

`python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cell_gates.py'`
from the repo root → **Ran 9, FAILED (errors=1)**: `test_dry_run_touches_no_network` errors with
`ModuleNotFoundError: No module named 'exit_codes'` (the in-process `exec_module` needs the
long-run dir importable). With `PYTHONPATH=…/longrun` → **OK (9/9)**; from the long-run dir → **OK
(9/9)**. So "9/9" is true only under an invocation the handoff does not state, and the stated
command is currently red because the concurrent exit-code work added a top-level
`import exit_codes`. Reported as a repronouncement gap, not as gate dishonesty.

## Verdict

`fail`. The chain is sound on A, B-baseline, C-explicit, D-unknown-flag/dry-run/offline, E (with a
named collision) and F, and all three gates are independently load-bearing. It fails the card's
own fail criterion: **a live cell starts with G2's refusal condition true when `--max-wall` is 0
or negative**, and **G3 passes a run that declares no hypothesis** (contract claim 6 false).
