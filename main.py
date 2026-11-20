import os
import re
from dotenv import load_dotenv
from analyzer import analyze_video_url
from downloader import download_clip_section
from transcriber import generate_dynamic_subtitles
from renderer import render_vertical_clip

load_dotenv()


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")


def run_pipeline(youtube_url: str, num_clips: int = 12):
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output_clips", exist_ok=True)

    print(f"1. Analizando video (emociones, reacciones y cámara) para extraer {num_clips} clips...")
    clips, facecam = analyze_video_url(youtube_url, total_clips=num_clips, chunk_minutes=40)
    print(f"   -> {len(clips)} momentos virales seleccionados.")
    if facecam and facecam.has_facecam:
        print(f"   -> Cámara del streamer ubicada en: ({facecam.x_min:.2f}, {facecam.y_min:.2f}) a ({facecam.x_max:.2f}, {facecam.y_max:.2f})")

    for idx, clip in enumerate(clips, start=1):
        safe_title = sanitize_filename(clip.title)[:35]
        print(f"\n[{idx}/{len(clips)}] Procesando: '{clip.title}' ({clip.start_time} - {clip.end_time}) | Score: {clip.virality_score}/100")

        raw_clip = os.path.join("temp", f"raw_{idx}.mp4")
        ass_file = os.path.join("temp", f"subs_{idx}.ass")
        final_clip = os.path.join("output_clips", f"{idx}_{safe_title}.mp4")

        download_clip_section(youtube_url, clip.start_time, clip.end_time, raw_clip)
        generate_dynamic_subtitles(raw_clip, ass_file)
        render_vertical_clip(raw_clip, ass_file, final_clip, facecam=facecam)

        print(f"   -> Listo: {final_clip}")

    print("\nProceso completado. Revisa la carpeta 'output_clips'.")


if __name__ == "__main__":
    url = input("Pega el link de YouTube (video o directo largo): ").strip()
    cantidad = input("¿Cuántos clips quieres generar? (ej. 8, 12, 16): ").strip()
    num_clips = int(cantidad) if cantidad.isdigit() and int(cantidad) > 0 else 12
    run_pipeline(url, num_clips=num_clips)