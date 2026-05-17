-- ============================================================
-- schema.sql — Asistente para Inclusión Digital
-- Define todas las tablas de la base de datos SQLite.
-- Ejecutado automáticamente por database.py al iniciar la app.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- Usuario
-- ============================================================
CREATE TABLE IF NOT EXISTS usuario (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre           TEXT    NOT NULL,
    apellido         TEXT    NOT NULL,
    username         TEXT    NOT NULL UNIQUE,
    password_hash    TEXT    NOT NULL,
    salt             TEXT    NOT NULL,
    algoritmo        TEXT    NOT NULL DEFAULT 'pbkdf2_hmac_sha256',
    iteraciones      INTEGER NOT NULL DEFAULT 200000,
    rol              TEXT    NOT NULL DEFAULT 'usuario',   -- 'usuario' | 'admin'
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta  TEXT                                  -- ISO 8601, NULL si no está bloqueado
);

-- ============================================================
-- Documento  (PDF, JPG, PNG)
-- ============================================================
CREATE TABLE IF NOT EXISTS documento (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER NOT NULL,
    ruta         TEXT    NOT NULL,
    tipo         TEXT    NOT NULL,                         -- 'PDF' | 'JPG' | 'PNG'
    fecha_subida TEXT    NOT NULL,                         -- ISO 8601
    estado       TEXT    NOT NULL DEFAULT 'cargado',       -- 'cargado' | 'procesado' | 'error'
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

-- ============================================================
-- Audio  (WAV, MP3)
-- ============================================================
CREATE TABLE IF NOT EXISTS audio (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER NOT NULL,
    ruta         TEXT    NOT NULL,
    tipo         TEXT    NOT NULL,                         -- 'WAV' | 'MP3'
    fecha_subida TEXT    NOT NULL,                         -- ISO 8601
    estado       TEXT    NOT NULL DEFAULT 'cargado',       -- 'cargado' | 'procesado' | 'error'
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

-- ============================================================
-- Proceso  (OCR, TTS, STT, RESUMEN)
-- ============================================================
CREATE TABLE IF NOT EXISTS proceso (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER NOT NULL,
    tipo         TEXT    NOT NULL,                         -- 'OCR' | 'TTS' | 'STT' | 'RESUMEN'
    entrada_id   INTEGER NOT NULL,                         -- FK hacia documento.id o audio.id
    entrada_tipo TEXT    NOT NULL,                         -- 'documento' | 'audio'
    fecha        TEXT    NOT NULL,                         -- ISO 8601
    estado       TEXT    NOT NULL DEFAULT 'pendiente',     -- 'pendiente' | 'en_proceso' | 'completado' | 'error'
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

-- ============================================================
-- Resultado  (archivo generado por un proceso)
-- ============================================================
CREATE TABLE IF NOT EXISTS resultado (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    proceso_id INTEGER NOT NULL,
    ruta       TEXT    NOT NULL,
    formato    TEXT    NOT NULL,                           -- 'txt' | 'mp3' | 'wav'
    fecha      TEXT    NOT NULL,                           -- ISO 8601
    FOREIGN KEY (proceso_id) REFERENCES proceso(id)
);

-- ============================================================
-- Log  (auditoría de todas las acciones relevantes)
-- ============================================================
CREATE TABLE IF NOT EXISTS log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER,                                   -- NULL para eventos previos al login
    tipo_accion TEXT    NOT NULL,                          -- 'LOGIN' | 'LOGOUT' | 'REGISTRO' | 'CARGA' | 'OCR' | 'TTS' | 'STT' | 'RESUMEN' | 'ERROR' | etc.
    descripcion TEXT    NOT NULL,
    fecha       TEXT    NOT NULL,                          -- ISO 8601
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);
