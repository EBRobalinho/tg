import sys
import os
import time

# Adiciona a pasta src ao caminho do Python para permitir imports relativos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from src.front.utils_ui import aplicar_tema_claro
from src.front.debug_utils import log_info, log_exception
from src.main import MainWindow

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)


        splash_pix = QPixmap("src/assets/imagem_icon/logo_stcad.png")
        aplicar_tema_claro(app)
        splash = QSplashScreen(splash_pix)
        splash.show()
        app.processEvents()

        log_info("Aplicação STCAD iniciada")
        time.sleep(3)  # Simula carregamento

        window = MainWindow()
        window.show()
        splash.finish(window)

        sys.exit(app.exec())
    except Exception as e:
        log_exception(e)
        raise
