# V-SPCC-2C — re-derive the compiler invariants against the current code

**Question.** The compiler was verified once, on code that no measurement path used, and both
`ptr_engine/layers.py` and its wiring then changed (per-run L0 state on `CompactionState`,
`reset_prefix_state()`, `compile_prompt` owning the journal lifecycle, real `spcc` arm in
`arm_cd.py:SpccArmState` + `run_longrun.py`). Re-derive every invariant from the current bytes.

**Verdict.** The compiler invariants hold on the current code: 32/32 independent checks pass,
author suite 4/4. One literal claim in the assignment is false and one code header is stale;
neither breaks the arm. Nothing fixed (report-only unit).

Pinned file hashes (sha256):

| file | sha256 |
|---|---|
| `experiments/ptr-engine/ptr_engine/layers.py` | `13b608e5d036c6d27ee4aa5b6675f550f262830e1b1602218da73f6cb229e606` |
| `experiments/ptr-engine/longrun/arm_cd.py` | `9f214da44e8588182d8ec06aa8b384427934a9108734b56508a8d4d2d5407cd5` |
| `experiments/ptr-engine/longrun/run_longrun.py` | `419f46d68c2031228cc98514bf84e21b77d8f6ffb09ceccef06e02d13be0a878` |
| `experiments/ptr-engine/longrun/tests/test_spcc_arm.py` | `858c8521eb9e00a435f3777ec778ef935e9bb928819cfe7ab257c7e8406e8635` |

## Results per invariant

| # | Invariant | Result |
|---|---|---|
| 1 | determinism | PASS — `compile_prompt` twice on one state: 234-byte identical prompt, equal `prefix_sha256`; two independent `SpccArmState`s agree on turn 1 |
| 2 | drift, one L0 byte within a run | PASS — `PtrPrefixDrift` raised |
| 2b | two runs in one process (old module-global defect) | PASS ×3 — different `run_id`s + different L0: no raise; **same** `run_id` + separate state + different L0: no false drift; one state reused by a different `run_id` restarts the baseline instead of raising. `layers._L0_HASHES == {}` after all of it, i.e. the legacy map is dead state |
| 3 | fetch isolation, 24 turns / 3 fetches | PASS — 1 distinct `prefix_sha256` across turns 1–24; L3 grew on exactly turns `[5, 12, 19]`; `"FETCHED BODY"` appears in none of L0/L1/L2; journal exactly 23 lines, `compactions == 0` |
| 4 | compaction at turn 25 | PASS — turn 24: `compactions == 0`, `epoch == 0`; turn 25: `compactions == 1`, `epoch == 1`, `state.journal == []` (immediately after the compile; turn 26 legitimately holds `['T25|user|QUESTION (T25)']`); all 4 world-index lines retained (index 5 = 4 world + 1 summary); exactly one `[summary: 24 turns folded into epoch 1]`, appended last; no prompt ever rendered with `len(journal) >= COMPACT_EVERY` (max post-build journal 23) |
| 5 | prefix covers L0+L1, doc states why | PASS for `PROMPT-ENGINE-V1.md` + `compile_prompt` docstring; **stale module header** (see below) — `prefix_sha256 == sha256(L0+L1)` recomputed by hand, and `!= sha256(whole prompt)` |
| 6 | wiring | PASS substantively, **assignment wording false**: `mask_output` is *not* absent from `arm_cd.py` |
| 7 | 26-turn offline proof | PASS — 26 rows, real `layer_tokens` dict over `{L0..L4}` on every row, exactly one prefix break at turn 25, `epoch == 1` / `compactions == 1` from turn 25, `cached_tokens` `None` on all 26 rows |
| 8 | row stamping | PASS — T1 row `prefix_sha256` equals the compiler's own L0+L1 hash (`1f251bcc8a1f5ac5…`) and differs from both `sha256(whole prompt)` and `run_longrun.sha256_text(prompt)` |

## Findings that are not invariant failures

1. **`mask_output` is still present in `arm_cd.py`, but not on the spcc path.** Imported at
   `arm_cd.py:24`, called at `arm_cd.py:132` and `arm_cd.py:200`, both inside `class ArmCDState`
   (arms C and D). `SpccArmState` (`arm_cd.py:399-501`) contains zero occurrences, and
   `ptr_engine/layers.py` contains zero. The substantive claim ("the legacy masker does not render
   the spcc prompt; `compile_prompt` does") holds; the literal claim ("absent from both") does not.

2. **`ptr_engine/layers.py:1-5` module header contradicts the implementation.** It says
   *"byte-stable prefix (L0+L1+L2), an append-only journal (L2)"* — self-contradictory, since L2
   cannot be both inside the hashed prefix and append-only. The authoritative text agrees with the
   code: `compile_prompt`'s docstring (lines ~181-190) and `PROMPT-ENGINE-V1.md:48-56` both say the
   hash covers `L0+L1`, with the reason ("hashing the growing L2 would report a change on every
   append and could not distinguish a legitimate append from a destructive rewrite"). Doc = correct;
   module header = stale. Cosmetic, comment-only.

3. **`run_longrun.py` is being edited concurrently.** Between two greps minutes apart, the
   `tools_enabled(...)` line naming `arm_cd.ARM_SPCC` moved from 3446 to 3468 (≈22 lines inserted
   above it). All spcc-relevant lines were stable: 1399-1400 (`SpccArmState` construction), 1534
   (dispatch), 1546-1549 (stamping). The hashes above pin the exact bytes verified.

## Wiring evidence

```
arm_cd.py:24        mask_output, build_table, fetch, ...            # legacy masker, C/D only
arm_cd.py:132       _marker, entry = mask_output(                   # inside ArmCDState
arm_cd.py:200       marker, entry = mask_output(                    # inside ArmCDState
arm_cd.py:30    from ptr_engine.layers import (compile_prompt, CompactionState, format_journal_line, RETURN_SYMBOL,
arm_cd.py:37    ARM_SPCC = "spcc"
arm_cd.py:490       prompt = compile_prompt(self.run, self.state, epoch=self.state.epoch, journal=new_lines, work=l3)
run_longrun.py:1399-1400  self.spcc = arm_cd.SpccArmState(fixture=fixture) if arm in (arm_cd.ARM_SPCC, "spcc") else None
run_longrun.py:1534  if arm == arm_cd.ARM_SPCC:
run_longrun.py:1546  info["prefix_sha256"] = prompt.prefix_sha256
run_longrun.py:1547-1549  info["epoch"] = prompt.epoch; info["compactions"] = prompt.compactions; info["layer_tokens"] = dict(prompt.layer_tokens)
run_longrun.py:1502  info["prefix_sha256"] = sha256_text(prefix)     # pointer-stable arm, NOT spcc
```

`mask_output(` inside `SpccArmState` = 0; `mask_output` in `ptr_engine/layers.py` = 0.

## Verification commands

```
.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_spcc_arm.py -q   → 4 passed in 0.34s
.venv/bin/python experiments/ptr-engine/longrun/tests/_scratch_2c.py                  → TOTAL 32 checks, 0 FAIL
```

The scratch file was written inside the repo, run, and deleted (`ls` confirms absent). Zero live
model requests: the row path monkeypatches `run_longrun.send_chat` and replaces `socket.socket`
with a raiser.

## Blocker

None. Report-only; no fixes applied.
