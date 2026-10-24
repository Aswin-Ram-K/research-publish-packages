# Unit UFIXPKG7 — apply the classifier's four reference fixes

**Purpose:** A report-only classifier (`strategy/PARENT_REFERENCE_CLASSIFICATION.md`) reduced a
large-looking set of parent-project references to a small, specific set. Apply exactly those fixes;
change nothing else.

**Hard bound:** 20 tool calls. If any fix cannot be verified, STOP and report `partial`.

**Declared write paths (exactly these):**
- `papers/encoder-crossover-190/**` (incl. `submission/`)
- `scratch/uneutral10/package/fixture/reflex-decisions.ts`
- `strategy/RELEASE_BUILD_3.md` — append only
- `orchestration/units/UFIXPKG7.md`
- `orchestration/handoffs/UFIXPKG7.json`
- `scratch/ufixpkg7/**`

**Never:** write in `/home/zer0null/Duval`; run any `git` command against it; touch
`orchestration/units/UBUILD1.build.sh`, `orchestration/packages/**`, `tests/**`, any `scratch/*/dest/`.

**Tasks:**
1. Fix 1 — `papers/encoder-crossover-190/MANUSCRIPT.md:301` generic parent reference; regenerate
   `submission/main.tex` via `scratch/uprep1/md2tex.py` (run twice, prove byte-identical); rebuild
   tarball, prove exactly one member byte-identical to on-disk `main.tex`.
2. Fix 2 — replace five dangling `see D43 §3` pointers at
   `scratch/uneutral10/package/fixture/reflex-decisions.ts:39,40,380,695,1889` with the in-payload
   phrasing named by the classifier.
3. Fix 3 — existence-check the five `submission/main.tex` paths (230,335,387,412,419); apply generic
   treatment to any that resolve into the parent private tree; leave genuine reader citations.
4. Fix 4 — extend/remap the tag regex `^(?:K|F|S|C|R|D)[0-9][0-9]$|^TAG_[0-9][0-9]$` to accept `P01`–`P05`;
   red→green control; no arbitrary-word permissiveness.

**Proof:** recompute-claims.py, parse_fixture.py, compare.py before/after with literal exit codes;
`recompute-claims.py` still PASS + exit 0. Tarball re-extraction. Before/after per file touched with
each before-string asserted to occur exactly once before writing. No new numbers — every value must
already exist on disk with its source named.

**Status:** in progress.
