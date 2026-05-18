"""
Módulo: main_menu.py
HU-001 — Pantalla principal post-login
Muestra las opciones de la aplicación como tarjetas navegables por teclado.
El usuario puede acceder a cada función con el ratón o con atajos Alt+número.
"""

import tkinter as tk

_FONDO      = "#1e1e2e"
_HEADER     = "#16213e"
_CARD       = "#2d2d3d"
_CARD_HOVER = "#383850"
_TEXTO      = "#e0e0e0"
_TENUE      = "#a0a0b0"
_ACENTO     = "#5b8dee"
_ACENTO_ACT = "#4a7ce0"
_FUENTE     = "Segoe UI"

# Definición de cada tarjeta del menú:
# (título, descripción, formatos aceptados, atajo, clave del callback)
_TARJETAS = [
    (
        "Cargar documento",
        "Sube un PDF o imagen y extraé\nel texto mediante OCR.",
        "PDF · JPG · PNG",
        "Alt+1",
        "on_cargar_documento",
    ),
    (
        "Cargar audio",
        "Sube un archivo de audio y\nobtené su transcripción en texto.",
        "WAV · MP3",
        "Alt+2",
        "on_cargar_audio",
    ),
    (
        "Texto a voz",
        "Convertí cualquier texto en\nun archivo de audio reproducible.",
        "Entrada libre · Salida MP3",
        "Alt+3",
        "on_tts",
    ),
    (
        "Historial",
        "Revisá el registro de todas\ntus operaciones anteriores.",
        "Logs · Resultados",
        "Alt+4",
        "on_historial",
    ),
]


class MainMenu(tk.Frame):
    """
    Menú principal con cuatro tarjetas de acceso a las funciones de la app.
    Cada tarjeta es clickeable y tiene un atajo de teclado Alt+N.

    Parámetros:
        master:             ventana o frame padre.
        usuario:            dict con los datos del usuario autenticado.
        on_cargar_documento: callback para la pantalla de carga de documentos.
        on_cargar_audio:    callback para la pantalla de carga de audio.
        on_tts:             callback para la pantalla de texto a voz.
        on_historial:       callback para la pantalla de historial.
        on_logout:          callback para cerrar sesión.
    """

    def __init__(
        self,
        master: tk.Misc,
        usuario: dict,
        on_cargar_documento,
        on_cargar_audio,
        on_tts,
        on_historial,
        on_logout,
    ):
        super().__init__(master, bg=_FONDO)
        self._usuario = usuario
        self._callbacks = {
            "on_cargar_documento": on_cargar_documento,
            "on_cargar_audio":     on_cargar_audio,
            "on_tts":              on_tts,
            "on_historial":        on_historial,
        }
        self._on_logout = on_logout

        self.pack(fill=tk.BOTH, expand=True)
        self._construir_header()
        self._construir_grid()
        self._registrar_atajos()

    # =====================================
    # Header
    # =====================================

    def _construir_header(self):
        """Barra superior con el nombre de la app, saludo al usuario y botón de logout."""
        header = tk.Frame(self, bg=_HEADER, pady=14, padx=24)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Asistente para Inclusión Digital",
            bg=_HEADER, fg=_ACENTO,
            font=(_FUENTE, 13, "bold"),
        ).pack(side=tk.LEFT)

        # Bloque derecho: nombre del usuario + logout
        bloque_der = tk.Frame(header, bg=_HEADER)
        bloque_der.pack(side=tk.RIGHT)

        nombre_completo = f"{self._usuario['nombre']} {self._usuario['apellido']}"
        tk.Label(
            bloque_der,
            text=nombre_completo,
            bg=_HEADER, fg=_TEXTO,
            font=(_FUENTE, 10),
        ).pack(side=tk.LEFT, padx=(0, 16))

        tk.Button(
            bloque_der,
            text="Cerrar sesión",
            command=self._on_logout,
            bg=_CARD, fg=_TEXTO,
            activebackground=_CARD_HOVER, activeforeground=_TEXTO,
            font=(_FUENTE, 9),
            relief=tk.FLAT, cursor="hand2",
            padx=12, pady=4,
        ).pack(side=tk.LEFT)

    # =====================================
    # Grid de tarjetas
    # =====================================

    def _construir_grid(self):
        """Crea el área central con las cuatro tarjetas en disposición 2×2."""
        area = tk.Frame(self, bg=_FONDO, padx=40, pady=40)
        area.pack(fill=tk.BOTH, expand=True)

        # Dos columnas de igual peso para que las tarjetas se distribuyan simétricamente
        area.columnconfigure(0, weight=1)
        area.columnconfigure(1, weight=1)
        area.rowconfigure(0, weight=1)
        area.rowconfigure(1, weight=1)

        for indice, (titulo, descripcion, formatos, atajo, clave) in enumerate(_TARJETAS):
            fila    = indice // 2
            columna = indice % 2
            callback = self._callbacks[clave]
            tarjeta = _Tarjeta(area, titulo, descripcion, formatos, atajo, callback)
            tarjeta.grid(row=fila, column=columna, padx=14, pady=14, sticky="nsew")

    # =====================================
    # Atajos de teclado
    # =====================================

    def _registrar_atajos(self):
        """Asocia Alt+1…4 a cada tarjeta y Alt+S al logout."""
        atajos = [
            ("<Alt-1>", self._callbacks["on_cargar_documento"]),
            ("<Alt-2>", self._callbacks["on_cargar_audio"]),
            ("<Alt-3>", self._callbacks["on_tts"]),
            ("<Alt-4>", self._callbacks["on_historial"]),
            ("<Alt-s>", self._on_logout),
            ("<Alt-S>", self._on_logout),
        ]
        for secuencia, accion in atajos:
            self.bind_all(secuencia, lambda _e, a=accion: a())


class _Tarjeta(tk.Frame):
    """
    Tarjeta individual del menú: área clickeable con título, descripción,
    indicador de formatos y atajo de teclado.
    """

    def __init__(
        self,
        parent: tk.Frame,
        titulo: str,
        descripcion: str,
        formatos: str,
        atajo: str,
        comando,
    ):
        super().__init__(parent, bg=_CARD, cursor="hand2")
        self._comando = comando
        self._construir(titulo, descripcion, formatos, atajo)
        self._registrar_eventos()

    def _construir(self, titulo: str, descripcion: str, formatos: str, atajo: str):
        """Coloca los labels dentro de la tarjeta."""
        interior = tk.Frame(self, bg=_CARD, padx=24, pady=22)
        interior.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            interior,
            text=titulo,
            bg=_CARD, fg=_TEXTO,
            font=(_FUENTE, 13, "bold"),
            anchor=tk.W,
        ).pack(fill=tk.X)

        tk.Label(
            interior,
            text=descripcion,
            bg=_CARD, fg=_TENUE,
            font=(_FUENTE, 10),
            anchor=tk.W,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(8, 0))

        pie = tk.Frame(interior, bg=_CARD)
        pie.pack(fill=tk.X, pady=(16, 0))

        tk.Label(
            pie,
            text=formatos,
            bg=_CARD, fg=_ACENTO,
            font=(_FUENTE, 9),
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        tk.Label(
            pie,
            text=atajo,
            bg=_CARD, fg=_TENUE,
            font=(_FUENTE, 8),
            anchor=tk.E,
        ).pack(side=tk.RIGHT)

    def _registrar_eventos(self):
        """Hace que el click y el hover funcionen sobre todo el frame, no solo el botón."""
        for widget in [self] + list(self.winfo_children()) + [
            w for child in self.winfo_children() for w in child.winfo_children()
        ]:
            widget.bind("<Button-1>", lambda _e: self._comando())
            widget.bind("<Enter>",    lambda _e: self._on_enter())
            widget.bind("<Leave>",    lambda _e: self._on_leave())

    def _on_enter(self):
        """Resalta la tarjeta al pasar el cursor."""
        self._set_color(_CARD_HOVER)

    def _on_leave(self):
        """Restaura el color base al salir el cursor."""
        self._set_color(_CARD)

    def _set_color(self, color: str):
        """Aplica el color de fondo a todos los widgets internos de la tarjeta."""
        for widget in [self] + list(self.winfo_children()) + [
            w for child in self.winfo_children() for w in child.winfo_children()
        ]:
            try:
                widget.configure(bg=color)
            except tk.TclError:
                pass
