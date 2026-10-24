#!/usr/bin/env python3
"""regen_manifest.py -- regenerate MANIFEST.json from disk.

SELF-EXEMPTION CONVENTION (authority: scratch/uneutral10/manifest.py:38-44, the generator of the
current shipped package; structural source scratch/udtag1/regen_manifest.py):

  * ``files[]`` lists every regular file in the tree EXCEPT MANIFEST.json itself, sorted by path;
  * ``counts.files``       = len(files[]) + 1     -- INCLUDES MANIFEST.json;
  * ``counts.bytes_total`` = sum(bytes of files[]) -- EXCLUDES MANIFEST.json's own bytes;
  * ``manifest_self`` = sha256 of json.dumps(body, indent=2, sort_keys=True) with
    ``generated_utc`` blanked and ``manifest_self`` dropped;
  * ``source`` / ``source_sha256`` / ``kind`` / ``identical_to_source`` are preserved from the
    previous manifest for paths it already described; a path it did not describe gets an explicit
    "provenance not established" note.

``counts.files`` including the manifest while ``counts.bytes_total`` excludes it is the exact
convention two units have mis-stated -- the note beside ``manifest_self`` restates it in-manifest.

Use ``--generated-utc`` to pin the timestamp and make the command byte-idempotent.
"""
import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pkg

SELF = "MANIFEST.json"
SELF_NOTE = ("NOT LISTED (a self-referential sha256 is impossible); MANIFEST.json is the only file "
             "in the tree absent from files[]. counts.files INCLUDES it (+1) and counts.bytes_total "
             "EXCLUDES its own bytes -- that is the self-exemption convention.")


def main():
    ap = argparse.ArgumentParser(description="regenerate MANIFEST.json from disk")
    _pkg.add_package_arg(ap)
    ap.add_argument("--generated-utc", default=None,
                    help="pin the RFC3339 timestamp (makes the output byte-idempotent)")
    ap.add_argument("--no-note", action="store_true",
                    help="omit the manifest_self_note key (reproduces the shipped bytes exactly)")
    a = ap.parse_args()
    tree = _pkg.resolve_package(a.package)
    mp = os.path.join(tree, SELF)
    old = json.load(open(mp, encoding="utf-8")) if os.path.isfile(mp) else {}
    old_by = {e["path"]: e for e in old.get("files", [])}

    files_out = []
    added, changed = [], []
    for rel, full, sz in _pkg.iter_files(tree):
        if rel == SELF:
            continue
        h = _pkg.sha256_file(full)
        o = old_by.get(rel)
        if o is None:
            added.append(rel)
            e = {"path": rel,
                 "source": ("present in the shipped tree at regeneration time; source provenance "
                            "not established by this regeneration"),
                 "source_sha256": "", "sha256": h, "bytes": sz,
                 "identical_to_source": False, "kind": "copy"}
        else:
            e = dict(o)
            if e.get("sha256") != h:
                changed.append(rel)
            e["sha256"] = h
            e["bytes"] = sz
            # source / source_sha256 / identical_to_source / kind are PRESERVED, never recomputed:
            # that is exactly what scratch/uneutral10/manifest.py:24-26 does (src.get(...)).  One
            # shipped entry (verify/recompute-claims.py) carries identical_to_source=true with an
            # EMPTY source_sha256; recomputing would silently flip it to false, so we do not.
        files_out.append(e)
    files_out.sort(key=lambda x: x["path"])

    body = dict(old)
    body["generated_utc"] = a.generated_utc or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    counts = dict(old.get("counts", {}))
    counts["files"] = len(files_out) + 1                     # self-INCLUSIVE
    counts["bytes_total"] = sum(e["bytes"] for e in files_out)  # self-EXEMPT
    body["counts"] = counts
    body["files"] = files_out
    body.pop("manifest_self", None)
    if a.no_note:
        body.pop("manifest_self_note", None)
    else:
        body["manifest_self_note"] = SELF_NOTE
    canon = json.dumps(body, indent=2, sort_keys=True).replace(body["generated_utc"], "")
    body["manifest_self"] = hashlib.sha256(canon.encode()).hexdigest()

    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(body, fh, indent=2)

    print("files_on_disk: %d   bytes_total: %d   manifest_self: %s"
          % (counts["files"], counts["bytes_total"], body["manifest_self"][:16]))
    print("files[] entries: %d (excludes MANIFEST.json)" % len(files_out))
    print("added: %s   changed: %d" % (added, len(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
