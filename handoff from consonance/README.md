# Handoff from Consonance — bounded context fabric, inference side

**From:** Duval/Consonance (workspace `30b03b80`, repo `/home/zer0null/Duval`, strand `land/rsi-round-1` @ `4a731e4`).
**To:** the research-extractor workspace (`/home/zer0null/reserach extarctor`, workspace `78cead56`).
**Date:** 2026-10-25. **Status:** staged package, not yet executed. Consonance runs **no** model hosting.

## Why this exists

The operator has drawn the line: **inference-side and eval-side experiments belong to the extractor; the
harness-side build belongs to Consonance.** The two halves only produce one result if their numbers can be
joined, so this package carries (a) the facts we already measured and will not measure again, (b) the
**interface contract** both sides must emit, (c) the inference-side experiments with pre-registrations
written *before* any run, and (d) the traps that cost us time.

## What to read, in order

| File | Why |
|---|---|
| `INTERFACE_CONTRACT.md` | the only thing that makes our quality numbers and your cache numbers comparable. Read first. |
| `MEASURED_FACTS.md` | what is already established here, with paths. Do not re-derive; extend or falsify. |
| `EXPERIMENTS.md` | six pre-registration skeletons, inference-side only, each with a falsifier and a budget. |
| `DO_NOT_REDO.md` | ten traps, each paid for once. |
| `handoff.json` | machine-readable index (`units[]`), so a unit card can be cut straight from it. |

## What Consonance will deliver, and when

Nothing in this package depends on our code landing. When our M1 lane lands it will ship, into this
directory's sibling area, the two artifacts that make the contract executable:

1. a **manifest schema** (`ContextManifest` v0) whose digest covers ordered modules, epoch, policy hash,
   renderer fingerprint, lease id, token count, output reserve, expansions, omissions, unknowns,
   watermarks;
2. a **replay fixture format** (task-replay JSON) with stable ids, accepted by our tests offline.

Until then, emit the contract fields from whatever harness you drive; the field names and the
absent-vs-zero rules are what matter.

## The one-line ask

E1 (`CACHE-BOUNDARY-SWEEP`) and E2 (`CHECKPOINT-COST`) decide whether our whole design has a premise.
If you can run only two things, run those two, in that order.

## Provenance and honesty

Every number in `MEASURED_FACTS.md` is quoted from a document in the Consonance repository, and the
documents distinguish a **registered** measurement from **unregistered reconnaissance**. That distinction
is preserved here: three of the six rows are reconnaissance or voids, and are marked as such. Nothing in
this package is a claim of novelty or of a measured improvement.
