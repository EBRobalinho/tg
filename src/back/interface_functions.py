from PySide6.QtGui import  QPalette, QColor
from PySide6.QtCore import Qt

import webbrowser
import os


def aplicar_tema_claro(app):
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#ffffff"))
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f0f0f0"))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor("#e0e0e0"))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor("#448aff"))
    palette.setColor(QPalette.HighlightedText, Qt.white)

    app.setPalette(palette)


def abrir_documento(destino):
    """
    Abre um documento local (PDF) ou um link da web.
    """
    if destino.startswith("http://") or destino.startswith("https://"):
        webbrowser.open(destino)
    else:
        caminho_absoluto = os.path.abspath(destino)
        if os.path.exists(caminho_absoluto):
            webbrowser.open(caminho_absoluto)
        else:
            print(f"Arquivo não encontrado: {caminho_absoluto}")

