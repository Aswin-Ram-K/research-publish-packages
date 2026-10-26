# UVER27/UVER28 — verification of UOUTSIDE1 (in progress)

## Check 1 — parse_fixture.py + compare.py, tree-seven vs tree-six
Ran on COPIES under scratch/uver28/{c-seven,c-six} because `parse_fixture.py:172-177` writes `cases.json`/`blinded_cases.json`/`parse_summary.json` into its own directory, the originals lack those files, and writing into a unit tree is forbidden.
EXIT_SEVEN_PARSE=0  EXIT_SEVEN_COMPARE=0  EXIT_SIX_PARSE=0  EXIT_SIX_COMPARE=0
Identical values in BOTH trees (literal, from compare.py stdout):
routeA: agreement 0.34210526315789475, po 0.34210526315789475, pe 0.025041551246537397, kappa 0.32520740993294694, exact_index_matches 65, ties 120, zero_score_cases 41
labelsB.json: agreement 0.9052631578947369, po 0.9052631578947369, pe 0.03958448753462604, kappa 0.9013584840356494, exact_index_matches 172, n_disagreements 18, AB_mutual_agreement 0.3526315789473684, disagreements_where_routeA_backs_record 5
disagreements_count_routeB 18; disagreement_kinds {K07:6, K03:4, K05:3, K02:2, N10:2, K04:1}; disagreements_where_routeA_backs_record 5
`diff -rq c-seven/second-labeller c-six/second-labeller` -> SECOND_LABELLER_TREES_IDENTICAL
The two trees do NOT differ in second-labeller (byte-identical). Whole-tree `diff -rq`: only harness/defect-probe.py, harness/evaluate.py, harness/tcmodel.py, harness/train.py, MANIFEST.json differ. fixture/ is IDENTICAL between the trees.

## Check 2 — hand-added keys and emitted feature keys
metrics.json: both trees 7346 bytes, byte-identical. Semantic diff (regenerated vs shipped):
  metric_keys_semantically_equal = False
  keys_only_in_shipped = ['_correction', 'limitation', 'passes.labelsB.json.limitation', 'routeB_primary.limitation']
  keys_only_in_regenerated = []   (4 added keys; key ORDER also differs, non-semantic)
CONFIRMED: hand-added `limitation` (3 sites) + `_correction` (1 site) exist, and the frozen tools do NOT emit them.
disagreements.jsonl: NOT reproducible — 18 of 18 rows differ. Literal first lines:
  regen: {"id": "N01-018", "kind": "K02", "question": "A reasoner step has proposed a new capability: it needs to write the file it has just described. role.canRequestEscalation is false for reasoner. Which TYPE_A can a reasoner step transition to in order to obtain a tool it lacks?", "options": ["editor (attached, writes)", "reasoner (propose only)", "none -- no path exists"], "recorded_index": 2, "recorded_label": "none -- no path exists", "F22": 0, "F40": "editor (attached, writes)", "F56": 1, "F30": "reasoner (propose only)", "routeA_agrees_with_record": false, "routeA_agrees_with_routeB": false, "recorded_rationale": "", "line": 233}
  ship : {"id": "N01-018", "kind": "K02", "question": "A R05 step has proposed a new capability: it needs to write the file it has just described. role.F07 is false for R05. Which S15 can a R05 step transition to in order to obtain a tool it lacks?", "options": ["editor (attached, writes)", "reasoner (propose only)", "none -- no path exists"], "recorded_index": 2, "recorded_label": "none -- no path exists", "F14": 0, "F55": "R03 (R08, writes)", "F33": 1, "F31": "R07 (propose only)", "routeA_agrees_with_record": false, "routeA_agrees_with_routeB": false, "recorded_rationale": "R08 is a hard ceiling, not a policy default: the K01 path is structurally absent, so no class is reachable by K01 from R05. A newer version of the same class is not a class transition and would not carry the write grant.", "line": 273}
Feature keys the tools emit: F22/F40/F56/F30. Feature keys in the shipped file: F14/F55/F33/F31. Fields differing on N01-018: F14, F22, F30, F31, F33, F40, F55, F56, line, question, recorded_rationale.
Cause: `reflex-decisions.ts` itself contains "reasoner" 35x and `parse_fixture.py` has NO redaction map (only an unescape `.replace()` at :22) -> the shipped disagreements.jsonl was generated from a different (unredacted) fixture and is STALE.
SAME DELTA IN tree-six: CONFIRMED. tree-six disagreements.jsonl is byte-identical to tree-seven's (both 14630 bytes), same F-key mismatch; tree-six metrics.json carries the identical 4 extra keys; fixture/ identical between trees. NOTE: this means the delta is not a redaction difference between the trees.

## Check 3 — manifest checker
check_seven.py output (run from scratch/uver28, cwd-safe):
```
Traceback (most recent call last):
  File "/home/zer0null/reserach extarctor/scratch/uver28/../uoutside1/check_seven.py", line 7, in <module>
    TREE = sys.argv[1]
           ~~~~~~~~^^^
IndexError: list index out of range
```
sha256sum scratch/uoutside1/tree-seven/MANIFEST.json:
fecd31574bad62cef328d7d95b851ac338aad552c420d1b08a1126cb48cd97ef  scratch/uoutside1/tree-seven/MANIFEST.json
claimed: fecd31574bad62cef328d7d95b851ac338aad552c420d1b08a1126cb48cd97ef
check_seven.py scratch/uoutside1/tree-seven ->
```
  files[] entries                            44
  files on disk (incl MANIFEST.json)         45
  missing (listed but on-disk absent)        0
  hash mismatch                              0
  size mismatch                              0
  unlisted (on disk but not listed)          0
  listed-but-absent                          0
  files[] count == disk-1                    True
  counts.files == 45                         45
  counts.files matches disk                  True
  counts.bytes_total == 3009245              3009245
  counts.bytes_total matches disk            True
  MANIFEST.json lines=443 bytes=22709 sha256=fecd31574bad62cef328d7d95b851ac338aad552c420d1b08a1126cb48cd97ef
CHECKER: PASS
```

## Check 4 — idempotence / build-twice
Builder `build_seven.py:15` hardcodes DST to scratch/uoutside1 (outside my write paths) and `:16` guards it; literal refusal when unpatched:
```
refusing to write outside /home/zer0null/reserach extarctor/scratch/uoutside1
```
Rebuilt with DST+ALLOWED redirected to scratch/uver28 in a PATCHED COPY (scratch/uver28/build_seven_uver28.py):
```
scratch/uver28/build-a.out:9:tree digest (this build, pre-manifest-regen): 63d015b152c931e98f6855a6bd262617147047453058031200b0697f77152ef6
scratch/uver28/build-a.out:10:census inside=2171 distinct=30 (baseline 2171/30)
scratch/uver28/build-a.out:11:OK: build-a emitted at /home/zer0null/reserach extarctor/scratch/uver28/build-a
scratch/uver28/build-b.out:9:tree digest (this build, pre-manifest-regen): 63d015b152c931e98f6855a6bd262617147047453058031200b0697f77152ef6
scratch/uver28/build-b.out:10:census inside=2171 distinct=30 (baseline 2171/30)
scratch/uver28/build-b.out:11:OK: build-b emitted at /home/zer0null/reserach extarctor/scratch/uver28/build-b
diff -rq scratch/uver28/build-a scratch/uver28/build-b -> BUILD_A_EQ_BUILD_B (exit 0, no output)
```
CLAIMED 63d015b152c931e98f6855a6bd262617147047453058031200b0697f77152ef6 -> CONFIRMED, both builds, byte-identical trees.
tree-seven vs tree-seven-b: `diff -rq` reports ONLY MANIFEST.json; semantic compare:
```
equal_except_generated_utc = True
differing_top_keys = ['generated_utc']
tree-seven   generated_utc 2026-10-16T03:19:13Z
tree-seven-b generated_utc 2026-10-16T03:19:47Z
```

## Check 5 — RED->GREEN (copy at scratch/uver28/redgreen)
Baseline (pristine copy): CHECKER: PASS (exit 0)
Mutated: appended 1 byte to EXCLUDED.md (a MANIFEST-listed released file) -> exit 1, literal text:
```
  files[] entries                            44
  files on disk (incl MANIFEST.json)         45
  missing (listed but on-disk absent)        0
  hash mismatch                              1
  size mismatch                              1
  unlisted (on disk but not listed)          0
  listed-but-absent                          0
  files[] count == disk-1                    True
  counts.files == 45                         45
  counts.files matches disk                  True
  counts.bytes_total == 3009246              3009245
  counts.bytes_total matches disk            False
  FAIL hash_bad: ['EXCLUDED.md']
  FAIL size_bad: ['EXCLUDED.md']
  MANIFEST.json lines=443 bytes=22709 sha256=fecd31574bad62cef328d7d95b851ac338aad552c420d1b08a1126cb48cd97ef
CHECKER: FAIL
```
Restored EXCLUDED.md from tree-seven -> CHECKER: PASS (exit 0); `diff -rq scratch/uver28/redgreen scratch/uoutside1/tree-seven` -> RESTORED_IDENTICAL

## Containment / census
```
tree-seven before=faf5ae6022ff092e91749d81a5bae8825016273c2723363ed4aac511e193145f now=faf5ae6022ff092e91749d81a5bae8825016273c2723363ed4aac511e193145f
tree-six   before=4d74f7fd3c3fffb9b5d9ec1df113058b01010b707360b4284712795b8f0d7a6b now=4d74f7fd3c3fffb9b5d9ec1df113058b01010b707360b4284712795b8f0d7a6b
build G5 census guard (independent re-derivation): census inside=2171 distinct=30 (baseline 2171/30)
```

## Census (settled; independently re-derived, not recomputed)
`census7.txt` / `outside7.txt` (uver27) literal lines, and the build G5 guard re-derivation:
```
DISTINCT ids present: inside=30 outside=70 keys=20
TOTAL inside=2778 outside=1101 keys=120
build G5 guard: census inside=2171 distinct=30 (baseline 2171/30)
```

## Census — CARD NUMBERS DO NOT MATCH THE NAMED FILES
The card states "inside-stimulus 2,171 occurrences / 30 distinct; out-of-stimulus 1,094 occurrences / 70 distinct" and names scratch/uver27/census7.txt + outside7.txt as its outputs. Literal file contents:
  census7.txt:5   inside stimulus (question/options/situation values): 2778  distinct=30
  census7.txt:4   TOTAL OCCURRENCES (decoded walk): 3999
  outside7.txt:1  DISTINCT ids present: inside=30 outside=70 keys=20
  outside7.txt:2  TOTAL inside=2778 outside=1101 keys=120
So the DISTINCT counts match (30 / 70) but the OCCURRENCE totals in the named files are 2778 / 1101, not 2171 / 1094. The figure 2171 does appear - as `BASELINE_INSIDE` in build_seven.py and in my rebuild's guard line "census inside=2171 distinct=30 (baseline 2171/30)". 1094 appears in NEITHER file I read. Recorded as contradicted (occurrence totals) / not_reproduced for 1094; distinct counts confirmed.
