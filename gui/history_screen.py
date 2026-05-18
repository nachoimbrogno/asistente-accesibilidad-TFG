"""
Módulo: history_screen.py
HU-009 — Registro de logs de actividad
Muestra el historial de acciones del usuario actual en una tabla ordenada
por fecha descendente. Los administradores pueden ver todos los logs del sistema.
Permite filtrar por tipo de acción y refrescar la vista.
"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from db.database import Database
from security.logger import Logger

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
_FUENTE     = "Segoe UI"

# Máximo de registros a recuperar de la BD en una sola consulta
_LIMITE = 200

# Opciones del filtro; el primero actúa como "sin filtro"
_OPCIONES_FILTRO = [
    "Todos",
    "LOGIN_OK", "LOGIN_FALLO", "LOGOUT",
    "REGISTRO", "BLOQUEO",
    "CARGA_DOCUMENTO", "CARGA_AUDIO",
    "OCR", "TTS", "STT", "RESUMEN",
    "DESCARGA", "ERROR",
]


class HistoryScreen(tk.Frame):
    """
    Pantalla de historial de actividad (HU-009).
    Los usuarios ven sus propios logs; los administradores ven todos los del sistema.

    Parámetros:
        master:    ventana o frame padre.
        usuario:   dict con datos del usuario autenticado.
        db:        instancia activa de Database.
        logger:    instancia activa de Logger.
        on_volver: callback para regresar al menú principal.
    """

    def __init__(
        self,
        master: tk.Misc,
        usuario: dict,
        db: Database,
        logger: Logger,
        on_volver,
    ):
        super().__init__(master, bg=_FONDO)
        self._usuario   = usuario
        self._db        = db
        self._logger    = logger
        self._on_volver = on_volver
        self._var_filtro = tk.StringVar(value="Todos")

        self.pack(fill=tk.BOTH, expand=True)
        _aplicar_estilo_treeview()
        self._construir_header()
        self._construir_barra_filtros()
        self._construir_tabla()
        self._construir_footer()
        self._cargar_logs()

    # =====================================
    # Header
    # =====================================

    def _construir_header(self):
        """Barra superior con botón de volver y título adaptado al rol."""
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

        titulo = "Historial del sistema" if self._es_admin() else "Mi historial de actividad"
        tk.Label(
            header,
            text=titulo,
            bg=_HEADER, fg=_TEXTO,
            font=(_FUENTE, 13, "bold"),
        ).pack(side=tk.LEFT, padx=20)

    # =====================================
    # Barra de filtros
    # =====================================

    def _construir_barra_filtros(self):
        """Combobox de tipo de acción y botón de actualización."""
        barra = tk.Frame(self, bg=_CARD, padx=24, pady=10)
        barra.pack(fill=tk.X)

        tk.Label(
            barra,
            text="Filtrar por tipo de acción:",
            bg=_CARD, fg=_TENUE,
            font=(_FUENTE, 10),
        ).pack(side=tk.LEFT, padx=(0, 10))

        combo = ttk.Combobox(
            barra,
            textvariable=self._var_filtro,
            values=_OPCIONES_FILTRO,
            state="readonly",
            width=20,
            font=(_FUENTE, 10),
            style="Dark.TCombobox",
        )
        combo.pack(side=tk.LEFT, padx=(0, 14))
        combo.bind("<<ComboboxSelected>>", lambda _: self._cargar_logs())

        tk.Button(
            barra,
            text="Actualizar",
            command=self._cargar_logs,
            bg=_ACENTO, fg="#ffffff",
            activebackground=_ACENTO_ACT, activeforeground="#ffffff",
            font=(_FUENTE, 10),
            relief=tk.FLAT, cursor="hand2",
            padx=14, pady=4,
        ).pack(side=tk.LEFT)

    # =====================================
    # Tabla de logs
    # =====================================

    def _construir_tabla(self):
        """Treeview con columnas adaptadas al rol del usuario."""
        frame = tk.Frame(self, bg=_FONDO, padx=24, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        # Columnas base; los admins tienen una columna extra de usuario
        if self._es_admin():
            columnas = ("fecha", "usuario_id", "accion", "descripcion")
        else:
            columnas = ("fecha", "accion", "descripcion")

        self._tree = ttk.Treeview(
            frame,
            columns=columnas,
            show="headings",
            selectmode="browse",
            style="Dark.Treeview",
        )

        self._tree.heading("fecha",       text="Fecha y hora")
        self._tree.heading("accion",      text="Acción")
        self._tree.heading("descripcion", text="Descripción")
        self._tree.column("fecha",        width=175, minwidth=150, stretch=False)
        self._tree.column("accion",       width=155, minwidth=120, stretch=False)
        self._tree.column("descripcion",  width=480, minwidth=200, stretch=True)

        if self._es_admin():
            self._tree.heading("usuario_id", text="Usuario ID")
            self._tree.column("usuario_id",  width=95, minwidth=70, stretch=False)

        sb_v = ttk.Scrollbar(frame, orient=tk.VERTICAL,   command=self._tree.yview)
        sb_h = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)

        sb_v.pack(side=tk.RIGHT,  fill=tk.Y)
        sb_h.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(fill=tk.BOTH, expand=True)

    # =====================================
    # Footer
    # =====================================

    def _construir_footer(self):
        """Etiqueta inferior con el recuento de registros mostrados."""
        self._lbl_conteo = tk.Label(
            self,
            text="",
            bg=_FONDO, fg=_TENUE,
            font=(_FUENTE, 9),
            anchor=tk.W,
            padx=24, pady=6,
        )
        self._lbl_conteo.pack(fill=tk.X, side=tk.BOTTOM)

    # =====================================
    # Carga y filtrado de datos
    # =====================================

    def _cargar_logs(self):
        """
        Recupera los logs de la BD, aplica el filtro activo y rellena la tabla.
        Los admins consultan todos los logs; los usuarios solo los propios.
        """
        uid  = None if self._es_admin() else self._usuario["id"]
        logs = self._db.obtener_logs(usuario_id=uid, limite=_LIMITE)

        filtro = self._var_filtro.get()
        if filtro != "Todos":
            logs = [log for log in logs if log["tipo_accion"] == filtro]

        # Vaciar la tabla antes de repoblarla
        for item in self._tree.get_children():
            self._tree.delete(item)

        for log in logs:
            fecha_fmt   = _formatear_fecha(log["fecha"])
            descripcion = _truncar(log["descripcion"], 120)

            if self._es_admin():
                valores = (
                    fecha_fmt,
                    log["usuario_id"] if log["usuario_id"] is not None else "—",
                    log["tipo_accion"],
                    descripcion,
                )
            else:
                valores = (fecha_fmt, log["tipo_accion"], descripcion)

            self._tree.insert("", tk.END, values=valores)

        total = len(logs)
        sufijo = f" (mostrando los últimos {_LIMITE})" if total >= _LIMITE else ""
        self._lbl_conteo.config(
            text=f"{total} {'registro' if total == 1 else 'registros'}{sufijo}"
        )

    # =====================================
    # Helpers internos
    # =====================================

    def _es_admin(self) -> bool:
        """Devuelve True si el usuario autenticado tiene rol de administrador."""
        return self._usuario.get("rol") == "admin"


# =====================================
# Helpers de módulo
# =====================================

def _aplicar_estilo_treeview():
    """
    Configura el estilo oscuro para el Treeview mediante ttk.Style.
    Se usa un nombre de estilo propio ('Dark.Treeview') para no afectar
    otros posibles Treeviews en la aplicación.
    """
    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Dark.Treeview",
        background      = _CARD,
        foreground      = _TEXTO,
        fieldbackground = _CARD,
        rowheight       = 28,
        font            = (_FUENTE, 10),
        borderwidth     = 0,
    )
    style.configure(
        "Dark.Treeview.Heading",
        background  = _HEADER,
        foreground  = _TEXTO,
        font        = (_FUENTE, 10, "bold"),
        relief      = "flat",
    )
    style.map(
        "Dark.Treeview",
        background = [("selected", _ACENTO)],
        foreground = [("selected", "#ffffff")],
    )


def _formatear_fecha(iso: str) -> str:
    """Convierte un timestamp ISO 8601 a 'DD/MM/YYYY  HH:MM:SS'."""
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y  %H:%M:%S")
    except (ValueError, TypeError):
        return iso


def _truncar(texto: str, max_chars: int) -> str:
    """Acorta el texto a max_chars caracteres añadiendo '…' si es necesario."""
    return texto if len(texto) <= max_chars else texto[: max_chars - 1] + "…"
