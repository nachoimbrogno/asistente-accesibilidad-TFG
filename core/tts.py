"""
Módulo: tts.py
HU-004 — Conversión de texto a voz (TTS)
Convierte texto en audio usando pyttsx3 (síntesis de voz offline).
Permite generar un archivo WAV exportable o reproducir directamente por los altavoces.
Intenta utilizar una voz en español si el sistema tiene una disponible.
"""

from datetime import datetime
from pathlib import Path

import pyttsx3

# Velocidad de habla en palabras por minuto (valor natural para español)
_VELOCIDAD_DEFAULT = 150

# Volumen: 0.0 (silencio) a 1.0 (máximo)
_VOLUMEN_DEFAULT = 1.0

_DIR_SALIDA = Path(__file__).parent.parent / "storage" / "outputs"


# =====================================
# API pública
# =====================================

def convertir_a_audio(
    texto: str,
    nombre_base: str,
    velocidad: int = _VELOCIDAD_DEFAULT,
    volumen: float = _VOLUMEN_DEFAULT,
) -> Path:
    """
    Convierte el texto a voz y lo guarda como archivo WAV en storage/outputs/.
    El nombre del archivo incluye un timestamp para evitar colisiones.

    Parámetros:
        texto:       texto a sintetizar (no puede estar vacío).
        nombre_base: nombre de referencia para el archivo de salida (se usa el stem).
        velocidad:   palabras por minuto (default 150).
        volumen:     nivel de volumen entre 0.0 y 1.0 (default 1.0).
    Devuelve la ruta del archivo WAV generado.
    Lanza:
        ValueError — si el texto está vacío o el volumen está fuera de rango.
    """
    _validar_entrada(texto, volumen)

    _DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(nombre_base).stem
    ruta = _DIR_SALIDA / f"{timestamp}_{stem}_tts.wav"

    motor = _crear_motor(velocidad, volumen)
    try:
        motor.save_to_file(texto, str(ruta))
        motor.runAndWait()
    finally:
        motor.stop()

    return ruta


def reproducir(
    texto: str,
    velocidad: int = _VELOCIDAD_DEFAULT,
    volumen: float = _VOLUMEN_DEFAULT,
) -> None:
    """
    Reproduce el texto directamente por los altavoces sin guardar ningún archivo.
    La llamada es bloqueante: no retorna hasta que termine la reproducción.
    Útil para retroalimentación auditiva inmediata (HU-007).

    Parámetros:
        texto:    texto a reproducir (no puede estar vacío).
        velocidad: palabras por minuto (default 150).
        volumen:  nivel de volumen entre 0.0 y 1.0 (default 1.0).
    Lanza:
        ValueError — si el texto está vacío o el volumen está fuera de rango.
    """
    _validar_entrada(texto, volumen)

    motor = _crear_motor(velocidad, volumen)
    try:
        motor.say(texto)
        motor.runAndWait()
    finally:
        motor.stop()


def obtener_voces() -> list[dict]:
    """
    Devuelve la lista de voces disponibles en el sistema.
    Cada entrada del resultado tiene las claves 'id', 'nombre' y 'idiomas'.
    Útil para mostrar un selector de voz en la interfaz.
    """
    motor = pyttsx3.init()
    try:
        voces = motor.getProperty("voices")
        return [
            {
                "id":      voz.id,
                "nombre":  voz.name,
                "idiomas": voz.languages,
            }
            for voz in voces
        ]
    finally:
        motor.stop()


# =====================================
# Helpers internos
# =====================================

def _crear_motor(velocidad: int, volumen: float) -> pyttsx3.Engine:
    """
    Inicializa el motor pyttsx3 con los parámetros dados.
    Intenta seleccionar una voz en español; si no hay ninguna disponible, usa la voz por defecto.
    """
    motor = pyttsx3.init()
    motor.setProperty("rate",   velocidad)
    motor.setProperty("volume", volumen)

    voz_espanol = _buscar_voz_espanol(motor)
    if voz_espanol:
        motor.setProperty("voice", voz_espanol)

    return motor


def _buscar_voz_espanol(motor: pyttsx3.Engine) -> str | None:
    """
    Busca entre las voces del sistema una que sea en español.
    Devuelve el id de la voz si la encuentra, o None si no hay ninguna disponible.
    """
    voces = motor.getProperty("voices")
    for voz in voces:
        nombre = (voz.name or "").lower()
        id_voz = (voz.id   or "").lower()
        if any(marca in nombre or marca in id_voz for marca in ("spanish", "español", "espanol", "es_", "_es", "spa")):
            return voz.id
    return None


def _validar_entrada(texto: str, volumen: float) -> None:
    """
    Comprueba que el texto no esté vacío y que el volumen esté en rango válido.
    Lanza ValueError con un mensaje descriptivo si alguna condición falla.
    """
    if not texto or not texto.strip():
        raise ValueError("El texto no puede estar vacío.")
    if not 0.0 <= volumen <= 1.0:
        raise ValueError(f"El volumen debe estar entre 0.0 y 1.0 (recibido: {volumen}).")
