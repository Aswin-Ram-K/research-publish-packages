# V6G — independent verifier: U6.12 rule arms + the two guards

Scope: the behavioural rule of U6.12 and its two guards (the parts U6.13 does not cover).
Not the author of U6.12. Fixes nothing. Bound: 16 tool calls, ≤3 server starts, zero live LLM calls.

## Verdict: PASS
- C1 rule arm-by-arm — PASS (LAN 192.168.2.187; anon 401, token 200, SSE gated, control 401→200;
  refusals exit 2 with nothing bound; loopback anon 200 + auto works). One wording correction on arm 2.
- C2 tests + what the guards pin — PASS. 9 / 42 / 66, exit 0, after a FULL __pycache__ purge.
  Refusal test asserts status **and** body (`"token" in error`), stronger than "not 200".
- C3 red→green — PASS. Both guards reproduced, sha-proven, restored bit-identical.

## Evidence
- Liveness: `curl http://192.168.2.168:8012/v1/models` → HTTP 000, curl exit 7 (DOWN, 2 attempts, 1 probe).
- C1: `state/logs/V6G-c1-{remote,auto-cli,auto-module,loopback}.log`
- C3: `state/logs/V6G-c3-red.log`; backups `state/verify/V6G/reverts/*.V6G-C3-backup`
- Release shas: app.py f27645f3…, cli.py (src/resextract/cli.py) 6ac4c039…, __main__.py a4a08753… — all matched.

## Findings beyond the claim
1. `python -m resextract.dashboard --token auto` is NOT refused: no `auto` keyword there, so it binds a
   remote listener with the literal secret "auto" (anon 401, `x-dashboard-token: auto` 200). Only the
   absence of `--token` exits 2. Not an anonymous leak, but a weak-secret footgun and an
   entry-point-semantics mismatch with the CLI.
2. Red(b) with the uvicorn sentinel: the test never binds (stub + failure at `pytest.raises` first), so
   it is a *logic* red. The real unguarded path does bind — I reproduced it live on 192.168.2.187:8944
   and, with guard (a) also reverted, anonymous `/api/status` returned 200 with the store payload.
3. `RESEXTRACT_STATE_DB` does NOT redirect the dashboard's DataLayer; servers read the real store. Main
   sha/rows unchanged, but the pre-existing -shm/-wal mtimes advanced.

## Containment
Duval HEAD 6c60da5a… identical before/after, porcelain unchanged (`?? .ci-trunk.txt`, `?? .lane-j-scratch/`),
0 `.worktrees/` reads, 0 outside writes. Store sha 40e8aa0c…, v4, 35 rows identical. My ports: 8941, 8942,
8944 — all stopped and free; 8943 never bound; 0 stray processes.
