"""
Build the demo-video narration track with Piper TTS.

Generates one WAV per segment so they can be dropped onto a timeline
individually, plus a single continuous narration track with silence gaps
sized to match the on-screen action.

    python build_narration.py
"""

from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

VOICE = "en_US-lessac-medium.onnx"
OUT = Path("segments")
OUT.mkdir(exist_ok=True)

# (id, gap_after_seconds, text)
# gap_after is dead air for on-screen action: clicking, waiting for a response,
# restarting the app. Tuned so the whole thing lands just under three minutes.
SEGMENTS: list[tuple[str, float, str]] = [
    (
        "01_intro",
        0.6,
        "This is a retrieval augmented generation assistant over four "
        "consecutive quarters of Apple earnings press releases, filed with the "
        "S E C as exhibit ninety nine point one to Form eight K. An analyst "
        "asks a question in plain English and gets an answer with the source "
        "page cited, so every figure can be checked against the filing before "
        "it goes into a client note.",
    ),
    (
        "02_why",
        0.6,
        "I chose the press releases over Apple's consolidated financial "
        "statements deliberately. The statements are tables and nothing else. "
        "The press release carries the same tables plus the C E O and C F O "
        "commentary, the dividend declaration with its record date, and the "
        "risk language. Every test question has a home in it.",
    ),
    (
        "03_index",
        2.5,
        "Indexing all four PDFs. Text is extracted page by page, split at "
        "twelve hundred characters with two hundred overlap, embedded with text "
        "embedding three small, and stored in ChromaDB. Twelve hundred keeps "
        "the wide statement tables intact. At eight hundred they split mid "
        "table and the row labels detach from the figures.",
    ),
    (
        "04_confirm",
        1.0,
        "Four files, fifty chunks. All four quarters live in one collection, "
        "which is what makes cross quarter comparison possible.",
    ),
    (
        "05_persistence",
        3.5,
        "Stopping the app and restarting it. Chroma persists to disk, so the "
        "index survives. Still fifty chunks.",
    ),
    (
        "06_q1_setup",
        1.0,
        "First question. Compare net profit across all four quarters. This one "
        "needs chunks from four different documents at the same time.",
    ),
    (
        "07_q1_answer",
        2.0,
        "Twenty seven point five billion in the September quarter. Forty two "
        "point one billion in December. Twenty nine point six in March, twenty "
        "nine point eight in June. December is the highest, which is the "
        "seasonal pattern for the holiday iPhone cycle. Underneath, citations "
        "from all four filings with page numbers.",
    ),
    (
        "08_topk",
        2.5,
        "This is the failure mode worth showing. At a top k of three, all three "
        "chunks come from a single quarter, and the model answers the "
        "comparison from one document. The output looks completely normal. "
        "Nothing in it signals the problem. That is why the test script prints "
        "how many distinct quarters were actually retrieved for every "
        "comparison question.",
    ),
    (
        "09_q2",
        1.5,
        "Second question. Was a dividend declared, and what was the record "
        "date? Twenty seven cents per share, payable on the thirteenth of "
        "August, to shareholders of record as of the tenth. The record date is "
        "the detail an analyst actually needs, and it only appears in the press "
        "release, not the statements.",
    ),
    (
        "10_trap",
        1.5,
        "Now the refusal test. What is the C E O's personal shareholding in "
        "twenty fifteen? Nothing in these four documents touches Tim Cook's "
        "shareholding, and none of them covers twenty fifteen. Ungrounded, a "
        "model invents a plausible number. This one says the information is not "
        "available.",
    ),
    (
        "11_api",
        1.0,
        "The same logic is exposed as a FastAPI service with ingest, ask and "
        "stats endpoints. Ask returns the answer with the file and page behind "
        "every source.",
    ),
    (
        "12_outro",
        0.0,
        "Every figure traces to a cited page, and when the answer is not in the "
        "documents, the system says so.",
    ),
]


def synth(seg_id: str, text: str) -> Path:
    path = OUT / f"{seg_id}.wav"
    subprocess.run(
        ["piper", "-m", VOICE, "-f", str(path)],
        input=text.encode("utf-8"),
        check=True,
        capture_output=True,
    )
    return path


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    manifest = []
    cursor = 0.0
    concat_parts: list[str] = []

    for seg_id, gap, text in SEGMENTS:
        path = synth(seg_id, text)
        dur = duration(path)
        manifest.append(
            {
                "id": seg_id,
                "start": round(cursor, 2),
                "duration": round(dur, 2),
                "gap_after": gap,
                "text": text,
            }
        )
        print(f"{seg_id:<16} start {cursor:6.2f}s  len {dur:5.2f}s  gap {gap:.1f}s")
        concat_parts.append(str(path))
        cursor += dur + gap

    print(f"\nTotal narration timeline: {cursor:.1f}s ({cursor/60:.2f} min)")

    # Build one continuous track with the gaps baked in.
    filter_parts = []
    inputs = []
    for i, (seg_id, gap, _) in enumerate(SEGMENTS):
        inputs.extend(["-i", str(OUT / f"{seg_id}.wav")])
        pad_ms = int(gap * 1000)
        filter_parts.append(f"[{i}:a]apad=pad_dur={gap}[a{i}]" if pad_ms else f"[{i}:a]anull[a{i}]")
    concat_inputs = "".join(f"[a{i}]" for i in range(len(SEGMENTS)))
    filter_complex = (
        ";".join(filter_parts)
        + f";{concat_inputs}concat=n={len(SEGMENTS)}:v=0:a=1[out]"
    )

    subprocess.run(
        [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-ar", "44100", "-b:a", "192k",
            "narration_full.mp3",
        ],
        check=True,
        capture_output=True,
    )

    Path("narration_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("Wrote narration_full.mp3 and narration_manifest.json")


if __name__ == "__main__":
    main()
