"""
Streamlit interface for the quarterly results research assistant.

    streamlit run app.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from config import DEFAULT_TOP_K, LLM_MODEL
from ingest import ingest_files, stats
from rag import answer_question

st.set_page_config(
    page_title="Quarterly Results Research Assistant",
    page_icon="📈",
    layout="wide",
)

SAMPLE_QUESTIONS = [
    "What was total revenue in the most recent quarter you loaded?",
    "Compare net profit across all the quarters you loaded. Which was highest?",
    "How did revenue in the latest quarter compare with the same quarter of the previous year?",
    "What did management say about the demand outlook or business environment?",
    "Which business segment or geography grew fastest, and by how much?",
    "What was the operating margin in each quarter, and is the trend rising or falling?",
    "Was any dividend declared? State the amount per share and the record date.",
    "What risks, headwinds, or challenges are mentioned in the documents?",
    "Give me a three-line summary of the latest quarter for a client email.",
    "What is the CEO's personal shareholding in 2015?",
]


# --- sidebar ---------------------------------------------------------------

with st.sidebar:
    st.header("Index status")
    try:
        s = stats()
        if s["total_chunks"]:
            st.metric("Chunks in store", s["total_chunks"])
            st.caption("Indexed documents")
            for name, count in s["documents"].items():
                st.write(f"• {name} — {count} chunks")
        else:
            st.info("Nothing indexed yet.")
        st.divider()
        st.caption(
            f"Embeddings: `{s['embedding_model']}`  \n"
            f"LLM: `{LLM_MODEL}`  \n"
            f"Chunk size: {s['chunk_size']} / overlap {s['chunk_overlap']}  \n"
            f"Store: `{s['persist_directory']}`"
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not read the collection: {exc}")

    st.divider()
    top_k = st.slider(
        "Chunks to retrieve (top_k)",
        min_value=2,
        max_value=12,
        value=DEFAULT_TOP_K,
        help=(
            "Cross-quarter comparisons need chunks from several PDFs at once. "
            "Below 5 they tend to come from a single quarter."
        ),
    )
    show_chunks = st.checkbox("Show retrieved chunks", value=False)


# --- header ----------------------------------------------------------------

st.title("Quarterly Results Research Assistant")
st.caption(
    "Ask about revenue, margins, dividends or management commentary. Answers "
    "come only from the indexed filings, with the source page cited."
)


# --- upload and index ------------------------------------------------------

with st.expander("Upload and index documents", expanded=not stats()["total_chunks"]):
    uploaded = st.file_uploader(
        "PDF files",
        type="pdf",
        accept_multiple_files=True,
        help="All quarterly PDFs go into the same collection.",
    )

    col_a, col_b = st.columns([1, 3])

    with col_a:
        index_clicked = st.button("Index uploaded files", type="primary")
    with col_b:
        default_clicked = st.button("Index the files in data/")

    if index_clicked:
        if not uploaded:
            st.warning("Choose at least one PDF first.")
        else:
            with st.spinner("Reading, chunking, embedding..."):
                tmpdir = Path(tempfile.mkdtemp())
                paths = []
                for f in uploaded:
                    p = tmpdir / f.name
                    p.write_bytes(f.getbuffer())
                    paths.append(p)
                try:
                    result = ingest_files(paths)
                    st.success(
                        f"{result['files']} files processed, "
                        f"{result['chunks']} chunks stored."
                    )
                    for row in result["detail"]:
                        st.write(
                            f"• {row['file']} — {row['pages']} pages, "
                            f"{row['chunks']} chunks"
                        )
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Indexing failed: {exc}")

    if default_clicked:
        pdfs = sorted(Path("data").glob("*.pdf"))
        if not pdfs:
            st.warning("No PDFs found in data/.")
        else:
            with st.spinner("Reading, chunking, embedding..."):
                try:
                    result = ingest_files(pdfs)
                    st.success(
                        f"{result['files']} files processed, "
                        f"{result['chunks']} chunks stored."
                    )
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Indexing failed: {exc}")


# --- ask -------------------------------------------------------------------

st.subheader("Ask a question")

picked = st.selectbox(
    "Sample questions from the assignment (optional)",
    ["—"] + SAMPLE_QUESTIONS,
    index=0,
)

default_text = "" if picked == "—" else picked
question = st.text_area("Question", value=default_text, height=90)

if st.button("Ask", type="primary"):
    if not question.strip():
        st.warning("Type a question first.")
    else:
        with st.spinner("Retrieving and answering..."):
            try:
                result = answer_question(question.strip(), top_k=top_k)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed: {exc}")
                result = None

        if result:
            st.markdown("### Answer")
            st.markdown(result["answer"])

            if result["sources"]:
                st.markdown("### Sources")
                for src in result["sources"]:
                    st.write(
                        f"• **{src['file']}** — page {src['page']} "
                        f"(similarity {src['similarity']})"
                    )

            if show_chunks and result["chunks"]:
                st.markdown("### Retrieved chunks")
                st.caption(
                    "What the model actually saw. If an answer is wrong, check "
                    "here before blaming GPT-4o."
                )
                for i, chunk in enumerate(result["chunks"], start=1):
                    with st.expander(
                        f"Chunk {i} — {chunk['file']} p.{chunk['page']} "
                        f"(similarity {chunk['similarity']})"
                    ):
                        st.text(chunk["text"])
