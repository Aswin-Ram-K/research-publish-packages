"""Canonical serialization shared by every record in the campaign arms."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def dumps(obj: Any) -> bytes:
    """UTF-8 JSON, sorted keys, compact separators, no ensure_ascii, LF only."""
    raw = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    raw = raw.rstrip(b" \t\n")
    return raw


def digest(data) -> str:
    """sha256 hex digest of raw bytes/str."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(bytes(data)).hexdigest()


__all__ = ["dumps", "digest"]
