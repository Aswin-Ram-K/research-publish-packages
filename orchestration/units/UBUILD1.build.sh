#!/usr/bin/env bash
# =============================================================================
# UBUILD1.build.sh — the build for /home/zer0null/research-publish-packages
#
# AUTHORISED BY THE ORCHESTRATOR as an additional write path for unit UBUILD1.
#
# This script IS the build DRIVER. Run it once from a shell that can write the
# target, naming the package to build:
#
#     bash orchestration/units/UBUILD1.build.sh --package gated-read-batching
#
# Per-package values live in orchestration/packages/<slug>.toml -- NOT here. The
# literal default block further down is the built-in default package
# (`gated-read-batching`); when that slug is selected the manifest must agree
# with it or the build stops. See strategy/PACKAGE_BUILD.md.
#
# PROPERTIES
#   * idempotent — it `rm -rf`s the target first, then rebuilds it from source and
#     commits. A second run produces the same tree and, because the commit date is
#     pinned, the SAME commit SHA. Verified: two consecutive runs both gave
#     sha 2b0e... (see the run log recorded in orchestration/units/UBUILD1.md).
#   * self-contained — copies nothing from /tmp and depends on no prior state.
#     Everything comes from the read-only source workspace (via `cp -r`) plus the
#     authored files written by this script itself.
#   * honest — it runs ./gate.sh and EXITS NON-ZERO if the gate hard-fails,
#     having printed every hit with file and line. It never edits source material
#     to make the gate pass.
#
# INPUTS (all optional; the defaults are the real thing)
#   SRC            read-only source workspace   default /home/zer0null/reserach extarctor
#   DEST           the new repository           default /home/zer0null/research-publish-packages
#   COMMIT_DATE    pinned so re-runs are byte-identical.
#                  Set COMMIT_DATE="$(date -Iseconds)" for a real timestamp.
#   SAN_SRC_OVERRIDE
#                  absolute path of ANY sanitised tree to stage from. Highest
#                  precedence; honoured only from the environment, never guessed
#                  from disk. Unset = the PROMOTED default below.
#   SAN_SRC_FROZEN_OVERRIDE
#                  set to 1 to select the FROZEN original sanitised tree,
#                  $SRC/repro/encoder-crossover-190-SANITISED. It is no longer
#                  the default but stays reachable so the pre-promotion input
#                  remains reproducible:
#                    SAN_SRC_FROZEN_OVERRIDE=1 bash orchestration/units/UBUILD1.build.sh
#
#   THE PROMOTED DEFAULT (UWIRE2) is $SRC/scratch/uneutral10/package — the
#   chosen release artifact. Its residual-identifier and gate-count figures are
#   not recorded here: the ones this block used to carry describe the SUPERSEDED
#   tree; current measurements are in strategy/BUILD_PIN_CHANGE.md. The ship-list,
#   licence plumbing, anchor asserts and gate are IDENTICAL on both trees — only
#   the staged bytes change. Every build prints ONE machine-greppable line saying
#   which tree it read and whether that is the promoted default:
#     SAN_SRC WIRING: tree=<path> promoted_default=<yes|no>
#   Selecting a non-default tree never fails the build by itself; it is loud, not
#   interactive. See strategy/BUILD_WIRING.md.
#
# =============================================================================
# THE SHIP-LIST  (decided by unit UCURATE1 — see strategy/PUBLISH_PACKAGE_MANIFEST.md)
#
# This build is FAIL-CLOSED: it ships exactly the files named in SHIP_STAGED and
# SHIP_AUTHORED below, and NOTHING ELSE. An unlisted file does not ship, and a
# listed file that is missing from the source is a FATAL error. A drop-list would
# have been fail-OPEN — a file nobody remembered to list would quietly ship — so
# the ship-list was chosen for exactly that reason. The staged list is enforced by
# pruning the copy against it; the authored list is written by this script.
#
# THE LINE DRAWN between "reader-load-bearing" and "record of our process":
#   * reader-load-bearing  = a reader needs it to (a) recompute a published
#     number from bytes inside this package, or (b) understand the manuscript's
#     claims and their limits. It SHIPS, even when it carries a residual
#     reference to an internal document name — that reference is declared, not
#     fixed, because fixing it would mean rewriting shipped evidence.
#   * record of our process = it documents how the sanitisation/curation was
#     performed (redaction report, exclusion inventory, licence to-do list,
#     scrub report, correction ledger, hash table of the unshipped tree). It is
#     DROPPED, because it names or locates the private side and a reader cannot
#     verify anything with it.
#
# WHAT A READER LOSES (every drop, spelled out):
#   * code/verify/VERIFICATION.txt, RECOMPUTE-CLAIMS.txt, RESIDUAL-SCAN.txt,
#     integrity-table.md, redaction-log.json — generated run output / hash tables
#     of the process. The reader loses the recorded run log; they keep the
#     SCRIPTS that regenerate the numbers (recompute-claims.py).
#   * code/verify/run-verification.sh — the UREDACT1 acceptance test. It cannot
#     run here at all: it requires the private AS-AUDITED tree as a sibling
#     (`O=dirname($S)/encoder-crossover-190`) and it deletes REDACTION_REPORT.md
#     and INTEGRITY.md from its scratch copy. It also EMBEDS the gate's hard-fail
#     pattern list (lines 138 and 156), i.e. shipping it would ship a
#     machine-readable list of the very identifiers the package withholds.
#   * code/verify/scrub-uscrub1.py — USCRUB1's own scrub engine; same defect
#     (line 63 embeds `publish-present-compete`).
#   * eval/second-labeller/OWED_CORRECTIONS.md — the per-defect correction ledger,
#     compiled by an internal unit from an internal work order
#     (`strategy/VERIFICATION_REPORT_3.md`). The reader loses the itemised
#     correction chain; the FINDING survives reachable in paper/MANUSCRIPT.md
#     ("a correction is carried, not hidden") and eval/results/REPORT.md.
#   * the SANITISED tree's top-level documents (README.md, INTEGRITY.md,
#     SCRUB_REPORT.md, REDACTION_REPORT.md, RESIDUALS.md, EXCLUDED.md,
#     LICENCE_TODO.md, MANIFEST.json, redact.py, variants/) — never shipped by
#     this or any previous revision of this script. INTEGRITY.md is the
#     authoritative hash record but it hashes a 58-file tree of which 26 files
#     do not ship, and it names every withheld record; its hashes are therefore
#     not verifiable inside this package. The load-bearing digests survive in
#     harness/tccommon.py and harness/data/manifest.json.
#
# DELIBERATELY KEPT — DO NOT "CLEAN" THESE:
#   `907fa39` and `ad301ae` are the read-only target-revision anchors. They are
#   the proof that the instrument was cut from a named revision of the
#   read-only target repository. They are KEPT ON PURPOSE and this script
#   ASSERTS (further down) that both are still present. Removing them would
#   weaken a checked claim, not sanitise anything.
#
# THE ONE TRANSFORM THIS SCRIPT APPLIES: three literal PATH rules, and only
# three. They are not a substitution vocabulary — they replace a local absolute
# path with a placeholder and touch nothing else. They cannot change a measured
# number (a path is not model input). Everything else that the gate flags is
# left exactly as authored, so the gate reports the real state of the material.
# =============================================================================
set -euo pipefail

# =============================================================================
# THE DRIVER ARGUMENTS
#
#     bash UBUILD1.build.sh --package <slug>
#
# <slug> names a manifest at orchestration/packages/<slug>.toml. With no
# argument the built-in default package is built, which is what a bare
# invocation has always done. Every per-package value (source tree, ship list,
# never-ship list, licence template and its hash, anchors, vocabulary, package
# name, commit subject, destination default) comes from that manifest; none is
# retyped in this file. Schema: strategy/PACKAGE_BUILD.md.
# =============================================================================
DEFAULT_SLUG="gated-read-batching"
PKG_SLUG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --package)   PKG_SLUG="${2:-}"; shift 2 ;;
    --package=*) PKG_SLUG="${1#--package=}"; shift ;;
    -h|--help)
      echo "usage: bash $0 [--package <slug>]"
      echo "  <slug> names orchestration/packages/<slug>.toml (default: $DEFAULT_SLUG)"
      exit 0 ;;
    *) echo "FATAL: unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PKG_SLUG" ] || PKG_SLUG="$DEFAULT_SLUG"
case "$PKG_SLUG" in
  ""|*/*|.*) echo "FATAL: a package slug must be a bare name: '$PKG_SLUG'" >&2; exit 2 ;;
esac

# The repository THIS DRIVER lives in. Deliberately not read from $SRC: the
# manifest set is harness, and $SRC is overridable (the wiring guard points it at
# a throwaway tree). Resolved from the script's own location, never guessed.
_REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$_REPO_ROOT/orchestration/packages/$PKG_SLUG.toml"
[ -f "$MANIFEST" ] || {
  echo "FATAL: no manifest for package '$PKG_SLUG': $MANIFEST" >&2; exit 2; }

SRC="${SRC:-/home/zer0null/reserach extarctor}"
COMMIT_DATE="${COMMIT_DATE:-2026-10-15T00:00:00+00:00}"

# ---- load the manifest: FAIL-CLOSED -----------------------------------------
# The TOML is read here and emitted as shlex-quoted shell assignments, so a
# malformed manifest cannot inject shell. A missing key, an unknown schema, a
# slug that disagrees with the file name, a missing prose/vocabulary fragment or
# an absent TOML parser all stop the build with exit 2 -- it never proceeds on a
# half-read manifest.
_manifest_shell="$(python3 - "$MANIFEST" "$SRC" <<'MANIFEST_LOADER_PY'
import json
import os
import shlex
import sys

try:
    import tomllib
except ImportError:                      # Python < 3.11
    sys.stderr.write("FATAL: python3 has no tomllib; the manifest cannot be read\n")
    sys.exit(2)

path, src = sys.argv[1], sys.argv[2]


def die(msg):
    sys.stderr.write("FATAL: manifest %s: %s\n" % (path, msg))
    sys.exit(2)


try:
    with open(path, "rb") as handle:
        man = tomllib.load(handle)
except (OSError, ValueError) as exc:
    die("cannot read or parse: %s" % exc)

REQUIRED = (
    "schema", "slug", "name", "dest_default", "promoted_san_src", "frozen_san_src",
    "licence_src", "licence_files", "licence_sha256", "commit_subject", "anchors",
    "index_row", "vocabulary_code", "vocabulary_public",
    "neutralise_rules", "neutralise_forbidden", "ship_staged", "never_ship",
)
for key in REQUIRED:
    if key not in man:
        die("missing required key %r" % key)
if man["schema"] != 1:
    die("unsupported schema %r" % man["schema"])
stem = os.path.basename(path)
if stem.endswith(".toml"):
    stem = stem[:-5]
if man["slug"] != stem:
    die("slug %r does not match the file name %r" % (man["slug"], stem))

PKG_DIR = os.path.dirname(os.path.abspath(path))


def resolve(value):
    """A manifest path is $SRC-relative unless absolute. Both are literal."""
    return value if os.path.isabs(value) else os.path.join(src, value)


def fragment(rel):
    return os.path.join(PKG_DIR, rel)


def strings(key, least=0):
    val = man[key]
    if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
        die("%s must be an array of strings" % key)
    if len(val) < least:
        die("%s must name at least %d entry/entries" % (key, least))
    return val


out = []


def emit(name, value):
    out.append("%s=%s" % (name, shlex.quote(value)))


def emit_array(name, values):
    out.append("%s=( %s )" % (name, " ".join(shlex.quote(v) for v in values)))


for key in ("name", "dest_default", "licence_sha256", "promoted_san_src",
            "frozen_san_src", "licence_src", "commit_subject", "index_row",
            "vocabulary_code", "vocabulary_public"):
    if not isinstance(man[key], str) or not man[key]:
        die("%s must be a non-empty string" % key)
for key in ("vocabulary_code", "vocabulary_public"):
    if not os.path.isfile(fragment(man[key])):
        die("missing fragment file: %s" % fragment(man[key]))

rules = man["neutralise_rules"]
if (not isinstance(rules, list) or not rules
        or not all(isinstance(r, list) and len(r) == 2
                   and all(isinstance(x, str) for x in r) for r in rules)):
    die("neutralise_rules must be a non-empty array of [old, new] string pairs")

emit("M_SLUG", man["slug"])
emit("M_NAME", man["name"])
emit("M_DEST_DEFAULT", man["dest_default"])
emit("M_PROMOTED", resolve(man["promoted_san_src"]))
emit("M_FROZEN", resolve(man["frozen_san_src"]))
emit("M_LICENCE_SRC", resolve(man["licence_src"]))
emit_array("M_LICENCE_FILES", strings("licence_files", 1))
emit("M_LICENCE_SHA", man["licence_sha256"])
emit("M_COMMIT_SUBJECT", man["commit_subject"])
emit_array("M_ANCHORS", strings("anchors", 1))
emit("M_VOCAB_CODE", fragment(man["vocabulary_code"]))
emit("M_VOCAB_PUBLIC", fragment(man["vocabulary_public"]))
emit_array("M_SHIP", strings("ship_staged", 1))
emit_array("M_NEVER", strings("never_ship"))
emit("M_RULES_JSON", json.dumps(rules))
emit("M_FORBIDDEN_JSON", json.dumps(strings("neutralise_forbidden", 1)))
print("\n".join(out))
MANIFEST_LOADER_PY
)"
eval "$_manifest_shell"
unset _manifest_shell

DEST="${DEST:-$M_DEST_DEFAULT}"
# The emitted package directory is a manifest value: refuse anything that could
# escape $DEST/packages/.
case "$M_NAME" in
  ""|*/*|.|..) echo "FATAL: manifest name must be a bare directory name: '$M_NAME'" >&2; exit 2 ;;
esac

step() { printf '\n=== [%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

# ---- guard: never rm -rf anything that is not the intended repository --------
[ -n "$DEST" ] || { echo "FATAL: DEST is empty" >&2; exit 2; }
case "$DEST" in
  */research-publish-packages) : ;;
  *) echo "FATAL: refusing to rm -rf '$DEST' — DEST must end in /research-publish-packages" >&2; exit 2 ;;
esac
[ "$DEST" != "/" ] || { echo "FATAL: DEST is /" >&2; exit 2; }

# The PROMOTED tree — the release package itself; the build stages it verbatim.
# PROMOTED DEFAULT (UWIRE2) = the chosen release artifact (UWIRE1's measured
# winner). The FROZEN original sanitised tree stays reachable through a NAMED
# environment override so the pre-promotion input remains reproducible. Neither
# variable is read from anywhere but the environment, neither is guessed from
# disk, and neither makes the build interactive.
PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"
FROZEN_SAN_SRC="$SRC/repro/encoder-crossover-190-SANITISED"
# ---- the built-in default block and the manifest must AGREE ------------------
# `PROMOTED_SAN_SRC` and `FROZEN_SAN_SRC` above are the DEFAULT package's
# declaration in code, which is what `tests/test_build_wiring.py` derives from
# this file. The manifest is authoritative for every package, so for the default
# slug the two must be the same: editing either one alone stops the build. The
# same tripwire guards the ship/never-ship lists and the licence hash below.
if [ "$PKG_SLUG" = "$DEFAULT_SLUG" ]; then
  [ "$PROMOTED_SAN_SRC" = "$M_PROMOTED" ] || {
    echo "FATAL: manifest promoted_san_src ($M_PROMOTED) disagrees with the built-in default ($PROMOTED_SAN_SRC)" >&2
    exit 2; }
  [ "$FROZEN_SAN_SRC" = "$M_FROZEN" ] || {
    echo "FATAL: manifest frozen_san_src ($M_FROZEN) disagrees with the built-in default ($FROZEN_SAN_SRC)" >&2
    exit 2; }
fi
PROMOTED_SAN_SRC="$M_PROMOTED"
FROZEN_SAN_SRC="$M_FROZEN"
if   [ -n "${SAN_SRC_OVERRIDE:-}" ]; then SAN_SRC="$SAN_SRC_OVERRIDE"
elif [ "${SAN_SRC_FROZEN_OVERRIDE:-0}" = "1" ]; then SAN_SRC="$FROZEN_SAN_SRC"
else SAN_SRC="$PROMOTED_SAN_SRC"
fi
# LOUD WIRING LINE — exactly one line, always printed, machine-greppable: which
# tree this build read and whether it is the promoted default. A build that
# consumes the frozen tree while the chosen artifact exists must be impossible to
# mistake. The extra WARNING lines below add context; they never change the exit
# code and never prompt, so the build stays scriptable.
if [ "$SAN_SRC" = "$PROMOTED_SAN_SRC" ]; then _san_promoted=yes; else _san_promoted=no; fi
echo "SAN_SRC WIRING: tree=$SAN_SRC promoted_default=$_san_promoted"
if [ "$_san_promoted" = no ]; then
  echo "SAN_SRC WIRING: WARNING - NOT the promoted release artifact; the promoted default is"
  echo "                $PROMOTED_SAN_SRC"
  if [ "$SAN_SRC" = "$FROZEN_SAN_SRC" ]; then
    echo "SAN_SRC WIRING: WARNING - this is the FROZEN original sanitised tree (the pre-promotion"
    echo "                input, not the promoted release artifact; see strategy/BUILD_PIN_CHANGE.md"
    echo "                for current measurements)."
  fi
fi
PKG="$DEST/packages/$M_NAME"

step "UBUILD1 build  package=$PKG_SLUG  SRC=$SRC  DEST=$DEST  (fail-closed ship-list)"
for d in "$SAN_SRC"; do
  [ -d "$d" ] || { echo "FATAL: missing source directory: $d" >&2; exit 1; }
done
echo "source directories present."
# The as-audited tree must never be read. Fail loudly if the card's SANITISED path is wrong.
echo "using SANITISED tree only: $SAN_SRC"

# ---- clean slate ------------------------------------------------------------
step "removing any previous target"
# Remove only THIS package's directory: sibling packages already built into the
# same repository are PRESERVED, so the archive accumulates packages instead of
# replacing them. The root README index is regenerated from the manifests of the
# packages that are present. The DEST suffix guard above still bounds removal.
rm -rf "$PKG"
mkdir -p "$PKG"

# ---- GAP 1: the ship-list must describe the tree it pins, for EVERY package --
# The two-way tripwire above is the DEFAULT package's cross-check only: for any
# other slug it is skipped, so a non-default manifest could declare a ship list
# that disagrees with the tree it pins and the build would not notice. This check
# closes that for ANY package and is DERIVED from the manifest itself
# (promoted_san_src + ship_staged), so it cannot go stale like a third literal.
# Inclusion rule: every regular file under promoted_san_src, any path with a
# `.git` component excluded. It runs after the per-package clean step but
# BEFORE anything is staged, so a mismatch ships nothing.
step "verifying ship_staged against the pinned tree (fail-closed, every package)"
python3 - "$MANIFEST" "$SRC" <<'SHIPLIST_TREE_CHECK_PY'
import os
import sys

try:
    import tomllib
except ImportError:
    sys.stderr.write("FATAL: python3 has no tomllib; the ship list cannot be verified\n")
    sys.exit(2)

manifest, src = sys.argv[1], sys.argv[2]
with open(manifest, "rb") as handle:
    man = tomllib.load(handle)
tree = man["promoted_san_src"]
if not os.path.isabs(tree):
    tree = os.path.join(src, tree)
if not os.path.isdir(tree):
    sys.stderr.write("FATAL: ship-list check: pinned tree is missing: %s\n" % tree)
    sys.exit(2)

present = []
for dirpath, dirnames, filenames in os.walk(tree):
    dirnames[:] = [d for d in dirnames if d != ".git"]
    for name in filenames:
        full = os.path.join(dirpath, name)
        if os.path.isfile(full):
            present.append(os.path.relpath(full, tree).replace(os.sep, "/"))
present.sort()
listed = sorted(man["ship_staged"])
if listed != present:
    sys.stderr.write(
        "FATAL: SHIP-LIST/TREE MISMATCH for package %r\n"
        "       ship_staged does not describe the pinned tree %s\n"
        "       listed but not on disk: %s\n"
        "       on disk but not listed: %s\n"
        % (man["slug"], tree, sorted(set(listed) - set(present)),
           sorted(set(present) - set(listed))))
    sys.exit(2)
print("  ship-list/tree check: %d declared file(s) == %d present in %s"
      % (len(listed), len(present), tree))
SHIPLIST_TREE_CHECK_PY


# =============================================================================
# THE SHIP-LIST (UCURATE1) — the single source of truth for what ships.
# Fail-closed: SHIP_STAGED is the COMPLETE list of staged files, relative to
# $PKG. A staged file that is not listed is DELETED; a listed file that is
# missing is FATAL. Nothing ships by omission.
# Hard-fail-hit counts below are UCURATE1's measurement with the gate's own
# verbatim pattern list, after the three path rules further down.
# =============================================================================
SHIP_STAGED=(
  # -- package root : the package's own entry documents and manifest ------------
  COMMERCIAL.md
  CONTRIBUTING.md
  LICENSE
  MANIFEST.json
  README.md
  # -- fixture/ : the sealed instrument. MODEL INPUT — never rewritten ----------
  fixture/DECISION_CASE_SCHEMA.ts
  fixture/fixture-190.json
  fixture/reflex-decisions.ts
  # -- preregistration/ : frozen before the runs -------------------------------
  preregistration/EXP12-typed-channel-comparison-prereg.md
  # -- results/ : the evaluation evidence --------------------------------------
  results/REPORT.md
  results/baselines.json
  results/eval-deberta-v3-base.json
  results/eval-majority-class.json
  results/eval-modernbert-base.json
  results/eval-setfit-mpnet.json
  results/eval-shuffled-label.json
  # -- second-labeller/ : the independent re-labelling --------------------------
  second-labeller/EVIDENCE.md
  second-labeller/OWED_CORRECTIONS.md
  second-labeller/PREREGISTRATION.md
  second-labeller/RUN.json
  second-labeller/blinded_cases.json
  second-labeller/cases.json
  second-labeller/compare.py
  second-labeller/disagreements.jsonl
  second-labeller/labelsB.json
  second-labeller/metrics.json
  second-labeller/parse_fixture.py
  second-labeller/parse_summary.json
  # -- verify/ : THE reproduction instrument, and nothing else ------------------
  verify/recompute-claims.py
)
# ---- the manifest is authoritative; the block above is the DEFAULT -----------
# Kept literal on purpose: `tests/test_build_wiring.py` derives the ship list
# from THIS file and checks it against the promoted tree on disk. The manifest
# must reproduce it exactly for the default package, or the build stops here.
DEFAULT_SHIP_STAGED=( "${SHIP_STAGED[@]}" )
SHIP_STAGED=( "${M_SHIP[@]}" )
if [ "$PKG_SLUG" = "$DEFAULT_SLUG" ]; then
  [ "$(printf '%s\n' "${DEFAULT_SHIP_STAGED[@]}")" = "$(printf '%s\n' "${SHIP_STAGED[@]}")" ] || {
    echo "FATAL: manifest ship_staged disagrees with the built-in default block" >&2; exit 2; }
fi

# ---- stage the candidate material -------------------------------------------
# The promoted tree IS the release package: its on-disk layout is already the
# shipped layout, so it is staged verbatim. `cp -r SRC/. DEST/` copies the
# CONTENTS; a plain `cp -r SRC DEST` would nest the directory one level deeper.
step "staging candidate material from the promoted package"
cp -r "$SAN_SRC/." "$PKG/"

# ---- PRUNE to the ship-list (fail-closed) ------------------------------------
step "pruning the staged tree against the ship-list"
in_ship() { printf '%s\n' "${SHIP_STAGED[@]}" | grep -qxF -- "$1"; }
staged=0; kept=0; dropped=0
while IFS= read -r -d '' f; do
  staged=$((staged + 1))
  rel="${f#"$PKG"/}"
  if in_ship "$rel"; then
    kept=$((kept + 1))
  else
    rm -f "$f"
    echo "  DROP    $rel"
    dropped=$((dropped + 1))
  fi
done < <(find "$PKG" -type f -print0)
find "$PKG" -mindepth 1 -type d -empty -delete
echo "  staged $staged file(s): $kept kept, $dropped dropped"
# FAIL-CLOSED: a ship-list entry with no file behind it stops the build.
missing=0
for rel in "${SHIP_STAGED[@]}"; do
  if [ ! -f "$PKG/$rel" ]; then
    echo "FATAL: ship-list names a file the package does not have: $rel" >&2
    missing=1
  fi
done
[ "$missing" -eq 0 ] || exit 1
echo "  ship-list enforced: ${#SHIP_STAGED[@]} staged file(s) present"

# ---- NEVER_SHIP: names that must never reach the package --------------------
# The ship-list already makes these unreachable, but "unreachable today" is not
# a guarantee: if a future revision points the staging at another tree, or adds a
# `cp -r` for a directory, a drop-by-omission silently becomes a ship. This list
# is checked by ABSENCE and is the one place the drop decisions are recorded by
# NAME, so an exclusion can never be lost to a refactor.
#
# NOTE on `papers/gated-read-batching/DISCLOSURE_CHANGES.md` (in from unit
# UFIX11's sweep): that paper is NOT part of this package — the package ships
# `papers/encoder-crossover-190` only, and nothing in this script references the
# second paper. If a future revision adds it, DISCLOSURE_CHANGES.md MUST NOT come
# with it: UCURATE1 measured 19 hard-fail lines in that one file under the gate's
# verbatim pattern list (UFIX11's own wider sweep list reports 52) — unit names,
# a verification-report filename, md5 digests and the target path. Its four
# siblings (MANUSCRIPT.md, CLAIMS.md, REFS.md, GAPS.md) are hard-clean, but the
# paper's `G:`/`P:`/`R:`/`S:` locators resolve into the READ-ONLY TARGET repo
# (`docs/research/GATED_READ_2026.md`, `GATED_READ_PROVENANCE.md`,
# `gated-read-rows.jsonl`, `gated-read-summary.json`), which this package does not
# redistribute — so those four are not shippable as a self-contained package
# either. The legend and the withholding are declared in CLAIMS.md:8,11-15; the
# decision is recorded in strategy/PUBLISH_PACKAGE_MANIFEST.md.
NEVER_SHIP=(
  # the SANITISED tree's own process/audit documents (never staged, never shipped)
  EXCLUDED.md
  INTEGRITY.md
  LICENCE_TODO.md
  REDACTION_REPORT.md
  RESIDUALS.md
  SCRUB_REPORT.md
  redact.py
  # generated verify output and the process tooling around it
  code/verify/VERIFICATION.txt
  code/verify/RECOMPUTE-CLAIMS.txt
  code/verify/RESIDUAL-SCAN.txt
  code/verify/redaction-log.json
  code/verify/integrity-table.md
  code/verify/run-verification.sh
  code/verify/scrub-uscrub1.py
  # (the old eval/second-labeller/OWED_CORRECTIONS.md exclusion is retired: that file is a
  #  real package member now — second-labeller/OWED_CORRECTIONS.md — and is shipped.)
  # the second paper's audit trail — see the note above
  paper/DISCLOSURE_CHANGES.md
)
# ---- the manifest is authoritative; the block above is the DEFAULT -----------
DEFAULT_NEVER_SHIP=( "${NEVER_SHIP[@]}" )
NEVER_SHIP=( "${M_NEVER[@]}" )
if [ "$PKG_SLUG" = "$DEFAULT_SLUG" ]; then
  [ "$(printf '%s\n' "${DEFAULT_NEVER_SHIP[@]}")" = "$(printf '%s\n' "${NEVER_SHIP[@]}")" ] || {
    echo "FATAL: manifest never_ship disagrees with the built-in default block" >&2; exit 2; }
fi
ns=0
for rel in "${NEVER_SHIP[@]}"; do
  if [ -e "$PKG/$rel" ] || [ -e "$DEST/$rel" ]; then
    echo "FATAL: NEVER_SHIP entry is present in the package: $rel" >&2
    ns=1
  fi
done
[ "$ns" -eq 0 ] || exit 1
echo "  never-ship list enforced: ${#NEVER_SHIP[@]} names checked absent"

# ---- authored files ---------------------------------------------------------
step "authoring the archive README index and the licence/checker files"
# GAP 2: the archive-level README is an INDEX, not one package's README. Each
# manifest supplies its own row (`index_row`), and the index lists every package
# already present in this destination, sorted by slug. Building a second package
# ADDS a row and leaves the first row (and the first package's tree) standing.
# The package's own README.md ships inside its directory, staged from the tree;
# the two are different documents. index_row comes from the manifest, so there is
# no third hand-maintained list to go stale.
python3 - "$DEST" "$_REPO_ROOT/orchestration/packages" <<'README_INDEX_PY'
import os
import sys

try:
    import tomllib
except ImportError:
    sys.stderr.write("FATAL: python3 has no tomllib; the README index cannot be built\n")
    sys.exit(2)

dest, manifest_dir = sys.argv[1], sys.argv[2]
rows = []
for name in sorted(os.listdir(manifest_dir)):
    if not name.endswith(".toml"):
        continue
    with open(os.path.join(manifest_dir, name), "rb") as handle:
        man = tomllib.load(handle)
    if os.path.isdir(os.path.join(dest, "packages", man["name"])):
        rows.append((man["slug"], man["index_row"]))
rows.sort()
out = [
    "# Research Publish Packages",
    "",
    "Data and verification packages released from the instrument. Each package",
    "lives under `packages/` and carries its own README, licence and gate.",
    "",
    "## Packages",
    "",
    "| package | contents |",
    "|---|---|",
]
out.extend(row for _slug, row in rows)
out.append("")
with open(os.path.join(dest, "README.md"), "w", encoding="utf-8") as handle:
    handle.write("\n".join(out))
print("  README.md index: %d package row(s)" % len(rows))
for slug, _row in rows:
    print("    - %s" % slug)
README_INDEX_PY

# The source-available paragraph is EXTRACTED verbatim from its single
# authoritative copy (strategy/licence-templates/README-PARAGRAPHS.md, "Case B")
# -- the build script never retypes it, so the wording cannot drift.
caseB="$(python3 - "$SRC/strategy/licence-templates/README-PARAGRAPHS.md" <<'CASEB_EOF'
import sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("## Case B"))
end = next(j for j in range(start, len(lines)) if lines[j].startswith("Standalone"))
print("\n".join(l for l in lines[start:end] if l.startswith(">")))
CASEB_EOF
)"
[ -n "$caseB" ] || { echo "FATAL: could not extract the Case B source-available paragraph" >&2; exit 1; }

printf '\n## Licensing\n\n%s\n\n' "$caseB" >> "$DEST/README.md"



# ---- licence set: SOURCE-AVAILABLE, not open source --------------------------
# strategy/CODE_LICENSING_STRATEGY.md ERRATA (UMEMO1) + PUBLICATION_STRATEGY.md
# §13: every released artifact is PolyForm Noncommercial 1.0.0 (commercial use
# requires a paid licence); paper text is CC BY 4.0; the core system carries no
# public licence at all. The licence files are COPIED from the template
# directory -- never retyped here -- so exactly ONE authoritative copy of the
# licence text exists.
step "authoring the licence set (PolyForm Noncommercial 1.0.0 + CC BY 4.0)"
LIC_SRC="$M_LICENCE_SRC"
[ -d "$LIC_SRC" ] || { echo "FATAL: missing licence templates: $LIC_SRC" >&2; exit 1; }
for f in "${M_LICENCE_FILES[@]}"; do
  [ -f "$LIC_SRC/$f" ] || { echo "FATAL: missing licence template: $LIC_SRC/$f" >&2; exit 1; }
  cp "$LIC_SRC/$f" "$DEST/$f"
done
# Drift guard: the licence text is pinned by hash. The default package's
# expected hash is the literal below (asserted against its manifest); another
# package names its own in the manifest. Either way the build stops rather than
# shipping an unrecorded licence.
LIC_SHA_EXPECTED="3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900"
if [ "$PKG_SLUG" = "$DEFAULT_SLUG" ]; then
  [ "$M_LICENCE_SHA" = "$LIC_SHA_EXPECTED" ] || {
    echo "FATAL: manifest licence_sha256 disagrees with the built-in default" >&2; exit 2; }
fi
LIC_SHA_EXPECTED="$M_LICENCE_SHA"
LIC_SHA="$(sha256sum "$DEST/LICENSE" | cut -d' ' -f1)"
[ "$LIC_SHA" = "$LIC_SHA_EXPECTED" ] || {
  echo "FATAL: LICENSE template drift: sha256 is $LIC_SHA, expected $LIC_SHA_EXPECTED" >&2; exit 1; }
# Scope clause APPENDED: the licence terms above are unmodified (bytes 1-5851 are
# the template byte-for-byte); this only states what the root licence does not
# cover. It exists so a reader who opens only LICENSE still learns the paper is
# CC BY 4.0.
cat >> "$DEST/LICENSE" <<'LICENSE_SCOPE_EOF'

## Scope -- which files the licence terms above do not cover

The terms above apply to this repository as a whole, **except** where a package
directory carries its own `LICENSE` instrument: that file governs the files it
covers and is not superseded by the terms above. Each package under `packages/*/`
is a **data + verification** package — its data, evidence and verification tools
are governed by the terms above (PolyForm Noncommercial License 1.0.0) unless its
own `LICENSE` says otherwise. Where a package's own instrument grants
**CC BY 4.0**, its scholarly text is licensed under CC BY 4.0; the full legal code
is at <https://creativecommons.org/licenses/by/4.0/legalcode>.

`gate.sh`, `vocabulary/` and the repository scripts are governed by the terms
above (PolyForm Noncommercial License 1.0.0).
LICENSE_SCOPE_EOF


cat > "$DEST/.gitignore" <<'GITIGNORE_EOF'
# ---------------------------------------------------------------------------
# Keep this file MINIMAL and conservative: every pattern here can silently drop
# a real package file from the release. Add per package when you must.
# ---------------------------------------------------------------------------

# OS / editor noise
.DS_Store
Thumbs.db
*.swp
*~

# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.ipynb_checkpoints/
*.egg-info/

# Node
node_modules/
npm-debug.log*

# Local scratch output — never package content
/.scratch/
/tmp/
GITIGNORE_EOF

# ---- the positive vocabulary checker (replaces the 24-pattern denylist) ------
# strategy/CODE_AGNOSTIC_RELEASE_POLICY.md §D.2. A closed denylist can only
# report what someone already remembered; the totality check inverts it. This
# emits a POSITIVE checker: the artifact may contain only the frozen declared
# vocabulary plus generic English. It therefore ships no withheld identifier and
# needs no self-exclusion -- everything it contains is allowed vocabulary, and
# it scans itself. Fail-closed: any out-of-vocabulary token exits non-zero.
step "authoring the positive vocabulary checker (gate.sh + vocabulary/)"
mkdir -p "$DEST/vocabulary"

# (c) generic English -- a FROZEN word list, taken from the system dictionaries
#     and frozen into the package. Fail closed if no dictionary is present.
WORDS_SRC=""
for cand in /usr/share/dict/american-english /usr/share/dict/british-english /usr/share/dict/words; do
  [ -r "$cand" ] && WORDS_SRC="$WORDS_SRC $cand"
done
[ -n "$WORDS_SRC" ] || { echo "FATAL: no system word list; vocabulary/english.txt cannot be frozen" >&2; exit 1; }
# shellcheck disable=SC2086
cat $WORDS_SRC \
  | LC_ALL=C tr 'A-Z' 'a-z' \
  | LC_ALL=C grep -E '^[a-z]{2,24}$' \
  | LC_ALL=C grep -v -E 'duval' \
  | LC_ALL=C sort -u > "$DEST/vocabulary/english.txt"
echo "  vocabulary/english.txt: $(wc -l < "$DEST/vocabulary/english.txt") words (frozen from:$WORDS_SRC)"

# (c) generic code / tooling vocabulary. PUBLIC, NEUTRAL terms only.
# (c) code / tooling vocabulary, PER PACKAGE: a package may name its own domain
#     words. PUBLIC, NEUTRAL terms only. Written VERBATIM from the fragment.
[ -r "$M_VOCAB_CODE" ] || { echo "FATAL: missing code vocabulary fragment: $M_VOCAB_CODE" >&2; exit 1; }
cat "$M_VOCAB_CODE" > "$DEST/vocabulary/code.txt"

# (b) the frozen public identifier list: identifiers that ship WHOLE. Anything
#     identifier-shaped (an interior lower-to-upper boundary) must be declared
#     here -- that is what makes an injected `grantPolicy`/`StateClass` fail.
# (b) the frozen public identifier list, PER PACKAGE: identifiers that ship
#     WHOLE. Anything identifier-shaped must be declared here -- that is what
#     makes an injected `grantPolicy`/`StateClass` fail.
[ -r "$M_VOCAB_PUBLIC" ] || { echo "FATAL: missing public vocabulary fragment: $M_VOCAB_PUBLIC" >&2; exit 1; }
cat "$M_VOCAB_PUBLIC" > "$DEST/vocabulary/public.txt"

# ---- (d) DECLARED data-file vocabulary for the scoped gate (UGATE2) ---------
# Derived from the STAGED TREE's own JSON object KEYS only -- never from string
# VALUES. `keys` mode, deliberately: declaring single-token VALUES would
# declare 8 of the 15 mechanism names as vocabulary, i.e. ship the leak as the
# vocabulary (UGATE1 measured `--mode full` doing exactly that; it is rejected).
# A key is the released format; a value is the data. Free-text mechanism names
# inside values stay under the strict prose rule.
# Fail-closed: a derivation error, a parse failure, or an empty key set stops
# the build BEFORE the gate can be run against an empty vocabulary input.
step "deriving declared data-file vocabulary (JSON keys only; fail-closed)"
python3 - "$DEST" "$DEST/vocabulary/data.txt" <<'DATAVOCAB_EOF'
import json
import os
import sys

EMIT, OUT = sys.argv[1], sys.argv[2]
DATA_EXT = (".json", ".jsonl")
SKIP_DIRS = {".git"}
keys = set()
parsed = 0


def walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                keys.add(k)
            walk(v)
    elif isinstance(obj, list):
        for v in obj:
            walk(v)


for dirpath, dirnames, filenames in os.walk(EMIT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in sorted(filenames):
        rel = os.path.relpath(os.path.join(dirpath, name), EMIT)
        if not rel.endswith(DATA_EXT):
            continue
        try:
            txt = open(os.path.join(dirpath, name), encoding="utf-8").read()
        except (OSError, ValueError):
            continue
        try:
            if rel.endswith(".jsonl"):
                for line in txt.splitlines():
                    line = line.strip()
                    if line:
                        walk(json.loads(line))
                        parsed += 1
            else:
                walk(json.loads(txt))
                parsed += 1
        except (ValueError, TypeError):
            continue

if not keys:
    sys.stderr.write("FATAL: derived an EMPTY data vocabulary from %s\n" % EMIT)
    sys.exit(1)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("# DECLARED data-file vocabulary for the scoped positive-vocabulary gate.\n")
    fh.write("# Derived from the released format: every JSON object KEY of every released\n")
    fh.write("# data file. Single-token VALUES are deliberately NOT declared (keys mode):\n")
    fh.write("# declaring values would declare mechanism names as vocabulary.\n")
    for tok in sorted(keys):
        fh.write(tok + "\n")
print("  vocabulary/data.txt: %d declared data-file key(s) from %d parsed document(s)"
      % (len(keys), parsed))
DATAVOCAB_EOF

cat > "$DEST/gate.sh" <<'GATE_EOF'
#!/usr/bin/env bash
# =============================================================================
# gate.sh -- the POSITIVE VOCABULARY checker (acceptance test) for
# research-publish-packages.
#
# This file carries NO denylist. It carries an allowlist, and it is a POSITIVE
# check: a token passes only if it is a declared member of this tree's own
# vocabulary. It names no withheld document, symbol or path.
#
# SCOPE -- the one correction to the strict rule. See
# strategy/GATE_VOCABULARY_ANALYSIS.md in the source tree for the analysis.
#   * prose and source keep the strict rule: every token must be declared in
#     vocabulary/{english,code,public}.txt. A mechanism token in prose or in
#     source still fails.
#   * data files (.json/.jsonl) are also checked against the released format's
#     declared vocabulary, vocabulary/data.txt, because a record key or a
#     single-token value that is a label IS the format, not a word.
#     data.txt holds JSON object KEYS only, so free text is never declared and
#     a mechanism name inside a data value still fails.
#
# THE LIST IS COMPLETE: every counted token is printed with file and
# line. A token late in the walk cannot be counted and left unnamed.
# THE CHECKER DOES NOT SCAN ITS OWN vocabulary/ INPUTS.
#
# FAIL-CLOSED: if a required vocabulary file is absent, unreadable or empty,
# the checker exits 2 and the build fails. It never passes on missing inputs.
#
#   exit 0   every token is a declared member of this tree's own vocabulary
#   exit 1   out-of-vocabulary tokens (every one printed with file:line)
#   exit 2   FAIL-CLOSED -- a required input cannot be read or is empty
#
# If this gate fails, do NOT hand-edit the source material to make it pass.
# Report the tokens and let the author decide.
# =============================================================================
set -uo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"

exec python3 -u - "$ROOT" "${GATE_JSON:-0}" <<'GATE_PY'
import json
import os
import re
import string
import sys

ROOT = sys.argv[1]
JSON_MODE = len(sys.argv) > 2 and sys.argv[2] == "1"
VOCAB_DIR = os.path.join(ROOT, "vocabulary")
VOCAB_REL = os.path.relpath(VOCAB_DIR, ROOT)
DATA_FILES = (".json", ".jsonl")


def load(name):
    out = set()
    path = os.path.join(VOCAB_DIR, name)
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for word in line.split():
                    out.add(word)
    except (OSError, ValueError):
        sys.stderr.write("FATAL: cannot read vocabulary file: %s\n" % path)
        sys.exit(2)
    if not out:
        sys.stderr.write("FATAL: vocabulary file has no declared terms: %s\n" % path)
        sys.exit(2)
    return out


ENGLISH = load("english.txt")
CODE = load("code.txt")
DECLARED = load("public.txt")
DATA_WORDS = load("data.txt")

DECLARED_LOWER = set(d.lower() for d in DECLARED)
WORDS = ENGLISH | CODE
DATA_LOWER = set(d.lower() for d in DATA_WORDS)
WORDS_DATA = WORDS | DATA_WORDS

ALNUM = string.ascii_letters + string.digits
DIGITS = string.digits
TOKEN_RE = re.compile("[" + ALNUM + "_.$/@-]+")
EDGE_CHARS = "-_.$/@"
CAMEL_RE = re.compile("[a-z][A-Z]")
SPLIT_RE = re.compile("[^" + ALNUM + "]+")
TAG_RE = re.compile("^(?:K|F|S|C|R|D|N|P)[" + DIGITS + "][" + DIGITS + "]$"
                    "|^TAG_[" + DIGITS + "][" + DIGITS + "]$")
HEX_RE = re.compile("^[" + DIGITS + "abcdef]{8,}$")
DIGIT_RE = re.compile("[" + DIGITS + "]+")
SKIP_DIRS = {".git"}

# Declared generated-id grammars -- patterns, not discovered tokens. Every one
# of them REQUIRES digits, so no mechanism word can match them.
ID_GRAMMARS = [
    re.compile(r"^fam(?:a|b|r)[" + DIGITS + "]{3,6}$"),
    re.compile(r"^ex1[12](?:a|b)[" + DIGITS + "]{3,6}$"),
    re.compile(r"^[^\W\d_][" + DIGITS + "]{2,4}-[" + DIGITS + "]{3}$"),
    re.compile(r"^(?:N|K|F|S)(?:[A-Z])?[" + DIGITS + "]{2,4}$"),
]


def classify(tok, is_data):
    tok = tok.strip(EDGE_CHARS)
    if not tok:
        return ""
    low = tok.lower()
    if TAG_RE.match(tok) or tok in DECLARED or low in DECLARED_LOWER or HEX_RE.match(tok):
        return ""
    for g in ID_GRAMMARS:
        if g.match(tok):
            return ""
    if is_data and (tok in DATA_WORDS or low in DATA_LOWER):
        return ""
    words = WORDS_DATA if is_data else WORDS
    if CAMEL_RE.search(tok):
        return "identifier-shaped, not a declared public identifier"
    for chunk in SPLIT_RE.split(low):
        for word in DIGIT_RE.split(chunk):
            if not word or len(word) == 1:
                continue
            if word not in words:
                return "word not in the declared vocabulary"
    return ""


print("=" * 70)
print("SCOPED POSITIVE VOCABULARY CHECK -- " + ROOT)
print("rule: every token must be a declared member of this tree's own vocabulary")
print("      prose/source: english+code+public (strict, unchanged)")
print("      data (.json/.jsonl): + vocabulary/data.txt (declared JSON keys)")
print("      vocabulary/ is not scanned; the list is complete")
print("=" * 70)

flagged = 0
printed = 0
by_class = {}
by_file = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in sorted(filenames):
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, ROOT)
        if rel.split(os.sep)[0] == VOCAB_REL:
            continue        # never scan the checker's own vocabulary inputs
        is_data = rel.endswith(DATA_FILES)
        kind = "data" if is_data else "prose-source"
        try:
            with open(path, encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    for match in TOKEN_RE.finditer(line):
                        tok = match.group(0)
                        why = classify(tok, is_data)
                        if why:
                            flagged = flagged + 1
                            by_class[kind] = by_class.get(kind, 0) + 1
                            by_file[rel] = by_file.get(rel, 0) + 1
                            printed = printed + 1
                            print("%s:%d: %s  [%s]" % (rel, number, tok, why))
        except (OSError, ValueError):
            continue

print("")
print("flagged tokens: %d" % flagged)
print("out-of-vocabulary token lines printed: %d" % printed)
if JSON_MODE:
    print(json.dumps({"flagged": flagged, "printed": printed,
                      "by_class": by_class, "by_file": by_file}))
if flagged:
    print("GATE RESULT: FAIL -- %d out-of-vocabulary token(s)." % flagged)
    print("Do NOT hand-edit shipped evidence to make this pass; report and let the author decide.")
    sys.exit(1)
print("GATE RESULT: PASS -- every token is a declared member of this tree's own vocabulary.")
GATE_PY
GATE_EOF
chmod +x "$DEST/gate.sh"
echo "  README.md, LICENSE, COMMERCIAL.md, CONTRIBUTING.md, .gitignore, gate.sh, vocabulary/ written."

# ---------------------------------------------------------------------------
# PATH NEUTRALISATION (UCURATE1) — the ONLY transform this script applies.
# Three literal rules, taken verbatim from UTOK2's measurement. They replace a
# local absolute path with a placeholder and touch nothing else: a path is not
# model input, so no measured number can move. The step is fail-closed — if
# `/home/zer0null` or `duval` survives anywhere, the build stops rather than
# shipping a local path.
# ---------------------------------------------------------------------------
step "neutralising local absolute paths (3 literal rules; fail-closed)"
# `gate.sh` is NOT skipped: the positive-vocabulary checker carries no path
# patterns, so the two path rules cannot disarm it and it is neutralised and
# verified like every other shipped file.
NEUTRALISE_RULES="$M_RULES_JSON" NEUTRALISE_FORBIDDEN="$M_FORBIDDEN_JSON" \
  python3 - "$DEST" <<'NEUTRALISE_EOF'
import json, os, sys
root = sys.argv[1]
SELF_EXCLUDED = set()                # the gate no longer excludes itself
RULES = [tuple(x) for x in json.loads(os.environ["NEUTRALISE_RULES"])]
FORBIDDEN = json.loads(os.environ["NEUTRALISE_FORBIDDEN"])
def walk():
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if os.path.relpath(p, root) in SELF_EXCLUDED:
                continue
            yield p
changed = total = 0
for p in walk():
    try:
        text = open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    new, n = text, 0
    for old, rep in RULES:
        c = new.count(old)
        if c:
            new = new.replace(old, rep); n += c
    if n:
        open(p, "w", encoding="utf-8").write(new)
        print("  %3d occurrence(s)  %s" % (n, os.path.relpath(p, root)))
        changed += 1; total += n
print("  %d occurrence(s) in %d file(s)" % (total, changed))
bad = []
for p in walk():
    try:
        text = open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    if any(f in text or f.lower() in text.lower() for f in FORBIDDEN):
        bad.append(os.path.relpath(p, root))
if bad:
    sys.stderr.write("FATAL: local path survived neutralisation:\n  "
                     + "\n  ".join(bad) + "\n")
    sys.exit(1)
NEUTRALISE_EOF

# ---------------------------------------------------------------------------
# DELIBERATELY KEPT — DO NOT "CLEAN" THESE (UCURATE1).
# `907fa39` is the read-only target-revision anchor this package carries: the proof
# that the instrument was cut from a named revision of the read-only target repo.
# (The second historical anchor, `ad301ae`, belonged to the paper text, which is a
# separate artifact and is not part of this data+verification package.) It is kept
# on purpose and asserted here so that a later pass cannot silently drop it in the
# name of sanitisation.
# ---------------------------------------------------------------------------
# Two revision anchors were named historically: 907fa39 and ad301ae. 907fa39 is
# carried by THIS package (fixture/, preregistration/, second-labeller/) and is
# asserted below. ad301ae lived in the PAPER TEXT (papers/encoder-crossover-190),
# which is a separate artifact and is NOT part of this data+verification package:
# its absence here is expected, not a regression.
step "asserting the deliberately-kept revision anchor is present"
for anchor in "${M_ANCHORS[@]}"; do
  n="$(grep -rl -F -- "$anchor" "$PKG" 2>/dev/null | wc -l || true)"
  if [ "$n" -eq 0 ]; then
    echo "FATAL: revision anchor '$anchor' is MISSING from the package." >&2
    echo "      '$anchor' is a declared revision proof for this package and is" >&2
    echo "      kept on purpose -- see the manifest. Do not remove it." >&2
    exit 1
  fi
  echo "  anchor $anchor present in $n file(s) — kept deliberately"
done

# ---- git --------------------------------------------------------------------
step "git init + one commit (fresh history, no remote)"
if   [ -n "${GIT_NAME:-}" ];  then :; else GIT_NAME="$(git config --global user.name  2>/dev/null || true)"; fi
if   [ -n "${GIT_EMAIL:-}" ]; then :; else GIT_EMAIL="$(git config --global user.email 2>/dev/null || true)"; fi
[ -n "$GIT_NAME" ]  || GIT_NAME="Research Publish Packages"
[ -n "$GIT_EMAIL" ] || GIT_EMAIL="research-publish-packages@localhost"

git -C "$DEST" init -q -b main 2>/dev/null || { git -C "$DEST" init -q; git -C "$DEST" symbolic-ref HEAD refs/heads/main; }
git -C "$DEST" add -A
GIT_AUTHOR_DATE="$COMMIT_DATE" GIT_COMMITTER_DATE="$COMMIT_DATE" \
  git -C "$DEST" -c user.name="$GIT_NAME" -c user.email="$GIT_EMAIL" \
  commit -q -m "$M_COMMIT_SUBJECT" \
  -m "Fresh history, no remote. Paper text CC BY 4.0; code PolyForm Noncommercial 1.0.0, required notice: Copyright 2026 Aswin-Ram-K."
# no remote is created and nothing is pushed, ever.
echo "  commits: $(git -C "$DEST" rev-list --count HEAD)   sha: $(git -C "$DEST" rev-parse --short HEAD)   remote: '$(git -C "$DEST" remote -v)'"
echo "  status: '$(git -C "$DEST" status --porcelain)'"

# ---- inventory --------------------------------------------------------------
step "inventory"
echo "  repo total     : $(find "$DEST" -path "$DEST/.git" -prune -o -type f -print | wc -l) files, $(du -sh "$DEST" | cut -f1)"
while IFS= read -r _d; do
  [ -n "$_d" ] || continue
  echo "  $_d/: $(find "$PKG/$_d" -type f | wc -l) files"
done < <(cd "$PKG" && find . -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort)
echo "  nested .git    : $(find "$DEST" -mindepth 2 -name .git | wc -l)"
echo "  working dirs   : $(find "$DEST" -type d \( -name journal -o -name jobs -o -name dockets -o -name state -o -name orchestration -o -name strategy \) | wc -l)"

# ---- gate -------------------------------------------------------------------
step "running the exclusion gate (any HARD-FAIL makes this script exit non-zero)"
set +e
bash "$DEST/gate.sh"
GATE_RC=$?
set -e

step "done"
if [ "$GATE_RC" -ne 0 ]; then
  echo "BUILD COMPLETE — the exclusion gate FAILED (exit $GATE_RC)."
  echo "Target tree: $DEST  (1 commit, clean working tree, no remote)"
  echo "Nothing was hand-edited to make the gate pass; the hits above are the real state"
  echo "of the material the unit card instructs this build to ship."
  exit "$GATE_RC"
fi
echo "BUILD COMPLETE — the exclusion gate PASSED."
echo "Target tree: $DEST  (1 commit, clean working tree, no remote)"
exit 0
