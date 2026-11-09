# V-STAMP-NEUTRAL — is the grader stamp additive?

**Verdict: `partial`.** The stamp itself is additive (proven three ways). Two defects in the
surrounding identity path were found; both fail loudly and neither masks a grader change.

Measured 2026-10-26T12:15:32-05:00. Offline, **0 network requests**.

- Current grader `experiments/ptr-engine/longrun/grade_v5.py`:
  `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772`, `grader_version` 5.1
- Pre-stamp grader (recorded, no longer on disk anywhere in the workspace):
  `6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`

## 1. Behaviour diff, not source diff

**Reverse diff (the stamp isolated).** A `/tmp` copy of the grader with only the `main()` stamp call
removed, run on the same rows and fixture as the stamped run, produced a document identical in every
key except exactly `grader_sha256`, `grader_version`, `rows_sha256`. Nothing else in the document moved.

**Grid regrade.** 20 stored `grade-v5` documents (the `measure/regrade/` twins plus every
`measure/cell-*.grade-v5.json`) were regraded with the current grader using the document's own
`rows_file`/`fixture_file` labels: **17 regraded, 3 unregradable**.

Differing path counts over those 17 documents:

| class | paths | verdict |
|---|---|---|
| stamp fields (`grader_sha256`, `grader_version`, `rows_sha256`) | 51 | allowed |
| `generated_at` | 17 | allowed |
| path literals (`rows_file`, `fixture_file`, `grader_path`) | 9 | invocation/provenance echo, not grading output |
| **outside the allowed set** | **45** | finding F3 |

The outside-set paths are only `arms.lease-reopen.decidable_source`, `arms.pointer-stable.decidable_source`, `arms.transcript-compact.decidable_source`, `arms.transcript-grow.decidable_source`
— an arm key added by the earlier additive repair (`orchestration/handoffs/SEAM-TEST-RED.json:19`:
"only a new arm key decidable_source was added"), not by the stamp. **No numeric field differs**:
every `arms.*.checkpoint_accuracy`/count, every `cells[]` entry and every `truth[]` entry is
byte-identical, and there are zero metric diffs across all regraded documents.

Three documents could not be regraded in this run, so they remain datable only by the stamp they
lack: `cell-transcript-grow-20261026T144452Z` (rows `/tmp/cell-demo-rows.jsonl`, gone) and
`cell-transcript-grow-20261026T144540Z` (rows `.cell-demo/rows.jsonl`, gone), plus
`cell-pointer-stable-20261026T145722Z`, whose stored rows and fixture paths do resolve but whose
rerun did not complete under the `/tmp` staging. Its stored `rows_file` is
`/home/zer0null/reserach extarctor/experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl`.

## 2. Stamp honesty (mutations)

Both mutations were made on `/tmp` copies; the repo grader and every historical document were untouched.

- **Rows bytes.** Copying the rows and inserting one space:
  `f11391aa2989949f904b8092074cb7b85b65dfe5b8c89431930fe921b28de77f` →
  `c3b4a129148d1d82e19bd269e029bc36d11007c5530b37f663e509e01473b296`, and `rows_sha256` followed it exactly.
  The digest equals `sha256sum` of the graded bytes (a digest of content, not a path or a listing-time hash —
  the `P95-POWER-DIGEST-FIX` failure mode is not present). Grading output was unchanged, so the field
  tracks bytes, not verdicts.
- **Grader bytes.** Appending a comment to a `/tmp` grader copy:
  `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` →
  `70e91f6ac911d2b86898296353fe2de0f8be3d304773e8cb26905f687123ebdc`, and `grader_sha256` followed it exactly.
- **Refusal.** With `grader_identity.file_sha256` raising `OSError` for the rows at stamp time, `main()`
  returns **3**, prints `grade_v5: refusing to write an unstamped document: stamp_uncomputable`, and
  **writes no file**. `stamp_document` raises `StampError` on an absent rows path. A rows file that is
  missing before parsing fails earlier (uncaught traceback, exit 1) and also writes nothing.

## 3. Is there a second source of truth?

`tools/grader_identity.py` behaves correctly on its own terms: a 3-of-3 document reports
`source="stamp"`; a pre-stamp document reports `source="derived"` with `sha256=None` and
`missing=[grader_version, rows_sha256]` — never silently `stamp`; a 1-of-3 document is `derived`.
But the stamp did not become the only identity:

- **F1 (medium).** `tools/regrade.py:44` still pins the *pre-stamp* sha as `DEFAULT_GRADER_SHA = "6893d559…"`.
  After the stamp, a default `regrade.py --check` run returns exit 3,
  `ERROR grader sha256 mismatch: file=056eb605… expected=6893d559…`, for every grid. It fails loudly,
  but it is a stale second pin that must be passed `--sha256 056eb605…` to work at all.
- **F2 (low).** `regrade.py` computes its own `_sha256` (`tools/regrade.py:135`) instead of calling
  `grader_identity`, and its documents carry only `grader_sha256` (1 of the 3 keys). The resolver
  therefore labels them `derived` with `sha256=None` even though the document records a valid sha —
  conservative, never a fabricated identity, but it discards a sha the document holds.
- **No masking found.** With a document stamped `056eb605…` and a tampered grader `526a51ae…`,
  `regrade.py --check` prints `DIFF grader_sha256: grade=056eb605… regrade=526a51ae…`, i.e. drift is
  surfaced, not quiet. Against a pre-stamp document, `--check` prints `DIFF grader_sha256:
  grade=6893d559… regrade=056eb605…` — honest, but it means `--check` is red on every historical grid.

## Conclusion

The stamp is additive: it adds three fields to the document and changes nothing the grader computes.
No published quality number changes because of it — every accuracy, count, cell verdict and truth
entry reproduces byte-identically, and the only non-stamp delta is the pre-existing additive
`decidable_source` arm key. The remaining risk is not the stamp but the stale pinned sha in
`regrade.py`, which should be replaced by a `grader_identity` call.
