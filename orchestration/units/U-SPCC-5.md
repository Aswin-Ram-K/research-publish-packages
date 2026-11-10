# U-SPCC-5 — 50% memory allowance enforcement

Implemented `experiments/ptr-engine/serving/spcc_supervisor.py` with subcommands
`open-window`, `run`, `close-window`. Cgroup v2 root injectable via
`SPCC_CGROUP_ROOT`; meminfo via `SPCC_MEMINFO_PATH`; base dir via `SPCC_BASE_DIR`.
Tests: 7 passed.

No live MEM-WINDOW.json left behind.