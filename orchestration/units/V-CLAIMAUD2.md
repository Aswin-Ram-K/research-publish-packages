# V-CLAIMAUD2

Verifier unit — write-capable retry of `V-CLAIMAUD`.

## Objective

Audit the claims in `papers/context-cache/CLAIMS.md` above C52 (C53–C62, ten claims) and the
count-consistency claim of the package. Re-run the evidence commands rather than trusting the
documents; re-check the source-cell digests; include a red→green check on at least one guard.
This unit is **not** the author of the material it judges.

## Context carried in

- Predecessor `V-CLAIMAUD` (read-only) produced no handoff, hence this retry.
- The card prompt was one line and carried no bound or write paths; the conservative defaults
  are recorded under `assumptions` in the handoff rather than stalling (AGENTS.md, "Automated
  sessions never ask the user").

## Hard bound

Max 40 tool calls / 21 used. Stop condition: if the count question cannot be settled from
`recompute.py`, `verify_package.py` and an independent parse of `CLAIMS.md` in 3 attempts, STOP
and report `partial` naming the remainder.

## Declared write paths

- `orchestration/handoffs/V-CLAIMAUD2.json` (written first, per the automated tag)
- `orchestration/units/V-CLAIMAUD2.md` (this card)
- `papers/context-cache/CLAIMS.md` — touched **only** for the red→green test, restored byte for
  byte in the same command; verified restored.

## Method

1. Re-ran `papers/context-cache/recompute.py all`; read every value line for C53–C62.
2. Re-ran `papers/context-cache/verify_package.py`.
3. Census by independent parse (not the checker's own function): claim ids matching
   `^\|\s*(C\d{2})\s*\|`, counted, de-duplicated, gap-checked against C01–C62.
4. Cross-read `READER-MAP.md` for 1:1 coverage.
5. Re-computed sha256 of the five cells backing C52–C62 and compared to the digest table.
6. Red→green: planted a synthetic C99 row in `CLAIMS.md`, confirmed `verify_package.py` fails
   exit 1, restored, confirmed exit 0. Second, negative attempt with a non-`C\d{2}` first cell.
7. Read the Coverage section against what the tool actually prints.

## Verdict

`pass` on all ten values (C53–C62 every value reproduces; source digests match; 62/62 1:1
mapped). Two prose defects found in the Coverage section, both recorded under `not_reproduced`
and `overstated`: a stale count of 58 against an actual 62 claims / 59 printed, and a
misclassification of C55–C60 as not running under `grid_guard` when `recompute.py:1176` puts
them there.

## Out of scope

No causal re-testing of C53's locality attribution (arithmetic only, recorded `unverified`); no
second cell for C62's generality, which the manuscript already scopes honestly.
