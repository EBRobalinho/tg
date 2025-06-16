from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QMenuBar, QGroupBox,QHBoxLayout,QPushButton,QLabel, QProgressBar,QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer
from pyautocad import Autocad 
from back.logs import MARCHA_LOG, limpar_marcha, registrar_marcha
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
            funcao_desenho()
            return  # se rodar sem erro, sai da função
        except pywintypes.com_error as e:
            if str(abs(e.args[0])).startswith("21474"):
                print(f"Tentativa {tentativa} falhou: AutoCAD ocupado. Retentando em {atraso}s...")
                time.sleep(atraso)
            else:
                raise  # outros erros COM são reenviados


    raise RuntimeError("Não foi possível se comunicar com o AutoCAD após múltiplas tentativas.")
