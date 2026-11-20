import os
import subprocess
from groq import Groq


def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_dynamic_subtitles(video_clip_path: str, ass_output_path: str) -> str:
    audio_path = video_clip_path.replace(".mp4", ".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_clip_path, "-vn", "-acodec", "libmp3lame", "-q:a", "4", audio_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    words = getattr(transcription, "words", [])

    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    chunk_size = 3

    for i in range(0, len(words), chunk_size):
        chunk = words[i : i + chunk_size]
        for j, active_word in enumerate(chunk):
            start_t = format_ass_time(active_word["start"])
            end_t = format_ass_time(
                chunk[j + 1]["start"] if j + 1 < len(chunk) else active_word["end"]
            )

            line_parts = []
            for k, w in enumerate(chunk):
                word_text = w["word"].strip().upper()
                if k == j:
                    line_parts.append(f"{{\\c&H0000FFFF&}}{word_text}{{\\c&H00FFFFFF&}}")
                else:
                    line_parts.append(word_text)

            events.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{' '.join(line_parts)}")

    with open(ass_output_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))

    if os.path.exists(audio_path):
        os.remove(audio_path)

    return ass_output_path