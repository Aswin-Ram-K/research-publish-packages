# RUN-C-PLAN — config C, executable and pre-registered (204 requests)

**Status:** PRE-REGISTERED PLAN, **zero requests sent** (dry-run only). Owner unit `RUN-C-PLAN`. **Scope:** execute `DESIGN-V3.md` §3 config C exactly — cap `4096`, N=48, 4 arms, 1 rep, `--thinking off`
— against `occamy-1.0-NVFP4` on SGLang `:8012`, then score the rows. It does **not** re-derive the rule.

## 1. Exact commands (verbatim, in order)

```bash
# 1.1 target liveness (allowed single GET; not a completion)
curl -s -m 10 http://192.168.2.168:8012/v1/models | head -c 400

# 1.2 the cell — one process, four arms, run id longrun-c-2026-10-26
cd "/home/zer0null/reserach extarctor"
python3 experiments/ptr-engine/longrun/run_longrun.py \
  --fixture experiments/ptr-engine/longrun/runtime/LR-01.json \
  --arms transcript-grow,transcript-compact,pointer-stable,lease-reopen \
  --reps 1 --thinking off --max-tokens 4096 --max-turns 48 \
  --run-id longrun-c-2026-10-26 \
  --rows experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl \
  --base-url http://192.168.2.168:8012/v1 --model occamy-1.0-NVFP4 --engine sglang --stream

# 1.3 resume after a break (same run id; a failed row refuses resume by design)
python3 experiments/ptr-engine/longrun/run_longrun.py ... --run-id longrun-c-2026-10-26 --resume
```
Flags are real, taken from `run_longrun.py --help` (§9): `--fixture --arms --reps --thinking {auto,on,off}
--max-tokens --max-turns --run-id --rows --base-url --model --engine --stream --resume --dry-run`. Manifest per cell: `experiments/ptr-engine/longrun/manifests/<run_id>-<arm>-r1.json`. Fixture sha256 the rows and the scorecard must both carry: `b7e303a65f200e7b3dfd339cf3c6a1f3b4e684e57ca271e74f8f5539a348a500`.

## 2. Frozen decision rule — verbatim from `experiments/ptr-engine/LONGRUN-PREREG.md` §4

> **PASS** iff all three: (i) C p95 TTFT ≤ 0.5 × A's; (ii) C tokens-to-verified-success ≤ A's; (iii) C's mean
> checkpoint accuracy ≥ A's − 0.10. **If (i) or (ii) fails, the "use the space better" thesis fails on this
> hardware** — recorded as FAIL with the measured ratio, and **not** re-run at a different N to find a passing one.
> **Narrowing, not a pass:** if D beats C on p95 *and* ties its accuracy, the win belongs to **scoped reopening**,
> not to the frozen prefix; if B ties C's accuracy at fewer total tokens, the digest is sufficient and the pointer
> machinery is unjustified. Either outcome is reported as PARTIAL with the winner named.
> **Falsifier, in one line:** if `pointer-stable` is not faster at p95 and does not solve with fewer total tokens
> than `transcript-grow`, the thesis fails on this hardware and this file says so.

Not paraphrased, not relaxed, not re-weighted. Where C cannot evaluate a clause, §6 says so.

## 3. Pre-registered predictions P1–P4, unchanged

| # | prediction | falsified if |
|---|---|---|
| P1 | C's **p95 TTFT ≤ 0.5× A's** at N=60 | C/A ≥ 0.5, **or** C's cached share after turn 12 < 0.80 (its own tail rewrites dominate) |
| P2 | A's **tokens-to-verified-success ≥ 1.5× C's**, and the excess is **repair**, not per-turn cost | A's repair_turns ≤ C's, or A's non-repair per-turn uncached alone (within 1.2× of C's) explains the gap — then the win is cost after all and the demotion is wrong |
| P3 | D has the **lowest** p95 TTFT but **loses checkpoint accuracy at t30/t60** unless the ≤400-token state line carries both the turn-2 fact and the turn-24 correction | D ties C's accuracy — then the distilled line *is* sufficient and the frozen prefix buys nothing |
| P4 | B lands within 2× of C on p95 but **fails t30** where its digest dropped the turn-2 code | B ties C's accuracy at lower total tokens — then compaction, not pointers, is sufficient |

## 4. Stop conditions (numeric — all pre-committed, none negotiable mid-run)

1. **Stall:** any single turn > **600 s** → let it finish and log; a **second** turn > 600 s in the same cell
   → **stop the cell**, report the two turn numbers, do not resume past them. 2. **Thinking-policy rejection:** any arm where **>10 %** of its 48 turns end `finish_reason=length` **with empty
   `content`** → that arm's thinking policy is **REJECTED**, not tuned. Record the fraction; no re-run with
   `--thinking on` inside this run id. 3. **Digest/fixture mismatch:** fixture sha256 at run ≠ `b7e303a6…a500` → **abort** (runner already exits 3);
   a scorecard with `fixture_sha256_matched: false` / `tampered: true` **voids the row file**. 4. **Budget:** > 204 requests in this run id → the run is void; nothing extended, no arm borrows turns. 5. **Control red** (PREREG §7 controls, run first): any red control voids the batch — record, stop, do not score.

## 5. Scoring procedure

```bash
python3 experiments/ptr-engine/longrun/score_longrun.py \
  experiments/ptr-engine/longrun/runtime/LR-01.json \
  experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl \
  --out experiments/ptr-engine/measure/score-longrun-c-2026-10-26.json --pretty
```
One invocation **per arm** (the scorer reads one run log, so filter rows per arm first, or invoke once per arm).
Output: one JSON scorecard — `task_id, arm, rep, checks[], verified_success, tokens_to_verified_success, repair_turns, checkpoint_accuracy, constraint_violations, fixture_sha256_at_score, fixture_sha256_at_run, fixture_sha256_matched, tampered, unverifiable_required, failed_required, counts_by_kind, exit_code`; exit 0 = ok, non-zero = failed / tampered / input error. `checks_structured` (all `match: "exact"`) is the decidable quality leg: **runtime/LR-01.json carries 12 structured checks** (+4 advisory prose). The arithmetic, honestly: **55 is the pool across LR-01…06 (12+8+8+9+9+9)**; C runs LR-01 only, so this cell's quality verdict rests on **12** structured checks — 12/12 decidable, not 55.

## 6. What config C cannot settle (limitations, stated, not fixed)

- **No t60 checkpoint.** N=48 ends before PREREG §2's t60; C keeps t12, t24/t30, t46. P1's "at N=60" is
  evaluated **at turn 48** and P3's t60 leg is dropped — a limitation of C, not a rule change.
- **One rep → p95 is the 2nd/3rd worst of 48 samples per arm**, not 120. Rule (i) stays a ratio C/A but with a
  wide interval: **no significance claim**. (iii) uses mean accuracy over the executed checkpoints. C **cannot**
  supply a 2-rep p95 (that is 408 requests, outside the ceiling).
- Concurrency unmodelled (sequential driver), one engine, one model, exact-match scoring.

## 7. Budget arithmetic

- This cell: **204 = 192 (4 arms × 48 turns × 1 rep) + 2 (transcript-compact digests at the 65,536 wall) + 4
  (controls, PREREG §7) + 6 (repair reserve, band 24–27)**. Dry-run prints `would_send_total=192` because it
  models arm-turns only; the +2 are reserved by `expected_digests()` and the +4/+6 are host-side budgets, so
  **192 is the floor, 204 the ceiling**.
- Ceiling: **4,320 − 208 spent = 4,112 left**, of which config C consumes **204** → 3,908 remain after C
  (5 of 6 fixtures still unrun, t60 leg still unmeasured).

## 8. Validity block — rows that may NEVER be pooled

| key | rule |
|---|---|
| `thinking` | `off` rows pool only with `off`. `auto`/absent or `on` is a **different instrument**; pooling voids the comparison. |
| `max_tokens` | `4096` pools only with `4096`. A 16,384 row is a different latency distribution (450 s mean on runaway turns) — never in the same p95. |
| fixture `sha256` | only `b7e303a6…a500` (runtime/LR-01.json). Foreign fixture, `fixture_sha256_matched:false` or `tampered:true` → excluded. |
| `run_id`/`arm`/`rep` | p95 per arm over its own turns; never across arms or run ids unless the three keys above match. |

## 9. Runner capability check (measured, not guessed)

`--dry-run` with the §1.2 settings: exit **0**, `would_send_total=192` (48 per arm, `N=48 x reps=1`), four manifests written (`dryrun-LR-01-<arm>-r1.json`: `dry_run:true`, `renderer.thinking:"off"`, `max_tokens:4096`, `fixture.sha256:b7e303a6…`). No needed capability is missing (`MISSING: none`): `--arms`, `--reps`, `--max-turns`, `--max-tokens`, `--thinking`, `--run-id`, `--rows` all exist. Two caveats, not gaps: (a) `--dry-run` reports `digest_requests=0` on LR-01/N=48 (no digest turn reached offline) while the live loop reserves 2; (b) `--dry-run` counts `N` and **ignores** `--max-turns`, so its total is trustworthy only when `--max-turns >= N` — true here (48 = 48).
