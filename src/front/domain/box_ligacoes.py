from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox,QDialog, 
QMenuBar, QHBoxLayout, QPushButton, QLabel, QProgressBar, QMessageBox)
from PySide6.QtCore import QTimer, QThreadPool, Qt
from PySide6.QtGui import QAction, QFont, QIcon
from back.conversions import CONVERSORES
from back import conversions
from back.logs import registrar_marcha
from back.draw_utils import tentar_desenhar_autocad_com_retentativas, DesenhoWorker
from back import draw_utils
from front.debug_utils import log_info, log_error, log_exception
from front.marcha_calculo_window import MarchaCalculoWindow
import back.draw_utils
import tempfile
import os


class Box_Ligacao(QWidget):
    def __init__(self, titulo):
        super().__init__()
        self.setWindowTitle(f"Parâmetros - {titulo}")
        self.setGeometry(150, 150, 450, 300)
        self.setWindowIcon(QIcon("../assets/imagem_icon/icon_stcad.ico"))
        self.layout_principal = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.layout_principal.addLayout(self.form_layout)
        self.init_menu_avancado()
        self.setLayout(self.layout_principal)
        self.dados_resultado : list
        self.obs = "Observações: \n"  # Inicializa com uma string vazia
        log_info(f"Inicializada janela de {titulo}")

    def init_menu_avancado(self):
        self.menu_bar = QMenuBar()
        menu = self.menu_bar.addMenu("Menu")
        self.acao_toggle = QAction("Opções Avançadas", self)
        self.acao_toggle.triggered.connect(self.toggle_opcoes_avancadas)
        menu.addAction(self.acao_toggle)
        
        # Remover a opção de debug console dos menus individuais das ligações
        
        self.layout_principal.setMenuBar(self.menu_bar)

        self.opcoes_avancadas = QGroupBox("Opções Avançadas")
        self.avancado_layout = QFormLayout()
        self.opcoes_avancadas.setLayout(self.avancado_layout)
        self.opcoes_avancadas.setVisible(False)
        self.layout_principal.addWidget(self.opcoes_avancadas)

    def toggle_opcoes_avancadas(self):
        self.opcoes_avancadas.setVisible(not self.opcoes_avancadas.isVisible())
        log_info(f"Opções avançadas {'abertas' if self.opcoes_avancadas.isVisible() else 'fechadas'}")

    def adicionar_botoes_resultado(self, layout, janela_resultado):

        botoes = QHBoxLayout()
        botao_salvar = QPushButton("💾 TXT: Dimensionamento")
        botao_salvar.clicked.connect(lambda: self.salvar_resultado_txt(layout))
        botoes.addWidget(botao_salvar)

        botao_salvar_marcha = QPushButton("📋 Marcha de Cálculo")
        botao_salvar_marcha.clicked.connect(self.mostrar_marcha_calculo)
        # botao_salvar_marcha.setStyleSheet("""
        #     QPushButton {
        #         background-color: #2c3e50;
        #         color: white;
        #         border: none;
        #         padding: 8px 16px;
        #         border-radius: 4px;
        #         font-weight: bold;
        #     }
        #     QPushButton:hover {
        #         background-color: #34495e;
        #     }
        # """)
        botoes.addWidget(botao_salvar_marcha)

        # Verificar se AutoCAD está disponível
        if draw_utils.AUTOCAD:
            botao_desenho = QPushButton("🎨 Desenhar (DXF/DWG)")
            botao_desenho.setToolTip("AutoCAD disponível - Escolha entre DXF ou DWG")
            botao_desenho.clicked.connect(lambda: self.selecionar_formato())
    
        else:
            botao_desenho = QPushButton("📄 Desenhar (DXF)")
            botao_desenho.setToolTip("Desenho em formato DXF - compatível com vários programas CAD")
            botao_desenho.clicked.connect(lambda: self.formato_dxf(self.dados_resultado))

        botoes.addWidget(botao_desenho)

        botao_ok = QPushButton("✅ OK")
        botao_ok.clicked.connect(janela_resultado.close)
        botoes.addWidget(botao_ok)

        layout.addLayout(botoes)
    
    def selecionar_formato(self):
        self.dialogo = QDialog(self)
        self.dialogo.setWindowTitle("Escolha do formato a ser salvo")
        self.dialogo.setFixedSize(400, 100)
        
        layout = QVBoxLayout()
        self.setWindowIcon(QIcon("../assets/imagem_icon/icon_stcad.ico"))
        
        # Título centralizado na parte superior
        titulo = QLabel("Selecione o formato para ser desenhado o detalhamento:")
        titulo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Layout horizontal para os botões
        botoes_layout = QHBoxLayout()
        
        # Botão DXF
        botao_dxf = QPushButton("DXF\n(Qualquer software CAD)")
        botao_dxf.clicked.connect(lambda: [self.formato_dxf(self.dados_resultado), self.dialogo.close()])
        botao_dxf.setFixedHeight(50)
        botoes_layout.addWidget(botao_dxf)

        # Botão DWG
        botao_dwg = QPushButton("DWG\n(Desenhado no AutoCAD)")
        botao_dwg.clicked.connect(lambda: [self.formato_dwg(self.dados_resultado), self.dialogo.close()])
        botao_dwg.setFixedHeight(50)
        botoes_layout.addWidget(botao_dwg)

        # Botão OK
        botao_ok = QPushButton("✅ OK")
        botao_ok.clicked.connect(self.dialogo.close)
        botao_ok.setFixedHeight(50)
        botoes_layout.addWidget(botao_ok)
        
        # Adicionar o layout de botões ao layout principal
        layout.addLayout(botoes_layout)
        layout.addStretch()
        
        self.dialogo.setLayout(layout)
        self.dialogo.exec()

    def formato_dwg(self,dados_resultado):
        back.draw_utils.DXF = 0
        self.executar_desenho_dwg(dados_resultado)
    
    def formato_dxf(self,dados_resultado):
        back.draw_utils.DXF = 1
        self.desenhar_no_autocad(dados_resultado)

    def executar_desenho_dwg(self, dados_resultado):
        try:
            # Verificar novamente se AutoCAD está disponível
            if not draw_utils.AUTOCAD:
                QMessageBox.warning(
                    self, 
                    "AutoCAD Não Disponível", 
                    "O AutoCAD não está configurado como disponível.\n\n"
                    "Para usar esta funcionalidade:\n"
                    "1. Certifique-se de que o AutoCAD está instalado e licenciado\n"
                    "2. Vá em Menu > Configurar AutoCAD na tela principal\n"
                    "3. Configure como 'Sim, tenho AutoCAD instalado e licenciado'"
                )
                return
                
            log_info("Iniciando desenho no AutoCAD")
            QMessageBox.information(self, "Desenho Iniciado", "Clique OK e aguarde o AutoCAD finalizar. A barra mostrará o progresso real.")
            self.iniciar_barra_progresso()

            def processo_desenho():
                try:
                    log_info("Executando desenho no AutoCAD")
                    tentar_desenhar_autocad_com_retentativas(lambda: self.desenhar_no_autocad(dados_resultado))
                    log_info("Desenho AutoCAD concluído com sucesso")
                except Exception as e:
                    log_exception(e)
                    raise
                    
            self.worker = DesenhoWorker(processo_desenho)
            self.worker.signals.finished.connect(self.finalizar_barra_progresso)
            QThreadPool.globalInstance().start(self.worker)

        except Exception as e:
            log_exception(e)
            QMessageBox.critical(self, "Erro", f"Erro ao desenhar no AutoCAD:\n{str(e)}")

    def iniciar_barra_progresso(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout_principal.addWidget(self.progress_bar)

    def finalizar_barra_progresso(self, duracao_segundos):
        log_info(f"Desenho concluído em {duracao_segundos:.2f} segundos")

        self.progress = 0
        steps = 100
        intervalo = duracao_segundos / (2*steps)  # segundos por passo (~frações de segundo)

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

    def desenhar_no_autocad(self, dados_resultado):
        """
        Método para ser sobrescrito nas classes filhas.
        Implementa o desenho no AutoCAD baseado nos resultados.
        """
        log_error("Método desenhar_no_autocad não implementado na classe derivada")
        raise NotImplementedError("Este método deve ser implementado em uma classe derivada")
        """
        log_error("Método desenhar_no_autocad não implementado na classe derivada")
        Implementa o desenho no AutoCAD baseado nos resultados.
                raise NotImplementedError("Este método deve ser implementado em uma classe derivada")"""

    def conversor_unidades(self, momento, cortante, tracao):
        """
        Converte os valores de entrada para as unidades corretas conforme a unidade escolhida globalmente.
        
        Args:
            momento: Campo de entrada com o valor do momento (QLineEdit ou similar)
            cortante: Campo de entrada com o valor do cortante (QLineEdit ou similar)
            tracao: Campo de entrada com o valor da tração (QLineEdit ou similar)
        
        Returns:
            Lista contendo [M, V, T] em kN·mm, kN e kN respectivamente
        """
        try:
            # Obtém a unidade selecionada pelo usuário da variável global
            unidade_atual = str(conversions.UNIDADE_ESCOLHIDA)
            log_info(f"Unidade atual selecionada: {unidade_atual}")
            
            # Obtém os conversores apropriados para a unidade selecionada
            conversor = CONVERSORES[unidade_atual]
            conversor_momento = conversor["momento"]
            conversor_forca = conversor["força"]
            
            # Aplica os conversores aos valores de entrada
            M = conversor_momento(str(momento))
            V = conversor_forca((cortante))
            T = conversor_forca((tracao))
            
            # Registrar o tipo de unidade no log de marcha de cálculo
            rotulos = conversor["rótulos"]
            registrar_marcha(f"Unidade selecionada: {unidade_atual} ({rotulos[0]} para força, {rotulos[1]} para momento)")
            
            log_info(f"Conversão de unidades ({unidade_atual}): M={M:.2f} kN·mm, V={V:.2f} kN, T={T:.2f} kN")
            return [M, V, T]
        except Exception as e:
            log_exception(e)
            raise ValueError(f"Erro na conversão de unidades: {str(e)}")
        
    def mostrar_marcha_calculo(self):
        """Abre a nova janela elegante da marcha de cálculo"""
        try:
            self.marcha_window = MarchaCalculoWindow(self)
            self.marcha_window.show()
            log_info("Janela de marcha de cálculo aberta")
        except Exception as e:
            log_exception(e)
            QMessageBox.critical(self, "Erro", f"Erro ao abrir marcha de cálculo:\n{str(e)}")

    def salvar_resultado_txt(self, layout):
        try:
            conteudo = ""
            for i in range(layout.count()):
                item = layout.itemAt(i).widget()
                if isinstance(item, QLabel):
                    conteudo += item.text() + "\n"
            conteudo += self.obs  # Remove a última quebra de linha
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
                tmp.write(conteudo)
                caminho = tmp.name
            
            log_info(f"Resultado TXT salvo em {caminho}")
            os.startfile(caminho)  # Abre com o editor de texto padrão do Windows
        except Exception as e:
            log_exception(e)
            QMessageBox.critical(self, "Erro", f"Erro ao salvar resultado: {str(e)}")

    def salvar_marcha(self):
        """Método mantido para compatibilidade - agora abre a nova janela"""
        self.mostrar_marcha_calculo()