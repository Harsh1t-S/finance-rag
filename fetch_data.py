"""
Re-download the four quarterly earnings press releases from SEC EDGAR.

    python fetch_data.py

The PDFs are committed to data/ already; this exists so the corpus is
reproducible and so the provenance of each file is explicit and checkable.
Each source is Exhibit 99.1 to a Form 8-K -- the earnings press release.
"""

import subprocess
from pathlib import Path

# SEC asks automated clients to identify themselves. Put your own contact here.
UA = "Harshit Sharma harshitkrsharma07@gmail.com"
BASE = "https://www.sec.gov/Archives/edgar/data/320193"

FILINGS = {
    "Apple_Q4_FY2025_Earnings_Press_Release": "000032019325000077/a8-kex991q4202509272025.htm",
    "Apple_Q1_FY2026_Earnings_Press_Release": "000032019326000005/a8-kex991q1202612272025.htm",
    "Apple_Q2_FY2026_Earnings_Press_Release": "000032019326000011/a8-kex991q2202603282026.htm",
    "Apple_Q3_FY2026_Earnings_Press_Release": "000032019326000018/a8-kex991q3202606272026.htm",
}


def main() -> None:
    data = Path("data")
    raw = Path("data/_raw")
    data.mkdir(exist_ok=True)
    raw.mkdir(exist_ok=True)

    for name, path in FILINGS.items():
        htm = raw / f"{name}.htm"
        pdf = data / f"{name}.pdf"
        print(f"{name} ...")
        subprocess.run(
            ["curl", "-s", "--max-time", "60", "-A", UA, f"{BASE}/{path}", "-o", str(htm)],
            check=True,
        )
        # SEC publishes filings as HTML; render to PDF so the pipeline gets a
        # real PDF with a clean text layer.
        subprocess.run(
            ["wkhtmltopdf", "--quiet", "--enable-local-file-access", "--page-size", "A4",
             "--margin-top", "15mm", "--margin-bottom", "15mm", str(htm), str(pdf)],
            check=True,
        )
        print(f"  -> {pdf}")

    print("\nDone. Now run: python ingest.py")


if __name__ == "__main__":
    main()
