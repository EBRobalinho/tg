from PySide6.QtWidgets import QComboBox, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel
from front.domain.ligacao_flexivel import Ligacao_Flexivel
from back.logs import registrar_marcha
from back.materials_constants import DIMENSOES_AÇO, DIMENSOES_SOLDA, DIMENSOES_PARAFUSO, gamma
from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.solda import Solda
from back.cantoneiras_design import dim_cant_solda
from back.draw_figures import desenhar_cantoneira
from front.debug_utils import log_info, log_error, log_exception, debug_function

class Cantoneira_Solda(Ligacao_Flexivel):
    
    def __init__(self,titulo="Cantoneira - Solda"):
        super().__init__()
        log_info(f"Iniciando {self.__class__.__name__} - {titulo}")

        self.combo_aco = QComboBox()
        self.combo_aco.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço da Cantoneira:", self.combo_aco)
        
        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in DIMENSOES_SOLDA.keys()])
        self.form_layout.addRow("Solda:", self.combo_solda)

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        # Opções Avançadas para manter a consistência na interface
        self.input_rosca = QComboBox()
        self.input_rosca.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ?", self.input_rosca)
    
    @debug_function
    def executar_calculo(self):
        try:
            # Desempacota os dados recebidos
            [V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, nome_solda, 
            dimensoes_solda] = self.receber_input()  

            log_info(f"Calculando para: V={V}, T={T}, perfil={nome_perfil}")

            aco_perfil = Aço(nome_aco_perfil,*dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,dimensoes_perfil,aco=aco_perfil)
            perfil.inercias()

            aco = Aço(nome_aco,*dimensoes_aco)
            solda = Solda(nome_solda,*dimensoes_solda)
            parafuso = Parafuso(nome_parafuso,*dimensoes_parafuso)  # Necessário por como é implementado dim_cant_solda
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            log_info("Iniciando dimensionamento da cantoneira soldada")
            S = dim_cant_solda(T, V, aco, perfil, solda, gamma, parafuso)

            if isinstance(S, list) and all(isinstance(x, str) for x in S):
                log_error(f"Dimensionamento falhou: {S[0]}")
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S[0])
            elif isinstance(S, tuple) and len(S) == 3:
                cantoneira, espessura_solda, _ = S
                log_info("Dimensionamento concluído com sucesso")
                
                registrar_marcha("\n Resultado encontrado com sucesso!\n")
                
                # Variáveis utilizadas
                nome_cantoneira = cantoneira.nome
                comprimento_cantoneira = cantoneira.comprimento  # em mm
                
                log_info(f"Resultado: cantoneira {nome_cantoneira}, comprimento={comprimento_cantoneira}mm, espessura solda={espessura_solda}mm")

                #propriedade com os dados do resultado para o desenho
                self.dados_resultado = [perfil, cantoneira, espessura_solda]

                # Exibe os resultados
                layout, resultado = self.exposicao_resultado(nome_cantoneira, comprimento_cantoneira, espessura_solda)
                self.adicionar_botoes_resultado(layout, resultado)
                resultado.setMinimumWidth(400)
                resultado.show()
                self.resultado_window = resultado
            else:
                log_error("Formato de resultado inesperado")
                raise ValueError("Formato de resultado inesperado")

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

    def exposicao_resultado(self, nome_cantoneira:str, comprimento:float, espessura_solda:int):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Cantoneira Soldada")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Perfil da Cantoneira: {nome_cantoneira}"))
        layout.addWidget(QLabel(f"Comprimento da Cantoneira: {comprimento:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura do Filete de Solda: {espessura_solda} mm"))
        self.obs = "A cantoneira será soldada na alma da viga e na mesa do pilar"
        resultado.setLayout(layout)
        return layout, resultado
    
    def desenhar_no_autocad(self, dados_resultado):
        try:
            log_info(f"Iniciando desenho no AutoCAD: {self.__class__.__name__}")
            desenhar_cantoneira(dados_resultado,"solda")
            log_info("Desenho concluído com sucesso")
        except Exception as e:
            log_exception(e)
            raise