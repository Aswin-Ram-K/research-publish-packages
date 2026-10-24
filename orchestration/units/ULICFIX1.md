# ULICFIX1 — Fix released-artifact licence file, re-freeze data release

**Purpose:** The released-artifact `COMMERCIAL.md` describes itself as a DRAFT template and links to
`../PLACEMENT.md`, which is not in the package. Replace the draft banner with a truthful statement that
commercial licensing is available on request; apply the same change to the template source; regenerate
`MANIFEST.json` via the package's own recorded procedure; rebuild the deposit zip; re-run the three
shipped tools and prove no published number moved.

**Hard bound:** 25 tool calls. If the manifest regeneration procedure cannot be found on disk, STOP and
report that as the blocker rather than hand-editing the manifest.

**Author's decision (verbatim constraint):** the file must state that **commercial licensing is available
on request**. Do not invent a price, a phone number or an email address.

**Write paths (nothing else):**
- `scratch/uneutral10/package/COMMERCIAL.md`
- `strategy/licence-templates/RELEASED-PIECE/COMMERCIAL.md`
- `scratch/uneutral10/package/MANIFEST.json`
- `scratch/ulicfix1/**`
- `strategy/RELEASE_LICENCE_FIX.md`
- `orchestration/units/ULICFIX1.md`
- `orchestration/handoffs/ULICFIX1.json`

**Do NOT:** touch `papers/`; call any network API; write outside listed paths; put any credential in any file.

## Tasks
1. Read both `COMMERCIAL.md` files; report exact draft text + dead link verbatim.
2. Replace the draft banner with a truthful "commercial licensing is available on request" statement.
   Keep the rest of the file's substance. **Do not touch the PolyForm Noncommercial body.**
3. Apply the same change to the template so a future emit is consistent.
4. Regenerate `MANIFEST.json` using the package's OWN recorded procedure (search `scratch/ufixpkg3/`,
   `scratch/utool1/`, `scratch/udtag1/` for `regen_manifest.py` / `rebuild_manifest.py`). Do not
   hand-edit. Run its own independent checker; report PASS/FAIL + missing/hash/size/unlisted counts.
5. Rebuild the zip into `scratch/ulicfix1/zenodo/` with the same member list + filename pattern.
   Extract to a separate dir and `diff -r` against the payload; report diff output and new zip sha256.
6. Re-run all three shipped tools in the package; report each literal exit code and
   `recompute-claims.py`'s verdict line. Prove no published number moved.
7. Report new `MANIFEST.json` sha256 + byte size, new zip sha256 + byte size, exact diff of edits.

## Evidence log
- Draft banner (verbatim, both files): `> **DRAFT — template for the author to place.** See [`../PLACEMENT.md`](../PLACEMENT.md).`
  Dead link: `../PLACEMENT.md` (absent from the 29-member payload; members are root-relative).
- Replacement (both files): `> **Commercial licensing is available on request.** See "How to obtain a commercial licence" below.`
  Only line 3 changed; the PolyForm/Noncommercial body untouched (LICENSE unchanged, sha `fdf6e69f…`).
- Procedure found: `tools/package/regen_manifest.py` (docstring cites authority `scratch/uneutral10/manifest.py:38-44`);
  `scratch/uauclean1/after_run2.json` is byte-identical to the pre-fix MANIFEST.json, so the tool reproduces the shipped convention.
- Regen: `--package scratch/uneutral10/package --no-note --generated-utc 2026-10-17T22:00:21Z` →
  `files_on_disk: 29 bytes_total: 831775 manifest_self: f8337fc2030c938f`, `added: [] changed: 1` (COMMERCIAL.md only).
- Checker `tools/package/check_manifest.py`: `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`,
  `manifest_self_recomputes=True`, `VERDICT PASS`, exit 0.
- Zip rebuilt 29 members (0 dir entries) → `scratch/ulicfix1/zenodo/`; extraction `diff -r` vs payload EMPTY, before and after the tools ran.
- Tools exit codes 0/0/0; `recompute-claims.py`: `VERDICT: PASS`, `ALL PUBLISHED NUMBERS REPRODUCED: True`.
- New digs: MANIFEST.json 11043 bytes sha `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02`;
  zip 169869 bytes sha `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610`.
- Evidence file: `scratch/ulicfix1/EVIDENCE.txt`. Full write-up: `strategy/RELEASE_LICENCE_FIX.md`.
