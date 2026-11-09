#!/usr/bin/env python3
"""withdrawn_screen.py - re-scan the corpus against `measure/WITHDRAWN.json` and hold the line.

`withdrawn_index.py` screens ONE file. This tool screens the whole publication surface it was
pointed at (every `docs/**/*.md`, every `experiments/ptr-engine/measure/*.md`, and the root
markdown files) and compares the result with the frozen verdict table in
`experiments/ptr-engine/measure/WITHDRAWN-SCREEN.json`, written by card `WITHDRAWN-SCREEN`.

  --check          re-scan; exit 1 when
                     * the scanned-file count drops below the recorded count, or
                     * a file recorded CLEAN trips again, or
                     * a file recorded as tripping gains an entry id it did not have, or
                     * either of the two CORRECTED documents trips.
                   Exit 0 otherwise (reported-only offenders are expected, not failures).
  --scan           print the current scan as JSON (no comparison).
  --scan --write   regenerate the `scanned` block of the screen record, preserving the
                   `corrected` and `reported_only` blocks already in it.
  --file PATH      screen a single arbitrary file; exit 1 if it trips (used by the tests and by
                   a `/tmp` paste-back closure proof).
  --strict         opt-in window for the two published latency pages (card WITHDRAWN-REGISTER-FIX):
                   the correction must sit in the SAME PARAGRAPH (blank-line delimited) as the
                   hit, instead of anywhere within 400 characters. A stale sentence can no longer
                   be excused by a marker in a neighbouring paragraph. Non-strict behaviour is
                   byte-identical to the recorded screen.

Two classes of hit:
  trip                a withdrawn quote with no correction marker inside the window.
  substring_artifact  the same, but the quote is preceded by a digit, i.e. it is a fragment of a
                      larger, unrelated number. The register no longer carries a bare 3-character
                      quote (WI-011's `98.7` was narrowed to `98.7 % prefix` on 2026-10-26), but
                      the class stays: a future entry whose quote is a numeric fragment is
                      reported as an artifact, never as a withdrawn claim.

Read-only except for `--write`. Offline, zero requests.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_REGISTER = os.path.abspath(os.path.join(HERE, "..", "measure", "WITHDRAWN.json"))
DEFAULT_SCREEN = os.path.abspath(os.path.join(HERE, "..", "measure", "WITHDRAWN-SCREEN.json"))

# The two documents the register flagged and earlier cards corrected. Neither may trip again.
CORRECTED = ("docs/LATENCY-REPORT.md", "experiments/ptr-engine/measure/ARM-RECONCILE.md")

sys.path.insert(0, HERE)
import withdrawn_index as wi  # noqa: E402  (sibling module, same directory)


def load_register(path: str | None = None) -> dict:
    return wi.load_register(path or DEFAULT_REGISTER)


def discover(root: str) -> list[str]:
    """Every markdown file on the screened surface, relative to `root`, sorted."""
    out: list[str] = []
    for base, pattern in (("docs", "*.md"), ("experiments/ptr-engine/measure", "*.md")):
        d = os.path.join(root, base)
        for dirpath, _dirs, files in os.walk(d):
            for f in files:
                if f.endswith(".md"):
                    out.append(os.path.relpath(os.path.join(dirpath, f), root))
    for f in os.listdir(root):
        if f.endswith(".md") and os.path.isfile(os.path.join(root, f)):
            out.append(f)
    return sorted(out)


def scan_file(path: str, reg: dict, window: int = wi.WINDOW, strict: bool = False) -> list[dict]:
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    hits: list[dict] = []
    for e in reg["entries"]:
        quote = e.get("quote") or ""
        if not quote:
            continue
        start = 0
        while True:
            i = text.find(quote, start)
            if i < 0:
                break
            j = i + len(quote)
            if not wi.corrected(text, i, j, e.get("markers") or [], window, strict=strict):
                hits.append({
                    "entry": e["id"],
                    "line": text.count("\n", 0, i) + 1,
                    # a quote glued to a preceding digit is a fragment of a bigger number
                    "artifact": i > 0 and text[i - 1].isdigit(),
                    "snippet": " ".join(text[i:j].split())[:110],
                })
            start = j
    return hits


def verdict_for(hits: list[dict]) -> tuple[str, list[str]]:
    real = [h for h in hits if not h["artifact"]]
    arts = [h for h in hits if h["artifact"]]
    if real:
        return "trips", sorted({h["entry"] for h in real})
    if arts:
        return "clean_substring_artifact", sorted({h["entry"] for h in arts})
    return "clean", []


def scan(root: str, reg: dict, strict: bool = False) -> list[dict]:
    rows = []
    for rel in discover(root):
        hits = scan_file(os.path.join(root, rel), reg, strict=strict)
        verdict, entries = verdict_for(hits)
        row = {"path": rel, "verdict": verdict, "entries": entries}
        if hits:
            row["hits"] = [{"entry": h["entry"], "line": h["line"], "artifact": h["artifact"]}
                           for h in hits]
        rows.append(row)
    return rows


def check(root: str, reg: dict, screen_path: str, strict: bool = False) -> int:
    with open(screen_path, encoding="utf-8") as fh:
        rec = json.load(fh)
    recorded = {r["path"]: (r["verdict"], set(r.get("entries") or [])) for r in rec["scanned"]}
    recorded_count = int(rec.get("scanned_count") or len(rec["scanned"]))
    problems: list[str] = []

    files = discover(root)
    if len(files) < recorded_count:
        problems.append(f"SCANNED-COUNT DROPPED: {len(files)} < recorded {recorded_count}")
    seen = set()
    for rel in files:
        seen.add(rel)
        hits = scan_file(os.path.join(root, rel), reg, strict=strict)
        verdict, entries = verdict_for(hits)
        exp = recorded.get(rel)
        if exp is None:
            if verdict == "trips":
                problems.append(f"NEW FILE TRIPS: {rel} -> {','.join(entries)}")
            continue
        exp_verdict, exp_entries = exp
        if exp_verdict in ("clean", "clean_substring_artifact"):
            if verdict == "trips":
                problems.append(f"REGRESSED: {rel} was {exp_verdict}, now trips "
                                f"{','.join(entries)} (line "
                                f"{','.join(str(h['line']) for h in hits if not h['artifact'])})")
        else:  # recorded as tripping
            new = set(entries) - exp_entries
            if new:
                problems.append(f"NEW ENTRY in {rel}: {','.join(sorted(new))}")
    for rel in sorted(seen - set(recorded)):
        pass  # additions are fine: the surface may grow
    missing = set(recorded) - seen
    for rel in sorted(missing):
        if rel in CORRECTED:
            problems.append(f"CORRECTED DOCUMENT MISSING: {rel}")

    for rel in CORRECTED:
        if rel not in seen:
            continue
        verdict, entries = verdict_for(scan_file(os.path.join(root, rel), reg, strict=strict))
        if verdict == "trips":
            problems.append(f"CORRECTED DOCUMENT TRIPS AGAIN: {rel} -> {','.join(entries)}")

    for p in problems:
        print("FAIL", p)
    trips = sum(1 for r in scan(root, reg, strict=strict) if r["verdict"] == "trips")
    mode = " [strict paragraphs]" if strict else ""
    if problems:
        print(f"SCREEN FAILED: {len(problems)} problem(s); {len(files)} files scanned, "
              f"{trips} tripping{mode}")
        return 1
    print(f"SCREEN CLEAN: {len(files)} files scanned (>= {recorded_count} recorded), "
          f"{trips} reported-only offender(s), both corrected documents clean{mode}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Re-scan the corpus for withdrawn claims and compare "
                                             "with the frozen screen record.")
    ap.add_argument("--check", action="store_true", help="exit 1 if the screen regressed")
    ap.add_argument("--scan", action="store_true", help="print the current scan as JSON")
    ap.add_argument("--write", action="store_true", help="with --scan, rewrite the scanned block")
    ap.add_argument("--file", metavar="PATH", help="screen one file; exit 1 if it trips")
    ap.add_argument("--root", default=ROOT, help="corpus root (default: the repository)")
    ap.add_argument("--screen", default=DEFAULT_SCREEN, help="screen record JSON")
    ap.add_argument("--register", default=None, help="WITHDRAWN.json override")
    ap.add_argument("--strict", action="store_true",
                    help="window = the enclosing paragraph, not 400 chars (opt-in, published pages)")
    a = ap.parse_args(argv)
    reg = load_register(a.register)

    if a.file:
        hits = scan_file(a.file, reg, strict=a.strict)
        verdict, entries = verdict_for(hits)
        real = [h for h in hits if not h["artifact"]]
        for h in hits:
            kind = "ARTIFACT" if h["artifact"] else "WITHDRAWN"
            print(f"{kind} {h['entry']} line {h['line']}: {h['snippet']}")
        print(("TRIPS " if real else "CLEAN ") + f"{a.file}: verdict={verdict}"
              + (f" entries={','.join(entries)}" if entries else ""))
        return 1 if real else 0

    if a.scan:
        rows = scan(a.root, reg, strict=a.strict)
        if a.write:
            rec = {"scanned_count": len(rows), "scanned": rows}
            if os.path.isfile(a.screen):
                with open(a.screen, encoding="utf-8") as fh:
                    old = json.load(fh)
                for k in ("corrected", "reported_only"):
                    if k in old:
                        rec[k] = old[k]
            with open(a.screen, "w", encoding="utf-8") as fh:
                json.dump(rec, fh, indent=1, sort_keys=False)
                fh.write("\n")
            print(f"WROTE {a.screen}: {len(rows)} scanned")
        else:
            print(json.dumps(rows, indent=1))
        return 0

    if a.check:
        return check(a.root, reg, a.screen, strict=a.strict)

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
