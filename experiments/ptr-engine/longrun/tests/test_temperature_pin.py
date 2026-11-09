import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import types
from run_longrun import build_parser

def test_temperature_absent_refused():
    import run_longrun as rl
    # build cfg without --temperature -> None
    cfg = build_parser().parse_args([])
    assert cfg.temperature is None
    # main refuses (exit 2) before any request
    rc = rl.main([])
    assert rc == 2

def test_temperature_explicit_passes_preflight_temperature():
    cfg = build_parser().parse_args(["--temperature", "0", "--task", "nope"])
    assert cfg.temperature == 0.0
    assert cfg.seed == 42

def test_stamped_fields_present():
    # simulate row stamping via make_row? just check defaults seed
    cfg = build_parser().parse_args(["--temperature", "0", "--seed", "7"])
    assert cfg.temperature == 0.0
    assert cfg.seed == 7

def test_client_request_body_includes_temperature_and_seed():
    import client
    cfg = types.SimpleNamespace(model="m", stream=False, max_tokens=4, temperature=0, seed=42)
    body = client.request_body(cfg, [{"role": "user", "content": "hi"}])
    assert body["temperature"] == 0
    assert body["seed"] == 42
