# Asistente para Inclusión Digital

Procesamiento accesible de documentos y audio — OCR · TTS · STT · Resumen automático

**Trabajo Final de Graduación — Licenciatura en Informática — Universidad Siglo 21**

---

## Descripción del Proyecto

El **Asistente para Inclusión Digital** es una aplicación de escritorio desarrollada en Python + Tkinter orientada a facilitar el acceso a información digital para personas con discapacidad visual o auditiva.

La aplicación integra en un único entorno:

- Carga de documentos (PDF, JPG, PNG) y archivos de audio (WAV, MP3)
- Reconocimiento óptico de caracteres (OCR) sobre imágenes y PDF escaneados
- Conversión de texto a voz (TTS) offline
- Transcripción de voz a texto (STT) mediante Whisper
- Generación automática de resúmenes de textos extensos
- Entrega de resultados en formato texto o audio
- Registro de actividad para auditoría
- Autenticación segura con bloqueo de cuenta tras intentos fallidos

Todo el procesamiento se realiza de forma **local y offline**. La única excepción es la descarga inicial de modelos (Whisper), que ocurre una sola vez.

---

## Arquitectura General

```
/
├── main.py                 # Punto de entrada
├── requirements.txt
│
├── /core
│   ├── ocr.py              # HU-003 — OCR con Tesseract
│   ├── tts.py              # HU-004 — Síntesis de voz con pyttsx3
│   ├── stt.py              # HU-005 — Transcripción con Whisper
│   └── summarizer.py       # HU-010 — Resumen extractivo con sumy
│
├── /security
│   ├── auth.py             # HU-001 — Autenticación y bloqueo de cuenta
│   └── logger.py           # HU-009 — Registro de eventos del sistema
│
├── /gui
│   ├── login_screen.py     # Pantalla de login y registro
│   ├── main_menu.py        # Menú principal
│   ├── document_upload.py  # HU-002/006 — Carga y validación de archivos
│   ├── content_view.py     # HU-003/008 — Visualización de resultados OCR/STT
│   ├── tts_screen.py       # HU-004/008 — Conversión texto a voz
│   └── history_screen.py   # HU-009 — Historial de actividad
│
├── /db
│   ├── schema.sql          # Definición de tablas SQLite
│   └── database.py         # Capa de acceso a datos
│
├── /storage                # Archivos generados (gitignored)
│   ├── /documents
│   ├── /audios
│   └── /outputs
│
└── /docs
    ├── HU.md
    ├── DER.png
    └── ClassDiagram.png
```

---

## Instalación

### Requisito previo 1 — Python 3.10 o superior

Verificar con:

```bash
python --version
```

Descargar desde [python.org](https://www.python.org/downloads/) si no está instalado.

---

### Requisito previo 2 — ffmpeg

ffmpeg es necesario para que Whisper (STT) pueda decodificar y convertir archivos de audio. Sin él, la transcripción falla al intentar procesar cualquier archivo.

**Windows**

```bash
winget install ffmpeg
```

O descargar el instalador desde https://ffmpeg.org/download.html y agregar la carpeta `bin/` al PATH del sistema.

Verificar la instalación:

```bash
ffmpeg -version
```

> Después de instalar ffmpeg es necesario **reiniciar la terminal** (o la aplicación) para que el nuevo PATH sea reconocido.

**Linux (Ubuntu/Debian)**

```bash
sudo apt update
sudo apt install ffmpeg
```

---

### Requisito previo 3 — Tesseract OCR

Tesseract es el motor de reconocimiento de texto que usa el módulo OCR. Debe instalarse a nivel del sistema operativo, no mediante pip.

**Windows**

1. Descargar el instalador desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Ejecutar el instalador (recomendado: instalar en `C:\Program Files\Tesseract-OCR\`)
3. Durante la instalación, seleccionar el paquete de idioma **Spanish** (o instalarlo después)
4. Agregar Tesseract al PATH del sistema:
   - Panel de control → Variables de entorno → PATH → agregar `C:\Program Files\Tesseract-OCR\`
5. Verificar la instalación:
   ```bash
   tesseract --version
   ```

**Linux (Ubuntu/Debian)**

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-spa
```

**Verificar que el idioma español está disponible:**

```bash
tesseract --list-langs
# Debe aparecer "spa" en la lista
```

---

### Paso 1 — Clonar el repositorio y crear entorno virtual

```bash
git clone <url-del-repositorio>
cd asistente-inclusion-digital

# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (Linux/macOS)
source venv/bin/activate
```

---

### Paso 2 — Instalar dependencias Python

```bash
pip install -r requirements.txt
```

> **Nota sobre `openai-whisper`:** este paquete descarga PyTorch como dependencia (~2–3 GB). La instalación puede tardar varios minutos según la velocidad de conexión. Es una descarga única.

---

### Paso 3 — Descargar datos de NLTK

El módulo de resumen automático (sumy) requiere los tokenizadores de NLTK para español. Ejecutar una sola vez:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

Los datos se guardan en `~/nltk_data/` y no necesitan descargarse nuevamente.

---

### Paso 4 — Primera ejecución (descarga del modelo Whisper)

Al usar la función de transcripción (STT) por primera vez, Whisper descarga automáticamente el modelo `base` (~140 MB) en `~/.cache/whisper/`. Esta descarga ocurre una sola vez; las ejecuciones siguientes son completamente offline.

Para predescargar el modelo antes de usar la app:

```bash
python -c "import whisper; whisper.load_model('base')"
```

---

### Paso 5 — Ejecutar la aplicación

```bash
python main.py
```

La base de datos SQLite se crea automáticamente en `storage/app.db` en el primer arranque.

---

## Librerías principales

| Librería | Versión mínima | Propósito |
|---|---|---|
| Tkinter | (incluida en Python) | Interfaz gráfica |
| Pillow | 10.0.0 | Manejo de imágenes |
| PyMuPDF | 1.23.0 | Lectura y renderizado de PDF |
| pytesseract | 0.3.10 | Wrapper de Tesseract OCR |
| pyttsx3 | 2.90 | Síntesis de voz offline |
| openai-whisper | 20231117 | Transcripción de voz offline |
| sumy | 0.11.0 | Generación de resúmenes extractivos |
| numpy | 1.24.0 | Requerido por sumy/LexRank |
| sqlite3 | (incluida en Python) | Base de datos local |

---

## Funcionalidades por Historia de Usuario

| HU | Funcionalidad | Sprint |
|---|---|---|
| HU-001 | Registro de usuario y autenticación segura | 1 |
| HU-002 | Carga de documentos y archivos de audio | 1 |
| HU-003 | Procesamiento OCR | 2 |
| HU-004 | Conversión de texto a voz (TTS) | 2 |
| HU-005 | Transcripción de voz a texto (STT) | 2 |
| HU-006 | Validación de formato y tamaño | 1 |
| HU-007 | Retroalimentación visual y auditiva | 1 |
| HU-008 | Entrega de resultados accesibles | 2 |
| HU-009 | Registro de logs de actividad | 3 |
| HU-010 | Generación de resumen automático | 3 |

---

## Seguridad

- Contraseñas hasheadas con **PBKDF2-HMAC-SHA256** + sal única por usuario + 200 000 iteraciones mínimas
- Bloqueo temporal de cuenta tras **5 intentos fallidos** (15 minutos)
- Registro de todos los eventos relevantes en la tabla de logs
- Los archivos binarios (documentos, audios, resultados) nunca se guardan en la base de datos: solo rutas y metadatos

---

## Documentación adicional

- `docs/HU.md` — Detalle completo de las historias de usuario
- `docs/DER.png` — Diagrama entidad-relación de la base de datos
- `docs/ClassDiagram.png` — Diagrama de clases del prototipo

---

## Autor

**Ignacio Ulises Imbrogno**
Legajo: VINF10215
Universidad Siglo 21 — Buenos Aires, 2025
