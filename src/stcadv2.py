from PySide6.QtWidgets import (
    QApplication)
from front.utils_ui import aplicar_tema_claro
from front.debug_utils import log_info, log_exception
from main import MainWindow
import sys

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

