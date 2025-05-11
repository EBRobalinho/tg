from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QMenuBar, QMenu, QGroupBox,QHBoxLayout,QPushButton,QLabel, QProgressBar,QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer
from draw_autocad.draw_autocad_figures import *
from pyautocad import Autocad, APoint 
import pythoncom
import win32com.client
import pywintypes
import tempfile
import os
import time
from PySide6.QtCore import QRunnable, Slot, QThreadPool, Signal, QObject

def iniciar_autocad():
        # Força o AutoCAD a abrir, se necessário
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = True  # Garante que a janela fique visível

    # Aguarda um tempo para garantir que carregou
    time.sleep(2)

    # Conecta com a instância ativa e garante documento aberto
    acad = Autocad(create_if_not_exists=True)
    return acad

class WorkerSignals(QObject):
    finished = Signal(float)  # envia o tempo total de execução (segundos)

class DesenhoWorker(QRunnable):
    def __init__(self, funcao_desenho):
        super().__init__()
        self.funcao_desenho = funcao_desenho
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        import time
        t0 = time.time()
        self.funcao_desenho()
        t1 = time.time()
        duracao = t1 - t0
        self.signals.finished.emit(duracao)

def tentar_desenhar_autocad_com_retentativas(funcao_desenho, tentativas=3, atraso=2):
    for tentativa in range(1, tentativas + 1):
        try:
            pythoncom.CoInitialize()  # garante contexto COM na thread
            funcao_desenho()
            return  # se rodar sem erro, sai da função
        except pywintypes.com_error as e:
            if str(abs(e.args[0])).startswith("21474"):
                print(f"Tentativa {tentativa} falhou: AutoCAD ocupado. Retentando em {atraso}s...")
                time.sleep(atraso)
            else:
                raise  # outros erros COM são reenviados
        finally:
            pythoncom.CoUninitialize()

    raise RuntimeError("Não foi possível se comunicar com o AutoCAD após múltiplas tentativas.")

class ParametrosLigacaoBase(QWidget):
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
        import time

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



