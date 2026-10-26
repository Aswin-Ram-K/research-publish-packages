# submission-kit — upload files

Assembled 2026-10-19 by UPRESKIT1. Every file here is a **byte-identical copy** of the file named in
"Source"; the copy was verified by `sha256sum` after copying (see `strategy/SUBMISSION_KIT.md` §6).
Upload from **this** directory, not from the paper trees.

Two form fields have their own sections in `strategy/SUBMISSION_KIT.md` §3 — read them before starting a
submission:

- **Type:** choose `Article`, for all three papers, identically (§3.0). `Conference Paper` is wrong — that
  option exists only for unpublished, DOI-less conference papers.
- **Data availability:** each paper enters **its own** concept DOI — `10.5281/zenodo.23463944`
  (encoder-crossover-190), `10.5281/zenodo.23482511` (replay-record-not-decision), `10.5281/zenodo.23483314`
  (gated-read-batching) (§3.9). Never one paper's DOI in another's form.

| # | File | Bytes | sha256 | Source |
|---|------|-------|--------|--------|
| 1 | `preprints/encoder-crossover-190-preprints.zip` | 28,712 | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` | `papers/encoder-crossover-190/preprints/encoder-crossover-190-preprints.zip` |
| 2 | `preprints/replay-record-not-decision-preprints.zip` | 11,526 | `1b520f22ad7ec0d83e0c82a734fd5790724a2dfbb175a2600ac323294953537d` | `papers/replay-record-not-decision/preprints/replay-record-not-decision-preprints.zip` |
| 3 | `preprints/gated-read-batching-preprints.zip` | 15,296 | `7efe3af1d358552b2e4231a63cb02820d25bd678aa1761f06ba5880bdfe783a0` | `papers/gated-read-batching/preprints/gated-read-batching-preprints.zip` |
| 4 | `tmlr/encoder-crossover-190-main.pdf` | 177,298 | `fb95f0ac302a07678eaf5f73ef7038a5d46beeb6807830f065a94ffb38cf1109` | `papers/encoder-crossover-190/tmlr/main.pdf` |
| 5 | `tmlr/replay-record-not-decision-main.pdf` | 93,109 | `cefd09a7a161d73bf7ae27303ca8cb00dbab2761485beca30bb90856846aee7a` | `papers/replay-record-not-decision/tmlr/main.pdf` |
| 6 | `tmlr/gated-read-batching-main.pdf` | 107,504 | `25a9394e4f649335dd61209dc0075ece5091d0363f675042078a440db79bfeba` | `papers/gated-read-batching/tmlr/main.pdf` |
| 7 | `abstracts/encoder-crossover-190.txt` | 1,195 chars | `fe6786245cee6c6eb72fc9bf7a9a0178ccc7e53884e9ca4478aff9f4ebe951ef` | `papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt` |
| 8 | `abstracts/replay-record-not-decision.txt` | 1,594 chars | `9765d28e0ca851084b327beaa5734b422634a8989a2799810035f3da795445dd` | `papers/replay-record-not-decision/submission/ABSTRACT_METADATA.txt` |
| 9 | `abstracts/gated-read-batching.txt` | 1,884 chars | `05ce7038056235b3bd52dd1f3dac3c048698701eac35cd779b3198192c88e962` | `papers/gated-read-batching/submission/ABSTRACT_METADATA.txt` |

Note on rows 2, 3, 5, 6: these sha256 values are the files **as they stand on disk today** and they differ
from the values recorded in the original task card (card values and the cause are documented in
`strategy/SUBMISSION_KIT.md` §6, "Hash drift"). The files here are correct copies of the current sources —
verify with:

```sh
cd submission-kit && sha256sum preprints/*.zip tmlr/*.pdf abstracts/*.txt
```

**Gated paper — final:** rows 3 and 6 were re-copied on 2026-10-19 after the Conflicts-of-Interest placement
correction (`strategy/SUBMISSION_KIT.md` §6.5, resolved) and their size and sha256 above were re-measured
from disk. All nine rows are final and may be uploaded.
