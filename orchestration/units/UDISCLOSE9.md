# UDISCLOSE9 — name the AI tools in the *Use of AI tools* disclosure

Owner: unit UDISCLOSE9. Workspace `/home/zer0null/reserach extarctor`. Parent: `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.

## Purpose
Establish from records, not memory, which models actually served as AI assistants; install the final
first-person *Use of AI tools* paragraph (one paragraph; the other five declaration headings untouched) with
the `<tool, version, month>` slot filled; prove the edit changed no number.

## Distinction kept
- **AI as assistant** — designing/running the analysis and writing/editing the text. This is the disclosure.
- **A model as an instrument inside the experiment** — the second-labeller study (reader B2 =
  `mimo-v2.6-flash`). That is a methodological component and stays in the methods; it was not moved here.

## Rules honoured
`/home/zer0null/Duval` never touched (no `git`). `submission/main.tex` regenerated only, never hand-edited
(`python3 tools/package/md2tex.py --package encoder-crossover-190`). No measured number, claim, reference or
bibliography entry changed. Nothing written outside the workspace.

## Hard bound and write paths
Bound: 18 tool calls (used 17). Wrote only: `papers/encoder-crossover-190/MANUSCRIPT.md`,
`.../submission/main.tex`, `.../submission/encoder-crossover-190.tar.gz`, `.../submission/BUILD_NOTES.md`,
`.../rendered/encoder-crossover-190.pdf`, `orchestration/units/UDISCLOSE9.md`,
`orchestration/handoffs/UDISCLOSE9.json`, `scratch/udisclose9/**`.

## Job 1 — model names, from records
Read-only scan of `/home/zer0null/.dsh/storages/session_projcache/sessions/*.json`, filtered to
`record.identity.cwd == /home/zer0null/reserach extarctor`: **514** session records, every one with
`rows.modelSelection.val.provider == "keyring"` and `lastUsed.model`:

| model | sessions |
|---|---|
| `deepseek-v4.1-flash` | 487 |
| `step-5-preview-free` | 14 |
| `mimo-v2.6-flash` | 13 |

`subagentModelSelectionPolicy` pool in all 514: those three plus `longcat-2.5-preview-free` (0 last-used).
`identity.createdAt` spans `2026-10-08T09:48:53Z` .. `2026-10-17T20:30:45Z` — all 2026-10. The harness is
**DeepSeek Harness** (store root `/home/zer0null/.dsh/`; checkout `/home/zer0null/deepseek-harness/`,
`@deepseek-ai/dsh-root` 0.1.7-rc.2). This session's own runtime route is `deepseek-v4.1-flash`.

**Not provable:** no record names one model as *the* assistant for this manuscript or allocates drafting to a
model. The `lastUsed` distribution is the strongest record available, not a per-task attribution.
`mimo-v2.6-flash` is additionally the second-labeller instrument (`orchestration/handoffs/UEXP2.json`:
`"model":"mimo-v2.6-flash (keyring/mimo-v2.6-flash), 2026-10-15; labelsB.json records no model id"`) — that
fact belongs in the methods.

## Job 2 — paragraph as installed
Heading unchanged; body replaced in `MANUSCRIPT.md` and shipped at `main.tex:447`:

> **Use of AI tools.** In October, I used large language models through DeepSeek Harness (chiefly
> `deepseek-v4.1-flash`, with `step-5-preview-free` and `mimo-v2.6-flash` as subagent routes) in two ways: to
> help design and implement the analysis and the experiment, and to help draft and edit this manuscript. The
> research idea, the experimental design, and all editorial decisions are my own. I checked and verified all
> AI-assisted output, and I take full responsibility for the entire content of this paper. The AI systems are
> not authors and are not credited as contributors.

The bare year is deliberately not printed: under the precedent's numeric regex
`(?<![\w.\-])\d+(?:\.\d+)?(?![\w])` digits glued to word characters (`v4.1`, `step-5`, `v2.6`) are ignored,
but a standalone `2026` is a literal — probe `October 2026` adds exactly one (`2026`).

## Job 3 — proof
- Two regenerations byte-identical: `main.tex` 84223 B, sha256
  `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`, 467 lines.
- Tarball 28556 B, sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed`,
  exactly 1 member `main.tex`, byte-identical to the shipped file.
- Numeric invariance (bibliography stripped): pre 763 / post 763 / **shared 763, added 0, removed 0**;
  full-file multiset also identical. Pre copy `scratch/udisclose9/pre/main.tex`.
- `tectonic -r 1 --keep-logs` (cache/TMPDIR/HOME inside the workspace, no `-Z continue-on-errors`):
  literal exit code **0**, `Undefined control sequence` **0**, LaTeX `!` **0**.
- PDF installed: 184933 B, sha256 `58c22c906d0220fb707eed538bf13bf33304a4b2751b033e0d4a0c71bce7fd44`,
  25 pages, 595.28 × 841.89 pts (A4).
- Paragraph verbatim in the installed PDF's extracted text = **True** (hyphen/ligature/whitespace-invariant);
  author-name count 1; `AUTHOR SLOT` 0; `AUTHOR TO CONFIRM` 0.
- `\author` lines 1 = `\author{Aswin Ram Kalugasala Moorthy}`; `\bibitem` 13; `\cite` occurrences 23;
  distinct cited 13; uncited 0; unresolved 0.
- `PYTHONPATH=src python3 -m pytest tests/test_md2tex.py -q` → `7 passed in 0.68s`.

## Re-run note and trap
A **prior UDISCLOSE9 run** had already appended a BUILD_NOTES section (identical `main.tex`/tarball hashes,
PDF sha256 `49c96ca7…`) and installed its PDF, but wrote no handoff, and `MANUSCRIPT.md`/`main.tex` had
reverted to the pre-edit bytes. The duplicate section appended by this re-run was removed; the surviving
section carries a dated correction with the current PDF hash and keeps the old value as history.

Trap for any verifier: a verbatim check that de-hyphenates by deleting `-` + newline reports **False** — LaTeX
hyphenates words the source does not, and that rule also eats the source's own hyphen in `sub-agent`. Drop
hyphens on **both** sides instead.
