# Historias de Usuario — Asistente para Inclusión Digital

Este archivo contiene el detalle de las 10 Historias de Usuario del prototipo, agrupadas por sprint según fueron planificadas en el Trabajo Final de Graduación.

---

## Sprint 1 — Registro, carga y retroalimentación

### HU-001 — Registro de usuario

| Elemento | Descripción |
|---|---|
| **ID** | HU-001 |
| **Nombre** | Registro de usuario |
| **Descripción** | Como usuario, quiero registrarme en el sistema para poder iniciar sesión y gestionar mis documentos personales. |
| **Criterios de aceptación** | Dado que el usuario accede al sistema por primera vez, cuando completa correctamente el formulario de registro, entonces el sistema debe crear una cuenta y permitir su autenticación. |
| **Prioridad** | Alta |
| **Puntos de historia** | 8 |
| **Dependencias** | — |

---

### HU-002 — Carga de documentos o archivos de audio

| Elemento | Descripción |
|---|---|
| **ID** | HU-002 |
| **Nombre** | Carga de documentos o archivos de audio |
| **Descripción** | Como usuario, quiero cargar documentos o archivos de audio en distintos formatos para poder procesarlos dentro del sistema. |
| **Criterios de aceptación** | Dado que el usuario se encuentra autenticado, cuando selecciona un archivo compatible y lo sube, entonces el sistema debe almacenarlo correctamente y mostrar un mensaje de confirmación. |
| **Prioridad** | Alta |
| **Puntos de historia** | 13 |
| **Dependencias** | HU-001 |

---

### HU-006 — Validación de formato y tamaño

| Elemento | Descripción |
|---|---|
| **ID** | HU-006 |
| **Nombre** | Validación de formato y tamaño |
| **Descripción** | Como usuario, quiero que el sistema valide automáticamente el formato y tamaño de los archivos cargados para evitar errores durante el procesamiento. |
| **Criterios de aceptación** | Dado un archivo incompatible o de gran tamaño, cuando el usuario intenta subirlo, entonces el sistema debe rechazarlo y mostrar un mensaje informativo. Dado que el archivo cumple los requisitos, cuando se carga correctamente, entonces el sistema debe habilitar el botón de procesamiento. |
| **Prioridad** | Alta |
| **Puntos de historia** | 5 |
| **Dependencias** | HU-002 |

---

### HU-007 — Retroalimentación visual y auditiva

| Elemento | Descripción |
|---|---|
| **ID** | HU-007 |
| **Nombre** | Retroalimentación visual y auditiva |
| **Descripción** | Como usuario, quiero recibir mensajes visuales o auditivos que confirmen el estado de las operaciones (éxito, error, progreso) para comprender fácilmente el funcionamiento del sistema. |
| **Criterios de aceptación** | Dado que el usuario ejecuta una operación (carga, procesamiento o conversión), cuando el sistema finaliza la acción, entonces debe mostrar o reproducir un mensaje confirmando el estado. |
| **Prioridad** | Media |
| **Puntos de historia** | 5 |
| **Dependencias** | HU-002, HU-003 |

---

## Sprint 2 — Módulos core de accesibilidad y entrega

### HU-003 — Procesamiento OCR

| Elemento | Descripción |
|---|---|
| **ID** | HU-003 |
| **Nombre** | Procesamiento OCR |
| **Descripción** | Como usuario, quiero que el sistema convierta mis imágenes o documentos escaneados en texto accesible mediante reconocimiento óptico de caracteres. |
| **Criterios de aceptación** | Dado que el documento fue cargado, cuando se inicia el procesamiento, entonces el sistema debe devolver un texto legible y exportable en formato .txt. |
| **Prioridad** | Alta |
| **Puntos de historia** | 10 |
| **Dependencias** | HU-002 |

---

### HU-004 — Conversión de texto a voz (TTS)

| Elemento | Descripción |
|---|---|
| **ID** | HU-004 |
| **Nombre** | Conversión de texto a voz (TTS) |
| **Descripción** | Como usuario con discapacidad visual, quiero convertir texto a voz natural para escuchar el contenido sin necesidad de leerlo. |
| **Criterios de aceptación** | Dado un texto procesado, cuando se selecciona la opción de conversión a voz, entonces el sistema debe generar un archivo de audio reproducible y comprensible. |
| **Prioridad** | Media |
| **Puntos de historia** | 8 |
| **Dependencias** | HU-003 |

---

### HU-005 — Transcripción de voz a texto (STT)

| Elemento | Descripción |
|---|---|
| **ID** | HU-005 |
| **Nombre** | Transcripción de voz a texto (STT) |
| **Descripción** | Como usuario con discapacidad auditiva, quiero transcribir un archivo de audio a texto para poder leer su contenido. |
| **Criterios de aceptación** | Dado un archivo de audio válido, cuando el usuario lo selecciona y confirma el procesamiento, entonces el sistema transcribe el contenido y muestra el texto resultante. Dado un archivo con formato no admitido, cuando intenta cargarse, entonces el sistema muestra un mensaje de error y no inicia la transcripción. |
| **Prioridad** | Alta |
| **Puntos de historia** | 8 |
| **Dependencias** | HU-002 |

---

### HU-008 — Entrega de resultados accesibles

| Elemento | Descripción |
|---|---|
| **ID** | HU-008 |
| **Nombre** | Entrega de resultados accesibles |
| **Descripción** | Como usuario, quiero recibir los resultados de los procesos en formatos accesibles (texto o audio) para poder utilizarlos según mis necesidades. |
| **Criterios de aceptación** | Dado que el usuario completa un proceso (OCR, TTS o STT), cuando selecciona la opción de descarga, entonces el sistema debe permitir guardar o reproducir el resultado en el formato elegido. Dado que el usuario no selecciona formato, entonces el sistema debe mostrar una advertencia solicitando la elección antes de continuar. |
| **Prioridad** | Alta |
| **Puntos de historia** | 8 |
| **Dependencias** | HU-004, HU-005 |

---

## Sprint 3 — Auditoría y funcionalidades complementarias

### HU-009 — Registro de logs de actividad

| Elemento | Descripción |
|---|---|
| **ID** | HU-009 |
| **Nombre** | Registro de logs de actividad |
| **Descripción** | Como administrador, quiero disponer de un registro de actividad del sistema para poder auditar acciones y detectar errores. |
| **Criterios de aceptación** | Dado que se produce una acción en el sistema, cuando se ejecuta cualquier proceso, entonces el sistema debe registrar el evento en el log con fecha, hora y tipo de acción. |
| **Prioridad** | Baja |
| **Puntos de historia** | 2 |
| **Dependencias** | HU-001 |

---

### HU-010 — Generación de resumen automático

| Elemento | Descripción |
|---|---|
| **ID** | HU-010 |
| **Nombre** | Generación de resumen automático |
| **Descripción** | Como usuario, quiero generar automáticamente un resumen de un texto extenso obtenido tras un proceso OCR o STT, para acceder a su contenido principal de forma más rápida y accesible. |
| **Criterios de aceptación** | Dado un texto procesado de longitud suficiente, cuando el usuario selecciona la opción "Generar resumen", entonces el sistema produce un resumen extractivo mediante la librería sumy y lo presenta en pantalla con opciones para guardar como .txt o enviarlo al módulo TTS. Dado un texto demasiado corto para resumir, cuando el usuario intenta la acción, entonces el sistema muestra un mensaje informativo y no ejecuta el proceso. |
| **Prioridad** | Media |
| **Puntos de historia** | 5 |
| **Dependencias** | HU-003 |

---

## Resumen del Product Backlog

| ID | Nombre | Prioridad | Puntos | Sprint |
|---|---|---|---|---|
| HU-001 | Registro de usuario | Alta | 8 | 1 |
| HU-002 | Carga de documentos o audios | Alta | 13 | 1 |
| HU-003 | Procesamiento OCR | Alta | 10 | 2 |
| HU-004 | Conversión texto a voz (TTS) | Media | 8 | 2 |
| HU-005 | Transcripción voz a texto (STT) | Alta | 8 | 2 |
| HU-006 | Validación formato y tamaño | Alta | 5 | 1 |
| HU-007 | Retroalimentación visual/auditiva | Media | 5 | 1 |
| HU-008 | Entrega de resultados accesibles | Alta | 8 | 2 |
| HU-009 | Registro de logs de actividad | Baja | 2 | 3 |
| HU-010 | Generación de resumen automático | Media | 5 | 3 |

**Total:** 72 puntos de historia distribuidos en 3 sprints.