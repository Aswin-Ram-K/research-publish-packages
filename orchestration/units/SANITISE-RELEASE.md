# UNIT SANITISE-RELEASE — build the publication staging tree

> Persisted verbatim from the task-board card prompt (tag `automated`), 2026-10-24.

AUTONOMOUS: no human is present. NEVER ask questions, never wait for input. Take the conservative default, record it under an "assumptions" key, and continue to a deliverable.

OPERATOR RULING (2026-10-24, binding): the Duval/Consonance repository was NEVER public, so no prior AGPL-3.0 grant ever existed. Current PolyForm Noncommercial 1.0.0 is the only grant. The licensing execution order is APPROVED.

OBJECTIVE
Produce `release/v0.1/` — a sanitised, licensed, self-contained copy of the publishable parts of this workspace, plus a manifest that proves what was excluded and why.

INPUTS (read-only — never modify these)
- `papers/context-cache/MANUSCRIPT.md` (the live paper; you sanitise the COPY only)
- `strategy/licence-templates/` — the licence template of record: `PLACEMENT.md`, `RELEASED-PIECE/LICENSE`, `RELEASED-PIECE/COMMERCIAL.md`, `RELEASED-PIECE/CONTRIBUTING.md`, `README-PARAGRAPHS.md`
- `/home/zer0null/Duval/LICENSE` — the upstream licence to carry (PolyForm NC 1.0.0; line 5 carries the Required Notice). READ ONLY. Never write anything under /home/zer0null/Duval.

INCLUDE (curate from these)
`src/`, `papers/`, `tests/`, `experiments/context-cache/`, `repro/encoder-crossover-190-SANITISED/`, curated `docs/`, `pyproject.toml`, `config/`
EXCLUDE ALWAYS: `.git`, `.venv`, `scratch/`, `state/`, `jobs/`, `archive/`, `journal/`, `dockets/`, `.pytest_cache`, `__pycache__`, `*.lock`, any file over 25 MB.

HARD REQUIREMENT — SANITISATION (must be scripted, not hand-edited)
- Replace every occurrence of the internal hosts and any port suffix with the literal placeholder `serving-host`: `192.168.2.168`, `192.168.2.187`.
- Replace absolute paths `/home/zer0null/reserach extarctor` and `/home/zer0null/Duval` with `<workspace>`.
- Record per-file replacement counts.

GATES (all must pass; paste each command and its verbatim output)
1. `grep -rE '192\.168\.' release/v0.1` returns 0 lines
2. `grep -rE '/home/zer0null' release/v0.1` returns 0 lines
3. `find release/v0.1 -size +25M` is empty
4. `release/v0.1/LICENSE` exists and contains both "PolyForm Noncommercial License 1.0.0" and the exact line "Required Notice: Copyright Aswin-Ram-K (https://github.com/Aswin-Ram-K/Consonance)"
5. `release/v0.1/` contains `NOTICE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `THIRD-PARTY-NOTICES.md`
6. `release/v0.1/MANIFEST.json` lists a sha256 for every shipped file
7. report `du -sh release/v0.1` and the file count

DELIVERABLES
- `release/v0.1/**`
- `release/v0.1/MANIFEST.json`
- `release/REPORT.md` — include/exclude lists with reasons, per-file redaction counts, gate outputs verbatim, measured size, assumptions
- `orchestration/units/SANITISE-RELEASE.md` (persist this card verbatim)
- `orchestration/handoffs/SANITISE-RELEASE.json` with exactly these keys: `unit`, `status`, `artifacts`, `evidence` {`command_or_count`, `commands`}, `blocker`, `next_unit_hint`, `write_paths`, `assumptions`

WRITE PATHS (touch nothing else)
`release/**`, `orchestration/units/SANITISE-RELEASE.md`, `orchestration/handoffs/SANITISE-RELEASE.json`

BOUND: 40 tool calls. If a gate cannot pass after 3 attempts on the same file, STOP and report `partial` naming the offending file and line.
Do NOT run the full test suite. Do NOT modify `papers/context-cache/MANUSCRIPT.md` in the live tree — another unit owns it this pass.
Return a <=15-line summary: status, artifacts, the gate evidence lines, blocker, next hint.
