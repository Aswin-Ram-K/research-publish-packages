# VPKGFINAL7 — independent verification of Paper #7 final deposit archive

**Verdict: FAIL** — one blocking residual leak. Everything else re-derived green.
**Bound:** 25 tool calls (used 24). **Frozen:** `papers/gated-read-batching/released/gated-read-batching-released.tar.gz`
+ payload. Work done on copies in `scratch/vpkgfinal7/`. No git command run anywhere. Shipped artifact sha256
re-checked after the rebuild and unchanged.

## Re-derived from bytes

| # | claim | result | evidence |
|---|---|---|---|
| 1 | 126,639 B / sha256 0e70ba54… / md5 e2af1616… / members / one top dir | PASS | `126639 bytes`; `0e70ba54…b99b6a85`; `e2af1616b64f7ca54b9bf61e60427785`; `tar tzf \| wc -l` = 16 (12 files + 4 dirs); `awk -F/ '{print $1}' \| sort -u` = `gated-read-batching-released` |
| 2 | check_manifest on payload + extraction → 5 counters 0, PASS, exit 0 | PASS | both: `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0` / `VERDICT PASS` / `exit=0`; payload dir `diff -r` extraction = identical |
| 3 | recompute-claims 49/49 PASS exit 0 | PASS | `checks: 49 passed: 49 failed: 0` `VERDICT: PASS` `exit=0` |
| 4a | rows 2,267,742 B / 9,260 lines | PASS | `2267742 bytes`, `9260` |
| 4b | `2026-09-28-trace-m0` ×4 only on 9195/9196/9198/9200 | PASS | `grep -c` = 4; `grep -n` = 9195, 9196, 9198, 9200; arms selfselect / gate_min / stage / stage_route, mode e2e, task T10 |
| 4c | no `2026-09-28-duval` / `duval-m0` / `-duval-` / `duval` (lowercase) | PASS (literal) | each `grep -rIl` = 0 |
| 5 | R5 figures + run-report claims unchanged; results md + summary json byte-identical | PASS | md5 identical pre→post: `fe1b900525c63ad0c1ee546d23370c6e` (GATED_READ_2026.md), `9bba213e4772692a7eccc7cf13715202` (summary json); recompute checks 15.279 / 0-of-20 / 20-of-20 all OK |
| 6 | leak grep, target zero | **FAIL** | `scratch/`0 `tools/package/`0 `papers/`0 `state/refresh-verify`0 `/home/`0 unit ids 0 — but **`data/gated-read-rows.jsonl:9235` and `:9239` carry `"answer": "DUVAL_HOSTED_LAYER_OK"`** (2 occurrences, uppercase, `grep -i duval` = 2 lines) |
| 7 | recipe reproduces archive byte-for-byte, no prior-archive dependency | PASS | ran it with output redirected to `scratch/vpkgfinal7/rebuild/` (script unmodified except REL/PAYLOAD/OUT/W): `built k=1: 126639` `built k=2: 126639` `cmp: out1 == out2`; produced sha256 `0e70ba54…` == shipped, `cmp` identical |
| 8 | red→green | PASS (checker) / not reproduced (recompute) | flipped 1 byte in rows → `HASH: data/gated-read-rows.jsonl`, `hash_mismatch=1`, `VERDICT FAIL`; restored → `VERDICT PASS`, recompute `49/49`. The recompute on the corrupted copy died with `json.decoder.JSONDecodeError: Expecting ':' delimiter: line 1 column 105` — **not** 48/49 |

## Beyond the report

- **Licence: PASS.** PolyForm body = lines 5–135, exactly **4,563 bytes, sha256 ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8** — matches the claim and the file's own recorded digest.
- **Digests documents state about their own files: one wrong.** MANIFEST.json: all 11 entries verify (12 files, 2,374,092 B total). README table rows verify for rows (`93acbf2e…` / `b063fbae…`), summary (`9bba213e…` / `496666c4…`) and `GATED_READ_2026.md` (`fe1b90…` / `17ac3c4c…`). But the `GATED_READ_PROVENANCE.md` row prints **31,679 B / `ba9f78dd…` / `0aca7cdb…`** while the shipped file is **31,562 B / `cfc81ef6…`** — a stale row left under a sentence that now says the digests "of the bytes shipped here" are listed.
- **"Exactly what the paper's §7 says": premise does not hold.** §7 of the paper is *Conclusion* (`MANUSCRIPT.md:213`, `main.tex` `\section{Conclusion}` at :247) and enumerates no files; the paper has no data-availability section. Measured instead against `README.md` "What ships" / `README_DEPOSIT.md` "What ships": both list **10 of the 12** shipped files — `CITATION.cff` and `README_DEPOSIT.md` are unlisted.
- **+792 bytes of dated notes.** `126,639 − 125,847 = 792` is the *compressed* delta. Raw additions are README.md **+1,188 B**, `verify/recompute-claims.py` **+239 B**, `MANIFEST.json` **+1 B** (rows unchanged) = **+1,428 B** of prose. The notes themselves are accurate: four rows, one per R5 arm, equal-length 20→20 char swap, size/lines unchanged, superseded `3aad1ae2…` / `5732766d…` correctly labelled as the source-tree values. The one wrong statement is the residual-byte claim implied by the sweep ("the target name is gone") — two `DUVAL_HOSTED_LAYER_OK` answers remain.
