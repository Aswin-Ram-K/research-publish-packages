# UNIT `PARM-1-ERRATA`

**Card:** `67e4cd7f-662f-4f8c-ab7e-ae978641d66d` · execution `b109aa99-768e-4c6d-9cd5-4d95a42e962c`
**Mode:** automated, offline. Zero inference requests, no network, no `git`. Frozen prereg, fixture, grade and
rows files read-only — additive errata only.
**Gated on:** `CHECKPOINT-ITEMS-V2` (partial), `TVS-DEFINE-AND-COMPUTE` (done).

## Purpose
Make the frozen PARM-1 denominators honest **before** the adjudicating grid runs, without re-freezing
anything. `PARM-1` froze H3 over 12 checkpoint ids at a 2/12 = 16.7 pp margin; two later units changed what
those 12 ids are worth (3 are now NONE-kind) and created a second, different denominator (TVS, 3 ids).

## Outcome
- `docs/PARM-1-ERRATA.md` — dated additive errata, E1..E5, each quoting the frozen text with `file:line`,
  the measured artefact with `file:line`, and what the run will therefore report. No edit to
  `docs/PREREG-ARM-RUN.md`; its rule body still hashes to `21cb85…` (`:276`).
- `E1` H3's 12 ids are **9 substantive + 3 NONE** (`cp.3.t14` / `cp.5.t20` / `cp.10.t42`); every H3 number
  travels as `x/12` with the NONE items flagged **and** `x/9` substantive, neither replacing the other.
- `E2` TVS's denominator is **3 ids** — a different claim, never a fraction of 12; its 3 ids are a subset of
  the substantive 9 (v6 names `cp.0.t12`, `cp.1.t24`, `cp.2.t46` → v7 `cp.2.t12`, `cp.6.t24`, `cp.11.t46`).
- `E3` `repair.t30` is **not scored**: turn 30 is absent from the 12 checkpoint turns, so the frozen 12-item
  denominator is unaffected; `2/13 = 15.4 pp` was never in force. Arithmetic shown in a table.
- `E4` 11 thresholds listed as **NOT** changed, with their `file:line`; the gate stays on `x/12` and on
  "more than 2 checkpoints", and `8 of 12` unadjudicable is unchanged.
- `E5` `CHECKPOINT-ITEMS-V2` settles `partial`; 12/12 are decidable **on paper** (`fixture_coverage.py` exit 0),
  and no claim is made about any run's 12/12 — run-time `decidable` is a `grade_v5` measurement, printed by name.

## Machine check
`experiments/ptr-engine/tools/parm1_errata_check.py` — offline, stdlib: (a) rule-body digest vs the recorded
`21cb85…` and a 13-threshold-phrase digest, (b) recomputes the id census from `LR-01.v7.json` and compares it
to the errata's claims block, (c) refuses any claim key it cannot recompute, plus the TVS denominator re-read
from `docs/TVS.md` and the `repair.t30` exclusion. Exit 0 on the real errata.
`experiments/ptr-engine/longrun/tests/test_parm1_errata.py` — 8 passed, including the contracted red case
(errata mutated to `"ids_substantive": 12` ⇒ exit 1) and a frozen-copy threshold mutation (16.7 → 20.0 ⇒ exit 1).

## Numbers
```
ok   frozen rule body sha256 = 21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8
ok   13 threshold phrases byte-identical, sha256 = 069d28a4a0...
ok   ids_total = 12 / ids_substantive = 9 / ids_none = 3
ok   ids_by_kind = {'CALL': 4, 'NUM': 5, 'NONE': 3}
ok   2/12 = 16.7 pp (matches the frozen 16.7)
ok   TVS declared space re-read from docs/TVS.md: 3 ids
ok   repair.t30 = turn 30, absent from checkpoint turns [6, 8, 12, ... , 46]
PASS parm1 errata check: frozen bytes intact, census 12/9 substantive/3 NONE, TVS 3 ids, repair.t30 excluded
8 passed in 0.19s
```

## What a reader must know before reading an H3 number
`x/12` is the gate; 3 of the 12 are NONE items a degenerate `ANSWER: NONE` policy passes for free, so `x/12`
must always be read with the NONE count and with `x/9` substantive beside it — and a tvs is a token sum over
3 ids, never a 12-item accuracy.
