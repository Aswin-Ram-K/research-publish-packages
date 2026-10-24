# UFIXDEP5 — de-falsify the "live value" claim at `strategy/ZENODO_DEPOSIT.md:22-23`

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Type:** bounded wording fix (not a verifier unit)
**Hard bound:** 6 tool calls. Write paths: `strategy/ZENODO_DEPOSIT.md`, `scratch/ufixdep5/**`, `orchestration/units/UFIXDEP5.md`, `orchestration/handoffs/UFIXDEP5.json`.

## Defect (from `strategy/VERIFICATION_REPORT_DEPOSIT_4.md` / VDEPOSIT4)
`strategy/ZENODO_DEPOSIT.md:22-23` carries the phrase **"live value `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3`"** (with `157650 B`).
That digest is two generations stale and is NOT live. Current archive: **158,956 B, sha256
`bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2`**. The file already has a top
supersession banner and an appended dated section (~`:429+`) carrying the correct value; the only wrong
thing is the present-tense wording **"live value"** at `:22-23`.

## Job
1. Re-word `:22-23` so it reads as the value current on its own date (dated-history style used elsewhere in
   the file). Do NOT delete the row; do NOT delete the digest. Assert before-string occurs exactly once.
2. Sweep the whole file for `live value`, `live:`, `current`, `LIVE`; classify each hit false-present-tense
   (fix same way) vs correctly-dated history (leave).
3. Report before/after byte size + sha256.

## Constraints
No archive/package/paper/report writes; no rebuild; no network. Archive must stay `bcdbf75e…`.

## Status
done 2026-10-18 — wording fixed; sweep clean
