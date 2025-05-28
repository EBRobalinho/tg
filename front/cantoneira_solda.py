from PySide6.QtWidgets import *
from front.base_form import ParametrosLigacaoBase, iniciar_autocad
import materials

#Importar libs do python
import pandas as pd 
import numpy as np 
import math
from pyautocad import Autocad, APoint 

#Importar libs do programa
from design_functions import *
from v_p_cantoneira_flex.v_p_cantoneira_flex_solda import dim_cant_solda
from draw_autocad.draw_autocad_figures import *
from materials import * 
#Importar bibliotecas do sistemas
import win32com.client


class ParametrosCantoneiraSolda(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:
            # Lê os valores dos esforços
            V = self.ler_forca_tonelada(self.input_cortante)
            T = self.ler_forca_tonelada(self.input_tracao)

            if V == 0 and T == 0:
                raise ValueError("Nenhum esforço foi informado. A ligação não foi solicitada.")

            # Dados que o usuário escolhe
            perfil = getattr(materials, self.combo_perfil.currentText())
            perfil.inercias()
            aco_perfil = getattr(materials, self.combo_aco_perfil.currentText())
            perfil.material(aco_perfil)
            aco_cantoneira = getattr(materials, self.combo_aco_cantoneira.currentText())
            solda = getattr(materials, self.combo_solda.currentText())
            parafuso = getattr(materials, self.combo_parafuso.currentText())
            rosca = 1 if self.input_rosca.currentText() == "Sim" else False

            planos=1 # Por causa da cantoneira-alma-cantoneira na viga ser 2 e no pilar ser 1, é a favor da segurança os dois sendo 1
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=planos) 

            # Função que faz o dimensionamento
            S = dim_cant_solda(T, V, materials.cantoneiras_dict, aco_cantoneira, perfil, solda, materials.gamma,parafuso)

            if isinstance(S[0], str):  # se for string, é um erro
                registrar_marcha("\nA ligação não aguenta a solicitação desejada.\n")
                raise ValueError(S[0])  # lança a string como erro


            # Variáveis utilizadas
            nome_cantoneira = S[0].nome
            comprimento = max(S[0].disp_vertices_chapa['z (mm)'])
            espessura_solda = S[1]

            #propriedade com os dados do resultado para o desenho
            self.dados_resultado = [S[0],perfil,espessura_solda]

            # Exibe os resultados
            layout, resultado = self.exposicao_resultado(nome_cantoneira, comprimento, espessura_solda)
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

    def exposicao_resultado(self, nome_cantoneira, comprimento, espessura_solda):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Cantoneira Flexível (Solda)")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Cantoneira Selecionada (Catálogo Gerdau): {nome_cantoneira}"))
        layout.addWidget(QLabel(f"Comprimento da Cantoneira : {comprimento:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura da Solda: {espessura_solda:.2f} mm"))
        self.obs = "A solda foi colocada em todo o contorno da cantoneira."
        resultado.setLayout(layout)
        return layout, resultado

    def __init__(self, titulo):
        super().__init__(titulo)

        # Campos principais
        self.combo_perfil = QComboBox()
        self.combo_perfil.addItems([k for k in dir(materials) if k.startswith("W_")])
        self.form_layout.addRow("Perfil:", self.combo_perfil)

        self.combo_aco_perfil = QComboBox()
        self.combo_aco_perfil.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço do Perfil:", self.combo_aco_perfil)

        self.combo_aco_cantoneira = QComboBox()
        self.combo_aco_cantoneira.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço da Cantoneira:", self.combo_aco_cantoneira)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow("Força Cortante (tf):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (tf):", self.input_tracao)

        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Solda)])
        self.form_layout.addRow("Solda:", self.combo_solda)

        # Opções Avançadas
        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Parafuso)])
        self.avancado_layout.addRow("Parafuso:", self.combo_parafuso)

        self.input_rosca = QComboBox()
        self.input_rosca.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ?", self.input_rosca)

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

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

