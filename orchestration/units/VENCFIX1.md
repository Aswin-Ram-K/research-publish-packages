# VENCFIX1 — independent verifier: encoder-crossover-190 published archive leak fix

Card persisted before any work. Verifier only: repaired nothing, modified no artifact.

- Purpose: independently re-derive six claims about `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`.
- Write paths: `strategy/VERIFICATION_REPORT_ENCFIX.md`, `scratch/vencfix1/**`, `orchestration/units/VENCFIX1.md`, `orchestration/handoffs/VENCFIX1.json`.
- Bound: 20 tool calls (used 13 incl. this write).
- Read-only: all registered target repos — no git run against any of them; workspace git used only read-only flags on this workspace's own untracked paper file.
- Method: own extraction to `scratch/vencfix1/ext` and `scratch/vencfix1/base_ext`; own sha256sum/md5sum; own builds with `BUILD_WORK` redirected to `scratch/vencfix1/`; red→green on a *copy* of `build_archive.sh`.

Result: C1 PASS, C2 PASS, C3 PASS (one imprecise "fixture digest" wording), C4 PASS, C5 PASS (red exit 1 reproduced; advisory gate proven), C6 PARTIAL (":350" true; "no other line rewritten" unverifiable). Overall: pass.

Full evidence: `strategy/VERIFICATION_REPORT_ENCFIX.md`.
