# V3 Independent Verification Verdict

**Unit:** V3-VERIFY · **Date:** 2026-11-07 · **Target:** `experiments/ptr-engine/research-seed-concepts/JOINT-SERVING-CONTEXT-PLAN.md` · **Overall:** `pass`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Row integrity (§7.2 vs §7.3) | PASS | MD and JSON id sets identical (20 ids L0–L19), no duplicates; requests/status/lower/upper agree numerically. Cosmetic notation differs (× vs *, ≈ vs ~, `1*7560`→`1 × 7,560`); L17 bounds shown as `—` in MD vs `90/90` in JSON on an unbounded line — presentation only, not a field mismatch on a committed bound. |
| 2 | Core sum | PASS | Recomputed `L0 0 + L4 7,560 + L5 1,260 + L8 225 + L9 378 + L10 151.2 + L14 2,520 = 12,094.2` (JSON). Candidate addendum `L1 9 + L2 36 + L3 185 + L18 696 = 926`; `12,094.2 + 926 = 13,020.2`. Both match document §7.4. |
| 3 | Derivations | PASS | `420 = 6×10+6×30+3×60 = 420`; `3×(4×420+2×420)=7,560`; `4×7,560=30,240`; `3×420=1,260`; `840×3=2,520`; `225` cell-arms. All arithmetically correct in place (§7.1, §7.2). |
| 4 | No precise total | PASS | §7.4 states lower bound + named unpriced lines; `Executable today: 0 requests` present with L19 gating reason. No line presents a precise programme total or executable commitment. |
| 5 | Status discipline | PASS | Statuses only `priced`/`unpriced-unavailable`/`unpriced-unbounded`; L1–L3 and O1–O4 are `unpriced-unavailable` with reasons; every unpriced line carries a reason; `priced` vocabulary (request count bounded, dollars unknown) defined at top of §7.4. |
| 6 | VRAM | PASS | §2 and tail acceptance block both carry total `17,095,983,104`, used `10,965,823,488`, free `6,130,159,616 B ≈ 5.71 GiB`; `7,674,114,048 B (~7.15 GiB)` only as conditional upper bound. No `6.13 GiB` anywhere. Live `rocm-smi` confirms total 17095983104 / used 10965823488. |
| 7 | Live-state fidelity | PASS | Re-observed: only PID 9738 `python -u /app/server.py` on 127.0.0.1:8088; no SGLang/vLLM process; no listener on 8012/8014/8017; `nvidia-smi` failed (no NVIDIA GPU). O1–O4 all marked HISTORICAL/UNAVAILABLE; no claim this machine runs a generative arm today. |
| 8 | Isolation/restore | PASS | §3.4/§4 name exclusive-session isolation, full fingerprint set (model/tokenizer/renderer/engine), pre-sweep snapshot, and mark restore UNVERIFIED/undocumented. |
| 9 | Results schema | PASS | §9.1 row carries all three dimensions + per-run/task id + quality outcome + null-capable cache fields; §9.2 retains invalid/missing rows with exclusion reasons and retains all rows (not only Pareto winners). |
| 10 | Ledger | PASS | §8 keeps spent (2,591) / reserved (1,500) / unknown / available (UNKNOWN) as four distinct lines; 1,729 never claimed spendable; reconciliation step named (`tools/request_ledger.py`). Reservation CCS-2026-11-05 recorded fields verified against `RESERVATIONS.json`. |
| 11 | Non-perturbation | PASS | No completion requests, restarts, target-repo writes, fixture/grader edits. Ledger/reservation mtimes unchanged (2026-11-05); only new file under experiments/ is the plan (mtime 2026-11-07 16:21) plus this verdict/handoff; docs/ untouched by this task. Server uptime unaffected. |
| 12 | Red→green guard | PASS | Copied plan to `/tmp/JOINT-PLAN-PERTURBED.md`; changed L5 requests 1,260→1,000. Row-integrity check caught `L5 requests md=1000 json=1260 delta=260.0`; core-sum check caught `11834.2 vs 12094.2 delta=260.0`. Both detected the perturbation. Perturbed copy removed; original (with cosmetic fix) retained. |

## Corrections applied (narrow exception)

- **L6 markdown-table formula cell:** `1*7560` → `1 × 7,560` (cosmetic token only; value unchanged, 7,560). Recorded per the permitted narrow exception. JSON cell left as `1*7560` (no other document edits).

## Defects found

None. All twelve checks reproduce.

## Red→green guard detail

- Perturbed file: `/tmp/JOINT-PLAN-PERTURBED.md` (removed after test).
- Change: L5 `requests` 1,260 → 1,000.
- Row-integrity detected: `L5 requests: md=1000 json=1260 delta=260.0`.
- Core-sum detected: `core sum 11834.2 vs expected 12094.2 delta 260.0`.
- Original restored: perturbed copy removed.

## Conclusion

`pass`: all twelve checks reproduce. No historical-as-current claim, no precise total over unknowns, no unpriced line mislabelled `priced`. Cosmetic L6 token corrected and recorded.