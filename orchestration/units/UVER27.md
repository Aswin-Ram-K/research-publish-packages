# UVER27 — independent verifier for UOUTSIDE1

**status:** partial
**blocker:** verification just started; this skeleton exists so a mid-run death is diagnosable.
**role:** verifier (did NOT author UOUTSIDE1)
**target:** `scratch/uoutside1/tree-seven` (45 files); control `scratch/utool1/tree-six` (unredacted)
**bound:** 25 tool calls

## planned checks (from unit card)
1. re-run `scratch/uoutside1/check_seven.py`
2. `python3 verify/recompute-claims.py` in tree-seven — exit code, claim-numbers line, fixture digest
3. second-labeller tools in tree-seven AND tree-six — exit codes, kappa/agreement/exact/ties/disagreements
4. independent re-derivation of 1,094 occurrences / 70 distinct mechanism ids
5. `\n`+"kind" artifact claim at `harness/prepare.py:148`, `harness/tccommon.py:118`, `harness/prepare.py:177`
6. `second-labeller/metrics.json` not current tools' output (hand-added limitation/_correction keys)
7. manifest checker: counts.files, counts.bytes_total, MANIFEST.json sha256
8. idempotence: build-again digest 63d015b1...2ef6; only MANIFEST.json differs, only generated_utc
9. inside-stimulus census unchanged (2,171 / 30)
10. RED→GREEN on a copy under scratch/uver27/

## progress log
- (in progress)
