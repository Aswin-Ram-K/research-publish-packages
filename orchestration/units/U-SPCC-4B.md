# U-SPCC-4B — launch-sglang-spcc.sh cosmetic defects

## Defect 1 — pool size
Comment said unified pool ~128 GB; verified figure is 121 GB. Corrected
comment to `0.45 of ~121 GB unified = ~54.45 GB`. `--mem-fraction-static`
unchanged at 0.45 (MEM_FRAC=0.45).

## Defect 2 — port
`--port 30000` → `--port 8012`. Determination: 30000 is SGLang's default
server port, but this script's server is the occamy instance served on :8012
(per REMOTE-ROOT.md and the live endpoint). It is not a distributed/training
port (no --dist-init-addr/--nnodes/--node-rank flags in the captured Args), so
it is an error, corrected to 8012.

## Acceptance
- grep shows 121, 8012, no 128/30000
- `bash -n` exit 0
- `--dry-run` emits full command with --port 8012
- no MEM-WINDOW.json in serving/