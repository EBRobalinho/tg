from PySide6.QtWidgets import QComboBox, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel
from front.domain.ligacao_flexivel import Ligacao_Flexivel
from back.logs import registrar_marcha
from back.materials_constants import DIMENSOES_AÇO, DIMENSOES_SOLDA, DIMENSOES_PARAFUSO, gamma
from back.conversions import mm_para_polegada
from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.solda import Solda
from back.chapas_design import dim_chapa_extremidade
from back.draw_figures import desenhar_chapa_generica


class Chapa_Extremidade(Ligacao_Flexivel):
    
    def __init__(self,titulo="Chapa de Extremidade"):
        super().__init__()

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
        dados_comuns = super().receber_input()
        chapa_rigida = 1 if self.combo_chapa_rigida.currentText() == "Sim" else 0
        return [*dados_comuns, chapa_rigida]
    
    def executar_calculo(self):
        try:
            # Desempacota os dados recebidos
            [V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, nome_solda, 
            dimensoes_solda, chapa_rigida] = self.receber_input()  

            aco_perfil = Aço(nome_aco_perfil,**dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,**dimensoes_perfil,aco=aco_perfil)
            perfil.inercias()

            aco      = Aço(nome_aco,**dimensoes_aco)

            solda    = Solda(nome_solda,**dimensoes_solda)

            parafuso = Parafuso(nome_parafuso,**dimensoes_parafuso)
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            S = dim_chapa_extremidade(V,T, perfil, parafuso, aco,chapa_rigida,solda,gamma)

            if isinstance(S, str):  # se for string, é um erro
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S[0])  # lança a string como erro
            if not isinstance(S, tuple):  # se não for uma tupla, é um erro
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError("Erro no dimensionamento da chapa de cabeça. Verifique os dados de entrada.")  # lança a string como erro
            else:
            # S é uma lista com os seguintes elementos:
                (chapa,exp,parafuso,ver_parafuso,solda,esp_solda) = S
                registrar_marcha("\n Resultado encontrado com sucesso!\n")
                # Variáveis utilizadas
                diam_pol = mm_para_polegada(parafuso.d)
                N_parafusos = len(ver_parafuso)
                altura_chapa = chapa.df["y (mm)"].max()
                largura_chapa = chapa.df["x (mm)"].max()

            #propriedade com os dados do resultado para o desenho
            self.dados_resultado = [perfil,parafuso,ver_parafuso,chapa,exp]

            # Exibe os resultados
            layout, resultado = self.exposicao_resultado(diam_pol, N_parafusos, altura_chapa, largura_chapa, exp, esp_solda)

            self.adicionar_botoes_resultado(layout, resultado)
            resultado.setMinimumWidth(400)
            resultado.show()
            self.resultado_window = resultado


        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Erro no cálculo")
            msg.setText(f"Ocorreu um erro:\n{e}")
            msg.setInformativeText("Deseja visualizar a marcha de cálculo?")
            
            btn_ver_marcha = msg.addButton("Abrir Marcha", QMessageBox.ButtonRole.AcceptRole)
            #btn_fechar = msg.addButton(QMessageBox.Close)

            msg.exec()

            if msg.clickedButton() == btn_ver_marcha:
                self.salvar_marcha()

    def exposicao_resultado(self,diam_pol:str,N_parafusos:int,altura_chapa:float,largura_chapa:float,esp_chapa_mm:float,esp:float):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Chapa de Extremidade")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
        layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos}"))
        layout.addWidget(QLabel(f"Altura da Chapa: {altura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Largura da Chapa: {largura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura da Chapa: {esp_chapa_mm:.2f} mm / {esp_chapa_mm/ 25.4:.3f} pol"))
        layout.addWidget(QLabel(f"Espessura do Filete de Solda: {esp:.2f} mm"))
        self.obs = "A solda será colocada em todo contorno da viga, com a chapa, inclusive na mesa da viga, sendo essa nas faces superior e inferior da chapa."
        resultado.setLayout(layout)
        return layout, resultado
    
    def desenhar_no_autocad(self, dados_resultado):
        desenhar_chapa_generica(dados_resultado,"extremidade")
    

