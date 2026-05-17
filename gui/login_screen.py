"""
Módulo: login_screen.py
HU-001 — Registro de usuario / autenticación
Pantalla inicial de la aplicación. Alterna entre el formulario de login
y el de registro dentro del mismo frame. Llama a on_login_exitoso(usuario)
cuando la autenticación es exitosa.
"""

import tkinter as tk
from datetime import datetime

from db.database import Database
from security.auth import autenticar, registrar_usuario
from security.logger import Logger

# =====================================
# Paleta de alto contraste
# =====================================

_FONDO       = "#1e1e2e"
_CARD        = "#2d2d3d"
_TEXTO       = "#e0e0e0"
_ACENTO      = "#5b8dee"
_ACENTO_ACT  = "#4a7ce0"
_ERROR       = "#f05050"
_EXITO       = "#50c878"
_ENTRADA     = "#3a3a4d"
_FUENTE      = "Segoe UI"


class LoginScreen(tk.Frame):
    """
    Pantalla de login y registro. Recibe db y logger como dependencias para
    mantenerse desacoplada de la inicialización de la aplicación.

    Parámetros:
        master:            ventana o frame padre de Tkinter.
        db:                instancia activa de Database.
        logger:            instancia activa de Logger.
        on_login_exitoso:  callable(usuario: dict) invocado al autenticarse correctamente.
    """

    def __init__(
        self,
        master: tk.Misc,
        db: Database,
        logger: Logger,
        on_login_exitoso,
    ):
        super().__init__(master, bg=_FONDO)
        self._db = db
        self._logger = logger
        self._on_login_exitoso = on_login_exitoso

        self._construir_layout()

        # Enter despacha al formulario activo
        self.bind_all("<Return>", self._manejar_enter)

        self._mostrar_login()

    # =====================================
    # Layout base
    # =====================================

    def _construir_layout(self):
        """Crea el contenedor central, el título y la etiqueta de feedback compartida."""
        self.pack(fill=tk.BOTH, expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        card = tk.Frame(self, bg=_CARD, padx=44, pady=44)
        card.grid(row=0, column=0)

        tk.Label(
            card,
            text="Asistente para\nInclusión Digital",
            bg=_CARD, fg=_ACENTO,
            font=(_FUENTE, 18, "bold"),
            justify=tk.CENTER,
        ).pack(pady=(0, 28))

        # Contenedor que alterna entre los dos paneles
        self._area = tk.Frame(card, bg=_CARD)
        self._area.pack(fill=tk.BOTH)

        self._panel_login    = self._construir_panel_login(self._area)
        self._panel_registro = self._construir_panel_registro(self._area)

        # Feedback de error / éxito: debajo del panel activo
        self._lbl_feedback = tk.Label(
            card,
            text="",
            bg=_CARD, fg=_ERROR,
            font=(_FUENTE, 10),
            wraplength=340,
            justify=tk.CENTER,
        )
        self._lbl_feedback.pack(pady=(10, 0))

    # =====================================
    # Panel de login
    # =====================================

    def _construir_panel_login(self, parent: tk.Frame) -> tk.Frame:
        """Construye el formulario de inicio de sesión y lo devuelve sin mostrarlo."""
        frame = tk.Frame(parent, bg=_CARD)

        tk.Label(
            frame, text="Iniciar sesión",
            bg=_CARD, fg=_TEXTO,
            font=(_FUENTE, 13, "bold"),
        ).pack(anchor=tk.W, pady=(0, 14))

        self._var_login_user = tk.StringVar()
        self._var_login_pass = tk.StringVar()

        _campo(frame, "Usuario:",     self._var_login_user)
        _campo(frame, "Contraseña:",  self._var_login_pass, ocultar=True)

        _boton_principal(frame, "Iniciar sesión", self._intentar_login).pack(
            fill=tk.X, pady=(18, 6)
        )

        tk.Button(
            frame,
            text="¿No tenés cuenta? Registrate aquí",
            bg=_CARD, fg=_ACENTO,
            font=(_FUENTE, 9, "underline"),
            relief=tk.FLAT, bd=0, cursor="hand2",
            activebackground=_CARD, activeforeground=_ACENTO_ACT,
            command=self._mostrar_registro,
        ).pack()

        return frame

    # =====================================
    # Panel de registro
    # =====================================

    def _construir_panel_registro(self, parent: tk.Frame) -> tk.Frame:
        """Construye el formulario de registro y lo devuelve sin mostrarlo."""
        frame = tk.Frame(parent, bg=_CARD)

        tk.Label(
            frame, text="Crear cuenta",
            bg=_CARD, fg=_TEXTO,
            font=(_FUENTE, 13, "bold"),
        ).pack(anchor=tk.W, pady=(0, 14))

        self._var_reg_nombre   = tk.StringVar()
        self._var_reg_apellido = tk.StringVar()
        self._var_reg_user     = tk.StringVar()
        self._var_reg_pass     = tk.StringVar()
        self._var_reg_pass2    = tk.StringVar()

        _campo(frame, "Nombre:",               self._var_reg_nombre)
        _campo(frame, "Apellido:",             self._var_reg_apellido)
        _campo(frame, "Nombre de usuario:",    self._var_reg_user)
        _campo(frame, "Contraseña:",           self._var_reg_pass,  ocultar=True)
        _campo(frame, "Confirmar contraseña:", self._var_reg_pass2, ocultar=True)

        _boton_principal(frame, "Registrarse", self._intentar_registro).pack(
            fill=tk.X, pady=(18, 6)
        )

        tk.Button(
            frame,
            text="¿Ya tenés cuenta? Iniciá sesión",
            bg=_CARD, fg=_ACENTO,
            font=(_FUENTE, 9, "underline"),
            relief=tk.FLAT, bd=0, cursor="hand2",
            activebackground=_CARD, activeforeground=_ACENTO_ACT,
            command=self._mostrar_login,
        ).pack()

        return frame

    # =====================================
    # Alternancia de paneles
    # =====================================

    def _mostrar_login(self):
        """Muestra el panel de login y oculta el de registro."""
        self._panel_registro.pack_forget()
        self._panel_login.pack(fill=tk.BOTH)
        self._limpiar_feedback()

    def _mostrar_registro(self):
        """Muestra el panel de registro y oculta el de login."""
        self._panel_login.pack_forget()
        self._panel_registro.pack(fill=tk.BOTH)
        self._limpiar_feedback()

    def _manejar_enter(self, _event=None):
        """Despacha la tecla Enter al formulario que esté visible en ese momento."""
        if self._panel_login.winfo_ismapped():
            self._intentar_login()
        elif self._panel_registro.winfo_ismapped():
            self._intentar_registro()

    # =====================================
    # Lógica de login
    # =====================================

    def _intentar_login(self):
        """Lee los campos, llama a autenticar() y muestra el feedback correspondiente."""
        username = self._var_login_user.get().strip()
        password = self._var_login_pass.get()

        if not username or not password:
            self._error("Completá usuario y contraseña.")
            return

        resultado = autenticar(self._db, self._logger, username, password)

        if resultado["exito"]:
            self._limpiar_feedback()
            self._on_login_exitoso(resultado["usuario"])
        elif resultado["motivo"] == "cuenta_bloqueada":
            hasta = _formatear_fecha(resultado.get("bloqueado_hasta", ""))
            self._error(f"Cuenta bloqueada. Podés intentar de nuevo {hasta}.")
        else:
            self._error("Usuario o contraseña incorrectos.")

    # =====================================
    # Lógica de registro
    # =====================================

    def _intentar_registro(self):
        """Valida los campos, llama a registrar_usuario() y muestra el feedback."""
        nombre    = self._var_reg_nombre.get().strip()
        apellido  = self._var_reg_apellido.get().strip()
        username  = self._var_reg_user.get().strip()
        password  = self._var_reg_pass.get()
        password2 = self._var_reg_pass2.get()

        # Validaciones en cascada — se muestra el primer error encontrado
        if not all([nombre, apellido, username, password, password2]):
            self._error("Completá todos los campos.")
            return

        if " " in username:
            self._error("El nombre de usuario no puede contener espacios.")
            return

        if len(password) < 8:
            self._error("La contraseña debe tener al menos 8 caracteres.")
            return

        if password != password2:
            self._error("Las contraseñas no coinciden.")
            return

        resultado = registrar_usuario(
            self._db, self._logger, nombre, apellido, username, password
        )

        if resultado["exito"]:
            self._exito("Cuenta creada correctamente. Ya podés iniciar sesión.")
            self._limpiar_campos_registro()
            # Redirige al login automáticamente después de 1,8 segundos
            self.after(1800, self._mostrar_login)
        elif resultado["motivo"] == "username_en_uso":
            self._error(f"El usuario '{username}' ya está registrado.")
        else:
            self._error("No se pudo crear la cuenta. Intentá de nuevo.")

    # =====================================
    # Feedback visual
    # =====================================

    def _error(self, mensaje: str):
        """Muestra un mensaje de error en la etiqueta de feedback."""
        self._lbl_feedback.config(text=mensaje, fg=_ERROR)

    def _exito(self, mensaje: str):
        """Muestra un mensaje de éxito en la etiqueta de feedback."""
        self._lbl_feedback.config(text=mensaje, fg=_EXITO)

    def _limpiar_feedback(self):
        self._lbl_feedback.config(text="")

    def _limpiar_campos_registro(self):
        """Vacía todos los campos del formulario de registro."""
        for var in (
            self._var_reg_nombre, self._var_reg_apellido,
            self._var_reg_user, self._var_reg_pass, self._var_reg_pass2,
        ):
            var.set("")


# =====================================
# Helpers de construcción de widgets
# =====================================

def _campo(
    parent: tk.Frame,
    etiqueta: str,
    variable: tk.StringVar,
    ocultar: bool = False,
) -> tk.Entry:
    """
    Agrega etiqueta + campo de texto al frame padre y devuelve el Entry.
    ocultar=True enmascara los caracteres (uso para contraseñas).
    La etiqueta se coloca siempre antes que el campo para compatibilidad con lectores de pantalla.
    """
    tk.Label(
        parent,
        text=etiqueta,
        bg=_CARD, fg=_TEXTO,
        font=(_FUENTE, 10),
        anchor=tk.W,
    ).pack(fill=tk.X, pady=(8, 2))

    entry = tk.Entry(
        parent,
        textvariable=variable,
        show="●" if ocultar else "",
        bg=_ENTRADA, fg=_TEXTO,
        insertbackground=_TEXTO,
        font=(_FUENTE, 11),
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=_ACENTO,
        highlightcolor=_ACENTO,
        width=30,
    )
    entry.pack(fill=tk.X, ipady=6)
    return entry


def _boton_principal(parent: tk.Frame, texto: str, comando) -> tk.Button:
    """Crea y devuelve un botón de acción principal con estilo de alto contraste."""
    return tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=_ACENTO, fg="#ffffff",
        activebackground=_ACENTO_ACT, activeforeground="#ffffff",
        font=(_FUENTE, 11, "bold"),
        relief=tk.FLAT,
        cursor="hand2",
        pady=10,
    )


def _formatear_fecha(iso: str) -> str:
    """Convierte un timestamp ISO 8601 a texto legible: 'el DD/MM/YYYY a las HH:MM'."""
    try:
        dt = datetime.fromisoformat(iso)
        return f"el {dt.strftime('%d/%m/%Y a las %H:%M')}"
    except (ValueError, TypeError):
        return "más tarde"
