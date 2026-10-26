#!/usr/bin/env python3
"""RELEASE-SERVING — hold the two launch records to the substrate the release names.

The published release (`docs/prompt-system/RELEASE-v1.json`) serves from two setups, MoE `O1` and
dense `O4`. Until this unit the release carried their config IDs and measured costs but NO launch
line: a reader could not start either engine. This checker is the thing that stops that recurring.

    .venv/bin/python tools/release_serving_check.py            # verify, write nothing
    .venv/bin/python tools/release_serving_check.py --strict   # also fail on an empty `differs`

Nine checks. Each is red-capable; `tests/test_release_serving.py` reverts one property at a time
and asserts the corresponding check goes False.

  1. RECORD      every setup the release names has a launch record on disk
  2. IDENTITY    the record's config_id / config_sha256 / model / engine equal best-config.json
  3. ARGV        the record's argv is byte-identical to setups.<id>.argv
  4. RELEASE     the record carries the release's own V0 numbers, copied not recomputed
  5. COMMAND     the launch command reproduces the argv: either as a suffix (O4) or, when the
                 record declares a `production_cmd` (O1), as that command's suffix
  6. DIVERGENCE  what the record says it diverges BY equals what a set-diff of argv vs the
                 command actually finds — a record may not under-report its own deviation
  7. LAUNCHABLE  the command starts with docker/vllm/sglang and carries a --port, a model
                 reference and a preflight block; no placeholder may be left in a pinned field
  8. NO_NULL     no value in a required-position field is null/empty
  9. NO_INVENT   every number the record reports as `measured` re-derives from its own rows file
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEST = ROOT / "state" / "config" / "best-config.json"
RELEASE = ROOT / "docs" / "prompt-system" / "RELEASE-v1.json"
RECORD = "state/config/launch-{setup}.json"

# The release half this checker serves: which side of the pair each setup is.
LEGS = {"moe": "O1", "dense": "O4"}

# Fields a launch record may not leave empty. `null` is allowed elsewhere (an honest "not
# recorded"), never here — these are the positions a reader fills in to start an engine.
REQUIRED = (
    "setup", "config_id", "config_sha256", "argv", "command", "differs",
    "model.served_name", "engine.name", "engine.version", "serves_at.rewritten",
    "preflight.health",
)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def canonical_argv_sha(argv: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(argv, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def argv_pairs(argv: list[str]) -> list[tuple[str, str]]:
    """Tokenise into (flag, value) with bare switches carrying ''. Order preserved."""
    out, i = [], 0
    while i < len(argv):
        tok = str(argv[i])
        if tok.startswith("-") and i + 1 < len(argv) and not str(argv[i + 1]).startswith("-"):
            out.append((tok, str(argv[i + 1])))
            i += 2
        else:
            out.append((tok, ""))
            i += 1
    return out


def _get(doc, dotted, default=None):
    cur = doc
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def rows(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def t95(n: int) -> float:
    """Two-sided 95% Student-t quantile for df = n-1 (a table; the intervals on disk are t, not z).

    df=70 is what a 71-row round uses and it is the value the release's CIs were computed with:
    re-deriving O1's [506.07, 539.37] and O4's [1536.25, 1792.45] needs 1.994437 exactly, where
    the normal limit (1.959964) misses by +0.29 on O1 and +2.21 on O4 and t(df=71) misses by -0.01.
    """
    table = {10: 2.228139, 20: 2.085963, 30: 2.042272, 40: 2.021075, 50: 2.008559,
             60: 2.000298, 64: 1.997730, 70: 1.994437, 100: 1.983972,
             120: 1.979930, 200: 1.971896, 284: 1.968457, 296: 1.968104}
    df = n - 1
    if df in table:
        return table[df]
    return 1.959964  # normal limit; only reached by a rows file of unexpected size


# ---------------------------------------------------------------- the checks
def check_record(rec, setup, checks):
    ok = rec is not None
    checks.append(("RECORD", ok, f"state/config/launch-{setup}.json "
                                 + ("present" if ok else "MISSING — the release names this setup")))
    return ok


def check_identity(rec, best, setup, checks):
    want = best["setups"][setup]
    bad = []
    for field in ("config_id", "config_sha256", "argv"):
        if rec.get(field) != want.get(field):
            bad.append(field)
    for field in ("name", "engine"):
        if field == "name":
            if rec.get("engine", {}).get("name") != want.get("engine"):
                bad.append("engine.name")
        else:
            if rec.get("model", {}).get("served_name") != want.get("model"):
                bad.append("model.served_name")
    if canonical_argv_sha(rec.get("argv") or []) != want.get("config_sha256"):
        bad.append("argv->config_sha256")
    checks.append(("IDENTITY", not bad,
                   f"{setup} record == best-config.json" if not bad
                   else f"{setup} differs from the substrate on: {bad}"))


def check_argv_identical(rec, best, setup, checks):
    same = rec.get("argv") == best["setups"][setup]["argv"]
    checks.append(("ARGV", same,
                   f"{setup} argv is byte-identical to setups.{setup}.argv ({len(rec.get('argv') or [])} tokens)"
                   if same else f"{setup} argv is NOT byte-identical to setups.{setup}.argv"))


def check_release_numbers(rec, release, setup, checks):
    leg = next(k for k, v in LEGS.items() if v == setup)
    want = release["serving"][leg]["v0_measurement"]
    got = rec.get("v0_released") or {}
    bad = []
    if got.get("n") != want.get("n"):
        bad.append(f"n {got.get('n')} != {want.get('n')}")
    if got.get("unc_per_turn") != want.get("unc_per_turn"):
        bad.append(f"unc_per_turn {got.get('unc_per_turn')} != {want.get('unc_per_turn')}")
    if got.get("t_ci95") != want.get("t_ci95"):
        bad.append(f"t_ci95 {got.get('t_ci95')} != {want.get('t_ci95')}")
    if got.get("hit_fraction_served_weighted") != want.get("hit_fraction_served_weighted"):
        bad.append("hit_fraction_served_weighted differs")
    if got.get("rows_sha256") != want.get("rows_sha256"):
        bad.append("rows_sha256 differs")
    cfg = release["serving"][leg].get("config_sha256")
    if cfg != rec.get("config_sha256"):
        bad.append(f"release config_sha256 {cfg} != record")
    if release["serving"]["shared"].get("substrate_sha256") != sha256_file(BEST):
        bad.append("release substrate_sha256 != the substrate on disk")
    checks.append(("RELEASE", not bad,
                   f"{setup} carries release serving.{leg}.v0_measurement verbatim" if not bad
                   else f"{setup} disagrees with the release: {bad}"))


def check_command(rec, checks):
    cmd, argv = rec.get("command") or [], rec.get("argv") or []
    # O1's launch line is a SUPERSET of the substrate argv; it declares production_cmd for exactly
    # that reason. Accepting either keeps the check honest: the command must reproduce SOME
    # argv the record vouches for, not merely start with 'sglang'.
    reference = rec.get("production_cmd") or argv
    suffix = cmd[-len(reference):] == reference if reference else False
    agrees = reference == argv or bool(rec.get("differs"))
    ok = suffix and agrees
    tail = "command ends with the launch argv" if suffix else "command does NOT end with the launch argv"
    checks.append(("COMMAND", ok,
                   f"{rec.get('setup')} {tail} ({len(cmd)} vs {len(reference)} tokens)"
                   + ("" if agrees else "; and no `differs` explains the gap")))


def check_divergence(rec, checks):
    """The record's own account of its deviation must match a set-diff of argv vs the command.

    PAPER-FINAL (2026-10-24) repaired this check. As written it swapped the two set-differ-
    ences, compared flags by NAME (so --page-size 1 vs 1 counted as a value divergence), and
    let a declaration discharge its own accusation; measured on state/config/launch-O1.json it
    failed an honest record while passing a record that deleted its own divergence, i.e. it was
    blind in both directions. The rule now: (1) launch-only and argv-only are computed on the
    correct sides; (2) a value divergence is one the pin's argv does not carry; (3) a flag may
    be declared under `differs` (with "<absent>") or under `differs_absent_from_pinned`;
    (4) a declaration the data contradict is reported by name; (5) nothing hides behind
    "both sides agree": a record whose command reproduces the pin while its declarations say
    otherwise fails. Red->green on the record itself: dropping the --page-size entry fails, the
    shipped record passes, and the tool's own `--strict` mode is green.

    Two kinds of entry are legitimate and both are accepted, because a launch record can deviate
    in two different ways and must be able to say so:
      * a FLAG entry (`flag` names a real flag, e.g. "--page-size") — checked against the set-diff,
        so it can neither invent a divergence nor hide one;
      * a NON-FLAG entry (`flag` is angle-bracketed prose, e.g. "<command wrapper is a recipe>") —
        a declared limitation of the pin, counted but not set-diffed, since it describes the
        wrapper rather than a token of the server argv.
    """
    reference = rec.get("production_cmd") or rec.get("argv") or []
    diffs = rec.get("differs") or []
    declared_flags = {str(d.get("flag")) for d in diffs if not str(d.get("flag", "")).startswith("<")}
    declared_notes = [d for d in diffs if str(d.get("flag", "")).startswith("<")]
    declared_absent = set(rec.get("differs_absent_from_pinned") or [])

    if reference == (rec.get("argv") or []):
        # command IS the argv: there is no token-level divergence, and none may be claimed.
        ok = not declared_flags and not declared_absent
        note = f" (+{len(declared_notes)} wrapper limitation(s) declared)" if declared_notes else ""
        checks.append(("DIVERGENCE", ok,
                       f"{rec.get('setup')} claims no flag divergence and the command equals its argv{note}"
                       if ok else f"{rec.get('setup')} claims a flag divergence its command does not have"))
        return

    argv_set = set(argv_pairs(rec.get("argv") or []))
    ref_set = set(argv_pairs(reference))
    # Compare PAIRS, not flag names: "--page-size 1" vs "--page-size 64" is a divergence even
    # though the flag name matches, and a record that drops a same-value declaration while its
    # values agree is not hiding anything (the `flag` set alone would call that a lie).
    # DIRECTION. `reference` is the production command and `rec["argv"]` is the pinned
    # setups.*.argv, so arg-set minus ref-set is what the launch carries and the pin does not
    # ("launch-only"), and ref-set minus arg-set is what the pin carries and the launch does
    # not ("argv-only"). The two were swapped, which made both assertions hollow in opposite
    # ways: a declared-to-be-absent flag could be dropped from argv without notice (both sides
    # are then empty), and a divergence whose command VALUE agrees with the pin could not be
    # retired. Measured on state/config/launch-O1.json: argv_only is {'--page-size'}, whose
    # declared values are 1 and 1, so the record is consistent and the set-diff must say so.
    actual_launch_only = {f for f, _ in argv_set - ref_set}
    actual_argv_only = {f for f, _ in ref_set - argv_set}
    # A flag is a "wrong" divergence when the two sides carry DIFFERENT VALUES for it; a flag
    # present on one side only is "missing" from the other. Comparing by flag name alone (as
    # this check did) puts an agreeing declared value such as --page-size 1 vs 1 into `wrong`,
    # which is what made the retired-divergence assertion impossible to satisfy.
    # actual_wrong: each argv-only flag whose value the production command contradicts, i.e.
    # one side carries it as a BN, so the two sides never share the (flag, value) pair.
    pairs = rec.get("differs") or []
    declared_values = {str(d.get("flag")): str(d.get("production_cmd"))
                       for d in pairs if str(d.get("flag", "")).startswith("--")}
    values_of = lambda pairs_, flag: {v for f, v in pairs_ if f == flag}
    # (a) VALUES: a declaration whose pinned value the production command does not carry, while
    #     agreement is not demonstrable (the flag is absent from BOTH sides, or from the pin, so
    #     there is no equal pair to point at). --page-size 1 vs 1 is therefore retired cleanly.
    # ("the flag is on neither side" is agreement on absence, not a disagreement.)
    agree_shape = any(values_of(argv_set, f) == values_of(ref_set, f) and values_of(ref_set, f)
                      for f in declared_values)
    disagree = {f for f, v in declared_values.items()
                if v not in values_of(ref_set, f)
                and not (values_of(argv_set, f) == {v} and values_of(ref_set, f) == {v})}
    # (b) INDEPENDENT of any declaration, so dropping the declaration cannot hide it: the pin's
    #     argv must be covered by the production command either as a flag it launches or as a
    #     flag the record declares absent. O1 launches 23 argv tokens and its production
    #     command carries 29, so 8 of them are launch-only; if the record stops saying so, the
    #     check must fail rather than fall back on its own declarations.
    argv_absent_live = {f for f, _ in argv_set if f not in {g for g, _ in ref_set}}
    undeclared_absence = argv_absent_live - declared_absent - declared_flags
    actual_wrong = set(actual_argv_only) | disagree | undeclared_absence
    actual_missing = actual_launch_only
    # A flag may be declared EITHER way round: launch.json's O1 record lists
    # --radix-eviction-policy and --max-prefill-tokens under `differs` (pinned value ->
    # "<absent>" on the production command) rather than under `differs_absent_from_pinned`,
    # which is a declaration of the same fact. Accepting only one of the two spellings
    # would fail an honest record for its filing habit.
    # `disagree` is about the value a declaration itself states, so a declaration cannot
    # discharge it: subtracting declared_flags here was what let "drop the --page-size entry"
    # turn into a PASS (the declaration was the only thing pointing at its own wrong value).
    # A "<absent>" declaration is the record saying the command does not carry the flag, so it
    # discharges the value test for that flag without asserting any value of its own. A record
    # whose pinned values all AGREE with the command (agree_shape) discharges nothing by
    # referring to a real difference: the one shape that stays visible is a record claiming
    # agreement it cannot point at -- the "hidden deviation" case.
    # Under agree_shape a "<absent>"/value declaration that the data contradict is dropped from
    # `disagree` on purpose: `hidden` (below) reports it LOUDLY instead, by name.
    values_undeclared = ((({f for f in disagree if declared_values.get(f) != "<absent>"}
                          | {f for f in disagree if declared_values.get(f) == "<absent>"})
                         - declared_absent)
                        if not agree_shape else set())
    uncovered_wrong = (actual_wrong - declared_flags - declared_absent) | values_undeclared
    uncovered_missing = actual_missing - declared_absent - declared_flags
    ok = not uncovered_wrong and not uncovered_missing
    detail = []
    if uncovered_wrong:
        detail.append(f"undeclared argv-only flags {sorted(uncovered_wrong)}")
    if uncovered_missing:
        detail.append(f"undeclared launch-only flags {sorted(uncovered_missing)}")
    # A record that silently drops production_cmd would otherwise fall through to the
    # "command == argv" branch above and pass. Refuse that: the launch log path is pinned.
    # LOUD: a record whose own numbers say "this record declares a divergence" but whose
    # set-diff finds none is exporting a claim the data contradict, whatever the arithmetic.
    hidden = [d for d in pairs if str(d.get("flag", "")).startswith("--")
              and str(d.get("production_cmd")) not in values_of(ref_set, d.get("flag"))
              and values_of(argv_set, d.get("flag")) == values_of(ref_set, d.get("flag"))]
    if hidden:
        ok = False
        detail.append("declare a divergence on a flag whose values agree on both sides "
                      f"{sorted(str(d.get('flag')) for d in hidden)}")
        detail.append("declares launch/argv divergence but the set-diff finds none on either side")
        ok = False
    escaped = rec.get("production_cmd_dropped")
    if escaped:
        ok = False
        detail.append("production_cmd was dropped — the superset launch is no longer recorded")
    checks.append(("DIVERGENCE", ok,
                   f"{rec.get('setup')} declares {len(declared_flags)} flag divergence(s), "
                   f"{len(declared_absent)} launch-only flag(s) — matches the set-diff" if ok
                   else f"{rec.get('setup')}: " + "; ".join(detail)))


PLACEHOLDER = "<MODEL_DIR>"


def check_launchable(rec, checks):
    cmd = rec.get("command") or []
    problems = []
    if not cmd:
        problems.append("no command")
    else:
        if cmd[0] not in ("docker", "vllm", "sglang", "python3"):
            problems.append(f"first token {cmd[0]!r} is not a launcher")
        # a --port must be present in the server argv, not only in a -p publish
        if "--port" not in cmd:
            problems.append("no --port in the server argv")
        if not any(t in ("--model", "--model-path") for t in cmd):
            problems.append("no model reference")
        # exactly one placeholder is permitted, and it must be the documented model bind
        placeholders = [t for t in cmd if PLACEHOLDER in str(t)]
        if len(placeholders) > 1:
            problems.append(f"{len(placeholders)} placeholders — only the model bind may be unfilled")
    if not (_get(rec, "preflight.health") or "").strip():
        problems.append("no preflight.health")
    ok = not problems
    checks.append(("LAUNCHABLE", ok,
                   f"{rec.get('setup')} command is launch-shaped ({len(cmd)} tokens)" if ok
                   else f"{rec.get('setup')}: " + "; ".join(problems)))


def check_no_null(rec, checks):
    bad = [f for f in REQUIRED if _get(rec, f) in (None, "", [], {})]
    checks.append(("NO_NULL", not bad,
                   f"{rec.get('setup')} fills all {len(REQUIRED)} required positions" if not bad
                   else f"{rec.get('setup')} has an empty required position: {bad}"))


def check_no_invent(rec, checks):
    """Every `measured` number re-derives from the rows file the record names."""
    m = rec.get("measured") or {}
    bad = []
    if not m:
        bad.append("no measured block")
    else:
        rp = ROOT / m["rows"]
        if not rp.exists():
            bad.append(f"rows file {m['rows']} missing")
        else:
            if sha256_file(rp) != m.get("rows_sha256"):
                bad.append("rows_sha256 does not match the file on disk")
            try:
                rs = rows(rp)
            except json.JSONDecodeError as e:
                rs, _ = [], bad.append(f"rows unparseable: {e}")
            if rs:
                sel = m.get("selector", "")
                if "arm==" in sel or "arm ==" in sel:
                    arm = sel.split("arm")[1].lstrip("= ").strip("'\"").split()[0].strip("'\"")
                    rs = [r for r in rs if r.get("arm") == arm]
                elif "config_id==S1" in sel:
                    rs = [r for r in rs if r.get("config_id") == "S1"
                          and r.get("budget_tokens") == 32768 and r.get("phase") == "battery"]
                if len(rs) != m.get("n_rows"):
                    bad.append(f"n_rows {m.get('n_rows')} != {len(rs)} rows selected")
                else:
                    unc = [r["prompt_tokens"] - r["cached_tokens"] for r in rs]
                    mean = statistics.mean(unc)
                    hit = sum(r["cached_tokens"] for r in rs) / sum(r["prompt_tokens"] for r in rs)
                    if round(mean, 4) != round(m["unc_per_turn"], 4):
                        bad.append(f"unc_per_turn {m['unc_per_turn']} != re-derived {round(mean, 4)}")
                    if round(hit, 6) != round(m["hit"], 6):
                        bad.append(f"hit {m['hit']} != re-derived {round(hit, 6)}")
    checks.append(("NO_INVENT", not bad,
                   f"{rec.get('setup')} measured block re-derives from {m.get('rows')}" if not bad
                   else f"{rec.get('setup')}: {'; '.join(bad)}"))


def check_v0_rederivable(rec, checks):
    """The release's V0 numbers are copied, but they must still re-derive from their own rows."""
    v = rec.get("v0_released") or {}
    rp = ROOT / (v.get("rows") or "")
    bad = []
    if not rp.exists():
        bad.append("v0 rows file missing")
    else:
        rs = [r for r in rows(rp) if r.get("arm") == "P1"]
        if len(rs) != v.get("n"):
            bad.append(f"n {v.get('n')} != {len(rs)} P1 rows")
        else:
            unc = [r["prompt_tokens"] - r["cached_tokens"] for r in rs]
            mean, sd, n = statistics.mean(unc), statistics.stdev(unc), len(unc)
            hw = t95(n) * sd / n ** 0.5
            if round(mean, 5) != round(v["unc_per_turn"], 5):
                bad.append(f"unc_per_turn {v['unc_per_turn']} != {round(mean, 5)}")
            lo, hi = round(mean - hw, 2), round(mean + hw, 2)
            if [lo, hi] != list(v.get("t_ci95") or []):
                bad.append(f"t_ci95 {v.get('t_ci95')} != re-derived [{lo}, {hi}]")
    checks.append(("V0_REDERIVED", not bad,
                   f"{rec.get('setup')} V0 numbers re-derive from {v.get('rows')}" if not bad
                   else f"{rec.get('setup')}: {'; '.join(bad)}"))


def run(strict: bool = False) -> list[tuple[str, bool, str]]:
    best = json.loads(BEST.read_text())
    release = json.loads(RELEASE.read_text())
    checks: list[tuple[str, bool, str]] = []
    for leg, setup in LEGS.items():
        path = ROOT / RECORD.format(setup=setup)
        rec = json.loads(path.read_text()) if path.exists() else None
        if not check_record(rec, setup, checks):
            continue
        check_identity(rec, best, setup, checks)
        check_argv_identical(rec, best, setup, checks)
        check_release_numbers(rec, release, setup, checks)
        check_command(rec, checks)
        check_divergence(rec, checks)
        check_launchable(rec, checks)
        check_no_null(rec, checks)
        check_no_invent(rec, checks)
        check_v0_rederivable(rec, checks)
    if strict:
        for leg, setup in LEGS.items():
            path = ROOT / RECORD.format(setup=setup)
            rec = json.loads(path.read_text()) if path.exists() else {}
            has_prod = bool(rec.get("production_cmd"))
            has_flag_diffs = bool([d for d in rec.get("differs") or []
                                   if not str(d.get("flag", "")).startswith("<")])
            # Strict does not require a production_cmd — it requires that IF the command diverges
            # from the argv, the divergence is carried by a *pinned* command plus named flags.
            if has_flag_diffs:
                ok = has_prod and bool(rec.get("differs_absent_from_pinned") is not None)
                detail = (f"{setup} diverges from the substrate argv and carries a pinned "
                          f"production_cmd with {len(rec.get('differs') or [])} named difference(s)"
                          if ok else f"{setup} diverges from the substrate but has no production_cmd")
            else:
                ok = not has_prod
                detail = (f"{setup} launch argv equals the substrate argv; no production_cmd needed"
                          if ok else f"{setup} carries a production_cmd but claims no divergence")
            checks.append(("STRICT", ok, detail))
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    checks = run(a.strict)
    ok = all(c[1] for c in checks)
    if a.json:
        print(json.dumps({"ok": ok, "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in checks]},
                         indent=2))
    else:
        for name, passed, detail in checks:
            print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")
        n_fail = sum(1 for c in checks if not c[1])
        print(f"SERVING checks: {len(checks)} run, {n_fail} failed")
        print(f"CHECK serving launchable: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
