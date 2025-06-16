from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QGroupBox, QMenuBar, QHBoxLayout, QPushButton, QLabel, QProgressBar, QMessageBox
from PySide6.QtCore import QTimer, QThreadPool
from PySide6.QtGui import QAction
from back.logs import MARCHA_LOG, limpar_marcha
from back.conversions import ler_momento_tonelada_metro, ler_forca_tonelada
import tempfile
import os

class Box_Ligacao(QWidget):
    def __init__(self, titulo):
        super().__init__()
        self.setWindowTitle(f"Parâmetros - {titulo}")
        self.setGeometry(150, 150, 450, 300)

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

        botao_salvar = QPushButton("TXT: Dimensionamento")
        botao_salvar.clicked.connect(lambda: self.salvar_resultado_txt(layout))
        botoes.addWidget(botao_salvar)

        botao_salvar_marcha = QPushButton("TXT: Marcha de Cálculo")
        botao_salvar_marcha.clicked.connect(self.salvar_marcha)
        botoes.addWidget(botao_salvar_marcha)

        botao_autocad = QPushButton("DWG: Desenho no AutoCAD")
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
        conteudo += self.obs  # Remove a última quebra de linha
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(conteudo)
            caminho = tmp.name

        os.startfile(caminho)  # Abre com o editor de texto padrão do Windows

    def salvar_marcha(self):
        if not MARCHA_LOG:
            return  # ou mostrar mensagem de "nenhuma marcha registrada"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.writelines(MARCHA_LOG)
            caminho = tmp.name
            limpar_marcha()
        os.startfile(caminho)  # Abre com o editor de texto padrão do Windows

    def executar_desenho_com_barra(self, dados_resultado):
        try:
            QMessageBox.information(self, "Desenho Iniciado", "Clique OK e aguarde o AutoCAD finalizar. A barra mostrará o progresso real.")
            self.iniciar_barra_progresso()

            def processo_desenho():
                tentar_desenhar_autocad_com_retentativas(lambda: self.desenhar_no_autocad(dados_resultado))
            self.worker = DesenhoWorker(processo_desenho)

            self.worker.signals.finished.connect(self.finalizar_barra_progresso_sincronizado)

            QThreadPool.globalInstance().start(self.worker)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao desenhar no AutoCAD:\n{e}")

    def iniciar_barra_progresso(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout_principal.addWidget(self.progress_bar)

    def finalizar_barra_progresso_sincronizado(self, duracao_segundos):

        self.progress = 0
        steps = 100
        intervalo = duracao_segundos / steps  # segundos por passo (~frações de segundo)

        def atualizar():
            self.progress += 1
            self.progress_bar.setValue(self.progress)
            if self.progress >= 100:
                self.timer.stop()
                QMessageBox.information(self, "Desenho Concluído", "Ligação desenhada com sucesso no AutoCAD!")
                self.layout_principal.removeWidget(self.progress_bar)
                self.progress_bar.deleteLater()

        self.timer = QTimer()
        self.timer.timeout.connect(atualizar)
        self.timer.start(int(intervalo * 1000))  # converte para ms

    def conversor_unidades(self, momento, cortante, tracao):
        # Converte os valores de entrada para as unidades corretas
        M = ler_momento_tonelada_metro(momento)
        V = ler_forca_tonelada(cortante)
        T = ler_forca_tonelada(tracao)
        return [M, V, T]

