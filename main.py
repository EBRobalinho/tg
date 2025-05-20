from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QComboBox, QLineEdit, QFormLayout, QMessageBox,QDialog,
    QGroupBox, QScrollArea, QFrame, QGridLayout, QMenuBar, QMenu, QStackedLayout, QToolButton, QMainWindow
)
from PySide6.QtGui import QIcon, QPixmap , QFont, QAction, QPalette, QColor
from PySide6.QtCore import Qt, QSize
import sys
import importlib
import math

# Carrega materiais dinamicamente
sys.path.append("./src")

from v_p_viga_sobre_pilar.v_p_viga_sobre_pilar import dim_chapa_pilar
from v_p_chapa_cabeca.v_p_chapa_cabeca import dim_chapa_parafuso as dim_chapa_cabeca
from v_p_chapa_extremidade.v_p_chapa_extremidade import dim_chapa_parafuso as dim_chapa_extremidade
from v_p_cantoneira_flex.v_p_cantoneira_flex import dim_cant_parafuso
from v_p_cantoneira_flex.v_p_cantoneira_flex_solda import dim_cant_solda
from src.interface_functions import *
from front.chapa_cabeca import ParametrosChapaCabeca
from front.chapa_extremidade import ParametrosChapaExtremidade
from front.viga_sobre_pilar import ParametrosVigaSobrePilar
from front.cantoneira_parafuso import ParametrosCantoneiraParafuso
from front.cantoneira_solda import ParametrosCantoneiraSolda
from front.cantoneira_solda_parafuso import ParametrosCantoneiraSoldaParafuso

from front.config import (
    STYLE_BOTAO_MENU,
    STYLE_BOTAO_JANELA,
    STYLE_BOTAO_FECHAR,
    COR_BARRA_SUPERIOR,
    icones
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        #Título do Aplicativo:
        self.setWindowTitle("STCAD – Structural Connections for AutoCAD")
        self.setGeometry(100, 100, 1200, 800)

        widget_central = QWidget()
        layout = QVBoxLayout(widget_central)
        self.setCentralWidget(widget_central)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        #Botão de Menu da tela principal
        layout.insertWidget(0, self.criar_barra_superior())

        layout.insertSpacing(1, 10)

        #Coloca o título do que o usuário deve fazer
        titulo = QLabel("Selecione o tipo de ligação estrutural:")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 16))
        titulo.setStyleSheet("border: none;")
        layout.addWidget(titulo)

        self.tipos_ligacoes()

        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        container = QWidget()
        grid_layout = QGridLayout()
        self.criar_box(grid_layout,icones)

        container.setLayout(grid_layout)
        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def criar_barra_superior(self):
        barra_titulo = QWidget()
        barra_layout = QHBoxLayout(barra_titulo)
        barra_layout.setContentsMargins(0, 0, 0, 0)
        barra_layout.setSpacing(0)
        barra_titulo.setStyleSheet(f"background-color: {COR_BARRA_SUPERIOR};")

        # Menu Arquivo
        btn_arquivo = QToolButton()
        btn_arquivo.setText("Menu")
        btn_arquivo.setStyleSheet(STYLE_BOTAO_MENU)
        btn_arquivo.setFocusPolicy(Qt.StrongFocus)  # necessário em barra customizada


        menu = QMenu()
        #Colocar o Link do Video e o TG
        menu.addAction("Ajuda", self.mostrar_ajuda)
        
        menu.addAction("Sobre", self.mostrar_sobre)  # <-- Adiciona ANTES de setMenu()

        btn_arquivo.clicked.connect(
            lambda: menu.exec(btn_arquivo.mapToGlobal(btn_arquivo.rect().bottomLeft()))
        )

        # Botões de janela
        botao_min = QPushButton("−")
        botao_max = QPushButton("⬜")
        botao_fechar = QPushButton("✕")

        botao_min.setFixedSize(32, 28)
        botao_max.setFixedSize(32, 28)
        botao_fechar.setFixedSize(32, 28)

        botao_min.setStyleSheet(STYLE_BOTAO_JANELA)
        botao_max.setStyleSheet(STYLE_BOTAO_JANELA)
        botao_fechar.setStyleSheet(STYLE_BOTAO_FECHAR)

        botao_min.clicked.connect(self.showMinimized)
        botao_max.clicked.connect(lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        botao_fechar.clicked.connect(self.close)

        # Montagem da barra
        barra_layout.addWidget(btn_arquivo)
        barra_layout.addStretch()
        barra_layout.addWidget(botao_min)
        barra_layout.addWidget(botao_max)
        barra_layout.addWidget(botao_fechar)

        return barra_titulo

    def criar_box(self,grid_layout,icones):
        row = 0
        col = 0
        for i, nome_ligacao in enumerate(self.ligacoes.keys()):
            botao = QToolButton()
            botao.setText(nome_ligacao)
            botao.setMinimumSize(150, 100)
            botao.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  # Texto abaixo do ícone

            if nome_ligacao in icones:
                botao.setIcon(QIcon(icones[nome_ligacao]))
                botao.setIconSize(QSize(300, 300))

            botao.clicked.connect(lambda _, nome=nome_ligacao: self.abrir_parametros(nome))
            grid_layout.addWidget(botao, row, col)

            col += 1
            if col == 3:
                col = 0
                row += 1

    def abrir_parametros(self, nome_ligacao):
        classe_parametros = self.ligacoes[nome_ligacao]
        self.parametros_window = classe_parametros(nome_ligacao)
        self.parametros_window.show()

    def tipos_ligacoes(self):
        self.ligacoes = {
            "Viga sobre Pilar (Rígida)": ParametrosVigaSobrePilar,
            "Chapa de Cabeça (Rígida)": ParametrosChapaCabeca,
            "Chapa de Extremidade (Flexível)": ParametrosChapaExtremidade,
            "Cantoneira - Parafuso (Flexível)": ParametrosCantoneiraParafuso,
            "Cantoneira - Parafuso/Solda (Flexível)": ParametrosCantoneiraSoldaParafuso,
            "Cantoneira - Solda (Flexível)": ParametrosCantoneiraSolda,
        }
    
    def mostrar_sobre(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Sobre – STCAD")

        layout = QVBoxLayout(dialogo)
        layout.setAlignment(Qt.AlignTop)

        titulo = QLabel("STCAD – Structural Connections for AutoCAD")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignCenter)

        subtitulo = QLabel("Aplicativo para dimensionamento e detalhamento de ligações metálicas estruturais entre vigas e pilares.")
        subtitulo.setFont(QFont("Arial", 10))
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setWordWrap(True)

        descricao = QLabel(
            "O STCAD permite o projeto e o desenho tridimensional em .dwg de conexões metálicas com integração ao AutoCAD. "
            "Inclui diferentes tipos de ligações rígidas e flexíveis, automatizando o processo de cálculo de ligações metálicas."
        )
        descricao.setWordWrap(True)
        descricao.setFont(QFont("Arial", 9))
        descricao.setAlignment(Qt.AlignJustify)

        autoria = QLabel(
            "O aplicativo foi desenvolvido como trabalho de graduação do Aspirante a Oficial Engenheiro Robalinho, desenvolvido para o Centro de Estudos e Projetos de Engenharia (CEPE). "
            "A finalidade exclusiva do aplicativo é auxiliar os projetos de estruturas metálicas no âmbito da Força Aérea Brasileira (FAB)."
        )
        autoria.setWordWrap(True)
        autoria.setFont(QFont("Arial", 9))
        autoria.setAlignment(Qt.AlignJustify)

        versao = QLabel("1º Versão: Ano 2025")
        fonte_italica = QFont("Arial", 9)
        fonte_italica.setItalic(True)
        versao.setFont(fonte_italica)
        versao.setAlignment(Qt.AlignRight)

        # Imagens (logos)
        img_fab = QLabel()
        img_cepe = QLabel()
        img_ita = QLabel()

        pix_fab = QPixmap("imagem_logo/fab_logo.png")
        pix_cepe = QPixmap("imagem_logo/cepe_logo.png")
        pix_ita = QPixmap("imagem_logo/ita_logo.png")

        img_fab.setPixmap(pix_fab)
        img_cepe.setPixmap(pix_cepe)
        img_ita.setPixmap(pix_ita)

        # Linha final: logos à esquerda, botão à direita
        texto_esquerda = QLabel("Aluno: Eduardo B. Robalinho D. da Gama \nProf Orientador: Dr. Igor Charlles Siqueira Leite \n")
          # ou qualquer texto
        linha_final = QHBoxLayout()
        linha_final.addWidget(texto_esquerda) 
        linha_final.addStretch()
        linha_final.addWidget(img_ita)
        linha_final.addWidget(img_cepe)
        linha_final.addWidget(img_fab)


        # Adiciona tudo ao layout principal
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addWidget(descricao)
        layout.addWidget(autoria)
        layout.addWidget(versao)
        layout.addLayout(linha_final)

        dialogo.exec()

    def mostrar_ajuda(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Ajuda – STCAD")
        dialogo.setFixedSize(500, 300)

        layout = QVBoxLayout(dialogo)
        layout.setAlignment(Qt.AlignTop)

        titulo = QLabel("Ajuda – Documentos de Apoio")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Botão 1 – PDF de instruções gerais (Video do Youtube)
        botao_manual = QPushButton("Video explicativo")
        botao_manual.clicked.connect(lambda: abrir_documento("..."))
        layout.addWidget(botao_manual)

        # Botão 2 – PDF de exemplos de uso
        botao_exemplo = QPushButton("Manual de Ligações da Gerdau S.A")
        botao_exemplo.clicked.connect(lambda: abrir_documento("documents/manual_de_ligacoes.pdf"))
        layout.addWidget(botao_exemplo)

        # Botão 3 – PDF da tabela de cantoneiras
        botao_normas = QPushButton("Tabela de cantoneiras da Gerdau S.A")
        botao_normas.clicked.connect(lambda: abrir_documento("documents/tabela_cantoneira_gerdau.pdf"))
        layout.addWidget(botao_normas)

        # Botão 4 – PDF da tabela dos perfis
        botao_perfis = QPushButton("Tabela de perfis da Gerdau S.A")   
        botao_perfis.clicked.connect(lambda: abrir_documento("documents/tabela_perfis_gerdau.pdf"))
        layout.addWidget(botao_perfis)

        dialogo.exec()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._posicao_click = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._posicao_click)
            event.accept()

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
    aplicar_tema_claro(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



