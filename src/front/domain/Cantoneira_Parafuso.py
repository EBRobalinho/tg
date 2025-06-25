from PySide6.QtWidgets import QComboBox, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel
from front.domain.ligacao_flexivel import Ligacao_Flexivel
from back.logs import registrar_marcha
from back.materials_constants import gamma
from back.materials_loader import DIMENSOES_AÇO, DIMENSOES_PARAFUSO
from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.cantoneira import Cantoneira
from back.cantoneiras_design import dim_cant_parafuso
from back.draw_figures import desenhar_cantoneira
from back.draw_ezdxf import desenhar_cantoneira_dxf
from front.debug_utils import log_info, log_error, log_exception, debug_function
import back.draw_utils


class Cantoneira_Parafuso(Ligacao_Flexivel):
    
    def __init__(self,titulo="Cantoneira - Parafuso"):
        super().__init__()
        log_info(f"Iniciando {self.__class__.__name__} - {titulo}")

        self.combo_aco = QComboBox()
        self.combo_aco.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço da Cantoneira:", self.combo_aco)

        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in DIMENSOES_PARAFUSO.keys()])
        self.form_layout.addRow("Parafuso:", self.combo_parafuso)

        self.combo_qtd_parafusos = QComboBox()
        self.atualizar_opcoes_parafusos()
        self.combo_perfil.currentTextChanged.connect(self.atualizar_opcoes_parafusos)
        self.form_layout.addRow("Número de Parafusos:", self.combo_qtd_parafusos)
        
        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        # Opções Avançadas
        self.input_rosca = QComboBox()
        self.input_rosca.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ?", self.input_rosca)

    def receber_input(self) -> list:
        log_info("Recebendo inputs da interface")
        try:
            dados_comuns = super().receber_input()
            n_parafusos = int(self.combo_qtd_parafusos.currentText())
            log_info(f"Inputs processados: n_parafusos={n_parafusos}")
            return [*dados_comuns, n_parafusos]
        except Exception as e:
            log_exception(e)
            raise ValueError(f"Erro ao processar entrada: {str(e)}")
    
    @debug_function
    def executar_calculo(self):
        try:
            # Desempacota os dados recebidos
            [V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, n_parafusos] = self.receber_input()  

            log_info(f"Calculando para: V={V}, T={T}, perfil={nome_perfil}, n_parafusos={n_parafusos}")

            aco_perfil = Aço(nome_aco_perfil,*dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,dimensoes_perfil,aco=aco_perfil)
            perfil.inercias()

            aco = Aço(nome_aco,*dimensoes_aco)
            parafuso = Parafuso(nome_parafuso,*dimensoes_parafuso)
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            log_info("Iniciando dimensionamento da cantoneira parafusada")
            S = dim_cant_parafuso(T, V, aco, perfil, parafuso, n_parafusos, gamma)

            if isinstance(S, list) and all(isinstance(x, str) for x in S):  # se for lista de strings, é um erro
                log_error(f"Dimensionamento falhou: {S[0]}")
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S[0])  # lança a string como erro
            else:
                resultado = S
                # Inicializa as variáveis para evitar "unbound"
                cantoneira = None
                parafuso = None
                comprimento: int = 0
                nome_cantoneira = "N/A"
                diam_pol = "N/A"
                n_parafusos = int(self.combo_qtd_parafusos.currentText())
                

                cantoneira, parafuso = resultado
                log_info("Dimensionamento concluído com sucesso")
                
                registrar_marcha("\n Resultado encontrado com sucesso!\n")
                
                # Variáveis utilizadas
                if isinstance(cantoneira, Cantoneira):
                    nome_cantoneira = cantoneira.nome
                    n_parafusos = cantoneira.disp_parafusos.shape[0]
                    comprimento = cantoneira.comprimento
                else:
                    nome_cantoneira = str(cantoneira)
                    
                if isinstance(parafuso, Parafuso):
                    diam_pol = parafuso.d_pol
                else:
                    diam_pol = str(parafuso)
                
                log_info(f"Resultado: {n_parafusos} parafusos, cantoneira {nome_cantoneira}, diâmetro={diam_pol}")

                # Propriedade com os dados do resultado para o desenho
                self.dados_resultado = [perfil, parafuso, cantoneira]

                # Exibe os resultados
                layout, resultado = self.exposicao_resultado(nome_cantoneira, diam_pol, n_parafusos,comprimento)
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

    def exposicao_resultado(self, nome_cantoneira:str, diam_pol:str, N_parafusos:int,comprimento: int):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Cantoneira Parafusada")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Perfil da Cantoneira: {nome_cantoneira}"))
        layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
        layout.addWidget(QLabel(f"Comprimento da Cantoneira: {comprimento:.2f} mm"))
        layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos} por aba"))
        self.obs = "As cantoneiras serão ligadas em ambos os lados da alma da viga"
        resultado.setLayout(layout)
        return layout, resultado
    
    def desenhar_no_autocad(self, dados_resultado):
        if back.draw_utils.DXF:
            desenhar_cantoneira_dxf(dados_resultado,"parafuso")
        else:
            desenhar_cantoneira(dados_resultado,"parafuso")
