#!/usr/bin/env python3
"""build_fixture.py -- the single generator for LR-01 runtime fixtures.

One spec, one generator. The spec
(`experiments/ptr-engine/longrun/fixtures-spec/LR-01.spec.json`) holds every generation as a
named merge over its predecessor, plus the exact serialization each generation was written with.
This tool materializes a generation; it never invents content.

Usage
  python3 experiments/ptr-engine/tools/build_fixture.py --variant v5 --out /tmp/LR-01.v5.json
  python3 experiments/ptr-engine/tools/build_fixture.py --check
        # every recorded fixture path on disk must equal what the spec generates
  python3 experiments/ptr-engine/tools/build_fixture.py --check --variant v5 --out /tmp/copy.json
        # compare one file against one variant

Exit codes
  0  wrote the fixture / no drift
  1  drift or mismatch (safe: nothing was written)
  2  usage error (unknown variant, missing --out, no variant for --check with --out)
  3  refused: target carries the bytes of a frozen fixture and --force-frozen was not passed

Byte-identity is the acceptance test. The serialization recorded per variant in `emit`
(indent, ensure_ascii, sort_keys, trailing newline) is part of the fixture: re-serializing the
same document with different settings is a different file, and rows on disk pin sha256.

FIXTURE IDENTITY RULE -- a fixture is identified by its path *and* its digest. Rows pin
sha256, so a path is only an addressing convention. A regeneration that changes any byte MUST
write a new versioned path (`TX-AGG.v2.json`, a fresh `--out`), and it must
never overwrite the previous version in place, because rows pin the digest and identity-by-path
silently becomes false. This already happened once: `tasks-v7/TX-AGG.v1.json` was rewritten in place at
2026-11-09T08:57:28Z under the same gen-7 identifiers, leaving 278 rows pinned to a digest that
exists in no file and in no git ref (`measure/FIXTURE-MAP-MT36.note`). Identity survives only
if the old bytes keep the old path; nothing can repair it after the fact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DEFAULT_SPEC = REPO / "experiments" / "ptr-engine" / "longrun" / "fixtures-spec" / "LR-01.spec.json"

OK, DRIFT, USAGE, REFUSED = 0, 1, 2, 3


class SpecError(RuntimeError):
    pass


# ---------------------------------------------------------------- spec + merge
def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SpecError(f"spec not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise SpecError(f"spec is not valid JSON: {path}: {exc}") from None
    if spec.get("schema") != "consonance.fixture-spec/1":
        raise SpecError(f"unexpected spec schema: {spec.get('schema')!r}")
    if "base" not in spec or not isinstance(spec.get("variants"), dict):
        raise SpecError("spec needs a 'base' document and a 'variants' map")
    return spec


def apply_patch(node: dict, patch: dict) -> dict:
    """Deep merge-patch: null deletes, dict recurses, anything else (incl. lists) replaces.

    The reserved key '@order' sets the key order of that level; insertion order is significant
    because it is encoded in the emitted bytes.
    """
    out = dict(node)
    for key, value in patch.items():
        if key == "@order":
            continue
        if value is None:
            out.pop(key, None)
        elif isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = apply_patch(out[key], value)
        else:
            out[key] = value
    order = patch.get("@order")
    if order is not None:
        missing = [k for k in order if k not in out]
        if missing:
            raise SpecError(f"@order names keys that do not exist: {missing}")
        out = {k: out[k] for k in order}
    return out


def resolve(spec: dict, name: str, _seen: tuple[str, ...] = ()) -> dict:
    variants = spec["variants"]
    if name not in variants:
        raise SpecError(f"unknown variant {name!r}; spec declares: {', '.join(sorted(variants))}")
    if name in _seen:
        raise SpecError(f"variant parent cycle: {' -> '.join(_seen + (name,))}")
    variant = variants[name]
    parent = variant.get("parent")
    doc = spec["base"] if parent is None else resolve(spec, parent, _seen + (name,))
    if parent is None:
        if variant.get("patch") is not None:
            raise SpecError(f"variant {name!r} has no parent but carries a patch")
        return doc
    patch = variant.get("patch")
    if not isinstance(patch, dict):
        raise SpecError(f"variant {name!r} needs a 'patch' object")
    return apply_patch(doc, patch)


def serialize(doc: dict, emit: dict) -> bytes:
    text = json.dumps(
        doc,
        indent=emit["indent"],
        ensure_ascii=emit["ensure_ascii"],
        sort_keys=emit["sort_keys"],
    )
    return (text + ("\n" if emit.get("trailing_newline") else "")).encode("utf-8")


def build(spec: dict, name: str) -> bytes:
    variant = spec["variants"][name]
    emit = variant.get("emit") or {}
    for key in ("indent", "ensure_ascii", "sort_keys"):
        if key not in emit:
            raise SpecError(f"variant {name!r} is missing emit.{key}")
    return serialize(resolve(spec, name), emit)


# ---------------------------------------------------------------- diff reporting
def first_field_difference(generated: Any, on_disk: Any, path: str = "") -> str | None:
    """Name the first structural difference, as a dotted/bracketed JSON path."""
    if isinstance(generated, dict) and isinstance(on_disk, dict):
        gen_keys, disk_keys = list(generated), list(on_disk)
        if gen_keys != disk_keys:
            for a, b in zip(gen_keys, disk_keys):
                if a != b:
                    return f"{path + '.' if path else ''}{a} vs {b} (key order/name at this level)"
            if len(gen_keys) > len(disk_keys):
                extra = [k for k in gen_keys if k not in on_disk]
                return f"{path + '.' if path else ''}{extra[0]} (missing on disk)"
            extra = [k for k in disk_keys if k not in generated]
            return f"{path + '.' if path else ''}{extra[0]} (unexpected on disk)"
        for key in gen_keys:
            sub = first_field_difference(generated[key], on_disk[key], f"{path + '.' if path else ''}{key}")
            if sub:
                return sub
        return None
    if isinstance(generated, list) and isinstance(on_disk, list):
        if len(generated) != len(on_disk):
            return f"{path} (list length {len(generated)} != {len(on_disk)})"
        for index, (a, b) in enumerate(zip(generated, on_disk)):
            sub = first_field_difference(a, b, f"{path}[{index}]")
            if sub:
                return sub
        return None
    if generated != on_disk:
        return f"{path or '<document>'} (value differs)"
    return None


def describe_drift(name: str, generated: bytes, on_disk: bytes, generated_doc: dict, disk_doc: Any) -> str:
    first_byte = next(
        (i for i, (a, b) in enumerate(zip(generated, on_disk)) if a != b),
        min(len(generated), len(on_disk)),
    )
    field = None
    if isinstance(disk_doc, dict):
        field = first_field_difference(generated_doc, disk_doc)
    if field is None:
        field = "<bytes only: same JSON values, different serialization>"
    return (
        f"drift: {name} differs from the spec -> field differs: {field}; "
        f"first byte offset {first_byte}; generated {len(generated)} bytes / "
        f"on disk {len(on_disk)} bytes; on-disk sha256 {hashlib.sha256(on_disk).hexdigest()}"
    )


# ---------------------------------------------------------------- frozen semantics
def frozen_records(spec: dict) -> dict[str, dict]:
    return {name: v for name, v in spec["variants"].items() if v.get("frozen")}


def frozen_hit(spec: dict, target: Path) -> tuple[str, dict, list[str]] | None:
    """Return (kind, variant, reasons) when writing `target` would clobber frozen bytes."""
    if target.exists():
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        for name, v in frozen_records(spec).items():
            if v.get("sha256") == digest:
                return ("content", v, referencing(v))
    resolved = target.resolve()
    for name, v in frozen_records(spec).items():
        recorded = v.get("path")
        if recorded and (REPO / recorded).resolve() == resolved:
            return ("path", v, referencing(v))
    return None


def referencing(variant: dict) -> list[str]:
    refs = variant.get("referenced_by") or {}
    rows = list(refs.get("row_and_grade_files") or [])
    manifests = list(refs.get("manifests") or [])
    return rows + manifests


# ---------------------------------------------------------------- commands
def cmd_check(spec: dict, variant: str | None, out: str | None) -> int:
    if out:
        target = Path(out)
        if not target.is_absolute():
            target = (Path.cwd() / target).resolve()
        if not variant:
            raise SpecError("--check with --out needs --variant so the target can be compared")
        if not target.exists():
            print(f"drift: {target} does not exist", file=sys.stderr)
            return DRIFT
        generated = build(spec, variant)
        on_disk = target.read_bytes()
        if generated == on_disk:
            print(f"ok: {variant} {target} matches the spec ({hashlib.sha256(generated).hexdigest()})")
            return OK
        try:
            disk_doc = json.loads(on_disk)
        except json.JSONDecodeError:
            disk_doc = None
        print(describe_drift(variant, generated, on_disk, resolve(spec, variant), disk_doc), file=sys.stderr)
        return DRIFT

    worst = OK
    for name in spec["variants"]:
        variant_rec = spec["variants"][name]
        target = REPO / variant_rec["path"]
        generated = build(spec, name)
        if not target.exists():
            print(f"drift: {name} {variant_rec['path']} is missing from disk", file=sys.stderr)
            worst = DRIFT
            continue
        on_disk = target.read_bytes()
        if generated == on_disk:
            print(f"ok: {name} {variant_rec['path']} {hashlib.sha256(on_disk).hexdigest()}")
            continue
        try:
            disk_doc = json.loads(on_disk)
        except json.JSONDecodeError:
            disk_doc = None
        print(describe_drift(name, generated, on_disk, resolve(spec, name), disk_doc), file=sys.stderr)
        worst = DRIFT
    return worst


def cmd_emit(spec: dict, variant: str, out: str, force_frozen: bool) -> int:
    target = Path(out)
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    generated = build(spec, variant)
    hit = frozen_hit(spec, target)
    if hit and not force_frozen:
        kind, rec, refs = hit
        print(
            f"refused: {target} {'carries the exact bytes of' if kind == 'content' else 'is'} frozen fixture "
            f"{rec.get('label') or variant} (sha256 {rec['sha256']}, {rec.get('path')}).",
            file=sys.stderr,
        )
        print("frozen because:", rec.get("frozen_reason", "recorded fixture"), file=sys.stderr)
        if refs:
            print("referenced by:", file=sys.stderr)
            for ref in refs:
                print(f"  - {ref}", file=sys.stderr)
        else:
            print("referenced by: (spec records no row/manifest reference)", file=sys.stderr)
        print("pass --force-frozen to overwrite anyway; prefer writing to a new path.", file=sys.stderr)
        return REFUSED
    if hit:
        print(f"warning: overwriting frozen fixture {hit[1]['sha256']} because --force-frozen was passed",
              file=sys.stderr)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(generated)
    print(f"wrote {target} {len(generated)} bytes sha256 {hashlib.sha256(generated).hexdigest()} (variant {variant})")
    return OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Regenerate LR-01 runtime fixtures from the spec.")
    ap.add_argument("--variant", help="generation to build: " + ", ".join(sorted({"v1"})) + " ... (see spec)")
    ap.add_argument("--out", help="path to write (required unless --check)")
    ap.add_argument("--check", action="store_true", help="compare instead of write; non-zero on drift")
    ap.add_argument("--force-frozen", action="store_true", help="allow overwriting frozen fixture bytes")
    ap.add_argument("--spec", default=str(DEFAULT_SPEC), help="spec path (default: LR-01.spec.json)")
    args = ap.parse_args(argv)

    try:
        spec = load_spec(Path(args.spec))
        if args.check:
            return cmd_check(spec, args.variant, args.out)
        if not args.variant or not args.out:
            ap.error("--variant and --out are required when not using --check")
        return cmd_emit(spec, args.variant, args.out, args.force_frozen)
    except SpecError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    sys.exit(main())
