from PySide6.QtWidgets import QComboBox, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel
from front.domain.ligacao_rigida import Ligacao_Rigida
from back.logs import registrar_marcha
from back.materials_constants import DIMENSOES_AÇO, DIMENSOES_SOLDA, DIMENSOES_PARAFUSO, gamma
from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.solda import Solda
from back.chapas_design import dim_chapa_cabeca
from back.draw_figures import desenhar_chapa_generica
from front.debug_utils import log_info, log_error, log_exception, debug_function

class Chapa_Cabeca(Ligacao_Rigida):
    
    def __init__(self,titulo="Chapa de Cabeça"):
        super().__init__()
        log_info(f"Iniciando {self.__class__.__name__} - {titulo}")

        self.combo_aco = QComboBox()
        self.combo_aco.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço da Chapa:", self.combo_aco)

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

        self.combo_chapa_rigida = QComboBox()
        self.combo_chapa_rigida.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("Chapa Rígida:", self.combo_chapa_rigida)

    def receber_input(self) -> list:
        log_info("Recebendo inputs da interface")
        try:
            dados_comuns = super().receber_input()
            chapa_rigida = 1 if self.combo_chapa_rigida.currentText() == "Sim" else 0
            log_info(f"Inputs processados: chapa_rigida={chapa_rigida}")
            return [*dados_comuns, chapa_rigida]
        except Exception as e:
            log_exception(e)
            raise ValueError(f"Erro ao processar entrada: {str(e)}")
    
    @debug_function
    def executar_calculo(self):
        try:
            # Desempacota os dados recebidos
            [M, V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, nome_solda, 
            dimensoes_solda, chapa_rigida] = self.receber_input()  

            log_info(f"Calculando para: M={M}, V={V}, T={T}, perfil={nome_perfil}, chapa_rigida={chapa_rigida}")

            aco_perfil = Aço(nome_aco_perfil,*dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,dimensoes_perfil,aco=aco_perfil)
            perfil.inercias()

            aco = Aço(nome_aco,*dimensoes_aco)
            solda = Solda(nome_solda,*dimensoes_solda)
            parafuso = Parafuso(nome_parafuso,*dimensoes_parafuso)
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            log_info("Iniciando dimensionamento da chapa de cabeça")
            S = dim_chapa_cabeca(M, V, T, perfil, aco, chapa_rigida,parafuso, solda, gamma)

            if isinstance(S, str):  # se for string, é um erro
                log_error(f"Dimensionamento falhou: {S}")
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S)  # lança a string como erro
                
            if not isinstance(S, tuple):  # se não for uma tupla, é um erro
                log_error("Resultado inválido retornado pelo dimensionamento")
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError("Erro no dimensionamento da chapa de cabeça. Verifique os dados de entrada.")
            else:
                # S é uma lista com os seguintes elementos:
                (k,parafuso,y_ln,chapa,ver_parafuso, esp_solda, exp) = S
                log_info("Dimensionamento concluído com sucesso")
                registrar_marcha("\n Resultado encontrado com sucesso!\n")
                
                # Variáveis utilizadas
                diam_pol = parafuso.d_pol
                N_parafusos = len(ver_parafuso)
                altura_chapa = chapa.df["y (mm)"].max()
                largura_chapa = chapa.df["x (mm)"].max()
                
                log_info(f"Resultado: {N_parafusos} parafusos, chapa {largura_chapa}x{altura_chapa}mm, esp={exp}mm")

            #propriedade com os dados do resultado para o desenho
            self.dados_resultado = [perfil, parafuso, ver_parafuso, chapa, exp]

            # Exibe os resultados
            layout, resultado = self.exposicao_resultado(diam_pol, N_parafusos, altura_chapa, largura_chapa, exp, esp_solda)

            self.adicionar_botoes_resultado(layout, resultado)
            resultado.setMinimumWidth(400)
            resultado.show()
            self.resultado_window = resultado

        except Exception as e:
            log_exception(e)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Erro no cálculo")
            msg.setText(f"Ocorreu um erro:\n{e}")
            msg.setInformativeText("Deseja visualizar a marcha de cálculo ou console de debug?")
            
            btn_ver_marcha = msg.addButton("Marcha de Cálculo", QMessageBox.ButtonRole.AcceptRole)
            btn_debug = msg.addButton("Console Debug", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Close)

            msg.exec()

            clicked = msg.clickedButton()
            if clicked == btn_ver_marcha:
                self.salvar_marcha()
            elif clicked == btn_debug:
                from front.debug_utils import show_debug_window
                show_debug_window()

    def exposicao_resultado(self, diam_pol:str, N_parafusos:int, altura_chapa:float, largura_chapa:float, esp_chapa_mm:float, esp:float):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Chapa de Cabeça")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
        layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos}"))
        layout.addWidget(QLabel(f"Altura da Chapa: {altura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Largura da Chapa: {largura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura da Chapa: {esp_chapa_mm:.2f} mm / {esp_chapa_mm/ 25.4:.3f} pol"))
        layout.addWidget(QLabel(f"Espessura do Filete de Solda: {esp:.2f} mm"))
        self.obs = "A solda será aplicada em todo contorno da viga, com a chapa, inclusive na alma, garantindo a fixação total da chapa na viga."
        resultado.setLayout(layout)
        return layout, resultado
    
    def desenhar_no_autocad(self, dados_resultado):
        try:
            log_info(f"Iniciando desenho no AutoCAD: {self.__class__.__name__}")
            desenhar_chapa_generica(dados_resultado, "cabeca")
            log_info("Desenho concluído com sucesso")
        except Exception as e:
            log_exception(e)
            raise