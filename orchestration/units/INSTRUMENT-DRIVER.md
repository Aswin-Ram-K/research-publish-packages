# Unit INSTRUMENT-DRIVER

Built campaign driver and freeze script.

- $CAMPAIGN/run/driver.py: reserve→render→dispatch→grade→row→record; watcher/counts gates; first-row audit; stub engine; recovery loop.
- $CAMPAIGN/run/freeze_envelope.py: cs.envelope/1 with self-digest and path invariants.
- $CAMPAIGN/tests/test_instrument_driver.py: 10 tests, all pass.
- Envelope: run/envelopes/CAMPAIGN.json (and aliases), self-digest 253ad2f9...
