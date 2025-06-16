from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QGroupBox, QMenuBar, QHBoxLayout, QPushButton, QLabel, QProgressBar, QMessageBox, QComboBox, QLineEdit
from PySide6.QtCore import QTimer, QThreadPool
from PySide6.QtGui import QAction
from back.logs import MARCHA_LOG, limpar_marcha, registrar_marcha
from back.materials_constants import DIMENSOES_PERFIS, DIMENSOES_AÇO, DIMENSOES_SOLDA, DIMENSOES_PARAFUSO, gamma
from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.solda import Solda
from back.chapas_design import dim_chapa_cabeca
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

class Ligacao_Rigida(Box_Ligacao):
    def __init__(self):
        super().__init__("Ligação Rígida")
        self.combo_perfil : QComboBox
        self.combo_aco_perfil : QComboBox
        self.combo_aco : QComboBox
        self.input_momento : QLineEdit
        self.input_cortante : QLineEdit
        self.input_tracao : QLineEdit
        self.combo_parafuso : QComboBox
        self.combo_solda : QComboBox

    def receber_input(self):
        # Lê os valores dos esforços
        [M,V,T] = self.conversor_unidades(self.input_momento,self.input_cortante,self.input_tracao)

        # Verificação: todos os esforços são zero
        if all(x == 0 for x in [M, V, T]):
            registrar_marcha("\n Nenhum esforço foi informado. A ligação não foi solicitada.")
            raise ValueError("Nenhum esforço foi informado. A ligação não foi solicitada.")
            return

        # Dados que o usuário escolhe
        nome_perfil = self.combo_perfil.currentText()
        nome_aco_perfil = self.combo_aco_perfil.currentText()
        nome_aco = self.combo_aco.currentText()
        nome_parafuso = self.combo_parafuso.currentText()
        nome_solda = self.combo_solda.currentText()

        dimensoes_perfil = DIMENSOES_PERFIS[nome_perfil]
        dimensoes_aco_perfil = DIMENSOES_AÇO[nome_aco_perfil]
        dimensoes_aco      = DIMENSOES_AÇO[nome_aco]
        dimensoes_solda    = DIMENSOES_SOLDA[nome_solda]
        dimensoes_parafuso = DIMENSOES_PARAFUSO[nome_parafuso]

        self.inputs = [M, V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, nome_solda, dimensoes_solda]

class Chapa_Cabeca(Ligacao_Rigida):
    def __init__(self,titulo="Chapa de Cabeça"):
        super().__init__()
        
        # Campos principais
        self.combo_perfil = QComboBox()
        self.combo_perfil.addItems([k for k in DIMENSOES_PERFIS.keys()])
        self.form_layout.addRow("Perfil:", self.combo_perfil)

        self.combo_aco_perfil = QComboBox()
        self.combo_aco_perfil.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço do Perfil:", self.combo_aco_perfil)

        self.combo_aco = QComboBox()
        self.combo_aco.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço da Chapa:", self.combo_aco)

        self.input_momento = QLineEdit()
        self.form_layout.addRow("Momento (tf.m):", self.input_momento)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow("Força Cortante (tf):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (tf):", self.input_tracao)

        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in DIMENSOES_PARAFUSO.keys()])
        self.form_layout.addRow("Parafuso:", self.combo_parafuso)
        
        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in DIMENSOES_SOLDA.keys()])
        self.form_layout.addRow("Solda:", self.combo_solda)

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        # Opções Avançadas
        self.input_rosca = QComboBox()
        self.input_rosca.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ?", self.input_rosca)

        #self.input_planos = QLineEdit("1")
        #self.avancado_layout.addRow("Quantidade de planos de Corte no Parafuso:", self.input_planos)

        self.combo_chapa_rigida = QComboBox()
        self.combo_chapa_rigida.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("Chapa Rígida:", self.combo_chapa_rigida)

        #self.combo_filete_duplo = QComboBox()
        #self.combo_filete_duplo.addItems(["Simples", "Dupla"])
        #self.combo_filete_duplo.setCurrentText("Dupla")  # define "Dupla" como padrão
        #self.avancado_layout.addRow("Solda Dupla:", self.combo_filete_duplo)

    def executar_calculo(self):
        try:
            self.receber_input()
            # Desempacota os dados recebidos
            [M, V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
             nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, nome_solda, dimensoes_solda] = self.inputs

            aco_perfil = Aço(nome_aco_perfil,*dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,*dimensoes_perfil,*aco_perfil)
            perfil.inercias()
            aco      = Aço(nome_aco,*dimensoes_aco)      
            solda    = Solda(nome_solda,*dimensoes_solda)    
            parafuso = Parafuso(nome_parafuso,*dimensoes_parafuso)

            rosca = 1 if self.input_rosca.currentText() == "Sim" else False
            chapa_rigida = 1 if self.combo_chapa_rigida.currentText() == "Sim" else 0
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            filete_duplo = True

            # Função que faz o dimensionamento
            S = dim_chapa_cabeca(M, V, T, perfil, parafuso, gamma)

            if isinstance(S[0], str):  # se for string, é um erro
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S[0])  # lança a string como erro

            # Variáveis utilizadas
            diam_pol = S[1].diametro_pol
            N_parafusos = len(S[4])
            altura_chapa = S[3].df["y (mm)"].max()
            largura_chapa = S[3].df["x (mm)"].max()
            chapa = S[3]
            ver_parafuso = S[4]

            #Calculo da espessura da chapa e da solda
            r_parafuso_total = resistencia_total(S[1],materials.gamma)
            #Considera os parafusos trabalhando plasticamente de forma que cada um receba a mesma carga
            s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, S[1] , S[0])
            s_p_t = solicitante_parafuso_tração(T,N_parafusos)
            s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
            
            espessura_placa = exp_placa(aco,chapa,chapa_rigida,ver_parafuso,S[1].diametro_mm,r_parafuso_total, (s_p_m + s_p_t), materials.gamma)

            if espessura_placa==["A ligação não aguenta a solicitação desejada."]:  # se for string, é um erro
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S[0])  # lança a string como erro

            espessura__solda = espessura_solda(M,V,T,solda,perfil,espessura_placa,filete_duplo,materials.gamma)


            C = criterio_cisalhamento_chapa(chapa,s_p_v,espessura_placa,ver_parafuso,S[1],aco,gamma)

            if C[0] == 0:
                raise ValueError(C[1])

            # propriedade com os dados do resultado para o desenho
            self.dados_resultado = [perfil,S[1],S[4],S[3],N_parafusos,espessura_placa,espessura_solda]

            layout, resultado = self.exposicao_resultado(diam_pol, N_parafusos, altura_chapa, largura_chapa, espessura_placa, espessura__solda)
            registrar_marcha("\n Resultado Encontrado! Abra o resultado do dimensionamento")
            self.adicionar_botoes_resultado(layout, resultado)
            resultado.setMinimumWidth(400)
            resultado.show()
            self.resultado_window = resultado

        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Erro no cálculo")
            msg.setText(f"Ocorreu um erro:\n{e}")
            msg.setInformativeText("Deseja visualizar a marcha de cálculo?")
            
            btn_ver_marcha = msg.addButton("Abrir Marcha", QMessageBox.ActionRole)
            btn_fechar = msg.addButton(QMessageBox.Close)

            msg.exec()

            if msg.clickedButton() == btn_ver_marcha:
                self.salvar_marcha()


