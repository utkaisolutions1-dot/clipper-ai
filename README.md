# ⚡ Clipper AI Studio — De streams a Shorts 9:16

Herramienta **open source** desarrollada por **[UTKAI Solutions](https://utkai-solutions.utkai-solutions1.workers.dev)** que convierte directos largos y videos de YouTube en **Shorts verticales (9:16)** listos para **TikTok, Instagram Reels y YouTube Shorts**.

## 1. ¿Qué hace Clipper AI?

- **Detección multimodal con Gemini:** Analiza picos de audio, risas, sustos y reacciones épicas para localizar los mejores momentos sin tener que descargar el directo completo.
- **Descarga quirúrgica (`yt-dlp`):** Baja únicamente los fragmentos seleccionados para ahorrar tiempo, ancho de banda y espacio en disco.
- **Encuadre vertical 9:16 con Picture-in-Picture (Facecam):** Detecta y encuadra automáticamente la cámara del streamer usando **MediaPipe / OpenCV** sobre un fondo ambiental difuminado en `1080×1920`.
- **Subtítulos dinámicos con Groq Whisper + FFmpeg:** Transcribe el audio a gran velocidad con **Groq Whisper** y quema subtítulos de alto contraste directamente en el video final con **FFmpeg**.
- **Interfaz web local (`http://localhost:8000`):** Panel visual intuitivo para pegar enlaces, monitorear el progreso y reproducir o descargar los clips generados.

---

## 2. Paso previo obligatorio — Obtener API Keys gratuitas

Clipper AI funciona bajo el modelo **BYOK** (*Bring Your Own Key*): tus claves se guardan únicamente en tu computadora dentro del archivo `.env`. Ambas plataformas ofrecen un nivel gratuito:

1. **Google AI Studio (Gemini):**
   - Entra a **[https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)**
   - Inicia sesión con tu cuenta de Google, haz clic en **Create API key** y copia la clave generada.

2. **Groq Console (Whisper + respaldo):**
   - Entra a **[https://console.groq.com/keys](https://console.groq.com/keys)**
   - Inicia sesión, haz clic en **Create API Key**, asígnale un nombre y copia la clave generada.

---

## 3. Opción 1: Instalación fácil en Windows (Para Streamers y Editores sin experiencia técnica)

### Paso 1: Descargar el proyecto
1. En esta página de GitHub, haz clic en el botón verde **`<> Code`** y selecciona **`Download ZIP`**.
2. Descomprime el archivo `.zip` en una carpeta fácil de encontrar (por ejemplo, en tu Escritorio o Documentos).

### Paso 2: Requisitos previos
1. **Python 3.10 o superior:**
   - Descárgalo desde [python.org/downloads](https://www.python.org/downloads/).
   - **MUY IMPORTANTE:** Al abrir el instalador, marca la casilla **"Add python.exe to PATH"** en la parte inferior antes de hacer clic en *Install Now*.
2. **FFmpeg:**
   - Abre **PowerShell** en Windows y ejecuta este comando rápido:
     ```powershell
     winget install Gyan.FFmpeg
     ```
   - Cuando termine, cierra y vuelve a abrir cualquier terminal para que reconozca el comando.

### Paso 3: Instalar dependencias
- Entra a la carpeta descomprimida de `clipper-ai` y haz doble clic en **`instalar.bat`**.
- Este script creará automáticamente el entorno virtual `.venv`, instalará todas las librerías necesarias y generará tu archivo `.env`.

### Paso 4: Configurar tus claves e iniciar
1. Abre el archivo **`.env`** con el **Bloc de notas** (Notepad).
2. Pega tus dos claves reemplazando los textos de ejemplo:
   ```env
   GEMINI_API_KEY=tu_clave_de_google_ai_studio
   GROQ_API_KEY=tu_clave_de_groq
   ```
3. Guarda el archivo (`Ctrl + S`) y ciérralo.
4. Haz doble clic en **`iniciar.bat`**.
   - Se abrirá automáticamente **`http://localhost:8000`** en tu navegador.
   - **No cierres la ventana negra (consola) mientras uses la herramienta**, ya que ahí se ejecuta el servidor y se muestra el progreso en tiempo real. Para detenerlo al terminar, cierra la ventana o presiona `Ctrl + C`.

---

## 4. Opción 2: Ejecución con Docker (Para Desarrolladores)

Si ya tienes **Docker Desktop** (o Docker Engine + Compose) instalado, puedes levantar todo el entorno con FFmpeg y dependencias listas en un solo paso:

1. Clona el repositorio y entra a la carpeta:
   ```bash
   git clone https://github.com/utkaisolutions1-dot/clipper-ai.git
   cd clipper-ai
   ```

2. Crea tu archivo de variables de entorno y configura tus API keys:
   ```bash
   cp .env.example .env
   ```
   *(En Windows PowerShell: `Copy-Item .env.example .env`)*
   Edita `.env` con tu `GEMINI_API_KEY` y `GROQ_API_KEY`.

3. Construye y levanta el contenedor:
   ```bash
   docker compose up -d --build
   ```

4. Abre **`http://localhost:8000`** en tu navegador.
   Los videos exportados se guardarán automáticamente en tu carpeta local **`./output_clips`**.

### Comandos útiles de Docker
- Ver los logs en tiempo real:
  ```bash
  docker compose logs -f
  ```
- Detener el servicio:
  ```bash
  docker compose down
  ```

---

## 5. Solución de problemas frecuentes

- **`ERR_CONNECTION_REFUSED` al abrir `http://localhost:8000`:**
  El servidor local no está encendido o cerraste la ventana negra de la consola. Vuelve a hacer doble clic en **`iniciar.bat`** (o ejecuta `docker compose up -d` si usas Docker) y recarga la página.

- **"Python no se reconoce como un comando interno o externo":**
  Al instalar Python faltó marcar **"Add python.exe to PATH"**. Desinstala o repara Python desde el instalador oficial asegurándote de marcar esa casilla, o reinicia tu PC si acabas de instalarlo.

- **Error relacionado con FFmpeg al procesar video o audio:**
  Verifica que FFmpeg esté instalado abriendo PowerShell y ejecutando `ffmpeg -version`. Si no responde, instálalo con `winget install Gyan.FFmpeg` y abre una nueva ventana antes de volver a ejecutar `iniciar.bat`.

---

Desarrollado por **[UTKAI Solutions](https://utkai-solutions.utkai-solutions1.workers.dev)** · [https://utkai-solutions.utkai-solutions1.workers.dev](https://utkai-solutions.utkai-solutions1.workers.dev)
