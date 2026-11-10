#!/usr/bin/env python3
"""Deterministic generator for cs.task/1 instances (D1-D4 discovery, H1-H4 heldout).

V2: two distinct families per split; held-out families structurally different
from discovery. Each turn carries `requires_turns` (source turns its answer
depends on) and `expect_exact_body` (whether only an exact body resolves it).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTANCES = HERE / "instances"
TURNS = 12


def _turn(n, event, question, contract, expect, requires_turns=None, expect_exact_body=False):
    return {
        "n": n,
        "event": event,
        "question": question,
        "answer_contract": list(contract),
        "expect": dict(expect),
        "requires_turns": list(requires_turns) if requires_turns is not None else [n],
        "expect_exact_body": bool(expect_exact_body),
    }


def _instance(task_id, split, seed, family, turns):
    return {
        "schema": "cs.task/1",
        "task_id": task_id,
        "split": split,
        "seed": seed,
        "family": family,
        "fixture": {"turns": TURNS, "values": [t["event"] for t in turns]},
        "turns": turns,
        "grader": "cs.grade/1",
    }


# ---------- Discovery family (i): running numeric aggregate ----------

def gen_d1(seed):
    """Cumulative sum of signed integers."""
    rng = random.Random(seed)
    vals = [rng.randint(-9, 9) for _ in range(TURNS)]
    turns = []
    total = 0
    for i, v in enumerate(vals, 1):
        total += v
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "value": v, "unit": "points"},
            f"Observation {i}: value={v}. What is the cumulative total of all observed values so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"total={total}"],
            {"total": total},
            requires_turns=list(range(1, i + 1)),
            expect_exact_body=False,
        ))
    return turns


def gen_d2(seed):
    """Running range (max-min) of observed integers."""
    rng = random.Random(seed)
    vals = [rng.randint(-20, 20) for _ in range(TURNS)]
    turns = []
    for i, v in enumerate(vals, 1):
        sub = vals[:i]
        rng_range = max(sub) - min(sub)
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "temperature": v},
            f"Observation {i}: temperature={v}. What is the current range (max minus min) and the number of observations so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"range={rng_range}", f"count={i}"],
            {"range": rng_range, "count": i},
            requires_turns=list(range(1, i + 1)),
            expect_exact_body=False,
        ))
    return turns


# ---------- Discovery family (ii): file-state recall ----------

def _gen_file_state(seed, value_kind):
    rng = random.Random(seed)
    keys = ["title", "owner", "status"]
    tokens = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    state = {k: None for k in keys}
    last_set = {k: None for k in keys}
    edits = []
    for i in range(TURNS):
        key = keys[i % len(keys)]
        if value_kind == "str":
            newval = f"{rng.choice(tokens)}-{i + 1}"
        else:
            newval = rng.randint(0, 99)
        edits.append((key, newval))

    turns = []
    for i, (key, newval) in enumerate(edits, 1):
        old = state[key]
        old_str = "UNSET" if old is None else str(old)
        rt = [last_set[key]] if last_set[key] is not None else [i]
        event = {"type": "edit", "seq": i, "key": key, "new": newval, "version": i}
        still_needs_body = (i > 1) and (old_str not in json.dumps(event))
        turns.append(_turn(
            i,
            event,
            f"Edit {i}: set {key}={newval}. What value did key '{key}' hold before this edit? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"previous={old_str}"],
            {"previous": old_str},
            requires_turns=rt,
            expect_exact_body=still_needs_body,
        ))
        state[key] = newval
        last_set[key] = i
    return turns


def gen_d3(seed):
    return _gen_file_state(seed, "str")


def gen_d4(seed):
    return _gen_file_state(seed, "int")


# ---------- Held-out family (iii): multi-step edit application ----------

def gen_h1(seed):
    """Apply append/replace/delete to a token list; report final joined sequence."""
    rng = random.Random(seed)
    tokens_pool = ["red", "green", "blue", "amber", "violet", "cyan"]
    ops = []
    seq = []
    for _ in range(TURNS):
        r = rng.random()
        if r < 0.45 or not seq:
            tok = rng.choice(tokens_pool)
            ops.append(("append", tok))
            seq.append(tok)
        elif r < 0.75:
            pos = rng.randrange(len(seq))
            tok = rng.choice(tokens_pool)
            ops.append(("replace", pos, tok))
            seq[pos] = tok
        else:
            pos = rng.randrange(len(seq))
            ops.append(("delete", pos))
            del seq[pos]

    seq = []
    turns = []
    for i, op in enumerate(ops, 1):
        if op[0] == "append":
            seq.append(op[1])
            event = {"type": "edit", "seq": i, "op": "append", "value": op[1]}
            desc = f"append {op[1]}"
        elif op[0] == "replace":
            seq[op[1]] = op[2]
            event = {"type": "edit", "seq": i, "op": "replace", "pos": op[1], "value": op[2]}
            desc = f"replace position {op[1]} with {op[2]}"
        else:
            del seq[op[1]]
            event = {"type": "edit", "seq": i, "op": "delete", "pos": op[1]}
            desc = f"delete position {op[1]}"
        joined = " ".join(seq) if seq else "EMPTY"
        still_needs_body = (i > 1) and (joined not in json.dumps(event))
        turns.append(_turn(
            i,
            event,
            f"Edit {i}: {desc}. What is the final joined sequence after all edits so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"sequence={joined}"],
            {"sequence": joined},
            requires_turns=list(range(1, i + 1)),
            expect_exact_body=still_needs_body,
        ))
    return turns


def gen_h2(seed):
    """Apply edits to a text buffer; report final buffer."""
    rng = random.Random(seed)
    ops = []
    buf = ""
    plan = ["append", "append", "insert", "append", "delete", "insert",
            "append", "delete", "append", "insert", "append", "delete"]
    for kind in plan:
        if kind == "append" or not buf:
            ch = rng.choice("abcde")
            ops.append(("append", ch))
            buf += ch
        elif kind == "insert":
            pos = rng.randrange(len(buf))
            ch = rng.choice("xyz")
            ops.append(("insert", pos, ch))
            buf = buf[:pos] + ch + buf[pos:]
        else:
            pos = rng.randrange(len(buf))
            ops.append(("delete", pos))
            buf = buf[:pos] + buf[pos + 1:]

    buf = ""
    turns = []
    for i, op in enumerate(ops, 1):
        if op[0] == "append":
            buf = buf + op[1]
            event = {"type": "edit", "seq": i, "op": "append", "value": op[1]}
            desc = f"append {op[1]}"
        elif op[0] == "insert":
            buf = buf[:op[1]] + op[2] + buf[op[1]:]
            event = {"type": "edit", "seq": i, "op": "insert", "pos": op[1], "value": op[2]}
            desc = f"insert {op[2]} at position {op[1]}"
        else:
            buf = buf[:op[1]] + buf[op[1] + 1:]
            event = {"type": "edit", "seq": i, "op": "delete", "pos": op[1]}
            desc = f"delete position {op[1]}"
        final = buf if buf else "EMPTY"
        still_needs_body = (i > 1) and (final not in json.dumps(event))
        turns.append(_turn(
            i,
            event,
            f"Edit {i}: {desc}. What is the final text buffer after all edits so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"buffer={final}"],
            {"buffer": final},
            requires_turns=list(range(1, i + 1)),
            expect_exact_body=still_needs_body,
        ))
    return turns


# ---------- Held-out family (iv): constraint / precedence resolution ----------

def gen_h3(seed):
    """Base defaults + overrides; precedence evidence in early turns only."""
    rng = random.Random(seed)
    base = {"mode": "standard", "level": "2", "format": "text"}
    turns = []
    turns.append(_turn(
        1,
        {"type": "constraint", "seq": 1, "kind": "default", "base": dict(base)},
        f"Constraint setup: base defaults are mode={base['mode']}, level={base['level']}, format={base['format']}. "
        "What is the default value of 'mode'? Reply with exactly one line per contracted key, no extra text.",
        [f"resolved={base['mode']}"],
        {"resolved": base["mode"]},
        requires_turns=[1],
        expect_exact_body=False,
    ))
    turns.append(_turn(
        2,
        {"type": "constraint", "seq": 2, "kind": "precedence", "rule": "base_wins"},
        "Constraint setup: precedence rule is 'base_wins' (a base default beats an explicit override). "
        "What precedence rule is in effect? Reply with exactly one line per contracted key, no extra text.",
        ["rule=base_wins"],
        {"rule": "base_wins"},
        requires_turns=[2],
        expect_exact_body=False,
    ))
    base_src = {k: 1 for k in base}
    for i in range(3, 7):
        key = rng.choice(list(base.keys()))
        val = rng.choice(["safe", "fast", "3", "json", "xml", "1"])
        base[key] = val
        base_src[key] = i
        turns.append(_turn(
            i,
            {"type": "constraint", "seq": i, "kind": "default_update", "key": key, "value": val},
            f"Constraint setup: base default for '{key}' updated to '{val}'. What is the current base default for '{key}'? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"base={val}"],
            {"base": val},
            requires_turns=[i],
            expect_exact_body=False,
        ))
    for j in range(7, 13):
        key = rng.choice(list(base.keys()))
        override = rng.choice(["OVERRIDE_A", "OVERRIDE_B", "9", "yaml"])
        resolved = base[key]
        turns.append(_turn(
            j,
            {"type": "request", "seq": j, "key": key, "override": override},
            f"Request {j}: override '{key}' with '{override}'. Given the precedence rule, what is the resolved value of '{key}'? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"resolved={resolved}"],
            {"resolved": resolved},
            requires_turns=[2, base_src[key]],
            expect_exact_body=False,
        ))
    assert len(turns) == TURNS, len(turns)
    return turns


def gen_h4(seed):
    """Multiple early constraints with increasing priority; later requests resolved."""
    rng = random.Random(seed)
    keys = ["mode", "level"]
    constraints = []
    turns = []
    base_vals = {"mode": "standard", "level": "1"}
    turns.append(_turn(
        1,
        {"type": "constraint", "seq": 1, "kind": "base", "values": dict(base_vals),
         "precedence": "early_constraints_outrank_late_overrides"},
        "Constraint setup: base values mode=standard, level=1. Precedence rule: early constraints outrank late overrides. "
        "What is the base value of 'mode'? "
        "Reply with exactly one line per contracted key, no extra text.",
        ["resolved=standard"],
        {"resolved": "standard"},
        requires_turns=[1],
        expect_exact_body=False,
    ))
    priority = 1
    for i in range(2, 7):
        key = rng.choice(keys)
        val = rng.choice(["safe", "fast", "high", "low"])
        priority += 1
        constraints.append((i, key, val, priority))
        turns.append(_turn(
            i,
            {"type": "constraint", "seq": i, "kind": "rule", "key": key, "value": val, "priority": priority},
            f"Constraint {i}: (priority {priority}) set {key}={val}. What value did this constraint assign to '{key}'? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"assigned={val}"],
            {"assigned": val},
            requires_turns=[i],
            expect_exact_body=False,
        ))
    for j in range(7, 13):
        key = rng.choice(keys)
        applicable = [c for c in constraints if c[1] == key]
        if applicable:
            chosen = max(applicable, key=lambda c: c[3])
            resolved = chosen[2]
            src_turns = [1] + [c[0] for c in applicable]
        else:
            resolved = base_vals.get(key, "UNSET")
            src_turns = [1]
        override = rng.choice(["overrideX", "overrideY"])
        turns.append(_turn(
            j,
            {"type": "request", "seq": j, "key": key, "override": override},
            f"Request {j}: late override {key}={override}. Given early constraints, what is the resolved value of '{key}'? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"resolved={resolved}"],
            {"resolved": resolved},
            requires_turns=src_turns,
            expect_exact_body=False,
        ))
    assert len(turns) == TURNS, len(turns)
    return turns


GENERATORS = {
    "D1": (gen_d1, "discovery", 2026110521, "running_numeric_aggregate"),
    "D2": (gen_d2, "discovery", 2026110522, "running_numeric_aggregate"),
    "D3": (gen_d3, "discovery", 2026110523, "file_state_recall"),
    "D4": (gen_d4, "discovery", 2026110524, "file_state_recall"),
    "H1": (gen_h1, "heldout", 2026110525, "multi_step_edit_application"),
    "H2": (gen_h2, "heldout", 2026110526, "multi_step_edit_application"),
    "H3": (gen_h3, "heldout", 2026110527, "constraint_precedence_resolution"),
    "H4": (gen_h4, "heldout", 2026110528, "constraint_precedence_resolution"),
}


def generate_all():
    out = {}
    for tid, (fn, split, seed, family) in GENERATORS.items():
        turns = fn(seed)
        assert len(turns) == TURNS, (tid, len(turns))
        for t in turns:
            assert isinstance(t["requires_turns"], list) and t["requires_turns"]
            for rt in t["requires_turns"]:
                assert isinstance(rt, int) and 1 <= rt <= TURNS
        out[tid] = _instance(tid, split, seed, family, turns)
    return out


def main():
    INSTANCES.mkdir(parents=True, exist_ok=True)
    for tid, inst in generate_all().items():
        path = INSTANCES / f"{tid}.json"
        path.write_text(json.dumps(inst, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
