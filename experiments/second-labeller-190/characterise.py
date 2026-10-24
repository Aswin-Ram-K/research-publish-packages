#!/usr/bin/env python3
"""UEXP step 3: characterise the labels and the case set.

NOTE ON STATUS: the checks in section 5 of PREREGISTRATION.md were declared in advance. The
extra checks appended here (mirror-impossible option strings within a case, undeclared `kind`
values, ESCALATE-availability) are POST-HOC additions, flagged as such in EVIDENCE.md.
"""
import json
import re
import statistics
from collections import Counter

cases = json.load(open("cases.json", encoding="utf-8"))
ts = open("reflex-decisions.sandbox.ts", encoding="utf-8").read()

out = {}
out["cases"] = len(cases)
out["header_declared_count"] = int(re.search(r"These (\d+) cases are a seed", ts).group(1))
out["kinds"] = dict(Counter(c["kind"] for c in cases).most_common())

declared = re.findall(r'^\s*\| "([a-z.]+)"', ts, re.M)
out["declared_kinds"] = declared
out["kinds_used_not_declared"] = sorted({c["kind"] for c in cases} - set(declared))
out["kinds_declared_not_used"] = [k for k in declared if k not in {c["kind"] for c in cases}]

# POST-HOC: two options in the same case that normalise to the same string make the case
# unlabelable-by-text alone.
out["cases_with_duplicate_option_strings"] = [
    c["id"] for c in cases
    if len(c["options"]) != len({o.strip().lower() for o in c["options"]})]

# POST-HOC: an option string that also appears as another case's recorded label tells us how
# much label vocabulary is reused vs bespoke.
all_labels = Counter(c["options"][c["correct"]] for c in cases)
out["labels_used_once"] = sum(1 for v in all_labels.values() if v == 1)

# POST-HOC: ESCALATE availability vs use (the header claims abstention is measured, not assumed)
esc_offered = [c["id"] for c in cases if "ESCALATE" in c["options"]]
esc_chosen = [c["id"] for c in cases if c["options"][c["correct"]] == "ESCALATE"]
out["escalate_offered_in_options"] = len(esc_offered)
out["escalate_chosen"] = len(esc_chosen)
out["escalate_offered_but_not_chosen"] = len(set(esc_offered) - set(esc_chosen))

out["namespaces"] = dict(Counter(ns for c in cases for ns in c["namespaces"]).most_common())
out["cases_with_no_namespaces"] = [c["id"] for c in cases if not c["namespaces"]]

L = [len(c["question"]) for c in cases]
out["question_chars_min_median_max"] = [min(L), int(statistics.median(L)), max(L)]
out["non_ascii_cases"] = [c["id"] for c in cases
                          if any(ord(ch) > 127 for ch in c["question"] + c["rationale"])]
out["empty_rationale"] = [c["id"] for c in cases if not c["rationale"].strip()]

out["per_kind"] = {}
for k in sorted({c["kind"] for c in cases}):
    ks = [c for c in cases if c["kind"] == k]
    dist = Counter(c["options"][c["correct"]] for c in ks)
    out["per_kind"][k] = {
        "n": len(ks),
        "options_per_case": dict(sorted(Counter(len(c["options"]) for c in ks).items())),
        "distinct_labels": len(dist),
        "distinct_options_total": len({o for c in ks for o in c["options"]}),
        "modal_labels": dist.most_common(3),
    }

out["fixture_lines"] = ts.count("\n") + 1
out["id_field_matches_including_interface"] = len(re.findall(r"^\s*id:", ts, re.M))
print(json.dumps(out, indent=1))
json.dump(out, open("characterisation.json", "w", encoding="utf-8"), indent=1)
