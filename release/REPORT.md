# RELEASE REPORT — SANITISE-RELEASE, `release/v0.1`

**Unit:** SANITISE-RELEASE · **Run:** 2026-10-24 (autonomous) · **Status: `done`** — all 7 gates pass.

**Licensing position (binding operator ruling, 2026-10-24):** the Duval/Consonance repository
was **never public**, so no prior AGPL-3.0 grant ever existed. **PolyForm Noncommercial 1.0.0 is
the only grant.** The licensing execution order is approved. This release carries PolyForm NC
1.0.0 and nothing else; no AGPL text is shipped.

---

## 1. What was measured

| Measure | Value |
|---|---|
| Shipped files | **943** (942 hashed + `MANIFEST.json`) |
| Total shipped bytes | **61,028,602** (~62M on disk) |
| Files whose content was sanitised | **170** |
| Host/port replacements | **850** |
| Absolute-path replacements | **244** |
| Largest shipped file | 13 MB (`experiments/context-cache/cells/M4/corpus.jsonl`) — under the 25 MB cap |
| Files over 25 MB shipped | **0** |
| Test suite | **not run** (forbidden by the card) |
| Live `papers/context-cache/MANUSCRIPT.md` | **untouched** — only the copy under `release/` was sanitised |

---

## 2. Method — scripted, not hand-edited

Two Python passes, both run over the staged copy only:

1. `build_release_v01.py` — walked the include list, applied the permanent exclude rules, copied and
   sanitised every surviving file, wrote the licence bundle, `README.md`, `NOTICE`,
   `THIRD-PARTY-NOTICES.md`, and the first `MANIFEST.json`.
2. `pass2_paths.py` — gate 2 was **not** zero after pass 1 (68 residual lines: `.cache/huggingface`,
   `.local/share/<...>`, `r2/launch-*.sh`, and others the two literal rules did not cover). Pass 2
   broadened the path rule to *any* `/home/zer0null` token while keeping the rest of the path, which
   drove gate 2 to 0. It was a scripted re-rule, not a hand edit.

Sanitisation rules in force:

| Rule | Pattern | Replacement |
|---|---|---|
| Host 1 | `192.168.2.168` (any port suffix) | `serving-host` |
| Host 2 | `192.168.2.187` (any port suffix) | `serving-host` |
| Host 3 | `192.168.2.1` — **near-miss internal address** found in 3 files | `serving-host` |
| Host 4 | `192.168.0.0/16` — RFC1918 constant in `src/resextract/web/fetch.py` | `the private IPv4 range` |
| Path 1 | `/home/zer0null/reserach extarctor[/…]` | `<workspace>` |
| Path 2 | `/home/zer0null/Duval[/…]` | `<workspace>` |
| Path 3 | `/home/zer0null/models[/…]`, `/home/zer0null/r2[/…]` | `<workspace>` |
| Path 4 | any remaining `/home/zer0null` token | `<workspace>` |

Host rule 3–4 and the generic path rule were **deliberate over-application**: gate 1 is a raw
`grep -rE '192\.168\.'`, so leaving the near-miss or the CIDR constant in place would have failed
the gate, and an internal address is an internal address whether or not it is one of the two named.
The cost is three test files and one doc sentence with a `<placeholder>` where a literal used to be;
none of them is load-bearing (see assumptions A3).

> **Note on `NOTICE`:** the first generated `NOTICE` restated the two raw internal addresses in its
> own explanation of the redaction — it would have failed gate 1 by itself. It was rewritten to
> describe the redaction **without** reprinting the addresses. A "sanitised" tree that names what it
> sanitised is not sanitised.

---

## 3. INCLUDE list

| Source | Shipped as | Why |
|---|---|---|
| `src/` | `src/` | The extraction/comparison implementation — the study's code |
| `papers/` | `papers/` | Manuscript, figures, data for the context-cache and gated-read-batching papers |
| `tests/` | `tests/` | Test suite; the evidence that the shipped code behaves as claimed |
| `experiments/context-cache/` | `experiments/context-cache/` | Per-cell measurement outputs underpinning the paper's numbers |
| `repro/encoder-crossover-190-SANITISED/` | same | Self-contained reproduction package, **already sanitised upstream** (14 hits re-applied where the upstream scrub left residue) |
| `docs/` | `docs/` (curated — all 27 files kept) | Operations, acceptance protocol, serving options, prompt system, plan |
| `config/` | `config/` (**2 of 3 files**) | `graph_pin.toml`, `resextract.toml`; `targets.toml` withheld (see §4) |
| `pyproject.toml` | `pyproject.toml` | Package metadata and dependency pins |
| — | `LICENSE` | PolyForm NC 1.0.0 **verbatim from `Duval/LICENSE`** (see §6) |
| — | `COMMERCIAL.md`, `CONTRIBUTING.md` | From `strategy/licence-templates/RELEASED-PIECE/` |
| — | `README.md` | Case B paragraph copied verbatim from `README-PARAGRAPHS.md`, plus a start-here table |
| — | `NOTICE` | What changed on the way out, and why |
| — | `THIRD-PARTY-NOTICES.md` | Attribution for bundled LaTeX classes/styles |
| — | `MANIFEST.json` | sha256 for **every** shipped file + sanitisation record |

---

## 4. EXCLUDE list, with reasons

### 4.1 Permanent exclusions (card rule)

| Pattern | Reason | Applies where |
|---|---|---|
| `.git`, `.venv` | VCS state and the local virtualenv — not publishable content | all trees |
| `scratch/`, `state/`, `jobs/`, `archive/`, `journal/`, `dockets/` | Private working state, run outputs and the docketing system; out of scope for a public piece | all trees |
| `.pytest_cache`, `__pycache__` | Build/cache artefacts, not source | all trees |
| `*.lock` | Lock files — machine-specific, non-reproducible | `experiments/context-cache/.occamy.lock` (1 file) |
| any file > 25 MB | Publication size bound | 0 files fell in the *include* trees; the 13 MB `corpus.jsonl` is the largest kept |

### 4.2 Content exclusions found during curation

| File | Reason |
|---|---|
| `config/targets.toml` | **Internal target registry** — lists private target-repository paths and internal hostnames. Shipping it would republish the exact identifiers the sanitisation exists to remove. Withheld. |
| `tests/fixtures/copy-src/.env` | Secret-shaped fixture (`.env`). It is almost certainly a harmless test fixture, but the rule is the rule and its content was never inspected. |

> Consequently `tests/fixtures/copy-src/` ships **without** its `.env`. If any test depends on that
> fixture file, that test will fail in the release tree — recorded as a known gap (A4), not silently.

---

## 5. Per-file redaction counts

170 of 942 shipped files were modified. Counts are **per file**, host/port and absolute-path separately.
`MANIFEST.json` records the totals; this table is the per-file breakdown the card asked for.

| File | Host/port | Absolute path | Total |
|---|---:|---:|---:|
| `NOTICE` | 0 | 3 | 3 |
| `config/resextract.toml` | 1 | 0 | 1 |
| `docs/ACCEPTANCE_PROTOCOL.md` | 3 | 25 | 28 |
| `docs/EXTERNAL_WORKSPACE_POINTER_PROTOCOL.md` | 0 | 1 | 1 |
| `docs/LIVE_TARGET_NOTES.md` | 0 | 3 | 3 |
| `docs/OPERATIONS.md` | 0 | 6 | 6 |
| `docs/PLAN.md` | 3 | 6 | 9 |
| `docs/PLAN_CORRECTIONS.md` | 3 | 2 | 5 |
| `docs/TARGET_POLICY.md` | 0 | 2 | 2 |
| `docs/prompt-system/R2-PROMPT-RESULTS.md` | 1 | 1 | 2 |
| `docs/prompt-system/RELEASE-v1.json` | 2 | 0 | 2 |
| `docs/serving-options/BEST-CONFIG.md` | 1 | 0 | 1 |
| `docs/serving-options/CROSS-HTTP.md` | 1 | 0 | 1 |
| `docs/serving-options/LAUNCH-VLLM.md` | 1 | 0 | 1 |
| `docs/serving-options/TRACK-INTERVAL.md` | 1 | 0 | 1 |
| `experiments/context-cache/README.md` | 1 | 0 | 1 |
| `experiments/context-cache/cells/CROSS-HTTP/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/CROSS-HTTP/cross_http.py` | 3 | 0 | 3 |
| `experiments/context-cache/cells/CROSS-HTTP/history/rows-run1-3probe.jsonl` | 3 | 0 | 3 |
| `experiments/context-cache/cells/CROSS-HTTP/history/rows-run2-3probe.jsonl` | 3 | 0 | 3 |
| `experiments/context-cache/cells/CROSS-HTTP/rows.jsonl` | 3 | 0 | 3 |
| `experiments/context-cache/cells/DENSE-SGL/analysis.md` | 0 | 1 | 1 |
| `experiments/context-cache/cells/DENSE-SGL/launch_dense_sgl.py` | 4 | 1 | 5 |
| `experiments/context-cache/cells/DENSE-SGL/logs/P1-launch.json` | 4 | 0 | 4 |
| `experiments/context-cache/cells/DENSE-SGL/progress_loop.sh` | 0 | 1 | 1 |
| `experiments/context-cache/cells/E3/e3_report.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/E3/e3_runlog.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/E3/e3_server_state.json` | 4 | 0 | 4 |
| `experiments/context-cache/cells/G3-LIMIT-V2/g3v2_cell.py` | 1 | 0 | 1 |
| `experiments/context-cache/cells/G3/run.log` | 0 | 1 | 1 |
| `experiments/context-cache/cells/GROUND-TRUTH-PROMPT/launch.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/GROUND-TRUTH-PROMPT/resume_r.py` | 1 | 1 | 2 |
| `experiments/context-cache/cells/GROUND-TRUTH-PROMPT/run_r_only.py` | 2 | 1 | 3 |
| `experiments/context-cache/cells/GROUND-TRUTH-PROMPT/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/GROUND-TRUTH-R/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/M4/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/M4/battery.py` | 1 | 0 | 1 |
| `experiments/context-cache/cells/MOE-VLLM/logs/V3-launch.json` | 1 | 3 | 4 |
| `experiments/context-cache/cells/MOE-VLLM/moe_vllm_cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/P2-REPAD/p2_repad.py` | 0 | 1 | 1 |
| `experiments/context-cache/cells/P2-REPAD/run_meta.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/PROMPT-O1/prompt_o1_cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/PROMPT-O1/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/PROMPT-O2-EXTRA/g0.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/PROMPT-O2-EXTRA/launch.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/PROMPT-O2-EXTRA/prompt_o2e_cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/PROMPT-O2-EXTRA/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/PROMPT-O2/prompt_o2_cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/PROMPT-O2/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/PROMPT-O4/g0.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/PROMPT-O4/launch.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/PROMPT-O4/prompt_o4_cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/PROMPT-O4/run.log` | 0 | 20 | 20 |
| `experiments/context-cache/cells/PROMPT-O4/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-P1-O1/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-P1-O1/g0.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-P1-O1/launch.json` | 2 | 0 | 2 |
| `experiments/context-cache/cells/R2-P1-O1/prompt_r2p1o1_cell.py` | 5 | 1 | 6 |
| `experiments/context-cache/cells/R2-P1-O1/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-P1-O2/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-P1-O2/cell_handoff.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-P1-O2/g0.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-P1-O2/launch.json` | 2 | 0 | 2 |
| `experiments/context-cache/cells/R2-P1-O2/prompt_r2p1o2_cell.py` | 5 | 1 | 6 |
| `experiments/context-cache/cells/R2-P1-O2/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-PROMPT/O2/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-PROMPT/O3-REPEAT/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-PROMPT/O3-REPEAT/probe_midchange.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-PROMPT/O3-REPEAT/probe_p2_cost.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-PROMPT/O3-REPEAT/probe_self_hit.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/R2-PROMPT/O3-REPEAT/prompt_o3_repeat.py` | 4 | 1 | 5 |
| `experiments/context-cache/cells/R2-PROMPT/build_matrix.py` | 2 | 1 | 3 |
| `experiments/context-cache/cells/R2-PROMPT/o23-launch.json` | 5 | 5 | 10 |
| `experiments/context-cache/cells/R2-PROMPT/prompt_r2prompt_cell.py` | 4 | 1 | 5 |
| `experiments/context-cache/cells/R2-SGL/prod-boot.log` | 3 | 0 | 3 |
| `experiments/context-cache/cells/R2-SGL/state-S1.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/R2-SGL/state-S2.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/R2-SGL/state-S3.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/R2-SGL/stopsafety.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/R2-SGL/window.py` | 6 | 0 | 6 |
| `experiments/context-cache/cells/R2-VLLM/analysis.json` | 0 | 3 | 3 |
| `experiments/context-cache/cells/R2-VLLM/discarded-r1/analysis.json` | 0 | 3 | 3 |
| `experiments/context-cache/cells/R2-VLLM/logs/A1-launch.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/R2-VLLM/logs/OH1-launch.json` | 1 | 10 | 11 |
| `experiments/context-cache/cells/R2-VLLM/logs/OH1L-launch.json` | 1 | 10 | 11 |
| `experiments/context-cache/cells/R2-VLLM/logs/analysis-guard.json` | 0 | 2 | 2 |
| `experiments/context-cache/cells/R2-VLLM/logs/pmu16_cell.v1-3runs.py` | 3 | 2 | 5 |
| `experiments/context-cache/cells/R2-VLLM/logs/pre.json` | 4 | 8 | 12 |
| `experiments/context-cache/cells/R2-VLLM/logs/preflight2.json` | 4 | 2 | 6 |
| `experiments/context-cache/cells/R2-VLLM/logs/repair2-offline.json` | 0 | 7 | 7 |
| `experiments/context-cache/cells/R2-VLLM/logs/repair2-run1.json` | 0 | 6 | 6 |
| `experiments/context-cache/cells/R2-VLLM/logs/repair2-run2.json` | 0 | 6 | 6 |
| `experiments/context-cache/cells/R2-VLLM/logs/run.json` | 1 | 6 | 7 |
| `experiments/context-cache/cells/R2-VLLM/pmu16_cell.py` | 3 | 2 | 5 |
| `experiments/context-cache/cells/R2-VLLM/selftest_offline.py` | 0 | 1 | 1 |
| `experiments/context-cache/cells/STATE-CLIFF/plan.md` | 0 | 1 | 1 |
| `experiments/context-cache/cells/SYS-OPT/g0-dense.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/SYS-OPT/g0-moe.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/SYS-OPT/round-result.json` | 2 | 0 | 2 |
| `experiments/context-cache/cells/SYS-OPT/sysopt_r1.py` | 2 | 1 | 3 |
| `experiments/context-cache/cells/TRACK-INTERVAL/run_track.py` | 1 | 0 | 1 |
| `experiments/context-cache/cells/TRACK-INTERVAL/t128/cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/TRACK-INTERVAL/t128/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/TRACK-INTERVAL/t256/cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/TRACK-INTERVAL/t256/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/TRACK-INTERVAL/t64/cell.py` | 2 | 0 | 2 |
| `experiments/context-cache/cells/TRACK-INTERVAL/t64/warmup.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/TUNED/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/TUNED/logs/run.log` | 0 | 1 | 1 |
| `experiments/context-cache/cells/TUNED/logs/variant-launch.json` | 2 | 2 | 4 |
| `experiments/context-cache/cells/TUNED/run.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/TUNED/run_tuned.py` | 3 | 0 | 3 |
| `experiments/context-cache/cells/U2/server_config.json` | 3 | 0 | 3 |
| `experiments/context-cache/cells/U2/u2_gate.py` | 1 | 0 | 1 |
| `experiments/context-cache/cells/U2/u2_report.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/VLLM-CELL/redgreen.py` | 0 | 1 | 1 |
| `experiments/context-cache/cells/W3-COLLECT-ABORT-bootstrap/rows.jsonl` | 284 | 0 | 284 |
| `experiments/context-cache/cells/W3-COLLECT/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/W3-COLLECT/analyze_w3collect.py` | 1 | 0 | 1 |
| `experiments/context-cache/cells/W3-COLLECT/logs/G0-gate.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/W3-COLLECT/logs/battery-summary.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/W3-COLLECT/logs/gate.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/W3-COLLECT/logs/grid-summary.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/W3-COLLECT/logs/probe-summary.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/W3-COLLECT/rows.jsonl` | 328 | 0 | 328 |
| `experiments/context-cache/cells/W3-COLLECT/w3collect_cell.py` | 3 | 0 | 3 |
| `experiments/context-cache/cells/WIN-SGL/launch_variant.py` | 5 | 0 | 5 |
| `experiments/context-cache/cells/WIN-SGL/logs/REH-launch.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/WIN-SGL/logs/S1-launch.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/WIN-SGL/logs/S2-launch.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/WIN-SGL/logs/S3-launch.json` | 1 | 2 | 3 |
| `experiments/context-cache/cells/WIN-SGL/win_sgl_cell.py` | 1 | 0 | 1 |
| `experiments/context-cache/cells/WIN-VLLM/analysis.json` | 1 | 0 | 1 |
| `experiments/context-cache/cells/WIN-VLLM/launch_variant.py` | 3 | 5 | 8 |
| `experiments/context-cache/cells/WIN-VLLM/logs/V1-launch.json` | 1 | 3 | 4 |
| `experiments/context-cache/cells/WIN-VLLM/logs/V2-launch.json` | 1 | 3 | 4 |
| `experiments/context-cache/cells/WIN-VLLM/logs/V3-launch-attempt1-mtp.json` | 0 | 3 | 3 |
| `experiments/context-cache/cells/WIN-VLLM/logs/V3-launch.json` | 1 | 3 | 4 |
| `experiments/context-cache/cells/WIN-VLLM/win_vllm_analyze.py` | 1 | 0 | 1 |
| `experiments/context-cache/cells/WIN-VLLM/win_vllm_cell.py` | 1 | 0 | 1 |
| `experiments/context-cache/client.py` | 1 | 0 | 1 |
| `papers/context-cache/CLAIMS.md` | 0 | 1 | 1 |
| `papers/context-cache/EVIDENCE.md` | 1 | 0 | 1 |
| `papers/context-cache/MANUSCRIPT.md` | 1 | 0 | 1 |
| `papers/context-cache/PACKAGE.md` | 0 | 1 | 1 |
| `papers/context-cache/RUN.json` | 8 | 0 | 8 |
| `papers/gated-read-batching/DISCLOSURE_CHANGES.md` | 0 | 13 | 13 |
| `repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md` | 0 | 6 | 6 |
| `repro/encoder-crossover-190-SANITISED/fixture/DECISION_CASE_SCHEMA.ts` | 0 | 1 | 1 |
| `repro/encoder-crossover-190-SANITISED/harness/data/manifest.json` | 0 | 3 | 3 |
| `repro/encoder-crossover-190-SANITISED/variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts` | 0 | 1 | 1 |
| `src/resextract/doctor.py` | 1 | 0 | 1 |
| `src/resextract/kg/policy.py` | 0 | 1 | 1 |
| `src/resextract/kg/staging.py` | 1 | 0 | 1 |
| `src/resextract/llm/occamy.py` | 2 | 0 | 2 |
| `src/resextract/mine/__init__.py` | 0 | 1 | 1 |
| `tests/fixtures/dashboard-store/build.py` | 0 | 1 | 1 |
| `tests/test_cli.py` | 0 | 3 | 3 |
| `tests/test_context_runner.py` | 1 | 0 | 1 |
| `tests/test_dashboard.py` | 3 | 0 | 3 |
| `tests/test_dashboard_auth.py` | 13 | 1 | 14 |
| `tests/test_docket_assemble.py` | 0 | 1 | 1 |
| `tests/test_docket_reassembly.py` | 0 | 2 | 2 |
| `tests/test_kg_policy.py` | 0 | 1 | 1 |
| `tests/test_kg_staging.py` | 0 | 1 | 1 |
| `tests/test_mine_candidates.py` | 0 | 1 | 1 |
| `tests/test_occamy_client.py` | 2 | 0 | 2 |
| `tests/test_store.py` | 0 | 3 | 3 |
| `tests/test_store_v2.py` | 0 | 1 | 1 |
| `tests/test_store_v3.py` | 0 | 3 | 3 |
| **TOTAL** | **850** | **244** | **1094** |

The `experiments/context-cache/` tree accounts for 949 of the 1094 replacements — logged command
lines and cell configs recorded the serving command verbatim, host and port included.

---

## 6. Licence — the one discrepancy, and how it was resolved

**The card and the template of record disagree, and the card wins because it is verifiable.**

| Source | Required Notice line as it actually reads |
|---|---|
| Card gate 4 (required text) | `Required Notice: Copyright Aswin-Ram-K (https://github.com/Aswin-Ram-K/Consonance)` |
| `/home/zer0null/Duval/LICENSE` line 5 | **byte-identical to the required text** (`duval==W: True`) |
| `strategy/licence-templates/RELEASED-PIECE/LICENSE` line 1 | `Required Notice: Copyright 2026 Aswin-Ram-K` — **different; year only, no URL** |

Carrying the template would have failed gate 4 on a byte comparison **and** would have shipped a
Required Notice differing from the notice on the text it is licensing. The licence was therefore
shipped **byte-for-byte from `/home/zer0null/Duval/LICENSE`** — the source the card itself names as
"the upstream licence to carry" — sha256 `a66aa879d12019240c67f56c14e0c95393300758263814a58c4827b35f5e18e3`, 4,666 bytes, read
**read-only**; nothing under `/home/zer0null/Duval` was written.

**This is the one place the card's inputs are internally inconsistent, and it needs a human
decision, not another agent's.** If the author actually intends the `Copyright 2026 Aswin-Ram-K`
form, then either gate 4 or the template must change. Nothing in this release depends on the answer:
swapping `release/v0.1/LICENSE` and re-hashing one manifest entry is the whole change.

`COMMERCIAL.md` and `CONTRIBUTING.md` ship **unmodified** from the template directory. A
`RELEASED-PIECE` piece conventionally has no AGPL file left behind and exactly one licence file —
satisfied: `LICENSE` is the only licence file in the tree.

---

## 7. GATES — verbatim outputs

```
$ grep -rE '192\.168\.' release/v0.1
[lines: 0]
$ grep -rE '/home/zer0null' release/v0.1
[lines: 0]
$ find release/v0.1 -size +25M
[empty]
$ grep -c "PolyForm Noncommercial License 1.0.0" release/v0.1/LICENSE
1
$ grep -Fx "Required Notice: Copyright Aswin-Ram-K (https://github.com/Aswin-Ram-K/Consonance)" release/v0.1/LICENSE
Required Notice: Copyright Aswin-Ram-K (https://github.com/Aswin-Ram-K/Consonance)
$ ls -1 release/v0.1/{NOTICE,COMMERCIAL.md,CONTRIBUTING.md,THIRD-PARTY-NOTICES.md}
release/v0.1/COMMERCIAL.md
release/v0.1/CONTRIBUTING.md
release/v0.1/NOTICE
release/v0.1/THIRD-PARTY-NOTICES.md
$ du -sh release/v0.1
62M	release/v0.1
$ find release/v0.1 -type f | wc -l
943
entries=942 mismatched=0 on_disk=942 unlisted=0 all_have_sha256=True
```

**Gate 6 verification (the check behind the claim):**

```
entries=942 mismatched=0 on_disk=942 unlisted=0 all_have_sha256=True
```

i.e. every manifest entry's sha256 re-verifies against the file on disk, every file on disk is
listed, and every entry carries a 64-hex-character digest.

*Gate 4 first failed and was fixed within the 3-attempt bound by shipping `Duval/LICENSE` instead
of the template (see §6) — not by editing the licence text to fit the gate.*

---

## 8. Assumptions

| # | Assumption | Why this default |
|---|---|---|
| A1 | **`Duval/LICENSE` is the licence of record** for the `Required Notice` line, over the template's `Copyright 2026` form. | The card names it as "the upstream licence to carry" and its line 5 matches the card's required text byte-for-byte. The template matches neither. Escalated in §6 rather than decided silently. |
| A2 | **"any port suffix" is read broadly** — `host:port` is replaced whole, so `192.168.2.168:8000` becomes `serving-host`, not `serving-host:8000`. | The card says "the internal hosts **and any port suffix**" — the suffix is named as part of what gets replaced. |
| A3 | **Over-sanitisation is preferred to under-sanitisation** for `192.168.2.1` and `192.168.0.0/16`. They are not the two named hosts, but gate 1 is a raw `192\.168\.` grep and internal addresses are internal. | A leaked internal address is irreversible; a `<placeholder>` in a test fixture is not. |
| A4 | **`tests/fixtures/copy-src/.env` and `config/targets.toml` are withheld** even though both are under `INCLUDE` trees. | Secret-shaped and internal-registry content respectively. The include list says "curate from these", not "ship everything". |
| A5 | **All 27 `docs/` files kept.** | The card says "curated `docs/`" without naming what to cut; every file is operational or architectural documentation of the shipped code. Over-inclusion of prose is cheap; a missing acceptance protocol is not. |
| A6 | **`README.md` generated** from the Case B paragraph plus a start-here table. | `PLACEMENT.md` requires the Case B paragraph verbatim in every released piece's README; the paragraph is copied unmodified. |
| A7 | **No test suite run.** | Forbidden by the card. The release's correctness claims rest on the gates and on the hash manifest, not on a green suite. |
| A8 | **`repro/encoder-crossover-190-SANITISED/` kept as-is** apart from 11 residual host/path substitutions. | Its own `EXCLUDED.md`/`INTEGRITY.md`/`REDACTION_REPORT.md` define its scope; re-curating it would contradict the package's own integrity record. That its upstream scrub left residue is recorded as a finding. |

---

## 9. Known gaps (recorded, not resolved)

1. **The `Required Notice` discrepancy (§6)** needs a human ruling.
2. **`tests/fixtures/copy-src/.env` withheld** — any test depending on it will fail in the release tree.
3. **`config/targets.toml` withheld** — code paths that read it will need the reader to supply their
   own registry; this is correct for a public piece but is a behavioural difference.
4. **`.occamy.lock` excluded** — anything that acquires that lock will create a fresh one.
5. **The release is a staging tree, not a publication.** Making it public is a legal act the author
   performs; `PLACEMENT.md` §3 governs the order and §"the one irreversible step" governs why the
   licence is placed before, never after, a repository goes public.

---

## 10. Refresh note — 2026-10-24 21:50 CDT (`REFRESH-RELEASE-PAPER`)

**What was stale.** `release/v0.1/papers/context-cache/MANUSCRIPT.md` was copied at 21:16, i.e. *before*
`CITE-VERIFY` and before `CITE-PROSE-REPAIR`. The release copy therefore carried **3** `[CITATION NEEDED]`
markers, none of the three verified citations, and one mangled sentence fragment. Shipping it would have
published a paper with unresolved markers. `papers/context-cache/CITATIONS.md` was not in the release tree
at all.

**What was done.** The live `MANUSCRIPT.md` (93,021 bytes, mtime 21:39) and `CITATIONS.md` (7,266 bytes,
mtime 21:17) were copied into the release tree, the §"sanitisation" substitution was re-applied to the
copies, and `MANIFEST.json` was regenerated from disk.

| File | sha256 before | sha256 after | bytes |
|---|---|---|---|
| `papers/context-cache/MANUSCRIPT.md` | `deeb0b1300dc79b8d0840181a44a0cb9c6770f8361bf8776ca0b06722c84c72b` | `9490bba6f3555bbae6ff32ac3df783d92503131c0c1e8254ed7dbe7559d6d700` | 92,454 → 93,015 |
| `papers/context-cache/CITATIONS.md` | *absent from release tree* | `82beb59baffef09f35bc87193e15e30fd15f27640586740fe90e5ef4e16a4090` | — → 7,266 |

(Source `MANUSCRIPT.md` sha256 was `37a3f1b34eb43c0c47dc9d41dd02158e6ac000f888b6ee92fe26c93f3ef008cd`;
the 6-byte difference between 93,021 and 93,015 is the single host substitution below.)

**Sanitisation re-applied to the copies** (host/port → `serving-host`, workspace paths → `<workspace>`):

| File | host:port replacements | `/home/zer0null/...` replacements | residual `192.168.` | residual `/home/zer0null` |
|---|---|---|---|---|
| `MANUSCRIPT.md` | 1 | 0 | 0 | 0 |
| `CITATIONS.md` | 0 | 0 | 0 | 0 |

The one replacement is line 993: `` `http://192.168.2.168:8012` `` → `` `http://serving-host` ``, matching the
§A2 rule that a host with a port suffix is replaced whole. `CITATIONS.md` was byte-identical to its live
source (no substitution needed). `diff` of live vs release `MANUSCRIPT.md` yields **exactly one changed
line (993)** and nothing else; line count is unchanged at 1214.

**Manifest.** 942 → **943** entries, `total_bytes` 61,027,417 → **61,035,244**. Exactly one existing entry
changed digest (`papers/context-cache/MANUSCRIPT.md`) and exactly one entry was added
(`papers/context-cache/CITATIONS.md`); nothing was removed. All other entries were re-hashed and are
byte-unchanged. Per-file counts for this refresh are recorded under
`sanitisation.refresh_2026_10_24`; the tree-wide tallies (`files_redacted` 167, host replacements 850,
path replacements 161) are carried over from the original SANITISE-RELEASE pass unchanged.

**Gate outputs (verbatim, all pass):**

```
### G1: grep -rE "192\.168\." release/v0.1 | wc -l
0
### G2: grep -rE "/home/zer0null" release/v0.1 | wc -l
0
### G3: grep -c "CITATION NEEDED" on release MANUSCRIPT
0
### G4: grep -c "SGLang review of attention backends" on release MANUSCRIPT
0
### G5: three verified citations
arXiv:2309.06180 -> 1
arXiv:2312.07104 -> 1
arXiv:2605.23296 -> 1
### G6: wc -l release MANUSCRIPT
1214 release/v0.1/papers/context-cache/MANUSCRIPT.md
### G7: find release/v0.1 -size +25M (expect empty)
[find exit=0]
### G8a: licence line present
1
### G8b: byte-identical to sed -n 5p Duval/LICENSE
IDENTICAL
a66aa879d12019240c67f56c14e0c95393300758263814a58c4827b35f5e18e3  release/v0.1/LICENSE
87eb3f8369b6d769e87e99aff69d7a9c4b59d81082ecd7ef8092544f2ad6b5f4  -
### G9: manifest entries vs shipped files
entries=943 on_disk=944 shipped_minus_manifest=943 equal=True
### G10: du -sh
62M	release/v0.1
file count: 944
```

**Read-only discipline.** Nothing was written under `papers/**` (copied *from*, never to) or under
`/home/zer0null/Duval` (read with `sed -n '5p'` only). No model server was restarted and no `/flush_cache`
was called. Live mtimes are unchanged (MANUSCRIPT 21:39, CITATIONS 21:17).

**Recorded assumption (A9).** The manifest carries `sanitisation.refresh_2026_10_24` as an *added* key inside
the existing `sanitisation` object; the top-level shape (`release`, `generated`, `licence`,
`licence_source`, `sanitisation`, `excluded`) and the pre-existing `file_count`, `total_bytes`, `files`,
`control_files`, `licence_template_note` keys are all preserved. `generated` was left at `2026-10-24` — the
refresh date is the same day, and the dated record of the refresh lives here rather than in that field.

---

## 11. Self-sufficiency repair — 2026-10-24 23:22 CDT (`RELEASE-DATA`)

**The defect.** The tree was published without `state/`, yet two of its own runners resolve their last data
source through the release root (`ROOT = Path(__file__).resolve().parents[2]`). From `cd release/v0.1`,
`papers/context-cache/recompute.py all` and `papers/context-cache/recompute_r2.py all` both exited **1** with
`FileNotFoundError: …/release/v0.1/state/config/rows.jsonl`, raised at **claim 65 of 69** — so C65, C66, C67,
C68 and SYSOPT (5 of 69 claims) were unreachable from the shipped artefact, and the verdict recorded in
[`REPRO.md`](REPRO.md) had to read "NO as shipped". By the same mechanism `tests/test_gap_closure_ledger.py`
failed 8/8 on `FileNotFoundError: …/release/v0.1/state/gap-ledger.json`.

**The fix — two files, nothing more.** `state/config/rows.jsonl` (82,565 bytes) and `state/gap-ledger.json`
(25,834 bytes) were copied from the live tree. No other `state/` content (1.6 GB) was shipped, and neither
`orchestration/` nor `scratch/` was shipped.

**Sanitisation — 0 replacements were required.** Both files were measured *before* copying:
`grep -c '192\.168\.'` → **0** and `grep -c '/home/zer0null'` → **0** for each, so the shipped bytes are the
live bytes (no redaction pass, no digest drift). `state/config/rows.jsonl` re-parses as JSONL: **284** non-blank
lines, every one a valid object.

| File | Bytes | sha256 |
|---|---|---|
| `state/config/rows.jsonl` | 82,565 | `8154e32d2f98f0d653ed6a3f03af7b6ca5effefd6c03c74c392e6a8819fc00e0` |
| `state/gap-ledger.json` | 25,834 | `56f2722862904ed78115eab427513b7a5b66ac45893b69f47c915c3610aa0b8a` |

**File count change.** `MANIFEST.json` was recomputed from disk rather than appended to:
**943 → 945 entries**, bytes **61,035,244 → 61,143,643**. On disk: **946** files, so entries = files − 1 (the
manifest never lists itself), and all 945 listed `{path, bytes, sha256}` triples were re-verified against the
files — **0 mismatches**. The `files`, `file_count` and `total_bytes` fields were rewritten; the recorded
exclusions and control-file list were left as they were, and a new
`state_files_added_2026_10_24` key records the two additions, their digests, the sanitisation result, and what
is still deliberately absent.

**Measured after the repair** (all from `cd release/v0.1`, `PYTHONDONTWRITEBYTECODE=1`, interpreter
`../../.venv/bin/python` — the venv is at the workspace root, not `release/.venv`):

| Command | Exit | Decisive line |
|---|---|---|
| `papers/context-cache/verify_package.py` | **0** | `verify_package: PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, … UNVERIFIED: none` |
| `papers/context-cache/recompute.py all` | **0** | `COVERAGE GUARD PASS  69 claims documented, 67 runnable here + 2 script-backed` |
| `papers/context-cache/recompute_r2.py all` | **0** | `PASS 61/61`, `38/38`, `48/48`, `75/75`, `85/85`, `70/70`, `50/50 values match` |
| `-m pytest tests/test_gap_closure_ledger.py -q` | **1** | `6 failed, 2 passed in 0.07s` — unresolvable content refs (limitation L1) |
| `-m pytest tests/test_g5_fanout_attribution.py -q` | **0** | `4 passed in 0.01s` |
| `-m pytest tests/test_paper_g3_bands.py -q` | **0** | `13 passed in 0.02s` |

Residual needles over the whole shipped tree: `192.168.` → **0**, `/home/zer0null` → **0**.

**Remaining named limitation (L1).** The gap-closure ledger guard is red **by design in any release**, and it
was deliberately not greened. Its first failure is
`AssertionError: unresolvable evidence refs:` → `G11: orchestration/VERDICTS.md:12 (file_line) does not resolve`,
followed by nine refs total: that verdict line, six `scratch/cache-audit/docs/pin_*` pinned upstream sources,
the `CACHE-AUDIT` and `PAPER-FINAL` handoffs, plus `state/config/live-server-config.json` (61,336 bytes — a
serving-host config carrying two internal addresses, excluded by the same policy as the other 167 redacted
files) and `state/sys-opt-verdict.json` (a workspace verdict document, not a numeric source). The guard is a
working-tree invariant: `8 passed` live, red in any faithful artefact. Shipping `orchestration/` or `scratch/`
to turn it green would publish workspace provenance and would not make a single claim more re-derivable, so the
red state is recorded here rather than fixed. It is not evidence about the 69 claims, which re-derive in full.

**Correction of record.** The brief stated that [`REPRO.md`](REPRO.md) documented root-level commands
(`release/v0.1/verify_package.py`) and that its commands therefore exited 2. That did **not** reproduce: a
search of all of `release/` finds no root-level invocation, and the previous revision already used
`papers/context-cache/…`. What was genuinely wrong in `REPRO.md` — the stale `NO as shipped` verdict, the
943-file/61,035,244-byte header, and a `$OLDPWD/.venv/bin/python` line pointing at a non-existent interpreter —
was corrected, and the file now carries the measured verdict and exit codes above (its deviation D7).
