# `research/tooling/` — index

Research only. Nothing here is wired into the pipeline, and nothing here authorises a product change.

**[`TOOLCHAIN.md`](TOOLCHAIN.md) is the single consolidated entry point** — the toolchain requirements R1–R9, what is installed today, the gap matrix, the ranked plan, what was rejected, and the links; every other file in this directory is its evidence, not an alternative reading.

| file | unit | what it is | verdict in one line |
|---|---|---|---|
| [`TOOLCHAIN.md`](TOOLCHAIN.md) | **S7** (consolidation) | The one document to act on: R1–R9 requirements, measured inventory, gap matrix, ranked P0/P1/P2 plan, rejections, invariants, corrections C1–C11, open questions, and a dated link table. | **Entry point** — merges the five research files below; they are its evidence. |
| [`01-inventory.md`](01-inventory.md) | **S1** (local inspection) | What the project already has, every claim carrying `path:line`: capability table, graphify's subcommands vs resextract reality, agent plugin surface, gaps G1–G15, plus a 2026-10-23 errata section (§7). | The capability is installed and the pipeline uses **3 of ~27 command families** (≈89% unwired) — `update` is wired but disabled. *(count corrected by V1 — C1, C2)* |
| [`02-candidates.md`](02-candidates.md) | **S2** (web research) | Every candidate tool with URL, licence, runtime, last release, overlap, verdict. | "Repo traversal: nothing missing" — a judgement about the *dependency*, not the pipeline. Its "436-file Python target" premise and Sourcegraph 404 are corrected (C4, C5). |
| [`FINDINGS.md`](FINDINGS.md) | **S3** (synthesis) | Reconciles the two: naming resolution, the subcommand finding, verdicts for every candidate, ranked P0/P1/P2, open questions, provenance. Carries targeted `(corrected by V1 …)` marks. | **Installed and unwired — in the app and in the agent.** ADD: plugin (conditional on a code change), `ast-grep-py`, `ripgrep`. |
| [`CORRECTIONS.md`](CORRECTIONS.md) | **S5** (correction) | The verifier's contradictions, answered one by one: claim as published → what is true → the proving command/`path:line` → which document carried the error → **effect on the recommendation**. C1–C11. | **Supersedes the clauses it names.** 6 claims contradicted, 5 record-accuracy/fix corrections; 12 other claims reproduced and untouched. `update` is wired-but-disabled (C1), and enabling it needs a *bounded* copy (C11). |
| [`03-lsp-code-error-rate.md`](03-lsp-code-error-rate.md) | **S6** (web research) | LSP/SCIP/`multilspy` against the two error rates — claims about the target, and our own Python — plus the non-LSP levers (target-toolchain type-check, ruff, hypothesis, mutmut) with ranked P0/P1/P2 adoption. | **Offline SCIP index + symbol-identity check is P0 for claim errors; `basedpyright` ratchet + mutation tests for ours. Stack graphs are archived — do not adopt.** |
| `handoffs/S1.json` | S1 | S1's report: artifacts, evidence, gaps, assumptions. | `status: done` — its `evidence.commands` need `-E` (C7) |
| `handoffs/S2.json` | S2 | S2's report: artifacts, evidence, adds, rejects, assumptions. | `status: done` — its 404 and 436 premises are corrected (C4, C5) |
| `handoffs/S3.json` | S3 | S3's report: verdicts, top recommendation, overrules, unverified items. | `status: done` |
| [`handoffs/V1.json`](handoffs/V1.json) | **V1** (independent verifier) | Re-checked every claim in S1/S2 by re-running the evidence: 20 checks, each with claim / verdict / evidence. | **`partial` — 12 reproduced, 6 contradicted.** The contradictions became `CORRECTIONS.md`. |
| `handoffs/S5.json` | S5 | S5's report: corrections applied, files edited, unchanged constants, write paths. | `status: done` |
| `_probe/` | S3 synthesis (60 KB fixture) | Two-file fixture (`src/a.py`, `src/n.md`) plus `out/graphify-out/` from one real `graphify extract --code-only --out …` run. | Evidence that `--out` keeps writes outside the analysed tree and that `--code-only` drops docs. **Keep it** — re-run before deleting. |

**Read order:** `FINDINGS.md` §0 → §1 → §4. §2 is the section the original question actually needed. **If any clause in `FINDINGS.md` or `01-inventory.md` is marked "(corrected by V1 …)", read `CORRECTIONS.md` first** — it carries the proof and the consequence for the plan.

**Rule for future edits to this directory**

- **Research only; no product changes.** Nothing here edits `src/`, `config/`, `orchestration/`, `docs/` or `tests/`, and no conclusion here is a substitute for a unit card.
- **Sources are dated 2026-10-23.** Every number is attributed to a command, a `path:line`, or a URL snapshot of that date — re-verify URLs and star/release counts before citing them again.
- **Re-verify before reuse:** graph artifact facts (digest, node count, `built_at_commit`) change on every rebuild; a rebuilt graph makes `FINDINGS.md` §4a *done*, not wrong.
- **`/home/zer0null/Duval` stays read-only.** Any new file here must be produced by reading or by running a tool with an explicit `--out` under this workspace — never by writing into a target.
- **New claims are appended, not asserted over old ones.** If a later unit disagrees, add a dated section naming what it supersedes; the two source files are a record and are not rewritten.
- **When a verifier contradicts a published claim, correct in `CORRECTIONS.md` and mark the clause — never silently rewrite the evidence files.**
