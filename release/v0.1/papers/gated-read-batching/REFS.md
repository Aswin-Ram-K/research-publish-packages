# REFS.md — references, identifiers, and exactly what was verified

**The rule this file enforces.** No citation in `MANUSCRIPT.md` may come from memory. Every reference below
is either (a) re-verified by the authors of this manuscript during preparation, (b) verified by *direct fetch* in the source material
with the fetched URL recorded, or (c) marked `UNVERIFIED`/`NOT CITED`. Tiers are kept separate deliberately:
"the source said it fetched this" is weaker evidence than "I fetched this", and the difference is stated
rather than smoothed over.

**Verification date for the authors' own checks:** 2026-10-15 (UTC).

**Source of the verification not performed by the authors:** `docs/research/GATED_READ_PROVENANCE.md` (abbreviated **P**) in the
read-only source material (an external checkout; name and location withheld), in particular its §1 master table (`P:23-56`), its §4 batching
section (`P:193-232`), and its fetched-URL list (`P:259-272`).

**Source of the `G:` locators:** `docs/research/GATED_READ_2026.md` (abbreviated **G**, the run report) in the same read-only source material (name and location withheld).

---

## Tier A — re-verified for this manuscript in this session (2 refs)

Each of these was independently confirmed in this session with a fresh search that returned the primary
record or abstract. Queries and returned URLs are recorded verbatim.

| # | Reference | Identifier | How re-verified (2026-10-15) | Returned URL | Status |
|---|---|---|---|---|---|
| A1 | Lin, Diesendruck, Du & Abraham — *BatchPrompt: Accomplish More with Less* | arXiv:2309.00384 | `local_web_search` query: `arXiv 2309.00384 BatchPrompt prompting batched data longer contexts worse performance`; returned abstract contains the exact quoted sentence "prompting with batched data in longer contexts will inevitably lead to worse performance, compared to single-data prompting" | `https://arxiv.org/pdf/2309.00384.pdf` | **VERIFIED** |
| A2 | Cheng, Kasai & Yu — *Batch Prompting: Efficient Inference with Large Language Model APIs* | arXiv:2301.08721; EMNLP 2023 Industry Track | `local_web_search` query: `Batch Prompting multiple samples batch inference costs inverse linearly arXiv 2301.08721`; returned abstract contains "inference costs decrease almost inverse linearly with the number of samples in each batch" and "up to 5x with six samples in batch" | `https://aclanthology.org/2023.emnlp-industry.74` and `https://arxiv.org/pdf/2301.08721.pdf` | **VERIFIED** (arXiv ID and ACL venue both confirmed by the two returned records) |

These two carry the paper's central external contrast (the −4 to −18 point batching loss), so they were the
ones re-checked rather than trusted.

---

## Tier B — verified by direct fetch in the source material, not re-fetched here (11 cited refs)

The source provenance document states its method explicitly: sources were found with a local SearXNG
instance and the arXiv export API, then **fetched directly** and read; "Only URLs actually fetched and read
are listed"; house rule "no unverified DOIs" (`P:6-9`). It also records that **four arXiv IDs recalled from
memory were wrong** and were corrected by fetching the record (`P:11-15`), which is positive evidence that
these identifiers came from records rather than recall. The authors did **not** re-fetch them.

| # | Reference | Identifier recorded by the source | Source line | Status |
|---|---|---|---|---|
| B1 | Schick, Dwivedi-Yu, Dessì, Raileanu, Lomeli, Hambro, Zettlemoyer, Cancedda & Scialom — *Toolformer* | arXiv:2302.04761; NeurIPS 2023 proceedings | **P:25**, fetched URL `arxiv.org/abs/2302.04761` at **P:259** | VERIFIED-in-source |
| B2 | Parisi, Zhao & Fiedel — *TALM: Tool Augmented Language Models* | arXiv:2205.12255 | **P:26**, URL at **P:260** | VERIFIED-in-source |
| B3 | Asai, Wu, Wang, Sil & Hajishirzi — *Self-RAG* | arXiv:2310.11511 | **P:28**, URLs `arxiv.org/pdf/2310.11511`, `arxiv.org/abs/2310.11511` at **P:260** | ID VERIFIED-in-source; **venue UNVERIFIED** (see below) |
| B4 | Mallen et al. — *When Not to Trust Language Models* | arXiv:2212.10511; ACL 2023 | **P:29**, URL at **P:261** | VERIFIED-in-source |
| B5 | Jiang et al. — *FLARE / Active Retrieval Augmented Generation* | arXiv:2305.06983; EMNLP 2023 | **P:30**, URL at **P:261** | VERIFIED-in-source |
| B6 | Jeong, Baek, Cho, Hwang & Park — *Adaptive-RAG* | arXiv:2403.14403; NAACL 2024 | **P:31**, URL at **P:261** | VERIFIED-in-source |
| B7 | Ong, Almahairi, Wu, Chiang, Wu, Gonzalez, Kadous & Stoica — *RouteLLM* | arXiv:2406.18665; ICLR 2025 | **P:44**, URL `arxiv.org/abs+pdf/2406.18665` at **P:267** | VERIFIED-in-source |
| B8 | Chen, Zaharia & Zou — *FrugalGPT* | arXiv:2305.05176 | **P:45**, URL at **P:267** | VERIFIED-in-source |
| B9 | Rombaut — *Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures* | arXiv:2604.03515 | **P:47**, URL `arxiv.org/abs+html/2604.03515` at **P:269** | VERIFIED-in-source |
| B10 | Xiang et al. — *GuardAgent* | arXiv:2406.09187; ICML 2025 | **P:37**, URL at **P:263** | VERIFIED-in-source |
| B11 | Yue & Yao — *Efficient but Vulnerable* | Findings of ACL 2025; arXiv:2503.15551 | **P:54**, URLs `aclanthology.org/2025.findings-acl.245`, `arxiv.org/html/2503.15551` at **P:271** | VERIFIED-in-source |

**Caveat on Tier B.** These are as good as the source document's fetch discipline, which is explicitly
recorded and which caught four recalled-ID errors. The authors did not independently re-fetch them, and a
verifier who wants Tier-A confidence for the whole list should re-fetch each URL at `P:259-272`.

---

## Tier C — UNVERIFIED, and either omitted or flagged in text

| Reference/claim | Problem | Handling |
|---|---|---|
| Self-RAG **conference venue** | The source states the arXiv record carries no venue comment and an ICLR proceedings PDF appeared in a search result but was not fetched (**P:246**). | arXiv ID cited (B3); **no venue** is claimed anywhere in `MANUSCRIPT.md` or the reference list. |
| Berkeley Function-Calling Leaderboard **paper arXiv ID** | `[UNVERIFIED]` in the source; the official blog/site were fetched and support the claims, but the paper ID is unresolved (**P:241-243**). | **Not cited** in the manuscript at all. |
| "Greshake et al. **2022**" indirect-injection citation | The source found no 2022 preprint; the correct record is 2023 (AISec '23 @ CCS '23, DOI 10.1145/3605764.3623985) (`G:49-51`, `STAGED_EXTRACTION_PROVENANCE.md:30-42`). | **Not cited** — injection is out of this paper's scope (Section 6). If it is cited in a future revision, it must be the 2023 record. |
| "No prior art for per-file-read relevance gating" | The source marks this `[INFERENCE]`: it is **searched absence**, based on a 13-scaffold taxonomy plus harness docs — not a systematic review (**P:250**). | Carried into the manuscript **as** a searched absence (Section 2.4), not as a proof of novelty. |
| Anthropic tool-call safety classifier doc | `[NOT FOUND]` in the source (**P:244-245**). | **Not cited.** |

---

## Tier D — deliberately NOT cited, with reason

These appear in the source provenance but are not used in this manuscript. Listed so a reviewer can see the
omission was a scope decision, not an oversight.

| Reference | Why not cited |
|---|---|
| SayCan (arXiv:2204.01691) | adjacent but a ranking gate over robot skills, not a binary read gate; adds length without load |
| API-Bank (arXiv:2304.08244), Llama Guard (arXiv:2312.06674), ShieldAgent (arXiv:2503.22738), CaMeL (arXiv:2503.18813), ToolEmu (arXiv:2309.15817) | guard/benchmark refs; the present paper is not about safety gating, and the injection arm is out of scope |
| RoBatch (arXiv:2605.28268) | current framing of batching degradation; a candidate for a revision that adds a discussion of batch-size scaling, not needed for the measured claims here |
| SWE-agent (arXiv:2405.15793), RAFT (arXiv:2403.10131), aider repo map, GraphRAG, MemGPT, Cursor blog | file-selection machinery; the one taxonomy citation (B9) carries the gap claim without a citation pile |
| AgentDojo (arXiv:2406.13352), InjecAgent, MCPTox, Greshake et al. (2023) | injection measurement — explicitly out of scope (Section 6) |

---

## Summary counts

| | count |
|---|---|
| References cited in `MANUSCRIPT.md` | **13** (numbered 1–13) |
| Re-verified for this manuscript in this session (Tier A) | **2** |
| Verified in the source material by direct fetch (Tier B) | **11** |
| Cited identifiers that remain `UNVERIFIED` in any respect | **0** (Self-RAG's *venue* is unverified and is not claimed) |
| Source-material references deliberately not cited (Tier D) | 14 listed |
| Fabricated or reconstructed metadata | **0** — author lists are truncated to what the source carries rather than completed from memory |
