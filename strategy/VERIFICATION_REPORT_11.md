# VERIFICATION REPORT 11 — UVER11 vs UCURATE1

**Verifier:** UVER11 (independent; not the author)
**Subject:** `strategy/PUBLISH_PACKAGE_MANIFEST.md` (UCURATE1), staged tree
`.ucurate1/pre/research-publish-packages/`, build script
`orchestration/units/UBUILD1.build.sh`
**Verdict:** **PARTIAL** — the headline reproduces exactly; one supporting number is
contradicted by the artifact and one citation is wrong.
**Bound:** 40 tool calls. **Used:** 30 (25 bash + 1 compress + 3 writes + 1 handoff message).
**Read-only honoured:** `/home/zer0null/Duval` and every registered target untouched; no `git`
command run against any target; the real `/home/zer0null/research-publish-packages` was only listed,
never written. All builds ran under `scratch/uver11/`.

**UFIX17 pointer (2026-10-15, dated record left unrewritten):** "untouched" above must now be read as
**"no write by this workspace's units"** — the root checkout was rewritten by a foreign actor
(`strategy/CONTAINMENT_CHECK.md` §2/§7), so "targets untouched" is false as written.

---

## A. Independent re-derivation of the headline gate number — **REPRODUCED (exact)**

Method: I extracted the gate's **own** HARD pattern list from the build script's heredoc
(`UBUILD1.build.sh:612–637`, patterns at 613–636 = 24 patterns) into
`scratch/uver11/hard.txt`, and ran my own case-insensitive fixed-string scan over the staged tree:

> **Superseded 2026-10-16:** the `PATTERNS_HARD` / `PATTERNS_REVIEW` heredocs named here were removed by unit ULICENCE3 and no longer exist. The gate is now the positive vocabulary checker whose heredoc opens `cat > "$DEST/gate.sh" <<'GATE_EOF'` (currently `:771`, closing `:896`, `chmod +x` `:897`), fed by `vocabulary/{english,code,public}.txt` (currently `:691`, `:695–743`, `:748–769`) and invoked at `bash "$DEST/gate.sh"` (currently `:1005`). Verify the anchors before relying on the numbers.

```
cd .ucurate1/pre/research-publish-packages
grep -rn -I -i -F -f scratch/uver11/hard.txt . --exclude-dir=.git --exclude=gate.sh | wc -l
→ 152
```

**My total: 152** — identical to UCURATE1's headline. My per-pattern tally
(occurrences; 165 occurrences over 152 distinct lines, 13 lines matching two patterns):

| pattern | my count |
|---|---|
| `StateClass` | 62 |
| `grantPolicy` | 40 |
| `expanded[` | 28 |
| `admit(` | 20 |
| `REDACTION_REPORT` | 10 |
| `EXCLUDED.md` | 2 |
| `src/broker` | 2 |
| `VERIFICATION_REPORT` | 1 |
| `/home/zer0null` | **0** |
| `duval` | **0** |

This matches UCURATE1's §5 table (manifest:255 block) pattern for pattern, including the two
declared-zero local-path patterns. **Claim 1's headline is exact.**

REVIEW count `2134` (manifest:255) was **not** independently re-derived — only HARD was. Noted as
`not_reproduced` (out of scope of the pass, not contradicted).

## A2. The 218 → 152 contrast — **CONTRADICTED / NOT REPRODUCED**

Manifest §8 says (manifest:286):

> UCURATE1's own comparable measurement of **the unmodified build's ship set with no transform at
> all** is **218**; with the three path rules it is **152**.

The artifact does not support 218. The build's own neutralisation step logs, verbatim, in my run's
`scratch/uver11/A.log`:

```
    1 occurrence(s)  packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts
    3 occurrence(s)  packages/exp12-encoder-crossover/code/harness/data/manifest.json
  4 occurrence(s) in 2 file(s)
```

I reconstructed the pre-transform ship set by reversing the script's three literal rules
(`<target-repo>/`→`/home/zer0null/Duval/`, `<target-repo>`→`/home/zer0null/Duval`,
`<user-home>`→`/home/zer0null`) on a scratch copy of the built tree and re-scanning:

```
pre-transform total = 156   (152 post-transform + 4 path-only lines)
```

So the path rules remove **4** lines, not the **66** that `218 − 152` implies. No measurement of the
ship set — fully untransformed (156) or post-transform (152) — yields 218. The `duval` and
`/home/zer0null` pre-transform counts are both 4 because those are the same 4 lines.

**Consequence (a real finding):** 156 is within 2 of the contract's `gate_before = 158`, so
UCURATE1's own comparable number is *nearly* the contract figure; the "incomparable numbers"
framing at manifest:286–288 is built on a 218 that does not exist in the artifact. The **152
headline is unaffected** and is not in doubt.

## B. Prune red→green, both directions — **REPRODUCED**

Builds ran against scratch only (`DEST=scratch/uver11/...`).

**(i) Add an unlisted file → it is DROPPED (the DROP is what removes it).**
Added `code/harness/UNLISTED_PROBE.txt` to staging, ran the ship/prune step:

```
DROP    code/harness/UNLISTED_PROBE.txt
... staged 67 file(s): 52 kept, 15 dropped
survivors of probe in final tree: 0
exit code: 1
```

The explicit `DROP` log line is the removal mechanism (not mere absence). Exit 1 is consistent with
both the drop and the still-failing gate; in this direction the *drop* is what was asserted and it
is proven by the log, not by the exit code.

**(ii) Omit a listed file → build exits 1.**
Omitted `code/harness/train.py` (a `SHIP_STAGED` entry) and ran the build:

```
FATAL: ship-list names a file the package does not have: code/harness/train.py
exit code: 1
```

The gate was never reached (`GATE RESULT` absent from that run's log) — the omission fails closed at
the ship-list check first. Matches the design note at `UBUILD1.build.sh:129` ("Nothing ships by
omission"). **Both directions reproduce; `not_reproduced` is not needed here.**

## C. Ship list = exactly 58 distinct files; list and tree agree — **REPRODUCED**

* `SHIP_STAGED` (extracted from `UBUILD1.build.sh`) holds **52** entries in the *source* layout
  (`paper/…`, `code/…`, `eval/…`).
* The build relocates them under `packages/exp12-encoder-crossover/` and authors **6** root files.
* Prefix-mapped reconciliation of the 52 mapped entries against the 58 tree files:

```
mapped-listed but ABSENT : (none)
present but UNLISTED     : gate.sh, .gitignore, LICENSE,
                           packages/exp12-encoder-crossover/README.md,
                           packages/exp12-encoder-crossover/code/README.md,
                           README.md      ← exactly the 6 authored files
tree files: 58   (all distinct)
```

No listed-but-absent file, no present-but-unlisted file beyond the six knowingly authored. The
`never-ship list enforced: 17 names checked absent` step also passed in every run. **Claim 2
reproduced.**

## D. Licence identity — **CLAIM REPRODUCED; CONFLICT WITH THE MEMO IS REAL**

**Shipped artifact (`strategy/PUBLISH_PACKAGE_MANIFEST.md` claim 9):**

```
head -1 .ucurate1/pre/research-publish-packages/LICENSE
→ MIT License
sha256 .ucurate1/pre/research-publish-packages/LICENSE
→ f2eb46b60685fe9bcb4a0075c865404d1f67a77363d3905025c46fcc335fb915
grep -ril polyform .ucurate1/pre/research-publish-packages | wc -l
→ 0
```

The root LICENSE is MIT with `<YEAR> <COPYRIGHT HOLDER>` placeholders, and **no PolyForm text exists
anywhere in the built package**. The README's "code **MIT** · paper text **CC BY 4.0**" declaration
was also confirmed. **Claim 9 reproduced.**

> **Superseded 2026-10-16:** the licence described here as MIT is now the PolyForm Non-Commercial 1.0.0 instrument, copied from `strategy/licence-templates/RELEASED-PIECE/` by `orchestration/units/UBUILD1.build.sh` (`LIC_SRC` `:575`, guard `:584`, sha256 `3d364676…f900`).

**`strategy/CODE_LICENSING_STRATEGY.md`, lines 9–40 — what the memo says a released piece is
(verbatim):**

> **ERRATA — unit UMEMO1, 2026-10-15.** … *"…so no licence on the main consonance folder that's
> proprietary"* (2026-10-15). **§5.1 and §6 Stage 0 are therefore superseded for the main Consonance
> repository.**
>
> **The two-tier structure now in force:**
>
> | | **Main Consonance repository** | **Each released piece** |
> |---|---|---|
> | **Status** | proprietary, private, trade secret | source-available, public |
> | **Licence** | **proprietary notice — all rights reserved** (no public licence) | **PolyForm Noncommercial 1.0.0** |
> | **Files carried** | `LICENSE` (proprietary notice), `TRADE-SECRET-NOTICE.md`, … | `LICENSE` (PolyForm NC + Required Notice), `COMMERCIAL.md`, `CONTRIBUTING.md`, source-available README paragraph |
>
> The main repository is **never published under PolyForm NC**. …

**Side by side, unresolved (known open item):**

| source | licence of a released piece |
|---|---|
| `strategy/CODE_LICENSING_STRATEGY.md:9–40` (UMEMO1 errata, 2026-10-15) | **PolyForm Noncommercial 1.0.0** (+ `COMMERCIAL.md`, `CONTRIBUTING.md`) |
| shipped `LICENSE` (`sha256 f2eb46b6…`) | **MIT License** |

Per instructions I **do not resolve** this: the artifact ships MIT, the memo of record says a
released piece carries PolyForm NC. Both facts stated.

> **Superseded 2026-10-16:** the licence described here as MIT is now the PolyForm Non-Commercial 1.0.0 instrument, copied from `strategy/licence-templates/RELEASED-PIECE/` by `orchestration/units/UBUILD1.build.sh` (`LIC_SRC` `:575`, guard `:584`, sha256 `3d364676…f900`).

## E. Anchors and build script identity — **REPRODUCED**

```
for a in 907fa39 ad301ae; do grep -rl -F --exclude-dir=.git -- "$a" \
    .ucurate1/pre/research-publish-packages | wc -l; done
→ 907fa39: 12
→ ad301ae: 7
sha256sum orchestration/units/UBUILD1.build.sh
→ 0b617414e5eb0e8a2a86930bdf5f2de1d0cf3fb3f9a93865b36e7380af293115
wc -l < orchestration/units/UBUILD1.build.sh
→ 826
```

Anchor file counts (12 and 7), build-script SHA-256 and line count all match UCURATE1 exactly. The
script also asserts anchors `907fa39`/`ad301ae` itself and would `exit 1` if either were missing
(`UBUILD1.build.sh:775–778`). **Claim 6 and claim 5's identity hold.**

> **Superseded 2026-10-16:** the `:775–778` range held the anchor assertion in the denylist-era script and no longer does. The assertion is now the loop `for anchor in 907fa39 ad301ae; do` (currently `:965`), with `exit 1` at `:971`; `:775`–`:778` is now gate-heredoc prose. Verify the anchors before relying on the number.

## F. Real destination not written — **CONFIRMED (observed read-only)**

```
ls -la /home/zer0null/research-publish-packages
→ total 8
  drwxrwxr-x 2 zer0null zer0null 4096 Oct 15 18:07 .
  drwxr-x--- 70 zer0null zer0null 4096 Oct 15 18:07 ..
find /home/zer0null/research-publish-packages -type f | wc -l
→ 0
```

Exists, empty, **0 files**, mtime Oct 15 18:07 (older than this verification). No README, LICENSE,
paper/, code/, or `.ucurate1` artifact from any build. Nothing was written there by me; observed via
listing only.

## G. `papers/gated-read-batching/REFS.md` locator mismatch — **REAL**

```
sed -n '11p;66p' papers/gated-read-batching/REFS.md
11 → **Source of the verification not performed by the authors:** `docs/research/GATED_READ_PROVENANCE.md` (abbreviated **P**) in the
66 → | "Greshake et al. **2022**" indirect-injection citation | … (`G:49-51`, `STAGED_EXTRACTION_PROVENANCE.md:30-42`). | …
```

Line 11 declares only the abbreviation **P** for `docs/research/GATED_READ_PROVENANCE.md`; line 66
cites a `G:` locator. A `G:` abbreviation is introduced in `CLAIMS.md:11–15`, not in `REFS.md`. The
mismatch is real. **Claim 11 reproduced.**

> **Corrected 2026-10-16 (UFIX19 row-mapping re-check; pointer added by UFIX21):** the row map was re-run against the literal text. `papers/gated-read-batching/REFS.md:66` uses **`P:246`**, not a `G:` locator; the only `G:` locator is `REFS.md:68` (`G:49-51`); the `G:` legend already exists at `REFS.md:15` and `P:` is declared at `REFS.md:11`. So `REFS.md:11-15` is already correct and no `G:` legend needs adding. The findings above are left unrewritten as the record of what was seen when this report ran.

## H. Is the gate advisory or build-gating? — **BUILD-GATING (exit 1), not advisory**

From the script:

* `gate.sh` itself: `exit 1` on any HARD-FAIL (`UBUILD1.build.sh:697–699`).

  > **Superseded 2026-10-16:** the gate was replaced by the positive vocabulary checker (`cat > "$DEST/gate.sh" <<'GATE_EOF'` at `:771`, closing `:896`, `chmod +x` `:897`); `:697`–`:699` is now vocabulary-heredoc text. The hard-fail exit-1 path is `sys.exit(1)` at `:893`. Verify the anchor before relying on the number.
* The build captures the gate's status and propagates it:
  `set +e; bash "$DEST/gate.sh"; GATE_RC=$?; set -e` … `if [ "$GATE_RC" -ne 0 ]; then … exit "$GATE_RC"; fi`
  (`UBUILD1.build.sh:810–826`).

  > **Superseded 2026-10-16:** the return-code propagation moved with the gate and is now `set +e` `:1004`, `bash "$DEST/gate.sh"` `:1005`, `GATE_RC=$?` `:1006`, `set -e` `:1007`, and `exit "$GATE_RC"` `:1015`; `:810`–`:826` is now gate-internal Python. Verify the anchors before relying on the numbers.
* My full run's log tail:

```
BUILD COMPLETE — the exclusion gate FAILED (exit 1).
```

So a gate hard-fail makes the **build process exit 1**; the package as staged is unshippable *by the
build's own exit status*. UCURATE1's "the gate is a leak detector, not a shipping checklist"
(manifest:292) is a statement of *why* it fires, not a claim of advisory behaviour — the same
sentence says "the build **correctly stops at exit 1**". The two are consistent.

**One nuance worth recording:** the build materialises the tree **and git-commits it** (step
`git init + one commit`, `UBUILD1.build.sh:~782–806`) **before** running the gate. The failing
package therefore exists on disk; the exit 1 is the only blocking signal. This is design, not
mislabelling, but it means "the build exits 1" and "no package is produced" are not the same thing.

> **Superseded 2026-10-16:** the git step moved; `git init + one commit` is now `:977`–`:991` (`git -C "$DEST" init -q -b main` at `:983`, commit at `:985`–`:988`); `:782`–`:806` is now vocabulary-heredoc text. Verify the anchor before relying on the number.

## Other claims

* **Claim 3 (exit 1 + idempotent):** exit 1 on gate hard-fail confirmed above; two consecutive full
  builds produced the **same short commit sha `67716cc`**. Reproduced.
* **Claim 4 (prune fail-closed):** reproduced both directions (see B).
* **Claim 5 (`code/verify/` one file):** tree contains exactly
  `packages/exp12-encoder-crossover/code/verify/recompute-claims.py`; `run-verification.sh` and
  `scrub-uscrub1.py` are never staged. Reproduced.
* **Claim 7 (dropped documents):** `find` for `EXCLUDED* / REDACTION_REPORT* / RESIDUALS* /
  LICENCE_TODO* / SCRUB_REPORT* / INTEGRITY*` over the built package → **0**; likewise `variants/`,
  `redact.py`, `MANIFEST.json`, `OWED_CORRECTIONS.md` → 0. Reproduced.
* **Claim 8 (only transform = path neutralisation, 3 literal rules):** the only content rewrite in
  the script is the NEUTRALISE python block; its sole mutator is `new = new.replace(old, rep)` at
  `UBUILD1.build.sh:744` with exactly three rules. All `cat >` sites (lines 327, 398, 499, 523, 547,
  577, 612, 640) **author** files, they do not transform staged content. Reproduced.

  > **Superseded 2026-10-16:** the `PATTERNS_HARD` / `PATTERNS_REVIEW` heredocs named here were removed by unit ULICENCE3 and no longer exist. The gate is now the positive vocabulary checker whose heredoc opens `cat > "$DEST/gate.sh" <<'GATE_EOF'` (currently `:771`, closing `:896`, `chmod +x` `:897`), fed by `vocabulary/{english,code,public}.txt` (currently `:691`, `:695–743`, `:748–769`) and invoked at `bash "$DEST/gate.sh"` (currently `:1005`). Verify the anchors before relying on the numbers.
* **Claim 10 (gated-read-batching judged not packageable):** the manifest **does** say so (§12.3,
  manifest:~500). Reported, not re-litigated.

## Defects found in UCURATE1's own prose (neither changes the headline)

1. **CONTRA—** the `218` untransformed-ship-set figure (manifest:286) is not reproducible; the
   artifact gives **156**, and the build's own log reports **4** path occurrences in 2 files, not 66.
2. **OVERSTATED—** the pattern-list citation (manifest:7) points at
   `UBUILD1.build.sh:423–458`; the **HARD** heredoc is actually at `UBUILD1.build.sh:612–637`
   (patterns 613–636) and **REVIEW** at `UBUILD1.build.sh:640–647`. Lines 423–458 of the script are
   README prose. The *content* is transcribed correctly — only the location is wrong.

   > **Superseded 2026-10-16:** the `PATTERNS_HARD` / `PATTERNS_REVIEW` heredocs named here were removed by unit ULICENCE3 and no longer exist. The gate is now the positive vocabulary checker whose heredoc opens `cat > "$DEST/gate.sh" <<'GATE_EOF'` (currently `:771`, closing `:896`, `chmod +x` `:897`), fed by `vocabulary/{english,code,public}.txt` (currently `:691`, `:695–743`, `:748–769`) and invoked at `bash "$DEST/gate.sh"` (currently `:1005`). Verify the anchors before relying on the numbers.

---

## Verdict

| claim | result |
|---|---|
| 1. GATE FAIL, exactly 152, per-pattern | **reproduced (exact)** |
| 1b. own contrast 218 → 152 | **contradicted** (artifact: 156 → 152) |
| 2. exactly 58 files; fail-closed list | reproduced |
| 3. exit 1 on gate hard-fail; idempotent | reproduced |
| 4. prune fail-closed both directions | reproduced |
| 5. `code/verify/` = one file | reproduced |
| 6. anchors 907fa39=12, ad301ae=7 | reproduced |
| 7. dropped documents absent | reproduced |
| 8. only transform is 3 path rules | reproduced |
| 9. LICENSE MIT, no PolyForm | reproduced (conflicts with memo — stated, unresolved) |
| 10. gated-read-batching judged unpackageable | reproduced (manifest says so) |
| 11. REFS.md `G:`/`P:` mismatch | reproduced |
| H. gate advisory or gating | **build-gating (exit 1)** |

> **Superseded 2026-10-16:** the licence described here as MIT is now the PolyForm Non-Commercial 1.0.0 instrument, copied from `strategy/licence-templates/RELEASED-PIECE/` by `orchestration/units/UBUILD1.build.sh` (`LIC_SRC` `:575`, guard `:584`, sha256 `3d364676…f900`).

**Overall: PARTIAL.** The deliverable's operative claim — GATE = FAIL at exactly 152 over the
58-file ship set — survives independent re-derivation to the line. One supporting comparison number
(218) is contradicted, and one citation line-range is wrong.
