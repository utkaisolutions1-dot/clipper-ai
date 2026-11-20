import os
import math
import time
import json
from typing import List, Optional
import yt_dlp
from groq import Groq
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError


class FacecamBox(BaseModel):
    has_facecam: bool = Field(description="True si hay una cámara superpuesta de un streamer/creador en alguna esquina o borde")
    x_min: float = Field(description="Coordenada izquierda normalizada (0.0 a 1.0) del recuadro de la cámara")
    y_min: float = Field(description="Coordenada superior normalizada (0.0 a 1.0) del recuadro de la cámara")
    x_max: float = Field(description="Coordenada derecha normalizada (0.0 a 1.0) del recuadro de la cámara")
    y_max: float = Field(description="Coordenada inferior normalizada (0.0 a 1.0) del recuadro de la cámara")


class ViralClip(BaseModel):
    title: str = Field(description="Título corto y llamativo para el nombre del archivo")
    hook_text: str = Field(description="Frase gancho corta (máx 6 palabras) para poner arriba del video")
    start_time: str = Field(description="Tiempo de inicio exacto respecto al video completo en formato HH:MM:SS")
    end_time: str = Field(description="Tiempo de fin exacto respecto al video completo en formato HH:MM:SS")
    virality_score: int = Field(description="Puntaje estimado de viralidad del 1 al 100")
    reason: str = Field(description="Emoción o reacción principal detectada (ej. grito, susto, risa, épico)")


class ClipsResponse(BaseModel):
    facecam: FacecamBox = Field(description="Ubicación exacta del recuadro de la cámara del streamer en pantalla")
    clips: List[ViralClip]


def get_video_duration(youtube_url: str) -> int:
    """Obtiene la duración total del video en segundos sin validar formatos de descarga."""
    cookie_path = "Cookies.txt" if os.path.exists("Cookies.txt") else ("cookies.txt" if os.path.exists("cookies.txt") else None)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
        "cookiefile": cookie_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return int(info.get("duration", 0))


def seconds_to_hhmmss(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_gemini_models(client) -> List[str]:
    """Obtiene modelos reales disponibles en la API Key actual."""
    try:
        models = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "gemini" in m.name and "embedding" not in m.name and "tts" not in m.name and "image" not in m.name
        ]
        flash = [m for m in models if "flash" in m and "lite" not in m]
        pro = [m for m in models if "pro" in m]
        ordered = []
        for candidate in ["gemini-3.8-flash", "gemini-3.8-pro"] + flash + pro:
            if candidate in models and candidate not in ordered:
                ordered.append(candidate)
        if ordered:
            return ordered[:3]
    except Exception:
        pass
    return ["gemini-3.8-flash"]


def get_groq_chat_models(groq_client: Groq) -> List[str]:
    """Detecta automáticamente los modelos de chat activos en tu cuenta de Groq."""
    excluded = ("whisper", "tts", "guard", "playai", "orpheus", "safeguard", "embed", "compound")
    try:
        all_models = [
            m.id for m in groq_client.models.list().data
            if not any(bad in m.id.lower() for bad in excluded)
        ]
        # Priorizar modelos grandes y rápidos más recientes
        priority_keywords = ("llama-4", "qwen", "gpt-oss", "llama-3.3", "deepseek", "70b", "versatile", "instruct")
        ranked = sorted(
            all_models,
            key=lambda name: next((i for i, kw in enumerate(priority_keywords) if kw in name.lower()), len(priority_keywords))
        )
        if ranked:
            return ranked[:5]
    except Exception:
        pass
    return ["llama-3.1-8b-instant"]


def fallback_analyze_via_groq(youtube_url: str, total_clips: int) -> tuple[List[ViralClip], Optional[FacecamBox]]:
    """Plan B infalible: descarga solo el audio ligero, transcribe con Whisper y detecta los clips con un LLM activo de Groq."""
    print("      [Plan B] Activando análisis ultrarrápido vía Groq (Whisper + LLM activo)...")
    os.makedirs("temp", exist_ok=True)
    audio_path = os.path.join("temp", "fallback_audio.m4a")
    cookie_path = "Cookies.txt" if os.path.exists("Cookies.txt") else ("cookies.txt" if os.path.exists("cookies.txt") else None)

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": audio_path,
        "overwrites": True,
        "cookiefile": cookie_path,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    with open(audio_path, "rb") as f:
        transcription = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )

    segments = getattr(transcription, "segments", []) or []
    transcript_lines = []
    for seg in segments:
        start_str = seconds_to_hhmmss(seg.get("start", 0))
        text = seg.get("text", "").strip()
        if text:
            transcript_lines.append(f"[{start_str}] {text}")

    # Limitar a ~22,000 caracteres para no exceder límites de tokens por minuto del plan gratuito
    full_transcript = "\n".join(transcript_lines)[:22000]

    prompt = f"""
    Eres un editor experto de TikTok y YouTube Shorts. Analiza esta transcripción con marcas de tiempo [HH:MM:SS]
    y extrae los {total_clips} momentos MÁS EMOCIONANTES, GRACIOSOS, INTENSOS O VIRALES.

    Reglas:
    - Cada clip debe durar entre 25 y 120 segundos.
    - Devuelve start_time y end_time exactos en formato HH:MM:SS.
    - Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
    {{
      "clips": [
        {{
          "title": "Titulo corto",
          "hook_text": "Gancho corto max 6 palabras",
          "start_time": "00:01:10",
          "end_time": "00:01:55",
          "virality_score": 92,
          "reason": "Reaccion intensa / risa / momento epico"
        }}
      ]
    }}

    Transcripción:
    {full_transcript}
    """

    candidate_models = get_groq_chat_models(groq_client)
    last_error = None

    for model_id in candidate_models:
        try:
            print(f"      -> Analizando transcripción con Groq ({model_id})...")
            chat = groq_client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            data = json.loads(chat.choices[0].message.content)
            clips = [ViralClip(**c) for c in data.get("clips", [])]
            if clips:
                clips.sort(key=lambda x: x.virality_score, reverse=True)
                return clips[:total_clips], None
        except Exception as e:
            print(f"      [Aviso] {model_id} falló ({type(e).__name__}). Probando siguiente modelo...")
            last_error = e

    raise RuntimeError(f"No se pudo completar el análisis con Groq: {last_error}")


def call_gemini_with_retry(client, contents, config):
    """Reintenta en modelos reales activos antes de activar el Plan B."""
    models_to_try = get_gemini_models(client)
    waits = [3, 6, 10]

    for attempt in range(3):
        model_name = models_to_try[min(attempt, len(models_to_try) - 1)]
        try:
            print(f"      -> Consultando modelo: {model_name} (intento {attempt + 1}/3)...")
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except (ServerError, ClientError) as e:
            code = getattr(e, "code", "503")
            print(f"      [Aviso] {model_name} saturado ({code}). Esperando {waits[attempt]}s...")
            time.sleep(waits[attempt])

    raise RuntimeError("GEMINI_SATURATED")


def analyze_video_url(youtube_url: str, total_clips: int = 12, chunk_minutes: int = 40):
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1)),
    )
    duration_sec = get_video_duration(youtube_url)
    chunk_sec = chunk_minutes * 60

    if duration_sec <= 45 * 60:
        num_chunks = 1
    else:
        num_chunks = math.ceil(duration_sec / chunk_sec)

    clips_per_chunk = max(1, math.ceil(total_clips / num_chunks))
    all_clips: List[ViralClip] = []
    detected_facecam: Optional[FacecamBox] = None

    print(f"   -> Duración detectada: {seconds_to_hhmmss(duration_sec)} | Dividido en {num_chunks} bloque(s).")

    try:
        for i in range(num_chunks):
            start_s = i * chunk_sec
            end_s = min((i + 1) * chunk_sec, duration_sec)
            start_str = seconds_to_hhmmss(start_s)
            end_str = seconds_to_hhmmss(end_s)

            if num_chunks > 1:
                print(f"   -> Analizando bloque {i + 1}/{num_chunks} ({start_str} a {end_str})...")

            prompt = f"""
            Analiza con atención tanto el AUDIO (tono de voz, gritos, risas, sustos, emoción, intensidad) como el VIDEO 
            del segmento entre {start_str} y {end_str} y extrae los {clips_per_chunk} momentos MÁS EMOCIONANTES Y VIRALES 
            para TikTok, Reels y YouTube Shorts.

            1. DETECCIÓN DE CÁMARA DEL STREAMER (facecam):
            - Observa si hay un recuadro de cámara donde aparece la persona/streamer (por ejemplo, en la esquina superior derecha, superior izquierda, inferior, etc.).
            - Devuelve en `facecam` las coordenadas normalizadas exactas (0.0 a 1.0) del RECUADRO COMPLETO de su cámara (incluyendo hombros y micrófono, no solo la cara). Si no hay webcam superpuesta, pon has_facecam=false.

            2. CRITERIOS DE SELECCIÓN EMOCIONAL:
            - Prioriza momentos de alta energía: cuando el creador reacciona con sorpresa, empieza a gritar, se asusta, se ríe a carcajadas, se emociona, se enfada por un fallo épico o vive una situación intensa/dramática.
            - Evita tramos aburridos, caminatas sin diálogo o pausas muertas.

            3. DURACIÓN Y TIEMPOS:
            - Cada clip debe durar entre 25 segundos y 120 segundos (hasta 2 minutos completos si la reacción, historia o jugada tiene desarrollo y remate que lo justifique).
            - Devuelve start_time y end_time en formato HH:MM:SS respecto al video completo (dentro de {start_str} - {end_str}).
            - Empieza justo antes del detonante/gancho y cierra justo después de la reacción final.
            """

            video_part = types.Part(
                file_data=types.FileData(file_uri=youtube_url),
                video_metadata=types.VideoMetadata(
                    start_offset=f"{start_s}s",
                    end_offset=f"{end_s}s",
                ),
            )

            response = call_gemini_with_retry(
                client=client,
                contents=types.Content(parts=[video_part, types.Part(text=prompt)]),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ClipsResponse,
                    temperature=0.45,
                ),
            )

            chunk_result = ClipsResponse.model_validate_json(response.text)
            if chunk_result.facecam.has_facecam and detected_facecam is None:
                detected_facecam = chunk_result.facecam

            all_clips.extend(chunk_result.clips)

            if i < num_chunks - 1:
                time.sleep(3)

        all_clips.sort(key=lambda x: x.virality_score, reverse=True)
        return all_clips[:total_clips], detected_facecam

    except Exception as e:
        if "GEMINI_SATURATED" in str(e) or "503" in str(e):
            return fallback_analyze_via_groq(youtube_url, total_clips)
        raise