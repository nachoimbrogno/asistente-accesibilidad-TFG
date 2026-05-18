"""
Módulo: main.py
Punto de entrada de la aplicación.
Inicializa la base de datos, el logger y la ventana principal, y gestiona
la navegación entre pantallas a lo largo de toda la sesión.
"""

import tkinter as tk
from tkinter import messagebox

from db.database import Database
from gui.content_view import ContentView
from gui.document_upload import DocumentUpload
from gui.login_screen import LoginScreen
from gui.main_menu import MainMenu
from gui.tts_screen import TTSScreen
from security.logger import Logger, LOGOUT

_FONDO = "#1e1e2e"


class Aplicacion:
    """
    Controlador principal de la aplicación.
    Crea los servicios compartidos (DB, Logger) y orquesta el cambio de pantallas.
    """

    def __init__(self):
        self._root = tk.Tk()
        self._db = Database()
        self._logger = Logger(self._db)
        self._usuario = None
        self._pantalla = None

        self._configurar_ventana()
        self._ir_login()

    def ejecutar(self):
        """Inicia el loop principal de Tkinter."""
        self._root.mainloop()

    # =====================================
    # Configuración de la ventana
    # =====================================

    def _configurar_ventana(self):
        """Establece título, tamaño, posición centrada y evento de cierre."""
        self._root.title("Asistente para Inclusión Digital")
        self._root.configure(bg=_FONDO)

        ancho, alto = 960, 680
        x = (self._root.winfo_screenwidth() - ancho) // 2
        y = (self._root.winfo_screenheight() - alto) // 2
        self._root.geometry(f"{ancho}x{alto}+{x}+{y}")
        self._root.minsize(800, 560)

        self._root.protocol("WM_DELETE_WINDOW", self._cerrar)

    # =====================================
    # Navegación entre pantallas
    # =====================================

    def _cambiar_pantalla(self, nueva: tk.Frame):
        """Destruye la pantalla activa y coloca la nueva."""
        if self._pantalla is not None:
            self._pantalla.destroy()
        self._pantalla = nueva

    def _ir_login(self):
        self._cambiar_pantalla(
            LoginScreen(self._root, self._db, self._logger, self._on_login)
        )

    def _ir_menu(self):
        self._cambiar_pantalla(
            MainMenu(
                self._root,
                self._usuario,
                on_cargar_documento=self._on_cargar_documento,
                on_cargar_audio=self._on_cargar_audio,
                on_tts=self._on_tts,
                on_historial=self._on_historial,
                on_logout=self._on_logout,
            )
        )

    # =====================================
    # Callbacks de pantallas
    # =====================================

    def _on_login(self, usuario: dict):
        """Recibe el usuario autenticado y navega al menú principal."""
        self._usuario = usuario
        self._ir_menu()

    def _on_logout(self):
        """Registra el cierre de sesión y vuelve al login."""
        self._logger.log(
            LOGOUT,
            f"Sesión cerrada: '{self._usuario['username']}'",
            usuario_id=self._usuario["id"],
        )
        self._usuario = None
        self._ir_login()

    def _on_cargar_documento(self):
        """Navega a la pantalla de carga de documentos (HU-002)."""
        self._ir_carga("documento")

    def _on_cargar_audio(self):
        """Navega a la pantalla de carga de audio (HU-002 / HU-005)."""
        self._ir_carga("audio")

    def _ir_carga(self, modo: str):
        """Instancia DocumentUpload en el modo indicado y lo muestra."""
        self._cambiar_pantalla(
            DocumentUpload(
                self._root,
                self._usuario,
                self._db,
                self._logger,
                modo=modo,
                on_volver=self._ir_menu,
                on_cargado=self._on_cargado,
            )
        )

    def _on_cargado(self, archivo_id: int, modo: str):
        """Navega a ContentView para procesar el archivo recién registrado."""
        self._cambiar_pantalla(
            ContentView(
                self._root,
                self._usuario,
                self._db,
                self._logger,
                archivo_id=archivo_id,
                modo=modo,
                on_volver=self._ir_menu,
                on_ir_tts=self._on_ir_tts,
            )
        )

    def _on_ir_tts(self, texto: str):
        """Navega a la pantalla de TTS con el texto pre-cargado (HU-004)."""
        self._cambiar_pantalla(
            TTSScreen(
                self._root,
                self._usuario,
                self._db,
                self._logger,
                texto_inicial=texto,
                on_volver=self._ir_menu,
            )
        )

    def _on_tts(self):
        """Navega a la pantalla de texto a voz (HU-004)."""
        self._on_ir_tts("")

    def _on_historial(self):
        """Navega a la pantalla de historial (HU-009)."""
        messagebox.showinfo(
            "Próximamente",
            "El historial de actividad se implementará en el Sprint 3.",
        )

    # =====================================
    # Cierre de la aplicación
    # =====================================

    def _cerrar(self):
        """Cierra la conexión a la BD antes de destruir la ventana."""
        self._db.cerrar()
        self._root.destroy()


# =====================================
# Punto de entrada
# =====================================

if __name__ == "__main__":
    app = Aplicacion()
    app.ejecutar()
