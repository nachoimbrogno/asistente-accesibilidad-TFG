"""
Módulo: summarizer.py
HU-010 — Generación de resumen automático
Produce un resumen extractivo de un texto extenso usando la librería sumy (LexRank).
Rechaza textos demasiado cortos con un mensaje descriptivo antes de intentar el procesamiento.
Guarda el resultado en storage/outputs/ como archivo .txt.
"""

from datetime import datetime
from pathlib import Path

from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.utils import get_stop_words

# Mínimo de palabras que debe tener el texto para que tenga sentido resumirlo.
# Por debajo de este umbral el resumen sería trivialmente similar al original.
_MIN_PALABRAS = 100

# Cantidad de oraciones del resumen por defecto.
# El caller puede sobrescribir este valor según el largo del texto.
_ORACIONES_DEFAULT = 5

_DIR_SALIDA = Path(__file__).parent.parent / "storage" / "outputs"


# =====================================
# API pública
# =====================================

def resumir(
    texto: str,
    num_oraciones: int = _ORACIONES_DEFAULT,
    idioma: str = "spanish",
) -> str:
    """
    Genera un resumen extractivo del texto usando el algoritmo LexRank de sumy.
    Selecciona las oraciones más representativas del documento original.

    Parámetros:
        texto:          texto a resumir (mínimo _MIN_PALABRAS palabras).
        num_oraciones:  cantidad de oraciones en el resumen (default 5).
                        Si el texto tiene menos oraciones, se ajusta automáticamente.
        idioma:         idioma del texto en formato sumy (default 'spanish').
                        Otros valores válidos: 'english', 'french', etc.
    Devuelve el resumen como string con las oraciones separadas por espacio.
    Lanza:
        ValueError — el texto tiene menos palabras que _MIN_PALABRAS.
    """
    _validar_longitud(texto)

    parser = PlaintextParser.from_string(texto, Tokenizer(idioma))

    # No pedir más oraciones que las disponibles menos una (evita devolver el texto completo)
    total_oraciones = len(list(parser.document.sentences))
    n = min(num_oraciones, max(1, total_oraciones - 1))

    summarizer = _crear_summarizer(idioma)
    oraciones = summarizer(parser.document, n)

    return " ".join(str(oracion) for oracion in oraciones)


def guardar_resultado(texto_resumen: str, nombre_base: str) -> Path:
    """
    Guarda el resumen en un archivo .txt dentro de storage/outputs/.
    El nombre incluye un timestamp para evitar colisiones entre ejecuciones.

    Parámetros:
        texto_resumen: contenido del resumen a guardar.
        nombre_base:   nombre de referencia para el archivo de salida (se usa el stem).
    Devuelve la ruta del archivo .txt creado.
    """
    _DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(nombre_base).stem
    ruta = _DIR_SALIDA / f"{timestamp}_{stem}_resumen.txt"
    ruta.write_text(texto_resumen, encoding="utf-8")
    return ruta


def contar_palabras(texto: str) -> int:
    """
    Devuelve la cantidad de palabras del texto.
    Útil para que la GUI informe al usuario antes de intentar el resumen.
    """
    return len(texto.split())


# =====================================
# Helpers internos
# =====================================

def _validar_longitud(texto: str) -> None:
    """
    Verifica que el texto tenga suficientes palabras para producir un resumen útil.
    Lanza ValueError con mensaje descriptivo si no se cumple la condición (HU-010).
    """
    palabras = len(texto.split())
    if palabras < _MIN_PALABRAS:
        raise ValueError(
            f"El texto es demasiado corto para resumir: tiene {palabras} "
            f"{'palabra' if palabras == 1 else 'palabras'} "
            f"y se necesitan al menos {_MIN_PALABRAS}."
        )


def _crear_summarizer(idioma: str) -> LexRankSummarizer:
    """
    Instancia y configura el summarizer LexRank con stemmer y stop words del idioma indicado.
    LexRank es un algoritmo basado en grafos que no requiere entrenamiento
    y funciona bien para español sin dependencias externas adicionales.
    """
    stemmer = Stemmer(idioma)
    summarizer = LexRankSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(idioma)
    return summarizer
