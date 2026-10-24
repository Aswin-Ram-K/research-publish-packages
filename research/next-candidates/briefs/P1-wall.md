# P1 — What to do at the wall: append-then-compact at a real 32k/64k limit

> **Prospective and unapproved.** Derived only from `research/next-candidates/2026-10-24-sweep.md`;
> it authorises no request, lock, restart or write. Every number is quoted from that memo.

## Objective

Turn C62's measured boundary cost into a policy paper — *what to do when the context wall arrives*:
does the hybrid beat summarise-in-place **after** the wall, does the trigger move only the boundary
turn, and does compacting to the baseline's resting window remove the flagship's §6a confound?

## Why now

- Hybrid is the paper's own recommendation and unrun (G14); MOE-VLLM H is append-only at 32k
  (284 rows), so no cell appends *and then* compacts.
- `experiments/context-cache/cells/G3-LIMIT-V2/` holds 2,780 rows / 18 compactions: baseline drops
  1,236–1,321, boundary turns 1,826–3,033, post-wall arm means +134.6 … +747.2 uncached tokens/turn,
  11/12 CIs excluding zero, per-turn range −927 … +5,473.
- §6a (arms rest on a shorter window) is the reviewer-facing weakness; the ~90-request
  resting-window arm is the named closure.

## Design / arms

`G3-LIMIT-V2` harness (`keep_last`/`keep_last_mode`/`trigger_reason` rows); **SGLang S0, no restart**.

| Arm | Policy | Wall | `keep_last` | Requests |
|---|---|---|---|---|
| H-32k | hybrid: append to the limit, then compact | 32k | default | 160 |
| H-64k | hybrid, longer wall | 64k | default | 190 |
| H-overrun-32k | hybrid, trigger past the edge | 32k | default | 160 |
| S-overrun-32k | summarise, trigger past the edge | 32k | default | 160 |
| S-baseline-window | summarise to baseline's resting window | 32k | ≈9,896 | 160 |
| R-rest | low-volume resting-window control | 32k | ≈9,896 | ~90 |

**Budget: ≈830 for the five arms + ~90 for R-rest = ≈920 requests**, one lock, no restart.

## Gates / controls

- **Pre-registered:** contrasts, arm order and the null band (C62's +134.6 … +747.2, per-turn
  −927 … +5,473) are fixed before launch; no post-hoc arm selection.
- **Triggers auditable:** every compaction row carries `trigger_reason`; an arm without it is
  invalid and is not patched by hand.
- **No restart; cold first; identity:** an arm needing a restart leaves the package; a cold pass
  precedes every repeated arm; arm identity distinct per group; `usage_has_details` true on every
  row; build pinned and recorded before the first arm; one lock and one restore proof.

## Kill condition

Stop the batch — not the paper — if a restart is needed, `trigger_reason` is absent,
`usage_has_details` is false, or arm identity is unrecoverable. If the batch completes with no arm
outside the C62 band, publish the null: the hybrid did not move the bill in this window.

## Deliverable

- `analysis.json` plus a short results note the paper's §6a/§6 can quote line-for-line.
- A contracted-shape handoff naming artefacts and evidence commands.

## Proposed write paths (future unit)

- `experiments/context-cache/cells/WALL-32K/plan.md` — pre-registration, written before launch.
- `experiments/context-cache/cells/WALL-32K/rows*.jsonl` — new rows only; never rewrite C62 rows.
- `experiments/context-cache/cells/WALL-32K/analysis.json` — per-arm table and contrast CIs.
- `orchestration/units/WALL1.md` — the unit card; `orchestration/handoffs/WALL1.json` — the handoff.

## Open risks

- H is near-certain to win directionally; the paper rides on magnitude, and a small effect is weak.
- S and F already fail to separate at 64k, so H-64k may spend 190 requests on a flat contrast.
- Without R-rest the §6a objection survives; box time is shared with P2, so sequence the lock. No GX10
  access in the sweep, so request counts are the memo's, not a measured runtime.
