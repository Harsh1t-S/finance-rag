# docs/

Generated output lands here. Nothing in this folder is committed except this
file, because everything else is the product of one particular run.

`test_answers.md` — written by `python run_test_questions.py --show-chunks`.
It records the system's actual answer to each of the ten assignment questions,
the source file and page behind every answer, the similarity score of each
retrieved chunk, and — for the multi-quarter questions — how many distinct
press releases retrieval actually reached.

That last number is the point. A comparison answered from a single quarter reads
exactly like one answered from four, so the check has to be mechanical rather
than editorial.

Regenerate it with a valid `OPENAI_API_KEY` in `.env`:

```bash
python ingest.py
python run_test_questions.py --show-chunks
```
