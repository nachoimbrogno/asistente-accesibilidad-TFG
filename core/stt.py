"""
Módulo: stt.py
HU-005 — Transcripción de voz a texto (STT)
Transcribe archivos de audio (WAV, MP3) a texto usando Whisper de OpenAI (modo offline).
El modelo se descarga automáticamente en el primer uso y queda en caché local;
las ejecuciones posteriores no requieren internet.
Guarda el resultado en storage/outputs/ como archivo .txt.
"""

from datetime import datetime
from pathlib import Path

# whisper se importa de forma diferida dentro de _cargar_modelo() para que
# la aplicación pueda arrancar aunque openai-whisper no esté instalado todavía.
# El error solo aparecerá cuando el usuario intente usar la función STT.

_FORMATOS_ADMITIDOS = {".wav", ".mp3"}

# 'base' (~140 MB) ofrece buen equilibrio entre velocidad y precisión para español.
# Opciones: 'tiny', 'base', 'small', 'medium', 'large'.
_MODELO_DEFAULT = "base"

# Forzar español mejora la precisión cuando se sabe que el audio está en ese idioma.
# Pasar None deja que Whisper detecte el idioma automáticamente.
_IDIOMA_DEFAULT = "es"

_DIR_SALIDA = Path(__file__).parent.parent / "storage" / "outputs"

# Modelos ya cargados en memoria: evita recargar en transcripciones sucesivas.
_cache_modelos: dict = {}


# =====================================
# API pública
# =====================================

def transcribir(
    ruta_audio: Path,
    idioma: str | None = _IDIOMA_DEFAULT,
    modelo: str = _MODELO_DEFAULT,
) -> str:
    """
    Transcribe un archivo de audio a texto con Whisper.
    El modelo se carga en el primer uso y se reutiliza en llamadas posteriores.

    Parámetros:
        ruta_audio: ruta al archivo WAV o MP3 (debe existir).
        idioma:     código ISO 639-1 para forzar el idioma ('es', 'en', etc.).
                    Pasar None para que Whisper detecte el idioma automáticamente.
        modelo:     tamaño del modelo Whisper a usar (default 'base').
    Devuelve el texto transcrito como string.
    Lanza:
        ValueError — el archivo no existe o tiene un formato no admitido.
    """
    _validar_archivo(ruta_audio)

    modelo_cargado = _cargar_modelo(modelo)
    opciones = {"language": idioma} if idioma else {}
    resultado = modelo_cargado.transcribe(str(ruta_audio), **opciones)
    return resultado["text"].strip()


def guardar_resultado(texto: str, nombre_base: str) -> Path:
    """
    Guarda la transcripción en un archivo .txt dentro de storage/outputs/.
    El nombre incluye un timestamp para evitar colisiones entre ejecuciones.

    Parámetros:
        texto:       transcripción a guardar.
        nombre_base: nombre del archivo de audio original (se usa el stem).
    Devuelve la ruta del archivo .txt creado.
    """
    _DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(nombre_base).stem
    ruta = _DIR_SALIDA / f"{timestamp}_{stem}_stt.txt"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


# =====================================
# Helpers internos
# =====================================

def _cargar_modelo(nombre: str):
    """
    Carga el modelo Whisper indicado en memoria.
    Si ya fue cargado en esta sesión lo devuelve desde el caché.
    La primera carga descarga el modelo si no está en la caché local de Whisper.
    """
    import whisper  # diferido: falla aquí si openai-whisper no está instalado
    if nombre not in _cache_modelos:
        _cache_modelos[nombre] = whisper.load_model(nombre)
    return _cache_modelos[nombre]


def _validar_archivo(ruta: Path) -> None:
    """
    Verifica que el archivo exista y tenga un formato admitido (WAV o MP3).
    Lanza ValueError con mensaje descriptivo si alguna condición falla.
    No inicia ningún procesamiento si la validación no pasa (criterio HU-005).
    """
    if not ruta.exists():
        raise ValueError(f"El archivo no existe: '{ruta.name}'")

    ext = ruta.suffix.lower()
    if ext not in _FORMATOS_ADMITIDOS:
        admitidos = ", ".join(f.upper().lstrip(".") for f in sorted(_FORMATOS_ADMITIDOS))
        raise ValueError(
            f"Formato no admitido: '{ext.upper().lstrip('.')}'. "
            f"Usá archivos {admitidos}."
        )
