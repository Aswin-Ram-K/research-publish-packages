WITHDRAWN — LR-01.v10 (QUARANTINE10)

LR-01.v10 was built to combine the two existing fixtures: LR-01.v9 has
12 gradable checkpoints but no tool output, so arm masking-no-fetch had
nothing to mask; PT-01/02/03.v9 reach masking but have no gradable
checkpoints. V10 was intended to give both tool output and gradable
checkpoints in one task.

It cannot discriminate mask-versus-fetch. Independent adversarial review
(V10CRITIC, confidence 0.99) found all 12 checkpoints keep their source
evidence in plaintext under both arms, so masking changes nothing the
model can read. The review also reported pointer-fetch integration and
generation-identity defects, and a self-check that fails to detect the
leak. Verdict: NO-GO on the 96 requests it was to justify.

Deleted: experiments/ptr-engine/longrun/tasks-v6/LR-01.v10.json and its
contrast test. Verified absent: no v10 file remains in tasks-v6 and no
code or JSON references LR-01.v10.

Standing consequence: no fixture in this repo currently supports a
discriminating mask-versus-fetch contrast. A new fixture would need
evidence present only behind the pointer, with a self-check that
demonstrates the leak is absent under the masked arm.
