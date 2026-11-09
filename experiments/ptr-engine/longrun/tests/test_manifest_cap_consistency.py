"""Guard: every LR-01.v8 dry-run manifest must quote design_cap_tokens == 10616.

RUNNER-WALL-KEY closed F3: run_longrun.py resolves a wall per arm from
`wall_tokens_by_arm` and refuses the top-level fallback. v8's top-level
`wall_tokens` is 3838 (below its own first prompt, 3848) while every arm runs at
10616. A manifest that still quotes 3838 is stale provenance: the grid would be
graded against a cap the runner never used. Archived pre-fix manifests live under
manifests/archive/ and are deliberately NOT scanned.
"""
import json
import pathlib

MANIFESTS = pathlib.Path(__file__).resolve().parents[1] / "manifests"
V8_FIXTURE_ID = "LR-01.v8"
V8_SHA256 = "0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641"
V8_CAP_TOKENS = 10616


def _is_v8(doc):
    prov = doc.get("provenance") or {}
    fixture = doc.get("fixture") or {}
    fixture_id = str(prov.get("fixture_id") or "")
    if fixture_id.startswith(V8_FIXTURE_ID):
        return True
    return (prov.get("fixture_sha256") or fixture.get("sha256")) == V8_SHA256


def v8_manifests():
    """(path, design_cap_tokens) for every live manifest naming v8."""
    out = []
    for path in sorted(MANIFESTS.glob("*.json")):
        if "archive" in path.parts:
            continue
        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(doc, dict) or not _is_v8(doc):
            continue
        cap = (doc.get("engine_flags") or {}).get("design_cap_tokens")
        out.append((path, cap))
    return out


def test_v8_manifests_exist():
    found = v8_manifests()
    assert found, "no live manifest names LR-01.v8; re-run the v8 dry run first"


def test_every_v8_manifest_quotes_the_by_arm_cap():
    bad = [(str(p), cap) for p, cap in v8_manifests() if cap != V8_CAP_TOKENS]
    assert not bad, (
        "stale v8 provenance: these manifests quote design_cap_tokens != %d "
        "(the runner resolves 10616 per arm from wall_tokens_by_arm; 3838 is the "
        "dead top-level fallback): %r" % (V8_CAP_TOKENS, bad))


if __name__ == "__main__":
    for p, cap in v8_manifests():
        print(cap, p)
