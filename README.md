# ⚡ Clipper AI — Generador Automático de Clips Virales 9:16

Herramienta open source desarrollada por **[UTKAI Solutions](https://utkai-solutions.utkai-solutions1.workers.dev/)** que transforma streams largos y videos de YouTube en clips verticales listos para **TikTok, Reels y YouTube Shorts**.

## ✨ Características principales
- **Análisis Multimodal Inteligente:** Detecta momentos de alta carga emocional (gritos, risas, sustos, reacciones épicas) usando **Gemini** con respaldo automático vía **Groq (Whisper + LLM)**.
- **Descarga Quirúrgica:** Descarga únicamente los fragmentos seleccionados con `yt-dlp` sin bajar directos completos de varias horas.
- **Diseño Picture-in-Picture (PiP) 1080×1920:** Detecta automáticamente la webcam del streamer y la encuadra en una tarjeta flotante con esquinas redondeadas y fondo ambiental difuminado.
- **Subtítulos Dinámicos:** Transcripción ultrarrápida con Groq Whisper quemada directamente en el video con FFmpeg.
- **Interfaz Web Local (BYOK):** Panel visual moderno donde cada usuario configura sus propias API Keys sin instalar Node.js.

## 🚀 Instalación rápida

### Requisitos previos
- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) instalado en el PATH del sistema.

### Pasos
```bash
git clone [https://github.com/utkaisolutions1-dot/clipper-ai.git](https://github.com/utkaisolutions1-dot/clipper-ai.git)
cd clipper-ai

python -m venv venv
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py