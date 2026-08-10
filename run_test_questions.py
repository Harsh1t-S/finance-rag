"""
Run all ten assignment questions against the indexed collection and write the
answers to docs/test_answers.md, ready to paste into the README.

    python ingest.py            # index first
    python run_test_questions.py

Add --show-chunks to also dump which chunks were retrieved for each question,
which is what you look at when an answer comes out wrong.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from config import CHUNK_OVERLAP, CHUNK_SIZE, DEFAULT_TOP_K, EMBEDDING_MODEL, LLM_MODEL
from ingest import stats
from rag import answer_question

QUESTIONS: list[tuple[str, str]] = [
    ("Single quarter", "What was total revenue in the most recent quarter you loaded?"),
    ("Comparison", "Compare net profit across all the quarters you loaded. Which was highest?"),
    ("Year on year", "How did revenue in the latest quarter compare with the same quarter of the previous year?"),
    ("Commentary", "What did management say about the demand outlook or business environment?"),
    ("Segment", "Which business segment or geography grew fastest, and by how much?"),
    ("Trend", "What was the operating margin in each quarter, and is the trend rising or falling?"),
    ("Dividend", "Was any dividend declared? State the amount per share and the record date."),
    ("Risk", "What risks, headwinds, or challenges are mentioned in the documents?"),
    ("Summary", "Give me a three-line summary of the latest quarter for a client email."),
    ("Trap", "What is the CEO's personal shareholding in 2015?"),
]

# Question kinds whose answer is only correct if retrieval reached more than one
# press release. Tracked mechanically because a single-document answer to these
# looks entirely normal on the page.
MULTI_QUARTER = {"Comparison", "Year on year", "Trend"}


def main() -> None:
    show_chunks = "--show-chunks" in sys.argv

    s = stats()
    if not s["total_chunks"]:
        print("Nothing indexed. Run `python ingest.py` first.")
        raise SystemExit(1)

    out = Path("docs")
    out.mkdir(exist_ok=True)
    target = out / "test_answers.md"

    lines: list[str] = [
        "# Test question results",
        "",
        f"Generated {datetime.now():%d %B %Y, %H:%M}",
        "",
        f"- Chunks indexed: **{s['total_chunks']}** "
        f"({', '.join(f'{k}: {v}' for k, v in s['documents'].items())})",
        f"- Chunk size / overlap: **{CHUNK_SIZE} / {CHUNK_OVERLAP}**",
        f"- Embeddings: `{EMBEDDING_MODEL}` · LLM: `{LLM_MODEL}` · top_k: **{DEFAULT_TOP_K}**",
        "",
        "---",
        "",
    ]

    for n, (kind, question) in enumerate(QUESTIONS, start=1):
        print(f"[{n}/10] {kind}: {question[:60]}...")
        result = answer_question(question, top_k=DEFAULT_TOP_K)

        lines.append(f"## Q{n} — {kind}")
        lines.append("")
        lines.append(f"**Question:** {question}")
        lines.append("")
        lines.append("**Answer:**")
        lines.append("")
        lines.append(result["answer"])
        lines.append("")

        if result["sources"]:
            lines.append("**Sources retrieved:**")
            lines.append("")
            for src in result["sources"]:
                lines.append(
                    f"- `{src['file']}` page {src['page']} "
                    f"(similarity {src['similarity']})"
                )
            lines.append("")

        files_hit = {src["file"] for src in result["sources"]}
        if kind in MULTI_QUARTER:
            # Reading the answer will not reveal this failure: if retrieval only
            # reached one press release, GPT-4o still produces a fluent
            # comparison and simply omits the quarters it never saw.
            verdict = (
                f"{len(files_hit)} of 4 quarters retrieved"
                if len(files_hit) > 1
                else "ONE DOCUMENT ONLY — check top_k"
            )
            lines.append(f"**Retrieval spread:** {verdict}")
            lines.append("")

        if show_chunks:
            lines.append("<details><summary>Retrieved chunks</summary>")
            lines.append("")
            for i, chunk in enumerate(result["chunks"], start=1):
                lines.append(
                    f"**Chunk {i}** — {chunk['file']} p.{chunk['page']} "
                    f"(similarity {chunk['similarity']})"
                )
                lines.append("")
                lines.append("```")
                lines.append(chunk["text"])
                lines.append("```")
                lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWritten to {target}")


if __name__ == "__main__":
    main()
