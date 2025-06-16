from PySide6.QtWidgets import QComboBox, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel
from front.domain.Ligacao_Flexivel import Ligacao_Flexivel
from back.logs import registrar_marcha
from back.materials_constants import  DIMENSOES_SOLDA, DIMENSOES_PARAFUSO,gamma
from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.solda import Solda
from back.cantoneiras_design import dim_cant_solda


class Cantoneira_Parafuso(Ligacao_Flexivel):
    
    def __init__(self,titulo="Cantoneira duplamente parafusada"):
        super().__init__()
        
        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in DIMENSOES_SOLDA.keys()])
        self.form_layout.addRow("Solda:", self.combo_solda)

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        # Opções Avançadas

        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in DIMENSOES_PARAFUSO.keys()])
        self.avancado_layout.addRow("Parafuso:", self.combo_parafuso)

        self.input_rosca = QComboBox()
        self.input_rosca.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ?", self.input_rosca)

    def receber_input(self) -> list:
        dados_comuns = super().receber_input()
        nome_solda = self.combo_solda.currentText()
        dimensoes_solda    = DIMENSOES_SOLDA[nome_solda]

        return [*dados_comuns, nome_solda, dimensoes_solda]

    def executar_calculo(self):
        try:
            [V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, nome_solda, dimensoes_solda] = self.receber_input()

            aco_perfil = Aço(nome_aco_perfil,*dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,*dimensoes_perfil,*aco_perfil)
            perfil.inercias()
            
            aco      = Aço(nome_aco,*dimensoes_aco)         
            
            solda    = Solda(nome_solda,*dimensoes_solda) 

            parafuso = Parafuso(nome_parafuso,*dimensoes_parafuso)
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            S = dim_cant_solda(T,V,aco,perfil,solda,gamma,parafuso)

            if isinstance(S, str):  # se for string, é um erro
                registrar_marcha("\nA ligação não aguenta a solicitação desejada.\n")
                raise ValueError(S)  # lança a string como erro
            if isinstance(S, tuple):
                registrar_marcha("\nResultado encontrado com sucesso!\n")
                # Se chegou aqui, S é uma lista com os resultados do dimensionamento    
                (cantoneira,espessura_solda,parafuso) = S

                # Variáveis utilizadas
                nome_cantoneira = S[0].nome
                comprimento = max(S[0].disp_vertices_chapa['z (mm)'])

                #propriedade com os dados do resultado para o desenho
                self.dados_resultado = [cantoneira,perfil,espessura_solda]

                #Exposição dos resultados
                layout, resultado = self.exposicao_resultado(nome_cantoneira, comprimento, espessura_solda)

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

    def exposicao_resultado(self, nome_cantoneira: str, comprimento: float, espessura_solda: int):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Cantoneira Flexível (Solda)")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Cantoneira Selecionada (Catálogo Gerdau): {nome_cantoneira}"))
        layout.addWidget(QLabel(f"Comprimento da Cantoneira : {comprimento:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura da Solda: {espessura_solda:.2f} mm"))
        self.obs = "A solda foi colocada em todo o contorno da cantoneira."
        resultado.setLayout(layout)
        return layout, resultado

    def desenhar_no_autocad(self, dados_resultado):

        acad = iniciar_autocad()

        limpar_desenho(acad)

        [cantoneira_escolhida,perfil_escolhido,espessura] = dados_resultado 
        ver_chapa = cantoneira_escolhida.disp_vertices_chapa
        objetos_s_cantoneira = desenhar_s_cantoneira(acad, cantoneira_escolhida, ver_chapa)

                # Vetor de translação (exemplo: mover 100 mm no eixo X)
        dx, dy, dz = 10, perfil_escolhido.t_w/2, (perfil_escolhido.h-cantoneira_escolhida.comprimento)/2  # ajuste aqui conforme necessário

        # Aponta o vetor de deslocamento
        vetor = APoint(dx, dy, dz)

        # Aplica a translação a todos os objetos na lista
        for obj in objetos_s_cantoneira:
            obj.Move(APoint(0,0,0),vetor) 
            obj.Mirror(APoint(1, 0, 0), APoint(0, 0, 0))

        objetos_secao_perfil = desenhar_secao_perfil(acad, perfil_escolhido, posicao_x=-perfil_escolhido.b_f/2, posicao_y=-perfil_escolhido.h/2, altura_z=0)

        # Rotacionar apenas a seção do perfil:
        for obj in objetos_secao_perfil:
            obj.Rotate3D(APoint(0, 0, 0), APoint(1,0, 0), math.radians(90))
            obj.Rotate3D(APoint(0, 0, 0), APoint(0,0, 1), math.radians(90))

        # Vetor de translação (exemplo: mover 100 mm no eixo X)
        dx, dy, dz = 0,0,perfil_escolhido.h/2  # ajuste aqui conforme necessário

        # Aponta o vetor de deslocamento
        vetor = APoint(dx, dy, dz)

        for obj in objetos_secao_perfil:
            obj.Move(APoint(0,0,0),vetor)     

        escrever_descricao(acad,0,0,perfil_escolhido.h + 10 ,"Cantoneira",cantoneira_escolhida.nome, perfil_escolhido.nome,espessura)

