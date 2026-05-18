"""
Módulo: tts_screen.py
HU-004 — Conversión de texto a voz (TTS)
HU-008 — Entrega de resultados accesibles
Pantalla que permite escribir o pegar texto, ajustar velocidad y volumen,
reproducirlo por los altavoces o exportarlo como archivo WAV.
Las operaciones bloqueantes (síntesis) corren en un hilo de fondo.
"""

import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from core import tts
from db.database import Database
from security.logger import TTS as LOG_TTS, ERROR, Logger

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

_VELOCIDAD_MIN  = 80
_VELOCIDAD_MAX  = 250
_VELOCIDAD_DEF  = 150


class TTSScreen(tk.Frame):
    """
    Pantalla de conversión de texto a voz.
    Puede recibir un texto inicial pre-cargado (proveniente de OCR o STT)
    o bien dejar el área vacía para que el usuario escriba o pegue texto.

    Parámetros:
        master:         ventana o frame padre.
        usuario:        dict con datos del usuario autenticado.
        db:             instancia activa de Database.
        logger:         instancia activa de Logger.
        texto_inicial:  texto pre-cargado en el área de edición (puede ser "").
        on_volver:      callback para regresar al menú principal.
    """

    def __init__(
        self,
        master: tk.Misc,
        usuario: dict,
        db: Database,
        logger: Logger,
        texto_inicial: str,
        on_volver,
    ):
        super().__init__(master, bg=_FONDO)
        self._usuario       = usuario
        self._db            = db
        self._logger        = logger
        self._on_volver     = on_volver
        self._en_proceso    = False     # impide operaciones concurrentes

        self.pack(fill=tk.BOTH, expand=True)
        self._construir_header()
        self._construir_cuerpo(texto_inicial)

    # =====================================
    # Header
    # =====================================

    def _construir_header(self):
        """Barra superior con botón de volver y título."""
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
            text="Texto a Voz (TTS)",
            bg=_HEADER, fg=_TEXTO,
            font=(_FUENTE, 13, "bold"),
        ).pack(side=tk.LEFT, padx=20)

    # =====================================
    # Cuerpo
    # =====================================

    def _construir_cuerpo(self, texto_inicial: str):
        """Arma el área central: texto editable, controles de voz y botonera."""
        cuerpo = tk.Frame(self, bg=_FONDO, padx=40, pady=28)
        cuerpo.pack(fill=tk.BOTH, expand=True)

        self._construir_area_texto(cuerpo, texto_inicial)
        self._construir_controles(cuerpo)
        self._construir_botonera(cuerpo)

        # Etiqueta de estado (progreso, errores, confirmaciones)
        self._lbl_estado = tk.Label(
            cuerpo,
            text="",
            bg=_FONDO, fg=_TENUE,
            font=(_FUENTE, 10),
        )
        self._lbl_estado.pack(anchor=tk.W, pady=(8, 0))

    def _construir_area_texto(self, parent: tk.Frame, texto_inicial: str):
        """Área de texto editable con scrollbar vertical."""
        tk.Label(
            parent,
            text="Texto a convertir:",
            bg=_FONDO, fg=_TEXTO,
            font=(_FUENTE, 10),
        ).pack(anchor=tk.W, pady=(0, 6))

        frame_txt = tk.Frame(parent, bg=_CARD)
        frame_txt.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self._txt = tk.Text(
            frame_txt,
            bg=_CARD, fg=_TEXTO,
            insertbackground=_TEXTO,
            font=(_FUENTE, 11),
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=14, pady=12,
            undo=True,
        )
        sb = tk.Scrollbar(frame_txt, command=self._txt.yview)
        self._txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if texto_inicial:
            self._txt.insert(tk.END, texto_inicial)

    def _construir_controles(self, parent: tk.Frame):
        """Sliders de velocidad y volumen con etiqueta de valor en tiempo real."""
        frame = tk.Frame(parent, bg=_FONDO)
        frame.pack(fill=tk.X, pady=(0, 20))

        self._var_velocidad = tk.IntVar(value=_VELOCIDAD_DEF)
        self._var_volumen   = tk.IntVar(value=100)

        _slider(
            frame,
            etiqueta="Velocidad:",
            variable=self._var_velocidad,
            desde=_VELOCIDAD_MIN,
            hasta=_VELOCIDAD_MAX,
            unidad="pal/min",
        ).pack(fill=tk.X, pady=(0, 10))

        _slider(
            frame,
            etiqueta="Volumen:  ",
            variable=self._var_volumen,
            desde=0,
            hasta=100,
            unidad="%",
        ).pack(fill=tk.X)

    def _construir_botonera(self, parent: tk.Frame):
        """Botones de acción: Reproducir y Guardar como audio."""
        frame = tk.Frame(parent, bg=_FONDO)
        frame.pack(anchor=tk.W, pady=(0, 8))

        self._btn_reproducir = tk.Button(
            frame,
            text="▶  Reproducir",
            command=self._reproducir,
            bg=_ACENTO, fg="#ffffff",
            activebackground=_ACENTO_ACT, activeforeground="#ffffff",
            font=(_FUENTE, 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=18, pady=9,
        )
        self._btn_reproducir.pack(side=tk.LEFT, padx=(0, 12))

        self._btn_guardar = tk.Button(
            frame,
            text="Guardar como audio",
            command=self._guardar_audio,
            bg=_CARD, fg=_TEXTO,
            activebackground="#383850", activeforeground=_TEXTO,
            font=(_FUENTE, 11),
            relief=tk.FLAT, cursor="hand2",
            padx=18, pady=9,
        )
        self._btn_guardar.pack(side=tk.LEFT)

    # =====================================
    # Acciones
    # =====================================

    def _reproducir(self):
        """
        Reproduce el texto por los altavoces en un hilo de fondo.
        Deshabilita los botones durante la reproducción para evitar llamadas concurrentes.
        """
        texto = self._leer_texto()
        if texto is None:
            return

        self._bloquear_botones("Reproduciendo...")
        hilo = threading.Thread(
            target=self._hilo_reproducir,
            args=(texto,),
            daemon=True,
        )
        hilo.start()

    def _hilo_reproducir(self, texto: str):
        """Ejecuta tts.reproducir() fuera del hilo de Tkinter."""
        try:
            tts.reproducir(
                texto,
                velocidad=self._var_velocidad.get(),
                volumen=self._var_volumen.get() / 100,
            )
            self._logger.log(
                LOG_TTS,
                f"Texto reproducido por altavoces ({len(texto)} caracteres)",
                usuario_id=self._usuario["id"],
            )
            self.after(0, lambda: self._desbloquear_botones(""))
        except Exception as e:
            self._logger.log(ERROR, f"Error en TTS reproducir: {e}", usuario_id=self._usuario["id"])
            self.after(0, lambda err=e: self._desbloquear_botones(f"Error al reproducir: {err}", error=True))

    def _guardar_audio(self):
        """
        Genera el archivo WAV en storage/outputs/ (hilo de fondo) y luego
        abre el diálogo de guardado para que el usuario elija la ubicación final.
        """
        texto = self._leer_texto()
        if texto is None:
            return

        self._bloquear_botones("Generando audio...")
        hilo = threading.Thread(
            target=self._hilo_guardar,
            args=(texto,),
            daemon=True,
        )
        hilo.start()

    def _hilo_guardar(self, texto: str):
        """Ejecuta tts.convertir_a_audio() y delega el guardado final al hilo principal."""
        try:
            ruta_storage = tts.convertir_a_audio(
                texto,
                nombre_base="tts_output",
                velocidad=self._var_velocidad.get(),
                volumen=self._var_volumen.get() / 100,
            )
            self.after(0, lambda r=ruta_storage, t=texto: self._on_audio_generado(r, t))
        except Exception as e:
            self._logger.log(ERROR, f"Error en TTS guardar: {e}", usuario_id=self._usuario["id"])
            self.after(0, lambda err=e: self._desbloquear_botones(f"Error al generar audio: {err}", error=True))

    def _on_audio_generado(self, ruta_storage: Path, texto: str):
        """
        Llamado en el hilo principal tras generar el WAV.
        Muestra el diálogo de guardado, registra el proceso en la BD y loguea.
        """
        ruta_destino = filedialog.asksaveasfilename(
            title="Guardar audio",
            defaultextension=".wav",
            filetypes=[("Archivo de audio WAV", "*.wav")],
            initialfile=ruta_storage.name,
        )

        if ruta_destino:
            shutil.copy2(str(ruta_storage), ruta_destino)

            # Registro en BD: proceso + resultado apuntan al archivo en storage
            proceso_id = self._db.registrar_proceso(
                self._usuario["id"], "TTS", 0, "texto"
            )
            self._db.actualizar_estado_proceso(proceso_id, "completado")
            self._db.registrar_resultado(proceso_id, ruta_storage, "wav")

            self._logger.log(
                LOG_TTS,
                f"Audio generado y guardado ({len(texto)} caracteres → {Path(ruta_destino).name})",
                usuario_id=self._usuario["id"],
            )
            self._desbloquear_botones(f"Audio guardado: {Path(ruta_destino).name}")
        else:
            # El usuario canceló el diálogo: el WAV queda en storage/outputs/ de todas formas
            self._desbloquear_botones("")

    # =====================================
    # Helpers de UI
    # =====================================

    def _leer_texto(self) -> str | None:
        """
        Lee el contenido del área de texto y lo valida.
        Devuelve el texto si es válido, o None si está vacío (y muestra el error).
        No inicia ninguna operación si ya hay una en curso.
        """
        if self._en_proceso:
            return None

        texto = self._txt.get("1.0", tk.END).strip()
        if not texto:
            self._mostrar_estado("Escribí o pegá el texto antes de continuar.", error=True)
            return None
        return texto

    def _bloquear_botones(self, mensaje: str):
        """Deshabilita los botones y muestra un mensaje de progreso."""
        self._en_proceso = True
        self._btn_reproducir.config(state=tk.DISABLED)
        self._btn_guardar.config(state=tk.DISABLED)
        self._mostrar_estado(mensaje)

    def _desbloquear_botones(self, mensaje: str, error: bool = False):
        """Rehabilita los botones y muestra el mensaje final de la operación."""
        self._en_proceso = False
        self._btn_reproducir.config(state=tk.NORMAL)
        self._btn_guardar.config(state=tk.NORMAL)
        self._mostrar_estado(mensaje, error=error)

    def _mostrar_estado(self, mensaje: str, error: bool = False):
        """Actualiza la etiqueta de estado con el color apropiado."""
        color = _ERROR if error else (_EXITO if mensaje else _TENUE)
        self._lbl_estado.config(text=mensaje, fg=color)


# =====================================
# Helper de construcción de widgets
# =====================================

def _slider(
    parent: tk.Frame,
    etiqueta: str,
    variable: tk.IntVar,
    desde: int,
    hasta: int,
    unidad: str,
) -> tk.Frame:
    """
    Crea una fila con etiqueta, slider y label de valor en tiempo real.
    Devuelve el frame contenedor para que el llamador lo empaque.
    """
    fila = tk.Frame(parent, bg=_FONDO)

    tk.Label(
        fila,
        text=etiqueta,
        bg=_FONDO, fg=_TEXTO,
        font=(_FUENTE, 10),
        width=12,
        anchor=tk.W,
    ).pack(side=tk.LEFT)

    lbl_valor = tk.Label(
        fila,
        text=f"{variable.get()} {unidad}",
        bg=_FONDO, fg=_ACENTO,
        font=(_FUENTE, 10, "bold"),
        width=10,
        anchor=tk.W,
    )

    def _actualizar(val):
        lbl_valor.config(text=f"{int(float(val))} {unidad}")

    tk.Scale(
        fila,
        variable=variable,
        from_=desde,
        to=hasta,
        orient=tk.HORIZONTAL,
        command=_actualizar,
        bg=_FONDO,
        fg=_TEXTO,
        troughcolor=_CARD,
        activebackground=_ACENTO,
        highlightthickness=0,
        showvalue=False,
        length=300,
    ).pack(side=tk.LEFT, padx=(8, 8))

    lbl_valor.pack(side=tk.LEFT)

    return fila
