# PRE-REG-SYSOPT — the ceiling rule, written before any SYS-OPT number exists

**Objective.** Freeze the SYS-OPT improvement/ceiling rule in `docs/prompt-system/VERSIONS.md`
**before** card `SYS-OPT` (`733058c8`) produces any measurement, so the thresholds cannot be
reverse-fitted to a result. Offline: zero live requests, no GX10, no model start.

**Contract.** Sections in card order: PRE-REGISTRATION (with measured `date -u`), Scoring,
IMPROVEMENT, ONE_SIDED, CEILING, REGRESSION, HEADROOM, ROUND PROTOCOL, CHANGE MENU, V0 definition,
and the single withdrawal condition. Anchors quoted from the card only (`PROMPT-O1` A 529.2958 /
C 547.0845 / R 583.1408 / H 961.9718 / C0 709.8592; `PROMPT-O2-EXTRA` R 600.169, A−R −71.3); no
measured number is invented and V0 is defined but left unfilled for SYS-OPT.

**Hard bound.** 12 tool calls. Handoff stub first, then the rule, then the filled handoff.

**Write paths.** `docs/prompt-system/VERSIONS.md`, `orchestration/handoffs/PRE-REG-SYSOPT.json`,
`orchestration/units/PRE-REG-SYSOPT.md`.

**Proof.** `python3 -c "import pathlib;t=pathlib.Path('docs/prompt-system/VERSIONS.md').read_text();
assert 'PRE-REGISTRATION' in t and 'CEILING' in t and 'ONE_SIDED' in t;print('OK',len(t),'chars')"`
quoted in the handoff, plus the empty-state listing that proves the file predates every SYS-OPT row.
