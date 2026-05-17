# Asistente para Inclusión Digital — TFG

## Contexto del proyecto
Aplicación de escritorio (Windows/Linux) que integra en un único entorno funciones de accesibilidad digital para personas con discapacidad visual o auditiva. Es el prototipo del Trabajo Final de Graduación de la Licenciatura en Informática (Universidad Siglo 21).

## Stack
- Lenguaje: Python 3.10+
- GUI: Tkinter (estándar de Python)
- OCR: Tesseract OCR vía pytesseract
- TTS: pyttsx3 (offline)
- STT: openai-whisper (offline)
- Resumen NLP: sumy (extractivo, offline)
- Base de datos: SQLite (sqlite3 de la stdlib)
- Hash de contraseñas: hashlib con PBKDF2-HMAC-SHA256

## Filosofía del proyecto
Todo el procesamiento es **local y offline**. No se permiten dependencias de servicios en la nube ni de APIs externas que requieran conexión a internet en tiempo de ejecución. La autonomía operativa es un requisito no funcional crítico.

## Estructura del proyecto
/
├── main.py                 # Punto de entrada
├── README.md               # Descripción general del proyecto (para humanos)
├── CLAUDE.md               # Este archivo (instrucciones para Claude Code)
├── /db
│   ├── schema.sql          # Definición de tablas
│   └── database.py         # Capa de acceso a datos
├── /core                   # Lógica de los módulos
│   ├── ocr.py
│   ├── tts.py
│   ├── stt.py
│   └── summarizer.py
├── /security
│   ├── auth.py             # Login, hash, bloqueo de cuenta
│   └── logger.py           # Registro de eventos del sistema
├── /gui                    # Pantallas Tkinter
│   ├── login_screen.py
│   ├── main_menu.py
│   ├── document_upload.py
│   ├── content_view.py
│   ├── tts_screen.py
│   └── history_screen.py
├── /storage                # Archivos generados (gitignored)
├── /docs                   # Documentación del TFG
│   ├── DER.png
│   ├── ClassDiagram.png
│   └── HU.md
└── requirements.txt

## Entidades del modelo de datos
- **Usuario**: id, nombre, apellido, username, password_hash, salt, algoritmo, iteraciones, rol, intentos_fallidos, bloqueado_hasta
- **Documento**: id, usuario_id, ruta, tipo, fecha_subida, estado
- **Audio**: id, usuario_id, ruta, tipo, fecha_subida, estado
- **Proceso**: id, usuario_id, tipo (OCR/TTS/STT/RESUMEN), entrada_id, entrada_tipo, fecha, estado
- **Resultado**: id, proceso_id, ruta, formato, fecha
- **Log**: id, usuario_id, tipo_accion, descripcion, fecha

Los archivos binarios (PDF, imágenes, audios) NO se guardan en la BD: van al sistema de archivos en `/storage/`, y en la BD se guardan rutas + metadatos.

## Convenciones de código
- Naming: `snake_case` para funciones y variables; `PascalCase` para clases
- Strings con f-strings, nunca con concatenación `+`
- Logging: usar el módulo `security/logger.py` para registrar eventos, no `print()`
- Manejo de errores: try/except con mensajes específicos; nunca `except:` pelado
- Path handling: usar `pathlib.Path`, no strings concatenados con `os.path`
- Idioma: comentarios y mensajes de UI en español; nombres de funciones/variables en inglés

## Estilo de documentación en el código
Cada función o bloque importante debe tener comentarios que permitan entender qué hace al leerlo. Reglas concretas:

- **Docstring obligatorio** al inicio de cada función pública (formato triple comilla).
  - Una línea inicial que explique qué hace la función en lenguaje claro.
  - Si aplica, describir parámetros, retorno y excepciones.
- **Encabezado de archivo**: cada archivo `.py` empieza con un docstring que indique el módulo, la HU asociada (si aplica) y una breve descripción.
- **Bloques importantes dentro de funciones largas**: separarlos con comentarios tipo banner para facilitar la lectura:
```python
  # =====================================
  # Login
  # =====================================
```
- **Comentarios inline** solo cuando la lógica no es obvia. No describir lo que el código ya dice claramente.
- Comentarios y docstrings **en español**.

Ejemplo de cabecera de archivo:
```python
"""
Módulo: historial.py
HU-XXX — Descripción de la HU asociada
Permite [qué hace este módulo en términos funcionales].
"""
```

Ejemplo de función documentada:
```python
def extract_text_from_pdf(pdf_path):
    """
    Procesa un PDF.
    - Si tiene texto embebido → lo extrae directo.
    - Si NO tiene texto → aplica OCR página por página.
    Devuelve el texto extraído como string.
    """
    ...
```

## Reglas de seguridad
- Contraseñas: SIEMPRE hasheadas con PBKDF2-HMAC-SHA256 + sal única por usuario + ≥200000 iteraciones
- Tras 5 intentos fallidos: bloqueo temporal de la cuenta
- Toda acción relevante (login, carga, proceso, error) debe registrarse en la tabla Log
- Nunca loguear contraseñas, hashes ni datos sensibles del usuario

## Reglas de accesibilidad
- Botones grandes, alto contraste, navegables por teclado
- Toda acción debe dar feedback visual y/o auditivo
- Mensajes de error claros y descriptivos
- Pensar siempre en usuarios con lectores de pantalla externos (compatibilidad con JAWS/NVDA)
- Atajos de teclado globales para acciones frecuentes (login, registro, salir, etc.)

## Comandos útiles
```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Correr la aplicación
python main.py
```

## Referencias del TFG
- HUs detalladas: `docs/HU.md`
- DER: `docs/DER.png`
- Diagrama de clases: `docs/ClassDiagram.png`