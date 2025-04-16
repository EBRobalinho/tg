from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QComboBox, QLineEdit, QFormLayout, QMessageBox,
    QGroupBox, QScrollArea, QFrame, QGridLayout, QMenuBar, QMenu, QStackedLayout
)
from PySide6.QtGui import QFont, QAction
from PySide6.QtCore import Qt
import sys
import importlib
import math

# Carrega materiais dinamicamente
sys.path.append("./src")
import materials
from v_p_viga_sobre_pilar.v_p_viga_sobre_pilar import dim_chapa_pilar
from v_p_chapa_cabeca.v_p_chapa_cabeca import dim_chapa_parafuso as dim_chapa_cabeca
from v_p_chapa_extremidade.v_p_chapa_extremidade import dim_chapa_parafuso as dim_chapa_extremidade
from v_p_cantoneira_flex.v_p_cantoneira_flex import dim_cant_parafuso
from v_p_cantoneira_flex.v_p_cantoneira_flex_solda import dim_cant_solda

from front.chapa_cabeca import ParametrosChapaCabeca
from front.chapa_extremidade import ParametrosChapaExtremidade
from front.viga_sobre_pilar import ParametrosVigaSobrePilar
from front.cantoneira_parafuso import ParametrosCantoneiraParafuso
from front.cantoneira_solda import ParametrosCantoneiraSolda

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seleção de Tipo de Ligação")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        titulo = QLabel("Selecione o tipo de ligação estrutural")
        titulo.setFont(QFont("Arial", 16))
        layout.addWidget(titulo)

        self.ligacoes = {
            "Viga sobre Pilar": ParametrosVigaSobrePilar,
            "Chapa de Cabeça": ParametrosChapaCabeca,
            "Chapa de Extremidade": ParametrosChapaExtremidade,
            "Cantoneira Flexível - Parafuso": ParametrosCantoneiraParafuso,
            "Cantoneira Flexível - Solda": ParametrosCantoneiraSolda,
        }

        scroll_area = QScrollArea()
        container = QWidget()
        grid_layout = QGridLayout()

        row = 0
        col = 0
        for i, nome_ligacao in enumerate(self.ligacoes.keys()):
            botao = QPushButton(nome_ligacao)
            botao.setMinimumSize(150, 60)
            botao.clicked.connect(lambda _, nome=nome_ligacao: self.abrir_parametros(nome))
            grid_layout.addWidget(botao, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1

        container.setLayout(grid_layout)
        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def abrir_parametros(self, nome_ligacao):
        classe_parametros = self.ligacoes[nome_ligacao]
        self.parametros_window = classe_parametros(nome_ligacao)
        self.parametros_window.show()

class ParametrosLigacaoBase(QWidget):
    def __init__(self, titulo):
        super().__init__()
        self.setWindowTitle(f"Parâmetros - {titulo}")
        self.setGeometry(150, 150, 600, 600)

        self.layout_principal = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.layout_principal.addLayout(self.form_layout)
        self.init_menu_avancado()
        self.setLayout(self.layout_principal)

    def init_menu_avancado(self):
        self.menu_bar = QMenuBar()
        menu = self.menu_bar.addMenu("Avançado")
        self.acao_toggle = QAction("Mostrar/Esconder Opções Avançadas", self)
        self.acao_toggle.triggered.connect(self.toggle_opcoes_avancadas)
        menu.addAction(self.acao_toggle)

        self.layout_principal.setMenuBar(self.menu_bar)

        self.opcoes_avancadas = QGroupBox("Opções Avançadas")
        self.avancado_layout = QFormLayout()
        self.opcoes_avancadas.setLayout(self.avancado_layout)
        self.opcoes_avancadas.setVisible(False)

        self.layout_principal.addWidget(self.opcoes_avancadas)

    def toggle_opcoes_avancadas(self):
        self.opcoes_avancadas.setVisible(not self.opcoes_avancadas.isVisible())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

