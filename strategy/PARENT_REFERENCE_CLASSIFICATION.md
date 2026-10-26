# PARENT_REFERENCE_CLASSIFICATION — UFIXPKG6 (report-only)

Scope: (A) parent-project references under `papers/encoder-crossover-190/`; (B) bare labels in the
released payload `scratch/uneutral10/package/`. Nothing outside `strategy/PARENT_REFERENCE_CLASSIFICATION.md`,
`orchestration/units/UFIXPKG6.md`, `orchestration/handoffs/UFIXPKG6.json`, `scratch/ufixpkg6/**` was written.
No `git` command was run against `/home/zer0null/Duval`; the single target access was a read-only `grep -rl`.

## 0. Headline facts (measured, and they change the ruling)

1. **The released artifact contains exactly ONE `docs/research/…` reference, and it is generated.**
   `tar -tzf papers/encoder-crossover-190/submission/encoder-crossover-190.tar.gz` → literal output: `main.tex`
   (one entry, nothing else). The other 20 of the 21 lines are **workspace working documents**, not shipped.
   Regeneration path is `scratch/uprep1/md2tex.py` (per `orchestration/units/UFIXPKG5.md:81-83`).
2. **The reported counts are partly stale.** Measured in the payload: `P01` = **0** (card/UFIXPKG5 said ×1 —
   UFIXPKG5 itself fixed the last bare `P01:47`, `orchestration/units/UFIXPKG5.md:89`); `P05` = **6** (said ×7);
   `D42` = **0** (said present — replaced in the prereg, `orchestration/units/UFIXPKG5.md:24`); `P04` = 10 ✓.
3. **The 21-count is a `docs/research`-only count.** The wider parent-path class also reaches the released
   artifact — measured hits at `papers/encoder-crossover-190/submission/main.tex:230,335,387,412,419`
   (`strategy/…`, `PAPER\_CANDIDATES.md`, `experiments/second-labeller-190/…`, kernel/runtime). This is the
   same "searched only the known form" failure the card warns about; those rows are class (iv) below.
4. **`D-067` is a genuine target decision-log id, and it is a deliberate citation** — not an exposure
   (§B-findings). **`D43` is a minted neutral tag**, so `see D43 §3` is a dangling pointer — the one real
   list-B defect.

## 1. Method — the commands whose literal output the counts come from

```
grep -rn "docs/research" papers/encoder-crossover-190/ --include=*.md --include=*.tex --include=*.bib --include=*.txt
grep -ro "docs/research" papers/encoder-crossover-190/ --include=*.md --include=*.tex --include=*.bib --include=*.txt | wc -l   # → 22
grep -rc "docs/research" papers/encoder-crossover-190/ --include=*.md --include=*.tex --include=*.bib --include=*.txt
grep -rnE "experiments/|kernel/|EXP#[0-9]+-evidence" papers/encoder-crossover-190/ --include=*.md --include=*.tex
grep -rhoE "\bP0[0-9]\b|\bD-?[0-9]{2,3}\b|\b[SFG][0-9]{2}\b" scratch/uneutral10/package/ | sort | uniq -c | sort -rn
tar -tzf papers/encoder-crossover-190/submission/encoder-crossover-190.tar.gz
timeout 30 grep -rlE "D-067" /home/zer0null/Duval --include=*.md --include=*.json     # read-only; no git
```

**Literal result of the count command: `22` occurrences on `21` lines.** Per-file line counts (only non-zero):
`submission/main.tex:1`, `REFS.md:3`, `CLAIMS.md:1`, `CHECKLIST.md:1`, `MANUSCRIPT.md:1`,
`EVIDENCE_NOTES.md:10`, `DISCLOSURE_CHANGES.md:1`, `LICENSE_ANALYSIS.md:2`, `GAPS.md:1` → **21 lines**.
22 occurrences because `LICENSE_ANALYSIS.md:433` carries two on one line. So "21" is the line count and is
correct; a count of the *string* is 22.

## 2. List A — the 21 lines, classified

Class key: (i) documented disclosure (record named) · (ii) necessary citation · (iii) unnecessary exposure ·
(iv) ambiguous.

| # | file:line | token as written | quoted context (≤1 line) | class | generic replacement |
|---|---|---|---|---|---|
| 1 | `papers/encoder-crossover-190/submission/main.tex:146` | `docs/research/EXP\#11-evidence/decider-rows.jsonl` (**TeX-escaped** `\#`) | `per-case rows survive in \texttt{docs/research/EXP\#11-evidence/decider-rows.jsonl}` | **(iii)** — the only occurrence inside the released artifact; a private path is unreachable to a reader | `the target repository's per-case decider rows` — then regenerate via `python3 scratch/uprep1/md2tex.py` and rebuild the tarball |
| 2 | `papers/encoder-crossover-190/MANUSCRIPT.md:301` | `docs/research/EXP#11-evidence/decider-rows.jsonl` | `**Yes** — per-case rows survive in \`docs/research/EXP#11-evidence/decider-rows.jsonl\`` | **(iii)** — source line of row 1 | same phrase; keeps the artifact's identity, drops the private path |
| 3 | `papers/encoder-crossover-190/GAPS.md:106` | `docs/research/EXP#11-evidence/decider-rows.jsonl` | `the **only** 4B figure with **per-case rows in the tree** (\`docs/research/EXP#11-evidence/decider-rows.jsonl\`)` | **(iii)** | same phrase |
| 4 | `papers/encoder-crossover-190/EVIDENCE_NOTES.md:160` | `docs/research/EXP#11-evidence/decider-rows.jsonl` | `` `docs/research/EXP#11-evidence/decider-rows.jsonl`. `` | **(iii)** | same phrase |
| 5 | `papers/encoder-crossover-190/CLAIMS.md:5` | `the read-only target repository/docs/research/EXP#12-evidence/` | `Evidence tree root (read-only): \`the read-only target repository/docs/research/EXP#12-evidence/\`.` | **(iii)** — the repo is already generic; the appended path re-names it | `Evidence tree root (read-only): the read-only target repository's evidence directory.` |
| 6 | `papers/encoder-crossover-190/REFS.md:27` | `docs/research/GATED_READ_PROVENANCE.md` | `` `docs/research/GATED_READ_PROVENANCE.md` as the project's citation-audit file `` | **(iii)** | `the target repository's citation-audit file` |
| 7 | `papers/encoder-crossover-190/REFS.md:124` | `docs/research/EXP#12-evidence/` | `` `docs/research/EXP#12-evidence/` (26 files) contains **zero** external citations `` | **(iii)** | `the target repository's evidence directory (26 files)` |
| 8 | `papers/encoder-crossover-190/REFS.md:130` | `docs/research/GATED_READ_PROVENANCE.md` | `` `docs/research/GATED_READ_PROVENANCE.md` carries full-ish citations `` | **(iii)** | `the target repository's citation-audit file` |
| 9 | `papers/encoder-crossover-190/CHECKLIST.md:137` | `docs/research/FINDINGS_REGISTER.md:47` | (table row 1: wrong imajev row count 3,590 -> **3,690**) | **(iii)** | `the target repository's findings register:47` (UFIXPKG5 already used exactly this form at `orchestration/units/UFIXPKG5.md:25,47`) |
| 10 | `papers/encoder-crossover-190/DISCLOSURE_CHANGES.md:140` | `docs/research/EXP#12-evidence` | `` `ls "docs/research/EXP#12-evidence" \| wc -l` (in the target) → **26** `` | **(iii)** | `ls "<evidence-dir>" \| wc -l` |
| 11 | `papers/encoder-crossover-190/LICENSE_ANALYSIS.md:433` | `docs/research/EXP#12-evidence/…`, `docs/research/EXP#11-evidence/decider-rows.jsonl` (**2 on this line**) | `the "eight load-bearing sources" table: exact in-repo paths (\`docs/research/EXP#12-evidence/…\`, \`docs/research/EXP#11-evidence/decider-rows.jsonl\` …)` | **(i)** — this line **is** the record (`LICENSE_ANALYSIS.md` §8.1 item 2). Its documented verdict is *reframe*, not *keep* | no edit needed to the record; if the record is ever shipped, same generic phrases |
| 12 | `papers/encoder-crossover-190/LICENSE_ANALYSIS.md:437` | `docs/research/EXP#11-evidence/decider-rows.jsonl` | `names \`docs/research/EXP#11-evidence/decider-rows.jsonl\` as the thing that re-scores to 0.6789` | **(i)** — the record, §8.1 item 6; same verdict | as above |
| 13–21 | `papers/encoder-crossover-190/EVIDENCE_NOTES.md:17,52,79,142,180,218,233,321,348` | `cd "the read-only target repository/docs/research/EXP#12-evidence"` | `cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "` | **(i)** — `LICENSE_ANALYSIS.md` §8.2 item 2 designates **this command list** as part of the intended public reproducibility subset ("the command list currently in `EVIDENCE_NOTES.md`, which lives in this workspace, not in the private repository") | the commands are meant to be public; only the literal private path should become a placeholder: `cd "<target-repo>/<evidence-dir>"` (9×, identical string) |

**Rows 13–21 rationale, stated so the orchestrator can overrule it:** the disclosure decision covers the
*commands*, and a released command list is worthless if its paths are deleted — so class (i) is right for the
command, and the private path segment is still replaceable with no loss, because no reader can resolve
`docs/research/EXP#12-evidence` (the repo is private / 404 unauthenticated, `LICENSE_ANALYSIS.md` §1.6).

**Rows 1–4 rationale for (iii) rather than (ii):** `LICENSE_ANALYSIS.md` §8.3 does argue the *per-case
decider rows* are disclosure "that genuinely requires the artifact" — but that argues for **publishing the
artifact** (§8.2's separate public repro repo), not for printing a path into the private tree. As written the
path is a citation a reader cannot follow, so it fails the (ii) test ("a reader genuinely needs it **to find**
the thing being cited"). The replacement keeps the artifact identifiable, which is what (ii) protects.

## 3. List A, wider class — the 21-count does not cover these (all class (iv))

Measured by `grep -rnE "experiments/|kernel/|EXP#[0-9]+-evidence" papers/encoder-crossover-190/ --include=*.md --include=*.tex`:

| file:line | token as written | quoted context | class | what settles it |
|---|---|---|---|---|
| `submission/main.tex:230` | `strategy/` | `The corpus's own summary (\texttt{strategy/` | **(iv)** | does `strategy/` resolve under `/home/zer0null/Duval` (parent path → (iii)) or under this workspace (own path → not a finding)? One existence check. |
| `submission/main.tex:335` | `PAPER\_CANDIDATES.md` | `\texttt{PAPER\_CANDIDATES.md} \SF.3 is not discharged` | **(iv)** | same check |
| `submission/main.tex:387` | `experiments/second-labeller-190/…` | `source experiment tree \texttt{…}` | **(iv)** | same check |
| `submission/main.tex:412` | `second-labeller/\{RUN.json,EVIDENCE.md,…\}` | `\texttt{second-labeller/\{RUN.json,EVIDENCE.md,disagreement…` | **(iv)** | same check (this one may be the payload's own shipped dir) |
| `submission/main.tex:419` | `src/**`, `kernel/**` (see `MANUSCRIPT.md:836`) | `The \textbf{agent-state kernel / runtime im…` | **(iv)** | `LICENSE_ANALYSIS.md` §8.1 item 2 calls `src/`, `kernel/` *withheld implementation* dirs of the target — so these are almost certainly (iii), but I did not read the full line |
| `MANUSCRIPT.md:422,639,756,761,818,836`; `LIMITATIONS_UPDATE.md:10,11,13,15,222,234`; `AVAILABILITY.md:44`; `REFS.md:125`; `CLAIMS.md:18,27,33,37,45,48,108`; `CHECKLIST.md:130`; `VERIFIER_CORRECTIONS.md:65`; `EVIDENCE_NOTES.md:35` | `experiments/…`, `strategy/…`, `src/**`, `kernel/**`, `LEARNINGS.md`, `REPORT.md`, `analysis.json` | e.g. `experiments/second-labeller-190/EVIDENCE.md:309` states it for one pass | **(iv)** | same check; these are workspace documents (not shipped) except where they feed `main.tex` |

## 4. List B — the released payload

### 4a. Checked and CLEARED: these are the project's own neutral tags, not exposures

The rename is on the workspace's own record. `orchestration/units/UDTAG1.md:22-23`: "Map: D09->P02, D15->P03,
D25->P05, D35->P04, D44->P01. 17 of 45 files rewritten; 0 residual occurrences."
`orchestration/handoffs/UDTAG1.json:16`: "NEUTRAL-TAG/v1 prefix P: D09->P02, D15->P03, D25->P05, D35->P04,
D44->P01". `strategy/DTAG_NEUTRALISATION.md:40`: "| `P02` | `P03` | `P05` | `P04` | `P01` |".
`strategy/WHOLE_CLASS_NEUTRALISATION.md:20` lists the "already-neutral families (F01–F56, N01–N10, K01–K07,
R01–R10, P01–P05, T01–T06, D01–D60, …)".

| token | measured count | where (measured) | ruling |
|---|---|---|---|
| `P04` | **10** | `preregistration/EXP12-typed-channel-comparison-prereg.md`, `results/REPORT.md` | **not an exposure** — minted neutral tag (D35→P04) |
| `P05` | **6** (card said 7) | `second-labeller/EVIDENCE.md:4`, `second-labeller/PREREGISTRATION.md:10`, `second-labeller/RUN.json:7`, `results/REPORT.md:5`, `preregistration/…prereg.md:55` | **not an exposure** — minted (D25→P05) |
| `P03` / `P02` | 2 / 1 | `preregistration/…prereg.md:6`, `results/REPORT.md:1` / `results/REPORT.md:157` | **not an exposure** — minted (D15→P03, D09→P02) |
| `P01` | **0** | — | **absent**; the card's ×1 is stale (UFIXPKG5 fixed the last bare `P01:47`, `orchestration/units/UFIXPKG5.md:89`) |
| `D01`–`D19` (11 distinct: D01×6, D03×1, D06×1, D07×15, D08×4, D11×2, D12×1, D14×1, D16×1, D17×1, D19×2) | 35 | mostly **filenames the payload ships** (`D07.sandbox.ts`, `D01`, `D11`, `D12`, `D16`, `D17`, `D08`, `D03`, `D02`, `D19`) plus `fixture/DECISION_CASE_SCHEMA.ts:1` | **not an exposure** — `D[0-9][0-9]` is the accepted tag family in the build gate (`orchestration/handoffs/UOUTSIDE1.json:16`: `TAG_RE ^(?:K|F|S|C|R|D)[0-9][0-9]$ \| ^TAG_[0-9][0-9]$`); removing them would break `MANIFEST.json` and the shipped commands |
| `D48` | 1 | `results/REPORT.md:11` (`D48 experiment discipline`) | **not an exposure** — same accepted family |
| `D14` | 1 | `fixture/DECISION_CASE_SCHEMA.ts:1` `// D14 — extracted verbatim from` | **not an exposure** as a tag; the comment is truncated mid-sentence — cosmetic, not a leak |
| `D42` | **0** | — | **absent**; card's list is stale (`[…](../../D42)` replaced, `orchestration/units/UFIXPKG5.md:24`) |
| `S02`×7, `S04`×1, `S07`×2, `F01`–`F56`, `G01`–`G58` | see census | payload's own case/tool vocabulary (`F54`×1333, `G11`×703, …) | **not exposures** — payload-internal names; the manifest is fail-closed over them |

**One actionable caveat, not an exposure:** the gate's `TAG_RE` accepts `K|F|S|C|R|D` but **not `P`**
(`orchestration/handoffs/UOUTSIDE1.json:16`; `strategy/OUTSIDE_TOKEN_REDACTION.md:69`: "the family `P01..P05`
used by UDTAG1 is **not** accepted by the [gate]"). So P01–P05 are legitimate neutral tags that the build
gate's own vocabulary does not recognise. That is a gate/registry mismatch for the orchestrator to close
(extend `TAG_RE` to `P`, or remap), **not** a disclosure finding.

### 4b. FINDINGS in list B

| file:line | token as written | quoted context | class | generic replacement |
|---|---|---|---|---|
| `scratch/uneutral10/package/fixture/reflex-decisions.ts:39,40,380,695,1889` (×5) | `D43 §3` | `/* [withheld: section note naming internal mechanism — see D43 §3] */` | **(iii)** | `/* [withheld: section note naming internal mechanism — see the withheld rationale note, section 3] */` — **the replacement already exists in-payload**: UFIXPKG5 used exactly `the withheld rationale note, section 5` for the same class at `second-labeller/OWED_CORRECTIONS.md` (`orchestration/units/UFIXPKG5.md:55-57`). No new tag is needed; the same file class was genericised in one file and retained in another. |
| `scratch/uneutral10/package/results/baselines.json:2425,2430`; `scratch/uneutral10/package/results/REPORT.md:36,104,189` (×5) | `D-067` | `"decider-4b 0.6684 (D-067)": {` · `no per-case rows for the D-067 measurement are in the tree` | **(ii) necessary citation** | keep the id; if a generic form is wanted, `the target project's recorded decision D-067` (attribution, not deletion). Record: `strategy/NONCENSUS_CLASSIFICATION.md:63` — "the *format* is partly public — the released papers cite `D-067` (2×)"; `strategy/DTAG_NEUTRALISATION.md:32` — "the released papers cite entirely different ones (`D-067`, `D-038`, `D-047`, …)" |

**Why `D-067` is (ii) and not (iii), measured:**
- The target's decision ids are written `D-0NN` **with a hyphen**, as headings: `strategy/NONCENSUS_CLASSIFICATION.md:58`
  records "(also `:971` `## D-035`, `:1086` `## D-038`, `:1305` `## D-044`, `:2091` `## D-061`, `:2362` `## D-067`)".
- Read-only target grep (`timeout 30 grep -rlE "D-067" /home/zer0null/Duval --include=*.md --include=*.json`,
  first 10 paths) returned `/home/zer0null/Duval/.worktrees/P3-CORE/docs/DECISION_LOG.md` among
  `docs/BOARD.md`, `docs/FINDINGS.md`, `docs/OPEN_DECISIONS.md`, `docs/research/EXP#12-evidence/{baselines.json,analysis.json,REPORT.md}`,
  `docs/research/TEARDOWN_TIMEOUT_2026.md`, `docs/INDEX.md`, `docs/migration/C7_END_STATES.md`. So the id names
  a real recorded decision, and the payload cites it to identify **which** 0.6684 measurement it means.
- It discloses no mechanism: an opaque id, not a path. `D-067` also **cannot be confused** with a minted
  neutral tag — the gate family is `^D[0-9][0-9]$` (two digits, no hyphen), so the two schemes are lexically
  disjoint. This is a reason to keep it, and it is also why a sweep keyed on `D[0-9]{2}` will never flag it.

**Why `D43` is (iii) and not (ii), measured:** the same format evidence (`## D-0NN` headings) means `D43`
— two digits, no hyphen — is **not** a target decision id; it is a minted neutral tag. So `see D43 §3` points
at nothing a reader (or a replicator) can resolve, while reading as if it were a pointer. It is the one
list-B item that is a real defect: a dangling cross-reference into a withheld note.

## 5. Measured / inferred / not determined

**Measured** (literal command output recorded above): the 22/21 counts and per-file lines; the tarball listing
(`main.tex`, one entry); the payload token census (`P04` 10, `P05` 6, `P01` 0, `D42` 0, `D-067` 5, `D43` 5,
`D48` 1, `D14` 1, `D01`–`D19` 35); the `docs/research` hits in `submission/main.tex:146` and the wider class at
`main.tex:230,335,387,412,419`; the target grep returning `DECISION_LOG.md` for `D-067`; the workspace records
quoted in §4a.

**Inferred:** that `P01`–`P05` are neutral tags (from UDTAG1's own map plus `WHOLE_CLASS_NEUTRALISATION.md:20`);
that `D-067` is a target decision-log id and `D43` is not (from the `## D-0NN` heading format recorded at
`strategy/NONCENSUS_CLASSIFICATION.md:58` — I did **not** open `DECISION_LOG.md` to confirm the heading exists);
that the 9 `EVIDENCE_NOTES.md` command lines are the ones §8.2 designates.

**Could not determine:** which root `experiments/`, `strategy/`, `src/**`, `kernel/**` resolve under (one
existence check settles §3); whether the bytes inside `submission/encoder-crossover-190.tar.gz` equal the
on-disk `main.tex` (I read the listing only); whether `D-067`'s cited decision text is itself already public —
`strategy/WITHHELD.md:242,279` records a `decisions/DECISION_LOG.md` as "public in the same repo (UDISC1 §1–§2,
§4)", which would make the citation a disclosure of something already public, but I did not verify that the
public file is the same one carrying `D-067`.

## 6. What this search would NOT catch (the card asks for this explicitly)

1. **TeX escaping.** The released artifact writes `EXP\#11-evidence`, **not** `EXP#11-evidence`. Any sweep
   keyed on `EXP#11` **misses `submission/main.tex` entirely**. I searched `docs/research` (escape-free), which
   is why the count survives — but a follow-up sweep for the wider class must normalise `\#` → `#`.
2. **Containers.** `grep -r` cannot see inside `submission/encoder-crossover-190.tar.gz`; I read its *listing*
   (`tar -tzf` → `main.tex`), not its bytes. If the archived copy differs, nothing above shows it. Same for
   any PDF/DOCX in the tree.
3. **Token shape.** Names split across lines, re-cased, hyphen/space-mangled, written with another dash
   (`D–067`, U+2013), unicode-escaped, or **paraphrased** ("our earlier comparison note") are invisible to
   every regex I ran. My own census regex `\bD-?[0-9]{2,3}\b` would have missed an en-dash form.
4. **A `docs/research`-only count understates the class.** See §3 — the wider parent-path class reaches the
   released artifact at five measured lines. A sweep that re-runs only the known form reproduces the last two
   sweeps' miss.
5. **I did not read the manuscript end-to-end.** A reference that names the parent by concept, sharing no
   token with anything known, is invisible to search by construction.
6. **Read-only discipline.** No `git` command was run against `/home/zer0null/Duval`; the only target access was
   `grep -rl` (no index refresh, no writes). I did not enumerate `.worktrees/**` or `rust/crates/**`, so a
   parent identifier living only there would not appear here.

## 7. Decision-ready summary for the orchestrator

- **List A is 1 real edit, not 21.** Exactly one line ships (`submission/main.tex:146`, generated from
  `MANUSCRIPT.md:301`). Fix `MANUSCRIPT.md:301`, regenerate with `python3 scratch/uprep1/md2tex.py`, rebuild the
  tarball. The other 20 lines are working documents; 11 of them are class (iii) and trivially replaceable with
  phrases **already used elsewhere in this workspace** (no new vocabulary needed), and 11 are class (i) —
  9 designated-for-release commands + 2 lines that *are* the `LICENSE_ANALYSIS.md` §8.1 record.
- **List B is 1 real edit, not 28.** `D43 §3` ×5 in `fixture/reflex-decisions.ts` — replace with the
  in-payload phrase `the withheld rationale note, section 3`. Everything else the card listed is either a
  minted neutral tag (the mechanism working), a payload-shipped filename the manifest depends on, or — for
  `D-067` — a deliberate citation of a real target decision-log entry, which should stay.
- **Two open policy calls, neither a leak:** (a) the build gate's `TAG_RE` does not accept the `P` family it
  must validate; (b) whether the class (i) command lines in `EVIDENCE_NOTES.md` should keep a literal private
  path or take a placeholder once the §8.2 repro repo exists.
