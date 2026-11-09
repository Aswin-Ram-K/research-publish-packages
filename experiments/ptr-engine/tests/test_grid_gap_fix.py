"""tests/test_grid_gap_fix.py — red->green for the ONE defect this card may repair.

GRID-GAP-DIAG (card ee6448b3) found three gaps in GRID-RUN-2. Only the third is
inside a layer this card may write: the cell-record/reader join.

THE DEFECT
    cell.py wrote the cell record with the rows file NESTED at
    ``record["run"]["rows_path"]`` (cell.py:2145-2146 builds ``run``; cell.py:2285
    puts it under ``"run": run``).  The pinned reader
    ``analyze_stats.load_cell_manifests`` (analyze_stats.py:655-687) only accepts a
    record whose TOP-LEVEL key ``rows_path`` is set:

        if isinstance(man, dict) and man.get("rows_path"):
            ...

    so every record cell.py wrote was silently DROPPED, and the GRID-RUN-2 report
    had to rebuild its census by hand.

THE FIX (layer A: cell.py is not in the harness pin — see HARNESS-FILES in
cell.py:129-135 and the pin's ``digest_recipe``)
    the record carries the flat key as well, through ``cell.with_rows_path()``.
    ``cell.cell_rows_path()`` reads either shape, so a record written before the
    fix is still readable by cell.py's own code paths.

The reader itself is PINNED and is not edited here: writing the flat key means the
pinned reader works unchanged.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.join(os.path.dirname(HERE), "longrun")
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import cell  # noqa: E402  (the writer under repair)
import analyze_stats  # noqa: E402  (the pinned reader; imported, never edited)

ROWS = "experiments/ptr-engine/measure/rows-cell-transcript-grow-20261028T031218Z.jsonl"


def record_as_cell_py_wrote_it(rows_path=ROWS):
    """The shape cell.py's ``stage_run`` detail + main() record produced before the fix."""
    return {
        "unit": "CELL-ONE-COMMAND",
        "arm": "transcript-grow",
        "turns": 48,
        "run": {"argv": [], "exit": 0, "rows_path": rows_path,
                "rows_written": 53, "offline": False},
    }


class RowsPathJoin(unittest.TestCase):
    def test_pinned_reader_drops_the_nested_shape(self):
        """The defect, pinned: a nested-only record is unlinkable by the reader.

        This test is the RED half of the pair. It must keep passing after the fix:
        it says the reader is unchanged and still requires the flat key, which is
        exactly why the writer has to emit it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cell-transcript-grow-x.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(record_as_cell_py_wrote_it(), fh)
            self.assertEqual(analyze_stats.load_cell_manifests([path], manifest_dir=""), [],
                             "the pinned reader must not link a nested-only record; "
                             "if this changed, the reader was edited (it is pinned)")

    def test_writer_emits_a_flat_rows_path_the_reader_links(self):
        """GREEN: the record the writer now builds is linkable by the pinned reader."""
        rec = cell.with_rows_path(record_as_cell_py_wrote_it())
        self.assertEqual(rec["rows_path"], ROWS)
        self.assertEqual(rec["run"]["rows_path"], ROWS,
                         "the nested key is kept: existing consumers read it")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cell-transcript-grow-x.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(rec, fh)
            linked = analyze_stats.load_cell_manifests([path], manifest_dir="")
        self.assertEqual(len(linked), 1, "cell.py's record must be linkable, no census by hand")
        self.assertEqual(linked[0]["rows_path"], ROWS)

    def test_accessor_reads_both_shapes(self):
        """cell.py's own code must read a record written either before or after the fix."""
        self.assertEqual(cell.cell_rows_path(record_as_cell_py_wrote_it()), ROWS)
        flat = {"rows_path": ROWS, "run": {"exit": 0}}
        self.assertEqual(cell.cell_rows_path(flat), ROWS)
        self.assertIsNone(cell.cell_rows_path({"run": {"exit": 0}}))
        self.assertIsNone(cell.cell_rows_path({"run": None}))
        self.assertIsNone(cell.cell_rows_path(None))

    def test_flat_key_wins_and_is_not_invented_when_absent(self):
        rec = {"run": {"exit": 0}, "rows_path": ROWS}
        rec = cell.with_rows_path(rec)
        self.assertEqual(rec["rows_path"], ROWS)
        empty = cell.with_rows_path({"run": {"exit": 0}})
        self.assertNotIn("rows_path", empty,
                         "a record with no rows file must not gain a null join key")


if __name__ == "__main__":
    unittest.main()
