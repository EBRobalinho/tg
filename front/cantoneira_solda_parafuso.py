from PySide6.QtWidgets import *
from pyautocad import Autocad, APoint 
from v_p_cantoneira_flex.v_p_cantoneira_flex_solda_parafuso import dim_cant_parafuso_solda
from draw_autocad.draw_autocad_figures import *
from front.base_form import ParametrosLigacaoBase, iniciar_autocad

import materials
import math
import time
#Importar bibliotecas do sistemas
import win32com.client

class ParametrosCantoneiraSoldaParafuso(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:
            # Lê os valores dos esforços
            V = self.ler_forca_tonelada(self.input_cortante)
            T = self.ler_forca_tonelada(self.input_tracao)

            if V == 0 and T == 0:
                raise ValueError("Nenhum esforço foi informado. A ligação não foi solicitada.")
                
            #Dados que o usuário escolhe
            perfil = getattr(materials, self.combo_perfil.currentText())
            aco_cantoneira = getattr(materials, self.combo_aco_cantoneira.currentText())
            aco_viga = getattr(materials, self.combo_aco_viga.currentText())
            perfil.inercias()
            perfil.material(aco_viga) 
            material_parafuso = getattr(materials, self.combo_parafuso.currentText())
            parafuso = getattr(materials, self.combo_parafuso.currentText())
            rosca = int(self.input_rosca.text())
            planos = int(self.input_planos.text())
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=planos)
            N_parafusos = int(self.combo_qtd_parafusos.currentText())
            solda = getattr(materials, self.combo_solda.currentText())
            tipo_solda = True if self.combo_filete_duplo.currentText() == "Dupla" else False

            #Função que faz o dimensionamento
            S = dim_cant_parafuso_solda(T,V,materials.cantoneiras_dict,N_parafusos,material_parafuso,aco_cantoneira,perfil,solda,tipo_solda,materials.gamma)
            if isinstance(S[0], str):  # se for string, é um erro
                raise ValueError(S[0])  # lança a string como erro

            #Variáveis utilizadas
            nome_cantoneira = S[0].nome
            diam_pol = S[2].diametro_pol
            qtd_total_parafusos = 2 * len(S[0].disp_parafusos)
            comprimento = max(S[0].disp_vertices_chapa['z (mm)'])
            espessura_solda = S[1]

            #propriedade com os dados do resultado para o desenho
            self.dados_resultado = [perfil,parafuso,S[0]]

            #Exposição dos resultados
            layout, resultado = self.exposicao_resultado(nome_cantoneira, diam_pol,qtd_total_parafusos,comprimento,espessura_solda)
            self.adicionar_botoes_resultado(layout, resultado)
            resultado.setMinimumWidth(400)
            resultado.show()
            self.resultado_window = resultado

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no cálculo: {e}")

    def __init__(self, titulo):
        super().__init__(titulo)

        # Campos principais
        self.combo_perfil = QComboBox()
        self.combo_perfil.addItems([k for k in dir(materials) if k.startswith("W_")])
        self.form_layout.addRow("Perfil:", self.combo_perfil)

        self.combo_aco_viga = QComboBox()
        self.combo_aco_viga.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço do Perfil:", self.combo_aco_viga)

        self.combo_aco_cantoneira = QComboBox()
        self.combo_aco_cantoneira.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço da Cantoneira:", self.combo_aco_cantoneira)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow("Força Cortante (tf):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (tf):", self.input_tracao)

        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Parafuso)])
        self.form_layout.addRow("Parafuso:", self.combo_parafuso)

        self.combo_qtd_parafusos = QComboBox()
        self.atualizar_opcoes_parafusos()
        self.combo_perfil.currentTextChanged.connect(self.atualizar_opcoes_parafusos)
        self.form_layout.addRow("Número de Parafusos:", self.combo_qtd_parafusos)

        # Opções Avançadas
        self.input_rosca = QLineEdit("1")
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ? (1=sim, 0=não):", self.input_rosca)

        self.input_planos = QLineEdit("2")
        self.avancado_layout.addRow("Quantidade de planos de Corte no Parafuso:", self.input_planos)

        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Solda)])
        self.form_layout.addRow("Solda:", self.combo_solda)

        # Opções Avançadas
        self.combo_filete_duplo = QComboBox()
        self.combo_filete_duplo.addItems(["Simples", "Dupla"])
        self.avancado_layout.addRow("Solda Dupla:", self.combo_filete_duplo)
        self.combo_filete_duplo.setCurrentText("Dupla")  # define "Dupla" como padrão

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        for widget in self.findChildren(QComboBox):
            widget.setFixedWidth(150)
        for widget in self.findChildren(QLineEdit):
            widget.setFixedWidth(150)

    def exposicao_resultado(self,nome_cantoneira, diam_pol,qtd_total_parafusos,comprimento,espessura_solda):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Cantoneira Flexível (Parafuso)")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Cantoneira Selecionada (Catálogo Gerdau): {nome_cantoneira}"))
        layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
        layout.addWidget(QLabel(f"Quantidade Total de Parafusos na ligação: {qtd_total_parafusos}"))
        layout.addWidget(QLabel(f"Comprimento da Cantoneira: {comprimento:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura da Solda: {espessura_solda:.2f} mm"))
        self.obs = "A solda foi colocada em todo o contorno da cantoneira com a viga."
        #Adiciona o resultado no Layout
        resultado.setLayout(layout)
        return layout, resultado

    #Permite que o usuário escolha a quantidade de parafusos a depender do perfil da viga
    def atualizar_opcoes_parafusos(self):
        nome_perfil = self.combo_perfil.currentText()
        if not nome_perfil or not hasattr(materials, nome_perfil):
            return

        perfil = getattr(materials, nome_perfil)

        try:
            h_w = perfil.h_w  # altura útil

            # ⬇️ Aqui entra sua regra condicional
            if nome_perfil.startswith("W_150x"):
                margem = 2 * 25
                espacamento = 60
            else:
                margem = 2 * 30
                espacamento = 75

            n_p_min = 1
            n_p_max = max(int((h_w - margem) // espacamento), 2)

            self.combo_qtd_parafusos.clear()
            for n in range(n_p_min, n_p_max + 1):
                self.combo_qtd_parafusos.addItem(str(n))

            self.combo_qtd_parafusos.setCurrentIndex(0)

        except Exception as e:
            self.combo_qtd_parafusos.clear()
            self.combo_qtd_parafusos.addItem("1")

    def desenhar_no_autocad(self, dados_resultado):

        [perfil_escolhido,parafuso,cantoneira_escolhida] = dados_resultado

        ver_parafuso = cantoneira_escolhida.disp_parafusos
        ver_chapa = cantoneira_escolhida.disp_vertices_chapa

        acad = iniciar_autocad()

        limpar_desenho(acad)

        pontos_hexagono = gerar_pontos_hexagono(parafuso.diametro_mm)   

        objetos_s_cantoneira = desenhar_s_cantoneira(acad, cantoneira_escolhida, ver_chapa)

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
