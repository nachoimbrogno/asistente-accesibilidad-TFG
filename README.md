# 📘 Asistente para Inclusión Digital

Procesamiento accesible de documentos y audio — OCR · TTS · STT · Resumen automático

**Trabajo Final de Graduación — Licenciatura en Informática — Universidad Siglo 21**

---

## 📑 Descripción del Proyecto

El **Asistente para Inclusión Digital** es una aplicación de escritorio desarrollada en Python + Tkinter orientada a facilitar el acceso a información digital para personas con discapacidad visual o auditiva.

La aplicación integra en un único entorno funciones de accesibilidad que actualmente se encuentran dispersas en herramientas independientes:

- Carga de documentos (PDF, JPG, PNG)
- Carga de archivos de audio (WAV, MP3)
- Reconocimiento óptico de caracteres (OCR) sobre imágenes y PDF escaneados
- Conversión de texto a voz (TTS) offline
- Transcripción de voz a texto (STT) mediante Whisper
- Generación automática de resúmenes de textos extensos
- Entrega de resultados accesibles en formato texto o audio
- Registro de actividad para auditoría
- Autenticación segura con bloqueo de cuenta

Todo el procesamiento se realiza de forma **local y offline**, sin requerir conexión a internet ni dependencia de servicios externos.

---

## 🏗️ Arquitectura General
/
├── main.py
├── README.md
├── CLAUDE.md
├── requirements.txt
│
├── /core
│   ├── ocr.py
│   ├── tts.py
│   ├── stt.py
│   └── summarizer.py
│
├── /security
│   ├── auth.py
│   └── logger.py
│
├── /gui
│   ├── login_screen.py
│   ├── main_menu.py
│   ├── document_upload.py
│   ├── content_view.py
│   ├── tts_screen.py
│   └── history_screen.py
│
├── /db
│   ├── database.py
│   └── schema.sql
│
├── /storage
│   ├── /documents
│   ├── /audios
│   └── /outputs
│
└── /docs
├── DER.png
├── ClassDiagram.png
└── HU.md

---

## 🚀 Instalación

### 1️⃣ Requisitos previos

- Python 3.10 o superior
- Tesseract OCR instalado a nivel sistema operativo
- pip actualizado

### 2️⃣ Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux
```

### 3️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### Librerías principales

| Librería | Propósito |
|---|---|
| Tkinter | Interfaz gráfica |
| Pillow | Manejo de imágenes |
| pytesseract | Wrapper de Tesseract OCR |
| pyttsx3 | Síntesis de voz offline |
| openai-whisper | Transcripción de voz offline |
| sumy | Generación de resúmenes extractivos |
| PyMuPDF | Lectura de PDF |
| sqlite3 | Base de datos local (incluido en Python) |

---

## ▶️ Ejecución

Desde la raíz del proyecto:

```bash
python main.py
```

La base de datos se crea automáticamente en el primer arranque si no existe.

---

## 🧩 Funcionalidades por Historia de Usuario

| HU | Funcionalidad | Sprint |
|---|---|---|
| **HU-001** | Registro de usuario | 1 |
| **HU-002** | Carga de documentos o archivos de audio | 1 |
| **HU-003** | Procesamiento OCR | 2 |
| **HU-004** | Conversión de texto a voz (TTS) | 2 |
| **HU-005** | Transcripción de voz a texto (STT) | 2 |
| **HU-006** | Validación de formato y tamaño | 1 |
| **HU-007** | Retroalimentación visual y auditiva | 1 |
| **HU-008** | Entrega de resultados accesibles | 2 |
| **HU-009** | Registro de logs de actividad | 3 |
| **HU-010** | Generación de resumen automático | 3 |

---

## 🔐 Seguridad

- Autenticación local con hash **PBKDF2-HMAC-SHA256**
- Sal única por usuario y mínimo de 200.000 iteraciones
- Bloqueo temporal de cuenta tras 5 intentos fallidos
- Registro de todos los eventos críticos en tabla de logs
- Política de respaldo local en unidad externa

---

## 🧪 Pruebas Realizadas

- Registro y autenticación de usuarios
- Bloqueo y desbloqueo de cuenta
- OCR con diversos formatos de imagen y PDF
- Conversión de texto a voz con distintas longitudes de entrada
- Transcripción de audios en español
- Generación de resúmenes automáticos
- Persistencia en base de datos
- Trazabilidad mediante logs
- Accesibilidad mediante atajos de teclado y navegación por foco

---

## 📚 Documentación adicional

- `docs/HU.md` — Detalle completo de las historias de usuario
- `docs/DER.png` — Diagrama entidad-relación de la base de datos
- `docs/ClassDiagram.png` — Diagrama de clases del prototipo

---

## 👤 Autor

**Ignacio Ulises Imbrogno**
Legajo: VINF10215
Universidad Siglo 21 — Buenos Aires, 2025