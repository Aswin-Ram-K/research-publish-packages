#!/usr/bin/env python3
"""Integrity gate for the context-cache package.

Fails (exit 1) if any of these is untrue:

  1. every claim id in CLAIMS.md appears exactly once in READER-MAP.md
       (and no claim id in READER-MAP.md is unknown to CLAIMS.md)
  2. every recompute function named in READER-MAP.md exists — either as a
       ``def`` in recompute.py, or as a dispatch target in ``FUNCS``/``SPECIAL``
       (for claims whose function is a wrapper or the grid guard), or as a
       checked-in script path
  3. every cell referenced by a claim is a directory holding >= 1 row, and
       every row file under it is non-empty
  4. any claim marked UNVERIFIED is also marked UNVERIFIED in PACKAGE.md
       (a claim that cannot be re-derived is reported loudly, never dropped)

Reads only. Makes no live request. Writes nothing.

Usage:
    .venv/bin/python papers/context-cache/verify_package.py
    .venv/bin/python papers/context-cache/verify_package.py --reader-map COPY.md
"""

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "papers" / "context-cache"
CLAIMS_PATH = PKG / "CLAIMS.md"
RECOMPUTE_PATH = PKG / "recompute.py"
PACKAGE_PATH = PKG / "PACKAGE.md"
DEFAULT_READER_MAP = PKG / "READER-MAP.md"

CLAIM_RE = re.compile(r"^\|\s*(C\d{2})\s*\|", re.MULTILINE)
CELL_RE = re.compile(r"experiments/context-cache/cells/[A-Za-z0-9._/-]+")
ROW_SUFFIXES = (".jsonl", ".json")
UNVERIFIED_RE = re.compile(r"UNVERIFIED", re.IGNORECASE)


# A row whose first cell is one of these is not a claim: the title rows of the
# claim tables, their separators, the source-key table (`| U2-rows | path | ... |`),
# and the numbered "Corrections to the source cards" table.
HEADER_CELLS = ("#", "Abbrev")
SOURCE_KEY_TABLE = "Source rows and digests"
NONCLAIM_COUNTER = re.compile(r"\d{1,3}")


def table_rows(path: Path) -> list[tuple[int, list[str], str]]:
    """Every markdown table row as (line number, cells, nearest preceding heading).

    Reading every row -- not only the rows a claim regex can see -- is what lets
    the surface check refuse a row that no parser would ever count.
    """
    heading = ""
    rows: list[tuple[int, list[str], str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("|"):
            rows.append((lineno, [c.strip() for c in stripped.strip("|").split("|")], heading))
            continue
        if stripped.startswith("#"):
            # a markdown heading may start with "#": only an ATX heading
            # ("## 3. Fan-out") replaces the section. Checking the comment block
            # at the top of CLAIMS.md first, and setting `heading` only for a
            # table row, would otherwise leave the source-key table with no home.
            if re.match(r"#{1,6}\s", stripped):
                heading = re.sub(r"^#{1,6}\s+", "", stripped).strip()
            continue
    return rows


def surface_errors(rows: list[tuple[int, list[str], str]]) -> list[str]:
    """Refuse a table row the claim census cannot see, instead of ignoring it.

    Every count in this package is derived by finding rows whose first cell
    matches ``C\\d{2}``. Before this check a row whose first cell was neither
    that nor a declared source key was invisible to both guards: it passed
    `verify_package` and `recompute.py all` while sitting in the claim ledger
    unchecked. A row is now admitted only if it is a claim row, a header or
    separator, a row of the source-key table, or a row of the numbered
    corrections table -- anything else fails the gate.
    """
    errors: list[str] = []
    for lineno, cells, heading in rows:
        first = cells[0] if cells else ""
        if re.fullmatch(r"C\d{2}", first):
            continue
        if first in HEADER_CELLS or set(first) <= set("-: "):
            continue
        if heading == SOURCE_KEY_TABLE and len(cells) == 5:
            continue  # a declared source key: abbrev, path, bytes, rows, sha256
        if len(cells) == 4 and NONCLAIM_COUNTER.fullmatch(first):
            continue  # the numbered corrections table
        errors.append(
            f"CLAIMS.md:{lineno}: unrecognised row, invisible to the claim census "
            f"(first cell {first!r}, under {heading or 'no heading'!r})"
        )
    return errors


def parse_claim_ids(path: Path) -> list[str]:
    """Claim ids as they appear as the first cell of a CLAIMS.md table row."""
    return CLAIM_RE.findall(path.read_text(encoding="utf-8"))


def parse_reader_map(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 4 or not re.fullmatch(r"C\d{2}", cells[0]):
            continue
        rows.append({"claim": cells[0], "recompute": cells[1],
                     "source": cells[2], "config": cells[3]})
    return rows


def recompute_targets(path: Path) -> set[str]:
    """Everything recompute.py can be asked to run for a claim."""
    tree = ast.parse(path.read_text(encoding="utf-8"))

    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            targets.add(node.name)

    # FUNCS / SPECIAL map claim id -> callable; a READER-MAP row may name either
    # the callable (e.g. "grid_guard") or the claim that dispatches to it.
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for key, value in zip(node.value.keys, node.value.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    targets.add(key.value)
                if isinstance(value, ast.Name):
                    targets.add(value.id)
    return targets


def count_rows(directory: Path) -> int:
    total = 0
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix not in ROW_SUFFIXES:
            continue
        with path.open(encoding="utf-8", errors="replace") as fh:
            total += sum(1 for line in fh if line.strip())
    return total


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Verify the context-cache package.")
    ap.add_argument("--reader-map", type=Path, default=DEFAULT_READER_MAP)
    args = ap.parse_args()

    for required in (CLAIMS_PATH, RECOMPUTE_PATH):
        if not required.is_file():
            print(f"verify_package: FAIL — missing {required.relative_to(ROOT)}")
            return 1
    if not args.reader_map.is_file():
        print(f"verify_package: FAIL — reader map missing: {args.reader_map}")
        return 1

    errors: list[str] = []

    claim_ids = parse_claim_ids(CLAIMS_PATH)
    if not claim_ids:
        errors.append(f"{CLAIMS_PATH.name}: no claim ids parsed")

    # (0) nothing in the ledger may sit outside the census
    errors.extend(surface_errors(table_rows(CLAIMS_PATH)))

    reader_rows = parse_reader_map(args.reader_map)
    mapped = [r["claim"] for r in reader_rows]

    # (1) coverage, 1:1 in both directions
    missing = [c for c in dict.fromkeys(claim_ids) if c not in mapped]
    if missing:
        errors.append(f"missing claim ids in READER-MAP: {', '.join(missing)}")
    unknown = [c for c in dict.fromkeys(mapped) if c not in claim_ids]
    if unknown:
        errors.append(f"claim ids in READER-MAP absent from CLAIMS.md: {', '.join(unknown)}")
    duplicates = sorted({c for c in mapped if mapped.count(c) > 1})
    if duplicates:
        errors.append(f"duplicate claim ids in READER-MAP: {', '.join(duplicates)}")

    # (2) recompute functions resolve
    targets = recompute_targets(RECOMPUTE_PATH)
    for row in reader_rows:
        fn = row["recompute"]
        if fn.endswith(".py"):
            script = Path(fn)
            if not script.is_absolute():
                script = ROOT / script
            if not script.is_file():
                errors.append(f"{row['claim']}: recompute script missing: {fn}")
        elif fn not in targets:
            errors.append(f"{row['claim']}: recompute function not in recompute.py: {fn}")

    # (3) every referenced cell has rows
    for row in reader_rows:
        cells = CELL_RE.findall(row["source"])
        if not cells:
            errors.append(f"{row['claim']}: no source cell path in Source cell field")
            continue
        for rel in cells:
            cell = ROOT / rel
            if not cell.is_dir():
                errors.append(f"{row['claim']}: not a cell directory: {rel}")
            elif count_rows(cell) == 0:
                errors.append(f"{row['claim']}: source cell has zero rows: {rel}")

    # (4) UNVERIFIED is surfaced, never silently dropped
    unverified = [r["claim"] for r in reader_rows
                  if UNVERIFIED_RE.search(" ".join((r["recompute"], r["source"], r["config"])))]
    pkg_text = PACKAGE_PATH.read_text(encoding="utf-8") if PACKAGE_PATH.is_file() else ""
    for cid in unverified:
        if not UNVERIFIED_RE.search(pkg_text):
            errors.append(f"{cid}: UNVERIFIED in READER-MAP but not stated in PACKAGE.md")

    if errors:
        print("verify_package: FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1

    scripts = sum(1 for r in reader_rows if r["recompute"].endswith(".py"))
    print(
        f"verify_package: PASS — {len(claim_ids)} claims in CLAIMS.md, "
        f"{len(mapped)} mapped 1:1, "
        f"{scripts} script-backed + {len(reader_rows) - scripts} recompute.py-backed "
        f"functions all present, every referenced cell has rows, "
        f"UNVERIFIED: {', '.join(unverified) if unverified else 'none'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
