from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QMenuBar, QMenu, QGroupBox,QHBoxLayout,QPushButton,QLabel
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QProgressBar,QMessageBox

import tempfile
import os

class ParametrosLigacaoBase(QWidget):
    def __init__(self, titulo):
        super().__init__()
        self.setWindowTitle(f"Parâmetros - {titulo}")
        self.setGeometry(150, 150, 200, 300)

        self.layout_principal = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.layout_principal.addLayout(self.form_layout)
        self.init_menu_avancado()
        self.setLayout(self.layout_principal)

    def init_menu_avancado(self):
        self.menu_bar = QMenuBar()
        menu = self.menu_bar.addMenu("Menu")
        self.acao_toggle = QAction("Opções Avançadas", self)
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

    def adicionar_botoes_resultado(self, layout, janela_resultado):
        botoes = QHBoxLayout()

        botao_salvar = QPushButton("Salvar como TXT")
        botao_salvar.clicked.connect(lambda: self.salvar_resultado_txt(layout))
        botoes.addWidget(botao_salvar)

        botao_autocad = QPushButton("Desenhar no AutoCAD")
        botao_autocad.clicked.connect(lambda: self.executar_desenho_com_barra(self.dados_resultado))
        botoes.addWidget(botao_autocad)  

        botao_ok = QPushButton("OK")
        botao_ok.clicked.connect(janela_resultado.close)
        botoes.addWidget(botao_ok)

        layout.addLayout(botoes)

    def salvar_resultado_txt(self, layout):

        conteudo = ""
        for i in range(layout.count()):
            item = layout.itemAt(i).widget()
            if isinstance(item, QLabel):
                conteudo += item.text() + "\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(conteudo)
            caminho = tmp.name

        os.startfile(caminho)  # Abre com o editor de texto padrão do Windows

    def executar_desenho_com_barra(self, dados_resultado):
        try:
            self.desenhar_no_autocad(dados_resultado) 
            QMessageBox.information(self, "Desenho Iniciado", "Calma! Clique OK e sua ligação estará sendo desenhada no AutoCAD, espere a barra de progresso completar 100%.")
            self.iniciar_barra_progresso()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao desenhar no AutoCAD:\n{e}")


    def iniciar_barra_progresso(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout_principal.addWidget(self.progress_bar)

        self.progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_barra_progresso)
        self.timer.start(100)  # leva 2 segundos total (100 ms * 20 passos)


    def atualizar_barra_progresso(self):
        self.progress += 5
        self.progress_bar.setValue(self.progress)
        if self.progress >= 100:
            self.timer.stop()
            self.layout_principal.removeWidget(self.progress_bar)
            self.progress_bar.deleteLater()
            QMessageBox.information(self, "Desenho Concluído", "Ligação desenhada com sucesso no AutoCAD!")


    def ler_forca_tonelada(self, campo_input):
        texto = campo_input.text().strip().replace(",", ".")
        if not texto:
            return 0.0
        valor_tf = float(texto)
        return valor_tf * 9.80665  # converte tf para kN

    def ler_momento_tonelada_metro(self, campo_input):
        texto = campo_input.text().strip().replace(",", ".")
        if not texto:
            return 0.0
        valor_tf_m = float(texto)
        return valor_tf_m * 9806.65  # converte tf·m para kN·mm



