"""Guard for the one-spec/one-generator fixture pipeline (unit FIXTURE-GENERATIONS).

Red->green contract:
  (a) regenerate v5 -> sha256 == 967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567
  (b) regenerate v6 -> byte-identical to the file on disk
  (c) --check on a one-byte-drifted copy in a temp dir -> non-zero, naming the differing field
  (d) overwriting frozen bytes without --force-frozen -> refused, non-zero, referencing rows named
  (e) the spec parses and every variant it declares builds to its recorded sha256

No inference requests, no writes outside tmp_path, no existing runtime fixture is touched.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ENGINE = REPO / "experiments" / "ptr-engine"
TOOL = ENGINE / "tools" / "build_fixture.py"
SPEC_PATH = ENGINE / "longrun" / "fixtures-spec" / "LR-01.spec.json"
LIVE_V5 = ENGINE / "longrun" / "tasks-v5" / "runtime-v5" / "LR-01.v5.json"
LIVE_V6 = ENGINE / "longrun" / "tasks-v5" / "runtime-v5" / "LR-01.v6.json"
FROZEN_V5_SHA = "967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )


def spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def test_a_v5_regenerates_to_the_frozen_sha(tmp_path: Path) -> None:
    out = tmp_path / "LR-01.v5.json"
    r = run("--variant", "v5", "--out", str(out))
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert sha256(out) == FROZEN_V5_SHA
    assert sha256(LIVE_V5) == FROZEN_V5_SHA  # the live file still carries the frozen bytes
    assert spec()["variants"]["v5"]["sha256"] == FROZEN_V5_SHA


def test_b_v6_regenerates_byte_identically(tmp_path: Path) -> None:
    out = tmp_path / "LR-01.v6.json"
    r = run("--variant", "v6", "--out", str(out))
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert out.read_bytes() == LIVE_V6.read_bytes()
    assert sha256(out) == sha256(LIVE_V6)


def test_c_check_names_the_drifted_field(tmp_path: Path) -> None:
    drifted = tmp_path / "LR-01.v5.drifted.json"
    doc = json.loads(LIVE_V5.read_text(encoding="utf-8"))
    assert doc["system_prompt"]  # the field we will perturb
    doc["system_prompt"] = doc["system_prompt"][:-1] + ("X" if doc["system_prompt"][-1] != "X" else "Y")
    emit = spec()["variants"]["v5"]["emit"]
    drifted.write_text(
        json.dumps(doc, indent=emit["indent"], ensure_ascii=emit["ensure_ascii"],
                   sort_keys=emit["sort_keys"]) + ("\n" if emit["trailing_newline"] else ""),
        encoding="utf-8",
    )
    r = run("--check", "--variant", "v5", "--out", str(drifted))
    assert r.returncode != 0
    combined = r.stdout + r.stderr
    assert "drift" in combined.lower(), combined
    assert "system_prompt" in combined, combined


def test_d_frozen_overwrite_is_refused_and_names_the_rows(tmp_path: Path) -> None:
    # a byte-identical copy of the frozen v5 fixture: same digest, different path.
    target = tmp_path / "LR-01.v5.json"
    shutil.copyfile(LIVE_V5, target)
    before = target.read_bytes()
    r = run("--variant", "v5", "--out", str(target))
    assert r.returncode != 0
    combined = r.stdout + r.stderr
    assert "frozen" in combined.lower(), combined
    assert "rows-cell-pointer-stable" in combined or "rows-longrun" in combined, combined
    assert target.read_bytes() == before  # nothing was written
    # and the escape hatch exists and is explicit
    r2 = run("--variant", "v5", "--out", str(target), "--force-frozen")
    assert r2.returncode == 0, (r2.stdout, r2.stderr)
    assert target.read_bytes() == before


def test_e_spec_parses_and_every_variant_builds(tmp_path: Path) -> None:
    s = spec()
    assert s["schema"] == "consonance.fixture-spec/1"
    assert s["task_id"] == "LR-01"
    assert s["engine_root"]
    variants = s["variants"]
    assert set(variants) == {"v1", "v2", "v3", "v4", "v4.tools", "v4.tools2", "v5", "v6", "v7", "v8"}
    for name, v in variants.items():
        assert v["frozen"] is True, name
        assert v["status"] in {"live", "historical-frozen", "superseded-deletable"}, name
        assert v["frozen_reason"], name
        assert set(v["emit"]) == {"indent", "ensure_ascii", "sort_keys", "trailing_newline"}, name
        out = tmp_path / f"{name.replace('.', '-')}.json"
        r = run("--variant", name, "--out", str(out))
        assert r.returncode == 0, (name, r.stdout, r.stderr)
        assert sha256(out) == v["sha256"], name
        assert out.read_bytes() == (REPO / v["path"]).read_bytes(), name
        doc = json.loads(out.read_text(encoding="utf-8"))
        for key in s["required_paths"]:
            assert key in doc, (name, key)
        assert len(doc["turns"]) == v["turns"]
        assert len(doc["checkpoints"]) == v["checkpoints"]
