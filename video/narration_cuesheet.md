# Finance RAG — narration cue sheet

Total: **176.7s**

| Start | Len | Segment | On screen |
|---|---|---|---|
| **0:00.00** | 19.5s | `01_intro` | App open, sidebar empty. Let it sit. |
| **0:20.12** | 17.6s | `02_why` | Show data/ folder with the four Apple PDFs, or the README source table. |
| **0:38.31** | 18.5s | `03_index` | Select all four PDFs, click Index. |
| **0:59.28** | 7.2s | `04_confirm` | Hover '4 files processed, 50 chunks stored'. |
| **1:07.50** | 6.2s | `05_persistence` | Terminal: Ctrl+C, restart, reload. Point at sidebar still showing 50. |
| **1:17.16** | 7.0s | `06_q1_setup` | Pick the net-profit comparison question. Don't click Ask yet. |
| **1:25.18** | 17.1s | `07_q1_answer` | Click Ask at START. Scroll to Sources, show citations from all four PDFs. |
| **1:44.30** | 18.2s | `08_topk` | Drag top_k slider to 3, re-Ask, show the answer now cites ONE quarter. Set back to 6. |
| **2:05.02** | 16.1s | `09_q2` | Ask the dividend question. Point at the record date. |
| **2:22.67** | 16.2s | `10_trap` | Ask the CEO shareholding question. Let the refusal render. |
| **2:40.35** | 9.4s | `11_api` | Cut to localhost:8000/docs, /ask, Try it out, Execute. |
| **2:50.75** | 6.0s | `12_outro` | Hold on the JSON or an answered question. |

---

## Narration text

**0:00.00 — 01_intro**

> This is a retrieval augmented generation assistant over four consecutive quarters of Apple earnings press releases, filed with the S E C as exhibit ninety nine point one to Form eight K. An analyst asks a question in plain English and gets an answer with the source page cited, so every figure can be checked against the filing before it goes into a client note.

**0:20.12 — 02_why**

> I chose the press releases over Apple's consolidated financial statements deliberately. The statements are tables and nothing else. The press release carries the same tables plus the C E O and C F O commentary, the dividend declaration with its record date, and the risk language. Every test question has a home in it.

**0:38.31 — 03_index**

> Indexing all four PDFs. Text is extracted page by page, split at twelve hundred characters with two hundred overlap, embedded with text embedding three small, and stored in ChromaDB. Twelve hundred keeps the wide statement tables intact. At eight hundred they split mid table and the row labels detach from the figures.

**0:59.28 — 04_confirm**

> Four files, fifty chunks. All four quarters live in one collection, which is what makes cross quarter comparison possible.

**1:07.50 — 05_persistence**

> Stopping the app and restarting it. Chroma persists to disk, so the index survives. Still fifty chunks.

**1:17.16 — 06_q1_setup**

> First question. Compare net profit across all four quarters. This one needs chunks from four different documents at the same time.

**1:25.18 — 07_q1_answer**

> Twenty seven point five billion in the September quarter. Forty two point one billion in December. Twenty nine point six in March, twenty nine point eight in June. December is the highest, which is the seasonal pattern for the holiday iPhone cycle. Underneath, citations from all four filings with page numbers.

**1:44.30 — 08_topk**

> This is the failure mode worth showing. At a top k of three, all three chunks come from a single quarter, and the model answers the comparison from one document. The output looks completely normal. Nothing in it signals the problem. That is why the test script prints how many distinct quarters were actually retrieved for every comparison question.

**2:05.02 — 09_q2**

> Second question. Was a dividend declared, and what was the record date? Twenty seven cents per share, payable on the thirteenth of August, to shareholders of record as of the tenth. The record date is the detail an analyst actually needs, and it only appears in the press release, not the statements.

**2:22.67 — 10_trap**

> Now the refusal test. What is the C E O's personal shareholding in twenty fifteen? Nothing in these four documents touches Tim Cook's shareholding, and none of them covers twenty fifteen. Ungrounded, a model invents a plausible number. This one says the information is not available.

**2:40.35 — 11_api**

> The same logic is exposed as a FastAPI service with ingest, ask and stats endpoints. Ask returns the answer with the file and page behind every source.

**2:50.75 — 12_outro**

> Every figure traces to a cited page, and when the answer is not in the documents, the system says so.
