"""
Módulo: document_upload.py
HU-002 — Carga de documentos o archivos de audio
HU-006 — Validación de formato y tamaño
Permite seleccionar un archivo, validarlo y copiarlo al directorio de storage
registrando los metadatos en la base de datos. Funciona en modo 'documento' o 'audio'.
"""

import shutil
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from db.database import Database
from security.logger import CARGA_AUDIO, CARGA_DOCUMENTO, ERROR, Logger

# =====================================
# Rutas de storage
# =====================================

_DIR_RAIZ       = Path(__file__).parent.parent
_DIR_DOCUMENTOS = _DIR_RAIZ / "storage" / "documents"
_DIR_AUDIOS     = _DIR_RAIZ / "storage" / "audios"

# =====================================
# Configuración por modo
# =====================================

_CONFIG = {
    "documento": {
        "titulo":      "Cargar documento",
        "extensiones": {".pdf", ".jpg", ".jpeg", ".png"},
        "tipos_str":   "PDF, JPG, PNG",
        "tamanio_max": 50 * 1024 * 1024,   # 50 MB
        "tamanio_str": "50 MB",
        "dir_storage": _DIR_DOCUMENTOS,
        "log_accion":  CARGA_DOCUMENTO,
        "filetypes":   [("Documentos compatibles", "*.pdf *.jpg *.jpeg *.png")],
    },
    "audio": {
        "titulo":      "Cargar audio",
        "extensiones": {".wav", ".mp3"},
        "tipos_str":   "WAV, MP3",
        "tamanio_max": 100 * 1024 * 1024,  # 100 MB
        "tamanio_str": "100 MB",
        "dir_storage": _DIR_AUDIOS,
        "log_accion":  CARGA_AUDIO,
        "filetypes":   [("Audio compatible", "*.wav *.mp3")],
    },
}

# Normalización de extensión → tipo guardado en BD
_EXT_A_TIPO = {
    ".pdf": "PDF", ".jpg": "JPG", ".jpeg": "JPG",
    ".png": "PNG", ".wav": "WAV", ".mp3":  "MP3",
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


class DocumentUpload(tk.Frame):
    """
    Pantalla de carga de archivos. Opera en modo 'documento' (PDF/imagen) o 'audio' (WAV/MP3).
    Valida el formato y el tamaño antes de permitir la carga (HU-006).
    Al registrar el archivo en la BD invoca on_cargado con su id (HU-002).

    Parámetros:
        master:      ventana o frame padre.
        usuario:     dict con datos del usuario autenticado.
        db:          instancia activa de Database.
        logger:      instancia activa de Logger.
        modo:        'documento' | 'audio'
        on_volver:   callback para regresar al menú principal.
        on_cargado:  callable(archivo_id: int, modo: str) invocado tras la carga exitosa.
    """

    def __init__(
        self,
        master: tk.Misc,
        usuario: dict,
        db: Database,
        logger: Logger,
        modo: str,
        on_volver,
        on_cargado,
    ):
        super().__init__(master, bg=_FONDO)
        self._usuario = usuario
        self._db = db
        self._logger = logger
        self._modo = modo
        self._cfg = _CONFIG[modo]
        self._on_volver = on_volver
        self._on_cargado = on_cargado

        self._ruta_seleccionada: Path | None = None
        self._id_registrado: int | None = None

        self.pack(fill=tk.BOTH, expand=True)
        self._construir_header()
        self._construir_cuerpo()

    # =====================================
    # Header
    # =====================================

    def _construir_header(self):
        """Barra superior con botón de volver y título de la pantalla."""
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
    # Cuerpo principal
    # =====================================

    def _construir_cuerpo(self):
        """Área central: info de formatos, selector, panel de archivo y botones."""
        self._cuerpo = tk.Frame(self, bg=_FONDO, padx=60, pady=36)
        self._cuerpo.pack(fill=tk.BOTH, expand=True)
        self._cuerpo.columnconfigure(0, weight=1)

        self._construir_info_formatos()
        self._construir_selector()
        self._construir_panel_archivo()
        self._construir_botonera()

    def _construir_info_formatos(self):
        """Card con los formatos aceptados y el tamaño máximo (HU-006)."""
        card = tk.Frame(self._cuerpo, bg=_CARD, padx=20, pady=16)
        card.pack(fill=tk.X, pady=(0, 24))

        tk.Label(
            card,
            text="Formatos aceptados",
            bg=_CARD, fg=_TENUE,
            font=(_FUENTE, 10),
        ).pack(anchor=tk.W)

        tk.Label(
            card,
            text=self._cfg["tipos_str"],
            bg=_CARD, fg=_TEXTO,
            font=(_FUENTE, 12, "bold"),
        ).pack(anchor=tk.W, pady=(2, 8))

        tk.Label(
            card,
            text=f"Tamaño máximo: {self._cfg['tamanio_str']}",
            bg=_CARD, fg=_TENUE,
            font=(_FUENTE, 10),
        ).pack(anchor=tk.W)

    def _construir_selector(self):
        """Botón que abre el diálogo del sistema para elegir un archivo."""
        tk.Button(
            self._cuerpo,
            text="Seleccionar archivo...",
            command=self._seleccionar_archivo,
            bg=_ACENTO, fg="#ffffff",
            activebackground=_ACENTO_ACT, activeforeground="#ffffff",
            font=(_FUENTE, 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=20, pady=10,
        ).pack(anchor=tk.W, pady=(0, 20))

    def _construir_panel_archivo(self):
        """Panel con los metadatos del archivo seleccionado (oculto hasta que haya selección)."""
        self._panel_archivo = tk.Frame(self._cuerpo, bg=_CARD, padx=20, pady=16)

        self._var_nombre  = tk.StringVar()
        self._var_tipo    = tk.StringVar()
        self._var_tamanio = tk.StringVar()

        for etiqueta, var in [
            ("Archivo:", self._var_nombre),
            ("Tipo:",    self._var_tipo),
            ("Tamaño:",  self._var_tamanio),
        ]:
            fila = tk.Frame(self._panel_archivo, bg=_CARD)
            fila.pack(fill=tk.X, pady=2)
            tk.Label(
                fila, text=etiqueta, bg=_CARD, fg=_TENUE,
                font=(_FUENTE, 10), width=9, anchor=tk.W,
            ).pack(side=tk.LEFT)
            tk.Label(
                fila, textvariable=var, bg=_CARD, fg=_TEXTO,
                font=(_FUENTE, 10), anchor=tk.W,
            ).pack(side=tk.LEFT)

        self._lbl_validacion = tk.Label(
            self._panel_archivo,
            text="",
            bg=_CARD,
            font=(_FUENTE, 10, "bold"),
        )
        self._lbl_validacion.pack(anchor=tk.W, pady=(10, 0))

    def _construir_botonera(self):
        """Botón 'Cargar' (deshabilitado hasta validación OK) y botón 'Continuar' post-carga."""
        self._btn_cargar = tk.Button(
            self._cuerpo,
            text="Cargar archivo",
            command=self._cargar_archivo,
            bg=_ACENTO, fg="#ffffff",
            activebackground=_ACENTO_ACT, activeforeground="#ffffff",
            disabledforeground="#7a7a9a",
            font=(_FUENTE, 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=20, pady=10,
            state=tk.DISABLED,
        )
        self._btn_cargar.pack(anchor=tk.W, pady=(22, 0))

        self._lbl_exito = tk.Label(
            self._cuerpo,
            text="",
            bg=_FONDO, fg=_EXITO,
            font=(_FUENTE, 11),
        )
        self._lbl_exito.pack(anchor=tk.W, pady=(8, 0))

        # Solo se muestra tras la carga exitosa
        self._btn_continuar = tk.Button(
            self._cuerpo,
            text="Continuar al procesamiento →",
            command=self._continuar,
            bg=_EXITO, fg="#1e1e2e",
            activebackground="#3db85e", activeforeground="#1e1e2e",
            font=(_FUENTE, 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=20, pady=10,
        )

    # =====================================
    # Selección y validación — HU-006
    # =====================================

    def _seleccionar_archivo(self):
        """
        Abre el diálogo del sistema operativo, valida el archivo elegido
        y actualiza la interfaz con el resultado de la validación.
        """
        ruta_str = filedialog.askopenfilename(
            title=f"Seleccionar {self._cfg['titulo'].lower()}",
            filetypes=self._cfg["filetypes"] + [("Todos los archivos", "*.*")],
        )
        if not ruta_str:
            return  # El usuario canceló el diálogo

        self._ruta_seleccionada = Path(ruta_str)
        self._id_registrado = None

        tamanio_bytes = self._ruta_seleccionada.stat().st_size

        # Actualizar metadatos visibles
        self._var_nombre.set(self._ruta_seleccionada.name)
        self._var_tipo.set(self._ruta_seleccionada.suffix.upper().lstrip("."))
        self._var_tamanio.set(_formatear_bytes(tamanio_bytes))

        # Resetear estado anterior
        self._panel_archivo.pack(fill=tk.X, pady=(0, 20))
        self._lbl_exito.config(text="")
        self._btn_continuar.pack_forget()

        # Validar y mostrar resultado (HU-006)
        error = self._validar(tamanio_bytes)
        if error:
            self._lbl_validacion.config(text=f"✗  {error}", fg=_ERROR)
            self._btn_cargar.config(state=tk.DISABLED)
        else:
            self._lbl_validacion.config(text="✓  Archivo válido", fg=_EXITO)
            self._btn_cargar.config(state=tk.NORMAL)

    def _validar(self, tamanio_bytes: int) -> str | None:
        """
        Comprueba que la extensión sea admitida y el tamaño no supere el límite.
        Devuelve un mensaje de error descriptivo, o None si el archivo es válido.
        """
        ext = self._ruta_seleccionada.suffix.lower()

        if ext not in self._cfg["extensiones"]:
            return (
                f"Formato no admitido ('{ext}'). "
                f"Usá archivos {self._cfg['tipos_str']}."
            )

        if tamanio_bytes > self._cfg["tamanio_max"]:
            return (
                f"El archivo pesa {_formatear_bytes(tamanio_bytes)}, "
                f"pero el máximo es {self._cfg['tamanio_str']}."
            )

        return None

    # =====================================
    # Carga y registro — HU-002
    # =====================================

    def _cargar_archivo(self):
        """
        Copia el archivo al directorio de storage y registra sus metadatos en la BD.
        Deshabilita el botón al terminar y muestra el botón de continuar.
        """
        if self._ruta_seleccionada is None:
            return

        try:
            ruta_destino = _copiar_a_storage(
                self._ruta_seleccionada,
                self._cfg["dir_storage"],
            )
            tipo = _EXT_A_TIPO[self._ruta_seleccionada.suffix.lower()]

            if self._modo == "documento":
                archivo_id = self._db.registrar_documento(
                    self._usuario["id"], ruta_destino, tipo
                )
            else:
                archivo_id = self._db.registrar_audio(
                    self._usuario["id"], ruta_destino, tipo
                )

            self._logger.log(
                self._cfg["log_accion"],
                f"Cargado: '{self._ruta_seleccionada.name}' ({tipo})",
                usuario_id=self._usuario["id"],
            )

            self._id_registrado = archivo_id
            self._btn_cargar.config(state=tk.DISABLED)
            self._lbl_exito.config(
                text=f"✓  Archivo registrado correctamente."
            )
            self._btn_continuar.pack(anchor=tk.W, pady=(8, 0))

        except Exception as e:
            self._logger.log(
                ERROR,
                f"Error al cargar '{self._ruta_seleccionada.name}': {e}",
                usuario_id=self._usuario["id"],
            )
            self._lbl_validacion.config(
                text=f"✗  No se pudo guardar el archivo: {e}", fg=_ERROR
            )

    def _continuar(self):
        """Invoca on_cargado con el id del archivo registrado para navegar al procesamiento."""
        if self._id_registrado is not None:
            self._on_cargado(self._id_registrado, self._modo)


# =====================================
# Utilidades de módulo
# =====================================

def _copiar_a_storage(origen: Path, destino_dir: Path) -> Path:
    """
    Copia el archivo al directorio de storage con un nombre único basado en timestamp.
    Crea el directorio si no existe. Devuelve la ruta del archivo copiado.
    """
    destino_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    nombre_unico = f"{timestamp}_{origen.name}"
    destino = destino_dir / nombre_unico
    shutil.copy2(str(origen), str(destino))
    return destino


def _formatear_bytes(b: int) -> str:
    """Convierte un valor en bytes a una representación legible (B, KB, MB)."""
    if b < 1024:
        return f"{b} B"
    if b < 1024 ** 2:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1024 ** 2:.1f} MB"
