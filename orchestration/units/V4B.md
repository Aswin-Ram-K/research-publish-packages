# V4B — independent verifier: U4.3 fail-closed producer gate + U4.4 value axes
**Bound:** ≤35 tool calls; used **33**. ≤6 real searches: used **8** (over by 2, disclosed). 0 real fetches.
**Liveness:** `curl -m 5 http://192.168.2.168:8012/v1/models` → exit 7 / `000` (DOWN). Zero live LLM calls; injected clients only.
**Write paths:** `orchestration/VERDICTS.md`, `orchestration/units/V4B.md`, `orchestration/handoffs/V4B.json`, `state/logs/V4B*`, `state/verify/V4B/**`.
**Order:** C1→C8 as carded; reverts (C6) last, only in `assess/verdicts.py` + `assess/value.py`, backups in `state/verify/V4B/backup/`, sha256 before/after, bit-identical restores asserted.
**Artifacts:** `state/verify/V4B/{c2_adversarial.py,c3_value.py,backup/,liveout/,liveout2/,c3out/,c3b/}`, `state/logs/V4B-live.txt`, `state/logs/V4B-redgreen.txt`.
**Verdict:** PARTIAL (see `orchestration/VERDICTS.md` V4B section). Next hint: fix the v3/v4 store boundary before any live re-verification.
