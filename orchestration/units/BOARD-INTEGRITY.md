# BOARD-INTEGRITY — unit card

Objective: Rework tools/board/session_recon.py so the classifier distinguishes interactive/user sessions (allowed, reported only) from board-execution sessions (must map to a card), card-subagents (VIOLATION: delegated-from-card), and user-subagents (reported only); add settled-lag and uncarded board execution checks; append three rules to AGENTS.md.

Hard bound: read-only over ~/.dsh; no card creation/movement/settlement; 40 tool calls.

Write paths: tools/board/session_recon.py, AGENTS.md, orchestration/handoffs/BOARD-INTEGRITY.json, state/logs/session-recon.json.

Deliverable: red→green→red proof with exact tails; offenders table on failure.