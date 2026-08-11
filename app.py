"""
Streamlit interface for the quarterly results research assistant.

    streamlit run app.py

Styling and HTML fragments live in ui.py so this file stays a readable sequence
of what the interface actually does.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

import ui
from config import CHUNK_OVERLAP, CHUNK_SIZE, DEFAULT_TOP_K, EMBEDDING_MODEL, LLM_MODEL
from ingest import ingest_files, stats
from rag import answer_question

st.set_page_config(
    page_title="Quarterly Results Research Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(ui.CSS, unsafe_allow_html=True)

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

# Answers accumulate rather than replacing one another, so an analyst can compare
# across questions instead of losing the previous answer on every submission.
if "history" not in st.session_state:
    st.session_state.history = []

try:
    store = stats()
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not read the collection: {exc}")
    st.stop()

indexed = store["total_chunks"] > 0


# --- sidebar ---------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="side-h">Index status</div>', unsafe_allow_html=True)
    st.markdown(ui.status_pill(indexed, store["total_chunks"]), unsafe_allow_html=True)

    if indexed:
        st.markdown('<div class="side-h">Indexed filings</div>', unsafe_allow_html=True)
        for name, count in store["documents"].items():
            st.markdown(
                f'<div class="doc-item"><div class="doc-name">{name}</div>'
                f'<div class="doc-meta">{count} chunks</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="side-h">Configuration</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="kv"><span>Embeddings</span><span>{EMBEDDING_MODEL}</span></div>'
        f'<div class="kv"><span>Answering</span><span>{LLM_MODEL}</span></div>'
        f'<div class="kv"><span>Chunk size</span><span>{CHUNK_SIZE}</span></div>'
        f'<div class="kv"><span>Overlap</span><span>{CHUNK_OVERLAP}</span></div>'
        f'<div class="kv"><span>Temperature</span><span>0.0</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-h">Retrieval</div>', unsafe_allow_html=True)
    top_k = st.slider(
        "Chunks to retrieve (top_k)",
        min_value=2,
        max_value=14,
        value=DEFAULT_TOP_K,
        help=(
            "Cross-quarter comparisons need chunks from several filings at once. "
            "Below 8 they tend to miss a quarter entirely."
        ),
    )
    show_chunks = st.checkbox("Show retrieved chunks", value=False)

    st.caption(f"Store: `{store['persist_directory']}`")


# --- header ----------------------------------------------------------------

st.markdown(
    ui.hero(
        "Retrieval augmented generation",
        "Quarterly Results Research Assistant",
        "Ask about revenue, margins, dividends or management commentary. Every "
        "answer is drawn only from the indexed filings and carries the document "
        "and page it came from, so an analyst can verify it before it reaches a "
        "client.",
    ),
    unsafe_allow_html=True,
)

st.markdown(
    ui.stat_strip(
        [
            ("Chunks indexed", str(store["total_chunks"]), f"{CHUNK_SIZE} / {CHUNK_OVERLAP} overlap"),
            ("Filings", str(len(store["documents"])), "quarterly press releases"),
            ("Retrieval", f"top_k {top_k}", "cosine similarity"),
            ("Answering", "GPT-4o", "temperature 0"),
        ]
    ),
    unsafe_allow_html=True,
)


# --- upload and index ------------------------------------------------------

with st.expander("Upload and index documents", expanded=not indexed):
    uploaded = st.file_uploader(
        "PDF files",
        type="pdf",
        accept_multiple_files=True,
        help="All quarterly PDFs go into the same collection.",
    )

    col_a, col_b = st.columns([1, 2])
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

st.markdown("### Ask a question")

picked = st.selectbox(
    "Sample questions from the assignment (optional)",
    ["—"] + SAMPLE_QUESTIONS,
    index=0,
)
question = st.text_area(
    "Question",
    value="" if picked == "—" else picked,
    height=95,
    placeholder="e.g. Compare net profit across all the quarters you loaded.",
)

ask_clicked = st.button("Ask", type="primary", disabled=not indexed)

if not indexed:
    st.info(
        "Nothing is indexed yet, so there is nothing to answer from. Open "
        "**Upload and index documents** above — the Ask button unlocks once the "
        "collection has chunks in it."
    )

if ask_clicked:
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
            st.session_state.history.insert(
                0, {"question": question.strip(), "result": result}
            )


def render_answer(entry: dict, *, latest: bool) -> None:
    """One question and its answer, as a card."""
    result = entry["result"]

    with st.container(border=True):
        label = "Answer" if latest else "Earlier answer"
        st.markdown(f'<div class="ans-head">{label}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ask-echo">{entry["question"]}</div>', unsafe_allow_html=True
        )
        st.markdown(result["answer"])

        if result["sources"]:
            st.markdown(
                ui.sources_block(result["sources"], unit_plural="filings"),
                unsafe_allow_html=True,
            )

        if show_chunks and result["chunks"]:
            st.markdown("")
            st.caption(
                "What the model actually saw. If an answer is wrong, check here "
                "before blaming GPT-4o."
            )
            for i, chunk in enumerate(result["chunks"], start=1):
                with st.expander(
                    f"Chunk {i} — {chunk['file']} p.{chunk['page']} "
                    f"(similarity {chunk['similarity']})"
                ):
                    st.text(chunk["text"])


for n, entry in enumerate(st.session_state.history):
    render_answer(entry, latest=(n == 0))

# Rendered after the answers so it appears on the same run that produces one,
# rather than only after the next interaction.
if st.session_state.history:
    if st.button("Clear answers"):
        st.session_state.history = []
        st.rerun()
