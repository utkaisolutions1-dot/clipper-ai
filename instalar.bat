@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   Clipper AI Studio - Instalador para Windows
echo ==================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python en el sistema.
    echo Descargalo desde https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

python --version
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual .venv.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Entorno virtual .venv ya existe.
)

echo.
echo [2/3] Instalando dependencias de requirements.txt...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando archivo de configuracion .env...
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo Se creo .env a partir de .env.example.
    ) else (
        echo GEMINI_API_KEY=pega_aqui_tu_api_key_de_google_ai_studio> ".env"
        echo GROQ_API_KEY=pega_aqui_tu_api_key_de_groq>> ".env"
        echo Se creo .env base.
    )
) else (
    echo El archivo .env ya existe. No se sobrescribio.
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo.
    echo [AVISO] FFmpeg no fue detectado en tu PATH.
    echo Para generar clips en Windows sin Docker, instala FFmpeg:
    echo   winget install Gyan.FFmpeg
)

echo.
echo ==================================================
echo   Instalacion completada correctamente
echo ==================================================
echo.
echo IMPORTANTE: Antes de iniciar, abre el archivo .env
echo y pega tus API keys de Gemini y Groq:
echo   - Google AI Studio: https://aistudio.google.com/apikey
echo   - Groq Console:     https://console.groq.com/keys
echo.
echo Luego haz doble clic en "iniciar.bat".
echo.
pause
