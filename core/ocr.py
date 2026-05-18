"""
Módulo: ocr.py
HU-003 — Procesamiento OCR
Extrae texto de imágenes (JPG, PNG) y documentos PDF mediante reconocimiento
óptico de caracteres. Para PDFs comprueba primero si hay texto embebido;
si una página es escaneada, recurre a Tesseract página por página.
Guarda el resultado en storage/outputs/ como archivo .txt.
"""

import io
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Mínimo de caracteres por página para considerar que tiene texto embebido.
# Por debajo de este umbral la página se trata como escaneada y se le aplica OCR.
_MIN_CHARS_PAGINA = 50

# Resolución de renderizado para páginas PDF que requieren OCR.
# 300 DPI ofrece buen equilibrio entre calidad de reconocimiento y velocidad.
_DPI_OCR = 300

_DIR_SALIDA = Path(__file__).parent.parent / "storage" / "outputs"


# =====================================
# API pública
# =====================================

def extraer_texto(ruta_archivo: Path, idioma: str = "spa") -> str:
    """
    Punto de entrada principal del módulo.
    - PDF con texto embebido  → extracción directa (sin Tesseract).
    - PDF escaneado           → OCR página por página.
    - Imagen JPG / PNG        → OCR directo.

    Parámetros:
        ruta_archivo: ruta al archivo a procesar (debe existir).
        idioma: código de idioma Tesseract; 'spa' para español, 'eng' para inglés.
    Devuelve el texto extraído como string.
    Lanza:
        ValueError                          — formato de archivo no soportado.
        pytesseract.TesseractNotFoundError  — Tesseract no está instalado en el sistema.
        fitz.FileDataError                  — el PDF está corrupto o no es legible.
    """
    ext = ruta_archivo.suffix.lower()

    if ext == ".pdf":
        return _procesar_pdf(ruta_archivo, idioma)
    if ext in {".jpg", ".jpeg", ".png"}:
        return _procesar_imagen(ruta_archivo, idioma)

    raise ValueError(f"Formato no soportado para OCR: '{ext}'")


def guardar_resultado(texto: str, nombre_base: str) -> Path:
    """
    Guarda el texto extraído en un archivo .txt dentro de storage/outputs/.
    El nombre incluye un timestamp para evitar colisiones entre ejecuciones.

    Parámetros:
        texto:       contenido a guardar.
        nombre_base: nombre del archivo original (se usa solo el stem).
    Devuelve la ruta del archivo .txt creado.
    """
    _DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(nombre_base).stem
    ruta = _DIR_SALIDA / f"{timestamp}_{stem}_ocr.txt"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


# =====================================
# Procesamiento de PDF
# =====================================

def _procesar_pdf(ruta: Path, idioma: str) -> str:
    """
    Recorre cada página del PDF y decide la estrategia por página:
    - Texto embebido suficiente → se extrae directamente.
    - Texto escaso o ausente   → se renderiza la página y se aplica OCR.
    Concatena el texto de todas las páginas separado por línea en blanco.
    """
    doc = fitz.open(str(ruta))
    paginas = []

    try:
        for pagina in doc:
            texto_embebido = pagina.get_text().strip()

            if len(texto_embebido) >= _MIN_CHARS_PAGINA:
                paginas.append(texto_embebido)
            else:
                paginas.append(_ocr_pagina_pdf(pagina, idioma))
    finally:
        doc.close()

    return "\n\n".join(paginas)


def _ocr_pagina_pdf(pagina: fitz.Page, idioma: str) -> str:
    """
    Renderiza una página de PDF a imagen PNG en alta resolución y le aplica OCR.
    Devuelve el texto reconocido por Tesseract.
    """
    pixmap = pagina.get_pixmap(dpi=_DPI_OCR)
    imagen = Image.open(io.BytesIO(pixmap.tobytes("png")))
    return pytesseract.image_to_string(imagen, lang=idioma).strip()


# =====================================
# Procesamiento de imágenes
# =====================================

def _procesar_imagen(ruta: Path, idioma: str) -> str:
    """
    Abre la imagen con Pillow y aplica OCR con Tesseract.
    Devuelve el texto reconocido.
    """
    imagen = Image.open(str(ruta))
    return pytesseract.image_to_string(imagen, lang=idioma).strip()
