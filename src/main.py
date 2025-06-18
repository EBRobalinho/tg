from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout,QDialog,
     QScrollArea, QGridLayout, QMenu, QToolButton, QMainWindow, QMessageBox,
     QRadioButton, QGroupBox, QButtonGroup, QTabWidget, QListWidget, QLineEdit,
     QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox
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
from back import conversions
from back.conversions import CONVERSORES
from back import draw_utils

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
        self.setWindowTitle("STCAD – Structural Connections for CAD")
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
        barra_titulo.setStyleSheet(f"background-color: {COR_BARRA_SUPERIOR};")
        
        # Menu principal
        btn_menu = QToolButton()
        btn_menu.setText("Menu")
        btn_menu.setStyleSheet(STYLE_BOTAO_MENU)
        btn_menu.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        menu_principal = QMenu()
        menu_principal.addAction("Ajuda", self.mostrar_ajuda)
        menu_principal.addAction("Sobre", self.mostrar_sobre)
        
        btn_menu.clicked.connect(
            lambda: menu_principal.exec(btn_menu.mapToGlobal(btn_menu.rect().bottomLeft()))
        )
        
        # Menu de configurações
        btn_config = QToolButton()
        btn_config.setText("Configurações")
        btn_config.setStyleSheet(STYLE_BOTAO_MENU)
        btn_config.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        menu_config = QMenu()
        menu_config.addAction("Unidades", self.escolher_unidades)
        menu_config.addAction("Configurar AutoCAD", self.configurar_autocad)
        menu_config.addAction("Gerenciar Materiais", self.gerenciar_materiais)
        
        # Adicionar opção de debug se o modo de debug estiver ativo
        if os.environ.get("STCAD_DEBUG", "0") == "1":
            menu_config.addAction("Debug Console", show_debug_window)
        
        btn_config.clicked.connect(
            lambda: menu_config.exec(btn_config.mapToGlobal(btn_config.rect().bottomLeft()))
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
        barra_layout.addWidget(btn_menu)
        barra_layout.addWidget(btn_config)
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
            if unidade == conversions.UNIDADE_ESCOLHIDA:
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
                
                conversions.UNIDADE_ESCOLHIDA = unidade
                log_info(f"Unidade escolhida: {conversions.UNIDADE_ESCOLHIDA}")
                dialogo.accept()
                return
        
        # Se nenhum botão foi selecionado (não deveria acontecer devido ao padrão)
        QMessageBox.warning(dialogo, "Aviso", "Por favor, selecione uma unidade.")

    def configurar_autocad(self):
        """
        Abre um diálogo para configurar se o AutoCAD está disponível no sistema.
        """
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Configuração do AutoCAD")
        dialogo.setFixedSize(450, 300)
        
        layout = QVBoxLayout(dialogo)
        
        titulo = QLabel("Configuração do AutoCAD")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Texto explicativo
        explicacao = QLabel(
            "O STCAD pode gerar desenhos técnicos em formato .dwg através do AutoCAD.\n\n"
            "Para utilizar esta funcionalidade, você precisa ter o AutoCAD instalado "
            "e licenciado em seu computador.\n\n"
            "Selecione a opção que corresponde à sua situação:"
        )
        explicacao.setWordWrap(True)
        explicacao.setAlignment(Qt.AlignmentFlag.AlignJustify)
        layout.addWidget(explicacao)
        
        # Grupo de botões de rádio
        grupo_box = QGroupBox("Status do AutoCAD")
        grupo_layout = QVBoxLayout()
        
        button_group = QButtonGroup(dialogo)
        
        # Botões de rádio
        self.radio_autocad_sim = QRadioButton("Sim, tenho AutoCAD instalado e licenciado")
        self.radio_autocad_nao = QRadioButton("Não, não possuo AutoCAD ou não está funcionando")
        
        # Define o estado atual baseado na variável global
        if draw_utils.AUTOCAD:
            self.radio_autocad_sim.setChecked(True)
        else:
            self.radio_autocad_nao.setChecked(True)
        
        button_group.addButton(self.radio_autocad_sim)
        button_group.addButton(self.radio_autocad_nao)
        
        grupo_layout.addWidget(self.radio_autocad_sim)
        grupo_layout.addWidget(self.radio_autocad_nao)
        
        grupo_box.setLayout(grupo_layout)
        layout.addWidget(grupo_box)
        
        # Aviso sobre funcionalidade reduzida
        aviso = QLabel(
            "⚠️ Nota: Se você selecionar 'Não', os botões de desenho no AutoCAD "
            "estarão desabilitados nas janelas de resultado."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet("color: #d47500; font-style: italic;")
        layout.addWidget(aviso)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialogo.reject)
        
        btn_confirmar = QPushButton("Salvar Configuração")
        btn_confirmar.clicked.connect(lambda: self.salvar_config_autocad(dialogo))
        btn_confirmar.setDefault(True)
        
        botoes_layout.addWidget(btn_cancelar)
        botoes_layout.addWidget(btn_confirmar)
        layout.addLayout(botoes_layout)
        
        dialogo.exec()
    
    def salvar_config_autocad(self, dialogo):
        """
        Salva a configuração do AutoCAD na variável global.
        """
        if self.radio_autocad_sim.isChecked():
            draw_utils.AUTOCAD = True
            log_info("AutoCAD configurado como disponível")
            QMessageBox.information(
                dialogo, 
                "Configuração Salva", 
                "AutoCAD configurado como disponível.\n"
                "Os botões de desenho estarão habilitados."
            )
        else:
            draw_utils.AUTOCAD = False
            log_info("AutoCAD configurado como não disponível")
            QMessageBox.information(
                dialogo, 
                "Configuração Salva", 
                "AutoCAD configurado como não disponível.\n"
                "Os botões de desenho estarão desabilitados."
            )
        
        dialogo.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._posicao_click = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._posicao_click)
            event.accept()

    def gerenciar_materiais(self):
        """
        Abre uma janela para visualizar e gerenciar a base de dados de materiais.
        """
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Gerenciar Base de Dados de Materiais")
        dialogo.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout(dialogo)
        
        titulo = QLabel("Base de Dados de Materiais")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Criar abas para cada tipo de material
        tab_widget = QTabWidget()
        
        # Aba de Aços
        tab_acos = self.criar_aba_acos()
        tab_widget.addTab(tab_acos, "Aços")
        
        # Aba de Parafusos
        tab_parafusos = self.criar_aba_parafusos()
        tab_widget.addTab(tab_parafusos, "Parafusos")
        
        # Aba de Soldas
        tab_soldas = self.criar_aba_soldas()
        tab_widget.addTab(tab_soldas, "Soldas")
        
        layout.addWidget(tab_widget)
        
        # Botão para fechar
        botao_fechar = QPushButton("Fechar")
        botao_fechar.clicked.connect(dialogo.close)
        layout.addWidget(botao_fechar)
        
        dialogo.exec()
    
    def criar_aba_acos(self):
        """Cria a aba para gerenciar aços"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Importar localmente para evitar importação circular
        from back.materials_loader import DIMENSOES_AÇO
        
        titulo = QLabel("Aços Disponíveis")
        titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(titulo)
        
        # Lista de aços existentes
        lista_acos = QListWidget()
        for nome, propriedades in DIMENSOES_AÇO.items():
            fy, fu, E, densidade = propriedades
            texto = f"{nome} - fy: {fy} MPa, fu: {fu} MPa, E: {E} GPa, ρ: {densidade} kg/m³"
            lista_acos.addItem(texto)
        
        layout.addWidget(lista_acos)
        
        # Botões para gerenciar a lista
        botoes_lista = QHBoxLayout()
        
        botao_remover_aco = QPushButton("Remover Selecionado")
        botao_remover_aco.clicked.connect(lambda: self.remover_aco(lista_acos))
        botoes_lista.addWidget(botao_remover_aco)
        
        botoes_lista.addStretch()
        layout.addLayout(botoes_lista)
        
        # Formulário para adicionar novo aço
        form_layout = QFormLayout()
        
        self.input_nome_aco = QLineEdit()
        self.input_nome_aco.setPlaceholderText("Ex: ASTM_A992")
        form_layout.addRow("Nome do Aço:", self.input_nome_aco)
        
        self.input_fy = QSpinBox()
        self.input_fy.setRange(100, 1000)
        self.input_fy.setValue(250)
        self.input_fy.setSuffix(" MPa")
        form_layout.addRow("Tensão de Escoamento (fy):", self.input_fy)
        
        self.input_fu = QSpinBox()
        self.input_fu.setRange(200, 1500)
        self.input_fu.setValue(400)
        self.input_fu.setSuffix(" MPa")
        form_layout.addRow("Tensão de Ruptura (fu):", self.input_fu)
        
        self.input_E = QSpinBox()
        self.input_E.setRange(150, 250)
        self.input_E.setValue(200)
        self.input_E.setSuffix(" GPa")
        form_layout.addRow("Módulo de Elasticidade (E):", self.input_E)
        
        self.input_densidade = QSpinBox()
        self.input_densidade.setRange(7000, 8500)
        self.input_densidade.setValue(7850)
        self.input_densidade.setSuffix(" kg/m³")
        form_layout.addRow("Densidade:", self.input_densidade)
        
        layout.addLayout(form_layout)
        
        # Botão para adicionar
        botao_adicionar_aco = QPushButton("Adicionar Aço")
        botao_adicionar_aco.clicked.connect(lambda: self.adicionar_aco(lista_acos))
        layout.addWidget(botao_adicionar_aco)
        
        return widget
    
    def criar_aba_parafusos(self):
        """Cria a aba para gerenciar parafusos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        from back.materials_loader import DIMENSOES_PARAFUSO
        
        titulo = QLabel("Parafusos Disponíveis")
        titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(titulo)
        
        # Lista de parafusos existentes
        lista_parafusos = QListWidget()
        for nome, propriedades in DIMENSOES_PARAFUSO.items():
            if propriedades[0] is None:
                texto = f"{nome} - fu: {propriedades[1]} MPa (sem escoamento definido)"
            else:
                texto = f"{nome} - fy: {propriedades[0]} MPa, fu: {propriedades[1]} MPa"
            lista_parafusos.addItem(texto)
        
        layout.addWidget(lista_parafusos)
        
        # Botões para gerenciar a lista
        botoes_lista = QHBoxLayout()
        
        botao_remover_parafuso = QPushButton("Remover Selecionado")
        botao_remover_parafuso.clicked.connect(lambda: self.remover_parafuso(lista_parafusos))
        botoes_lista.addWidget(botao_remover_parafuso)
        
        botoes_lista.addStretch()
        layout.addLayout(botoes_lista)
        
        # Formulário para adicionar novo parafuso
        form_layout = QFormLayout()
        
        self.input_nome_parafuso = QLineEdit()
        self.input_nome_parafuso.setPlaceholderText("Ex: ASTM_A449")
        form_layout.addRow("Nome do Parafuso:", self.input_nome_parafuso)
        
        self.input_fy_parafuso = QSpinBox()
        self.input_fy_parafuso.setRange(0, 1500)
        self.input_fy_parafuso.setValue(635)
        self.input_fy_parafuso.setSuffix(" MPa")
        self.input_fy_parafuso.setSpecialValueText("Sem escoamento")
        form_layout.addRow("Tensão de Escoamento (fy):", self.input_fy_parafuso)
        
        self.input_fu_parafuso = QSpinBox()
        self.input_fu_parafuso.setRange(300, 2000)
        self.input_fu_parafuso.setValue(830)
        self.input_fu_parafuso.setSuffix(" MPa")
        form_layout.addRow("Tensão de Ruptura (fu):", self.input_fu_parafuso)
        
        # Lista de diâmetros (simplificada)
        info_diametros = QLabel("Nota: Os diâmetros padrão serão aplicados automaticamente conforme AISC.")
        info_diametros.setWordWrap(True)
        info_diametros.setStyleSheet("font-style: italic; color: #666;")
        form_layout.addRow("Diâmetros:", info_diametros)
        
        layout.addLayout(form_layout)
        
        # Botão para adicionar
        botao_adicionar_parafuso = QPushButton("Adicionar Parafuso")
        botao_adicionar_parafuso.clicked.connect(lambda: self.adicionar_parafuso(lista_parafusos))
        layout.addWidget(botao_adicionar_parafuso)
        
        return widget
    
    def criar_aba_soldas(self):
        """Cria a aba para gerenciar soldas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        from back.materials_loader import DIMENSOES_SOLDA
        
        titulo = QLabel("Soldas Disponíveis")
        titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(titulo)
        
        # Lista de soldas existentes
        lista_soldas = QListWidget()
        for nome, propriedades in DIMENSOES_SOLDA.items():
            texto = f"{nome} - Resistência: {propriedades[0]} ksi"
            lista_soldas.addItem(texto)
        
        layout.addWidget(lista_soldas)
        
        # Botões para gerenciar a lista
        botoes_lista = QHBoxLayout()
        
        botao_remover_solda = QPushButton("Remover Selecionado")
        botao_remover_solda.clicked.connect(lambda: self.remover_solda(lista_soldas))
        botoes_lista.addWidget(botao_remover_solda)
        
        botoes_lista.addStretch()
        layout.addLayout(botoes_lista)
        
        # Formulário para adicionar nova solda
        form_layout = QFormLayout()
        
        self.input_nome_solda = QLineEdit()
        self.input_nome_solda.setPlaceholderText("Ex: E110XX")
        form_layout.addRow("Nome da Solda:", self.input_nome_solda)
        
        self.input_resistencia_solda = QSpinBox()
        self.input_resistencia_solda.setRange(40, 150)
        self.input_resistencia_solda.setValue(70)
        self.input_resistencia_solda.setSuffix(" ksi")
        form_layout.addRow("Resistência:", self.input_resistencia_solda)
        
        layout.addLayout(form_layout)
        
        # Botão para adicionar
        botao_adicionar_solda = QPushButton("Adicionar Solda")
        botao_adicionar_solda.clicked.connect(lambda: self.adicionar_solda(lista_soldas))
        layout.addWidget(botao_adicionar_solda)
        
        return widget
    
    def remover_aco(self, lista_widget):
        """Remove um aço selecionado da base de dados"""
        item_atual = lista_widget.currentItem()
        if not item_atual:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um aço para remover.")
            return
        
        # Extrair o nome do aço do texto do item
        texto_item = item_atual.text()
        nome_aco = texto_item.split(" - ")[0]
        
        # Confirmar remoção
        resposta = QMessageBox.question(
            self, 
            "Confirmar Remoção", 
            f"Tem certeza que deseja remover o aço '{nome_aco}'?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            from back.materials_loader import DIMENSOES_AÇO
            from back.materials_loader import remove_material
            
            if nome_aco in DIMENSOES_AÇO:
                # Remover da memória
                del DIMENSOES_AÇO[nome_aco]
                
                # Remover do arquivo
                remove_material("acos.json", nome_aco)
                
                # Remover da lista visual
                row = lista_widget.row(item_atual)
                lista_widget.takeItem(row)
                
                log_info(f"Aço removido: {nome_aco}")
                QMessageBox.information(self, "Sucesso", f"Aço '{nome_aco}' removido com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", f"Aço '{nome_aco}' não encontrado na base de dados.")
    
    def remover_parafuso(self, lista_widget):
        """Remove um parafuso selecionado da base de dados"""
        item_atual = lista_widget.currentItem()
        if not item_atual:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um parafuso para remover.")
            return
        
        # Extrair o nome do parafuso do texto do item
        texto_item = item_atual.text()
        nome_parafuso = texto_item.split(" - ")[0]
        
        # Confirmar remoção
        resposta = QMessageBox.question(
            self, 
            "Confirmar Remoção", 
            f"Tem certeza que deseja remover o parafuso '{nome_parafuso}'?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            from back.materials_loader import DIMENSOES_PARAFUSO
            from back.materials_loader import remove_material
            
            if nome_parafuso in DIMENSOES_PARAFUSO:
                # Remover da memória
                del DIMENSOES_PARAFUSO[nome_parafuso]
                
                # Remover do arquivo
                remove_material("parafusos.json", nome_parafuso)
                
                # Remover da lista visual
                row = lista_widget.row(item_atual)
                lista_widget.takeItem(row)
                
                log_info(f"Parafuso removido: {nome_parafuso}")
                QMessageBox.information(self, "Sucesso", f"Parafuso '{nome_parafuso}' removido com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", f"Parafuso '{nome_parafuso}' não encontrado na base de dados.")
    
    def remover_solda(self, lista_widget):
        """Remove uma solda selecionada da base de dados"""
        item_atual = lista_widget.currentItem()
        if not item_atual:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma solda para remover.")
            return
        
        # Extrair o nome da solda do texto do item
        texto_item = item_atual.text()
        nome_solda = texto_item.split(" - ")[0]
        
        # Confirmar remoção
        resposta = QMessageBox.question(
            self, 
            "Confirmar Remoção", 
            f"Tem certeza que deseja remover a solda '{nome_solda}'?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            from back.materials_loader import DIMENSOES_SOLDA
            from back.materials_loader import remove_material
            
            if nome_solda in DIMENSOES_SOLDA:
                # Remover da memória
                del DIMENSOES_SOLDA[nome_solda]
                
                # Remover do arquivo
                remove_material("soldas.json", nome_solda)
                
                # Remover da lista visual
                row = lista_widget.row(item_atual)
                lista_widget.takeItem(row)
                
                log_info(f"Solda removida: {nome_solda}")
                QMessageBox.information(self, "Sucesso", f"Solda '{nome_solda}' removida com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", f"Solda '{nome_solda}' não encontrada na base de dados.")

    def adicionar_aco(self, lista_widget):
        """Adiciona um novo aço à base de dados"""
        nome = self.input_nome_aco.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Por favor, insira um nome para o aço.")
            return
        
        from back.materials_loader import DIMENSOES_AÇO
        from back.materials_loader import add_material
        
        if nome in DIMENSOES_AÇO:
            QMessageBox.warning(self, "Erro", f"O aço '{nome}' já existe na base de dados.")
            return
        
        fy = self.input_fy.value()
        fu = self.input_fu.value()
        E = self.input_E.value()
        densidade = self.input_densidade.value()
        
        propriedades = [fy, fu, E, densidade]
        
        # Adicionar à base de dados em memória
        DIMENSOES_AÇO[nome] = propriedades
        
        # Salvar no arquivo
        add_material("acos.json", nome, propriedades)
        
        # Atualizar a lista
        texto = f"{nome} - fy: {fy} MPa, fu: {fu} MPa, E: {E} GPa, ρ: {densidade} kg/m³"
        lista_widget.addItem(texto)
        
        # Limpar campos
        self.input_nome_aco.clear()
        self.input_fy.setValue(250)
        self.input_fu.setValue(400)
        self.input_E.setValue(200)
        self.input_densidade.setValue(7850)
        
        log_info(f"Novo aço adicionado: {nome}")
        QMessageBox.information(self, "Sucesso", f"Aço '{nome}' adicionado com sucesso!")
    
    def adicionar_parafuso(self, lista_widget):
        """Adiciona um novo parafuso à base de dados"""
        nome = self.input_nome_parafuso.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Por favor, insira um nome para o parafuso.")
            return
        
        from back.materials_loader import DIMENSOES_PARAFUSO
        from back.materials_loader import add_material
        
        if nome in DIMENSOES_PARAFUSO:
            QMessageBox.warning(self, "Erro", f"O parafuso '{nome}' já existe na base de dados.")
            return
        
        fy = self.input_fy_parafuso.value() if self.input_fy_parafuso.value() > 0 else None
        fu = self.input_fu_parafuso.value()
        
        # Diâmetros padrão conforme AISC
        diametros_padrao = ["1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]
        
        propriedades = [fy, fu, diametros_padrao]
        
        # Adicionar à base de dados em memória
        DIMENSOES_PARAFUSO[nome] = propriedades
        
        # Salvar no arquivo
        add_material("parafusos.json", nome, propriedades)
        
        # Atualizar a lista
        if fy is None:
            texto = f"{nome} - fu: {fu} MPa (sem escoamento definido)"
        else:
            texto = f"{nome} - fy: {fy} MPa, fu: {fu} MPa"
        lista_widget.addItem(texto)
        
        # Limpar campos
        self.input_nome_parafuso.clear()
        self.input_fy_parafuso.setValue(635)
        self.input_fu_parafuso.setValue(830)
        
        log_info(f"Novo parafuso adicionado: {nome}")
        QMessageBox.information(self, "Sucesso", f"Parafuso '{nome}' adicionado com sucesso!")
    
    def adicionar_solda(self, lista_widget):
        """Adiciona uma nova solda à base de dados"""
        nome = self.input_nome_solda.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Por favor, insira um nome para a solda.")
            return
        
        from back.materials_loader import DIMENSOES_SOLDA
        from back.materials_loader import add_material
        
        if nome in DIMENSOES_SOLDA:
            QMessageBox.warning(self, "Erro", f"A solda '{nome}' já existe na base de dados.")
            return
        
        resistencia = self.input_resistencia_solda.value()
        propriedades = [resistencia]
        
        # Adicionar à base de dados em memória
        DIMENSOES_SOLDA[nome] = propriedades
        
        # Salvar no arquivo
        add_material("soldas.json", nome, propriedades)
        
        # Atualizar a lista
        texto = f"{nome} - Resistência: {resistencia} ksi"
        lista_widget.addItem(texto)
        
        # Limpar campos
        self.input_nome_solda.clear()
        self.input_resistencia_solda.setValue(70)
        
        log_info(f"Nova solda adicionada: {nome}")
        QMessageBox.information(self, "Sucesso", f"Solda '{nome}' adicionada com sucesso!")

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



