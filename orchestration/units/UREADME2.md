# UREADME2 — correct the false manifest-state bullets in the repository README

**Workspace:** /home/zer0null/reserach extarctor
**Bound:** 15 tool calls. **Status: done** (14 used).
**Write paths:** orchestration/units/UREADME2.md, orchestration/handoffs/UREADME2.json,
scratch/ureadme2/** (clone + verify), the cloned repository's own README.md and MANIFEST.json.
**Not touched:** papers/**, /home/zer0null/Duval, workspace-root git, DOI sentences.

## Purpose
The public repo Aswin-Ram-K/research-publish-packages at main 36a82bcb had had MANIFEST.json
regenerated over its own tree, so its check already passed. But the README's integrity bullets still
asserted the OLD state (manifest mismatches on README.md, and that this is expected) and its lead-in
claimed "exactly one exception"; the file table claimed MANIFEST.json was "as published on Zenodo".
Those sentences were false.

## Sentences classified, by line (clone at 36a82bcb)
| line | sentence (abridged) | class | action |
|---|---|---|---|
| 39 | `MANIFEST.json` ... "as published on Zenodo" | (a) false | corrected: citation as published; manifest regenerated for this repo |
| 98 | "**with exactly one exception**" (README.md) | (a) false | corrected: two exceptions (README.md substituted, MANIFEST.json regenerated) |
| 102-105 | manifest is the archive's, shipped unmodified; re-hash reports README.md as a mismatch; expected | (a) false | replaced by the true primary statement; old wording kept as dated "Superseded history" |
| 106 | "The archive's README.md, and the manifest entry for it, remain authoritative on Zenodo" | (b) true | kept, shortened to the still-true half (archive README.md) |
| 108-109 | "To check any other file ... every other entry describes the file shipped here exactly" | (a) false (presupposed an exception) | corrected: every file here, README.md included |
| 111-113 | "**Update:** ... now reports zero mismatches" | (b) true | folded into the primary statement (was redundant); no longer a trailing addendum |

## Convention followed
New statement primary; false wording kept as explicitly dated "Superseded history (before
MANIFEST.json was regenerated ..., 2026-10-19)" — the date comes from the manifest's own
generated_utc 2026-10-19T04:30:53Z. Nothing silently reworded as if always true.

## Evidence (literal)
- BEFORE: check_manifest.py on the clone => all five counts 0, VERDICT PASS, exit 0;
  README.md sha256 5194f59b...a9, 6369 bytes (matched the manifest entry).
- AFTER the README edit, BEFORE regen => hash_mismatch=1 size_mismatch=1, HASH/SIZE: README.md,
  VERDICT FAIL, exit 1 — i.e. the edit did touch a manifest-listed file.
- regen_manifest.py --no-note => files_on_disk 31, bytes_total 849704, manifest_self 9fba3bf481035468,
  entries 30, added [] changed 1.
- AFTER regen => all five counts 0, VERDICT PASS, exit 0.
- DOI lines 13,14,61,64 byte-identical HEAD~1 vs HEAD.
- Remote: fresh clone scratch/ureadme2/verify @ 5554d82bb355ea709032f46cc7444da342329246 =>
  all five counts 0, VERDICT PASS, exit 0; worktree clean.

## Disagreements / extra findings (card said report them)
1. The card named only the mismatch bullets; two more class-(a) sentences existed (line 39 table row,
   line 98 "exactly one exception"). Both corrected, minimally.
2. `tools/package/check_manifest.py --package .` run from inside the clone resolves the arg against the
   workspace root, not the cwd: "FATAL: no MANIFEST.json in /home/zer0null/reserach extarctor", exit 2.
   The check must be run from the workspace root with a workspace-relative path.
3. No DOI sentence was found to be wrong from repository-internal evidence; DOI resolution was not
   attempted (out of scope, no network check of Zenodo). DOI sentences untouched.

## Consequence (accepted, inherited from UREPOMAN1)
The repository now differs from the Zenodo archive in two files (README.md substituted, MANIFEST.json
regenerated) instead of one; the README says so.
