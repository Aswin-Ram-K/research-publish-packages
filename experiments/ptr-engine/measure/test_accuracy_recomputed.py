"""Deterministic self-check for measure/ACCURACY-RECOMPUTED.json (unit
ACCURACY-DENOMINATOR-RECOMPUTE).

The consolidated record embeds the generator that produced it. This test
re-executes that generator into a temporary directory and asserts the output is
BYTE-IDENTICAL to the published file: the record is a pure function of the
historical sources it reads, and the historical sources were not touched.

Run:  pytest experiments/ptr-engine/measure/test_accuracy_recomputed.py -q
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISHED = os.path.join(HERE, "ACCURACY-RECOMPUTED.json")


def test_recomputed_record_regenerates_byte_identically(tmp_path):
    with open(PUBLISHED) as f:
        doc = json.load(f)
    gen = tmp_path / "gen.py"
    gen.write_text(doc["generator"])
    out = tmp_path / "regen"
    subprocess.run([sys.executable, str(gen), "--outdir", str(out)],
                   check=True, capture_output=True)
    regen = (out / "ACCURACY-RECOMPUTED.json").read_bytes()
    published = open(PUBLISHED, "rb").read()
    assert regen == published, "regenerated record differs from the published one"


def test_published_record_carries_its_provenance():
    with open(PUBLISHED) as f:
        doc = json.load(f)
    assert doc["rule"].startswith("decidable = pass + fail")
    assert doc["owner_source"] == "experiments/ptr-engine/longrun/grade_v5.py:752-789"
    for rec in doc["records"]:
        assert len(rec["source_sha256"]) == 64
    assert all(len(x["source_sha256"]) == 64 for x in doc["aggregate_records_checked"])
