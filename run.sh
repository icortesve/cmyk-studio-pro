#!/usr/bin/env bash
echo "==================================================="
echo "  Iniciando CMYK Studio Pro (Separador Halftone)   "
echo "==================================================="
echo ""

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -d "venv/bin" ]; then
    echo "[INFO] Activando entorno virtual local 'venv'..."
    source venv/bin/activate
else
    echo "[ADVERTENCIA] No se encontró entorno 'venv'. Usando el Python global..."
fi

echo "[INFO] Verificando dependencias..."
pip install --quiet -r requirements.txt

echo ""
echo "[INFO] Lanzando servidor Streamlit..."
streamlit run app.py