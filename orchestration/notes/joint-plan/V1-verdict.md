# V1 Independent Verification Verdict

**Unit:** V1-VERIFY · **Date:** 2026-11-07 · **Target:** `experiments/ptr-engine/research-seed-concepts/JOINT-SERVING-CONTEXT-PLAN.md` · **Overall:** `partial`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Per-arm-per-replicate `420` | PASS | Independent derivation: `6×10 + 6×30 + 3×60 = 60 + 180 + 180 = 420`. Document §7.1 matches (`6×10 + 6×30 + 3×60 = 420`). |
| 2 | `3 × (4 × 420 + 2 × 420) = 7,560`; no false coverage claim | PASS | Recomputes to `3 × (1,680 + 840) = 3 × 2,520 = 7,560`. Document states 7,560 excludes B digests/D checkpoints (§7.1) and keeps C0F (L5) and serving variants (L12/L13) separate. |
| 3 | All arithmetic lines | **FAIL** | Two mismatches: (a) L14 formula `1 × 7,560 (D arm only: 840 × 3 = 2,520)` evaluates to `7,560`, not the stated `2,520` (correct: `840 × 3 = 2,520`). (b) §7.4 sum of priced lines is `13,020.2`, not `12,820.2`: `0+9+36+185+7,560+1,260+225+378+151.2+2,520+696 = 13,020.2`. |
| 4 | Price-status audit | **FAIL** | L1, L2, L3 are labelled `priced` but their stack is historical SGLang, which the serving inventory proves is not launchable today (no SGLang process/listener/container). They should be `unpriced-unavailable`, not `priced`. |
| 5 | Lower-bound total not precise | PASS | §7.4 explicitly calls the sum a lower bound, names all unpriced-unavailable (L6, L7, L12, L13, L19) and unpriced-unbounded (L15, L16, L17) lines, and states no precise total. |
| 6 | Result-row schema | PASS | §9.1 carries all three dimensions, per-run/per-task identifiers, a quality outcome, and null-capable cache fields; §9.2 retains invalid/missing rows with exclusion reasons and retains all rows. |
| 7 | Live-state fidelity | PASS (minor unit note) | Live `ps`/`ss`/`rocm-smi` match §2/§3.1: only PID 9738 `python -u /app/server.py` on 127.0.0.1:8088; no SGLang/vLLM; no listener on 8012/8014/8017. O1–O4 all marked HISTORICAL/UNAVAILABLE; no claim this machine runs a generative arm today. Minor: “free ~6.13 GiB” should be ~5.71 GiB (`6,130,159,616 B`); the tenant-removed figure `7,674,114,048 B` (~7.15 GiB) is correct. |
| 8 | Restore/isolation | PASS | §3.4/§4 name exclusive-session isolation, the full fingerprint set, the pre-sweep snapshot, and mark restore UNVERIFIED/undocumented rather than assuming rollback. |
| 9 | Ledger | PASS | §8 keeps spent/reserved/unknown/available as four separate lines; 1,729 is not claimed spendable; available is `UNKNOWN`; no precise funding total over unknowns. Ledger SHA `8ebf4ed5…` unchanged. |
| 10 | Non-perturbation | PASS | Deliverable is the only new file under `experiments/`/`docs/`; ledger/reservation SHAs unchanged; no service restart or fixture/grader write recorded; server uptime unaffected. |
| 11 | Red→green guard | PASS | Copied document to `/tmp`, changed L4 formula `3*(4*420+2*420)` → `2*(4*420+2*420)`; recomputation gave `5,040` vs stated `7,560` (delta `2,520`) and was caught; original restored. |

## Defects (exact locations and corrected values)

1. `§7.2` / `§7.3` (L14): formula `1 × 7,560 (D arm only: 840 × 3 = 2,520)` is internally inconsistent. Correct formula/count: `840 × 3 = 2,520` requests.
2. `§7.4` first bullet: sum of priced lines is `13,020.2`, not `12,820.2`. Correct lower bound over priced lines: `≈13,020` requests.
3. `§7.2` / `§7.3` (L1, L2, L3): `price status` should be `unpriced-unavailable` because the SGLang historical stack is not launchable today; not `priced`.
4. `§2` table: “free ~6.13 GiB” is a unit error. Correct: free VRAM is `6,130,159,616 B` ≈ `5.71 GiB` (6.13 GB). The tenant-removed figure `7,674,114,048 B` ≈ `7.15 GiB` is correct.

## Red→green guard detail

- Perturbed line: L4 formula `3*(4*420+2*420)` → `2*(4*420+2*420)` in `/tmp/JOINT-PLAN-PERTURBED.md`.
- Recomputed: `2 × (4 × 420 + 2 × 420) = 5,040`; stated requests remained `7,560`; delta `2,520`.
- Result: mismatch detected on L4. Original file restored; perturbed copy no longer differs.

## Conclusion

`partial`: checks 1, 2, 5, 6, 7, 8, 9, 10, 11 pass; checks 3 and 4 fail on the four defects above. No historical-as-current claim and no precise total over unknowns were found.
