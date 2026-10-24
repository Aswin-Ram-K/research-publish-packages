# READER-MAP.md — claim-to-recompute map

One row per claim in `CLAIMS.md` — **every claim, each exactly once**. Columns: **Claim** |
**Recompute function** | **Source cell** | **Config id**.

- A bare name (`c17`, `grid_guard`) is a function or dispatch key in
  `papers/context-cache/recompute.py`. `grid_guard` is C61's own check; it also runs
  automatically after any grid claim.
- A path ending in `.py` is an external verifier script, run directly.
- **Config id** names the `config_id` field inside that cell's rows (`S0`, `S1`, `V1`, …), or
  `n/a` when the claim is not stratified by stack configuration.

Enforced by `papers/context-cache/verify_package.py`; re-run it after any edit here.

| Claim | Recompute function | Source cell | Config id |
|---|---|---|---|
| C01 | experiments/context-cache/cells/CX-V2/u5_recon.py | experiments/context-cache/cells/U5 | n/a (external replay) |
| C02 | c02 | experiments/context-cache/cells/U5 | n/a |
| C03 | c03 | experiments/context-cache/cells/U5 | n/a |
| C04 | c04 | experiments/context-cache/cells/U4b | n/a |
| C05 | c05 | experiments/context-cache/cells/U4b | n/a |
| C06 | c06 | experiments/context-cache/cells/U4b | n/a |
| C07 | c07 | experiments/context-cache/cells/U5 | n/a |
| C08 | c08 | experiments/context-cache/cells/U5 | n/a |
| C09 | c09 | experiments/context-cache/cells/U5 | n/a |
| C10 | c10 | experiments/context-cache/cells/U5 | n/a |
| C11 | c11 | experiments/context-cache/cells/U4 | n/a |
| C12 | c12 | experiments/context-cache/cells/U4 | n/a |
| C13 | c13 | experiments/context-cache/cells/U4 | n/a (static) |
| C14 | c14 | experiments/context-cache/cells/U4 | n/a |
| C15 | c15 | experiments/context-cache/cells/U13 | n/a |
| C16 | experiments/context-cache/cells/CX-V2/u4_recon.py | experiments/context-cache/cells/U4 | n/a (external replay) |
| C17 | c17 | experiments/context-cache/cells/U15 | n/a |
| C18 | c18 | experiments/context-cache/cells/U15 | n/a |
| C19 | c19 | experiments/context-cache/cells/U15 | n/a |
| C20 | c20 | experiments/context-cache/cells/U15 | n/a |
| C21 | c21 | experiments/context-cache/cells/U15 | n/a |
| C22 | c22 | experiments/context-cache/cells/U15 | n/a |
| C23 | c23 | experiments/context-cache/cells/U15 | n/a |
| C24 | c24 | experiments/context-cache/cells/U15 | n/a |
| C25 | c25 | experiments/context-cache/cells/U15 | n/a |
| C26 | c26 | experiments/context-cache/cells/U15 | n/a |
| C27 | c27 | experiments/context-cache/cells/U9 | n/a |
| C28 | c28 | experiments/context-cache/cells/U9 | n/a |
| C29 | c29 | experiments/context-cache/cells/U9 | n/a |
| C30 | c30 | experiments/context-cache/cells/U9 | n/a |
| C31 | c31 | experiments/context-cache/cells/U9 | n/a |
| C32 | c32 | experiments/context-cache/cells/U9 | n/a |
| C33 | c33 | experiments/context-cache/cells/U9 | n/a |
| C34 | c34 | experiments/context-cache/cells/U9 | n/a |
| C35 | c35 | experiments/context-cache/cells/U9 | n/a |
| C36 | c36 | experiments/context-cache/cells/U9 | n/a |
| C37 | c37 | experiments/context-cache/cells/U2 | n/a |
| C38 | c38 | experiments/context-cache/cells/U4 | n/a |
| C39 | c39 | experiments/context-cache/cells/U2, experiments/context-cache/cells/U4 | n/a |
| C40 | c40 | experiments/context-cache/cells/U10 | n/a |
| C41 | c41 | experiments/context-cache/cells/U10 | n/a |
| C42 | c42 | experiments/context-cache/cells/U10 | n/a |
| C43 | c43 | experiments/context-cache/cells/U10 | n/a |
| C44 | c44 | experiments/context-cache/cells/G1 | n/a |
| C45 | c45 | experiments/context-cache/cells/WIN-SGL | S1, S2 |
| C46 | c46 | experiments/context-cache/cells/WIN-SGL | S1, S2 |
| C47 | c47 | experiments/context-cache/cells/G3 | S0 |
| C48 | c48 | experiments/context-cache/cells/WIN-VLLM | V1, V2, V3 |
| C49 | c49 | experiments/context-cache/cells/WIN-VLLM | V1, V2, V3 |
| C50 | c50 | experiments/context-cache/cells/WIN-VLLM | V1, V2 |
| C51 | c51 | experiments/context-cache/cells/G3, experiments/context-cache/cells/WIN-VLLM | S0, V1 |
| C52 | c52 | experiments/context-cache/cells/TUNED | TUNED |
| C53 | c53 | experiments/context-cache/cells/G5 | n/a |
| C54 | c54 | experiments/context-cache/cells/M4 | n/a |
| C55 | c55 | experiments/context-cache/cells/G3, experiments/context-cache/cells/WIN-SGL, experiments/context-cache/cells/WIN-VLLM, experiments/context-cache/cells/TUNED | S0, S1, S2, V1, V2, V3, TUNED |
| C56 | c56 | experiments/context-cache/cells/WIN-VLLM | V1, V2, V3 |
| C57 | c57 | experiments/context-cache/cells/G3, experiments/context-cache/cells/WIN-SGL | S0, S1, S2 |
| C58 | c58 | experiments/context-cache/cells/WIN-SGL | S1, S2 |
| C59 | c59 | experiments/context-cache/cells/TUNED | TUNED |
| C60 | c60 | experiments/context-cache/cells/TUNED, experiments/context-cache/cells/G3, experiments/context-cache/cells/WIN-VLLM | TUNED, S0, V1 |
| C61 | grid_guard | experiments/context-cache/cells/G3, experiments/context-cache/cells/WIN-SGL, experiments/context-cache/cells/WIN-VLLM, experiments/context-cache/cells/TUNED | S0, S1, S2, V1, V2, V3, TUNED |
| C62 | c62 | experiments/context-cache/cells/G3-LIMIT-V2 | n/a |
| C63 | c63 | experiments/context-cache/cells/MOE-VLLM, experiments/context-cache/cells/G3, experiments/context-cache/cells/WIN-VLLM, experiments/context-cache/cells/DENSE-SGL | V3, S0, V1, P1 |
