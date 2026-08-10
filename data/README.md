# Data

Four consecutive quarters of Apple Inc. earnings press releases, each filed with
the SEC as Exhibit 99.1 to a Form 8-K.

| File | Quarter ended | Accession |
|---|---|---|
| `Apple_Q4_FY2025_Earnings_Press_Release.pdf` | 27 Sep 2025 | 0000320193-25-000077 |
| `Apple_Q1_FY2026_Earnings_Press_Release.pdf` | 27 Dec 2025 | 0000320193-26-000005 |
| `Apple_Q2_FY2026_Earnings_Press_Release.pdf` | 28 Mar 2026 | 0000320193-26-000011 |
| `Apple_Q3_FY2026_Earnings_Press_Release.pdf` | 27 Jun 2026 | 0000320193-26-000018 |

Regenerate them from the primary source with `python fetch_data.py`.

SEC filings are published as HTML, so these were rendered to PDF with
`wkhtmltopdf`. Text is unmodified; page breaks are the renderer's.
