# V5C - independent verification of U5.12 (re-labelling the two real dockets)

Scope: verify that U5.12's re-label of `dockets/duval/duval-u55-pinned` and
`dockets/duval/duval-replay-material` is honest and lost nothing. I authored none of it.
Write paths: this card, `orchestration/VERDICTS.md`, `orchestration/handoffs/V5C.json`,
`state/logs/V5C*`, `state/verify/V5C/**`. Hard bound 30 tool calls (used 30). Zero LLM calls.

Dockets and `state/backups/U5.12-*` were treated as READ-ONLY (hashed, never restored over).
The five docket test files only. Full `__pycache__` purge + `PYTHONDONTWRITEBYTECODE=1` per run.
Tree-hash recipe (stated): sha256 over `cd <root> && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum`.

Verdict: PARTIAL - the re-label is honest and material/pinned provenance is intact, but it was
not information-neutral and two of the unit's evidence claims are overstated. See VERDICTS.md.
