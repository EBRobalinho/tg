from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout,QDialog,
     QScrollArea, QGridLayout, QMenu, QToolButton, QMainWindow, QMessageBox,
     QRadioButton, QGroupBox, QButtonGroup
)
from PySide6.QtGui import QIcon, QPixmap , QFont
from PySide6.QtCore import Qt, QSize
import sys
import os

# Configurar modo de debug (isso pode ser movido para um arquivo de configuração)
os.environ["STCAD_DEBUG"] = "1"  # 1 para ativar, 0 para desativar

# Importar utilitários de debug
from front.debug_utils import log_info, log_exception, show_debug_window

# Carrega materiais dinamicamente
from front.utils_ui import aplicar_tema_claro, abrir_documento
from front.domain.viga_sobre_pilar import Viga_sobre_Pilar
from front.domain.chapa_cabeca import Chapa_Cabeca
from front.domain.chapa_extremidade import Chapa_Extremidade
from front.domain.cantoneira_parafuso import Cantoneira_Parafuso
from front.domain.cantoneira_solda_parafuso import Cantoneira_Solda_Parafuso
from front.domain.cantoneira_solda import Cantoneira_Solda
from back.conversions import CONVERSORES, UNIDADE_ESCOLHIDA

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
        
        log_info("Inicializando aplicação principal STCAD")

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
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        
        log_info("Aplicação principal inicializada com sucesso")

    def criar_barra_superior(self):
        barra_titulo = QWidget()
        barra_layout = QHBoxLayout(barra_titulo)
        barra_layout.setContentsMargins(0, 0, 0, 0)
        barra_layout.setSpacing(0)
        barra_titulo.setStyleSheet(f"background-color: {COR_BARRA_SUPERIOR};")        # Menu Arquivo
        btn_arquivo = QToolButton()
        btn_arquivo.setText("Menu")
        btn_arquivo.setStyleSheet(STYLE_BOTAO_MENU)
        btn_arquivo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # necessário em barra customizada
        
        menu = QMenu()
        # Adicionar opção de debug se o modo de debug estiver ativo
        if os.environ.get("STCAD_DEBUG", "0") == "1":
            menu.addAction("Debug Console", show_debug_window)

        menu.addAction("Unidades", self.escolher_unidades)
            
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
        try:
            row = 0
            col = 0
            for i, nome_ligacao in enumerate(self.ligacoes.keys()):
                botao = QToolButton()
                botao.setText(nome_ligacao)
                botao.setMinimumSize(150, 100)
                botao.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)  # Texto abaixo do ícone

                if nome_ligacao in icones:
                    botao.setIcon(QIcon(icones[nome_ligacao]))
                    botao.setIconSize(QSize(300, 300))

                botao.clicked.connect(lambda _, nome=nome_ligacao: self.abrir_parametros(nome))
                grid_layout.addWidget(botao, row, col)

                col += 1
                if col == 3:
                    col = 0
                    row += 1
        except Exception as e:
            log_exception(e)
            raise

    def abrir_parametros(self, nome_ligacao):
        try:
            log_info(f"Abrindo janela de parâmetros para: {nome_ligacao}")
            classe_parametros = self.ligacoes[nome_ligacao]
            self.parametros_window = classe_parametros(nome_ligacao)
            self.parametros_window.show()
        except Exception as e:
            log_exception(e)
            QMessageBox.critical(self, "Erro", f"Erro ao abrir parâmetros:\n{str(e)}")

    def tipos_ligacoes(self):
        self.ligacoes = {
            "Viga sobre Pilar (Rígida)": Viga_sobre_Pilar,
            "Chapa de Cabeça (Rígida)": Chapa_Cabeca,
            "Chapa de Extremidade (Flexível)": Chapa_Extremidade,
            "Cantoneira - Parafuso (Flexível)": Cantoneira_Parafuso,
            "Cantoneira - Parafuso/Solda (Flexível)": Cantoneira_Solda_Parafuso,
            "Cantoneira - Solda (Flexível)": Cantoneira_Solda,
        }
    
    def mostrar_sobre(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Sobre – STCAD")

        layout = QVBoxLayout(dialogo)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        titulo = QLabel("STCAD – Structural Connections for AutoCAD")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitulo = QLabel("Aplicativo para dimensionamento e detalhamento de ligações metálicas estruturais entre vigas e pilares.")
        subtitulo.setFont(QFont("Arial", 10))
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setWordWrap(True)

        descricao = QLabel(
            "O STCAD permite o projeto e o desenho tridimensional em .dwg de conexões metálicas com integração ao AutoCAD. "
            "Inclui diferentes tipos de ligações rígidas e flexíveis, automatizando o processo de cálculo de ligações metálicas."
        )
        descricao.setWordWrap(True)
        descricao.setFont(QFont("Arial", 9))
        descricao.setAlignment(Qt.AlignmentFlag.AlignJustify)

        autoria = QLabel(
            "O aplicativo foi desenvolvido como trabalho de graduação do Aspirante a Oficial Engenheiro Robalinho, desenvolvido para o Centro de Estudos e Projetos de Engenharia (CEPE). "
            "A finalidade exclusiva do aplicativo é auxiliar os projetos de estruturas metálicas no âmbito da Força Aérea Brasileira (FAB)."
        )
        autoria.setWordWrap(True)
        autoria.setFont(QFont("Arial", 9))
        autoria.setAlignment(Qt.AlignmentFlag.AlignJustify)

        versao = QLabel("1º Versão: Ano 2025")
        fonte_italica = QFont("Arial", 9)
        fonte_italica.setItalic(True)
        versao.setFont(fonte_italica)
        versao.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Imagens (logos)
        img_fab = QLabel()
        img_cepe = QLabel()
        img_ita = QLabel()

        pix_fab = QPixmap("../assets/imagem_logo/fab_logo.png")
        pix_cepe = QPixmap("../assets/imagem_logo/cepe_logo.png")
        pix_ita = QPixmap("../assets/imagem_logo/ita_logo.png")

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
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        titulo = QLabel("Ajuda – Documentos de Apoio")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Botão 1 – PDF de instruções gerais (Video do Youtube)
        botao_manual = QPushButton("Video explicativo")
        botao_manual.clicked.connect(lambda: abrir_documento("..."))
        layout.addWidget(botao_manual)

        # Botão 2 – PDF de exemplos de uso
        botao_exemplo = QPushButton("Manual de Ligações da Gerdau S.A")
        botao_exemplo.clicked.connect(lambda: abrir_documento("../assets/documents/manual_de_ligacoes.pdf"))
        layout.addWidget(botao_exemplo)

        # Botão 3 – PDF da tabela de cantoneiras
        botao_normas = QPushButton("Tabela de cantoneiras da Gerdau S.A")
        botao_normas.clicked.connect(lambda: abrir_documento("../assets/documents/tabela_cantoneira_gerdau.pdf"))
        layout.addWidget(botao_normas)

        # Botão 4 – PDF da tabela dos perfis
        botao_perfis = QPushButton("Tabela de perfis da Gerdau S.A")   
        botao_perfis.clicked.connect(lambda: abrir_documento("../assets/documents/tabela_perfis_gerdau.pdf"))
        layout.addWidget(botao_perfis)

        dialogo.exec()

    def escolher_unidades(self):
        
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Escolha de Unidades")
        dialogo.setFixedSize(400, 250)
        
        layout = QVBoxLayout(dialogo)
        
        titulo = QLabel("Selecione as unidades para entrada de dados:")
        titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Grupo de botões de rádio para as unidades
        grupo_box = QGroupBox("Unidades disponíveis")
        grupo_layout = QVBoxLayout()
        
        # Grupo de botões para garantir que apenas um possa ser selecionado
        button_group = QButtonGroup(dialogo)
        
        # Criar botões para cada unidade disponível
        self.radio_buttons = {}
        
        for idx, unidade in enumerate(CONVERSORES.keys()):
            rotulos = CONVERSORES[unidade]["rótulos"]
            texto = f"{unidade} - Força: {rotulos[0]}, Momento: {rotulos[1]}"
            radio = QRadioButton(texto)
            if unidade == UNIDADE_ESCOLHIDA:
                radio.setChecked(True)
            
            self.radio_buttons[unidade] = radio
            button_group.addButton(radio)
            grupo_layout.addWidget(radio)
        
        grupo_box.setLayout(grupo_layout)
        layout.addWidget(grupo_box)
        
        # Informação adicional
        info = QLabel("A escolha da unidade afeta como os valores são interpretados\n"
                     "e convertidos internamente para os cálculos.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialogo.reject)
        
        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.clicked.connect(lambda: self.salvar_unidade_escolhida(dialogo))
        btn_confirmar.setDefault(True)
        
        botoes_layout.addWidget(btn_cancelar)
        botoes_layout.addWidget(btn_confirmar)
        layout.addLayout(botoes_layout)
        
        dialogo.exec()
    
    def salvar_unidade_escolhida(self, dialogo):
        
        # Verificar qual botão está selecionado
        for unidade, radio in self.radio_buttons.items():
            if radio.isChecked():
                UNIDADE_ESCOLHIDA = unidade
                log_info(f"Unidade escolhida: {UNIDADE_ESCOLHIDA}")
                dialogo.accept()
                return
        
        # Se nenhum botão foi selecionado (não deveria acontecer devido ao padrão)
        QMessageBox.warning(dialogo, "Aviso", "Por favor, selecione uma unidade.")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._posicao_click = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._posicao_click)
            event.accept()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        aplicar_tema_claro(app)
        log_info("Aplicação STCAD iniciada")
        window = MainWindow()
        window.show()
        
        # Se estivermos no modo de debug, mostra a janela de debug automaticamente
        if os.environ.get("STCAD_DEBUG", "0") == "1":
            show_debug_window()
            
        sys.exit(app.exec())
    except Exception as e:
        log_exception(e)
        # Aqui você pode exibir uma mensagem de erro ou simplesmente deixar o aplicativo falhar
        raise



