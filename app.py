import os
import re
import uuid
import threading
from typing import Dict, Any
from dotenv import load_dotenv, set_key
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from analyzer import analyze_video_url
from downloader import download_clip_section
from transcriber import generate_dynamic_subtitles
from renderer import render_vertical_clip

load_dotenv()

os.makedirs("temp", exist_ok=True)
os.makedirs("output_clips", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="Clipper AI Studio")

# Servir los clips renderizados para reproducirlos directo en el navegador
app.mount("/clips", StaticFiles(directory="output_clips"), name="clips")

# Almacén en memoria del estado de los trabajos en curso
JOBS: Dict[str, Dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    youtube_url: str
    num_clips: int = 5


class ConfigRequest(BaseModel):
    gemini_api_key: str = ""
    groq_api_key: str = ""


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")


def run_job_background(job_id: str, youtube_url: str, num_clips: int):
    job = JOBS[job_id]
    try:
        job["status"] = "analyzing"
        job["message"] = "Analizando video (emociones, audio y detección de cámara)..."
        job["progress"] = 10

        clips, facecam = analyze_video_url(youtube_url, total_clips=num_clips, chunk_minutes=40)
        total = len(clips)

        if total == 0:
            job["status"] = "error"
            job["message"] = "No se encontraron momentos virales en el video."
            return

        job["total_clips"] = total
        job["facecam_detected"] = bool(facecam and getattr(facecam, "has_facecam", False))
        job["status"] = "processing"
        job["progress"] = 25

        for idx, clip in enumerate(clips, start=1):
            safe_title = sanitize_filename(clip.title)[:35] or f"clip_{idx}"
            filename = f"{job_id[:6]}_{idx}_{safe_title}.mp4"
            raw_clip = os.path.join("temp", f"raw_{job_id[:6]}_{idx}.mp4")
            ass_file = os.path.join("temp", f"subs_{job_id[:6]}_{idx}.ass")
            final_clip = os.path.join("output_clips", filename)

            job["message"] = f"[{idx}/{total}] Descargando segmento: {clip.title}..."
            download_clip_section(youtube_url, clip.start_time, clip.end_time, raw_clip)

            job["message"] = f"[{idx}/{total}] Generando subtítulos dinámicos..."
            generate_dynamic_subtitles(raw_clip, ass_file)

            job["message"] = f"[{idx}/{total}] Renderizando vertical 9:16 (PiP)..."
            render_vertical_clip(raw_clip, ass_file, final_clip, facecam=facecam)

            # Publicar el clip al instante para que aparezca en la interfaz
            job["clips"].append({
                "title": clip.title,
                "hook_text": clip.hook_text,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "virality_score": clip.virality_score,
                "reason": clip.reason,
                "filename": filename,
                "url": f"/clips/{filename}",
            })
            job["progress"] = 25 + int((idx / total) * 75)

        job["status"] = "completed"
        job["progress"] = 100
        job["message"] = f"¡Listo! Se generaron {total} clips verticales."

    except Exception as e:
        job["status"] = "error"
        job["message"] = f"Error: {str(e)}"


@app.get("/")
def serve_home():
    return FileResponse("static/index.html")


@app.get("/api/config")
def get_config_status():
    return {
        "has_gemini": bool(os.getenv("GEMINI_API_KEY")),
        "has_groq": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/api/config")
def save_config(cfg: ConfigRequest):
    env_file = ".env"
    if not os.path.exists(env_file):
        open(env_file, "a").close()

    if cfg.gemini_api_key.strip():
        set_key(env_file, "GEMINI_API_KEY", cfg.gemini_api_key.strip())
        os.environ["GEMINI_API_KEY"] = cfg.gemini_api_key.strip()

    if cfg.groq_api_key.strip():
        set_key(env_file, "GROQ_API_KEY", cfg.groq_api_key.strip())
        os.environ["GROQ_API_KEY"] = cfg.groq_api_key.strip()

    return {"ok": True, "has_gemini": bool(os.getenv("GEMINI_API_KEY")), "has_groq": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/api/generate")
def start_generation(req: GenerateRequest):
    if not req.youtube_url.strip():
        raise HTTPException(status_code=400, detail="Debes pegar un enlace de YouTube válido.")
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=400, detail="Configura tus API Keys primero en el botón ⚙️ API Keys.")

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 5,
        "message": "Iniciando pipeline...",
        "total_clips": req.num_clips,
        "clips": [],
    }

    thread = threading.Thread(
        target=run_job_background,
        args=(job_id, req.youtube_url.strip(), max(1, min(20, req.num_clips))),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado.")
    return JOBS[job_id]


@app.get("/api/library")
def list_existing_clips():
    """Muestra los clips ya guardados en output_clips aunque recargues la página."""
    files = sorted(
        [f for f in os.listdir("output_clips") if f.endswith(".mp4")],
        key=lambda f: os.path.getmtime(os.path.join("output_clips", f)),
        reverse=True,
    )
    return {
        "clips": [
            {
                "title": f.replace(".mp4", "").replace("_", " "),
                "filename": f,
                "url": f"/clips/{f}",
            }
            for f in files
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Clipper AI Studio corriendo en: http://localhost:8000\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
    import os
import re
import uuid
import threading
from typing import Dict, Any
from dotenv import load_dotenv, set_key
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from analyzer import analyze_video_url
from downloader import download_clip_section
from transcriber import generate_dynamic_subtitles
from renderer import render_vertical_clip

load_dotenv()

os.makedirs("temp", exist_ok=True)
os.makedirs("output_clips", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="Clipper AI Studio")

# Servir los clips renderizados para reproducirlos directo en el navegador
app.mount("/clips", StaticFiles(directory="output_clips"), name="clips")

# Almacén en memoria del estado de los trabajos en curso
JOBS: Dict[str, Dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    youtube_url: str
    num_clips: int = 5


class ConfigRequest(BaseModel):
    gemini_api_key: str = ""
    groq_api_key: str = ""


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")


def run_job_background(job_id: str, youtube_url: str, num_clips: int):
    job = JOBS[job_id]
    try:
        job["status"] = "analyzing"
        job["message"] = "Analizando video (emociones, audio y detección de cámara)..."
        job["progress"] = 10

        clips, facecam = analyze_video_url(youtube_url, total_clips=num_clips, chunk_minutes=40)
        total = len(clips)

        if total == 0:
            job["status"] = "error"
            job["message"] = "No se encontraron momentos virales en el video."
            return

        job["total_clips"] = total
        job["facecam_detected"] = bool(facecam and getattr(facecam, "has_facecam", False))
        job["status"] = "processing"
        job["progress"] = 25

        for idx, clip in enumerate(clips, start=1):
            safe_title = sanitize_filename(clip.title)[:35] or f"clip_{idx}"
            filename = f"{job_id[:6]}_{idx}_{safe_title}.mp4"
            raw_clip = os.path.join("temp", f"raw_{job_id[:6]}_{idx}.mp4")
            ass_file = os.path.join("temp", f"subs_{job_id[:6]}_{idx}.ass")
            final_clip = os.path.join("output_clips", filename)

            job["message"] = f"[{idx}/{total}] Descargando segmento: {clip.title}..."
            download_clip_section(youtube_url, clip.start_time, clip.end_time, raw_clip)

            job["message"] = f"[{idx}/{total}] Generando subtítulos dinámicos..."
            generate_dynamic_subtitles(raw_clip, ass_file)

            job["message"] = f"[{idx}/{total}] Renderizando vertical 9:16 (PiP)..."
            render_vertical_clip(raw_clip, ass_file, final_clip, facecam=facecam)

            # Publicar el clip al instante para que aparezca en la interfaz
            job["clips"].append({
                "title": clip.title,
                "hook_text": clip.hook_text,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "virality_score": clip.virality_score,
                "reason": clip.reason,
                "filename": filename,
                "url": f"/clips/{filename}",
            })
            job["progress"] = 25 + int((idx / total) * 75)

        job["status"] = "completed"
        job["progress"] = 100
        job["message"] = f"¡Listo! Se generaron {total} clips verticales."

    except Exception as e:
        job["status"] = "error"
        job["message"] = f"Error: {str(e)}"


@app.get("/")
def serve_home():
    return FileResponse("static/index.html")


@app.get("/api/config")
def get_config_status():
    return {
        "has_gemini": bool(os.getenv("GEMINI_API_KEY")),
        "has_groq": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/api/config")
def save_config(cfg: ConfigRequest):
    env_file = ".env"
    if not os.path.exists(env_file):
        open(env_file, "a").close()

    if cfg.gemini_api_key.strip():
        set_key(env_file, "GEMINI_API_KEY", cfg.gemini_api_key.strip())
        os.environ["GEMINI_API_KEY"] = cfg.gemini_api_key.strip()

    if cfg.groq_api_key.strip():
        set_key(env_file, "GROQ_API_KEY", cfg.groq_api_key.strip())
        os.environ["GROQ_API_KEY"] = cfg.groq_api_key.strip()

    return {"ok": True, "has_gemini": bool(os.getenv("GEMINI_API_KEY")), "has_groq": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/api/generate")
def start_generation(req: GenerateRequest):
    if not req.youtube_url.strip():
        raise HTTPException(status_code=400, detail="Debes pegar un enlace de YouTube válido.")
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=400, detail="Configura tus API Keys primero en el botón ⚙️ API Keys.")

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 5,
        "message": "Iniciando pipeline...",
        "total_clips": req.num_clips,
        "clips": [],
    }

    thread = threading.Thread(
        target=run_job_background,
        args=(job_id, req.youtube_url.strip(), max(1, min(20, req.num_clips))),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado.")
    return JOBS[job_id]


@app.get("/api/library")
def list_existing_clips():
    """Muestra los clips ya guardados en output_clips aunque recargues la página."""
    files = sorted(
        [f for f in os.listdir("output_clips") if f.endswith(".mp4")],
        key=lambda f: os.path.getmtime(os.path.join("output_clips", f)),
        reverse=True,
    )
    return {
        "clips": [
            {
                "title": f.replace(".mp4", "").replace("_", " "),
                "filename": f,
                "url": f"/clips/{f}",
            }
            for f in files
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Clipper AI Studio corriendo en: http://localhost:8000\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)