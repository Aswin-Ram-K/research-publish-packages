# STALE_RECORD_FIX.md — UFIX28

**Scope.** Regenerate the shipped `second-labeller/disagreements.jsonl` mechanically from the shipped
fixture; decide on `metrics.json`'s four extra keys (recommendation only — acted on nothing); reconcile the
2,171 vs 2,778 census totals in one section. RC tree = `scratch/uoutside1/tree-seven`; all mutation done on
a copy at `scratch/ufix28/tree-seven`. No other unit's tree was modified.

---

## JOB 1 — the stale record, regenerated mechanically

### How the shipped tools produce `disagreements.jsonl`
`second-labeller/parse_fixture.py` parses `fixture/reflex-decisions.ts` (`SRC`, `parse_fixture.py:16`) and
writes **into its own directory** (`parse_fixture.py:172-177`): `cases.json`, `blinded_cases.json`,
`parse_summary.json`. `second-labeller/compare.py` then reads `cases.json` + every `labelsB*.json`
(`compare.py:79`), keys the catalogue on the primary pass `labelsB.json` (`compare.py:148-155`), and writes
`disagreements.jsonl` (`compare.py:176-178`) plus `metrics.json` (`compare.py:184-185`). The four
anonymised feature keys it emits are hard-coded: `"F22": b, "F40": options[b], "F56": A_idx[k],
"F30": A_lbl[k]` (`compare.py:162-163`).

Because both scripts write in-place, the pipeline was run on the copy:
`cp -a scratch/uoutside1/tree-seven scratch/ufix28/tree-seven`, then
`python3 parse_fixture.py && python3 compare.py` in `scratch/ufix28/tree-seven/second-labeller/`.
**No field was hand-edited.** Exits: `parse_exit=0`, `compare_exit=0`.

### Row count and disagreement count

| | before (shipped) | after (shipped tools) |
|---|---|---|
| rows in `disagreements.jsonl` | 18 | 18 |
| `metrics.disagreements_count_routeB` | 18 | 18 |
| ids, in order | `N01-018 … N06-023` | identical, same order |

Disagreement COUNT does **not** change: 18 → 18, same 18 ids. 18 of 18 rows differ in content.

### Literal before/after (row 0, id `N01-018`)
- keys — before `['id','kind','question','options','recorded_index','recorded_label','F14','F55','F33','F31','routeA_agrees_with_record','routeA_agrees_with_routeB','recorded_rationale','line']`
  → after `['id','kind','question','options','recorded_index','recorded_label','F22','F40','F56','F30','routeA_agrees_with_record','routeA_agrees_with_routeB','recorded_rationale','line']`
- question — before `'A R05 step has proposed a new capability: it needs to write the file it has just described. role.F07 is false for R05. Which S15 can a R05 step transition to i…'`
  → after `'A reasoner step has proposed a new capability: it needs to write the file it has just described. role.canRequestEscalation is false for reasoner. Which TYPE_A …'`
- `recorded_rationale` — before `'R08 is a hard ceiling, not a policy default: the K01 path is structurally absen…'`
  → after `''` (empty)
- `line` — before `273` → after `233`
- `recorded_index`/`recorded_label` unchanged (`recorded_label` = `'none -- no path exists'` both sides).

Aggregate over all 18 rows (mechanically measured):
`rows_with_changed_question=3`, `changed_line=18`, `changed_rationale=18`, `changed_keyset=18 of 18`;
`before rationale nonempty: 18` → `after rationale nonempty: 0`;
line range `2175 … 273` (before) → `2135 … 233` (after) — every line shifts by the same −40.
Only 3 questions changed text (the other 15 rows differ only in keys/line/rationale).

### Do any figures in `papers/encoder-crossover-190/` move?
**No.** `metrics.json` shared values changed **0** (`CHANGED_SHARED_VALUES: 0`), and the disagreement count
stays 18, so every figure derived from those two files is invariant. A literal scan of the paper directory
for the stale artefacts found no hit: `grep -rn "F14\|F55\|F33\|F31\|R05 step\|hard ceiling\|structurally
absen\|2171\|2778\|1094\|1101" papers/encoder-crossover-190/` returned one unrelated hit (the token
`1094` inside the parameter count `109489537` in `EVIDENCE_NOTES.md:322`). No paper text quotes a stale
question, a stale rationale, an F-key, or a line number. **Nothing to stop for.**

### `metrics.json`'s four extra keys — additive, not value-bearing
`EXTRA_IN_BEFORE` = `/ _correction`, `/limitation`, `/passes/labelsB.json/limitation`,
`/routeB_primary/limitation`; `EXTRA_IN_AFTER` = `[]`. All four are additive annotations.

**Recommendation: KEEP the four keys, but mark them hand-curated — do not let a bare regeneration stand.**
Reason: `compare.py:6-7` freezes Route A and the tool never emits these keys, so a mechanical regeneration
silently deletes disclosed limitations (`limitation` notes are disclosure content). The honest fix is a
thin, versioned post-processing step — or an explicit `metrics.json` preamble stating the four keys are
hand-curated additions to the tool output — so the four keys reappear *and* the hand edit is declared.
Removing them is a disclosure regression; keeping them undeclared is a provenance defect. **No action was
taken on `metrics.json`**; the four keys survive only in
`scratch/ufix28/before_metrics.json` and in the shipped tree, which was not modified.

### Manifest regeneration (because two files changed on the copy)
`scratch/ufix28/regen_manifest.py` is UOUTSIDE1's `regen_manifest.py` with the tree base changed
(`"scratch","uoutside1"` → `"scratch","ufix28"`). Two consecutive builds produced identical `files[]`
sha256 maps (`files_listing_identical_between_builds: True`, n=47). Independent checker
`scratch/uoutside1/check_seven.py scratch/ufix28/tree-seven`:

```
files[] entries 47 | files on disk (incl MANIFEST.json) 48
missing 0 | hash mismatch 0 | size mismatch 0 | unlisted 0 | listed-but-absent 0
counts.files == 48 | counts.bytes_total == 3162709
MANIFEST.json lines=464 bytes=23648 sha256=f4f4b3741e9c82325096c598f5c18eebb7450f88f9d9d52d3ec2fed92317581c
CHECKER: PASS
```

`counts.bytes_total = 3162709`. Regenerated-artifact digests:
`disagreements.jsonl` sha256 `d9d1f33bf3d12d74cba7160b8b981b593af8f5b09b8a6dd2b9e48f9c21f647b3`
(same on build 2), `metrics.json` sha256 `5d05dd13c51b55465cee0f4ff4d3e01645fad9ee1a2e9ff25b5e99fd0ddc726`
(same on build 2) — **idempotent**. The 3 added `files[]` entries are the parse intermediates
`second-labeller/{cases,blinded_cases,parse_summary}.json`; the 2 changed hashes are
`disagreements.jsonl` + `metrics.json`. The manifest line `generated_utc` is a timestamp, so the manifest
file's own bytes are not bit-stable across runs, but its `files[]`/`counts` are (verified above).

---

## JOB 2 — census totals reconciled (one section)

**The 2,171 and 2,778 figures do not come from two definitions. They come from two different file sets.**
All three census scanners agree exactly when run on the same tree:

| scanner | inside | outside | keys |
|---|---|---|---|
| `scratch/ubij1/census_one.py` on 45-file shipped tree | **2171** | **1094** | 78 |
| `scratch/uver13/census_uver13.py` on the same tree | **2171** | — | 78 |
| `scratch/uoutside1/outside_scan.py` on the same tree | **2171** | **1094** | 78 |

The shared inside rule is identical in each: *decoded JSON/JSONL walk; a string VALUE is inside-stimulus iff
its immediate parent key is in `{"question","options","situation"}`; list elements inherit the parent key;
JSON object keys are counted separately; non-JSON files are all outside.* See
`scratch/ubij1/census_one.py:21` (`PROSE = {"question","options","situation"}`) with the split at
`census_one.py:114-121` (`cl()`: `tgt = inside if k in PROSE else outside`) and the non-JSON fallback at
`census_one.py:136-142`; and `scratch/uver13/census_uver13.py:10` (`STIM = {...}`) with
`census_uver13.py:80` (`walk(v, in_stim or (k in STIM))`) and the split at `census_uver13.py:88-92`.
**There is no scanner line that produces 2,778.**

The 2,778 comes from the tree state. `scratch/uver27/census7.txt:2` records `files scanned: 48`; the
shipped tree has **45** files. The extra 3 are exactly the `parse_fixture.py` intermediates
(`cases.json`, `blinded_cases.json`, `parse_summary.json`), which are second copies of the fixture's
question/option text. Reproduced on a fresh copy of the shipped tree:

- 45 files (shipped) → `inside stimulus …: 2171 distinct=30`, `outside …: 1094` (`census7.txt:5` class
  profile matches: data-jsonl 1221 / json 932).
- shipped + `cases.json` only → `inside: 2470` (**+299**).
- shipped + all three intermediates (48 files) → `inside: 2769`, `outside: 1094`, keys 120 — the json class
  jumps 932 → 1530, identical to `census7.txt:12` (`json inside=1530`) and `census7.txt` keys=120. The
  remaining `2769→2778` inside / `1094→1101` outside (9 and 7) sit entirely in the `data-jsonl-other`
  class, i.e. the content of `disagreements.jsonl` as it stood when `census7.txt` was produced
  (`census7.txt:11` `data-jsonl-other inside=27 outside=7` vs `18/0` today) — a changed input file, not a
  changed definition.

**Which definition is the published one.** The decoded-walk inside rule is the one behind the package's
other published census figures: `scratch/uneutral4/residual-floor.txt:1` reads
`pinned: inside-stimulus occurrences=2171; outside-values=11267; json-keys=3375; total=16813`, and
`census_one.py:4-6` names that 16,813 / 9,247 / 5,384 walk as the "Money number". Both other independent
scanners reproduce 2,171 on the shipped tree, so the 2,171 definition is the consensus one.

**Quote going forward: `inside-stimulus occurrences = 2,171` and `outside-value occurrences = 1,094`
(plus `78 JSON object keys`), labelled** *"decoded-value walk over the shipped 45-file tree
`scratch/uoutside1/tree-seven`; inside = values of `question`/`options`/`situation`"*. Do **not** quote
2,778 / 1,101: those are the same census over a 48-file tree that still contained the `parse_fixture.py`
intermediates, i.e. a double-count of the stimulus text, not a wider definition.

---

## Verdict / handoff
- `disagreements.jsonl`: stale confirmed and regenerated mechanically; 18 → 18 rows, 18/18 rows corrected,
  no paper figure moves. Regeneration recipe + digests above. **Shipped tree left unmodified** (copy only).
- `metrics.json`: four extra keys are purely additive; **recommend keep-and-annotate-as-hand-curated**;
  no action taken.
- Census: 2,171/1,094 is the quote-forward figure; 2,778/1,101 is a 48-file-tree artifact. No scanner
  definition differs.

### Evidence commands (exact)
```
cp -a scratch/uoutside1/tree-seven scratch/ufix28/tree-seven
cd scratch/ufix28/tree-seven/second-labeller && python3 parse_fixture.py && python3 compare.py
wc -l < disagreements.jsonl                       # 18 (before and after)
python3 scratch/uoutside1/check_seven.py scratch/ufix28/tree-seven
grep -rn "F14\|F55\|F33\|F31\|R05 step\|2171\|2778" papers/encoder-crossover-190/
python3 scratch/ubij1/census_one.py scratch/ufix28/censustest          # 2171/1094 on 45 files
python3 scratch/uver13/census_uver13.py scratch/ufix28/censustest A    # 2171 inside
python3 scratch/uoutside1/outside_scan.py scratch/ufix28/censustest    # 2171/1094
(cd scratch/ufix28/censustest/second-labeller && python3 parse_fixture.py)
python3 scratch/ubij1/census_one.py scratch/ufix28/censustest          # 2769/1094 on 48 files
```
