#!/usr/bin/env python3
"""grader_identity.py - WHO WROTE THIS GRADE DOCUMENT: a stamp, or a derivation.

WHY THIS EXISTS (orchestration/handoffs/QUALITY-ERA-TABLE.json, .evidence.real_output.census):
of 20 grade_v5 documents, 9 record a grader sha -- all nine are regrade outputs --
and the 11 genuinely stored grade files record none. Every historical accuracy
figure was therefore datable only by RE-RUNNING the grader against the rows, which
is why REGRADE-ONE-COMMAND had to exist before any grid could be trusted.

THE FIX IS FORWARD-ONLY. grade_v5.py stamps every document it writes with
`grader_sha256` (its own file's sha256 at write time), `grader_version` and
`rows_sha256` (the rows file it graded), and REFUSES to write at all if any of the
three cannot be computed -- an unstamped grade file is the defect, not a fallback.
Historical files are NOT restamped (`docs/QUALITY-ERAS.md` records the era table;
the 11 unstamped files stay datable only by re-derivation).

ONE RESOLVER, NO SECOND COPY. `grader_identity(document)` is the only place that
answers "which grader wrote this". It returns the stamped identity when present;
for a historical document it says `source="derived"` and requires the caller to
pass the regrade result that re-derived the sha. There is NO lookup table of
historical shas: there is only ever one current grader, and a sha table would be
the same drift this module exists to prevent.

    from grader_identity import grader_identity
    ident = grader_identity(doc)                       # {"sha256": None, "source": "derived", ...}
    ident = grader_identity(doc, regrade_result)       # {"sha256": "<regrade sha>", "source": "derived", ...}

Offline. Stdlib only. Reads nothing but the bytes of the file it is asked to hash.
"""
import hashlib
import os
import re

# The three fields grade_v5.py writes. All three or nothing: a partially stamped
# document is the defect this module exists to make visible.
STAMP_KEYS = ("grader_sha256", "grader_version", "rows_sha256")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

STAMP = "stamp"
DERIVED = "derived"


def file_sha256(path):
    """sha256 of a file's bytes -- the one implementation, used by writer and reader."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_sha(value, field):
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise ValueError("malformed %s: %r is not a 64-hex sha256" % (field, value))
    return value


def missing_stamp_keys(document):
    """The stamp fields this document does not carry (empty list == fully stamped)."""
    return [k for k in STAMP_KEYS if not document.get(k)]


def is_stamped(document):
    """True only when ALL THREE fields are present -- two of three is not a stamp."""
    return not missing_stamp_keys(document)


def _derived_sha(regrade_result):
    """The sha a regrade run re-derived. The caller must supply it; we never guess."""
    if isinstance(regrade_result, str):
        return _check_sha(regrade_result, "regrade_result")
    if isinstance(regrade_result, dict):
        for key in ("grader_sha256", "sha256", "sha"):
            if regrade_result.get(key):
                return _check_sha(regrade_result[key], "regrade_result[%r]" % key)
        raise ValueError("regrade_result carries no grader sha: keys=%s"
                         % sorted(regrade_result))
    raise TypeError("regrade_result must be a sha256 string or a dict carrying one, "
                    "got %r -- a historical document is NOT silently accepted"
                    % (regrade_result,))


def grader_identity(document, regrade_result=None):
    """Return {"sha256", "source", "stamped", ...} for one grade document.

    source="stamp"   -- the document dates itself (forward-only from GRADER-STAMP).
    source="derived" -- historical file with no stamp; `sha256` is the sha the
                        caller's regrade run re-derived, and is None when the
                        caller passed no regrade result (the report still says
                        `derived`, never a fabricated identity).
    """
    if not isinstance(document, dict):
        raise TypeError("document must be a dict, got %r" % (type(document),))

    missing = missing_stamp_keys(document)
    if not missing:
        sha = _check_sha(document["grader_sha256"], "grader_sha256")
        rows_sha = _check_sha(document["rows_sha256"], "rows_sha256")
        version = document["grader_version"]
        if not isinstance(version, str) or not version.strip():
            raise ValueError("malformed grader_version: %r" % (version,))
        return {"sha256": sha, "source": STAMP, "stamped": True,
                "grader_version": version, "rows_sha256": rows_sha,
                "rows_source": STAMP, "missing": []}

    # A field that IS present but unparseable is a defect, not "historical":
    # say so instead of folding it into `derived`.
    if document.get("grader_sha256"):
        _check_sha(document["grader_sha256"], "grader_sha256")
    if document.get("rows_sha256"):
        _check_sha(document["rows_sha256"], "rows_sha256")

    sha = _derived_sha(regrade_result) if regrade_result is not None else None
    out = {"sha256": sha, "source": DERIVED, "stamped": False,
           "grader_version": document.get("grader_version") or None,
           "rows_sha256": document.get("rows_sha256") or None,
           "rows_source": (STAMP if document.get("rows_sha256") else DERIVED),
           "missing": missing}
    if sha is None:
        out["requires"] = "regrade_result"
    return out


def describe(identity):
    """One line a later reader can rely on; never claims more than the stamp holds."""
    if identity.get("source") == STAMP:
        return ("grader %s (version %s), rows %s -- stamped by the writer"
                % (identity["sha256"][:16], identity["grader_version"],
                   identity["rows_sha256"][:16]))
    if identity.get("sha256"):
        return ("grader %s -- DERIVED by re-running the grader, not stamped"
                % (identity["sha256"][:16],))
    return ("grader sha UNKNOWN -- historical document with no stamp and no "
            "regrade result supplied (missing: %s)" % ", ".join(identity.get("missing") or []))


if __name__ == "__main__":       # small read-only probe for an operator
    import json
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("usage: grader_identity.py <grade-v5.json> [regrade-count.json]")
    with open(sys.argv[1], encoding="utf-8") as fh:
        _doc = json.load(fh)
    _res = None
    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as fh:
            _res = json.load(fh)
    _ident = grader_identity(_doc, _res)
    print(json.dumps(_ident, indent=1, sort_keys=True))
    print(describe(_ident))
