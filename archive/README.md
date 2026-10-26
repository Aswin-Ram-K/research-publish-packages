# archive/ — preserved, not deleted

This directory holds artifacts that were **sitting loose in the workspace root** and were
moved here by unit **USTRUCT**. Nothing here was deleted, edited or renamed: every file
keeps its original name and bytes. The archive exists so the root reads as a map rather
than a pile, while the evidence stays on disk and citable.

Moved here by USTRUCT: **2 files** (plus one empty directory tree removed, see below).

## `U5.3_red1.txt` (37,726 B, 1,043 lines)

The **pre-fix ("red") revision** of `src/resextract/docket/materialize.py` — a full Python
module dump, not a log. It is the copy from unit **U5.3**'s red→green cycle in which the
refusal guard was *absent*: compared with `U5.3_red2.txt` it lacks the `{"outside_target_root",
…}` unresolved-ref branch and the `MaterializeRefused` guard that raises when a plan has no
resolvable provenance references.

- **Came from:** workspace root (`./U5.3_red1.txt`), untracked in git.
- **Why preserved:** it is the *only* copy of that pre-fix revision. It is **not** a duplicate
  of `state/logs/U5.3_red1.txt` — that file (1,295 B) is the short *pytest* log; this one is the
  whole module. `sha256(U5.3_red1.txt) = f6bfde355b588d0d41aa942102a6f012c46b01ff0320e547a1827ac071ea3330`.
- **Referenced by:** `orchestration/handoffs/U5.3.json`, `orchestration/units/U5.3.md`,
  `orchestration/units/U0.15.md`, `orchestration/VERDICTS.md` and several `U8.*` handoffs, all of
  which still name the **root** path (they are historical records and were deliberately not edited).

## `U5.3_red2.txt` (38,370 B, 1,058 lines)

The **post-fix ("green") revision** of the same module — the same source snapshot *with* the
refusal guard restored. Together, red1 and red2 are the red→green transcript pair for the
materialize refusal guard.

- **Came from:** workspace root (`./U5.3_red2.txt`), untracked in git.
- **Why preserved:** same as above — the only copy of that revision; differs from the
  shortened pytest log at `state/logs/U5.3_red2.txt` (1,304 B). `sha256 = 68af787ff1f36401dd77adaf50a8ab698fd5a4d1d769d22711e5563af613d6f7`.
- Note: neither red file is byte-identical to today's committed
  `src/resextract/docket/materialize.py` (2,226 lines) — they are an earlier revision, which is
  exactly why they are worth keeping.

## The `file:` directory (REMOVED — it was empty)

The root also held a directory literally named **`file:`**. It was an accident: a shell
redirect that meant to split stdout/stderr spelled its target as a bare `file:...` path, and
the shell created that as a *relative directory name* instead. It was a 5-level directory tree
mirroring an absolute path —

```
file:/home/zer0null/reserach extarctor/state/
```

— containing **0 regular files and 0 other content** (verified with `find "file:" -type f` →
no output, and `ls -laR` showing only `.` and `..` at every level). It held no meaningful
data, so it was removed rather than archived (`rmdir` was used, which can only ever delete
*empty* directories — it would have failed had anything been inside). Its existence and exact
reconstructed path are recorded above so the record is not lost with it.
