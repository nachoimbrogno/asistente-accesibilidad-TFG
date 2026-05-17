"""
Módulo: auth.py
HU-001 — Registro de usuario / autenticación segura
Gestiona el registro de nuevos usuarios y la autenticación con bloqueo por intentos fallidos.
Toda contraseña se hashea con PBKDF2-HMAC-SHA256 + sal única. Nunca se almacena en claro.
"""

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timedelta

from db.database import Database
from security.logger import Logger, BLOQUEO, LOGIN_FALLO, LOGIN_OK, REGISTRO

# =====================================
# Configuración de seguridad
# =====================================

ITERACIONES      = 200_000
ALGORITMO        = "pbkdf2_hmac_sha256"
INTENTOS_MAX     = 5
MINUTOS_BLOQUEO  = 15

# Campos sensibles que nunca se exponen fuera de este módulo
_CAMPOS_PRIVADOS = {"password_hash", "salt", "algoritmo", "iteraciones"}


# =====================================
# API pública
# =====================================

def registrar_usuario(
    db: Database,
    logger: Logger,
    nombre: str,
    apellido: str,
    username: str,
    password: str,
    rol: str = "usuario",
) -> dict:
    """
    Crea una cuenta nueva con contraseña hasheada.
    Devuelve un dict con la clave 'exito'. Si falla, incluye 'motivo'.

    Motivos posibles de fallo:
        'campos_vacios'    — algún campo obligatorio está en blanco
        'username_en_uso'  — ya existe un usuario con ese username
        'error_interno'    — fallo inesperado al insertar en la BD
    """
    # =====================================
    # Validación de entradas
    # =====================================
    if not all([nombre.strip(), apellido.strip(), username.strip(), password]):
        return {"exito": False, "motivo": "campos_vacios"}

    # =====================================
    # Hash de la contraseña
    # =====================================
    hash_hex, salt_hex = _hashear_password(password)

    # =====================================
    # Inserción en la base de datos
    # =====================================
    try:
        usuario_id = db.crear_usuario(
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            username=username.strip(),
            password_hash=hash_hex,
            salt=salt_hex,
            algoritmo=ALGORITMO,
            iteraciones=ITERACIONES,
            rol=rol,
        )
    except sqlite3.IntegrityError:
        return {"exito": False, "motivo": "username_en_uso"}
    except Exception as e:
        logger.log(REGISTRO, f"Error al crear usuario '{username}': {e}")
        return {"exito": False, "motivo": "error_interno"}

    logger.log(REGISTRO, f"Usuario registrado: '{username}'", usuario_id=usuario_id)
    return {"exito": True, "usuario_id": usuario_id}


def autenticar(db: Database, logger: Logger, username: str, password: str) -> dict:
    """
    Verifica credenciales y gestiona el bloqueo por intentos fallidos.
    Devuelve un dict con la clave 'exito'. Si es exitoso, incluye 'usuario' (sin datos sensibles).

    Motivos posibles de fallo:
        'credenciales_invalidas' — usuario inexistente o contraseña incorrecta
                                   (ambos casos devuelven el mismo motivo por seguridad)
        'cuenta_bloqueada'       — demasiados intentos fallidos; incluye 'bloqueado_hasta'
    """
    usuario = db.obtener_usuario_por_username(username)

    # Usuario inexistente: mismo mensaje que contraseña incorrecta para evitar enumeración
    if usuario is None:
        logger.log(LOGIN_FALLO, f"Intento de login con username inexistente: '{username}'")
        return {"exito": False, "motivo": "credenciales_invalidas"}

    # =====================================
    # Verificación de bloqueo
    # =====================================
    resultado_bloqueo = _verificar_bloqueo(db, usuario)
    if resultado_bloqueo is not None:
        return resultado_bloqueo

    # =====================================
    # Verificación de contraseña
    # =====================================
    password_ok = _verificar_password(
        password,
        usuario["password_hash"],
        usuario["salt"],
        usuario["iteraciones"],
    )

    if not password_ok:
        return _registrar_intento_fallido(db, logger, usuario)

    # =====================================
    # Login exitoso
    # =====================================
    db.resetear_intentos_fallidos(usuario["id"])
    logger.log(LOGIN_OK, f"Login exitoso: '{username}'", usuario_id=usuario["id"])
    return {"exito": True, "usuario": _datos_publicos(usuario)}


# =====================================
# Funciones internas
# =====================================

def _hashear_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    """
    Aplica PBKDF2-HMAC-SHA256 a la contraseña.
    Si no se pasa salt, genera uno aleatorio de 32 bytes.
    Devuelve (hash_hex, salt_hex).
    """
    if salt_hex is None:
        salt_hex = os.urandom(32).hex()
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        ITERACIONES,
    )
    return hash_bytes.hex(), salt_hex


def _verificar_password(password: str, hash_hex: str, salt_hex: str, iteraciones: int) -> bool:
    """
    Compara la contraseña ingresada contra el hash almacenado.
    Usa comparación en tiempo constante para prevenir ataques de timing.
    """
    hash_intento = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        iteraciones,
    )
    return hmac.compare_digest(hash_intento.hex(), hash_hex)


def _verificar_bloqueo(db: Database, usuario: dict) -> dict | None:
    """
    Revisa si el usuario está actualmente bloqueado.
    Si el bloqueo ya expiró lo limpia automáticamente.
    Devuelve un dict de error si sigue bloqueado, o None si puede continuar.
    """
    bloqueado_hasta = usuario["bloqueado_hasta"]
    if not bloqueado_hasta:
        return None

    limite = datetime.fromisoformat(bloqueado_hasta)
    if datetime.now() < limite:
        return {
            "exito": False,
            "motivo": "cuenta_bloqueada",
            "bloqueado_hasta": bloqueado_hasta,
        }

    # El bloqueo expiró: se limpia para no penalizar en el siguiente intento
    db.resetear_intentos_fallidos(usuario["id"])
    return None


def _registrar_intento_fallido(db: Database, logger: Logger, usuario: dict) -> dict:
    """
    Incrementa el contador de intentos fallidos.
    Si se alcanza INTENTOS_MAX, bloquea la cuenta durante MINUTOS_BLOQUEO.
    Devuelve el dict de respuesta correspondiente.
    """
    intentos = usuario["intentos_fallidos"] + 1

    if intentos >= INTENTOS_MAX:
        bloqueado_hasta = (datetime.now() + timedelta(minutes=MINUTOS_BLOQUEO)).isoformat()
        db.actualizar_intentos_fallidos(usuario["id"], intentos, bloqueado_hasta)
        logger.log(
            BLOQUEO,
            f"Cuenta bloqueada por {MINUTOS_BLOQUEO} min tras {intentos} intentos fallidos",
            usuario_id=usuario["id"],
        )
        return {
            "exito": False,
            "motivo": "cuenta_bloqueada",
            "bloqueado_hasta": bloqueado_hasta,
        }

    db.actualizar_intentos_fallidos(usuario["id"], intentos)
    logger.log(
        LOGIN_FALLO,
        f"Contraseña incorrecta para '{usuario['username']}' (intento {intentos}/{INTENTOS_MAX})",
        usuario_id=usuario["id"],
    )
    return {"exito": False, "motivo": "credenciales_invalidas"}


def _datos_publicos(usuario: dict) -> dict:
    """Filtra los campos sensibles antes de exponer el dict de usuario al resto de la app."""
    return {k: v for k, v in usuario.items() if k not in _CAMPOS_PRIVADOS}
