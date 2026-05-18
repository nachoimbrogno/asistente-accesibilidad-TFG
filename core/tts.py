"""
Módulo: tts.py
HU-004 — Conversión de texto a voz (TTS)
Convierte texto en audio usando pyttsx3 (síntesis de voz offline).
La reproducción se divide en oraciones para permitir pausar y detener
en cualquier momento sin esperar a que todo el texto termine.
"""

import re
import threading
import time
from datetime import datetime
from pathlib import Path

import pyttsx3

_VELOCIDAD_DEFAULT = 150
_VOLUMEN_DEFAULT   = 1.0

_DIR_SALIDA = Path(__file__).parent.parent / "storage" / "outputs"

# =====================================
# Estado de reproducción (compartido entre hilos)
# =====================================

_parado  = threading.Event()   # señal para detener la reproducción
_pausado = threading.Event()   # señal para pausar entre oraciones
_lock    = threading.Lock()    # protege el acceso a _motor_activo
_motor_activo = None           # referencia al motor en curso para poder interrumpirlo


# =====================================
# API pública — reproducción con control
# =====================================

def reproducir(
    texto: str,
    velocidad: int = _VELOCIDAD_DEFAULT,
    volumen: float = _VOLUMEN_DEFAULT,
) -> None:
    """
    Reproduce el texto por los altavoces dividiéndolo en oraciones.
    Entre oración y oración verifica si se solicitó pausa o detención,
    lo que permite responder a esas acciones sin esperar al final del texto.
    La llamada es bloqueante: retorna cuando termina, se detiene o se interrumpe.

    Parámetros:
        texto:     texto a reproducir (no puede estar vacío).
        velocidad: palabras por minuto (default 150).
        volumen:   nivel entre 0.0 y 1.0 (default 1.0).
    Lanza:
        ValueError — texto vacío o volumen fuera de rango.
    """
    global _motor_activo
    _validar_entrada(texto, volumen)

    _parado.clear()
    _pausado.clear()

    for oracion in _dividir_oraciones(texto):
        if _parado.is_set():
            break

        # Esperar mientras está pausado (polling fino para detectar detención)
        while _pausado.is_set():
            if _parado.is_set():
                return
            time.sleep(0.05)

        if _parado.is_set():
            break

        motor = _crear_motor(velocidad, volumen)
        with _lock:
            _motor_activo = motor
        try:
            motor.say(oracion)
            motor.runAndWait()
        finally:
            with _lock:
                if _motor_activo is motor:
                    _motor_activo = None
            motor.stop()


def pausar() -> None:
    """
    Pausa la reproducción. El texto en curso termina su oración actual
    y luego la reproducción queda en espera hasta que se llame a reanudar().
    """
    _pausado.set()


def reanudar() -> None:
    """Reanuda la reproducción desde la siguiente oración."""
    _pausado.clear()


def detener() -> None:
    """
    Detiene la reproducción interrumpiendo la oración en curso.
    Envía la señal al motor activo para que corte el audio inmediatamente.
    """
    global _motor_activo
    _parado.set()
    _pausado.clear()
    with _lock:
        if _motor_activo is not None:
            try:
                _motor_activo.stop()
            except Exception:
                pass


# =====================================
# API pública — exportación a archivo
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
        ValueError — texto vacío o volumen fuera de rango.
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


def obtener_voces() -> list[dict]:
    """
    Devuelve la lista de voces disponibles en el sistema.
    Cada entrada tiene las claves 'id', 'nombre' e 'idiomas'.
    """
    motor = pyttsx3.init()
    try:
        voces = motor.getProperty("voices")
        return [
            {"id": voz.id, "nombre": voz.name, "idiomas": voz.languages}
            for voz in voces
        ]
    finally:
        motor.stop()


# =====================================
# Helpers internos
# =====================================

def _dividir_oraciones(texto: str) -> list[str]:
    """
    Divide el texto en oraciones usando la puntuación como delimitador.
    También separa por saltos de línea para manejar listas y párrafos.
    Las porciones vacías o con solo espacios se descartan.
    """
    # Dividir por punto, exclamación, interrogación seguidos de espacio
    partes = re.split(r'(?<=[.!?])\s+', texto.strip())
    oraciones = []
    for parte in partes:
        for sub in parte.splitlines():
            sub = sub.strip()
            if sub:
                oraciones.append(sub)
    return oraciones


def _crear_motor(velocidad: int, volumen: float) -> pyttsx3.Engine:
    """
    Inicializa el motor pyttsx3 con los parámetros dados.
    Intenta seleccionar una voz en español; si no hay ninguna, usa la voz por defecto.
    """
    motor = pyttsx3.init()
    motor.setProperty("rate",   velocidad)
    motor.setProperty("volume", volumen)

    voz_es = _buscar_voz_espanol(motor)
    if voz_es:
        motor.setProperty("voice", voz_es)

    return motor


def _buscar_voz_espanol(motor: pyttsx3.Engine) -> str | None:
    """
    Busca una voz en español entre las disponibles en el sistema.
    Devuelve el id de la primera que encuentre, o None si no hay ninguna.
    """
    marcas = ("spanish", "español", "espanol", "es_", "_es", "spa")
    for voz in motor.getProperty("voices"):
        nombre = (voz.name or "").lower()
        id_voz = (voz.id   or "").lower()
        if any(m in nombre or m in id_voz for m in marcas):
            return voz.id
    return None


def _validar_entrada(texto: str, volumen: float) -> None:
    """Verifica que el texto no esté vacío y que el volumen esté en rango [0.0, 1.0]."""
    if not texto or not texto.strip():
        raise ValueError("El texto no puede estar vacío.")
    if not 0.0 <= volumen <= 1.0:
        raise ValueError(f"El volumen debe estar entre 0.0 y 1.0 (recibido: {volumen}).")
