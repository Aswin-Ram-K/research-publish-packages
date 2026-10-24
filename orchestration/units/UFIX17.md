# UFIX17 — apply UTRACE1's trace-pin corrections

**Bound:** 25 tool calls (**used 16**). **Status: done.**

**Purpose.** Apply the corrections derived in `strategy/TRACE_PIN_REVERIFICATION.md` to every
trace-dependent figure in this workspace, by **sweep** (grep the figure, classify every hit, edit) rather
than by repairing only the handed-over list.

## 1. Pinned artefact — recomputed by this unit (not taken from any citation)

`dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` (pinned-copy docket path; the
`## 1. The pinned artefact` table sits at `strategy/TRACE_PIN_REVERIFICATION.md:7-15`).

| field | measured here | UTRACE1 | verdict |
|---|---|---|---|
| bytes | **866,816** | 866,816 | matches |
| sha256 | `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb` | same | matches |
| lines / JSON records | **573 / 573**, 0 unparseable | 573/573 | matches |
| gated lines | **573** (every record's own `session` field matches `duval`) | 573 | matches |
| gate occurrences (pattern set `strategy/LEAD_PACKAGE.md` §1 "Gate-hit measurement", `:41-46`) | **712** | 712 | matches |
| mtime | 2026-10-08 06:25:11 -0500 | same | matches |

Live path re-measured at 2026-10-15 21:02:05: **1,624,082 B / 1087 lines /
sha256 `35687221b1a19d540534ff601ee233f67b814f643243bc933107ce703bff075d` / 1262 occurrences / 1087 gated
lines** — so the live file is *still moving*, exactly as UTRACE1 warned. `1,031` appears on no state as
a gate count.

Blob pair re-extracted by this unit (zlib read of `/home/zer0null/Duval/.git/objects`, no git):
`e25ac80f…` = **1,567,661 B / 1029 lines** / sha256 `92a45657…`; `2ec22a67…` = **1,570,243 B / 1031 lines**
/ sha256 `03fa52a6…` / **1205** gate occurrences / 1031 gated lines. Parent→HEAD delta = **+2,582 B**, so
`strategy/CONTAINMENT_CHECK.md` §2's old pair could not carry the ~700 KB growth it was used to show.

## 2. Sweep and classification (raw output: `scratch/ufix17/sweep.txt`)

Command: `grep -rn -I -E '1570243|1,570,243|1\.5 ?MB|1031|94495930|e25ac80f|2ec22a67|35687221|866816|866,816|1,624,082|1624082|1087|1205|0\.83 ?MB' .`
with `.git/`, `state/`, `archive/`, `jobs/`, `node_modules/` and `*.jsonl` excluded.

- **Class A — repaired (declared write paths):** 12 files, **26 edits** (24 in the batch patch, 2 in a
  follow-up). See §3.
- **Class B — stale figures in files OUTSIDE my write paths (reported, not edited):**
  - `docs/ACCEPTANCE_PROTOCOL.md`, trace-row item `:522` and L11 table row `:771` (same T5 class as the
    repaired `docs/LIVE_TARGET_NOTES.md:50`).
  - `orchestration/VERDICTS.md:335` and `:341` (`94495930` presented as the tracked trace's blob).
  - `orchestration/units/UPOLICY1.md:10`, `:33`, `:34` — the unit that authored the AGENTS clause.
  - `orchestration/units/UVER18.md:14` — verifier recomputation of the pin figures (correct when run).
  - `orchestration/handoffs/UPOLICY1.json:7-8` — recorded grep command strings (historical).
  - `orchestration/handoffs/V5.json:82, 97-98, 166, 256` — frozen verifier verdict, dated.
  - `strategy/VERIFICATION_REPORT_17.md:23` — "verified" D6's `1,570,243 B / 1031 hits` against
    `NC1_UNBLOCK.md:133-135`; **this is the stale-source failure mode precisely** (fidelity to a stale
    source is not truth). Dated record.
  - `strategy/VERIFICATION_REPORT_18.md:25-28, :35` — "match" for `866816` / `94495930` / growth
    `866816 → 1570243` against `strategy/CONTAINMENT_CHECK.md`; same failure mode. Dated record.
- **Class C — false positives (the token means something else):** `1031` as a *line number*
  (`orchestration/handoffs/U8.64.json:175`, `strategy/COPYRIGHT_DEADLINES.md:53`, build logs) and as
  numeric JSON values; `1087`/`1205`/`1624082` as unrelated result numbers or sha fragments under
  `scratch/`, `.ucurate1/`, `.uredact3/`, `experiments/`.
- **Class D — frozen/bulk copies:** `scratch/utrace1/gatecount.txt` (UTRACE1's raw evidence, correct),
  `scratch/uver18/AGENTS.md.pristine`, and the `state/**` mirror trees — 23 byte-identical pinned mirrors
  plus frozen unit trees, historical artefacts rather than guidance. **Scope limit:** `state/`, `archive/`,
  `jobs/` and the bulk `*.jsonl` corpora were excluded from the sweep because they are frozen data, not
  prose that cites figures.

## 3. Edits applied (verbatim before/after for all 26: `scratch/ufix17/changes.json`)

| file | anchor | change |
|---|---|---|
| `strategy/AUTHOR_DECISIONS.md` | D6 heading `:81` | "1.5 MB corpus" → "the trace corpus" |
| `strategy/AUTHOR_DECISIONS.md` | D6 option (i) `:83` | "1.5 MB trace corpus" → "trace corpus (pinned: 0.83 MB)" |
| `strategy/AUTHOR_DECISIONS.md` | D6 cost/buys option (i) `:93-96` | pinned **866,816 B / 573 records / 573 gated lines / 712 occurrences** + source path/sha |
| `strategy/AUTHOR_DECISIONS.md` | D6 cost/buys end `:97` | +one line: 1,031 was a live-path line count; no state reproduces it as a gate count |
| `strategy/NC1_UNBLOCK.md` | check C `:133-135` | pinned figures; superseded-1,031 note |
| `strategy/NC1_UNBLOCK.md` | route 1 `:189` | "1.5 MB / 1031-hit" → "pinned 0.83 MB (866,816 B / 712-occurrence)" |
| `strategy/NC1_UNBLOCK.md` | simulation note `:205` | "1.5 MB" → "0.83 MB pinned" |
| `strategy/NC1_UNBLOCK.md` | containment sentence `:257` | "older and untouched" → "unmodified **by this workspace's units**" + foreign-actor pointer |
| `strategy/NC1_FIX_PROPOSAL.md` | §B(i) corpus row `:118` | pinned figures; recorded live figure labelled as such |
| `strategy/NC1_FIX_PROPOSAL.md` | §B(ii).5 `:142` | "1.5 MB corpus" → "pinned 0.83 MB corpus" |
| `strategy/NC1_FIX_PROPOSAL.md` | containment item 6 `:169` | "target repo untouched" → "**no write by this workspace's units**" + root-not-untouched |
| `strategy/CONTAINMENT_CHECK.md` | §2 blob pair `:151-152` | +measured pair sizes, **+2,582 B** correction, `03fa52a6…` |
| `strategy/CONTAINMENT_CHECK.md` | §2 pin capture `:161-166` | qualifier: `94495930…` is the **workspace docket repo's** blob, absent from Duval; 573/712 stated; false "grep → no hits" replaced |
| `strategy/CONTAINMENT_CHECK.md` | §7 item 1 `:261-262` | growth dated to 18:50:03, live object named, **second move** to 1,624,082 B / 1087 lines dated 2026-10-15 21:02:05 |
| `strategy/CONTAINMENT_CHECK.md` | §7 item 1 tail `:264` | `94495930…` labelled the docket's own recorded blob, not a target object |
| `docs/LIVE_TARGET_NOTES.md` | report table, trace row `:50` | working-tree leg marked *recon-time*; current live `35687221` (1624082 B) added |
| `AGENTS.md` | trace-pin clause under `## Hard constraints`, `:82-87 → :82-88` | pinned figures now the cited numbers; growth only as a **dated observation**; clause length preserved; `## Current state` shifted `:94 → :95` |
| `orchestration/units/UCONT1.md` | attribution table, trace row `:30` | pair sizes (+2,582 B) + superseded live re-measurement |
| `orchestration/handoffs/UDECIDE1.json` | `nc1_corpus` evidence `:15` | recorded command preserved; `[CORRECTED UFIX17: …]` appended |
| `orchestration/handoffs/UNC1A.json` | `blocker` `:56` | recorded figure preserved; correction appended |
| `orchestration/handoffs/UNC1A.json` | `next_unit_hint` `:57` | "1.5 MB 1031-gate-hit" labelled live-path; pinned 0.83 MB given |
| `orchestration/units/UNC1A.md` | checks C/D bullet `:45` | pinned figures; superseded live figure labelled |
| `orchestration/units/UNC1A.md` | simulation bullet `:62` | same-class sweep hit: "1.5 MB corpus" → "0.83 MB pinned corpus" |
| `strategy/VERIFICATION_REPORT_10.md` | under the read-only bullet `:10-11` | one-line **dated pointer** only (see §4) |
| `strategy/VERIFICATION_REPORT_11.md` | under `Read-only honoured` `:10-12` | one-line **dated pointer** only (see §4) |

An incident worth recording: the first `UNC1A.json:57` edit inserted unescaped `"` inside a JSON string and
broke the handoff's JSON; caught by the mandatory parse check and repaired (escaped `\"`). Both edited
handoffs now parse.

## 4. Verifier reports — classification (`VERIFICATION_REPORT_10/11` vs `17/18`)

- **`VERIFICATION_REPORT_10.md`** and **`VERIFICATION_REPORT_11.md` are dated records of a past
  measurement** (each opens with its own verdict and a tool-call count/bound). Per the card they were
  **not rewritten in place**: each got a **one-line dated UFIX17 pointer** (2026-10-15) reading the old
  "untouched" claim as "**no write by this workspace's units**", because the audit's own conclusion
  (`strategy/CONTAINMENT_CHECK.md` §7 item 2, `:285-287`) is that foreign actors rewrote five root files
  and the trace.
- **`VERIFICATION_REPORT_17.md:23`** and **`VERIFICATION_REPORT_18.md:25-28` are the same dated class**,
  and fall **outside my write paths** — they are reported, not edited. They are the clearest evidence of
  the failure mode the card names: a verifier confirming a figure against a document that was already
  stale.

## 5. Verification run

- `sha256sum` / `stat` / record parse on the pinned copy (table §1); gate counts for pin, live, and both
  extracted blobs; all four JSON handoffs touched by this unit parse; pinned file byte-identical
  (866,816 B, `431605e6…`, mtime unchanged) after the edits.

**Blocker:** none. **Next hint:** a follow-up unit (fresh write paths) should repair the Class B sites —
notably `docs/ACCEPTANCE_PROTOCOL.md:522/:771`, `orchestration/VERDICTS.md:335/:341`,
`orchestration/units/UPOLICY1.md:10/:33/:34`, and add dated pointers to `VERIFICATION_REPORT_17.md:23` /
`VERIFICATION_REPORT_18.md:25-28`.
