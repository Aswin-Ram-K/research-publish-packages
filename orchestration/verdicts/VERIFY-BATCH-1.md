# VERIFY-BATCH-1 — independent verification of four improvements

Verifier is not an author of any unit. **Zero inference requests**; nothing touched 192.168.2.168.
Every number below was recomputed by me; red→green ran in a throwaway full-tree copy
(`.verify-tmp/rev/experiments/ptr-engine`, removed after the run), never in place.

All four handoffs existed at start: HARNESS-GUARDS (4260 B), CHECKPOINT-COVERAGE (5278 B),
MATRIX-HONESTY (3574 B), HANDOFF-LINT (2959 B).

---

## 1. HARNESS-GUARDS — **pass**

**Claim.** Four run guards; `test_guards.py` 6/6 green; default `max_tokens` finite; wall cap aborts a
runaway turn; `--runaway-turns` exits 6 after partial rows; the projection refuses exit 8 before the
runner is entered.

**My re-run.** `python3 experiments/ptr-engine/longrun/tests/test_guards.py` → `6/6 GREEN`, exit 0.

**Payload capture (not a grep).** Injected transport into `client.send_chat` and read the outgoing body:
`max_tokens = 4096` on the wire, `returned max_tokens = 4096`. The suite's own fake HTTP server asserts
`last_body["max_tokens"] == 4096` on a real socket.

**Red→green (throwaway copy, full tree so all six cases are green at baseline).**

| revert | result |
|---|---|
| R1 `"max_tokens": cap` removed from `request_body` | **(a) RED**, (c) RED |
| R2 wall-cap check disabled in `client.collect_stream` | **(b) RED** |
| R3 `DEFAULT_THINKING = "auto"` | **(e) RED** |
| restored baseline | **6/6 GREEN, exit 0** |

**(d) red half, checked by hand.** My own fake runner + marker: cell exit **8**,
`projected_wall=8640s cap=3600s`, **marker absent**, out-dir empty → the runner was never entered.
With `--max-wall 0` the marker **is** written (exit 5) → the projection is load-bearing.

**Evidence rows not deleted.** `measure/rows-cell-pointer-stable-20261026T145758Z.jsonl`: 6 rows,
sha256 `5ac9dd992f5d8715696925f56c225024e172cb98b4b9a937a0ee63bd099e9800`, mtime **10:17** (before the
10:24 handoff). Turn 5 still carries `truncated=True`, `completion_tokens=16384`, `wall_ms=475873`.

**Attack A (slow stream).** 1 token / 100 ms, never stopping, cap 2.0 s → aborted at **wall 2.002 s**,
overshoot 0.002 s, 19 tokens emitted. **The cap does abort a slow-but-emitting stream.**
Limit found: the cap fires *when a chunk arrives* (`client.py:389`), so a stream that emits **nothing**
is not bounded by `--turn-wall-cap` at all — my silent generator with a 1.0 s cap aborted only at
**3.00 s**, when its next chunk arrived. With no chunk it is bounded only by `--timeout`. The handoff's
`assumptions` say exactly this, so it is a documented limit rather than a hidden one.

**Attack B (4095 tokens, normal stop).** `4095 deltas + finish=stop`, no usage chunk → `finish_reason=stop`,
`truncated=False`, cap did not trip. **PASS.**
Hole at the boundary: **4096** deltas, no usage chunk, no `finish_reason` → `truncated=False`
(`completion` is `None`, so the `completion is not None` clause never fires). Reported, not fixed.

## 2. CHECKPOINT-COVERAGE — **pass** (two coverage gaps)

**Claim.** 12/12 checkpoints decidable, all ≤40 tokens, none colliding; `LR-01.v5.json` unchanged;
+108 requests v5→v6.

**Independent AST derivation** (my own script; the author's tool was not imported for this step):
NUM `64, 6, 31, 5, 2`; CALL 4 (`ledger.record_resolution(scope=scope.name, …)`, `scope.block()`,
`ledger.resolved_count()`, `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)`);
NONE 3. **12/12 truths match**, every truth line inside its declared range, kinds NUM 5 / CALL 4 / NONE 3,
cl100k answer tokens max **29** (cp.3.t06) — all ≤40.

**Tool re-run.** `fixture_coverage.py --fixture .../LR-01.v6.json` → exit 0
`PASS: 12/12 checkpoints decidable, none colliding, all <= 40 tokens`. `pytest test_fixture_coverage.py` → 8 passed.

**v5 untouched.** sha256 `967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567`, 42183 B,
mtime 09:35:15 (predates the unit). Matches the claimed digest.

**Cost arithmetic.** v5 = 3 × 4 × 3 = 36; v6 = 12 × 4 × 3 = 144; Δ = +108 = 9 × 4 × 3. ✓

**Author mutants.** All three reproduce: range shift → exit 1 `truth at [163] falls outside … #L36-L110`;
duplicate truth → exit 1 (both ids reported); `kind TEXT` → exit 1.

**Attack C (shift one checkpoint's pinned range by one line).** cp.0.t12 `source` `#L39` → `#L40`
(truth `64` is at L39) → `cp.0.t12: truth at [39] falls outside the declared pinned range #L40`,
**answerable NO, exit 1**. **PASS.**

**Attacks the author did not write — both succeed against the tool:**

1. `answerable_from_pinned_range` is evaluated against the **per-item `source` pointer only**, never
   against `sources[].pointer` (the pinned working set the model is actually shown). Moving
   resolve.py's working-set pin from `#L36-L166` to `#L100-L166` leaves cp.0.t12 (truth at L39) reported
   **YES** with **exit 0** — a truth that is no longer in what the agent can read still passes the gate.
2. `answer_spec.kind` is never cross-checked against `derive.rule`: cp.3.t06 declared `kind NUM` over a
   `call_inside_function` derive → **PASS, exit 0**, though no NUM answer can ever match that truth.
3. A `derive.file` naming a missing module exits 1, but via an **uncaught `FileNotFoundError` traceback**
   and a doubled path (`.../ptr-engine/experiments/ptr-engine/...`) — fails safe, but not as a finding.

## 3. MATRIX-HONESTY — **pass** (declared space cannot detect extraneous cells)

**Claim.** 23 run/arm pairs × 4 checkpoint ids × 1 rep = 92; pass 5, fail 38, missing 36, undecidable 13;
overall 5/43; corrected `0/3`/`1/3` lines.

**Independent derivation from fixtures + row files.** Fixture declares `cp.0.t12, cp.1.t24, cp.2.t46,
repair.t30`. Nine `rows-longrun-*.jsonl` files carry `task_id LR-01`, 4 arms, rep always 1 →
**23 run/arm pairs × 4 × 1 = 92**. ✓

**Recomputed states.** 5 pass / 38 fail / 29 missing_turn_absent / 7 missing_answer_empty /
0 missing_row_absent / 0 missing_checkpoint_absent / 13 undecidable = 92; overall **5/43**. ✓
`pytest test_matrix_audit.py` → 11 passed.

**Corrected headlines, recomputed from the `cells` array.** config-C: lease-reopen `0/3`,
**pointer-stable `1/3`**, transcript-compact `0/3`, transcript-grow `0/3`; V6 pointer-stable **`2/3`**;
v4 pointer-stable **`1/3`**. All match `docs/MATRIX-COVERAGE.md:84-87,103`.

**mtime sweep.** No `rows-longrun-*.jsonl` (latest 08:23) and no `*.grade-v4.json` (08:36) was touched.
`measure/MATRIX-COVERAGE.json` carries 10:32 **because my attack D run reopened it** through the tool's
default `--out`; I regenerated it with the author's exact command and the restored content reports
92 cells, 5/38/29/7/0/0/13, 5/43, `live_requests: 0` — identical to the handoff. Disclosure, not damage.

**Attack D (a cell no fixture declares).** Synthetic rows dir + arm `ghost-arm` + one row for an
undeclared checkpoint `cp.99.t99`:

```
declared cell space: 2 run/arm pairs x 4 checkpoint ids x 1 rep = 8 cells
ghost-arm                0     1      0      3      0      0      0      4
overall 0/1 … EXIT=0
```

The ghost arm is **silently absorbed as declared and scored**; the undeclared checkpoint row is
**silently dropped**. Neither is reported. Cause: `matrix_audit.py:122`
`arms = sorted({r.get("arm") for r in rows if r.get("arm")})` — the space is defined by the rows, so it
structurally cannot tell a legitimate arm from a fabricated one. **Overstated**: the audit is a
classification of whatever rows exist, not an inventory that can detect an extraneous cell.

## 4. HANDOFF-LINT — **pass**

**Claim.** 946 handoffs scanned, shape split unit=778/verifier=168, code counts, 40/759 substantiation gap,
13/13 tests, every code red→green.

**Re-run.** `pytest test_handoff_lint.py` → **13 passed**.
Corpus audit reproduces **every** code count: E_MISSING_KEY 34, E_ARTIFACT_ABSENT 75, E_STUB 16,
E_DONE_NO_EVIDENCE 4, E_DONE_NO_ARTIFACTS 3, W_NO_COMMANDS 182, W_VERSION_STALE 21, done/pass with
missing artifacts **40**, unit=786 / verifier=168 / neither=0.

**Scanned count.** My run: `files scanned: 954` and `ls orchestration/handoffs/*.json | wc -l` = **954**
at the same moment. The author's 946 was the live count at their run: **15** handoffs arrived after
10:24:30 from concurrent units (960 by my byte snapshot). So *not reproduced* as 946 — drift, explained.

**Byte-integrity.** sha256 + size + mtime of all 960 handoffs before and after a lint run:
**0 changed**.

**Attack E (done handoff whose artifacts exist but are 0 bytes).**
`E_ARTIFACT_ABSENT: EMPTY.json` + `E_DONE_NO_ARTIFACTS: done with 1 artifacts, 0 exist`, **exit 1**.
It does **not** pass — the existence check is content-blind but not size-blind. So the
"existence ≠ correctness" limitation is **narrower** than hypothesised: empty files are caught, the
*content* of a non-empty file is still unchecked. Note the diagnostic mislabels an existing empty file
as "absent".

**Also caught:** `artifacts` pointing at a **directory** → `E_ARTIFACT_ABSENT` (refused);
verifier-shaped handoff without `checks` → `E_MISSING_KEY: verifier shape requires 'checks'`
+ `E_DONE_NO_EVIDENCE`. Both exit 1.

---

## Verdict table

| unit | verdict | attacks | defects found (not fixed) |
|---|---|---|---|
| HARNESS-GUARDS | pass | A pass (slow stream aborts; silent stream bound only by `--timeout`) · B pass, boundary hole at 4096-with-no-usage | `truncated` needs a usage chunk |
| CHECKPOINT-COVERAGE | pass | C pass (item pointer) · C3 **not caught** (working-set pin) | `sources[]` pin unvalidated; kind/rule mismatch passes; missing-file = traceback |
| MATRIX-HONESTY | pass | D **not caught** (ghost arm silently declared) | no extraneous-cell concept |
| HANDOFF-LINT | pass | E **caught** (0-byte refused) | empty file mislabelled "absent" |

**The single thing a reader should not trust from this batch:** the MATRIX-HONESTY "92 declared cells".
That number is a census of the rows on disk, not an independent declaration — it cannot certify that a
cell *should* exist, and a fabricated arm passes as declared.
