#!/usr/bin/env python3
"""Verify historical preservation against a PRESERVE-MANIFEST.json baseline."""
import argparse, hashlib, json, os, sys, time

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def file_stat(p):
    st = os.stat(p)
    return st.st_size, st.st_mtime

def load_manifest(path):
    with open(path) as f:
        return json.load(f)

def list_files(root):
    out = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            out.append((rel, full))
    return out

def check(manifest):
    errors = []
    drift = {"modified": [], "deleted": [], "added": []}
    # roots
    for name, info in manifest.get("roots", {}).items():
        root = info["root"]
        if not os.path.isdir(root):
            errors.append(f"missing root: {root}")
            continue
        recorded = {e["relpath"]: e for e in info["files"]}
        # check recorded
        for rel, e in recorded.items():
            full = os.path.join(root, rel)
            if not os.path.isfile(full):
                drift["deleted"].append(f"{name}/{rel}")
                continue
            try:
                h = sha256_file(full)
            except Exception as ex:
                errors.append(f"unreadable: {full}: {ex}")
                continue
            if h != e["sha256"]:
                drift["modified"].append(f"{name}/{rel}")
            # size check
            try:
                sz, _ = file_stat(full)
            except Exception as ex:
                errors.append(f"stat failed: {full}: {ex}")
                continue
            if sz != e["size"]:
                if f"{name}/{rel}" not in drift["modified"]:
                    drift["modified"].append(f"{name}/{rel}")
        # added
        for rel, full in list_files(root):
            if rel not in recorded:
                drift["added"].append(f"{name}/{rel}")
    # external single files
    for e in manifest.get("external", []):
        p = e["path"]
        if not os.path.isfile(p):
            drift["deleted"].append(p)
            continue
        try:
            h = sha256_file(p)
        except Exception as ex:
            errors.append(f"unreadable: {p}: {ex}")
            continue
        if h != e["sha256"]:
            drift["modified"].append(p)
        try:
            sz, _ = file_stat(p)
        except Exception as ex:
            errors.append(f"stat failed: {p}: {ex}")
            continue
        if sz != e["size"]:
            if p not in drift["modified"]:
                drift["modified"].append(p)
    # manifest/path mismatch: ensure recorded root paths exist in manifest roots
    if "roots" not in manifest:
        errors.append("manifest missing roots")
    ok = (not errors) and not (drift["modified"] or drift["deleted"] or drift["added"])
    return ok, errors, drift

def build_baseline(manifest_path):
    # Not used for generation here; --update regenerates by calling external? 
    # We'll just error: regeneration must be done by manifest builder.
    print("ERROR: --update not supported in this checker; regenerate manifest via builder.", file=sys.stderr)
    sys.exit(2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.update:
        # regenerate not implemented in checker; fail closed
        print(json.dumps({"ok": False, "error": "update not implemented in checker"}) if args.json else "update not implemented")
        sys.exit(2)

    try:
        manifest = load_manifest(args.baseline)
    except Exception as ex:
        msg = f"cannot load manifest: {ex}"
        if args.json:
            print(json.dumps({"ok": False, "errors": [msg], "drift": {}}))
        else:
            print(msg)
        sys.exit(1)

    ok, errors, drift = check(manifest)
    result = {"ok": ok, "errors": errors, "drift": drift}
    if args.json:
        print(json.dumps(result))
    else:
        if errors:
            for e in errors:
                print("ERROR:", e)
        for k in ("modified", "deleted", "added"):
            for p in drift[k]:
                print(f"DRIFT {k}: {p}")
        if ok:
            print("OK: no drift")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
