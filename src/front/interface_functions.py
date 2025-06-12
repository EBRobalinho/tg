from PySide6.QtGui import  QPalette, QColor
import webbrowser
import os


def aplicar_tema_claro(app):
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("black"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f0f0f0"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("black"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("black"))
    palette.setColor(QPalette.ColorRole.Text, QColor("black"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("black"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("red"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#448aff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))

    app.setPalette(palette)


def abrir_documento(destino: str):
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

