# UVER32 — independent verification of UNEUTRAL9 (whole-class neutralisation)
Status: DONE (21/25 tool calls). OVERALL: partial. Bound: 25 tool calls. Write paths: strategy/VERIFICATION_REPORT_32.md, orchestration/units/UVER32.md, orchestration/handoffs/UVER32.json, scratch/uver32/**.
Claims tested: 1 tokens/renames, 2 exit codes, 3 moved diagnostics, 4 unchanged diagnostics, 5 census split, 6 MANIFEST, 7 paper citations, 8 mechanism. Plus: residual system vocabulary.

## Verdict summary
REPRODUCED: 6177 occ / 17-of-29 files; exit codes 1-0/0-0/0-0; all 7 moved diagnostics; all unchanged
diagnostics + digest c7696edc...; census 1390->83 (1083/13->26/2, 265->57, 42->0); manifest 0/0/0/0/0 with
manifest_self 9656d35a... verified; mechanism supported by compare.py:16/21/27/31.
CONTRADICTED: residual is 1 not 0 (ANSWER, verify/recompute-claims.py:117); in-stimulus residual is 2 distinct
not 1 (MATERIALISE + broker/Broker); UNEUTRAL8's 'exit 0 / ALL CLAIM NUMBERS PRESERVED: True' fails on its own
tree (byte-identical to before_pkg, exits 1).
OVERSTATED: paper-delta list misses submission/main.tex:194,334, GAPS.md:19, DISCLOSURE_CHANGES.md:143,
EVIDENCE_NOTES.md:279-280; 'all values measured' table omits disagreements_where_routeA_backs_record 5->4.
Report: strategy/VERIFICATION_REPORT_32.md
