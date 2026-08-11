"""
Central configuration for the Apple quarterly earnings RAG system.

Every tunable lives here so that ingest.py, rag.py, app.py and the FastAPI
service all agree on chunk sizes, model names and where Chroma stores itself.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- paths -----------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# --- chunking --------------------------------------------------------------
# 1200 characters is the top of the range the brief allows. Apple's earnings
# press releases are dominated by financial tables -- the condensed statements
# of operations, and the segment and product-category breakdowns. At 800
# characters those tables split mid-column and the retriever returns a fragment
# with the row labels detached from the figures, which is worse than useless
# for "compare net profit across the quarters". At 1200 each table survives
# inside a single chunk.
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

# --- models ----------------------------------------------------------------

# The defaults are what the brief mandates. They are overridable from .env only
# so the same code can run through an OpenAI-compatible gateway, which requires
# provider-prefixed slugs (openai/gpt-4o) for the identical models. The OpenAI
# SDK picks up OPENAI_BASE_URL from the environment on its own, so nothing below
# the config layer changes.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
TEMPERATURE = 0.0

# --- retrieval -------------------------------------------------------------
# The comparison questions need the net income line from four separate filings
# in one context window, so top_k has to be large enough to span four documents
# rather than two.
#
# Measured on "compare net profit across all the quarters you loaded":
#   top_k=6  -> 3 of 4 quarters (Q1 FY2026 missing)
#   top_k=8  -> 4 of 4 quarters
#
# At 6 the answer was confidently wrong: it named Q3 FY2026 at $29,789M as the
# highest, because Q1 FY2026 at $42,097M was never retrieved. Nothing in the
# output signalled the omission, which is why run_test_questions.py reports the
# retrieval spread for every multi-quarter question.
# 8 is the value with evidence behind it: it is the smallest that reaches all
# four filings on the comparison questions.
#
# It was raised to 10 and then 12 in an attempt to rescue the commentary
# question ("what did management say about the demand outlook"), which retrieves
# financial tables and no CEO or CFO quotes and then correctly refuses. Neither
# helped, so it is back at 8 rather than carrying a larger context window that
# buys nothing. Eight of the fifty chunks do contain the quotes, all on page 1
# of the four releases; plain semantic similarity simply ranks the statements
# tables above them for that phrasing. See the README.
DEFAULT_TOP_K = 8

COLLECTION_NAME = "apple_quarterly_results"

# --- API key ---------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def require_api_key() -> str:
    """Fail loudly and early rather than deep inside an OpenAI call."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and put your "
            "key in it, or export OPENAI_API_KEY in your shell."
        )
    return OPENAI_API_KEY
