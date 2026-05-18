"""
Módulo: database.py
HU-001, HU-002, HU-009 — Capa de acceso a datos
Gestiona la conexión SQLite y expone métodos CRUD para todas las entidades
del modelo: Usuario, Documento, Audio, Proceso, Resultado y Log.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# Rutas resueltas desde la ubicación de este archivo
_DIR_DB = Path(__file__).parent
_DIR_STORAGE = _DIR_DB.parent / "storage"
DB_PATH = _DIR_STORAGE / "app.db"
SCHEMA_PATH = _DIR_DB / "schema.sql"


class Database:
    """
    Punto de acceso único a la base de datos SQLite de la aplicación.
    Crea el archivo y las tablas si no existen al instanciarse.
    """

    def __init__(self, db_path: Path = DB_PATH):
        """
        Abre (o crea) la base de datos en db_path y aplica el esquema.
        Parámetros:
            db_path: ruta al archivo .db. Usa DB_PATH por defecto.
        """
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._aplicar_schema()

    def _aplicar_schema(self):
        """Lee schema.sql y ejecuta las sentencias CREATE TABLE IF NOT EXISTS."""
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        self._conn.executescript(schema)
        self._conn.commit()

    def cerrar(self):
        """Cierra la conexión a la base de datos."""
        self._conn.close()

    # =====================================
    # Usuario
    # =====================================

    def crear_usuario(
        self,
        nombre: str,
        apellido: str,
        username: str,
        password_hash: str,
        salt: str,
        algoritmo: str,
        iteraciones: int,
        rol: str = "usuario",
    ) -> int:
        """
        Inserta un nuevo usuario y devuelve su id generado.
        Lanza sqlite3.IntegrityError si el username ya existe.
        """
        cursor = self._conn.execute(
            """INSERT INTO usuario
               (nombre, apellido, username, password_hash, salt, algoritmo, iteraciones, rol)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (nombre, apellido, username, password_hash, salt, algoritmo, iteraciones, rol),
        )
        self._conn.commit()
        return cursor.lastrowid

    def obtener_usuario_por_username(self, username: str) -> dict | None:
        """
        Devuelve todos los campos del usuario cuyo username coincide, o None si no existe.
        """
        row = self._conn.execute(
            "SELECT * FROM usuario WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None

    def obtener_usuario_por_id(self, usuario_id: int) -> dict | None:
        """
        Devuelve todos los campos del usuario por id, o None si no existe.
        """
        row = self._conn.execute(
            "SELECT * FROM usuario WHERE id = ?", (usuario_id,)
        ).fetchone()
        return dict(row) if row else None

    def actualizar_intentos_fallidos(
        self, usuario_id: int, intentos: int, bloqueado_hasta: str | None = None
    ):
        """
        Actualiza el contador de intentos fallidos y, opcionalmente, el timestamp de bloqueo.
        Parámetros:
            bloqueado_hasta: string ISO 8601 con la fecha/hora hasta la que el usuario queda
                             bloqueado, o None para no modificar el bloqueo.
        """
        self._conn.execute(
            "UPDATE usuario SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE id = ?",
            (intentos, bloqueado_hasta, usuario_id),
        )
        self._conn.commit()

    def resetear_intentos_fallidos(self, usuario_id: int):
        """Pone intentos_fallidos en 0 y elimina cualquier bloqueo activo."""
        self._conn.execute(
            "UPDATE usuario SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id = ?",
            (usuario_id,),
        )
        self._conn.commit()

    # =====================================
    # Documento
    # =====================================

    def registrar_documento(self, usuario_id: int, ruta: Path | str, tipo: str) -> int:
        """
        Registra un documento recién subido y devuelve su id.
        Parámetros:
            tipo: 'PDF', 'JPG' o 'PNG'
        """
        cursor = self._conn.execute(
            "INSERT INTO documento (usuario_id, ruta, tipo, fecha_subida) VALUES (?, ?, ?, ?)",
            (usuario_id, str(ruta), tipo, _ahora()),
        )
        self._conn.commit()
        return cursor.lastrowid

    def obtener_documento_por_id(self, documento_id: int) -> dict | None:
        """Devuelve el documento con el id indicado, o None si no existe."""
        row = self._conn.execute(
            "SELECT * FROM documento WHERE id = ?", (documento_id,)
        ).fetchone()
        return dict(row) if row else None

    def obtener_documentos_por_usuario(self, usuario_id: int) -> list[dict]:
        """Devuelve los documentos del usuario ordenados del más reciente al más antiguo."""
        rows = self._conn.execute(
            "SELECT * FROM documento WHERE usuario_id = ? ORDER BY fecha_subida DESC",
            (usuario_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def actualizar_estado_documento(self, documento_id: int, estado: str):
        """
        Actualiza el estado de un documento.
        Parámetros:
            estado: 'cargado', 'procesado' o 'error'
        """
        self._conn.execute(
            "UPDATE documento SET estado = ? WHERE id = ?", (estado, documento_id)
        )
        self._conn.commit()

    # =====================================
    # Audio
    # =====================================

    def registrar_audio(self, usuario_id: int, ruta: Path | str, tipo: str) -> int:
        """
        Registra un archivo de audio recién subido y devuelve su id.
        Parámetros:
            tipo: 'WAV' o 'MP3'
        """
        cursor = self._conn.execute(
            "INSERT INTO audio (usuario_id, ruta, tipo, fecha_subida) VALUES (?, ?, ?, ?)",
            (usuario_id, str(ruta), tipo, _ahora()),
        )
        self._conn.commit()
        return cursor.lastrowid

    def obtener_audio_por_id(self, audio_id: int) -> dict | None:
        """Devuelve el audio con el id indicado, o None si no existe."""
        row = self._conn.execute(
            "SELECT * FROM audio WHERE id = ?", (audio_id,)
        ).fetchone()
        return dict(row) if row else None

    def obtener_audios_por_usuario(self, usuario_id: int) -> list[dict]:
        """Devuelve los audios del usuario ordenados del más reciente al más antiguo."""
        rows = self._conn.execute(
            "SELECT * FROM audio WHERE usuario_id = ? ORDER BY fecha_subida DESC",
            (usuario_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def actualizar_estado_audio(self, audio_id: int, estado: str):
        """
        Actualiza el estado de un audio.
        Parámetros:
            estado: 'cargado', 'procesado' o 'error'
        """
        self._conn.execute(
            "UPDATE audio SET estado = ? WHERE id = ?", (estado, audio_id)
        )
        self._conn.commit()

    # =====================================
    # Proceso
    # =====================================

    def registrar_proceso(
        self, usuario_id: int, tipo: str, entrada_id: int, entrada_tipo: str
    ) -> int:
        """
        Registra el inicio de un proceso y devuelve su id.
        Parámetros:
            tipo:         'OCR', 'TTS', 'STT' o 'RESUMEN'
            entrada_id:   id del documento o audio de entrada
            entrada_tipo: 'documento' o 'audio'
        """
        cursor = self._conn.execute(
            """INSERT INTO proceso (usuario_id, tipo, entrada_id, entrada_tipo, fecha)
               VALUES (?, ?, ?, ?, ?)""",
            (usuario_id, tipo, entrada_id, entrada_tipo, _ahora()),
        )
        self._conn.commit()
        return cursor.lastrowid

    def actualizar_estado_proceso(self, proceso_id: int, estado: str):
        """
        Actualiza el estado de un proceso.
        Parámetros:
            estado: 'pendiente', 'en_proceso', 'completado' o 'error'
        """
        self._conn.execute(
            "UPDATE proceso SET estado = ? WHERE id = ?", (estado, proceso_id)
        )
        self._conn.commit()

    def obtener_procesos_por_usuario(self, usuario_id: int) -> list[dict]:
        """Devuelve todos los procesos del usuario, del más reciente al más antiguo."""
        rows = self._conn.execute(
            "SELECT * FROM proceso WHERE usuario_id = ? ORDER BY fecha DESC",
            (usuario_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # =====================================
    # Resultado
    # =====================================

    def registrar_resultado(self, proceso_id: int, ruta: Path | str, formato: str) -> int:
        """
        Registra el archivo de salida generado por un proceso y devuelve su id.
        Parámetros:
            formato: 'txt', 'mp3' o 'wav'
        """
        cursor = self._conn.execute(
            "INSERT INTO resultado (proceso_id, ruta, formato, fecha) VALUES (?, ?, ?, ?)",
            (proceso_id, str(ruta), formato, _ahora()),
        )
        self._conn.commit()
        return cursor.lastrowid

    def obtener_resultado_por_proceso(self, proceso_id: int) -> dict | None:
        """Devuelve el resultado asociado a un proceso, o None si aún no existe."""
        row = self._conn.execute(
            "SELECT * FROM resultado WHERE proceso_id = ?", (proceso_id,)
        ).fetchone()
        return dict(row) if row else None

    # =====================================
    # Log
    # =====================================

    def registrar_log(
        self, tipo_accion: str, descripcion: str, usuario_id: int | None = None
    ):
        """
        Inserta un registro de auditoría.
        Parámetros:
            tipo_accion:  constante de acción (ej. 'LOGIN', 'OCR', 'ERROR')
            descripcion:  texto libre descriptivo del evento
            usuario_id:   puede ser None para eventos anteriores al login
        """
        self._conn.execute(
            "INSERT INTO log (usuario_id, tipo_accion, descripcion, fecha) VALUES (?, ?, ?, ?)",
            (usuario_id, tipo_accion, descripcion, _ahora()),
        )
        self._conn.commit()

    def obtener_logs(self, usuario_id: int | None = None, limite: int = 100) -> list[dict]:
        """
        Devuelve los logs más recientes.
        Parámetros:
            usuario_id: si se indica, filtra los logs de ese usuario; None devuelve todos.
            limite:     máximo de registros a retornar (default 100).
        """
        if usuario_id is not None:
            rows = self._conn.execute(
                "SELECT * FROM log WHERE usuario_id = ? ORDER BY fecha DESC LIMIT ?",
                (usuario_id, limite),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM log ORDER BY fecha DESC LIMIT ?", (limite,)
            ).fetchall()
        return [dict(r) for r in rows]


# =====================================
# Utilidad interna
# =====================================

def _ahora() -> str:
    """Devuelve la fecha y hora actual en formato ISO 8601."""
    return datetime.now().isoformat()
