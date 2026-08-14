# 🎨 CMYK Studio Pro — Separador Halftone & Fine Art

**CMYK Studio Pro** es una aplicación interactiva desarrollada en Python y Streamlit orientada a la preparación técnica de imágenes para serigrafía, risografía y técnicas de impresión Fine Art. Permite realizar la separación cromática CMYK, aplicar tramas de medios tonos (*halftone*) personalizables, simular el comportamiento visual de las tintas y exportar fotolitos listos para insolvado/quemado de mallas.

---

## 🚀 Características Principales

- **Separación de Color CMYK:** Conversión matemática precisa desde espacio de color RGB a canales C, M, Y, K.
- **Transformación de Imagen:** Rotación acumulativa en pasos de 90°, espejos horizontal y vertical, y control de brillo/contraste.
- **Tramado de Medios Tonos (*Halftone*):**
  - Ajuste de frecuencia de trama (LPI - *Lines Per Inch*).
  - Geometrías de punto configurables: *Circular*, *Líneas* y *Elíptica*.
  - Ángulos de inclinación oficiales para evitar el patrón de interferencia **Moiré** (Roseta).
- **Control de Calce / Registro:** Adición automática de cruces de registro técnico en las cuatro esquinas con etiquetas identificadoras de canal.
- **Simulación Analógica:** Opción de simular descalces mecánicos (*off-register*) para acabados estilo risografía o imprenta retro.
- **Visualización Simultánea y Conmutabilidad de Tintas:**
  - Inspección en tiempo real de los 4 fotolitos individuales en blanco y negro.
  - Previsualización combinada con activación/desactivación dinámica de canales de tinta.
- **Exportación Técnica Profesional:**
  - Exportación individual de fotolitos en formato PNG a 300 DPI.
  - Exportación en **PDF Multi-Página** (1 fotolito por hoja a tamaño completo).
  - Exportación en **PDF Hoja de Muestra** (Grilla 2x2 para catálogo y control de calidad).

---

## 🛠️ Tecnologías Utilizadas

- **Python 3.10+**
- **Streamlit** (Interfaz de usuario y reactividad)
- **NumPy** (Procesamiento matricial y manipulación de canales)
- **Pillow / PIL** (Procesamiento de imágenes y generación de PDFs)

---

## 🔧 Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/cmyk-studio-pro.git](https://github.com/TU_USUARIO/cmyk-studio-pro.git)
   cd cmyk-studio-pro