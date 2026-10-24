#!/usr/bin/env python3
"""UEXP2: three-way comparison of the SECOND blind model pass (labelsB2.json, model
mimo-v2.6-flash) against (a) the fixture's recorded labels and (b) UEXP's primary pass
(labelsB.json), plus per-dimension stratified kappa, the memory.admission convention test
and the option-arity test.

Reads only. Writes metrics2.json and disagreementsB2.jsonl in this sandbox.
NEVER writes labelsB.json / metrics.json / disagreements.jsonl (UEXP's frozen record) and
never touches the target repo. Re-runnable: python3 compare2.py
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))
B = json.load(open(os.path.join(HERE, "labelsB.json"), encoding="utf-8"))["labels"]
B2blob = json.load(open(os.path.join(HERE, "labelsB2.json"), encoding="utf-8"))
B2 = B2blob["labels"]
by_id = {c["id"]: c for c in cases}

missing = [c["id"] for c in cases if c["id"] not in B2]
extra = [i for i in B2 if i not in by_id]
bad = [i for i, v in B2.items() if i in by_id and not (isinstance(v, int) and 0 <= v < len(by_id[i]["options"]))]
if missing or extra or bad:
    raise SystemExit("labelsB2 invalid: missing=%s extra=%s bad=%s" % (missing, extra, bad))

rec_idx = [c["correct"] for c in cases]
rec_lbl = [c["options"][c["correct"]] for c in cases]
B_idx = [B[c["id"]] for c in cases]
B2_idx = [B2[c["id"]] for c in cases]
B_lbl = [c["options"][B_idx[k]] for k, c in enumerate(cases)]
B2_lbl = [c["options"][B2_idx[k]] for k, c in enumerate(cases)]


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in set(ca) | set(cb)) / (n * n)
    return {"n": n, "agreement": po, "po": po, "pe": pe,
            "kappa": None if pe == 1 else (po - pe) / (1 - pe)}


out = {"pass2": {"file": "labelsB2.json", "labeller_string": B2blob.get("labeller"),
                 "model": "mimo-v2.6-flash (keyring/mimo-v2.6-flash)", "date": "2026-10-15",
                 "cases": len(cases)}}

out["vs_fixture"] = kappa(rec_lbl, B2_lbl)
out["vs_fixture"]["exact_index_matches"] = sum(r == b for r, b in zip(rec_idx, B2_idx))
out["vs_UEXP_labelsB"] = kappa(B_lbl, B2_lbl)
out["vs_UEXP_labelsB"]["exact_index_matches"] = sum(a == b for a, b in zip(B_idx, B2_idx))
out["UEXP_vs_fixture_recomputed"] = kappa(rec_lbl, B_lbl)  # sanity: should match RUN.json

# ---- per-dimension (per-kind) stratified kappa ------------------------------
kinds = sorted({c["kind"] for c in cases})
out["stratified_kappa_vs_fixture"] = {}
for kd in kinds:
    sub = [k for k, c in enumerate(cases) if c["kind"] == kd]
    out["stratified_kappa_vs_fixture"][kd] = {
        "n": len(sub),
        "B2": kappa([rec_lbl[k] for k in sub], [B2_lbl[k] for k in sub]),
        "B_UEXP": kappa([rec_lbl[k] for k in sub], [B_lbl[k] for k in sub])}

# ---- option-arity test: does accuracy track option count? -------------------
out["arity_test"] = {}
for a in sorted({len(c["options"]) for c in cases}):
    sub = [k for k, c in enumerate(cases) if len(c["options"]) == a]
    k2 = kappa([rec_lbl[k] for k in sub], [B2_lbl[k] for k in sub])
    kB = kappa([rec_lbl[k] for k in sub], [B_lbl[k] for k in sub])
    out["arity_test"]["arity_%d" % a] = {
        "n": len(sub),
        "B2_agreement": k2["agreement"], "B2_kappa": k2["kappa"],
        "B_UEXP_agreement": kB["agreement"], "B_UEXP_kappa": kB["kappa"]}

# ---- trivially-labelable stratum (escalation names its answer; 30/30) -------
for name, sel in (("escalation_names_answer", lambda c: c["kind"] == "escalation"),
                  ("all_other_kinds", lambda c: c["kind"] != "escalation")):
    sub = [k for k, c in enumerate(cases) if sel(c)]
    out["stratum_" + name] = {
        "n": len(sub),
        "B2": kappa([rec_lbl[k] for k in sub], [B2_lbl[k] for k in sub]),
        "B_UEXP": kappa([rec_lbl[k] for k in sub], [B_lbl[k] for k in sub])}

# ---- disagreement structure vs UEXP's --------------------------------------
d2 = [k for k in range(len(cases)) if B2_idx[k] != rec_idx[k]]
dB = [k for k in range(len(cases)) if B_idx[k] != rec_idx[k]]
s2 = {cases[k]["id"] for k in d2}
sB = {cases[k]["id"] for k in dB}
out["disagreements_B2_vs_fixture"] = len(d2)
out["disagreements_UEXP_vs_fixture"] = len(dB)
out["disagreement_set_overlap"] = {
    "both_models": sorted(s2 & sB),
    "B2_only": sorted(s2 - sB),
    "UEXP_only": sorted(sB - s2),
    "jaccard": len(s2 & sB) / len(s2 | sB) if (s2 | sB) else 1.0}

# UEXP's four conventions + the two unclustered items, from EVIDENCE.md s6
CLUSTERS = {
    "memory.admission_tier_boundary": ["memory.admission-001", "memory.admission-008",
                                       "memory.admission-009", "memory.admission-018",
                                       "memory.admission-021", "memory.admission-027"],
    "capability.family_construction": ["capability.family-004", "capability.family-009",
                                       "capability.family-010"],
    "acquisition_escalate_vs_dispose": ["acquisition-007", "acquisition-014",
                                        "acquisition-019", "acquisition-023"],
    "context.package_reuse_by_hash": ["context.package-002", "context.package-004"],
    "unclustered_in_UEXP": ["worker.class-018", "worker.class-023", "topology-018"],
}
out["B2_disagreements_by_UEXP_cluster"] = {
    cl: sorted(s2 & set(ids)) for cl, ids in CLUSTERS.items()}

# ---- memory.admission convention test (the specific systematic finding) -----
CONV = ["memory.admission-001", "memory.admission-009", "memory.admission-021",
        "memory.admission-027"]
conv_cases = {}
for cid in CONV:
    c = by_id[cid]
    k = cases.index(c)
    conv_cases[cid] = {"recorded": c["options"][rec_idx[k]],
                       "UEXP_labelsB": c["options"][B_idx[k]],
                       "B2_labelsB2": c["options"][B2_idx[k]],
                       "B2_matches_UEXP_choice": B2_idx[k] == B_idx[k],
                       "B2_matches_record": B2_idx[k] == rec_idx[k]}
n_rep = sum(1 for v in conv_cases.values()
            if v["B2_matches_UEXP_choice"] and not v["B2_matches_record"])
out["memory_admission_convention_test"] = {
    "convention": "step-scoped scratch never re-read: recorded EPHEMERAL vs blind-reader DROP",
    "cases": conv_cases,
    "B2_sides_with_UEXP_not_record_count": n_rep, "of": len(CONV),
    "replicated": n_rep >= 3}

# ---- per-case disagreement file --------------------------------------------
rows = []
for k, c in enumerate(cases):
    if B2_idx[k] == rec_idx[k]:
        continue
    rows.append({
        "id": c["id"], "kind": c["kind"], "question": c["question"], "options": c["options"],
        "recorded_index": rec_idx[k], "recorded_label": rec_lbl[k],
        "B2_index": B2_idx[k], "B2_label": B2_lbl[k],
        "B_UEXP_index": B_idx[k], "B_UEXP_label": B_lbl[k],
        "B2_agrees_with_UEXP": B2_idx[k] == B_idx[k],
        "recorded_rationale": c["rationale"], "line": c["_line"]})
with open(os.path.join(HERE, "disagreementsB2.jsonl"), "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
out["disagreementsB2_jsonl_rows"] = len(rows)

with open(os.path.join(HERE, "metrics2.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)

# ---- bounded human-readable summary (this is the verbatim evidence capture) --
print("=== compare2.py summary ===")
print("cases %d  B2 labeller-string %r" % (len(cases), B2blob.get("labeller")))
for key in ("vs_fixture", "vs_UEXP_labelsB", "UEXP_vs_fixture_recomputed"):
    m = out[key]
    print("%-28s n=%d agreement=%.6f po=%.6f pe=%.6f kappa=%s exact=%s" % (
        key, m["n"], m["agreement"], m["po"], m["pe"],
        "%.6f" % m["kappa"] if m["kappa"] is not None else "None",
        m.get("exact_index_matches", "-")))
print("\n-- stratified kappa vs fixture (B2 = this run, B = UEXP) --")
for kd, e in out["stratified_kappa_vs_fixture"].items():
    print("%-18s n=%3d  B2 agr=%.4f k=%.4f   UEXP agr=%.4f k=%.4f" % (
        kd, e["n"], e["B2"]["agreement"], e["B2"]["kappa"] or 0.0,
        e["B_UEXP"]["agreement"], e["B_UEXP"]["kappa"] or 0.0))
print("\n-- arity test (agreement vs fixture) --")
for a, e in out["arity_test"].items():
    print("%-10s n=%3d  B2 agr=%.4f k=%.4f   UEXP agr=%.4f k=%.4f" % (
        a, e["n"], e["B2_agreement"], e["B2_kappa"] or 0.0,
        e["B_UEXP_agreement"], e["B_UEXP_kappa"] or 0.0))
for name in ("stratum_escalation_names_answer", "stratum_all_other_kinds"):
    e = out[name]
    print("%-34s n=%3d  B2 agr=%.4f k=%.4f   UEXP agr=%.4f k=%.4f" % (
        name, e["n"], e["B2"]["agreement"], e["B2"]["kappa"] or 0.0,
        e["B_UEXP"]["agreement"], e["B_UEXP"]["kappa"] or 0.0))
print("\n-- disagreement structure --")
print("B2 disagreements %d ; UEXP disagreements %d ; overlap both=%d B2-only=%d UEXP-only=%d jaccard=%.4f" % (
    len(d2), len(dB), len(s2 & sB), len(s2 - sB), len(sB - s2),
    out["disagreement_set_overlap"]["jaccard"]))
for cl, ids in out["B2_disagreements_by_UEXP_cluster"].items():
    print("  %-32s %s" % (cl, ids))
print("\n-- memory.admission convention test (recorded EPHEMERAL vs blind DROP) --")
for cid, v in conv_cases.items():
    print("  %-22s recorded=%-10s UEXP=%-6s B2=%-6s  replicated=%s" % (
        cid, v["recorded"], v["UEXP_labelsB"], v["B2_labelsB2"],
        v["B2_matches_UEXP_choice"] and not v["B2_matches_record"]))
print("replicated %d/%d -> %s" % (n_rep, len(CONV), out["memory_admission_convention_test"]["replicated"]))
print("\nwrote metrics2.json and disagreementsB2.jsonl (%d rows)" % len(rows))
