# UCURATE1 — ship/drop decision for the public package

**Status:** done · **Bound:** 45 tool calls (+12 granted for the `papers/gated-read-batching` addition) ·
**Purpose (one):** decide and encode exactly which files the public package ships, by editing the build
script's exclusion logic. **The gate is the arbiter, not opinion.**

**Write paths:** `orchestration/units/UBUILD1.build.sh` · `strategy/PUBLISH_PACKAGE_MANIFEST.md` ·
`orchestration/units/UCURATE1.md` · `orchestration/handoffs/UCURATE1.json`.
Nothing else touched. `repro/encoder-crossover-190-SANITISED/**` and `papers/gated-read-batching/**` were
read only. `/home/zer0null/Duval` read only. Nothing written outside the workspace.

## What was changed and why

| # | change | why |
|---|---|---|
| 1 | The `cp -r`-then-`rm -f` shape was replaced by a **fail-closed `SHIP_STAGED` ship-list** (52 entries) plus a prune loop that deletes and logs every unlisted staged file and `exit 1`s on a listed-but-missing file. | A drop-list is **fail-OPEN**: an unlisted file ships by default and nobody is told. A ship-list fails towards under-shipping, which is visible and cheap to fix. |
| 2 | A **`NEVER_SHIP` list** (17 names) checked **by absence** at the end of the build, with `FATAL` + `exit 1` on any hit. | The ship-list makes these unreachable *today*; `NEVER_SHIP` makes the drop decisions survive a refactor that adds another `cp -r`. |
| 3 | **`INCLUDE_VERIFY` deleted.** | Its only use was to omit the reproduction instrument. Removing it is strictly stricter. |
| 4 | The **only transform**: three literal path rules (UTOK2 §1) via a fail-closed Python step that aborts if `/home/zer0null` or `duval` survives; `gate.sh` excluded (it *is* the pattern list). | `manifest.json` is read at runtime by `harness/analyze.py:133`; a path is not model input. Cleared `/home/zer0null` 4→0, `duval` 4→0. |
| 5 | The two anchors `907fa39`/`ad301ae` are now **asserted present**, with a `FATAL` that says they are the read-only target-revision proof and must not be removed. | A future reader must not "clean" them. |
| 6 | The three authored READMEs were rewritten to describe what actually ships (`code/verify/` holds **one** file) and to state *why* the sanitisation driver and its log are excluded. | The old text pointed a reader at files the package no longer contains. |
| 7 | The second-labeller dedup comment was corrected: `ROBUSTNESS.md` and `RUN2.json` are **gate-clean (0 hits each)** and ship. | The old comment claimed they hard-fail; measurement says otherwise. |

## The line drawn

- **Reader-load-bearing → SHIPS**, even with a declared internal cross-reference: needed to recompute a
  published number from bytes inside the package, or to understand the claims and their limits.
- **Record of our process → DROPS**, whatever its hit count, and it is dropped rather than scrubbed — an
  edited audit record is no longer an audit record.

Consequences: `code/fixture/reflex-decisions.ts` carries 54 hard hits and **ships**;
`code/verify/RECOMPUTE-CLAIMS.txt` carries 0 and **does not**.

## Gate, re-run over what ships

Executed **inside the workspace** (`DEST=.ucurate1/pre/research-publish-packages`) with the denylist then read
out of the built `gate.sh` — the HARD patterns then at the `PATTERNS_HARD`/`PATTERNS_REVIEW` heredocs of `UBUILD1.build.sh`, a range that is now dead. ULICENCE3 has since deleted that list and replaced it with the positive vocabulary checker written by the heredoc beginning `cat > "$DEST/gate.sh" <<'GATE_EOF'`, currently `:771`–`:896` (`chmod +x` at `:897`).

```
GATE RESULT: FAIL — 152 HARD-FAIL hit(s) and 2134 REVIEW hit(s).
```

Per HARD pattern: `StateClass` 62 · `grantPolicy` 40 · `expanded[` 28 · `admit(` 20 · `REDACTION_REPORT` 10 ·
`EXCLUDED.md` 2 · `src/broker` 2 · `VERIFICATION_REPORT` 1 · `/home/zer0null` **0** · `duval` **0** · 14
further patterns **0**. Per-pattern occurrences 165 over **152 distinct lines** (13 lines match two patterns).

Baseline: the contract's `gate_before` is `"158"` (UTOK2, whole 58-file SANITISED tree, *with* prose
substitution). UCURATE1's own comparable numbers: **218** for the unmodified build's ship set with no
transform, **152** after the three path rules. The two are not comparable and both are reported.

**150 of the 152 are model input / instrument vocabulary** that only a re-cut experiment could remove, and 2
are declared documentary cross-references. The gate is a **leak detector, not a shipping checklist** — it
fires on the instrument itself by construction. It was left strict and the build correctly stops at exit 1:
`152` is the deliberate minimum for this ship set, not a failure to reach 158.

## Evidence

```
staged 66 file(s): 52 kept, 14 dropped
ship-list enforced: 52 staged file(s) present
never-ship list enforced: 17 names checked absent
  1 occurrence(s)  packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts
  3 occurrence(s)  packages/exp12-encoder-crossover/code/harness/data/manifest.json
  4 occurrence(s) in 2 file(s)
anchor 907fa39 present in 12 file(s) — kept deliberately
anchor ad301ae present in 7 file(s) — kept deliberately
GATE RESULT: FAIL — 152 HARD-FAIL hit(s) and 2134 REVIEW hit(s).
```

Ship list: **52 staged + 6 authored = 58 files** (itemised in `strategy/PUBLISH_PACKAGE_MANIFEST.md` §9).
Build script: 826 lines, sha256 `0b617414e5eb0e8a2a86930bdf5f2de1d0cf3fb3f9a93865b36e7380af293115`.

> **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** `orchestration/units/UBUILD1.build.sh` has been edited since this measurement; it is now **1,019 lines**, sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`. The cited values are the record.

## Commands run

```
bash -n orchestration/units/UBUILD1.build.sh
SRC="<workspace>" DEST="<workspace>/.ucurate1/pre/research-publish-packages" bash orchestration/units/UBUILD1.build.sh
cd .ucurate1/pre/research-publish-packages && bash gate.sh
grep -rn -I -i -F -f .ucurate1/HARD.txt . --exclude-dir=.git --exclude=gate.sh   # per-pattern + per-file
grep -c -I -i -F -f .ucurate1/HARD.txt <each dropped doc>
find . -name 'GATED_READ*' -not -path './state/*' ; ls -la /home/zer0null/Duval/docs/research/
sha256sum orchestration/units/UBUILD1.build.sh
```

## Folded in from UFIX11 (the +12)

1. `papers/gated-read-batching/DISCLOSURE_CHANGES.md` → **DROP**; measured **19** hard-hit lines under the
   gate's verbatim list (UFIX11's 52 is against its own wider 19-alternative sweep list — both correct, not
   comparable). Recorded by name in `NEVER_SHIP`.
2. **Precedent confirmed concretely:** `EXCLUDED.md` is *genuinely excluded* — a `find` over the built
   package for `EXCLUDED*`/`REDACTION_REPORT*`/`RESIDUALS*`/`LICENCE_TODO*`/`SCRUB_REPORT*`/`INTEGRITY*`
   returns **0 files**, and `EXCLUDED.md` occurs in the build script only inside explanatory comments. Not a
   documented-only exclusion.
3. **Actual file list verified myself:** `papers/gated-read-batching/` holds **exactly 5 files**
   (`CLAIMS.md`, `DISCLOSURE_CHANGES.md`, `GAPS.md`, `MANUSCRIPT.md`, `REFS.md`) — no `CHECKLIST.md`, no
   `OPEN_QUESTIONS.md`, no `REFERENCES.bib`, no README. The other four are **hard-clean (0 each)**.
4. **Traceability settled: (b) — the sources do not ship, and no new manuscript prose is needed.** The
   locator sources live **only in the read-only target repository** (`/home/zer0null/Duval/docs/research/GATED_READ_2026.md`
   23,591 B, `GATED_READ_PROVENANCE.md` 31,679 B) plus workspace mirrors of it under `state/`. The legend and
   the withholding are already declared and gate-clean: `CLAIMS.md:8` ("relative to the root of the read-only
   source material (an external checkout; name and location withheld)") and `CLAIMS.md:11-15` (the four-letter
   legend: **G** `GATED_READ_2026.md`, **R** `gated-read-rows.jsonl`, **S** `gated-read-summary.json`,
   **P** `GATED_READ_PROVENANCE.md`). Shipping them is not open to this package — it does not redistribute the
   target.
5. **One real defect found, recommended not shipped** (`papers/gated-read-batching/**` is not my write path):
   the **G/R/S** legend lives only in `CLAIMS.md:11-15`, while `REFS.md:66` uses a `G:` locator and `REFS.md:11`
   declares only **P** — so a reader opening `REFS.md` alone has no legend for **G**. Add one line to
   `REFS.md` (the four-letter legend, or "letter legend: `CLAIMS.md:11-15`").

   > **Superseded 2026-10-16 (UFIX22, dated record left unrewritten):** the `REFS.md` reading above is wrong. `papers/gated-read-batching/REFS.md:66` uses **`P:246`**, not a `G:` locator; the only `G:` locator is `REFS.md:68` (`G:49-51`); and the `G:` legend already exists at `REFS.md:15` (`P:` at `:11`), so the recommendation to add a legend line is moot.

## UNVERIFIED

Full list in `strategy/PUBLISH_PACKAGE_MANIFEST.md` §11. The load-bearing ones: the real `DEST` build was
**not run** (card requirement) — all verification was with `DEST` inside the workspace; UTOK2's `158` was not
re-derived; the 2 `GrantPolicy` strings were not substituted so the `/routeA/ties` 120→119 and the
projection-digest movement remain UTOK2's measurements; `harness/analyze.py` needs the excluded
`manifest-eval.json` and was not run; `manifest.json` neutralisation is not durable against re-running
`prepare.py` (UTOK2 §7.4, not re-verified); the 2,134 REVIEW-pattern hits were left alone as report-only.

## OPEN DECISIONS — the orchestrator's three flags (added on request, nothing changed)

Full text: `strategy/PUBLISH_PACKAGE_MANIFEST.md` §12. 9 of the granted 12 tool calls used. The staged
tree was left exactly as measured (58 files, gate 152).

1. **Licence tier — MIT is stale; flagged, not switched.** The root `LICENSE` is a **root-level MIT** file
   authored by the *pre-existing* `UBUILD1.build.sh` heredoc (build-script lines 524–545) — **inherited from
   UBUILD1, not introduced by me, and not changed.** Its provenance is
   `strategy/PUBLICATION_STRATEGY.md:570` ("public under MIT … the public copy is citable today") and `:576`
   ("what the public repo's **MIT** licence already granted over the **public** material cannot be undone for
   those versions"), plus `strategy/ARCHIVE_WINDOW_CHECK.md:295` ("the published root is MIT") — i.e. **the
   target's already-public versions, not a grant over this package.** The binding decision is the **UMEMO1
   errata at `strategy/CODE_LICENSING_STRATEGY.md:9-31`** (author, 2026-10-15: *"no licence on the main
   consonance folder that's proprietary"*): main repo proprietary/all-rights-reserved; **each released piece
   PolyForm Noncommercial 1.0.0**, carrying `LICENSE` (PolyForm NC + Required Notice), `COMMERCIAL.md`,
   `CONTRIBUTING.md` and a source-available README paragraph; only **extracted pieces** are released;
   corrected per-file table at §5.1. Corroborated by `strategy/WITHHELD.md:132`. **⚠️ Correction to the
   request:** the quoted *"PolyForm Noncommercial 1.0.0, 4,563 bytes, sha256 `ffcca388…`"* **matches nothing
   on disk** — `strategy/licence-templates/RELEASED-PIECE/LICENSE` is **5,662 bytes, sha256
   `25aa637ba1689e87ad34c5acc25464a4eaaa2f5b2c84e3dc4d7ed84158277cfe`**, and no file under
   `strategy/licence-templates/` carries digest `ffcca388`. Also, **no "fragments … fully MIT" author
   statement exists** in `strategy/` or `orchestration/` (grepped `fully MIT` and `fragments`); the nearest
   real text is the `PUBLICATION_STRATEGY.md:570/576` pair above, which is about the target's public root —
   so "fragments" and "released pieces" are **not** two categories as far as this workspace records.
   Switching would change shipped bytes and add 3 files → the author's/orchestrator's call.

   > **Superseded 2026-10-16:** the licence described here as MIT is now the PolyForm Non-Commercial 1.0.0 instrument, copied from `strategy/licence-templates/RELEASED-PIECE/` by `orchestration/units/UBUILD1.build.sh` (`LIC_SRC` `:575`, guard `:584`, sha256 `3d364676…f900`).

   > **Superseded 2026-10-16 (UFIX23, dated record left unrewritten):** the `:524–545` range cited
   > above no longer holds a licence heredoc. `orchestration/units/UBUILD1.build.sh` is now **1,019
   > lines**, sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`; `:524–545` is
   > now prose inside the emitted package README (heredoc `cat > "$PKG/README.md" <<'PKG_README_EOF'`
   > at `:433`, closing `PKG_README_EOF` at `:541`). The root licence is no longer authored by the heredoc
   > cited here: it comes from the template-copy block
   > `LIC_SRC="$SRC/strategy/licence-templates/RELEASED-PIECE"` (`:575`), with the scope clause appended
   > by `cat >> "$DEST/LICENSE" <<'LICENSE_SCOPE_EOF'` (`:590`, heading `## Scope -- which files the licence
   > terms above do not cover` at `:592`), and the paper instrument at
   > `cat > "$PKG/paper/LICENSE" <<'PAPER_LICENSE_EOF'` (`:607`). Verify the anchors before relying on the
   > numbers.

   > **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** `strategy/licence-templates/RELEASED-PIECE/LICENSE` has since been rewritten: it is now **5851 bytes**, sha256
   > `3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900`, with `COMMERCIAL.md` 3512 B and
   > `CONTRIBUTING.md` 3036 B. The 5,662 B / `25aa637b…` values cited above are the record.
2. **Scope division is PROSE-ONLY.** Code MIT · paper CC BY 4.0 is declared only in README prose
   (build-script lines 344, 380, 383, 495) plus the author decision at `strategy/WITHHELD.md:124` and
   `:129-133`. **No per-directory notice** (`code/LICENSE`, `paper/LICENSE`, `eval/LICENSE` all absent) and
   **no scoping clause** in the root `LICENSE`, which nominally covers the whole tree including
   `paper/MANUSCRIPT.md`. Materially weaker than a notice; the fix depends on item 1, so it was not applied.

   > **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** build-script lines 344, 380, 383 and 495
   > no longer carry the MIT prose cited above. `:344` is now the emitted root README's package table
   > (`code **PolyForm NC 1.0.0** · paper text **CC BY 4.0**`); `:380`–`:382` extracts the source-available
   > paragraph from `strategy/licence-templates/README-PARAGRAPHS.md` (heredoc `caseB=` at `:383`); `:495`–`:497`
   > is the `run-verification.sh`/`VERIFICATION.txt` path caveat. The licence is now the copied `LIC_SRC` template
   > (`:575`, `:579`) with the scope clause appended at `:590`–`:602` (digest guard `:584`).
3. **One package staged; #7 is NOT packageable this pass.** `packages/` holds only
   `exp12-encoder-crossover`, though the repo is named *packages* plural. For `papers/gated-read-batching/`
   the manuscript side is nearly ready (4 files hard-clean; drop `DISCLOSURE_CHANGES.md`), but the
   reproducibility subset does not exist: the raw rows `gated-read-rows.jsonl` (9,260 rows) and
   `gated-read-summary.json` exist **only as mirrors of the read-only target** (e.g.
   `./state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/gated-read-rows.jsonl`),
   there is **no `repro/gated-read-batching/` at all** (`find '*gated*read*'` outside `state/` returns only
   `./papers/gated-read-batching`), and there is no fixture, analysis script, exact commands or
   pre-registration. It fails the "minimal reproducibility subset" norm (`strategy/WITHHELD.md:129-133`).
   **Recommendation:** ship it **paper-only** (4 docs, with the explicit "source material withheld; the
   `G/R/S/P` locators resolve in the read-only checkout, deliberately not redistributed" statement), or
   withhold it — **not** as a reproducibility package. Adding it changes the ship list, `NEVER_SHIP` and the
   gate total, so it was not added.
