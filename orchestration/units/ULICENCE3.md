# ULICENCE3 — licence posture in the publish package

**Purpose.** Make `orchestration/units/UBUILD1.build.sh` emit the release licence
posture the author decided: source-available (PolyForm Noncommercial 1.0.0) for
code/eval/gate, CC BY 4.0 for paper text, no public licence for the core system.
**Status: partial** (all four edits landed and are verified by a build; the built
package's own gate then correctly FAILS on today's material — see Blocker).
**Hard bound:** ≤30 tool calls (used 29). Write paths honoured; the DEST used for
every run was `scratch/ulicence3/rel/research-publish-packages`; the real
`/home/zer0null/research-publish-packages` was never touched; `/home/zer0null/Duval`
was never written, never git-invoked.

## The four edits (all inside `orchestration/units/UBUILD1.build.sh`)
1. The MIT heredoc (`cat > "$DEST/LICENSE" <<'LICENSE_EOF'` … `LICENSE_EOF`) is
   replaced by a block that copies `strategy/licence-templates/RELEASED-PIECE/`
   `{LICENSE,COMMERCIAL.md,CONTRIBUTING.md}` into the package (one authoritative
   copy, sha256-guarded for LICENSE), appends the **Scope** clause, and writes
   `packages/*/paper/LICENSE` (CC BY 4.0). Root README's `## Licensing` now extracts
   the Case B paragraph verbatim from `strategy/licence-templates/README-PARAGRAPHS.md`
   and appends the per-directory breakdown; the package README and the root licence
   table row (`code **PolyForm NC 1.0.0** · paper text **CC BY 4.0**`) and the git
   commit message follow. Author identity strings are NOT known: `<YEAR>`,
   `<COPYRIGHT HOLDER>`, `<CONTACT>` (Case B) and `<CONTACT EMAIL OR URL — author to
   fill in>` (COMMERCIAL.md:44) ship as declared placeholders.
2. Scope split: root `LICENSE` carries a closing `## Scope` section that defers the
   paper text to each package's `paper/LICENSE`; that file states it is CC BY 4.0
   "and NOT under the repository root LICENSE".
3. READMEs: root, package, `code/` and the shipped `code/harness/README.md` — no
   licence instrument names MIT (see evidence).
4. `gate.sh`'s 24-pattern HARD denylist is replaced by the §D.2 positive vocabulary
   checker: `vocabulary/{english.txt,code.txt,public.txt}` + an inline Python checker
   that FAILS any token that is not tag-grammar, a declared public identifier, or
   generic English. It no longer excludes itself, and the build still `exit "$GATE_RC"`.

## Evidence (verbatim in `orchestration/handoffs/ULICENCE3.json`)
- Before/after of the replaced heredoc: `scratch/ulicence3/heredoc-before-after.txt`
  (extracted from `scratch/ulicence3/patch.diff`, 487 changed lines).
- Emitted `LICENSE`: **6219 bytes**, sha256 `16e51b3dc1114cae3e53f1fa71306accf4d8f2a1119f6fff0fd4fdc1e0d13035`;
  its first 5662 bytes are **byte-identical** to the template (sha256
  `25aa637ba1689e87ad34c5acc25464a4eaaa2f5b2c84e3dc4d7ed84158277cfe`) — `diff` vs
  template is 12 lines, all the deliberately appended Scope section.
- `grep -r -i -o '\bMIT\b'` over the emitted tree = **8**, all third-party model
  attributions (microsoft/deberta-v3-base is MIT) or the frozen dictionary word
  `mit`; **no licence or README names MIT**.
- Gate red→green: clean control tree `exit 0`; injecting `grantPolicy` **and**
  `familyId` (an in-corpus identifier the old 24-pattern list could not see) →
  `exit 1`, both flagged; removing them → `exit 0`.

## Blocker / remainder
The positive checker correctly rejects the package as built from today's material:
**95,597** flagged tokens, dominated by in-stimulus internal identifiers
(`nCandidate`, `nKind`, `nSituation`, `clanId`, `ruleId`, `familyId`, `goldIndex`)
in `code/harness/data/{train,dev}.jsonl` and `corpus.json`. §D.2 step 0 presumes the
code-agnostic tree (the UCURATE1 retagging) which does not exist yet. Declaring
those identifiers into `vocabulary/` was rejected: it would ship the leak as
vocabulary. `strategy/PUBLISH_PACKAGE_MANIFEST.md` was not updated (call bound).
