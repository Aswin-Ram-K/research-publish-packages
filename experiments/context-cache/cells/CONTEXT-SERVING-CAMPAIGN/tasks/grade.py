#!/usr/bin/env python3
"""Grader implementing cs.grade/1 for cs.task/1 instances."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

KEY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
LENGTH_REASONS = {"length", "max_tokens", "max_output_tokens"}


def parse_answer(text: Any) -> Optional[Dict[str, str]]:
    """Parse key=value lines from a model answer. Returns None if none found."""
    if text is None:
        return None
    pairs: Dict[str, str] = {}
    found = False
    for raw in str(text).splitlines():
        line = raw.strip()
        # strip markdown/backtick wrappers so a fenced `key=value` still parses
        line = line.strip("`").strip()
        # keep only the final key=value-shaped line's content is handled by KEY_RE below
        m = KEY_RE.match(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        pairs[k] = v
        found = True
    return pairs if found else None


def classify_turn(output: Any, finish_reason: Any = None) -> Dict[str, bool]:
    text = "" if output is None else str(output)
    return {
        "silent": text.strip() == "",
        "length_exhausted": str(finish_reason).lower() in LENGTH_REASONS,
    }


def _turn_from(instance_or_turn: Any, turn_number: Optional[int] = None) -> Optional[dict]:
    if isinstance(instance_or_turn, dict) and "answer_contract" in instance_or_turn and "n" in instance_or_turn:
        return instance_or_turn
    if isinstance(instance_or_turn, dict) and "turns" in instance_or_turn:
        tn = turn_number
        if tn is None:
            return None
        for t in instance_or_turn["turns"]:
            if t.get("n") == tn:
                return t
    return None


def _contract_keys(turn: dict) -> List[str]:
    keys = []
    for line in turn.get("answer_contract", []):
        if "=" in str(line):
            keys.append(str(line).split("=", 1)[0].strip())
    return keys


def _expected_map(turn: dict) -> Dict[str, str]:
    ex = turn.get("expect", {})
    out = {}
    for k, v in (ex or {}).items():
        out[str(k)] = str(v).strip()
    # fall back to answer_contract
    if not out:
        for line in turn.get("answer_contract", []):
            if "=" in str(line):
                k, v = str(line).split("=", 1)
                out[k.strip()] = v.strip()
    return out


def grade_turn(turn: dict, output: Any = None, finish_reason: Any = None) -> Dict[str, Any]:
    contract_keys = _contract_keys(turn)
    expected = _expected_map(turn)
    parsed = parse_answer(output)
    cls = classify_turn(output, finish_reason)
    silent = cls["silent"]
    length_exhausted = cls["length_exhausted"]

    checks: List[Dict[str, Any]] = []
    missing: List[str] = []
    extra: List[str] = []
    mismatched: List[str] = []

    if parsed is None:
        # unparseable
        if length_exhausted:
            ok = None
        else:
            ok = False
        # still emit per-key checks as failed
        for key in contract_keys:
            checks.append({"id": f"key:{key}", "key": key, "ok": False,
                           "expected": expected.get(key), "got": None})
        checks.append({"id": "no_extra_keys", "ok": True, "extra": []})
        checks.append({"id": "parseable", "ok": False})
        return {
            "ok": ok,
            "checks": checks,
            "finish_reason": finish_reason,
            "silent": silent,
            "length_exhausted": length_exhausted,
            "parsed": None,
            "missing": list(contract_keys),
            "extra": [],
            "mismatched": [],
        }

    # presence
    for key in contract_keys:
        if key not in parsed:
            missing.append(key)
    for key in parsed:
        if key not in contract_keys:
            extra.append(key)

    for key in contract_keys:
        got = parsed.get(key)
        exp = expected.get(key)
        key_ok = key in parsed and (got == exp)
        if key in parsed and got != exp:
            mismatched.append(key)
        checks.append({"id": f"key:{key}", "key": key, "ok": bool(key_ok),
                       "expected": exp, "got": got})

    no_extra_ok = (len(extra) == 0)
    checks.append({"id": "no_extra_keys", "ok": bool(no_extra_ok), "extra": extra})
    checks.append({"id": "parseable", "ok": True})

    ok = (len(missing) == 0 and len(extra) == 0 and len(mismatched) == 0)
    return {
        "ok": bool(ok),
        "checks": checks,
        "finish_reason": finish_reason,
        "silent": silent,
        "length_exhausted": length_exhausted,
        "parsed": parsed,
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
    }


def grade(*args, **kwargs) -> Dict[str, Any]:
    """Flexible entry point.

    Accepted forms:
      grade(output, turn, finish_reason=None)
      grade(turn, output, finish_reason=None)
      grade(output, instance, turn_number, finish_reason=None)
      grade(output=..., turn=..., finish_reason=...)
      grade(output=..., instance=..., turn_number=..., finish_reason=...)
    """
    output = kwargs.get("output", kwargs.get("answer", kwargs.get("text")))
    turn = kwargs.get("turn")
    instance = kwargs.get("instance")
    turn_number = kwargs.get("turn_number", kwargs.get("n"))
    finish_reason = kwargs.get("finish_reason")
    answer_contract = kwargs.get("answer_contract")
    expect = kwargs.get("expect")

    positional = list(args)
    # resolve instance/turn/output from positionals
    for a in positional:
        if isinstance(a, str):
            if output is None:
                output = a
            elif finish_reason is None and a in ("stop", "length", "max_tokens"):
                # ambiguous; only set if not already
                pass
        elif isinstance(a, dict):
            if "answer_contract" in a and "n" in a:
                if turn is None:
                    turn = a
            elif "turns" in a and "task_id" in a:
                if instance is None:
                    instance = a
        elif isinstance(a, int):
            if turn_number is None:
                turn_number = a

    # If a finish_reason string was passed positionally after output/turn
    # handle: collect remaining strings
    strs = [a for a in positional if isinstance(a, str)]
    if len(strs) >= 2 and finish_reason is None:
        # second string might be finish_reason
        if strs[1].lower() in LENGTH_REASONS or strs[1].lower() in ("stop", "error", "content_filter"):
            finish_reason = strs[1]

    if turn is None and instance is not None and turn_number is not None:
        turn = _turn_from(instance, turn_number)
    if turn is None and answer_contract is not None:
        turn = {"answer_contract": answer_contract, "expect": expect or {}}

    if turn is None:
        # build a synthetic turn from provided contract/expect
        turn = {"answer_contract": answer_contract or [], "expect": expect or {}}

    if answer_contract is not None and "answer_contract" not in turn:
        turn["answer_contract"] = answer_contract
    if expect is not None and "expect" not in turn:
        turn["expect"] = expect

    return grade_turn(turn, output, finish_reason)


# aliases
grade_answer = grade
grade_instance_turn = grade
grade_cell = grade


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True)
    ap.add_argument("--turn", type=int, required=True)
    ap.add_argument("--answer", help="path to answer text file")
    ap.add_argument("--answer-text", dest="answer_text")
    ap.add_argument("--finish-reason", dest="finish_reason", default="stop")
    args = ap.parse_args()

    inst = json.loads(Path(args.instance).read_text(encoding="utf-8"))
    turn = _turn_from(inst, args.turn)
    if args.answer:
        text = Path(args.answer).read_text(encoding="utf-8")
    else:
        text = args.answer_text or ""
    res = grade_turn(turn, text, args.finish_reason)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
