@echo off
TITLE CMYK Studio Pro - Launcher
echo ===================================================
echo   Iniciando CMYK Studio Pro (Separador Halftone)
echo ===================================================
echo.

cd /d "%~dp0"

IF EXIST "venv\Scripts\activate.bat" (
    echo [INFO] Activando entorno virtual local 'venv'...
    call venv\Scripts\activate.bat
) ELSE (
    echo [ADVERTENCIA] No se encontro entorno 'venv'. Ejecutando con el Python global...
)

echo [INFO] Verificando dependencias...
python -m pip install --quiet -r requirements.txt

echo.
echo [INFO] Lanzando servidor Streamlit...
streamlit run app.py

pause