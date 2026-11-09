#!/usr/bin/env python3
"""gate_ledger.py -- price the preflight gate chain, and prove the price is counted.

The artefact `experiments/ptr-engine/measure/GATE-LEDGER.json` is the record: per gate
what it prevents and for what evidence, how many defects the guard itself had, what would
replace it, whether a live path can still bypass it, the recommendation and -- mandatorily
-- the compliance sentence. The `cards` array is the cost side: one row per gate-related
card, with its Host card id, execution id, verdict, requests and measured tool calls.

`--check` recomputes the per-gate totals from that record and refuses (exit 1) when:

  * a card in `population` has no `cards` row          (an uncounted card)
  * a `cards` row names a handoff that is not on disk  (a claimed card with no corpus)
  * a cards row has no handoff and no `unreconstructible` reason (silence about a hole)
  * a gate has no `prevents` / `prevention_evidence`   (a gate with no stated benefit)
  * a gate's recommendation is missing its compliance sentence, or the sentence is not one
    of the two licensed forms, or the sentence contradicts the recommendation (retiring a
    guard cannot be described as "this does not weaken a guard")
  * the stored `totals` disagree with the recomputation

The compliance sentences are licensed verbatim as:
  "this does not weaken a guard: the refusal is unchanged and the removed element is ..."
  "this DOES relax a guard, and here is the measurement that licenses it ..."

Offline: stdlib only, no network, no request, no write. Read-only over the artefact and the
handoff corpus.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DEFAULT_ARTEFACT = os.path.join(
    REPO_ROOT, "experiments", "ptr-engine", "measure", "GATE-LEDGER.json")

RECOMMENDATIONS = ("keep", "demote_to_advisory", "retire")
KEEP_SENTENCE = "this does not weaken a guard: the refusal is unchanged and the removed element is"
RELAX_SENTENCE = "this DOES relax a guard, and here is the measurement that licenses it"
GATE_REQUIRED = ("gate", "prevents", "prevention_evidence", "defects_list",
                 "replacement", "live_path_bypass_possible", "recommendation",
                 "compliance_statement")
LEAKY_RECOMMENDATIONS = ("demote_to_advisory", "retire")
#: A gate-related card's handoff may legitimately be absent only when the record says why.
HANDOFF_OPTIONAL = ()


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _recount(doc):
    """Recompute every total from the arrays. Nothing is read back from `totals`."""
    gates = doc.get("gates") or []
    cards = doc.get("cards") or []
    per_gate = []
    for g in gates:
        lst = g.get("defects_list") or []
        per_gate.append({
            "gate": g.get("gate"),
            "recommendation": g.get("recommendation"),
            "defects": len(lst),
            "cards": sorted({c for d in lst for c in (d.get("cards") or [])}),
        })
    defects = sum(len(g.get("defects_list") or []) for g in gates)
    requests = sum(int(c.get("requests") or 0) for c in cards)
    measured = sum(int(c["tool_calls"]) for c in cards
                   if isinstance(c.get("tool_calls"), int))
    unrecorded = sum(1 for c in cards if not isinstance(c.get("tool_calls"), int))
    estimate = int(doc.get("estimate_per_unrecorded") or 0)
    return {
        "per_gate": per_gate,
        "cards": len(cards),
        "defects": defects,
        "requests": requests,
        "rounds_estimate": measured + estimate * unrecorded,
        "measured_tool_calls": measured,
        "unrecorded_cards": unrecorded,
    }


def check(doc, corpus_root=REPO_ROOT):
    """Return a list of human-readable errors. Empty means the record is counted."""
    errors = []
    gates = doc.get("gates") or []
    cards = doc.get("cards") or []
    population = doc.get("population") or []

    if not gates:
        errors.append("no gates: the record must price at least one gate")
    if not cards:
        errors.append("no cards: the cost side is empty")

    # 1. every gate states its benefit, its replacement, its decision, its compliance.
    for idx, g in enumerate(gates):
        label = g.get("gate") or ("gates[%d]" % idx)
        for key in GATE_REQUIRED:
            if key not in g:
                errors.append("%s: missing required field %r" % (label, key))
        for key in ("prevents", "prevention_evidence", "replacement"):
            if not str(g.get(key) or "").strip():
                errors.append("%s: %s is empty -- a gate with no stated benefit is"
                              " unchallenged, not justified" % (label, key))
        bypass = g.get("live_path_bypass_possible")
        if not isinstance(bypass, dict):
            errors.append("%s: live_path_bypass_possible must answer per thinking mode"
                          " (thinking_off, thinking_on_auto)" % label)
        else:
            for mode in ("thinking_off", "thinking_on_auto"):
                if not str(bypass.get(mode) or "").strip():
                    errors.append("%s: live_path_bypass_possible[%r] is missing -- a bypass"
                                  " answer that skips a mode is not an answer"
                                  % (label, mode))
        # 2. every gate's own defect count must match its list.
        found = g.get("defects_found")
        actual = len(g.get("defects_list") or [])
        if found is not None and int(found) != actual:
            errors.append("%s: defects_found=%s but defects_list holds %d"
                          % (label, found, actual))
        for d in (g.get("defects_list") or []):
            if not d.get("class"):
                errors.append("%s: defect %r has no class"
                              % (label, d.get("id") or "<unidentified>"))
            if not (d.get("cards") or []):
                errors.append("%s: defect %r names no card -- an unattributed cost"
                              % (label, d.get("id") or "<unidentified>"))
        # 3. the decision and its licensed sentence.
        rec = g.get("recommendation")
        sentence = str(g.get("compliance_statement") or "").strip()
        if rec not in RECOMMENDATIONS:
            errors.append("%s: recommendation %r is not one of %s"
                          % (label, rec, ", ".join(RECOMMENDATIONS)))
        if not sentence:
            errors.append("%s: recommendation %r has NO compliance sentence -- the licence"
                          " for the decision is what makes it a decision" % (label, rec))
        elif not (sentence.startswith(KEEP_SENTENCE) or sentence.startswith(RELAX_SENTENCE)):
            errors.append("%s: compliance sentence is not one of the two licensed forms"
                          " (it must start %r or %r)"
                          % (label, KEEP_SENTENCE, RELAX_SENTENCE))
        elif rec in LEAKY_RECOMMENDATIONS and sentence.startswith(KEEP_SENTENCE):
            errors.append("%s: recommendation %r claims 'this does not weaken a guard',"
                          " but removing a gate's refusal is exactly a relaxation"
                          % (label, rec))
        elif rec == "keep" and sentence.startswith(RELAX_SENTENCE):
            errors.append("%s: recommendation 'keep' claims the guard is being relaxed"
                          % label)

    # 4. every card in the population is counted, exactly once.
    seen = {}
    for c in cards:
        name = c.get("card")
        if not name:
            errors.append("cards[]: a row has no 'card' name")
            continue
        seen[name] = seen.get(name, 0) + 1
    for name, count in sorted(seen.items()):
        if count > 1:
            errors.append("%s: counted %d times -- one card, one cost" % (name, count))
    for name in population:
        if name not in seen:
            errors.append("%s: uncounted card -- it is in the population and has no cost row"
                          % name)
    for name in sorted(seen):
        if population and name not in population:
            errors.append("%s: counted but not in population -- the population is the"
                          " declared denominator" % name)

    # 5. a counted card must point at the corpus, or say why it cannot.
    for c in cards:
        name = c.get("card")
        hand = c.get("handoff")
        if hand:
            path = hand if os.path.isabs(hand) else os.path.join(corpus_root, hand)
            if not os.path.exists(path):
                errors.append("%s: handoff %s is not on disk" % (name, hand))
        elif not str(c.get("unreconstructible") or "").strip():
            errors.append("%s: no handoff and no reason -- an absent corpus is a finding,"
                          " not a blank" % name)
        for key in ("card_id", "execution_id", "verdict", "requests", "gate"):
            if key not in c:
                errors.append("%s: missing %r" % (name, key))
    gate_names = {g.get("gate") for g in gates} | {"chain"}
    for c in cards:
        if c.get("gate") not in gate_names:
            errors.append("%s: gate %r is not a gate this record prices"
                          % (c.get("card"), c.get("gate")))

    # 6. the totals must be the recomputation, not a claim about it.
    got = _recount(doc)
    stored = doc.get("totals") or {}
    for key in ("cards", "defects", "requests", "rounds_estimate"):
        if key not in stored:
            errors.append("totals: missing %r" % key)
        elif int(stored[key]) != got[key]:
            errors.append("totals.%s: stored %s, recomputed %s"
                          % (key, stored[key], got[key]))
    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description="price the preflight gate chain")
    ap.add_argument("--check", action="store_true",
                    help="recompute the totals and exit 1 on an uncounted card, a gate"
                         " with no stated benefit, or a decision with no compliance"
                         " sentence")
    ap.add_argument("--artefact", default=DEFAULT_ARTEFACT,
                    help="the GATE-LEDGER.json to read (default: the record of record)")
    ap.add_argument("--json", action="store_true", help="print the recomputation as JSON")
    args = ap.parse_args(argv)

    try:
        doc = _load(args.artefact)
    except (OSError, ValueError) as exc:
        print("GATE-LEDGER UNREADABLE: %s: %s" % (args.artefact, exc), file=sys.stderr)
        return 2

    if not args.check:
        got = _recount(doc)
        if args.json:
            print(json.dumps(got, indent=1, sort_keys=True))
            return 0
        print("GATE-LEDGER %s" % os.path.relpath(args.artefact, REPO_ROOT))
        for row in got["per_gate"]:
            print("  %-14s %-18s defects=%-2d cited-by=%s"
                  % (row["gate"], row["recommendation"], row["defects"],
                     ", ".join(row["cards"]) or "-"))
        print("  cards=%d defects=%d requests=%d rounds_estimate=%d"
              " (measured tool_calls %d over %d card(s), %d unrecorded)"
              % (got["cards"], got["defects"], got["requests"],
                 got["rounds_estimate"], got["measured_tool_calls"],
                 got["cards"] - got["unrecorded_cards"], got["unrecorded_cards"]))
        return 0

    errors = check(doc)
    if errors:
        for e in errors:
            print("GATE-LEDGER CHECK: %s" % e)
        print("GATE-LEDGER CHECK FAILED: %d error(s)" % len(errors))
        return 1
    got = _recount(doc)
    print("GATE-LEDGER CHECK OK: %d gates, %d cards, %d defects, %d requests,"
          " %d rounds (estimate)" % (len(doc.get("gates") or []), got["cards"],
                                     got["defects"], got["requests"],
                                     got["rounds_estimate"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
