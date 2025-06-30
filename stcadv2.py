import sys
import os

# Adiciona a pasta src ao caminho do Python para permitir imports relativos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import (
    QApplication)
from front.utils_ui import aplicar_tema_claro
from front.debug_utils import log_info, log_exception
from main import MainWindow

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        aplicar_tema_claro(app)
        log_info("Aplicação STCAD iniciada")
        window = MainWindow()
        window.show()
            
        sys.exit(app.exec())
    except Exception as e:
        log_exception(e)
        # Aqui você pode exibir uma mensagem de erro ou simplesmente deixar o aplicativo falhar
        raise

