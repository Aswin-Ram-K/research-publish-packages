# CITATIONS.md — resolution record for the three `[CITATION NEEDED — verify]` markers

Unit `CITE-VERIFY`. Manuscript line numbers are those of
`papers/context-cache/MANUSCRIPT.md` **before and after** the unit (the file keeps 1214 lines
throughout; every edit replaced text inside an existing line).

Method: `web_search` (DeepSeek route) was unavailable in this session (no API key), so discovery ran
through the local SearXNG tool and each source was confirmed by fetching its own landing page
(abstract, title, id). No id, venue or author in this record is reconstructed from memory.

---

## Marker 1 — line 887 (`## 10a. Related work`, introduction)

**Was:** `This section is bounded by what could be verified **inside this workspace, without network
access**: … A citation is marked **verified** only when this package could name a source that was read
*in this workspace*; everything else is marked `[CITATION NEEDED — verify]` and must be resolved
against the primary source before submission.`

**Now (line 887):** `… A citation is marked **verified** only when this package could name a source
that was read *in this workspace*; everything else is marked
`[SGLang review of attention backends](https://docs.sglang.io/docs/advanced_features/attention_backend)`,
sources cited only when that package read them here (`R-SGL.md`, `R-VLLM.md`); any other pointer is
marked and resolved against the primary source as in 10a.1 and 10a.2.`

**Source named:** SGLang documentation, *Attention backends* —
<https://docs.sglang.io/docs/advanced_features/attention_backend> (official project documentation; no
arXiv id or DOI exists for it). It is the same URL the paper already cites on line 896 via
`docs/serving-options/R-SGL.md` row 1, so this line names no source the package had not already read.

**Why not a new marker-free claim:** the sentence at 887 is *methodological*, not a finding. It
describes the citation policy, so it cannot be "supported" by a paper; the honest fix is to make the
policy self-consistent after 10a.1 and 10a.2 stopped being unsupported. The two residual families
that stay uncited are named on the following two lines (888-889) exactly as before.

---

## Marker 2 — lines 906-907 (`### 10a.1 Prefix caching in the serving engines this paper ran`)

**Was:** `The papers that introduced the two engines (vLLM/PagedAttention; SGLang/RadixAttention)
`[CITATION NEEDED — verify]` — this workspace pins the engines' documentation and source, not their
papers.`

**Now (lines 906-907):** `introduced the two engines are known and are cited here:
**vLLM/PagedAttention** (Kwon et al., [arXiv:2309.06180](https://arxiv.org/abs/2309.06180);
SOSP 2023, [doi:10.1145/3600006.3613165](https://doi.org/10.1145/3600006.3613165)) and
**SGLang/RadixAttention** (Zheng et al., [arXiv:2312.07104](https://arxiv.org/abs/2312.07104)) —
both resolved`

| Field | vLLM / PagedAttention | SGLang / RadixAttention |
|---|---|---|
| Title | Efficient Memory Management for Large Language Model Serving with PagedAttention | SGLang: Efficient Execution of Structured Language Model Programs |
| Authors (first) | Woosuk Kwon et al. | Lianmin Zheng et al. |
| arXiv id | 2309.06180 | 2312.07104 |
| DOI | 10.1145/3600006.3613165 (SOSP '23) | — (DOI issued by arXiv only: 10.48550/arXiv.2312.07104) |
| URL | https://arxiv.org/abs/2309.06180 | https://arxiv.org/abs/2312.07104 |
| Confirmed via | arXiv abs page (abstract, title) + Crossref/Semantic Scholar record for the SOSP DOI | arXiv abs page (abstract, title) — "RadixAttention for KV cache reuse" is in the abstract |

**Note on the deleted clause:** the old line said the workspace pins "the engines' documentation and
source, **not their papers**". That is no longer true — both papers are now named — so the clause was
replaced rather than left in place as a false statement.

**Correction recorded (not applied — out of scope):** the journal version of the SGLang paper appears
in the ACL Anthology, not SOSP. The manuscript's prose is true (RadixAttention *was* introduced by
that paper), but a bibliography entry should name the ACL Anthology / PACMPL venue rather than
"arXiv preprint".

---

## Marker 3 — lines 911-912 (`### 10a.2 LLM-agent context management, compaction and summarisation`)

**Was:** `This is the family the compaction findings of Sections 4, 6 and 6a sit in.
`[CITATION NEEDED — verify]` **for the family as a whole**: this workspace's surveys … contain no
agent-memory or context-compaction reference in citable form, so no pointer is asserted here rather
than a plausible-looking one.`

**Now (lines 911-916):** `This is the family the compaction findings of Sections 4, 6 and 6a sit in;
**Parallel Context Compaction for Long-Horizon LLM Agent Serving** (Cim et al.,
[arXiv:2605.23296](https://arxiv.org/abs/2605.23296);
[doi:10.48550/arXiv.2605.23296](https://doi.org/10.48550/arXiv.2605.23296)) **for the family as a
whole** states this paper's own premise: compaction via LLM-based summarization keeps a growing
conversation bounded but is inherently lossy, so what an agent retains fluctuates across runs — the
one citable in-family statement this workspace can assert. Its surveys … carry no other agent-memory
source in citable form, so nothing further is asserted: what this paper contributes to that family is
the shape its own literature is least likely to have measured — most work compaction work reports
*task quality* at a fixed number of turns, whereas Section 6a drives eight arms …`

| Field | Value |
|---|---|
| Title | Parallel Context Compaction for Long-Horizon LLM Agent Serving |
| Authors | Musa Cim, Burak Topcu, Chita Das, Mahmut Taylan Kandemir |
| arXiv id | 2605.23296 (cs.AI) |
| DOI | 10.48550/arXiv.2605.23296 (arXiv-issued, DataCite) |
| URL | https://arxiv.org/abs/2605.23296 (submitted 22 May 2026, v1) |
| Confirmed via | arXiv abs page — title, authors, date, DOI all read from the page |

**Exact sentence it supports:** "context compaction via LLM-based summarization keeps the conversation
bounded, but summarization is inherently lossy", and "as context grows, … the information it retains
fluctuate[s] substantially from run to run, making the agent's retained knowledge unpredictable across
runs" — both are near-verbatim from that paper's abstract, and both describe the *family*, not this
paper's contribution.

**Boundary the edit deliberately keeps:** the manuscript's own contribution sentence ("most compaction
work reports *task quality* at a fixed number of turns, whereas Section 6a drives eight arms … and
reports the **uncached tokens per turn**") is **not** attributed to this source. This unit could not
verify a survey establishing that gap across the family, so the claim still stands as the paper's own
positioning statement, now flagged by the phrase "the shape its own literature is least likely to have
measured" rather than by a fabricated reference.

---

## Not done (reported, not guessed)

- No general survey of LLM-agent context compaction was verified. `GAPS.md` G16 and the surviving
  sentence in 10a.2 still say a full bibliography must be written before submission; that remains true.
- No number in the manuscript was changed by this unit.
