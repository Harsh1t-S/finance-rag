# docs/

`test_answers.md` — the answers this app actually produced for all ten
assignment questions, written by `python run_test_questions.py --show-chunks`.
It records each answer, the source file and page behind it, the similarity score
of every retrieved chunk, and — for the multi-quarter questions — how many
distinct press releases retrieval actually reached.

That last number is the point. A comparison answered from three quarters reads
exactly like one answered from four. It was `top_k=6` reporting *3 of 4* that
caught the retriever missing Q1 FY2026 entirely, while the answer itself looked
completely normal. See the `top_k` section of the main README.

`screenshot-*.png` — the working app: indexing, a cross-quarter comparison, the
trap question being refused, and the FastAPI docs page.

Regenerate the answers with a valid `OPENAI_API_KEY` in `.env`:

```bash
python ingest.py
python run_test_questions.py --show-chunks
```
