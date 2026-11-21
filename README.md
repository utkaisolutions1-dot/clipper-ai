# ⚡ Clipper AI Studio — De streams a Shorts 9:16

Herramienta open source desarrollada por **[UTKAI Solutions](https://utkai-solutions.utkai-solutions1.workers.dev/)** para **creadores, streamers y editores**. Transforma directos largos y videos de YouTube en clips verticales `1080×1920` listos para **TikTok, Instagram Reels y YouTube Shorts**.

## ✨ ¿Qué hace Clipper AI?

- **Detección multimodal con Gemini:** Analiza momentos de alta carga emocional (reacciones épicas, risas, sustos, picos de audio) sin tener que descargar todo el directo.
- **Descarga quirúrgica (`yt-dlp`):** Extrae únicamente los fragmentos seleccionados para ahorrar tiempo y espacio en disco.
- **Encuadre vertical 9:16 con Facecam PiP:** Detecta la cámara del streamer y la ubica en formato *Picture-in-Picture* con fondo difuminado.
- **Subtítulos dinámicos con Groq Whisper + FFmpeg:** Transcribe el audio a gran velocidad y quema subtítulos de alto contraste directo en el video final (`output_clips/`).
- **Interfaz web local en `http://localhost:8000`:** Panel visual para pegar enlaces, seguir el progreso en tiempo real y reproducir o descargar tus clips.

---

## 🔑 Paso previo: Consigue tus API Keys gratis

Clipper AI utiliza el modelo **BYOK** (*Bring Your Own Key*): tus claves se guardan únicamente en tu archivo local `.env`.

1. **Google AI Studio (Gemini):** Obtén tu clave gratis en [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. **Groq Console (Whisper + respaldo):** Obtén tu clave gratis en [console.groq.com/keys](https://console.groq.com/keys)

---

## 🐳 Opción 1: Ejecución con Docker (Recomendada)

Ideal si ya tienes **Docker Desktop** instalado y quieres olvidarte de instalar Python o FFmpeg manualmente.

1. Copia `.env.example` a `.env` y pega tus dos API keys:
   ```bash
   cp .env.example .env
   ```
   *(En Windows PowerShell: `Copy-Item .env.example .env`)*

2. Levanta el contenedor:
   ```bash
   docker compose up -d --build
   ```

3. Abre tu navegador en **`http://localhost:8000`**.
   Todos los clips generados se guardarán automáticamente en tu carpeta local **`./output_clips`**.

Para detenerlo cuando termines:
```bash
docker compose down
```

---

## 🪟 Opción 2: Instalación rápida en Windows (Doble clic)

Pensada para usarla directo en Windows sin complicaciones de terminal:

1. **Requisitos previos:**
   - [Python 3.10 o superior](https://www.python.org/downloads/) *(marca "Add Python to PATH" al instalar)*.
   - [FFmpeg](https://ffmpeg.org/download.html) en tu PATH *(puedes instalarlo rápido en PowerShell con `winget install Gyan.FFmpeg`)*.

2. **Instalar:**
   Haz doble clic en **`instalar.bat`**. Este script creará el entorno virtual `.venv`, instalará todas las librerías de `requirements.txt` y generará tu archivo `.env`.

3. **Configurar tus claves:**
   Abre el archivo **`.env`** con el Bloc de notas y pega tu `GEMINI_API_KEY` y tu `GROQ_API_KEY`.

4. **Iniciar:**
   Haz doble clic en **`iniciar.bat`**. Se abrirá automáticamente **`http://localhost:8000`** en tu navegador y verás el progreso de cada clip en la consola.
