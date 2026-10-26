# VERIFICATION REPORT 35 — UVER35 (verifier of UFIX34)

Scope: records-only fix. Touched files: `orchestration/handoffs/UMERGE1.json` (frozen handoff),
`papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md` (dated change-log).
Verdict: **partial** — 6 of 7 checks pass as stated; Check 1 fails strictly for `orchestration/handoffs/UMERGE1.json` (1 changed line, not purely additive).

## 1. Additions only — PARTIAL
- `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md`: `diff scratch/ufix34/MANUSCRIPT_CHANGES.md.before papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md` = hunks `83a84,85` and `157a160,161`; `<` = 0 deleted, `>` = 4 added, 0 modified. **PASS.** Added lines (each a dated note):
  - `MANUSCRIPT_CHANGES.md:84-85` (blank + note): `> **Note 2026-10-16 (UFIX34, measured by UVER34):** the block above is the 2026-10-15 record of the *deleted* text and is retained unchanged, byte for byte. Its recital ("unsourced … therefore not cited", "four works … no locatable identifier") is **superseded and no longer current**: the counter-case is now sourced and cited as a blog post (§2.1, §6.4), and the U1 125M-RoBERTa item was sourced and merged — see \`UNSOURCED_RETAINED.md:18\` and \`submission/BUILD_NOTES.md:57\`. This is a dated historical log, not shipped prose.`
  - `MANUSCRIPT_CHANGES.md:160-161` (blank + note): `> **Note 2026-10-16 (UFIX34, measured by UVER34):** this "From" record of the 2026-10-15 text is retained unchanged and is historical — it is **not** a live statement of fact. "Therefore not cited" is superseded: the counter-case (\`simmering2025modernbert\`) is now cited as a blog post and the four-works/no-identifier recital was resolved for U1 (\`UNSOURCED_RETAINED.md:18\`, \`submission/BUILD_NOTES.md:57\`).`
- `orchestration/handoffs/UMERGE1.json`: `diff scratch/ufix34/UMERGE1.json.before orchestration/handoffs/UMERGE1.json` = hunk `68c68,78`; `<` = **1 deleted-style line**, `>` = 11. The line is **changed, not added**: before `UMERGE1.json.before:68` is `}` and after `UMERGE1.json:68` is `,`, with the object's closing brace re-emitted on the last added line `]}` (`UMERGE1.json:78`). So the handoff is **not** additions-only at line level (1 modified line: the object's closing brace consumed to append a sibling key). No *value* line was touched — the 10 new content lines are exactly the `corrections_2026_10_16` entry. Strict "0 deleted and 0 modified lines" holds for the changelog, not for this file. This is an intrinsic consequence of appending a top-level key to a JSON object.

## 2. Handoff shape / seven keys — PASS
- `orchestration/handoffs/UMERGE1.json` parses as JSON; `before_keys = ['artifacts','blocker','evidence','next_unit_hint','status','unit','write_paths']`, `after_keys =` the same **plus** `corrections_2026_10_16`; `added_only = {'corrections_2026_10_16'}`, `removed = set()`.
- All seven contracted keys present and **value-byte-identical** to the before-image (`json.dumps(value, sort_keys=True)` equality): `unit` True, `status` True, `artifacts` True, `evidence` True, `blocker` True, `next_unit_hint` True, `write_paths` True. The addition is additive; no value rewritten.
- Workspace guard **cannot run**: `python3 -m pytest tests/test_orchestration_handoffs.py -q` → `ImportError while loading conftest 'tests/conftest.py'; tests/conftest.py:19: from resextract.llm import OccamyClient; ModuleNotFoundError: No module named 'resextract'` (pytest exit 4). Per the card, I assert the seven keys myself: verified present and identical above.

## 3. No substantive claim changed — PASS
- `sha256(papers/encoder-crossover-190/MANUSCRIPT.md)` = `0ca2360cf221fe8b072811ca8da6def97b32ffad9f7c24e2cfb69d6578a89e7d` (full value read off disk; matches the `0ca2360c…` prefix).
- `sha256(papers/encoder-crossover-190/submission/main.tex)` = `0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160` (matches the required value; also matches `scratch/ufix34/main_tex_before.sha256`).
- mtime sweep over UFIX34's write window (`-newermt "2026-10-16 14:21:10" ! -newermt "2026-10-16 14:21:40"`) shows exactly 8 files, all inside declared write paths: `orchestration/handoffs/UMERGE1.json`, `orchestration/handoffs/UFIX34.json`, `orchestration/units/UFIX34.md`, `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md`, and `scratch/ufix34/{apply_fix.py,main_tex_before.sha256,MANUSCRIPT_CHANGES.md.before,UMERGE1.json.before}`. No file outside the declared write paths changed at UFIX34's write time (14:21:18). Earlier paper-dir mtimes (REFERENCES.bib/MANUSCRIPT.md 14:16:35, main.tex 14:18:52) predate UFIX34 and belong to other units.

## 4. Correction is correct — PASS
- `REFERENCES.bib:71` opens `@misc{pride2309_03882,`; its `note` field spans `:79-83` and the entry closes at `:84` (`}`); `:86` opens `@misc{gcd2305_13971,`. So `REFERENCES.bib:80-82` lies **inside `pride2309_03882`**, and `gcd2305_13971` begins later at `:86`. The pre-fix attribution was wrong; the correction is right.
- Merge claim confirmed at `:10-12`: `:10 % MERGED BY UNIT UPAPER1c (2026-10-15) from UREFS's verified additions` / `:11 % \`REFS_VERIFIED.md\`). Every added entry was observed on a page UREFS fetched on 2026-10-15.` / `:12 % pre-existing entries above are preserved unchanged.` (line 11 quoted in part; the claim block is exactly :10–12).

## 5. Annotation judgement was right — PASS
- The file is a dated historical change-log, not live prose: `MANUSCRIPT_CHANGES.md:1` `# MANUSCRIPT_CHANGES.md — UPAPER1c · what changed in \`MANUSCRIPT.md\`, sentence by sentence`; `MANUSCRIPT_CHANGES.md:3` `**Unit:** UPAPER1c. **Date:** 2026-10-15.`
- Both hits are records of *superseded* text: `MANUSCRIPT_CHANGES.md:80` `- **From (deleted in full):** the paragraph beginning *"**Unsourced in the corpus, and therefore not cited` and `MANUSCRIPT_CHANGES.md:158` `- **Body — from:** the text stating four works have no locatable identifier and that the counter-case is therefore not cited.` Deciding evidence: they sit under a "From" heading inside a dated per-unit log, so a live-fact reading is not supportable → **annotate with a dated pointer, keep every original byte** (as done). The in-place-correction alternative would have falsified a historical record.

## 6. Red→green — PASS (not vacuous)
- Dated-note probe: `grep -c 'Note 2026-10-16 (UFIX34'` → **0** on `scratch/ufix34/MANUSCRIPT_CHANGES.md.before`, **2** on `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md`.
- Correction-key probe: `grep -c 'corrections_2026_10_16'` → **0** on `scratch/ufix34/UMERGE1.json.before`, **1** on `orchestration/handoffs/UMERGE1.json`.
- The before-image still parses and still carries all seven keys (`keys-ok: True`), so the discriminating test is the correction-presence/dated-note probe, not parseability — it goes red on the real pre-fix state and green on the shipped file, which is why it is not vacuous.

## 7. Secrets — none found
- Secret-shaped scan (`api[_-]?key|secret|passwd|password|token|BEGIN … PRIVATE KEY|sk-…`) over the two verified files and both before-images hit only a DOI (`10.1007/s10579-024-09796-y`) and the phrase "output-token budgets". No credential-shaped content; nothing quoted that needed redacting. (Note: the harness's high-entropy guard redacted two write-path strings in the UFIX34 card/handoff as displayed to me; I did not attempt to recover them.)

Artifacts of the checks: `scratch/uver35/` (diff and probe outputs).
Tool calls used: 8 of 10. Hard bound: 10.
