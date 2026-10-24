# UFIXDRIVER1 — close the two second-package gaps in the generalised build driver

Workspace: `/home/zer0null/reserach extarctor`. Parent: `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.

## Purpose (one)

Close the two real defects a verification unit found in the generalised package
builder (`orchestration/units/UBUILD1.build.sh` + `orchestration/packages/*.toml`),
both about a SECOND package behaving differently from the first.

## The two gaps

1. **Ship-list tripwire only guards the default package.** The check that catches
   drift between the driver's built-in default block and the manifest fires only
   when `PKG_SLUG = DEFAULT_SLUG`. A non-default package can declare a
   `ship_staged` that disagrees with the tree it pins and nothing in the build
   notices. Close: for ANY package, assert `ship_staged` exactly equals the file
   set of the manifest's `promoted_san_src` (under the manifest's inclusion rule:
   every regular file, `.git` excluded), fail closed with a named FATAL, BEFORE
   the first destructive step. The check is derived from the manifest itself.
2. **Root README index is overwritten.** `cat "$M_README_HEAD" > "$DEST/README.md"`
   writes a single-package-shaped root README, so a second package replaces the
   first entry. Close: root README becomes a manifest-driven, accumulating INDEX
   (one row per package, deterministic order by slug) that preserves other
   packages' entries and their trees.

## Constraints honoured

- `/home/zer0null/Duval` strictly read-only; no `git` run against it.
- Only declared write paths touched. Builds only under `scratch/ufixdriver1/**`.
- Do not weaken: licence sha256 guard, fail-closed exclusion gate, never-ship
  checks, no-package-digest-pinned rule. Do not touch `PROMOTED_SAN_SRC` pin line.
- No new number not read from disk or measured.

## Hard bound

20 tool calls. Stop and report `partial` if the red/green proof or the
two-package index proof cannot be produced.

## Write paths (exactly)

- `orchestration/units/UBUILD1.build.sh`
- `orchestration/packages/**`
- `tests/test_package_build.py`
- `strategy/PACKAGE_BUILD.md`
- `orchestration/units/UFIXDRIVER1.md`
- `orchestration/handoffs/UFIXDRIVER1.json`
- `scratch/ufixdriver1/**`
