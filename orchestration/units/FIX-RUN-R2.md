# FIX-RUN-R2 — resolve `RUN.json`'s mis-pinned digest (fresh unit)

**Trigger:** task board card tagged `automated` — no human present, no questions asked.

**Bound:** ≤40 tool calls, ≤3 red→green cycles. **Used: 34.**

**Declared write paths** (no clash: the only concurrent neighbour is a read-only custody scan):

- `papers/context-cache/RUN.json` (the record being repaired)
- `tests/test_run_record_digests.py` (new guard, so the "new guard" survives CI)
- `scratch/fixrunr2/**` (snapshots, canary, captured command output)
- `orchestration/units/FIX-RUN-R2.md`, `orchestration/handoffs/FIX-RUN-R2.json`

## The card's brief, and what it actually names

The card: *"resolve RUN.json's mis-pinned digest (fresh unit; the first attempt 'succeeded'
writing nothing)"*. Two predecessors were read rather than trusted:

- `orchestration/handoffs/FIX-RUN.json` — `partial`, 34 tool calls. It names the package record
  `scratch/uneutral10/package/second-labeller/RUN.json` (re-measured here: 160 lines, 13064 B,
  sha256 `0737ac8891c754de…`, byte-for-byte what its handoff claims) and three defects in
  `_sha256_labels` (`:12`), `_sha256_labels_note` (`:13`) and `_fixture_path_in_target`
  (`:7` = `"P05"`). All three are present exactly as described. That chain is **unfinished work,
  not a wrong measurement** — it was left untouched because the card's "mis-pinned digest" is,
  verbatim, V-FINAL3's item (a) below, and because editing a 29-file shipped package deserves
  its own card.
- `orchestration/handoffs/V-FINAL3.json` → `next_unit_hint`, the live repair list. Its item (a),
  labelled **"FIX-RUN"**, is a concrete, re-measurable defect:

  > `RUN.json:350` records `verifier_handoff_sha256_prefix` `2f17f26215d5fa77` for
  > `verifier_handoff` `orchestration/handoffs/CX-V2.json`, but `2f17f26215d5fa77` is
  > `sha256(V-FINAL.json)[:16]` and `0887c656baaa3748` is `sha256(CX-V2.json)[:16]`.

That sentence **is** "the mis-pinned digest" — a digest filed beside the name of a different
file. It was taken as the contract; the assumption is recorded in the handoff.

## What was wrong (measured)

1. **The named pin did not resolve.** `sha256(orchestration/handoffs/CX-V2.json)` =
   `0887c656baaa3748…`; the record pinned `2f17f26215d5fa77`, which is
   `sha256(orchestration/handoffs/V-FINAL.json)[:16]` — a file the record does not point at.
2. **Five more pins named no file at all**, so no re-hash was even possible: four in `pins`
   (`u4_sessions_payload_sha256`, `u5_cases_json_sha8`, `u5_render_py_sha8`, `u4_cell_py_sha256`)
   and one at `verification.synthesis_recompute.script_sha256`. A digest nobody can check is the
   same defect in a quieter form.
3. **Three of those five values do not resolve to what their names imply**, and fixing only the
   named one would have left them: `u4_sessions_payload_sha256` is the *content* digest recorded
   *inside* `u4_sessions.json:5`, not the file's digest; `u5_cases_json_sha8` was transcribed one
   digit short (`e8e3e981c22808e` vs the file's `e8e3e9819c22808e`); `script_sha256` carried
   `4845bd8d…`, the digest of a `recompute.py` that no longer exists (on disk: `85917e48…`).
4. **No guard re-hashed a pinned digest against the file its key names.** Grep for any of these
   pin keys across `papers/ tools/ tests/ src/ docs/ strategy/ experiments/*.py` returned no
   consumer: nothing read them, so nothing could be wrong about them.

## What was changed

`papers/context-cache/RUN.json`, exactly these:

| Site | Change |
|---|---|
| `verification.verifier_handoff_sha256_prefix` | `2f17f26215d5fa77` → `0887c656baaa3748`, plus `verifier_handoff_file` and `verifier_handoff_sha256_prefix_note` naming the superseded value and the file that value belonged to |
| `pins` | each pin now names its file (`*_file`); `u4_sessions_payload_sha256` 78b725cb… → 0ca987d9… with `_claimed` + `_repair`; `u5_cases_json_sha8` one digit corrected + `_repair`; `u5_render_py_sha8` named and marked history (`_repair`); `u4_cell_py_sha256` and the two `_after_u14` pins name their files (values unchanged, they already recomputed) |
| `verification.synthesis_recompute` | `script_sha256` 4845bd8d… → `85917e48…` with `_claimed` + `_repair`, and `tail` regenerated from a fresh `recompute.py all` run (exit 0) |
| `units[11]/units[12]/stacks[3].flags` | `config_file` added beside each `config_sha256` |

No claim was renumbered, no value about the paper's findings was touched, and the two
superseded values are kept on the record (in `_claimed` and in the repair sentence) rather than
overwritten — the repair records why a hash is not a lie, it does not delete the hash.

## The guard

`tests/test_run_record_digests.py` (new, 5 tests). It checks every `*_sha256*` key in the record:
shape → names a file → the pinned prefix occurs **inside a digest `sha256sum` prints** for that
file (not inside the concatenation of digest and filename, where a prefix straddling the two
would look found) → a `_repair` must be corroborated by `<key>_claimed` and the sentence must
state the same digest. `path#field` names a digest-valued field; a `*_files` list names several
files. 27 pins: **25 verified, 2 superseded-and-explained.**

## Evidence

```
RED    (historical value restored in the real record)
       E  verification.verifier_handoff_sha256_prefix: pinned 2f17f26215d5fa77 does not occur in
          sha256(orchestration/handoffs/CX-V2.json) = 0887c656baaa3748...
       FAIL: orchestration/handoffs/CX-V2.json sha256 0887c656baaa3748 but the record pins 2f17f26215d5fa77   [exit 1]
GREEN  5 passed in 0.04s;  canary: OK: ...CX-V2.json sha256 0887c656baaa3748 matches the pinned prefix
       cmp: byte-identical restore
```

## Where it stopped, and what it did not do

- **FIX-RUN's own three defects were not repaired.** The package record it names does not match
  its own measurements (see above), so repairing it from that handoff would mean encoding numbers
  that no longer describe the tree. `scratch/fixrun/check_digest_pins.py` was **not** adopted: it
  was written against the drifted payload and has never been green (its author's notes record 8
  findings on first run).
- **`u4_sessions_payload_sha256`'s old value is superseded, not explained.** `78b725cb…` is the
  payload digest carried inside `u4_sessions.json` and by U4's runlog/report; which other
  artefact it covers was not established.
- **`u5_render_py_sha8` cannot be confirmed** — it describes the pre-U14 renderer, which is not
  on disk. Recorded as history, not re-hashed.
