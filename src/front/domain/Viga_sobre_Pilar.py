from PySide6.QtWidgets import QComboBox, QLineEdit, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel
from front.domain.ligacao_rigida import Ligacao_Rigida
from back.domain.perfil import Perfil
from PySide6.QtGui import QIcon
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.solda import Solda
from back.materials_constants import gamma
from back.draw_figures import desenhar_viga_sobre_pilar
from back.draw_ezdxf import desenhar_viga_sobre_pilar_dxf
from back.logs import registrar_marcha
from back.chapas_design import dim_chapa_viga_pilar
from front.debug_utils import log_info, log_error, log_exception, debug_function
import back.draw_utils


class Viga_sobre_Pilar(Ligacao_Rigida):
    def __init__(self,titulo="Viga Sobre Pilar"):
        super().__init__()
        self.setWindowTitle(titulo)
        log_info(f"Iniciando {self.__class__.__name__} - {titulo}")

        # Componentes específicos desta classe
        self.combo_enrijecedor = QComboBox()
        self.combo_enrijecedor.addItems(["Sim", "Não"])
        self.form_layout.addRow("Enrijecedor (nas mesas do Pilar):", self.combo_enrijecedor)

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        # Opções Avançadas
        self.input_rosca = QComboBox()
        self.input_rosca.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ?", self.input_rosca)

        self.input_altura_enrijecedor = QLineEdit()
        self.input_altura_enrijecedor.setText("100")
        self.avancado_layout.addRow("Altura do Enrijecedor (mm):", self.input_altura_enrijecedor)

    def receber_input(self):
        log_info("Recebendo inputs da interface")
        try:
            dados_comuns = super().receber_input()

            enrijecedor = 1 if self.combo_enrijecedor.currentText() == "Sim" else 0
            altura = int(self.input_altura_enrijecedor.text())
            
            log_info(f"Inputs processados: enrijecedor={enrijecedor}, altura={altura}")
            return [*dados_comuns, enrijecedor, altura]
        except Exception as e:
            log_exception(e)
            raise ValueError(f"Erro ao processar entrada: {str(e)}")

    @debug_function
    def executar_calculo(self):
        try:
            # Desempacota os dados recebidos
            [M, V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, nome_solda, 
            dimensoes_solda, enrijecedor, altura] = self.receber_input()
            
            log_info(f"Calculando para: M={M}, V={V}, T={T}, perfil={nome_perfil}, enrijecedor={enrijecedor}")

            aco_perfil = Aço(nome_aco_perfil,*dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,dimensoes_perfil,aco=aco_perfil)
            perfil.inercias()

            aco = Aço(nome_aco,*dimensoes_aco)
            solda = Solda(nome_solda,*dimensoes_solda)
            parafuso = Parafuso(nome_parafuso,*dimensoes_parafuso)
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            log_info("Iniciando dimensionamento da chapa")
            S = dim_chapa_viga_pilar(M, V, T, aco, enrijecedor, altura, perfil, parafuso,solda, gamma)
            
            if isinstance(S, str):  # se for string, é um erro
                log_error(f"Dimensionamento falhou: {S}")
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S)  # lança a string como erro
                
            if isinstance(S, tuple):  # se não for uma tupla, é um erro
                log_info("Dimensionamento concluído com sucesso")
                (k, parafuso, chapa, ver_parafuso, espessura_chapa, espessura_enrijecedor, espessura__solda) = S
                N_parafusos = len(ver_parafuso)
                altura_chapa = chapa.df["y (mm)"].max()
                largura_chapa = chapa.df["x (mm)"].max()
                esp_chapa_mm = espessura_chapa
                esp_chapa_pol = esp_chapa_mm / 25.4
                diam_pol = parafuso.d_pol
                
                log_info(f"Resultado: {N_parafusos} parafusos, chapa {largura_chapa}x{altura_chapa}mm, esp={esp_chapa_mm}mm")

                # Calculo da espessura do enrijecedor e salva a propiedade com os dados do resultado para o desenho
                if enrijecedor == 1:
                    self.enrijecedor = 1
                    self.dados_resultado = [parafuso, perfil, chapa, ver_parafuso, N_parafusos, altura_chapa, largura_chapa, espessura_chapa, espessura_enrijecedor, espessura__solda]
                    log_info(f"Enrijecedor configurado: espessura={espessura_enrijecedor}mm")
                else:
                    self.dados_resultado = [parafuso, perfil, chapa, ver_parafuso, N_parafusos, altura_chapa, largura_chapa, espessura_chapa, espessura__solda]    
                    self.enrijecedor = 0
                    espessura_enrijecedor = 0
                    log_info("Sem enrijecedor")
                    
                # Exibe os resultados
                layout, resultado = self.exposicao_resultado(diam_pol, N_parafusos, altura_chapa, largura_chapa,
                                                             esp_chapa_pol, espessura__solda, altura, espessura_enrijecedor)
                registrar_marcha("\n Resultado Encontrado! Abra o resultado do dimensionamento")
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

    def exposicao_resultado(self,diam_pol: str,N_parafusos: int,altura_chapa: float,largura_chapa: 
                            float,esp_chapa_pol: float,esp: float,altura_do_Enrijecedor: float,esp_enrij_mm: float = 0):

        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Viga sobre Pilar")
        layout = QVBoxLayout()
        resultado.setWindowIcon(QIcon("assets/imagem_icon/icon_stcad.ico"))
        layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
        layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos}"))
        layout.addWidget(QLabel(f"Altura da Chapa: {altura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Largura da Chapa: {largura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura da Chapa: {esp_chapa_pol * 25.4:.2f} mm / {esp_chapa_pol:.3f} pol"))
        if self.enrijecedor ==1:
            layout.addWidget(QLabel(f"Espessura do Enrijecedor: {esp_enrij_mm:.2f} mm / {esp_enrij_mm/25.4:.3f} pol"))
            layout.addWidget(QLabel(f"Altura do Enrijecedor: {altura_do_Enrijecedor} mm"))
        layout.addWidget(QLabel(f"Espessura do Filete de Solda: {esp:.2f} mm"))
        self.obs = "Solda colocada na seção transversal do contorno do pilar com a chapa."

        resultado.setLayout(layout)
        return layout, resultado
    
    def desenhar_no_autocad(self, dados_resultado: list):
        if back.draw_utils.DXF:
            desenhar_viga_sobre_pilar_dxf(self.enrijecedor, dados_resultado)
        else:    
            desenhar_viga_sobre_pilar(self.enrijecedor, dados_resultado)