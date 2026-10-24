# UNEUTRAL7 — finish the neutralisation of the four same-class tokens

## Purpose
UNEUTRAL6 neutralised ten system-specific tokens inside the reduced release package and proved no
diagnostic moved. It found four more tokens of the same class and left them. This unit sweeps the
**whole class**, neutralises everything safe in a working copy, and proves the consequences by running.

## Write paths
`strategy/STIMULUS_NEUTRALISATION.md` (append), `orchestration/units/UNEUTRAL7.md`,
`orchestration/handoffs/UNEUTRAL7.json`, `scratch/uneutral7/**`. Read anything else; edit nothing else.

## Source
`scratch/uneutral6/package/` → copied to `scratch/uneutral7/package/`. Work only on the copy.

## The four named
`test.run`, `memory.write`, `web.fetch`, `role.model`.

## Hard bound
20 tool calls. Small increments; never `cat` a large file.

## Method
1. Census + classify the whole class of runtime action / tool / capability / role / state tokens.
2. Neutralise with `NEUTRAL-TAG/v1`, family `NC01…` continuing U6 numbering; longest-first,
   case-sensitive; mapping never written or logged.
3. Prove by running in the copy: `verify/recompute-claims.py`, `second-labeller/parse_fixture.py`,
   `second-labeller/compare.py`; fixture-correctness digest before and after.
4. Regenerate `MANIFEST.json` with the package's own procedure; independent checker; idempotence diff.
5. Report (do not edit) paper/gate quote status.

## Log
- (in progress — skeleton first, work appended below)
