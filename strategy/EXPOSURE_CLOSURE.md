# EXPOSURE_CLOSURE — the live exposure was closed on 2026-10-15; what that does and does not do

**Unit:** UCLOSE1 · **Date of all checks in this file:** 2026-10-15 (UTC) · **Target repo:** strictly read-only, never written, no `git` run there · **Not legal advice.**
**Companion:** corrects [`DISCLOSURE_INVENTORY.md`](DISCLOSURE_INVENTORY.md) (see its §10 correction block). Supersedes the *live* finding of [`ARCHIVE_WINDOW_CHECK.md`](ARCHIVE_WINDOW_CHECK.md) (UARCH1) — which this unit does **not** own and did not edit.
**Every HTTP code, hash, byte count and commit id below was produced by a command this unit ran or a fetch it made. Nothing is inherited on trust.**

---

## 0. Headline

**The live exposure UARCH1 found at ~16:00 is closed.** An unauthenticated fetch of the pre-rewrite Consonance source, its AGPL licence, the whole-tree tarball, and the public paper all now return **HTTP 404**; the repository reports **`visibility: PRIVATE`**; public repo count fell **19 → 18**.

**Three distinctions must travel with that sentence, or it overstates the fix:**

1. **Retrieval is closed. Deletion is not done.** The unreferenced objects still exist in GitHub's storage and are still served *to the authenticated owner* — this unit proved that by fetching the same file back through an authenticated route (§3).
2. **Copies already taken are not recalled.** The repository was publicly fetchable until today. Privacy is prospective.
3. **`forkCount = 0`** — no fork preserves a copy. That part is genuinely clean, and it is the strongest true statement available (§3).

`private` is a *door*, not an *eraser*.

---

## 1. What I observed, first-hand

### 1.1 The exact URLs and codes

All fetched unauthenticated with `curl -s -o /dev/null -w '%{http_code}'`, 2026-10-15.

| URL | Code observed by UCLOSE1 | Before (UARCH1, ~16:00) |
|---|---|---|
| `raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/89003e70/consonance/src/journal.ts` | **404** | 200, 46,450 B |
| `raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/89003e70/consonance/src/dag.ts` | **404** | 200, 44,468 B |
| `raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/89003e70/consonance/LICENSE` | **404** | 200, 34,523 B (AGPL-3.0) |
| `raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/main/findings/PAPER-DERIVATION.md` | **404** | 200 |
| `codeload.github.com/Aswin-Ram-K/publish-present-compete/tar.gz/89003e70` | **404** | HTTP/2 200, 481 entries |
| `github.com/Aswin-Ram-K/publish-present-compete` | **404** | 200 (public repo page) |
| `api.github.com/repos/Aswin-Ram-K/publish-present-compete` | **404** | 200 |

The short prefix `89003e70` was expanded from UARCH1's own handoff to the full object id
**`89003e7069c9ad79c40d91982720751b1ddf0360`**, and the four object URLs were re-run against the **full** SHA as well — **all 404**. So the closure is not an artifact of an ambiguous short ref.

**Control, so the 404s are not read as a broken network:** `raw.githubusercontent.com/Aswin-Ram-K/ai-pe-deck/main/README.md` → **200**. A public repository on the same account still serves; the 404s are about *this* repository's visibility, not about the fetcher.

### 1.2 Repository state

```
gh repo view Aswin-Ram-K/publish-present-compete --json visibility,isPrivate,forkCount
  -> {"forkCount":0,"isPrivate":true,"visibility":"PRIVATE"}

gh repo list Aswin-Ram-K --limit 200 --json visibility  -> PUBLIC count = 18
gh repo view Aswin-Ram-K/publish-present-compete --json forkCount -> 0
```

**19 public repos before → 18 after.** `publish-present-compete` moved to the private set. `forkCount` is **0**, before and after.

### 1.3 What proves the objects were not deleted (the part that matters)

With the owner-authenticated `gh` token, the **same unreferenced object** still resolves:

```
gh api repos/Aswin-Ram-K/publish-present-compete/commits/89003e7069c9ad79c40d91982720751b1ddf0360
  -> {"sha":"89003e7069c9ad79c40d91982720751b1ddf0360",
      "date":"2026-10-10T06:26:07Z",
      "tree":"1aadb1ef509824bd9219e6a917fdf059afcd2f03"}

gh api "repos/Aswin-Ram-K/publish-present-compete/contents/consonance/src/journal.ts?ref=89003e7069c9ad79c40d91982720751b1ddf0360"
  -> {"name":"journal.ts","size":46450}
```

`journal.ts` is still **46,450 bytes** — the same byte count UARCH1 measured when it was live. **The object is intact and served.** What changed is the *audience*: unauthenticated callers get 404, the owner still gets the file. This is the single most important fact on this page. Nothing was purged.

---

## 2. The profile README edit

**Commit confirmed, and its "before" state re-derived from the repository's own history rather than taken on trust:**

```
gh api repos/Aswin-Ram-K/Aswin-Ram-K/commits/2f8d09213503
  -> sha  2f8d092135039a8b6da5e1b3797833d144b60f96
     msg  "Profile: remove capability-kernel mechanism description"
     date 2026-10-15T21:26:50Z
     parent 73ffa8e4b4523e37b3826777571fb2dbb35e404b
     (this is also the current latest commit on the profile repo)
```

String probe, `grep -c` over the README fetched from each ref:

| String | Parent `73ffa8e4` (before) | Current `main` (after) |
|---|---|---|
| `Capability-materialisation` | **1** | **0** |
| `rather than by refusal` | **1** | **0** |
| `byte-identical when the capability` | **1** | **0** |

README size fell **2,352 B → 2,023 B** (`curl` returned `http=200 bytes=2023` for the current file).

**Confirmed:** the mechanism paragraph existed in the public profile README immediately before the edit, and the three strings are absent from the public file now. This unit verified *both* sides — the "before" by fetching the parent commit, not by trusting the orchestrator's account of it.

---

## 3. What `private` does and does NOT do

### It DOES stop unauthenticated retrieval — proven
Every object URL that returned 200 at ~16:00 returns **404** now, at both the short and the full SHA (§1.1). The whole-tree tarball is gone from the anonymous channel. `api.github.com` 404s anonymously. This is a real, measured change in who can fetch the work.

### It does NOT delete the unreferenced objects
Proven in §1.3: the commit and the 46,450-byte `journal.ts` are still served to the authenticated owner. The bytes remain **in GitHub's storage**, unreferenced by any branch, reachable only by a caller GitHub recognizes as authorised. **The only things that remove them are a purge request to GitHub Support for unreferenced objects, or deleting the repository.** Both are account actions; **the author has stated he will handle this himself**, so this unit took none of them and changed no repository setting.

### It does NOT recall anything already fetched, cloned or cached
Anyone who fetched during the public window holds their own copy. Privacy cannot reach it. The honest statement: *the implementation may have been obtained by an unknown party during the window, and nothing available now can establish that it was not.* (The inventory §7.1 already names this as the highest-value unanswerable question.)

### On the archive channel — a finding, explicitly NOT reassurance
UARCH1 searched the archive channel and found **nothing**: Software Heritage has **no repository of this author at all**; Wayback returned **0 captures** across the 8 URLs it queried; GH Archive carried **0 mentions**. That is a finding **about the archive channel only**. It is **not** evidence about the direct channel, which was open and serving 200s until today — and the direct channel is the one that matters, because a `git clone` or a `curl` needs no archive.

### `forkCount = 0` — genuinely good news, stated plainly
**No fork of `publish-present-compete` exists.** No other account holds a GitHub-hosted copy that privacy would not reach. Combined with the archive finding, the *known* mirror population is empty. This is the strongest true comfort in this file. It is not a guarantee that no *unhosted* copy exists — a clone on someone's disk leaves no trace here.

### The AGPL-3.0 grant on any copy taken during the window — a residual, not an alarm
UARCH1 read the licence text itself at the live URL: 34,523 B opening *"GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007"*. AGPL-3.0 is a grant, not a restriction. **A copy lawfully obtained during the window carries that licence for that copy, and the author cannot revoke it** — the permission already attached. This does not make the work public now; it constrains what the author can do about a copy that already exists. Recorded as a residual, without alarm.

---

## 4. Residual public surface after the closure — a decision list, not a settled answer

What is **still** publicly visible about this work at 2026-10-15:

| # | Residual | Verified how | Author's decision? |
|---|---|---|---|
| R1 | The profile README still carries a **`bubblewrap, capability-based security, Merkle-DAG state`** skills line. | Current public README fetched (`http=200`, 2,023 B); `bubblewrap` → 1 occurrence, `Merkle-DAG` → 1. | **Yes.** The orchestrator deliberately **left this alone** as generic technique keywords — each is standard public vocabulary. Keep or trim is the author's call. |
| R2 | The profile README's **`Consonance`** link now points at a **private repository**, so it is a **dead link** to every visitor. | `Consonance` → 1 occurrence in the current README; `Consonance` repo `visibility: PRIVATE`; `github.com/Aswin-Ram-K/publish-present-compete` → **404**. | **Yes.** A dead link still *names* the project. Leave it, remove it, or point it elsewhere. |
| R3 | The **disclosure event itself cannot be undone.** The MIT documents (WHITEPAPER, PAPER-DERIVATION, DECISION_LOG, experiments, findings — inventory P1–P9) and the AGPL `consonance/` tree were publicly fetchable for the window. Privacy stops *future* retrieval; it does not un-publish. | Inventory §1 P1–P10; UARCH1's 200s; this unit's 404s. | **Yes — and this is the consequential one.** It is a legal/strategic question (prior art, trade-secret status), outside this unit's remit. **Not legal advice.** |
| R4 | The profile README hosted the mechanism paragraph for roughly **seven days** (public ≤ 2026-10-08 → removed 2026-10-15T21:26:50Z), longer than the ~27.5 h repository window, in a plain file crawlers read. The edit closes future retrieval; it recalls no index snapshot or copy. | Parent-commit probe (§2); UARCH1's window measurement. | **Awareness item.** A targeted re-crawl request is the only lever, and it is optional. |
| R5 | The **other 17 public repos** besides the profile README. UDISC2 swept all 18 and found **no mechanism disclosure**; this unit re-verified the **set is unchanged** — same 18 names, no additions, no newly-public repo. | `gh repo list` diff against the inventory §3 table (18 PUBLIC names, identical). | **Yes.** Advisory: re-verify **contents**, not membership, if the author wants belt-and-braces. **This unit did not re-read the 17 repos' contents** — budget bound, stated as a limit not a clearance. |

**Net:** after the closure the *only* public surfaces that mention this work are the profile README (R1, R2, R4) and whatever third parties took copies during the windows (R3). Everything else is behind authentication.

---

## 5. `UNVERIFIED` / limits of this unit

1. **Whether any third party fetched the source during the window.** Not determinable from public data (inventory §7.1). The closure does not change this.
2. **Whether GitHub keeps serving `89003e7069c9…` to the authenticated owner indefinitely.** It does today (§1.3). GitHub's retention of unreferenced objects is not a documented guarantee I can cite.
3. **Contents of the other 17 public repos** were not re-read (R5) — UDISC2's sweep stands; membership was re-confirmed here.
4. **Whether a purge request or repository deletion has been filed.** The author said he will do it himself; no action was observable and none was taken by this unit.
5. **The legal weight of the prior disclosure** (R3) — no primary source fetched. Out of scope.
6. **`strategy/ARCHIVE_WINDOW_CHECK.md` still asserts the live exposure as current.** That file is outside this unit's write paths and was **not** edited. Its §"Old head reachable" / "Source file" / "Whole-tree download" rows describe a state that no longer holds. **It needs its own dated correction by a unit that owns it.** Flagged, not fixed.

---

## 6. Provenance and read-only discipline

- **Nothing was changed on GitHub.** Only `gh repo view`, `gh repo list`, and `gh api` **GET** calls; only `curl` GETs. No repository setting, visibility, branch, issue, or object was modified. No write to any GitHub repository.
- **No `git` was run in `/home/zer0null/Duval`**, and it was never written to.
- **Write paths touched — exactly four:** `strategy/EXPOSURE_CLOSURE.md` (this file), `strategy/DISCLOSURE_INVENTORY.md` (appended correction block), `orchestration/units/UCLOSE1.md`, `orchestration/handoffs/UCLOSE1.json`. No other file was edited. No concurrent unit was running.
- **Network:** GET-only to `raw.githubusercontent.com`, `codeload.github.com`, `github.com`, `api.github.com`. No server started, no plugin mounted.
