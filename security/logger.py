"""
Módulo: logger.py
HU-009 — Registro de logs de actividad
Envuelve la capa de datos para registrar eventos del sistema de forma centralizada.
Todas las acciones relevantes (login, carga, procesamiento, errores) pasan por aquí.
"""

from db.database import Database

# =====================================
# Constantes de tipo de acción
# =====================================

LOGIN_OK          = "LOGIN_OK"
LOGIN_FALLO       = "LOGIN_FALLO"
LOGOUT            = "LOGOUT"
REGISTRO          = "REGISTRO"
BLOQUEO           = "BLOQUEO"
CARGA_DOCUMENTO   = "CARGA_DOCUMENTO"
CARGA_AUDIO       = "CARGA_AUDIO"
OCR               = "OCR"
TTS               = "TTS"
STT               = "STT"
RESUMEN           = "RESUMEN"
DESCARGA          = "DESCARGA"
ERROR             = "ERROR"


class Logger:
    """
    Registra eventos del sistema en la tabla log de la base de datos.
    Debe instanciarse una vez y compartirse entre los módulos que necesiten loguear.
    """

    def __init__(self, db: Database):
        """
        Parámetros:
            db: instancia activa de Database ya inicializada.
        """
        self._db = db

    def log(self, tipo_accion: str, descripcion: str, usuario_id: int | None = None):
        """
        Registra un evento en la tabla log.
        Parámetros:
            tipo_accion:  una de las constantes definidas en este módulo (LOGIN_OK, OCR, etc.)
            descripcion:  mensaje descriptivo del evento; nunca incluir datos sensibles.
            usuario_id:   id del usuario que realizó la acción, o None si aún no hay sesión.
        """
        try:
            self._db.registrar_log(tipo_accion, descripcion, usuario_id)
        except Exception as e:
            # Fallo silencioso: el logger no debe interrumpir el flujo de la aplicación.
            # Se imprime solo durante desarrollo; en producción se podría redirigir a un archivo.
            print(f"[Logger] Error al escribir log: {e}")

    def obtener_logs(self, usuario_id: int | None = None, limite: int = 100) -> list[dict]:
        """
        Devuelve los registros de log más recientes.
        Parámetros:
            usuario_id: filtra por usuario si se indica; None devuelve todos los logs.
            limite:     máximo de registros a retornar.
        """
        return self._db.obtener_logs(usuario_id=usuario_id, limite=limite)
