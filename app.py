import io
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
import streamlit as st

# ------------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CMYK Studio Pro — Fine Art & Halftone",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎨 CMYK Studio Pro — Separador Halftone & Fine Art")

# Estado de sesión para la rotación acumulativa (90° por cada clic)
if "angle_rotation" not in st.session_state:
    st.session_state.angle_rotation = 0

# ------------------------------------------------------------------------------
# 1. FUNCIONES NÚCLEO: CMYK, HALFTONE, CRUCES DE CALCE Y PDF
# ------------------------------------------------------------------------------
def rgb_to_cmyk(image_np):
    """Convierte matriz RGB (0-255) a canales CMYK (0.0 - 1.0)."""
    rgb = image_np.astype(float) / 255.0
    k = 1.0 - np.max(rgb, axis=2)
    
    k_mask = k < 1.0
    c = np.zeros_like(k)
    m = np.zeros_like(k)
    y = np.zeros_like(k)
    
    c[k_mask] = (1.0 - rgb[:, :, 0][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    m[k_mask] = (1.0 - rgb[:, :, 1][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    y[k_mask] = (1.0 - rgb[:, :, 2][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    
    return c, m, y, k


def generate_halftone_channel(channel_data, angle_deg, lpi, dpi=300, dot_shape='circular'):
    """Genera la trama de medios tonos para un canal específico."""
    height, width = channel_data.shape
    grid_period = dpi / lpi
    
    x = np.arange(width)
    y = np.arange(height)
    xx, yy = np.meshgrid(x, y)
    
    rad = np.radians(angle_deg)
    rot_x = xx * np.cos(rad) - yy * np.sin(rad)
    rot_y = xx * np.sin(rad) + yy * np.cos(rad)
    
    if dot_shape == 'line':
        mod_x = np.abs((rot_x % grid_period) - (grid_period / 2.0)) / (grid_period / 2.0)
        halftone = mod_x < channel_data
    elif dot_shape == 'elliptical':
        mod_x = (rot_x % grid_period) - (grid_period / 2.0)
        mod_y = (rot_y % grid_period) - (grid_period / 2.0)
        dist = np.sqrt((mod_x * 0.7)**2 + (mod_y * 1.3)**2) / (grid_period / 2.0)
        halftone = dist < channel_data
    else:  # circular
        mod_x = (rot_x % grid_period) - (grid_period / 2.0)
        mod_y = (rot_y % grid_period) - (grid_period / 2.0)
        dist = np.sqrt(mod_x**2 + mod_y**2) / (grid_period / 2.0)
        halftone = dist < channel_data
        
    return halftone.astype(float)


def apply_misregistration(channel_matrix, shift_x, shift_y):
    """Simula el descalce mecánico (Off-Register) para acabado analógico."""
    return np.roll(channel_matrix, shift=(shift_y, shift_x), axis=(0, 1))


def add_registration_marks(pil_image, margin=40, size=15, label=""):
    """Agrega cruces de registro/calce y una etiqueta identificadora al pie."""
    w, h = pil_image.size
    new_w, new_h = w + 2 * margin, h + 2 * margin + (30 if label else 0)
    
    canvas = Image.new("RGB", (new_w, new_h), (255, 255, 255))
    canvas.paste(pil_image, (margin, margin))
    
    draw = ImageDraw.Draw(canvas)
    centers = [
        (margin // 2, margin // 2),                  # Superior Izquierda
        (new_w - margin // 2, margin // 2),          # Superior Derecha
        (margin // 2, new_h - margin // 2 - (30 if label else 0)),  # Inferior Izquierda
        (new_w - margin // 2, new_h - margin // 2 - (30 if label else 0)) # Inferior Derecha
    ]
    
    for cx, cy in centers:
        draw.ellipse([cx - size//2, cy - size//2, cx + size//2, cy + size//2], outline="black", width=2)
        draw.line([cx - size, cy, cx + size, cy], fill="black", width=2)
        draw.line([cx, cy - size, cx, cy + size], fill="black", width=2)
        
    if label:
        draw.text((margin, new_h - 25), f"FOTOLITO TÉCNICO: {label}", fill="black")
        
    return canvas


def generate_pdf_multipage(fotolitos_images):
    """Exporta los 4 fotolitos en un PDF de 4 páginas (1 por página)."""
    pdf_buffer = io.BytesIO()
    
    # Convertir todas a RGB para compatibilidad de PDF
    rgb_images = [img.convert('RGB') for img in fotolitos_images]
    
    # Guardar primera imagen y anexar el resto como páginas
    rgb_images[0].save(
        pdf_buffer, 
        format="PDF", 
        save_all=True, 
        append_images=rgb_images[1:],
        resolution=300.0
    )
    return pdf_buffer.getvalue()


def generate_pdf_grid(fotolitos_dict, angles):
    """Exporta los 4 fotolitos juntos en una sola página (Grilla 2x2)."""
    # Tomar dimensiones base de una imagen
    sample_img = list(fotolitos_dict.values())[0]
    w, h = sample_img.size
    
    margin = 40
    grid_w = (w * 2) + (margin * 3)
    grid_h = (h * 2) + (margin * 3) + 60
    
    canvas = Image.new("RGB", (grid_w, grid_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    positions = {
        'C': (margin, margin),
        'M': (w + margin * 2, margin),
        'Y': (margin, h + margin * 2),
        'K': (w + margin * 2, h + margin * 2)
    }
    
    for name, img in fotolitos_dict.items():
        pos = positions[name]
        canvas.paste(img, pos)
        draw.text((pos[0], pos[1] - 20), f"CANAL {name} — ÁNGULO: {angles[name]}°", fill="black")
        
    pdf_buffer = io.BytesIO()
    canvas.save(pdf_buffer, format="PDF", resolution=300.0)
    return pdf_buffer.getvalue()

# ------------------------------------------------------------------------------
# 2. BARRA LATERAL (CONTROLES)
# ------------------------------------------------------------------------------
st.sidebar.header("📁 1. Archivo de Entrada")
uploaded_file = st.sidebar.file_uploader("Sube tu imagen a color (JPG/PNG)", type=["jpg", "png", "jpeg"])

st.sidebar.header("🔄 2. Transformación de Imagen")
with st.sidebar.expander("🛠️ Rotar, Voltear y Ajustes", expanded=True):
    if st.button("🔄 Rotar 90°"):
        st.session_state.angle_rotation = (st.session_state.angle_rotation + 90) % 360
    st.caption(f"Rotación actual: {st.session_state.angle_rotation}°")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        flip_h = st.checkbox("Espejo Horiz.")
    with col_f2:
        flip_v = st.checkbox("Espejo Vert.")
        
    brightness = st.slider("Brillo", 0.2, 2.0, 1.0, step=0.05)
    contrast = st.slider("Contraste", 0.2, 2.0, 1.0, step=0.05)

st.sidebar.header("📐 3. Parámetros de Impresión / Fine Art")
lpi = st.sidebar.slider("Frecuencia de Trama (LPI)", 10, 100, 35, help="Controla el tamaño de punto. Valores bajos = puntos grandes.")
dot_shape = st.sidebar.selectbox("Geometría del Punto", ["circular", "line", "elliptical"])
add_marks = st.sidebar.checkbox("Incluir Cruces de Calce / Registro", value=True)

with st.sidebar.expander("⚙️ Ángulos de Prensa Tradicional (Roseta)"):
    st.caption("Ángulos oficiales para evitar patrones de Moiré:")
    ang_c = st.number_input("Cyan (°)", value=15.0)
    ang_m = st.number_input("Magenta (°)", value=75.0)
    ang_y = st.number_input("Yellow (°)", value=0.0)
    ang_k = st.number_input("Black (°)", value=45.0)

with st.sidebar.expander("🎨 Descalce de Registro (Efecto Analógico)"):
    st.caption("Simula imperfección de imprenta / risografía (desplazamiento en px):")
    shift_m_x = st.slider("Desplazar Magenta X", -10, 10, 0)
    shift_m_y = st.slider("Desplazar Magenta Y", -10, 10, 0)
    shift_y_x = st.slider("Desplazar Amarillo X", -10, 10, 0)
    shift_y_y = st.slider("Desplazar Amarillo Y", -10, 10, 0)

# ------------------------------------------------------------------------------
# 3. PROCESAMIENTO Y VISUALIZACIÓN
# ------------------------------------------------------------------------------
if uploaded_file is not None:
    # 1. Cargar la imagen base
    img_original = Image.open(uploaded_file).convert("RGB")
    
    # 2. Aplicar Transformaciones
    img_transformed = img_original.copy()
    
    if st.session_state.angle_rotation != 0:
        img_transformed = img_transformed.rotate(-st.session_state.angle_rotation, expand=True)
    if flip_h:
        img_transformed = img_transformed.transpose(Image.FLIP_LEFT_RIGHT)
    if flip_v:
        img_transformed = img_transformed.transpose(Image.FLIP_TOP_BOTTOM)
        
    if brightness != 1.0:
        img_transformed = ImageEnhance.Brightness(img_transformed).enhance(brightness)
    if contrast != 1.0:
        img_transformed = ImageEnhance.Contrast(img_transformed).enhance(contrast)

    # 3. PROCESAMIENTO DE TRAMAS
    img_np = np.array(img_transformed)
    c, m, y, k = rgb_to_cmyk(img_np)
    
    channels = {'C': c, 'M': m, 'Y': y, 'K': k}
    angles = {'C': ang_c, 'M': ang_m, 'Y': ang_y, 'K': ang_k}
    shifts = {
        'C': (0, 0),
        'M': (shift_m_x, shift_m_y),
        'Y': (shift_y_x, shift_y_y),
        'K': (0, 0)
    }
    
    halftones = {}
    
    with st.spinner("Generando trama de medios tonos CMYK..."):
        for name, ch_data in channels.items():
            ht = generate_halftone_channel(ch_data, angles[name], lpi=lpi, dot_shape=dot_shape)
            
            sx, sy = shifts[name]
            if sx != 0 or sy != 0:
                ht = apply_misregistration(ht, sx, sy)
                
            halftones[name] = ht

    # --------------------------------------------------------------------------
    # DESPLIEGUE VISUAL
    # --------------------------------------------------------------------------
    
    # SECCIÓN SUPERIOR: COMPARACIÓN DE LA IMAGEN ORIGINAL VS SIMULACIÓN COMBINADA
    st.subheader("🖼️ Comparación: Imagen Editada vs. Simulación CMYK Combinada")
    
    st.write("Activa o desactiva tintas para ver cómo combinan entre sí:")
    col_ch1, col_ch2, col_ch3, col_ch4 = st.columns(4)
    with col_ch1:
        use_c = st.checkbox("Cyan (C)", value=True)
    with col_ch2:
        use_m = st.checkbox("Magenta (M)", value=True)
    with col_ch3:
        use_y = st.checkbox("Yellow (Y)", value=True)
    with col_ch4:
        use_k = st.checkbox("Black (K)", value=True)

    ht_c = halftones['C'] if use_c else np.zeros_like(halftones['C'])
    ht_m = halftones['M'] if use_m else np.zeros_like(halftones['M'])
    ht_y = halftones['Y'] if use_y else np.zeros_like(halftones['Y'])
    ht_k = halftones['K'] if use_k else np.zeros_like(halftones['K'])

    sim_r = (1.0 - ht_c) * (1.0 - ht_k)
    sim_g = (1.0 - ht_m) * (1.0 - ht_k)
    sim_b = (1.0 - ht_y) * (1.0 - ht_k)
    
    sim_rgb = np.stack([sim_r, sim_g, sim_b], axis=-1)
    sim_rgb = np.clip(sim_rgb * 255, 0, 255).astype(np.uint8)
    sim_pil = Image.fromarray(sim_rgb)
    
    if add_marks:
        sim_pil = add_registration_marks(sim_pil, label="SIMULACIÓN CMYK")

    col_orig, col_sim = st.columns(2)
    with col_orig:
        st.image(img_transformed, caption="Original Editada", use_container_width=True)
    with col_sim:
        st.image(sim_pil, caption="Simulación Impresa (Mezcla de Tintas Activas)", use_container_width=True)

    st.markdown("---")

    # SECCIÓN INTERMEDIA: VISTA SIMULTÁNEA DE LOS 4 FOTOLITOS INDIVIDUALES
    st.subheader("🖨️ Fotolitos Individuales de Impresión (4 Canales a la vez)")
    st.caption("Matriz Blanco y Negro pura lista para quemar/insolvar placas o mallas:")

    col_fot_c, col_fot_m, col_fot_y, col_fot_k = st.columns(4)
    
    fotolitos_processed_dict = {}
    fotolitos_list_for_pdf = []
    
    for name, col_target in zip(['C', 'M', 'Y', 'K'], [col_fot_c, col_fot_m, col_fot_y, col_fot_k]):
        with col_target:
            st.markdown(f"**Fotolito {name}** ({angles[name]}°)")
            
            fotolito_np = ((1.0 - halftones[name]) * 255).astype(np.uint8)
            f_img = Image.fromarray(fotolito_np)
            if add_marks:
                f_img = add_registration_marks(f_img, label=f"CANAL {name} ({angles[name]}°)")
                
            fotolitos_processed_dict[name] = f_img
            fotolitos_list_for_pdf.append(f_img)
            
            st.image(f_img, use_container_width=True)
            
            # Botón de Descarga PNG individual
            buf = io.BytesIO()
            f_img.save(buf, format="PNG", dpi=(300, 300))
            st.download_button(
                label=f"📥 PNG {name}",
                data=buf.getvalue(),
                file_name=f"fotolito_{name}.png",
                mime="image/png",
                use_container_width=True
            )

    st.markdown("---")

    # SECCIÓN INFERIOR: EXPORTACIÓN PDF COMPLETA
    st.subheader("📄 Exportación Técnica en PDF")
    st.caption("Descarga un único archivo listo para imprenta o archivo de producción:")

    col_pdf1, col_pdf2 = st.columns(2)
    
    with col_pdf1:
        pdf_pages_data = generate_pdf_multipage(fotolitos_list_for_pdf)
        st.download_button(
            label="📑 Descargar PDF Multi-Página (1 Fotolito por Hoja - 4 Págs)",
            data=pdf_pages_data,
            file_name="fotolitos_CMYK_4_paginas.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.caption("Ideal para imprimir cada canal directo en filminas/micas independientes a tamaño completo.")

    with col_pdf2:
        pdf_grid_data = generate_pdf_grid(fotolitos_processed_dict, angles)
        st.download_button(
            label="📊 Descargar PDF Muestra Grilla 2x2 (4 Fotolitos en 1 Hoja)",
            data=pdf_grid_data,
            file_name="fotolitos_CMYK_hoja_grilla.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.caption("Ideal para archivo de control de calidad, catálogo o revisión de mesa.")

else:
    st.info("👈 Sube una imagen a color desde la barra lateral para comenzar la preparación.")