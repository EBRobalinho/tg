import logging
import traceback
import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, 
     QTabWidget, QWidget, QHBoxLayout,
    QCheckBox, QSplitter
)
from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtGui import QFont, QColor

# Configuração de logging padrão
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "app_debug.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configurar logger global
logger = logging.getLogger('STCAD')
logger.setLevel(logging.DEBUG)

# Handler para arquivo
file_handler = logging.FileHandler(LOG_FILE, mode='a')
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# Variáveis globais para controle de UI
DEBUG_WINDOW = None
BUFFER = []
MAX_BUFFER_SIZE = 1000

class DebugSignals(QObject):
    """Classe para emitir sinais de eventos de debug"""
    new_log = Signal(str, str)  # level, message
    exception = Signal(str, str, str)  # type, message, traceback

debug_signals = DebugSignals()

def log_debug(message):
    """Registra mensagem de debug"""
    logger.debug(message)
    BUFFER.append(("DEBUG", message))
    debug_signals.new_log.emit("DEBUG", message)
    trim_buffer()

def log_info(message):
    """Registra mensagem informativa"""
    logger.info(message)
    BUFFER.append(("INFO", message))
    debug_signals.new_log.emit("INFO", message)
    trim_buffer()

def log_warning(message):
    """Registra mensagem de aviso"""
    logger.warning(message)
    BUFFER.append(("WARNING", message))
    debug_signals.new_log.emit("WARNING", message)
    trim_buffer()

def log_error(message):
    """Registra mensagem de erro"""
    logger.error(message)
    BUFFER.append(("ERROR", message))
    debug_signals.new_log.emit("ERROR", message)
    trim_buffer()

def log_exception(e=None):
    """Captura e registra exceção atual"""
    if e is None:
        exc_type, exc_value, exc_tb = sys.exc_info()
    else:
        exc_type, exc_value, exc_tb = type(e), e, e.__traceback__
    
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    # Log para arquivo
    exc_name = exc_type.__name__ if exc_type else "Unknown"
    logger.error(f"Exception: {exc_name}: {exc_value}\n{tb_str}")
    
    # Log para buffer
    BUFFER.append(("EXCEPTION", f"{exc_name}: {exc_value}"))
    # Emitir sinal
    debug_signals.exception.emit(
        exc_name, str(exc_value), tb_str
    )
    trim_buffer()
    
    return tb_str

def trim_buffer():
    """Mantém o buffer dentro do tamanho máximo definido"""
    global BUFFER
    if len(BUFFER) > MAX_BUFFER_SIZE:
        BUFFER = BUFFER[-MAX_BUFFER_SIZE:]

def show_debug_window():
    """Mostra a janela de debug ou a traz para frente se já estiver aberta"""
    global DEBUG_WINDOW
    if DEBUG_WINDOW is None or not DEBUG_WINDOW.isVisible():
        DEBUG_WINDOW = DebugWindow()
        DEBUG_WINDOW.show()
    else:
        DEBUG_WINDOW.activateWindow()
        DEBUG_WINDOW.raise_()

class DebugWindow(QDialog):
    """Janela de debug que exibe logs e exceções em tempo real"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("STCAD Debug Console")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlag(Qt.WindowType.Window)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Abas
        self.tab_widget = QTabWidget()
        
        # Tab de logs
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)
        
        # Filtros
        filter_layout = QHBoxLayout()
        self.chk_debug = QCheckBox("Debug")
        self.chk_info = QCheckBox("Info")
        self.chk_warning = QCheckBox("Warning")
        self.chk_error = QCheckBox("Error")
        
        for chk in [self.chk_debug, self.chk_info, self.chk_warning, self.chk_error]:
            chk.setChecked(True)
            chk.stateChanged.connect(self.filter_logs)
            filter_layout.addWidget(chk)
        
        log_layout.addLayout(filter_layout)
        
        # Editor de texto para logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        font = QFont("Consolas", 10)
        self.log_text.setFont(font)
        log_layout.addWidget(self.log_text)
        
        # Tab de exceções
        self.exception_tab = QWidget()
        exception_layout = QVBoxLayout(self.exception_tab)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Lista de exceções
        self.exception_list = QTextEdit()
        self.exception_list.setReadOnly(True)
        self.exception_list.setMaximumHeight(150)
        self.exception_list.setFont(font)
        splitter.addWidget(self.exception_list)
        
        # Detalhes da exceção selecionada
        self.exception_details = QTextEdit()
        self.exception_details.setReadOnly(True)
        self.exception_details.setFont(font)
        splitter.addWidget(self.exception_details)
        
        exception_layout.addWidget(splitter)
        
        # Adicionar abas ao widget
        self.tab_widget.addTab(self.log_tab, "Logs")
        self.tab_widget.addTab(self.exception_tab, "Exceções")
        
        # Adicionar o widget de abas ao layout principal
        main_layout.addWidget(self.tab_widget)
        
        # Botões de controle
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_button)
        
        save_button = QPushButton("Salvar Logs")
        save_button.clicked.connect(self.save_logs)
        button_layout.addWidget(save_button)
        
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
        # Conectar sinais
        debug_signals.new_log.connect(self.on_new_log)
        debug_signals.exception.connect(self.on_exception)
        
        # Carregar logs existentes
        self.reload_logs()
        
        # Auto-refresh
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.reload_logs)
        self.timer.start(1000)  # atualiza a cada 1 segundo
    
    def reload_logs(self):
        """Carrega logs do buffer"""
        self.log_text.clear()
        for level, msg in BUFFER:
            self.display_log(level, msg)
    
    def on_new_log(self, level, message):
        """Callback para novo log"""
        self.display_log(level, message)
    
    def display_log(self, level, message):
        """Exibe mensagem de log conforme filtro selecionado"""
        should_display = (
            (level == "DEBUG" and self.chk_debug.isChecked()) or
            (level == "INFO" and self.chk_info.isChecked()) or
            (level == "WARNING" and self.chk_warning.isChecked()) or
            (level == "ERROR" and self.chk_error.isChecked()) or
            level == "EXCEPTION"
        )
        
        if should_display:
            # Cores para níveis de log
            if level == "DEBUG":
                color = QColor(128, 128, 128)  # Cinza
            elif level == "INFO":
                color = QColor(0, 0, 0)  # Preto
            elif level == "WARNING":
                color = QColor(255, 165, 0)  # Laranja
            elif level == "ERROR" or level == "EXCEPTION":
                color = QColor(255, 0, 0)  # Vermelho
            else:
                color = QColor(0, 0, 0)  # Preto default
            
            # Formatar texto com cor
            self.log_text.setTextColor(color)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}] {level}: {message}")
    
    def on_exception(self, exc_type, exc_value, tb_str):
        """Callback para nova exceção"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {exc_type}: {exc_value}"
        
        # Adicionar à lista de exceções
        self.exception_list.append(entry)
        
        # Adicionar aos detalhes
        self.exception_details.clear()
        self.exception_details.setTextColor(QColor(255, 0, 0))
        self.exception_details.append(f"{exc_type}: {exc_value}")
        self.exception_details.setTextColor(QColor(0, 0, 0))
        self.exception_details.append(tb_str)
        
        # Mudar para a aba de exceções
        self.tab_widget.setCurrentWidget(self.exception_tab)
    
    def filter_logs(self):
        """Aplica filtro aos logs"""
        self.reload_logs()
    
    def clear_logs(self):
        """Limpa todos os logs"""
        self.log_text.clear()
        self.exception_list.clear()
        self.exception_details.clear()
        global BUFFER
        BUFFER = []
    
    def save_logs(self):
        """Salva logs em um arquivo"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Logs", "", "Log Files (*.log);;All Files (*.*)"
        )
        
        if filename:
            with open(filename, 'w') as f:
                for level, msg in BUFFER:
                    f.write(f"{level}: {msg}\n")

def excepthook(exc_type, exc_value, exc_traceback):
    """Substitui o excepthook padrão para capturar exceções não tratadas"""
    log_exception()
    # Chamar o excepthook original
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

# Substituir excepthook para capturar exceções não tratadas
sys.excepthook = excepthook

# Funções de decorador para debug
def debug_function(func):
    """Decorador para debug de função"""
    def wrapper(*args, **kwargs):
        arg_str = ", ".join([str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()])
        log_debug(f"Chamando {func.__name__}({arg_str})")
        try:
            result = func(*args, **kwargs)
            log_debug(f"{func.__name__} retornou: {result}")
            return result
        except Exception as e:
            log_exception(e)
            raise
    return wrapper
