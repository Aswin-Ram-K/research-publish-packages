#!/usr/bin/env python3
"""parm1_errata_check.py - machine check for the PARM-1 denominators errata (PARM-1-ERRATA).

OFFLINE. Stdlib only. Zero inference requests, no network, no model call, no `git`,
no re-grade of any arm, and it writes nothing. It reads three files read-only:

    docs/PREREG-ARM-RUN.md                     the FROZEN rule (never edited by this unit)
    docs/PARM-1-ERRATA.md                      the additive errata + its claims block
    experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json
                                               the frozen v7 fixture (the id census)

and it checks three things, in this order:

  1. FROZEN BYTES   the sha256 of the delimited PARM-1 rule body still equals the digest
                    recorded outside the body (`docs/PREREG-ARM-RUN.md:276`), and the 13
                    threshold-bearing phrases are byte-identical to their recorded digest.
                    A threshold may not move while its denominator is being corrected.

  2. CENSUS         the ledger claims in `docs/PARM-1-ERRATA.md` are recomputed from the
                    fixture: 12 ids, 9 substantive, 3 NONE, NUM/CALL/NONE kinds, the named
                    NONE ids, the named substantive ids, paper-decidability, the H3
                    denominator, the TVS 3-id denominator (re-read from `docs/TVS.md`), and
                    the `repair.t30` exclusion.

  3. NO INVENTED DENOMINATOR
                    every claim key must be one this tool knows how to recompute; an unknown
                    or unverifiable denominator claim fails the run instead of being ignored.

Exit 0 iff all three hold. Exit 1 otherwise, and every failure is named on its own line, so
the red case (an errata mutated to claim `12/12 substantive`) fails loudly rather than quietly.

    python3 experiments/ptr-engine/tools/parm1_errata_check.py
    python3 experiments/ptr-engine/tools/parm1_errata_check.py --print-claims
    python3 experiments/ptr-engine/tools/parm1_errata_check.py --errata /tmp/mutated.md   # red case

Idempotent: same output on every run, nothing written.
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

BODY_BEGIN = "<!-- parm-rule:begin -->"
BODY_END = "<!-- parm-rule:end -->"
CLAIMS_BEGIN = "<!-- parm1-errata-claims:begin -->"
CLAIMS_END = "<!-- parm1-errata-claims:end -->"

# Recorded at docs/PREREG-ARM-RUN.md:276 (S8) and re-recorded in docs/PARM-1-ERRATA.md.
FROZEN_BODY_SHA256 = "21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8"

# sha256 of "\\n".join(f"{name}={match}") over the threshold phrases below, in this order.
# Computed on 2026-10-26 against the frozen body; any threshold edit breaks it.
THRESHOLD_SHA256 = "069d28a4a023856b5b82273247568fba5b6a83a2f8ad81cee154e668ed6d64f6"

# Every threshold the errata claims unchanged, as (name, phrase regex). The name is the claim
# token used in the errata's `thresholds_unchanged` list.
THRESHOLDS = [
    ("h3_margin", r"2 checkpoints out of the 12 declared checkpoints = 16\.7 percentage points"),
    ("h3_margin_rule", r"loses more than 2 checkpoints fails H3"),
    ("h3_unadjudicable", r"below \*\*8 of 12\*\*"),
    ("h2_ratio", r"≤ 0\.95 × A's"),
    ("h2_uncached", r"< 1\.00 ×"),
    ("min_n", r"MIN_N \(=20\)"),
    ("tail_min", r"TAIL_MIN \(=3\)"),
    ("level", r"LEVEL=0\.95"),
    ("resamples", r"resamples=10000"),
    ("seed", r"seed=20261020"),
    ("p95_min_n", r"n ≥ 60"),
    ("mcnemar_discordant", r"`b \+ c >= 6`"),
    ("mcnemar_alpha", r"p < 0\.05"),
]

# H3's and TVS's declared ids, by the names of record (v6 ids in CHECKPOINT-COVERAGE/TVS.md).
TVS_DECLARED = ["cp.0.t12", "cp.1.t24", "cp.2.t46"]
SUPPORTED_KINDS = ("NUM", "CALL", "NONE")

# Claim keys this tool can recompute. Anything else in the claims block is an unverifiable
# denominator and is refused (see check 3).
RECOMPUTABLE_KEYS = {
    "unit", "date_utc", "prereg", "frozen_digest", "threshold_digest", "fixture",
    "fixture_sha256", "ids_total", "ids_substantive", "ids_none", "ids_by_kind",
    "none_ids", "substantive_ids", "decidable_fixture", "undecidable_fixture",
    "h3_denominator", "h3_margin_checkpoints", "h3_margin_pp_on_12",
    "h3_unadjudicable_below", "tvs_denominator", "tvs_ids", "tvs_ids_v7",
    "rep_t30_status", "rep_t30_in_h3_denominator", "rep_t30_scored",
    "thresholds_unchanged",
}


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def rule_body(prereg_text):
    """The frozen body: lines strictly between the markers, joined with \\n, one trailing \\n."""
    tail = prereg_text.split(BODY_BEGIN + "\n", 1)[1]
    return tail.split(BODY_END, 1)[0]


def recorded_body_digest(prereg_text):
    """The digest the prereg itself records outside the body (S8)."""
    m = re.search(r"sha256 of the PARM-1 rule body:\*\* `([0-9a-f]{64})`", prereg_text)
    return m.group(1) if m else None


def threshold_digest(body):
    """Digest of the 13 threshold phrases, or (None, missing_names) if any is absent/ambiguous."""
    parts, missing = [], []
    for name, pattern in THRESHOLDS:
        hits = re.findall(pattern, body)
        if len(hits) != 1:
            missing.append("%s (matches=%d)" % (name, len(hits)))
            continue
        parts.append("%s=%s" % (name, hits[0]))
    if missing:
        return None, missing
    return sha256_text("\n".join(parts)), []


def load_claims(errata_text):
    tail = errata_text.split(CLAIMS_BEGIN, 1)
    if len(tail) != 2:
        raise SystemExit("FAIL claims: no %s marker in the errata" % CLAIMS_BEGIN)
    block = tail[1].split(CLAIMS_END, 1)[0]
    m = re.search(r"```json\s*(\{.*?\})\s*```", block, re.S)
    if not m:
        raise SystemExit("FAIL claims: no ```json block between the claims markers")
    return json.loads(m.group(1))


def paper_decidable(cp):
    """Decidable on paper: a contracted answer line, a supported kind, non-empty truth, a derive rule."""
    form = cp.get("answer_form") or ""
    spec = cp.get("answer_spec") or {}
    derive = spec.get("derive") or {}
    return bool(
        form.startswith("ANSWER: ")
        and spec.get("kind") in SUPPORTED_KINDS
        and str(cp.get("expected", "")).strip()
        and derive.get("rule")
    )


def census(fixture):
    cps = fixture["checkpoints"]
    kinds = {}
    for cp in cps:
        k = cp["answer_spec"]["kind"]
        kinds[k] = kinds.get(k, 0) + 1
    none_ids = sorted(cp["id"] for cp in cps if cp["answer_spec"]["kind"] == "NONE")
    sub_ids = sorted(cp["id"] for cp in cps if cp["answer_spec"]["kind"] != "NONE")
    decidable = sum(1 for cp in cps if paper_decidable(cp))
    return {
        "ids_total": len(cps),
        "ids_by_kind": kinds,
        "ids_none": len(none_ids),
        "none_ids": none_ids,
        "ids_substantive": len(sub_ids),
        "substantive_ids": sub_ids,
        "decidable_fixture": decidable,
        "undecidable_fixture": len(cps) - decidable,
        "checkpoint_turns": sorted(cp["turn"] for cp in cps),
        "id_map": fixture.get("id_map") or {},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="PARM-1 errata machine check (offline)")
    ap.add_argument("--errata", default=os.path.join(ROOT, "docs", "PARM-1-ERRATA.md"))
    ap.add_argument("--prereg", default=os.path.join(ROOT, "docs", "PREREG-ARM-RUN.md"))
    ap.add_argument("--tvs", default=os.path.join(ROOT, "docs", "TVS.md"))
    ap.add_argument("--fixture",
                    default=os.path.join(ROOT, "experiments", "ptr-engine", "longrun",
                                         "tasks-v6", "LR-01.v7.json"))
    ap.add_argument("--print-claims", action="store_true", help="print the recomputed census")
    args = ap.parse_args(argv)

    problems = []
    ok = []

    # ---- 1. frozen bytes -------------------------------------------------------------
    with open(args.prereg, encoding="utf-8") as fh:
        prereg_text = fh.read()
    body = rule_body(prereg_text)
    body_sha = sha256_text(body)
    if body_sha != FROZEN_BODY_SHA256:
        problems.append("frozen body moved: sha256 %s != recorded %s"
                        % (body_sha, FROZEN_BODY_SHA256))
    else:
        ok.append("frozen rule body sha256 = %s" % body_sha)

    recorded = recorded_body_digest(prereg_text)
    if recorded != body_sha:
        problems.append("S8 records %s but the body hashes to %s" % (recorded, body_sha))
    else:
        ok.append("S8 recorded digest agrees with the body")

    t_digest, missing = threshold_digest(body)
    if missing:
        problems.append("threshold phrases missing/ambiguous in the frozen body: %s"
                        % ", ".join(missing))
    elif t_digest != THRESHOLD_SHA256:
        problems.append("threshold set moved: sha256 %s != recorded %s"
                        % (t_digest, THRESHOLD_SHA256))
    else:
        ok.append("13 threshold phrases byte-identical, sha256 = %s" % t_digest)

    # ---- 2. census -------------------------------------------------------------------
    with open(args.fixture, encoding="utf-8") as fh:
        fixture = json.load(fh)
    c = census(fixture)
    fixture_sha = sha256_file(args.fixture)
    with open(args.errata, encoding="utf-8") as fh:
        claims = load_claims(fh.read())

    if claims.get("fixture_sha256") != fixture_sha:
        problems.append("errata fixture_sha256 %s != actual %s"
                        % (claims.get("fixture_sha256"), fixture_sha))
    else:
        ok.append("fixture sha256 = %s" % fixture_sha)

    if claims.get("frozen_digest") != body_sha:
        problems.append("errata frozen_digest %s != body %s"
                        % (claims.get("frozen_digest"), body_sha))
    else:
        ok.append("errata frozen_digest agrees with the body")

    if t_digest and claims.get("threshold_digest") != t_digest:
        problems.append("errata threshold_digest %s != measured %s"
                        % (claims.get("threshold_digest"), t_digest))

    cmp_int = [("ids_total", c["ids_total"]), ("ids_substantive", c["ids_substantive"]),
               ("ids_none", c["ids_none"]), ("decidable_fixture", c["decidable_fixture"]),
               ("undecidable_fixture", c["undecidable_fixture"]),
               ("h3_denominator", c["ids_total"])]
    for key, measured in cmp_int:
        claimed = claims.get(key)
        if claimed != measured:
            problems.append("CLAIM %s = %r but the fixture measures %r" % (key, claimed, measured))
        else:
            ok.append("%s = %r (recomputed)" % (key, measured))

    if claims.get("ids_by_kind") != c["ids_by_kind"]:
        problems.append("CLAIM ids_by_kind = %r but the fixture measures %r"
                        % (claims.get("ids_by_kind"), c["ids_by_kind"]))
    else:
        ok.append("ids_by_kind = %r (recomputed)" % (c["ids_by_kind"],))
    if sorted(claims.get("none_ids") or []) != c["none_ids"]:
        problems.append("CLAIM none_ids = %r but the fixture measures %r"
                        % (claims.get("none_ids"), c["none_ids"]))
    if sorted(claims.get("substantive_ids") or []) != c["substantive_ids"]:
        problems.append("CLAIM substantive_ids do not match the fixture's %d non-NONE ids"
                        % c["ids_substantive"])
    else:
        ok.append("3 NONE + 9 substantive id names match the fixture")
    if c["ids_substantive"] + c["ids_none"] != c["ids_total"]:
        problems.append("census does not add up: %d + %d != %d"
                        % (c["ids_substantive"], c["ids_none"], c["ids_total"]))

    # ---- H3 margin arithmetic (a claim about counts, not a new threshold) -------------
    if claims.get("h3_margin_checkpoints") != 2:
        problems.append("CLAIM h3_margin_checkpoints = %r, frozen value is 2"
                        % claims.get("h3_margin_checkpoints"))
    pp = claims.get("h3_margin_pp_on_12")
    measured_pp = round(2 * 100.0 / c["ids_total"], 1)
    if not isinstance(pp, (int, float)) or abs(pp - measured_pp) > 0.05:
        problems.append("CLAIM h3_margin_pp_on_12 = %r but 2/%d = %r"
                        % (pp, c["ids_total"], measured_pp))
    else:
        ok.append("2/%d = %r pp (matches the frozen 16.7)" % (c["ids_total"], measured_pp))
    if claims.get("h3_unadjudicable_below") != "8 of 12":
        problems.append("CLAIM h3_unadjudicable_below = %r, frozen value is '8 of 12'"
                        % claims.get("h3_unadjudicable_below"))

    # ---- 3. TVS denominator, recomputed from the document that declares it ------------
    with open(args.tvs, encoding="utf-8") as fh:
        tvs_text = fh.read()
    m = re.search(r"\| declared space per arm \| [^|]*\| (\d+) ids? \(([^)]*)\) \|", tvs_text)
    if not m:
        problems.append("TVS: cannot find the 'declared space per arm' row in %s" % args.tvs)
        tvs_n, tvs_ids = None, []
    else:
        tvs_n = int(m.group(1))
        tvs_ids = [x.strip().strip("`") for x in m.group(2).split(",") if x.strip()]
        ok.append("TVS declared space re-read from docs/TVS.md: %d ids %r" % (tvs_n, tvs_ids))
        if tvs_n != len(tvs_ids):
            problems.append("TVS: declares %d ids but names %d" % (tvs_n, len(tvs_ids)))
    if tvs_n is not None:
        if claims.get("tvs_denominator") != tvs_n:
            problems.append("CLAIM tvs_denominator = %r but docs/TVS.md declares %d"
                            % (claims.get("tvs_denominator"), tvs_n))
        if sorted(claims.get("tvs_ids") or []) != sorted(tvs_ids):
            problems.append("CLAIM tvs_ids = %r but docs/TVS.md names %r"
                            % (claims.get("tvs_ids"), tvs_ids))
        for tid in tvs_ids:
            v7 = c["id_map"].get(tid, tid)
            if v7 not in c["substantive_ids"]:
                problems.append("TVS id %s (v7 %s) is not one of the 9 substantive ids"
                                % (tid, v7))
        all_ids = set(c["substantive_ids"]) | set(c["none_ids"])
        unmapped = [t for t in tvs_ids if (c["id_map"].get(t) or t) not in all_ids]
        if unmapped:
            problems.append("TVS ids %r do not map to any fixture checkpoint id" % (unmapped,))
        if all((c["id_map"].get(t) or t) in c["substantive_ids"] for t in tvs_ids):
            ok.append("all %d TVS ids are substantive (non-NONE) fixture ids" % len(tvs_ids))
        if claims.get("tvs_ids_v7") and sorted(
                c["id_map"].get(t) or t for t in tvs_ids) != sorted(claims["tvs_ids_v7"]):
            problems.append("CLAIM tvs_ids_v7 = %r but the fixture id_map maps them to %r"
                            % (claims["tvs_ids_v7"],
                               sorted(c["id_map"].get(t) or t for t in tvs_ids)))
    if claims.get("tvs_denominator") == c["ids_total"]:
        problems.append("TVS denominator claimed equal to the H3 denominator (%d): "
                        "TVS is a different claim and is never x/12" % c["ids_total"])

    # ---- repair.t30 ------------------------------------------------------------------
    rep_turn = (fixture.get("repair") or {}).get("at_turn")
    t30_in = rep_turn in c["checkpoint_turns"] if rep_turn is not None else None
    if t30_in:
        problems.append("repair.t30 (turn %r) IS one of the checkpoint turns: the census is wrong"
                        % (rep_turn,))
    else:
        ok.append("repair.t30 = turn %r, absent from checkpoint turns %r"
                  % (rep_turn, c["checkpoint_turns"]))
    if claims.get("rep_t30_in_h3_denominator") is not False:
        problems.append("CLAIM rep_t30_in_h3_denominator = %r, must be false"
                        % claims.get("rep_t30_in_h3_denominator"))
    if claims.get("rep_t30_scored") is not False:
        problems.append("CLAIM rep_t30_scored = %r, must be false (no grade_v5 cell exists)"
                        % claims.get("rep_t30_scored"))
    status = claims.get("rep_t30_status") or ""
    if not status or "excluded" not in status.lower():
        problems.append("CLAIM rep_t30_status must say 'excluded', got %r" % status)

    # ---- thresholds_unchanged: exactly the set this tool verified ---------------------
    want = sorted(name for name, _ in THRESHOLDS)
    got = sorted(claims.get("thresholds_unchanged") or [])
    if got != want:
        problems.append("CLAIM thresholds_unchanged differs from the verified set: "
                        "missing=%r extra=%r"
                        % (sorted(set(want) - set(got)), sorted(set(got) - set(want))))
    else:
        ok.append("all %d unchanged thresholds are listed by name" % len(want))

    # ---- no invented denominator -----------------------------------------------------
    unknown = sorted(set(claims) - RECOMPUTABLE_KEYS)
    if unknown:
        problems.append("CLAIM(S) this check cannot recompute (refused, not ignored): %r" % unknown)

    if args.print_claims:
        print(json.dumps({"claims": claims, "recomputed": c}, indent=1, sort_keys=True))

    for line in ok:
        print("ok   " + line)
    if problems:
        for line in problems:
            print("FAIL " + line)
        print("FAIL parm1 errata check: %d problem(s)" % len(problems))
        return 1
    print("PASS parm1 errata check: frozen bytes intact, census %d/%d substantive/%d NONE, "
          "TVS %d ids, repair.t30 excluded"
          % (c["ids_total"], c["ids_substantive"], c["ids_none"],
             claims.get("tvs_denominator")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
