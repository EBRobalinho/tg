from PySide6.QtWidgets import QComboBox, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel
from front.domain.ligacao_flexivel import Ligacao_Flexivel
from back.logs import registrar_marcha
from back.materials_constants import DIMENSOES_PARAFUSO
from back.conversions import mm_para_polegada
from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.cantoneiras_design import dim_cant_parafuso


class Cantoneira_Parafuso(Ligacao_Flexivel):
    
    def __init__(self,titulo="Cantoneira duplamente parafusada"):
        super().__init__()

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
        dados_comuns = super().receber_input()
        N_parafusos = int(self.combo_qtd_parafusos.currentText())

        return [*dados_comuns, N_parafusos]

    def executar_calculo(self):
        try:
            [V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil, nome_aco,
             dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, N_parafusos] = self.receber_input()

            aco_perfil = Aço(nome_aco_perfil,**dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,**dimensoes_perfil,aco=aco_perfil)
            perfil.inercias()
            
            aco      = Aço(nome_aco,**dimensoes_aco)         

            parafuso = Parafuso(nome_parafuso,**dimensoes_parafuso)
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)

            S = dim_cant_parafuso(T,V,aco,perfil,parafuso,N_parafusos,rosca)

            if isinstance(S, str):  # se for string, é um erro
                registrar_marcha("\nA ligação não aguenta a solicitação desejada.\n")
                raise ValueError(S)  # lança a string como erro
            if isinstance(S, tuple):
                registrar_marcha("\nResultado encontrado com sucesso!\n")
                # Se chegou aqui, S é uma lista com os resultados do dimensionamento    
                (cantoneira,parafuso) = S

                #Variáveis utilizadas
                nome_cantoneira = cantoneira.nome
                diam_pol = mm_para_polegada(parafuso.d)
                qtd_total_parafusos = 4 * len(cantoneira.disp_parafusos)
                comprimento = max(cantoneira.disp_vertices_chapa['z (mm)'])

                #propriedade com os dados do resultado para o desenho
                self.dados_resultado = [perfil,parafuso,cantoneira]

                #Exposição dos resultados
                layout, resultado = self.exposicao_resultado(nome_cantoneira, diam_pol,qtd_total_parafusos,comprimento)

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

    def exposicao_resultado(self,nome_cantoneira: str, diam_pol: str,qtd_total_parafusos: int,comprimento: float):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Cantoneira Flexível (Parafuso)")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Cantoneira Selecionada (Catálogo Gerdau): {nome_cantoneira}"))
        layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
        layout.addWidget(QLabel(f"Quantidade Total de Parafusos na ligação: {qtd_total_parafusos}"))
        layout.addWidget(QLabel(f"Comprimento da Cantoneira: {comprimento:.2f} mm"))
        self.obs =""
        #Adiciona o resultado no Layout
        resultado.setLayout(layout)
        return layout, resultado

    def desenhar_no_autocad(self, dados_resultado):

        [perfil_escolhido,parafuso,cantoneira_escolhida] = dados_resultado

        ver_parafuso = cantoneira_escolhida.disp_parafusos
        ver_chapa = cantoneira_escolhida.disp_vertices_chapa

        acad = iniciar_autocad()

        limpar_desenho(acad)

        pontos_hexagono = gerar_pontos_hexagono(parafuso.diametro_mm)   

        objetos_s_cantoneira = desenhar_s_cantoneira(acad, cantoneira_escolhida, ver_chapa)

        #### Desenhar os parafusos do plano XZ
        objetos_p1_cantoneira = []   
        # === Parafusos e hexágonos ===
        for i in range(ver_parafuso.shape[0]):
            x_centro = ver_parafuso.iat[i, 1]
            y_centro = ver_parafuso.iat[i, 2]
            z_centro = ver_parafuso.iat[i, 3]

            # Face do hexágono em X
            obj1 = acad.model.AddCircle(APoint(x_centro, z_centro, -y_centro), parafuso.diametro_mm / 2)
            obj1.Rotate3D(APoint(0, 0, 0), APoint(1, 0, 0), math.radians(90))
            objetos_p1_cantoneira.append(obj1)

            # Face traseira em X
            obj2 = acad.model.AddCircle(APoint(x_centro, z_centro, 0), parafuso.diametro_mm / 2)
            obj2.Rotate3D(APoint(0, 0, 0), APoint(1, 0, 0), math.radians(90))
            objetos_p1_cantoneira.append(obj2)

            # Hexágono desenhado com linhas
            hexagono_transladado = transladar_pontos(pontos_hexagono, x_centro, z_centro, y_centro)

            for j in range(len(hexagono_transladado) - 1):
                p1 = APoint(hexagono_transladado[j][0], hexagono_transladado[j][1], -cantoneira_escolhida.t_mm)
                p2 = APoint(hexagono_transladado[j + 1][0], hexagono_transladado[j + 1][1], -cantoneira_escolhida.t_mm)

                linha = acad.model.AddLine(p1, p2)
                linha.Rotate3D(APoint(0, 0, 0), APoint(1, 0, 0), math.radians(90))
                objetos_p1_cantoneira.append(linha)

        #### Desenhar os parafusos do plano XY
        objetos_p2_cantoneira = []
        # === Parafusos e hexágonos ===
        for i in range(ver_parafuso.shape[0]):
            x_centro = ver_parafuso.iat[i, 2]
            y_centro = ver_parafuso.iat[i, 1]   #Muda a tabela considerando agora os parafusos do outro plano
            z_centro = ver_parafuso.iat[i, 3]

            # Face do hexágono em X
            obj1 = acad.model.AddCircle(APoint(z_centro, y_centro, -x_centro), parafuso.diametro_mm / 2)
            obj1.Rotate3D(APoint(0, 0, 0), APoint(0, 1, 0), math.radians(-90))
            objetos_p2_cantoneira.append(obj1)

            # Face traseira em X
            obj2 = acad.model.AddCircle(APoint(z_centro, y_centro, 0), parafuso.diametro_mm / 2)
            obj2.Rotate3D(APoint(0, 0, 0), APoint(0, 1, 0), math.radians(-90))
            objetos_p2_cantoneira.append(obj2)

            # Hexágono desenhado com linhas
            hexagono_transladado = transladar_pontos(pontos_hexagono, z_centro, y_centro, -y_centro)

            for j in range(len(hexagono_transladado) - 1):
                p1 = APoint(hexagono_transladado[j][0], hexagono_transladado[j][1], -cantoneira_escolhida.t_mm)
                p2 = APoint(hexagono_transladado[j + 1][0], hexagono_transladado[j + 1][1], -cantoneira_escolhida.t_mm)

                linha = acad.model.AddLine(p1, p2)
                linha.Rotate3D(APoint(0, 0, 0), APoint(0, 1, 0), math.radians(-90))
                objetos_p2_cantoneira.append(linha)

        #### Desenhar seção das cantoneiras

        # Vetor de translação (exemplo: mover 100 mm no eixo X)
        dx, dy, dz = 10, perfil_escolhido.t_w/2, (perfil_escolhido.h-cantoneira_escolhida.comprimento)/2  # ajuste aqui conforme necessário

        # Aponta o vetor de deslocamento
        vetor = APoint(dx, dy, dz)

        # Aplica a translação a todos os objetos na lista
        for obj in objetos_s_cantoneira:
            obj.Move(APoint(0,0,0),vetor) 
            obj.Mirror(APoint(1, 0, 0), APoint(0, 0, 0))
        for obj in objetos_p2_cantoneira:
            obj.Move(APoint(0,0,0),vetor) 
            obj.Mirror(APoint(1, 0, 0), APoint(0, 0, 0))
        for obj in objetos_p1_cantoneira:
            obj.Move(APoint(0,0,0),vetor) 
            obj.Mirror(APoint(1, 0, 0), APoint(0, 0, 0))

        #### Desenhar seção do perfil

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
