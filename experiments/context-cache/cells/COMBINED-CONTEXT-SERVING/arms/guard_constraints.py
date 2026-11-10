"""Guard: required negative-constraint lines must survive in the preamble."""

from __future__ import annotations

from typing import Any


def required_constraint_lines(fixture: dict) -> list[str]:
    acc = (fixture or {}).get("acceptance", {}) or {}
    out = []
    for nc in acc.get("negative_constraints", []) or []:
        line = nc.get("prose") or nc.get("id") or ""
        if line:
            out.append(str(line))
    return out


def guard(preamble: str, fixture: dict) -> tuple[bool, list[str]]:
    missing = [line for line in required_constraint_lines(fixture) if line not in (preamble or "")]
    return (len(missing) == 0, missing)


__all__ = ["required_constraint_lines", "guard"]
