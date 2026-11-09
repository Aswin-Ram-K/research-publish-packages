# V-HANDOFF-SHAPE — independent verification of HANDOFF-SHAPE-CLASSIFY

**Purpose.** Judged, not repaired: does the classifier change really only remove a false positive, and does the guard still bite?
**Bound.** 22 tool calls (used 20). **Mode.** read-only over the card's artefacts; writes only to my three paths + transient `scratch/v-handoff-shape/` (removed).

## Checks run
1. Guard on the real tree: `PYTHONPATH=src pytest tests/test_orchestration_handoffs.py -q` → 13 passed, exit 0.
2. Diff vs HEAD `f17663d1` + sha256 of `tests/test_orchestration_handoffs.py` = `918f4af9…` == handoff `test_file_sha256.after`.
3. Red cases in one self-contained scratch invocation (per-call private `/tmp` is how the two stray fixtures happened to the author): a unit-complete V-named fixture passes (by design); a key-short one fails naming `['write_paths']`; verdict-shaped fixtures missing `checks` / `overall` fail naming each; classifier reverted to prefix-first → the 13 return.
4. Strays absent; `git status --porcelain -- state/logs` empty; both frozen baselines match their pins.
5. Residual: `checks` is in `contract_verifier`, yet a NEW doc carrying all 7 unit keys + `overall` and no `checks` passes silently (exit 0).

## Verdict: **fail**
Not because the fix is wrong — it correctly removes 11 false positives — but because it also removes a **real** required-key report for two verdict-role documents, and a fresh fixture proves the hole is open to new documents. `RECORD-REFRESH.json` was a true false positive; `VERDICT-DISPUTE.json` and `VERDICT-REFUSAL-SEMANTICS.json` were real `checks` gaps (content present under `evidence.commands`, so material loss is low).

## Owed follow-up (a card, not an edit)
Record the shape decision for the two ambiguous files; if verdict-role, add a pinned baseline entry naming them with `['checks']`; add a non-failing report listing docs carrying both `overall` and the full unit contract; record the ending sha of the test file.
