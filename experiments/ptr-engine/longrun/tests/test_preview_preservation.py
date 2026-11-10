"""PREVIEW-PRESERVATION: a dry run must never delete committed preview evidence.

`state/previews/<task_id>/**` is tracked evidence — the request bodies each arm would
send.  `run_dry` used to `rmtree` the whole task directory up front, so an offline
`--dry-run` deleted the previews of every arm it did not happen to render (this really
happened to `LR-01/transcript-compact`).  The invariant tested here is about the tree,
not about the function: files a run does not render stay, byte for byte, and so do files
outside the run's turn scope.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import run_longrun as R  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
UNRENDERED_ARM = "masking-no-fetch"
UNRENDERED_BODY = b'{"arm": "masking-no-fetch", "turn": 1, "evidence": "tracked"}\n'


class _Cfg:
    """The least a dry run reads; no socket, no ledger, one turn of scope."""

    def __init__(self):
        self.tools = ""
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model"
        self.temperature = 0
        self.thinking = "off"
        self.max_turns = 1
        self.show_prompts = False
        self.fetch_policy = "strict"
        self.fetch_rounds_per_turn = 0


def test_dry_run_keeps_previews_of_arms_it_does_not_render():
    fixture = R.load_fixture(FIXTURE)
    root = tempfile.mkdtemp(prefix="preview-preserve-")

    # (a) evidence for an arm this run never renders
    kept_dir = os.path.join(root, UNRENDERED_ARM)
    os.makedirs(kept_dir)
    kept_path = os.path.join(kept_dir, "turn-01.json")
    with open(kept_path, "wb") as fh:
        fh.write(UNRENDERED_BODY)

    # (b) a rendered arm's preview OUTSIDE this run's turn scope (--max-turns 1 < 48)
    rendered_dir = os.path.join(root, "pointer-stable")
    os.makedirs(rendered_dir)
    far_path = os.path.join(rendered_dir, "turn-48.json")
    with open(far_path, "wb") as fh:
        fh.write(b'{"turn": 48}\n')

    rc = R.run_dry(_Cfg(), fixture, [("pointer-stable", 1)], root=root)
    assert rc == 0, "the preview exited %r" % (rc,)

    assert os.path.exists(kept_path), (
        "the dry run deleted %s: an arm it never rendered" % kept_path)
    with open(kept_path, "rb") as fh:
        assert fh.read() == UNRENDERED_BODY, "the untouched preview's bytes changed"

    assert os.path.exists(os.path.join(rendered_dir, "turn-01.json")), (
        "the rendered turn's preview is missing")
    assert os.path.exists(far_path), (
        "the dry run deleted %s: outside its 1-turn scope" % far_path)
