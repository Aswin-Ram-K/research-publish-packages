#!/usr/bin/env python3
"""c8_census_check.py — gate for experiments/miss-law/FIT-GAP-CENSUS.md (unit C8-CENSUS-FIX-V2).

Re-derives the 21-row census from the sources the document cites. It is NOT a spot-check:
it parses every row of section 2, opens the exact `rows.jsonl` line each row cites, and
requires the row's own cell/server/phase/role/n_payload to equal the document's claim.
It then re-derives every section-1 total, the section-4 prediction, and resolves every
`path:line` citation anywhere in the document.

Exits 0 only when all of that holds. Exits 1 with a printed reason otherwise.

Usage:
  python3 experiments/ptr-engine/tools/c8_census_check.py
  python3 experiments/ptr-engine/tools/c8_census_check.py --root /tmp/c8-census/red
"""

import argparse
import json
import os
import re
import sys

REL_DOC = "experiments/miss-law/FIT-GAP-CENSUS.md"
REL_ROWS = "experiments/miss-law/rows.jsonl"
REL_FIT = "experiments/miss-law/law_fit.json"

CITATION_RE = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:py|json|jsonl|md|txt)):(\d+)(?:-(\d+))?`")


class Checker:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.fails = []
        self.passes = 0

    # ---------- helpers ----------
    def path(self, rel):
        return os.path.join(self.root, rel)

    def read(self, rel):
        with open(self.path(rel), "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def lines(self, rel):
        return self.read(rel).splitlines()

    def ok(self, label, detail=""):
        self.passes += 1
        if detail:
            print("  PASS %-46s %s" % (label, detail))

    def bad(self, label, detail):
        self.fails.append("%s: %s" % (label, detail))
        print("  FAIL %-46s %s" % (label, detail))

    def want(self, label, got, exp):
        if got == exp:
            self.ok(label, "= %r" % (got,))
        else:
            self.bad(label, "expected %r, got %r" % (exp, got))

    @staticmethod
    def bare(cell):
        return cell.replace("`", "").replace("*", "").strip()

    # ---------- citation resolution ----------
    def resolve_citation(self, token, rel_hint=None):
        """Return (file_lines, line_no) for a 'path:line' token, or raise with a reason."""
        m = re.match(r"^(.*):(\d+)$", token)
        if not m:
            raise ValueError("not a path:line citation")
        rel = m.group(1).lstrip("/")
        line_no = int(m.group(2))
        if not os.path.exists(self.path(rel)):
            raise ValueError("source file not found: %s" % rel)
        lines = self.lines(rel)
        if line_no < 1 or line_no > len(lines):
            raise ValueError("%s has %d lines, cited line %d does not resolve"
                             % (rel, len(lines), line_no))
        return lines, line_no

    # ---------- sections ----------
    def check_doc_citations(self, text):
        print("\n[1] every path:line citation in the document resolves")
        seen = 0
        for m in CITATION_RE.finditer(text):
            token, start, end = m.group(1), int(m.group(2)), m.group(3)
            try:
                lines, _ = self.resolve_citation("%s:%d" % (token, start))
                if end is not None:
                    e = int(end)
                    if e < start or e > len(lines):
                        raise ValueError("range end %d outside %d lines" % (e, len(lines)))
                seen += 1
            except ValueError as exc:
                self.bad("citation %s:%s" % (token, start), str(exc))
        if seen == 0:
            self.bad("citation scan", "found no path:line citations at all")
        else:
            self.ok("citations resolved", "%d distinct path:line occurrences" % seen)

    def parse_row_table(self, text):
        rows, in_tbl = [], False
        for line in text.splitlines():
            if line.startswith("| # | cell |"):
                in_tbl = True
                continue
            if in_tbl:
                if not line.startswith("|"):
                    break
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) != 8:
                    continue
                if set(cells[0]) <= set("-: "):
                    continue
                rows.append(cells)
        return rows

    def check_rows(self, text, all_rows):
        print("\n[2] the 21-row table, re-derived row by row")
        doc_rows = self.parse_row_table(text)
        self.want("row-table length", len(doc_rows), 21)
        if len(doc_rows) != 21:
            return []

        total = len(all_rows)
        nums = []
        groups = {}
        payloads = {"residue": {}, "position": {}}
        non_measure = 0
        for cells in doc_rows:
            idx_s, cell, server, phase, role, npay_s, source, correction = cells
            try:
                idx = int(self.bare(idx_s))
                npay = int(self.bare(npay_s))
            except ValueError:
                self.bad("row %r" % idx_s, "non-integer index or n_payload")
                continue
            nums.append(idx)
            try:
                lines, line_no = self.resolve_citation(self.bare(source).split()[0])
            except ValueError as exc:
                self.bad("row %d citation" % idx, str(exc))
                continue
            raw = lines[line_no - 1].strip()
            if not raw.startswith("{"):
                self.bad("row %d citation" % idx,
                         "%s:%d is not a JSON row" % (REL_ROWS, line_no))
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as exc:
                self.bad("row %d citation" % idx, "%s:%d is not parseable JSON: %s"
                         % (REL_ROWS, line_no, exc))
                continue
            claimed = {
                "cell": self.bare(cell),
                "server": self.bare(server),
                "phase": self.bare(phase),
                "role": self.bare(role),
                "n_payload": npay,
            }
            actual = {
                "cell": rec.get("cell"),
                "server": rec.get("server"),
                "phase": rec.get("phase"),
                "role": rec.get("role"),
                "n_payload": rec.get("n_payload"),
            }
            mismatch = {k: (v, actual[k]) for k, v in claimed.items() if v != actual[k]}
            if mismatch:
                self.bad("row %d fields" % idx,
                         "document says %s but %s:%d holds %s"
                         % (mismatch, REL_ROWS, line_no, actual))
                continue
            if line_no != idx:
                self.bad("row %d citation" % idx,
                         "cites line %d but table row number is %d" % (line_no, idx))
                continue
            if "SNAPSHOT-LAG" not in correction:
                self.bad("row %d correction" % idx,
                         "class is not SNAPSHOT-LAG: %r" % correction[:60])
                continue
            if "residue" in rec:
                self.bad("row %d schema" % idx, "tail row unexpectedly carries a 'residue' key")
                continue
            if rec.get("error") is not None:
                self.bad("row %d error" % idx, "error is %r, census claims null" % rec.get("error"))
                continue
            groups[(claimed["phase"], claimed["server"], claimed["role"])] = \
                groups.get((claimed["phase"], claimed["server"], claimed["role"]), 0) + 1
            if claimed["phase"] in payloads:
                b = payloads[claimed["phase"]]
                b[claimed["n_payload"]] = b.get(claimed["n_payload"], 0) + 1
            if claimed["role"] != "measure":
                non_measure += 1

        self.ok("rows field-verified", "%d/21 rows match their cited line exactly" % len(nums))
        self.want("cited lines are the appended tail", nums, list(range(total - 20, total + 1)))
        self.want("group split", groups,
                  {("residue", "vllm", "prime"): 5,
                   ("residue", "vllm", "measure"): 5,
                   ("position", "sglang", "measure"): 11})
        self.want("role != measure", non_measure, 5)
        self.want("residue n_payload histogram", payloads["residue"], {64: 2, 512: 4, 1056: 4})
        self.want("position n_payload histogram", payloads["position"], {1: 11})
        return doc_rows

    def check_totals(self, text, all_rows):
        print("\n[3] section-1 totals re-derived from rows.jsonl / law_fit.json")
        fit = json.loads(self.read(REL_FIT))
        counts = {}
        for r in all_rows:
            counts[r.get("role")] = counts.get(r.get("role"), 0) + 1
        expected = {
            "rows.jsonl line count": len(all_rows),
            "law_fit.json:n_rows": fit.get("n_rows"),
            "role == measure": counts.get("measure"),
            "role == prime": counts.get("prime"),
            "control rows": sum(counts.get(k, 0) for k in ("warm1", "warm2", "cold1", "cold2")),
            "rows carrying l_app": sum(1 for r in all_rows if r.get("L_app") is not None),
            "measure rows lacking l_app": sum(
                1 for r in all_rows if r.get("role") == "measure" and r.get("L_app") is None),
            "appended tail": 21,
        }
        found = 0
        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 3:
                continue
            claim = self.bare(cells[0]).lower()
            m = re.search(r"-?\d+", self.bare(cells[1]))
            if not m:
                continue
            value = int(m.group(0))
            key = None
            for k in expected:
                if claim.startswith(k) or k in claim:
                    key = k
                    break
            if key is None:
                continue
            found += 1
            self.want("total %r" % key, value, expected[key])
            src = re.search(r"`([^`]+)`", cells[2])
            if not src:
                self.bad("total %r source" % key, "no citation in the source column")
                continue
            try:
                if ":" in src.group(1):
                    slines, sno = self.resolve_citation(src.group(1))
                    if not src.group(1).split(":")[0].endswith((".jsonl", ".txt")) \
                            and str(value) not in slines[sno - 1]:
                        self.bad("total %r source" % key,
                                 "cited line %s does not contain %d" % (src.group(1), value))
                elif not os.path.exists(self.path(src.group(1))):
                    self.bad("total %r source" % key, "%s not found" % src.group(1))
            except ValueError as exc:
                self.bad("total %r source" % key, str(exc))
        if found < 8:
            self.bad("section-1 table", "only %d total rows parsed, expected 8" % found)
        else:
            self.ok("section-1 totals", "%d claims re-derived" % found)

    def check_prediction(self, all_rows):
        print("\n[4] section-4 onfile - intail == n_residue_rows, re-run")
        fit = json.loads(self.read(REL_FIT))
        tail = all_rows[-21:]

        def resid_measure(rows):
            return sum(1 for r in rows
                       if r.get("role") == "measure" and not r.get("error")
                       and r.get("phase") == "residue")

        for server in ("sglang", "vllm"):
            declared = fit["servers"][server]["n_residue_rows"]
            onfile = sum(1 for r in all_rows
                         if r.get("role") == "measure" and not r.get("error")
                         and r.get("phase") == "residue" and r.get("server") == server)
            intail = resid_measure([r for r in tail if r.get("server") == server])
            self.want("%s declared n_residue_rows" % server, declared,
                      {"sglang": 232, "vllm": 73}[server])
            self.want("%s onfile - intail == declared" % server, onfile - intail, declared)
            if server == "vllm":
                self.want("vllm shortfall is the tail", onfile - declared, intail)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=default_root)
    ap.add_argument("--doc", default=REL_DOC)
    args = ap.parse_args()

    c = Checker(args.root)
    print("c8_census_check root=%s doc=%s" % (c.root, args.doc))
    for rel in (args.doc, REL_ROWS, REL_FIT):
        if not os.path.exists(c.path(rel)):
            print("  FAIL missing  %s" % rel)
            print("\nRED — required input missing")
            return 1
    text = c.read(args.doc)
    all_rows = [json.loads(l) for l in c.lines(REL_ROWS) if l.strip()]

    c.check_doc_citations(text)
    c.check_rows(text, all_rows)
    c.check_totals(text, all_rows)
    c.check_prediction(all_rows)

    print("\n%d checks passed, %d failed" % (c.passes, len(c.fails)))
    if c.fails:
        print("RED — census does not re-derive from its citations:")
        for f in c.fails:
            print("  - %s" % f)
        return 1
    print("GREEN — 21/21 appended rows re-derived from cited lines; "
          "%d lines, measure %d + prime %d + controls %d"
          % (len(all_rows),
             sum(1 for r in all_rows if r.get("role") == "measure"),
             sum(1 for r in all_rows if r.get("role") == "prime"),
             sum(1 for r in all_rows if r.get("role") in ("warm1", "warm2", "cold1", "cold2"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
