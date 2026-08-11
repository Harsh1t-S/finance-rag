"""
Retrieval and answering.

Question -> embedding -> nearest chunks from Chroma -> prompt -> GPT-4o.
The model only ever sees the retrieved chunks, never the full documents.
"""

from __future__ import annotations

from openai import OpenAI

from config import (
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    LLM_MODEL,
    TEMPERATURE,
    require_api_key,
)
from ingest import get_collection

# The refusal instruction is the single most important line in this file.
# Without it GPT-4o will happily invent a penalty clause that sounds exactly
# like a real one, which is the specific failure mode the trap question tests.
SYSTEM_PROMPT = """\
You are an equity research assistant at an investment advisory firm.

Answer ONLY from the context provided below. The context is extracted from
quarterly earnings press releases filed by the company with the SEC.

Rules:
1. If the context does not contain the answer, reply exactly: "That information
   is not available in the uploaded documents." Do not guess, do not use general
   knowledge, and do not fill a gap with a figure you happen to know. An analyst
   will act on this and an invented number is worse than no answer.
   This applies to facts that are absent, not to arithmetic. If the context
   carries the figures a question needs but not the derived quantity itself --
   a growth rate, a margin, a change between two periods -- work it out from
   those figures and show the inputs you used. Refusing to divide two numbers
   that are both on the page in front of you is a wrong answer, not a careful
   one.
2. Always state which fiscal quarter each figure belongs to. "Revenue was $109.4
   billion" is useless without the quarter attached.
3. Cite the document name and page number inline for each fact you assert,
   in the form [Document name, p. N].
4. Quote exact figures, percentages and dates as they appear. Never round a
   number that is stated precisely, and never convert currencies.
5. When comparing quarters, only compare quarters actually present in the
   context. If the context is missing a quarter needed for the comparison, say
   which one is missing rather than inferring it.
6. Distinguish clearly between what the company reported and what management
   said. Attribute quotes to the named executive.
"""


def _format_context(documents: list[str], metadatas: list[dict]) -> str:
    """Label every chunk so the model can cite it accurately."""
    blocks = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        blocks.append(
            f"[Chunk {i}] Source: {meta['source']} | Page: {meta['page']}\n{doc}"
        )
    return "\n\n---\n\n".join(blocks)


def retrieve(question: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """Embed the question and pull the nearest chunks out of Chroma."""
    collection = get_collection()
    if collection.count() == 0:
        return {"documents": [], "metadatas": [], "distances": []}

    client = OpenAI(api_key=require_api_key())
    query_vector = (
        client.embeddings.create(model=EMBEDDING_MODEL, input=[question])
        .data[0]
        .embedding
    )

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    return {
        "documents": result["documents"][0],
        "metadatas": result["metadatas"][0],
        "distances": result["distances"][0],
    }


def answer_question(question: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """
    Full RAG round trip.

    Returns the answer, the sources behind it, and the raw retrieved chunks so
    the UI can show what the model actually saw. Being able to inspect
    retrieval is what turns "the answer is wrong" into a fixable problem.
    """
    retrieved = retrieve(question, top_k=top_k)

    if not retrieved["documents"]:
        return {
            "answer": (
                "No documents have been indexed yet. Upload the PDFs and press "
                "Index first."
            ),
            "sources": [],
            "chunks": [],
        }

    context = _format_context(retrieved["documents"], retrieved["metadatas"])

    client = OpenAI(api_key=require_api_key())
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n\n{context}\n\n---\n\nQuestion: {question}",
            },
        ],
    )
    answer = completion.choices[0].message.content.strip()

    # De-duplicate sources to one row per (file, page) pair, preserving the
    # order the retriever ranked them in.
    seen: set[tuple[str, int]] = set()
    sources: list[dict] = []
    for meta, dist in zip(retrieved["metadatas"], retrieved["distances"]):
        key = (meta["source"], meta["page"])
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "file": meta["source"],
                "page": meta["page"],
                "similarity": round(1 - dist, 4),
            }
        )

    chunks = [
        {
            "file": meta["source"],
            "page": meta["page"],
            "similarity": round(1 - dist, 4),
            "text": doc,
        }
        for doc, meta, dist in zip(
            retrieved["documents"], retrieved["metadatas"], retrieved["distances"]
        )
    ]

    return {"answer": answer, "sources": sources, "chunks": chunks}
