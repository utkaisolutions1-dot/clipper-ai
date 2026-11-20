import os
import yt_dlp


def download_clip_section(youtube_url: str, start_time: str, end_time: str, output_path: str) -> str:
    """Descarga únicamente el segmento exacto del clip en hasta 1080p sin bajar el video entero."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    base_path = output_path.replace(".mp4", "")
    cookie_path = "Cookies.txt" if os.path.exists("Cookies.txt") else ("cookies.txt" if os.path.exists("cookies.txt") else None)

    ydl_opts = {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "outtmpl": f"{base_path}.%(ext)s",
        "merge_output_format": "mp4",
        "download_ranges": yt_dlp.utils.download_range_func(None, [(time_to_sec(start_time), time_to_sec(end_time))]),
        "force_keyframes_at_cuts": True,
        "cookiefile": cookie_path,
        "overwrites": True,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    return output_path


def time_to_sec(t_str: str) -> int:
    parts = [int(p) for p in t_str.strip().split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]
