#Importar bibliotecas do sistemas
import sys
import os

# Caminho absoluto até a pasta src
sys.path.append(os.path.abspath("../src"))

#Importar libs do python
import pandas as pd 
import numpy as np 
import math
from pyautocad import Autocad, APoint 

#Importar libs do programa 
import design_functions
from v_p_chapa_extremidade.v_p_chapa_extremidade import *
from draw_autocad.draw_autocad_figures import *
from materials import * 
import time
#Importar bibliotecas do sistemas
import win32com.client

from PySide6.QtWidgets import *
from front.base_form import ParametrosLigacaoBase, iniciar_autocad
import materials

from v_p_chapa_extremidade.v_p_chapa_extremidade import dim_chapa_parafuso

class ParametrosChapaExtremidade(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:
            V = self.ler_forca_tonelada(self.input_cortante)
            T = self.ler_forca_tonelada(self.input_tracao)

            if V == 0 and T == 0:
                raise ValueError("Nenhum esforço foi informado. A ligação não foi solicitada.")

            perfil = getattr(materials, self.combo_perfil.currentText())
            perfil.inercias()
            aco = getattr(materials, self.combo_aco.currentText())
            aco_perfil = getattr(materials, self.combo_aco_perfil.currentText())
            perfil.material(aco_perfil)
            solda = getattr(materials, self.combo_solda.currentText())
            parafuso = getattr(materials, self.combo_parafuso.currentText())

            rosca = int(self.input_rosca.text())
            planos = int(self.input_planos.text())
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=planos)

            chapa_rigida = 1 if self.combo_chapa_rigida.currentText() == "Sim" else 0
            tipo_solda = 2 if self.combo_filete_duplo.currentText() == "Dupla" else 1

            S = dim_chapa_parafuso(V, T, perfil, parafuso, aco, chapa_rigida, solda, tipo_solda, materials.gamma)
            if isinstance(S[0], str):  # se for string, é um erro
                raise ValueError(S[0])  # lança a string como erro
                
            esp = S[-1]  # espessura do filete de solda

            diam_pol = S[2].diametro_pol
            N_parafusos = len(S[3])
            altura_chapa = S[0].df["y (mm)"].max()
            largura_chapa = S[0].df["x (mm)"].max()
            esp_chapa_mm = S[1]
            esp_chapa_pol = esp_chapa_mm / 25.4
            [chapa,exp,parafuso,ver_parafuso,solda,esp_solda]=S
            self.dados_resultado = [perfil,chapa,exp,parafuso,ver_parafuso,solda,esp_solda]

            resultado = QWidget()
            resultado.setWindowTitle("Resultado - Chapa de Extremidade")
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
            layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos}"))
            layout.addWidget(QLabel(f"Altura da Chapa: {altura_chapa:.2f} mm"))
            layout.addWidget(QLabel(f"Largura da Chapa: {largura_chapa:.2f} mm"))
            layout.addWidget(QLabel(f"Espessura da Chapa: {esp_chapa_mm:.2f} mm / {esp_chapa_pol:.3f} pol"))
            layout.addWidget(QLabel(f"Espessura do Filete de Solda: {esp:.2f} mm"))

            resultado.setLayout(layout)
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
                
        self.combo_aco_perfil = QComboBox()
        self.combo_aco_perfil.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço do Perfil:", self.combo_aco_perfil)

        self.combo_aco = QComboBox()
        self.combo_aco.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço da Chapa:", self.combo_aco)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow("Força Cortante (tf):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (tf):", self.input_tracao)

        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Parafuso)])
        self.form_layout.addRow("Parafuso:", self.combo_parafuso)

        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Solda)])
        self.form_layout.addRow("Solda:", self.combo_solda)
        
        # Opções Avançadas
        self.input_rosca = QLineEdit("1")
        self.avancado_layout.addRow("Rosca (1=sim, 0=não):", self.input_rosca)

        self.input_planos = QLineEdit("1")
        self.avancado_layout.addRow("Planos de Corte:", self.input_planos)

        self.combo_chapa_rigida = QComboBox()
        self.combo_chapa_rigida.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("Chapa Rígida:", self.combo_chapa_rigida)

        self.combo_filete_duplo = QComboBox()
        self.combo_filete_duplo.addItems(["Simples", "Dupla"])
        self.combo_filete_duplo.setCurrentText("Dupla")  # define "Dupla" como padrão
        self.avancado_layout.addRow("Solda Dupla:", self.combo_filete_duplo)

        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

    def desenhar_no_autocad(self, dados_resultado):

        [perfil_escolhido,chapa,exp,parafuso,ver_parafuso,solda,esp_solda] =  dados_resultado 

        acad = iniciar_autocad()

        limpar_desenho(acad)

        pontos_hexagono = gerar_pontos_hexagono(parafuso.diametro_mm)

        # Chamando a função para desenhar a chapa 3D
        objetos_chapa = criar_chapa_3d(acad, chapa.df, exp)

        objetos_secao_perfil = desenhar_secao_perfil(acad, perfil_escolhido, (chapa.B / 2) - (perfil_escolhido.b_f / 2), posicao_y=(-perfil_escolhido.t_f), altura_z=exp)

        # Criação dos objetos dos parafusos
        objetos_parafusos=[]

        #Rearranjar os parafusos para desenhar  
        rearranjar_parafusos(acad, ver_parafuso,objetos_parafusos, parafuso,pontos_hexagono, exp)

        # Rotacionar apenas a seção do perfil:
        for obj in objetos_parafusos:
            obj.Rotate3D(APoint(0, 0, 0), APoint(1,0, 0), math.radians(90))
            obj.Rotate3D(APoint(0, 0, 0), APoint(0,0, 1), math.radians(90))

        for obj in objetos_chapa:
            obj.Rotate3D(APoint(0, 0, 0), APoint(1,0, 0), math.radians(90))
            obj.Rotate3D(APoint(0, 0, 0), APoint(0,0, 1), math.radians(90))

        for obj in objetos_secao_perfil:
            obj.Rotate3D(APoint(0, 0, 0), APoint(1,0, 0), math.radians(90))
            obj.Rotate3D(APoint(0, 0, 0), APoint(0,0, 1), math.radians(90))

        # Vetor de translação (exemplo: mover 100 mm no eixo X)
        dx, dy, dz = 0,-perfil_escolhido.b_f/2,0  # ajuste aqui conforme necessário

        # Aponta o vetor de deslocamento
        vetor = APoint(dx, dy, dz)

        for obj in objetos_secao_perfil:
            obj.Move(APoint(0,0,0),vetor)


        for obj in objetos_chapa:
            obj.Move(APoint(0,0,0),vetor)


        for obj in objetos_parafusos:
            obj.Move(APoint(0,0,0),vetor)

        obs="(A solda será colocada em todo contorno da viga, com a chapa, inclusive na mesa da viga, sendo uma solda com face superior da chapa)"
        escrever_descricao(acad,-perfil_escolhido.b_f*0.75,0,perfil_escolhido.h-10 ,"Chapa","",perfil_escolhido.nome,math.ceil(esp_solda),obs)