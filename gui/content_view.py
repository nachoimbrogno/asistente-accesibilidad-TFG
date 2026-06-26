"""
Módulo: content_view.py
HU-003 — Procesamiento OCR
HU-008 — Entrega de resultados accesibles
Pantalla de procesamiento y visualización de texto extraído.
Ejecuta OCR o STT en un hilo de fondo para no bloquear la interfaz y muestra
el texto resultante con opciones de guardado (.txt) y envío a la pantalla de TTS.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from core import ocr, stt, summarizer
from db.database import Database
from security.logger import ERROR, OCR as LOG_OCR, RESUMEN as LOG_RESUMEN, STT as LOG_STT, Logger

# =====================================
# Configuración por modo de procesamiento
# =====================================

_CONFIG_MODO = {
    "documento": {
        "titulo":       "Resultado del OCR",
        "tipo_proceso": "OCR",
        "log_accion":   LOG_OCR,
        "msg_cargando": "Aplicando reconocimiento de texto (OCR)...\nEsto puede tardar unos segundos según el tamaño del archivo.",
    },
    "audio": {
        "titulo":       "Resultado de la transcripción",
        "tipo_proceso": "STT",
        "log_accion":   LOG_STT,
        "msg_cargando": "Transcribiendo audio con Whisper...\nEsto puede tardar varios segundos.",
    },
}

# =====================================
# Paleta de colores
# =====================================

_FONDO      = "#1e1e2e"
_HEADER     = "#16213e"
_CARD       = "#2d2d3d"
_TEXTO      = "#e0e0e0"
_TENUE      = "#a0a0b0"
_ACENTO     = "#5b8dee"
_ACENTO_ACT = "#4a7ce0"
_ERROR      = "#f05050"
_EXITO      = "#50c878"
_FUENTE     = "Segoe UI"


class ContentView(tk.Frame):
    """
    Pantalla de procesamiento y visualización de texto extraído (OCR o STT).

    Flujo:
        1. Al montarse lanza el procesamiento en un hilo de fondo.
        2. Muestra un indicador de carga mientras trabaja.
        3. Al terminar, presenta el texto en un área scrolleable.
        4. Ofrece botones para guardar el .txt, enviarlo a TTS o generar un resumen.

    Parámetros:
        master:      ventana o frame padre.
        usuario:     dict con datos del usuario autenticado.
        db:          instancia activa de Database.
        logger:      instancia activa de Logger.
        archivo_id:  id del documento (modo 'documento') o audio (modo 'audio') en la BD.
        modo:        'documento' | 'audio'
        on_volver:   callback para regresar al menú principal.
        on_ir_tts:   callable(texto: str) para abrir la pantalla TTS con el texto pre-cargado.
    """

    def __init__(
        self,
        master: tk.Misc,
        usuario: dict,
        db: Database,
        logger: Logger,
        archivo_id: int,
        modo: str,
        on_volver,
        on_ir_tts,
    ):
        super().__init__(master, bg=_FONDO)
        self._usuario   = usuario
        self._db        = db
        self._logger    = logger
        self._archivo_id = archivo_id
        self._modo      = modo
        self._cfg       = _CONFIG_MODO[modo]
        self._on_volver = on_volver
        self._on_ir_tts = on_ir_tts

        self._texto_resultado: str | None  = None
        self._ruta_txt: Path | None        = None
        self._proceso_id: int | None       = None

        self.pack(fill=tk.BOTH, expand=True)
        self._construir_header()
        self._construir_cuerpo()
        self._iniciar_procesamiento()

    # =====================================
    # Header
    # =====================================

    def _construir_header(self):
        """Barra superior con botón de volver y título del proceso activo."""
        header = tk.Frame(self, bg=_HEADER, pady=14, padx=24)
        header.pack(fill=tk.X)

        tk.Button(
            header,
            text="← Volver",
            command=self._on_volver,
            bg=_HEADER, fg=_ACENTO,
            activebackground=_HEADER, activeforeground=_ACENTO_ACT,
            font=(_FUENTE, 10),
            relief=tk.FLAT, cursor="hand2", bd=0,
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text=self._cfg["titulo"],
            bg=_HEADER, fg=_TEXTO,
            font=(_FUENTE, 13, "bold"),
        ).pack(side=tk.LEFT, padx=20)

    # =====================================
    # Cuerpo
    # =====================================

    def _construir_cuerpo(self):
        """
        Crea el área central con tres zonas:
          - indicador de carga (visible durante el procesamiento)
          - área de texto scrolleable (visible tras el procesamiento)
          - barra de acciones (visible tras el procesamiento)
        """
        self._cuerpo = tk.Frame(self, bg=_FONDO, padx=40, pady=30)
        self._cuerpo.pack(fill=tk.BOTH, expand=True)

        # Indicador de carga — centrado verticalmente mientras se procesa
        self._lbl_cargando = tk.Label(
            self._cuerpo,
            text=self._cfg["msg_cargando"],
            bg=_FONDO, fg=_TENUE,
            font=(_FUENTE, 11),
            justify=tk.CENTER,
        )
        self._lbl_cargando.pack(expand=True)

        # Área de texto scrolleable (oculta hasta que haya resultado)
        self._frame_texto = tk.Frame(self._cuerpo, bg=_CARD)
        self._txt_resultado = tk.Text(
            self._frame_texto,
            bg=_CARD, fg=_TEXTO,
            insertbackground=_TEXTO,
            font=(_FUENTE, 11),
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=16, pady=14,
            state=tk.DISABLED,
        )
        scrollbar = tk.Scrollbar(self._frame_texto, command=self._txt_resultado.yview)
        self._txt_resultado.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Barra de acciones (oculta hasta que haya resultado)
        self._frame_botones = tk.Frame(self._cuerpo, bg=_FONDO)
        self._construir_botones()

    def _construir_botones(self):
        """Crea los botones de acción que se muestran una vez finalizado el procesamiento."""
        especificaciones = [
            ("Guardar como .txt",  self._guardar_txt,      _ACENTO, "#ffffff", True),
            ("Convertir a voz",    self._enviar_a_tts,     _CARD,   _TEXTO,   False),
            ("Generar resumen",    self._generar_resumen,  _CARD,   _TEXTO,   False),
        ]
        for texto, cmd, bg, fg, negrita in especificaciones:
            tk.Button(
                self._frame_botones,
                text=texto,
                command=cmd,
                bg=bg, fg=fg,
                activebackground=_ACENTO_ACT if bg == _ACENTO else "#383850",
                activeforeground="#ffffff" if bg == _ACENTO else _TEXTO,
                font=(_FUENTE, 10, "bold" if negrita else "normal"),
                relief=tk.FLAT, cursor="hand2",
                padx=16, pady=8,
            ).pack(side=tk.LEFT, padx=(0, 10))

    # =====================================
    # Procesamiento en hilo de fondo
    # =====================================

    def _iniciar_procesamiento(self):
        """Registra el proceso en la BD y lanza el hilo de fondo para OCR / STT."""
        self._proceso_id = self._db.registrar_proceso(
            self._usuario["id"],
            self._cfg["tipo_proceso"],
            self._archivo_id,
            self._modo,
        )
        self._db.actualizar_estado_proceso(self._proceso_id, "en_proceso")

        hilo = threading.Thread(target=self._procesar_en_hilo, daemon=True)
        hilo.start()

    def _procesar_en_hilo(self):
        """
        Corre OCR o STT fuera del hilo principal de Tkinter.
        Delega la actualización de la UI al hilo principal mediante after().
        """
        try:
            archivo  = self._obtener_archivo()
            ruta_src = Path(archivo["ruta"])

            if self._modo == "documento":
                texto   = ocr.extraer_texto(ruta_src)
                ruta_txt = ocr.guardar_resultado(texto, ruta_src.name)
            else:
                texto   = stt.transcribir(ruta_src)
                ruta_txt = stt.guardar_resultado(texto, ruta_src.name)

            self.after(0, lambda t=texto, r=ruta_txt: self._on_exito(t, r))

        except Exception as e:
            self.after(0, lambda err=e: self._on_error(err))

    # =====================================
    # Callbacks del procesamiento
    # =====================================

    def _on_exito(self, texto: str, ruta_txt: Path):
        """
        Llamado en el hilo principal cuando el procesamiento termina correctamente.
        Actualiza el estado en la BD, registra el resultado y muestra el texto.
        """
        self._texto_resultado = texto
        self._ruta_txt = ruta_txt

        # Actualizar BD
        self._db.actualizar_estado_proceso(self._proceso_id, "completado")
        self._db.registrar_resultado(self._proceso_id, ruta_txt, "txt")

        if self._modo == "documento":
            self._db.actualizar_estado_documento(self._archivo_id, "procesado")
        else:
            self._db.actualizar_estado_audio(self._archivo_id, "procesado")

        self._logger.log(
            self._cfg["log_accion"],
            f"Procesamiento completado (proceso_id={self._proceso_id})",
            usuario_id=self._usuario["id"],
        )

        # Transición de UI: ocultar carga, mostrar texto y acciones
        self._lbl_cargando.pack_forget()
        self._mostrar_texto(texto)
        self._frame_texto.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        self._frame_botones.pack(anchor=tk.W)

    def _on_error(self, error: Exception):
        """
        Llamado en el hilo principal cuando el procesamiento falla.
        Actualiza el estado en la BD y muestra el mensaje de error.
        """
        self._db.actualizar_estado_proceso(self._proceso_id, "error")
        self._logger.log(
            ERROR,
            f"Error en procesamiento (proceso_id={self._proceso_id}): {error}",
            usuario_id=self._usuario["id"],
        )
        self._lbl_cargando.config(
            text=f"No se pudo procesar el archivo:\n{error}",
            fg=_ERROR,
        )

    # =====================================
    # Acciones sobre el resultado — HU-008
    # =====================================

    def _guardar_txt(self):
        """
        Abre el diálogo de guardado del sistema para que el usuario elija
        la ubicación del archivo .txt (HU-008).
        """
        if not self._texto_resultado:
            return
        nombre_inicial = self._ruta_txt.name if self._ruta_txt else "resultado.txt"
        ruta = filedialog.asksaveasfilename(
            title="Guardar resultado",
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            initialfile=nombre_inicial,
        )
        if ruta:
            Path(ruta).write_text(self._texto_resultado, encoding="utf-8")
            messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta}")

    def _enviar_a_tts(self):
        """Abre la pantalla de TTS con el texto ya cargado (HU-008)."""
        if self._texto_resultado:
            self._on_ir_tts(self._texto_resultado)

    def _generar_resumen(self):
        """
        Genera un resumen extractivo del texto mostrado (HU-010).
        Persiste el resultado en disco y BD siguiendo el mismo patrón que OCR/STT:
          1. Genera el resumen con sumy (LexRank).
          2. Guarda el .txt en storage/outputs/ vía summarizer.guardar_resultado().
          3. Registra el proceso (tipo RESUMEN) y su resultado en la BD.
          4. Registra el evento en la tabla log para el historial (HU-009).
          5. Abre el diálogo modal con opciones de guardado manual y TTS.
        Si la persistencia falla después de crear el proceso, este se marca como
        'error' para no dejar registros a medias en la BD.
        """
        if not self._texto_resultado:
            return

        # =====================================
        # Generación del resumen
        # =====================================
        try:
            texto_resumen = summarizer.resumir(self._texto_resultado)
        except ValueError as e:
            messagebox.showwarning("Texto insuficiente", str(e))
            return

        # =====================================
        # Persistencia en disco y BD
        # =====================================
        archivo = self._obtener_archivo()
        nombre_base = Path(archivo["ruta"]).name
        proceso_id_resumen = None

        try:
            ruta_resumen = summarizer.guardar_resultado(texto_resumen, nombre_base)

            proceso_id_resumen = self._db.registrar_proceso(
                self._usuario["id"],
                "RESUMEN",
                self._archivo_id,
                self._modo,
            )
            self._db.actualizar_estado_proceso(proceso_id_resumen, "completado")
            self._db.registrar_resultado(proceso_id_resumen, ruta_resumen, "txt")

        except Exception as e:
            if proceso_id_resumen is not None:
                self._db.actualizar_estado_proceso(proceso_id_resumen, "error")
            self._logger.log(
                ERROR,
                f"Error al persistir resumen: {e}",
                usuario_id=self._usuario["id"],
            )
            messagebox.showerror(
                "Error",
                f"El resumen se generó pero no pudo guardarse:\n{e}",
            )
            return

        self._logger.log(
            LOG_RESUMEN,
            f"Resumen generado y persistido (proceso_id={proceso_id_resumen})",
            usuario_id=self._usuario["id"],
        )
        _DialogoResumen(self, texto_resumen, self._on_ir_tts)

    # =====================================
    # Helpers internos
    # =====================================

    def _obtener_archivo(self) -> dict:
        """
        Recupera el registro del documento o audio desde la BD por su id.
        Lanza ValueError si no se encuentra.
        """
        if self._modo == "documento":
            archivo = self._db.obtener_documento_por_id(self._archivo_id)
        else:
            archivo = self._db.obtener_audio_por_id(self._archivo_id)

        if archivo is None:
            tipo = "documento" if self._modo == "documento" else "audio"
            raise ValueError(f"No se encontró el {tipo} con id={self._archivo_id}.")
        return archivo

    def _mostrar_texto(self, texto: str):
        """Inserta el texto en el widget de solo lectura manteniendo el color visible."""
        self._txt_resultado.config(state=tk.NORMAL)
        self._txt_resultado.delete("1.0", tk.END)
        self._txt_resultado.insert(tk.END, texto)
        # tk.Text no acepta disabledforeground; el color queda fijado por fg en la creación
        self._txt_resultado.config(state=tk.DISABLED)


# =====================================
# Diálogo de resumen — HU-010
# =====================================

class _DialogoResumen(tk.Toplevel):
    """
    Ventana modal que muestra el resumen generado con opciones de guardado y TTS.
    Se crea desde ContentView._generar_resumen() cuando el texto es suficientemente largo.
    """

    def __init__(self, parent: tk.Frame, texto_resumen: str, on_ir_tts):
        super().__init__(parent, bg=_FONDO)
        self.title("Resumen automático")
        self.resizable(True, True)
        self.geometry("680x440")
        self.grab_set()  # modal: bloquea la ventana padre

        self._texto = texto_resumen
        self._on_ir_tts = on_ir_tts

        self._construir()

    def _construir(self):
        """Arma el contenido del diálogo: título, texto y botonera."""
        tk.Label(
            self,
            text="Resumen generado",
            bg=_FONDO, fg=_ACENTO,
            font=(_FUENTE, 13, "bold"),
        ).pack(anchor=tk.W, padx=24, pady=(20, 8))

        # Área de texto solo lectura
        frame_txt = tk.Frame(self, bg=_CARD)
        frame_txt.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 16))

        txt = tk.Text(
            frame_txt,
            bg=_CARD, fg=_TEXTO,
            font=(_FUENTE, 11),
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=14, pady=12,
            state=tk.NORMAL,
        )
        sb = tk.Scrollbar(frame_txt, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.insert(tk.END, self._texto)
        txt.config(state=tk.DISABLED)

        # Botonera
        frame_btns = tk.Frame(self, bg=_FONDO)
        frame_btns.pack(anchor=tk.W, padx=24, pady=(0, 20))

        for texto_btn, cmd, bg, fg in [
            ("Guardar como .txt",  self._guardar,     _ACENTO, "#ffffff"),
            ("Enviar a TTS",       self._enviar_tts,  _CARD,   _TEXTO),
            ("Cerrar",             self.destroy,       _CARD,   _TEXTO),
        ]:
            tk.Button(
                frame_btns,
                text=texto_btn, command=cmd,
                bg=bg, fg=fg,
                activebackground=_ACENTO_ACT if bg == _ACENTO else "#383850",
                activeforeground="#ffffff" if bg == _ACENTO else _TEXTO,
                font=(_FUENTE, 10, "bold" if bg == _ACENTO else "normal"),
                relief=tk.FLAT, cursor="hand2",
                padx=14, pady=7,
            ).pack(side=tk.LEFT, padx=(0, 10))

    def _guardar(self):
        """Abre el diálogo del sistema para guardar el resumen como .txt."""
        from pathlib import Path
        from tkinter import filedialog
        ruta = filedialog.asksaveasfilename(
            title="Guardar resumen",
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            initialfile="resumen.txt",
        )
        if ruta:
            Path(ruta).write_text(self._texto, encoding="utf-8")
            from tkinter import messagebox
            messagebox.showinfo("Guardado", f"Resumen guardado en:\n{ruta}", parent=self)

    def _enviar_tts(self):
        """Cierra el diálogo y abre la pantalla de TTS con el resumen pre-cargado."""
        self.destroy()
        self._on_ir_tts(self._texto)
