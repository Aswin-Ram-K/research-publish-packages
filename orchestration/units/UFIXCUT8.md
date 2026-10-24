# UFIXCUT8 — gated-read release: honest headline + verifier corrections

**Workspace:** `/home/zer0null/reserach extarctor` · **Bound:** 15 tool calls · **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## Purpose (one)
Correct the gated-read release artifact (`scratch/urelease7/cut3/**`, 5 files) and the document that
describes it (`strategy/GATED_READ_RELEASE_CUT.md`), acting on UCLAIM7's cross-check
(`strategy/CLAIM_CROSSCHECK_7.md`) that established 136/143 expectations anchored, 4 derived, 3 orphans
(the sealed figures `0.575` and `207`), i.e. the honest headline is **140 of 143 recomputable; 3 sealed**.

## Declared write paths
- `scratch/urelease7/cut3/**` (the 5-file release artifact)
- `strategy/GATED_READ_RELEASE_CUT.md` (append own dated note; do NOT touch UVEREL7/UFIXCUT7 notes)
- `orchestration/units/UFIXCUT8.md`, `orchestration/handoffs/UFIXCUT8.json`
- `scratch/ufixcut8/**` (recovery copy + failure-test copy)

## Read-only constraints
- `/home/zer0null/Duval` strictly read-only, and **no `git` command against it at all**.
- Do not edit `papers/**`. Never quote withheld literals (payload tokens, answer strings, private
  paths, model ids).

## Plan
1. Byte copy of `scratch/urelease7/cut3/` → `scratch/ufixcut8/cut3-before/` (done, `diff -r` clean).
2. Persist this card first.
3. Read `strategy/CLAIM_CROSSCHECK_7.md` + tail of the release doc.
4. **Fix 1:** `R1-F1-[MODE-4]` stale `0.210` → corrected `0.211` (56/266 = 0.210526) with explicit tight
   tolerance; prove PASS on current record and FAIL on a copy under `scratch/ufixcut8/` forced back to
   `0.210`; record literal messages.
5. **Fix 2:** honest headline ("140 of 143 recompute; 3 sealed") in the release doc + shipped `METHOD.md`
   (+ wording of `sealed.json` if a reader could mistake the constants for verified values). Keep
   anchored-in-the-main as the good news.
6. **Fix 3:** (a) `gold_derivation` claimed covered but 0 occurrences in verifier — check or de-claim;
   (b) R5 ASR row published for six arms, only `[ARM-6]` checked — extend if data carries the rest, else
   say so; (c) four-decimal accuracy constants have no four-decimal published source — align or note;
   (d) "per-arm files" vs `units_mean` mismatch — report, fix only if unambiguous; (e) file-exposure vs
   context-carry is resolved (ARM-5 `0` correct) — wording only.
7. Re-run verifier (literal exit code, PASS/NOTE/FAIL counts), new md5 table (old values superseded, not
   deleted), internal-consistency check, second run byte-identical, report unverifiable items.

## Stop condition
If a fix cannot be supported by evidence within the bound, record `partial` with the remainder named
rather than guessing.
