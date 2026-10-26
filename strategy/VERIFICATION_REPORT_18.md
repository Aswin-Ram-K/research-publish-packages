# UVER18 — verification of UPOLICY1's AGENTS.md containment edit

**overall: pass.** Independent, non-author re-check of `AGENTS.md` against
`strategy/CONTAINMENT_CHECK.md`. Every figure, every structural claim, the pin
digest, and a red→green revert all reproduce. No contradicted / overstated /
not_reproduced / unverified items.

## A. Are the two new bullets present and actionable?
- `AGENTS.md:77-81` — **Never run a bare `git status` against a target.** Names the
  forbidden form, both compliant forms (`--no-optional-locks` *or* `GIT_OPTIONAL_LOCKS=0`),
  the mechanism (`git status` refreshes `.git/index`, so it writes), the preference
  (read files over invoking git), and the measured exposure. **Actionable.**
- `AGENTS.md:82-87` — **Trace-dependent claims cite a pinned copy, not a live path.**
  Requires *path and digest* (sha256 + blob), names the pin, and shows why (the live
  file grew mid-batch). **Actionable.**
Neither is vague: both give a testable condition ("must pass X", "must name path and digest").

## B. Every cited number, checked against the source line
| Rule figure | Source line | Source text (verified) | Verdict |
|---|---|---|---|
| 136 handoffs / 194 target-referencing command strings | `strategy/CONTAINMENT_CHECK.md:179` | "**136** handoffs reference `/home/zer0null/Duval`; **194** target-referencing command strings." | match |
| 62 ran a plain `git … status` without `--no-optional-locks` | `strategy/CONTAINMENT_CHECK.md:184` | "**62 units issued a plain `git -C /home/zer0null/Duval … status`** (no `--no-optional-locks`) as an actual command" | match |
| 0 target-mutating verbs | `strategy/CONTAINMENT_CHECK.md:191` | "**No unit ran a target-mutating git verb.**" | match |
| pin path | `strategy/CONTAINMENT_CHECK.md:161` | `.../duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` | match |
| 866816 bytes | `strategy/CONTAINMENT_CHECK.md:162` | "is **866816 bytes**" | match |
| blob `94495930fbf0fd991b14c1e4de79d87a93fce9ae` | `strategy/CONTAINMENT_CHECK.md:162` | "git blob `94495930fbf0fd991b14c1e4de79d87a93fce9ae`" | match |
| sha256 `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb` | `strategy/CONTAINMENT_CHECK.md:163` | same string | match |
| growth 866816 → 1570243 bytes | `strategy/CONTAINMENT_CHECK.md:261-262` | "grew from **866816** B at our pin to **1570243** B now" | match |

No figure is wrong. A rule citing a wrong number would be worse than no citation; none is.

## C. Pin identity — computed, not inherited
`sha256sum` on the pinned file itself:
`431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb  dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl`
`stat` size = **866816**; `git hash-object` blob = **94495930fbf0fd991b14c1e4de79d87a93fce9ae**.
All three agree with the rule and the source. **Digest independently verified, not inherited.**

## D. Structural claims
- Real size: **6647 bytes** — matches UPOLICY1's report.
- Real line count after edit: **96**; pre-edit (`HEAD:AGENTS.md`) is **85**. 85 + 11 = 96 — consistent.
- Headings, by `grep -n '^#'`: **1** (title), **6**, **19**, **65**, **72**, **94**. Exactly as claimed;
  `diff` of HEAD headings vs current headings → **HEADINGS IDENTICAL** (no heading text altered).
- `## Current state` was at **83** pre-edit, **94** now: +11, exactly the insertion. UPOLICY1's "83 → 94" confirmed.
- `git diff HEAD -- AGENTS.md` is a **single hunk**, `@@ -72,8 +72,19 @@`: 13 insertions, 2 deletions
  (the 2 deletions are the reflowed sharpened bullet's two lines). Hunk content is *only* the two new
  bullets plus the `lock-free` sharpening. **Nothing else was changed.**
- Sharpening of `AGENTS.md:74-76` is present verbatim, and the pre-edit before-string occurs
  **exactly once** in the 85-line HEAD version (`mtime-sweep` count = 1).

## E. red→green (scratch copy — `AGENTS.md` was not edited)
Copy at `scratch/uver18/AGENTS.md.reverted`, lines 77-87 deleted with `sed`.
- GREEN (`AGENTS.md.pristine`, 96 lines): `P1(git-status rule)=1  P2(pinned-copy rule)=1`
- RED (`AGENTS.md.reverted`, 85 lines): `P1(git-status rule)=0  P2(pinned-copy rule)=0`
- Literal `grep -n 'Never run a bare\|Trace-dependent claims cite a pinned copy' scratch/uver18/AGENTS.md.reverted`
  → no output, `grep exit=1` (no match).
The check can fail — the rules vanish when the bullets are removed and return when restored.

## Lists
- **contradicted:** none.
- **overstated:** none. (Minor precision note, not an overstatement: `AGENTS.md:81` says "**62** ran a
  plain status" where the source counts **62 units**. The figure is right; the noun is a unit count.)
- **not_reproduced:** none.
- **unverified:** none. The pin digest, the only thing that could have been merely inherited, was
  recomputed from the file.

## Containment
No git command was run against `/home/zer0null/Duval`. The only git calls executed were inside this
workspace under `GIT_OPTIONAL_LOCKS=0`. `/home/zer0null/research-publish-packages` was not written.
`AGENTS.md` was not edited; the revert was performed on a copy under `scratch/uver18/`.

**Blocker:** none. **Next unit hint:** accept the UPOLICY1 edit as verified.
