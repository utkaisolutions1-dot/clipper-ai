@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual .venv.
    echo Ejecuta primero "instalar.bat" haciendo doble clic sobre el.
    echo.
    pause
    exit /b 1
)

echo ==================================================
echo   Iniciando Clipper AI Studio en localhost:8000
echo ==================================================
echo.
echo Abriendo el navegador en 2 segundos...
echo Deja esta ventana abierta para ver el progreso de los clips.
echo Para detener el servidor presiona Ctrl+C.
echo.

call ".venv\Scripts\activate.bat"

start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"
python -m uvicorn app:app --host 127.0.0.1 --port 8000

if errorlevel 1 (
    echo.
    echo [ERROR] El servidor se detuvo con un error.
    pause
)
