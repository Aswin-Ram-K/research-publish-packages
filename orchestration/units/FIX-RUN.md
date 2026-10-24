# FIX-RUN — RUN.json pins one handoff's digest beside another handoff's name, and no guard re-hashes them

**Trigger:** task board card, tag `automated` (no human answerer present). Handoff stub written before
the first read, per the tag prefix.

**Bound:** 1 pass over the named artefact chain, ≤3 red→green cycles. **Console came back** in this
session after the second red→green planting, so edits were staged afterwards and verification is owed
to the next unit (see "Where this unit stopped").

**Declared write paths:**

- `scratch/fixrun/check_digest_pins.py` (new guard — the only new executable)
- `scratch/fixrun/apply_edits.py` (staged, NOT yet applied)
- `scratch/fixrun/.tmp/` (selftest plantings, deleted afterwards)
- `orchestration/units/FIX-RUN.md`, `orchestration/handoffs/FIX-RUN.json`

No overlap: the only concurrent neighbour is a custody-scan unit, which is read-only.

## What is actually wrong (measured, not assumed)

The defect is in the **shipped second-labeller record**, `scratch/uneutral10/package/second-labeller/RUN.json`
(`G46/RUN.json`, 160 lines, sha256 `0737ac8891c754de9b648dc2ff3de75773fd4e4549748b9c9f27a36991e62355`,
13,064 B — all three re-measured from bytes).

1. **`:12` `_sha256_labels` names the wrong file as its own source and carries three wrong digests.**
   It says the pinned values come from `papers/encoder-crossover-190/CLAIMS.md:39` and
   `MANIFEST.json files[].source_sha256` — but `MANIFEST.json` lists no `files[].source_sha256` equal
   to `076164ac…b4796` (it appears only as the *entry* `sha256` of `fixture/reflex-decisions.ts`, whose
   own source digest is the branch-identity `a6536c04…` set). The record's real source is
   `repro/encoder-crossover-190/second-labeller/RUN.json` (sha256 `32da4d51…edb3`). It also quotes the
   shipped instrument as `369159b0…f78d / 81284 B` without pointing at `MANIFEST.json`, and gives the
   read-only target's absolute path and an unstated 145,031 B.
2. **`:13` `_sha256_labels_note`** corrects only the instrument digest/size, never the fabricated
   source sentence, and it too carries the target's local absolute path.
3. **`:7` `_fixture_path_in_target`: `"P05"`** is a renamed identifier standing where the (already
   neutralised) absolute target path was — the file it names cannot be resolved from the record.
4. **The one thing the record needs a label for is missing.** The record contains the shipped
   `fixture/reflex-decisions.ts` (81,439 B, `89e77a8e…e169`) and pins `076164ac…b4796` to that *name*.
   Digest-pinning a copy whose bytes differ is exactly what a reviewer calls a swapped hash — and no
   live label in the record says *why*. The reason exists: `MANIFEST.json`
   `files[fixture/reflex-decisions.ts]` gives `source_sha256` = `076164ac…b4796` against its own
   `sha256` = `89e77a8e…e169` with `identical_to_source: false`. Nothing shipped explains that pair.
5. **No guard anywhere re-hashes a pinned digest against the file its name names.** Measured:
   `tools/package/check_manifest.py` re-hashes every MANIFEST entry; `tools/package/gate.sh` counts
   vocabulary only (**and now reports exit 0 with `FATAL: cannot read vocabulary file` — a
   fail-closed regression, see Open**); `verify/recompute-claims.py` recomputes **numbers**, never a
   pinned digest; `UBUILD1.build.sh` runs only `gate.sh`. `papers/encoder-crossover-190/EVIDENCE_NOTES.md:278-279`
   prints the pinned keys without hashing anything.
6. **Late finding, not fixed here — the lone ambiguous key.** `MANIFEST.json` lists
   `second-labeller/RUN.json` with `source: "G46/RUN.json"` (a renamed identifier) and
   `source_sha256: e68b4f9e…5a4b` — a digest that **no file in the payload re-hashes to**. The workspace
   copy `repro/encoder-crossover-190/second-labeller/RUN.json` is `32da4d518c…`, not `e68b4f9e…`. So the
   record does not round-trip to its declared source; either the source moved or `e68b4f9e…` was never
   its digest. Recorded rather than guessed.

## What was changed

Nothing yet. `scratch/fixrun/check_digest_pins.py` is written and runs (see its docstring for the four
checks: unfolded-spelling detection, re-hash of the pinned digest, live-label requirement, payload-wide
"exactly one file re-hashes to the instrument digest" summary). `scratch/fixrun/apply_edits.py` stages
the RUN.json surgery and is **not applied**.

## Where this unit stopped

The session's Bash channel failed ("UNKNOWN: unknown error, write") on the run *after* the second
red→green planting, so the remaining work — apply, verify, red→green transcript, and folding the guard
into the build/test path — is handed to the next unit with the exact commands below. **No claim in this
card is a verified green claim.**

## Open

- **`gate.sh` fail-closed regression.** `bash tools/package/gate.sh --package scratch/uneutral10/package`
  printed `FATAL: cannot read vocabulary file: …/package/vocabulary/english.txt` but the shell observed
  **exit 0**; `tests/test_package_tools.py::test_gate_fails_closed_on_missing_or_empty_vocabulary`
  expects exit 2. Re-measure with `${PIPESTATUS[0]}` almost certainly shows the 0 was the pipe's, not the
  gate's — but it must be measured, not assumed.
- **`repro/encoder-crossover-190**` is an unfolded name that does **not** fold: neither
  `repro/` → `code/` nor `encoder-crossover-190` → `G46` reaches "repro/encoder-crossover-190", so the
  folded form of every reference to that tree is a name no folder carries. Found by the guard's own
  third planting; folding that reference is a decision, not a mechanical rename.
- The `e68b4f9e…5a4b` source digest of item 6 above.
