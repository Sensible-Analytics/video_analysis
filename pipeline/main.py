#!/usr/bin/env python3

from pathlib import Path
from typing import Dict, List

from .utils import (
    list_local_videos,
    AUDIO_DIR,
    TRANSCRIPT_DIR,
    clean_text,
    chunk_text_by_words,
    read_text_file,
)
from .audio import extract_audio
from .transcript import transcribe_audio
from .llm import build_llm_prompt_for_chunk, call_local_llm, safe_parse_json, CHUNK_WORD_TARGET
from .diagrams import normalize_mermaid, DiagramSpec
from .slides import render_reveal_html, slides_output_path


def process_video_file(video_path: Path):
    video_id = video_path.stem
    print(f"\n[INFO] Processing video: {video_id}")

    final_html = slides_output_path(video_id)
    if final_html.exists():
        print(f"[SKIP] Slides already exist → {final_html}")
        return

    # Audio
    wav = AUDIO_DIR / f"{video_id}.wav"
    if wav.exists():
        print(f"[SKIP] Audio already exists → {wav}")
    else:
        wav = extract_audio(video_path)

    # Transcript
    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"
    if transcript_path.exists():
        print(f"[SKIP] Transcript already exists → {transcript_path}")
    else:
        transcript_path = transcribe_audio(wav)
        if transcript_path is None or not transcript_path.exists():
            print(f"[ERROR] No transcript produced for {video_id}")
            return

    print(f"[INFO] Using transcript → {transcript_path}")

    # Read + chunk
    raw = read_text_file(transcript_path)
    cleaned = clean_text(raw)
    chunks = chunk_text_by_words(cleaned, CHUNK_WORD_TARGET)
    total_chunks = len(chunks)
    print(f"[INFO] Generating slides from {total_chunks} chunks")

    slides: List[Dict] = []

    for idx, chunk in enumerate(chunks, start=1):
        print(f"[INFO] Chunk {idx}/{total_chunks}")
        prompt = build_llm_prompt_for_chunk(chunk, video_id, idx, total_chunks)
        llm_out = call_local_llm(prompt)

        if not llm_out:
            print(f"[WARN] Empty LLM output for chunk {idx}")
            continue

        parsed = safe_parse_json(llm_out)
        if not parsed:
            print(f"[WARN] JSON parse failed for chunk {idx}")
            continue

        diagram_spec: DiagramSpec | None = None
        diagram_type = (parsed.get("diagram_type") or "none").lower()
        mermaid_raw = parsed.get("mermaid") or ""

        if diagram_type != "none":
            diagram_spec = normalize_mermaid(diagram_type, mermaid_raw)
            if not diagram_spec:
                print(f"[WARN] Invalid Mermaid for chunk {idx}, skipping diagram")

        slide = {
            "title": parsed.get("title", ""),
            "bullets": parsed.get("bullets", []),
            "notes": parsed.get("notes", ""),
            "diagram": diagram_spec,
        }
        slides.append(slide)

    if not slides:
        print(f"[ERROR] No slides generated for {video_id}")
        return

    render_reveal_html(slides, f"Lecture {video_id}", final_html)


def main():
    videos = list_local_videos()
    for video_path in videos:
        try:
            process_video_file(video_path)
        except Exception as e:
            print(f"[ERROR] processing {video_path}: {e}")


if __name__ == "__main__":
    main()
