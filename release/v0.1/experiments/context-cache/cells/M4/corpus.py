#!/usr/bin/env python3
"""M4-EVICT — the pressure corpus, built **offline** (no network, no model).

Purpose
-------
Every cell measured before M4 ran *inside* the KV cache.  To find out what the
LRU does **past capacity** this module builds a corpus of distinct,
non-overlapping documents that, submitted one at a time, total more tokens than
the server's whole KV pool.

Construction rules (each one defends a measurement fact)
--------------------------------------------------------
1. **One document = one request**, sent as a two-message prompt: a salted
   invariant head (``system``) followed by one body (``user``).  That is the
   append-only shape of ``resextract.context.render`` — the same discipline the
   context-cache cells use — so a re-request is byte-identical to the first
   submission and can therefore be served from the radix cache.
2. **A 4-word (~4-token) salt is the first thing in the head**, and the body's
   first line carries the document id.  Two documents share *no* prefix, so a
   document's ``cached_tokens`` on first submission can only be its own.
3. **Bodies are generated from a per-document seeded PRNG over a fixed word
   pool**, so the corpus is reproducible byte-for-byte from this file alone, and
   two documents never share a long n-gram run.
4. **Size is expressed in the repo's own offline estimator**
   (``default_est_tokens`` = ceil(chars/4)), because the server's tokenizer is
   not available offline.  ``battery.py`` re-sizes nothing: it reads the
   *measured* ``prompt_tokens`` and keeps submitting until the measured
   cumulative pressure reaches the target ratio — the estimate only has to be
   close enough that the document *pool* is big enough, and the pool is capped
   at 300 documents by the unit card.

Usage
-----
    python corpus.py --docs 300 --target-tokens 8600 --out-dir .

writes ``corpus.jsonl`` (one document per line) and ``corpus_manifest.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]

# The offline estimator is the repo's own, so corpus sizing and the cells that
# pre-date M4 are talking about the same unit of "token".
import sys  # noqa: E402

sys.path.insert(0, str(REPO / "src"))
from resextract.context import default_est_tokens  # noqa: E402

SEED = 20261023

# Salts: four short words drawn deterministically per document.  The point is
# that the first ~4 tokens differ per document; the words themselves are
# arbitrary.
SALT_WORDS = (
    "alder", "basalt", "cobalt", "dahlia", "ember", "fathom", "garnet", "harbor",
    "indigo", "juniper", "kelvin", "lumen", "marlin", "nectar", "onyx", "pewter",
    "quartz", "ripple", "sable", "tundra", "umber", "vellum", "willow", "xenon",
    "yarrow", "zephyr", "amber", "birch", "cedar", "drift", "elm", "flint",
)

# A fixed pool of ordinary English words.  Prose-like, not entropy-like: the
# measurement cares about token counts, and repeated words tokenise the same way
# every time, so the pool does not affect the pressure arithmetic.
WORDS = (
    "the of and to in a is that for on with as by at from this be are or an it "
    "which not but its had has were when we they you can if will there their what "
    "about would all one after also more these two may then first any into only "
    "time new could than other some up out them such very well where most over "
    "between during under against while because both through before around again "
    "still however therefore although within without across among toward each "
    "system state window cache prefix token block server request response stream "
    "measure sample record field value mean median range spread depth budget "
    "policy chain node fold summary delta append pointer fork eviction capacity "
    "pool allocation pressure resident sequence order position interval boundary "
    "residual latency throughput prefill decode schedule budget threshold floor "
    "ceiling index column table report figure method result evidence claim "
    "material repository docket trace log line file path digest count total"
).split()

# Sentence frames keep the text readable and the length distribution narrow.
FRAMES = (
    "{a} {b} {c} {d} the {e} of {f} {g} {h}.",
    "In {a} {b}, the {c} {d} {e} {f} and {g} {h}.",
    "The {a} {b} {c} {d} {e} {f} {g} {h} {i}.",
    "{a} {b} {c} {d} {e} and {f} {g} {h} {i} {j}.",
    "When the {a} {b} {c} {d} {e}, {f} {g} {h} {i}.",
)


def salt_for(doc_id: str) -> str:
    """Four deterministic words, one per document."""

    rng = random.Random(f"{SEED}:{doc_id}")
    return " ".join(rng.sample(SALT_WORDS, 4))


def head_for(doc_id: str) -> str:
    """The invariant head: the salt is the *first* token run of the prompt."""

    return (
        f"[m4-{doc_id}] salt {salt_for(doc_id)}\n"
        f"Pressure corpus document {doc_id}. This message is the fixed head of "
        f"the document and never changes between submissions."
    )


def body_for(doc_id: str, target_tokens: int) -> str:
    """One document body sized to ``target_tokens`` by the offline estimator."""

    rng = random.Random(f"{SEED}:body:{doc_id}")
    target_chars = target_tokens * 4
    lines = [f"Document {doc_id} — section 1 of 1. Read only this document.\n"]
    length = len(lines[0])
    section = 1
    while length < target_chars:
        paragraph = []
        for _ in range(rng.randint(4, 7)):
            frame = rng.choice(FRAMES)
            slots = "abcdefghij"
            words = {slot: rng.choice(WORDS) for slot in slots}
            sentence = frame.format(**words)
            paragraph.append(sentence)
        if length + 1 >= target_chars:
            break
        chunk = " ".join(paragraph)
        if length + len(chunk) + 1 > target_chars:
            chunk = chunk[: target_chars - length - 1].rsplit(" ", 1)[0] + "."
            lines.append(chunk)
            length += len(chunk) + 1
            break
        lines.append(chunk)
        length += len(chunk) + 1
        section += 1
        if section % 6 == 0:
            # A document-specific marker every few sections: cheap insurance
            # that no two bodies can ever be mistaken for one another.
            marker = f"[{doc_id}.{section}]"
            lines.append(marker)
            length += len(marker) + 1
    body = "\n".join(lines)
    return body


def build_documents(n_docs: int, target_tokens: int) -> list[dict]:
    docs: list[dict] = []
    for index in range(1, n_docs + 1):
        doc_id = f"D{index:04d}"
        head = head_for(doc_id)
        body = body_for(doc_id, target_tokens)
        docs.append(
            {
                "doc_id": doc_id,
                "doc_index": index,
                "salt": salt_for(doc_id),
                "head": head,
                "body": body,
                "chars": len(head) + len(body),
                "est_tokens": default_est_tokens(head) + default_est_tokens(body),
                "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "head_sha256": hashlib.sha256(head.encode("utf-8")).hexdigest(),
            }
        )
    return docs


def messages_for(doc: dict) -> list[dict[str, str]]:
    """The append-only two-message prompt of one document."""

    return [
        {"role": "system", "content": doc["head"]},
        {"role": "user", "content": doc["body"]},
    ]


def note_messages_for(doc: dict, note_text: str) -> list[dict[str, str]]:
    """Append-note-at-delta-end: the document, then one note node.

    The first message is byte-identical to :func:`messages_for`, which is the
    discipline's whole claim: the fold is recorded by *adding* a node at the
    tail, never by rewriting the cacheable prefix.
    """

    return [*messages_for(doc), {"role": "assistant", "content": note_text}]


def note_text_for(doc: dict) -> str:
    """A deterministic ``APPEND_NOTE``-shaped note (same marker as budget.compact)."""

    summarises_through = hashlib.sha256(
        f"{doc['doc_id']}:{doc['body_sha256']}".encode("utf-8")
    ).hexdigest()[:16]
    return (
        f"[note] summarises nodes through {summarises_through}; "
        f"chain {doc['body_sha256'][:16]}\n\n"
        f"Folded head of document {doc['doc_id']}: the body above is the whole "
        f"document; this note records that it has been retained and pinned by "
        f"its content address."
    )


def write_corpus(docs: list[dict], out_dir: Path, target_tokens: int) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / "corpus.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, sort_keys=True, ensure_ascii=False) + "\n")
    manifest = {
        "unit": "M4-EVICT",
        "generator": "experiments/context-cache/cells/M4/corpus.py",
        "seed": SEED,
        "n_docs": len(docs),
        "target_tokens_per_doc": target_tokens,
        "estimator": "resextract.context.default_est_tokens (ceil(chars/4))",
        "total_est_tokens": sum(d["est_tokens"] for d in docs),
        "chars_total": sum(d["chars"] for d in docs),
        "salt_words_per_doc": 4,
        "distinct_head_sha256": len({d["head_sha256"] for d in docs}),
        "distinct_body_sha256": len({d["body_sha256"] for d in docs}),
        "corpus_sha256": hashlib.sha256(jsonl.read_bytes()).hexdigest(),
        "doc_ids": [d["doc_id"] for d in docs],
    }
    (out_dir / "corpus_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def load_corpus(path: Path) -> list[dict]:
    docs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            docs.append(json.loads(line))
    return docs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=int, default=300, help="pool size (cap 300)")
    parser.add_argument("--target-tokens", type=int, default=8600)
    parser.add_argument("--out-dir", type=Path, default=HERE)
    args = parser.parse_args()
    if args.docs > 300:
        raise SystemExit("the unit card caps the pool at 300 documents")
    docs = build_documents(args.docs, args.target_tokens)
    manifest = write_corpus(docs, args.out_dir, args.target_tokens)
    print(
        f"corpus: {manifest['n_docs']} docs, "
        f"{manifest['total_est_tokens']} est tokens, "
        f"{manifest['distinct_body_sha256']} distinct bodies, "
        f"{manifest['chars_total']} chars -> {args.out_dir / 'corpus.jsonl'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
