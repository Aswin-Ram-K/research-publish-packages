# BOX-INV — pre-maintenance box inventory (HTTP-only probe)

Purpose: capture everything the maintenance window needs about `gx10-163b` before it opens, without credentials.

Hard constraints: HTTP GET only; no SSH, no `~/.ssh`, no lock, no live model requests. Allowed GETs only: `:8012/get_server_info`, `:8012/v1/models`, `:8014/version`, `:8014/v1/models`, `:8014/health`, `:8000/v1/models`, `:8010/v1/models`.

Write paths:
- `state/config/box-inventory.json`
- `orchestration/units/BOX-INV.md`
- `orchestration/handoffs/BOX-INV.json`

Key results:
- Production rollback line reconstructed from `/get_server_info` (183 flags; model path resolved to live snapshot).
- `qwen3.5-9b` dense vs hybrid not answerable over HTTP (SSH-gated question #1).
- 8010 requires bearer token; model not enumerable without credentials.
- Disk/RAM/HF cache/systemd/GPU utilisation are `unverified-ssh-gated`.
