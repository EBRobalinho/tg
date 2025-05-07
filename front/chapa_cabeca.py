from PySide6.QtWidgets import *
from front.base_form import ParametrosLigacaoBase
import materials
from design_functions import *
from v_p_chapa_cabeca.v_p_chapa_cabeca import * 
from draw_autocad.draw_autocad_figures import *
from materials import * 

import math
import time
#Importar bibliotecas do sistemas
import win32com.client

from pyautocad import Autocad, APoint 


class ParametrosChapaCabeca(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:
            M = self.ler_momento_tonelada_metro(self.input_momento)
            V = self.ler_forca_tonelada(self.input_cortante)
            T = self.ler_forca_tonelada(self.input_tracao)

            # Verificação: todos os esforços são zero
            if all(x == 0 for x in [M, V, T]):
                raise ValueError("Nenhum esforço foi informado. A ligação não foi solicitada.")

            perfil = getattr(materials, self.combo_perfil.currentText())
            aco_perfil = getattr(materials, self.combo_aco_perfil.currentText())
            perfil.inercias()
            perfil.material(aco_perfil)
            aco = getattr(materials, self.combo_aco.currentText())
            solda = getattr(materials, self.combo_solda.currentText())
            parafuso = getattr(materials, self.combo_parafuso.currentText())
            rosca = int(self.input_rosca.text())
            planos = int(self.input_planos.text())
            filete_duplo = True if self.combo_filete_duplo.currentText() == "Dupla" else False
            chapa_rigida = 1 if self.combo_chapa_rigida.currentText() == "Sim" else 0
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=planos)
            S = dim_chapa_parafuso(M, V, T, perfil, materials.disposicoes_gerdau_chapa_cabeca, parafuso, materials.gamma)
            
            if isinstance(S[0], str):  # se for string, é um erro
                raise ValueError(S[0])  # lança a string como erro

            diam_pol = S[1].diametro_pol
            N_parafusos = len(S[4])
            altura_chapa = S[3].df["y (mm)"].max()
            largura_chapa = S[3].df["x (mm)"].max()
            
            chapa = S[3]
            ver_parafuso = S[4]

            r_parafuso_total = resistencia_total(S[1],materials.gamma)

            s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, S[1] , S[0])
            s_p_t = solicitante_parafuso_tração(T,N_parafusos)


            exp = exp_placa(aco,chapa,chapa_rigida,ver_parafuso,S[1].diametro_mm,r_parafuso_total, (s_p_m + s_p_t), materials.gamma)
            esp =espessura_solda(M,V,T,solda,perfil,exp,filete_duplo,materials.gamma)

            self.dados_resultado = [perfil,S[1],S[4],S[3],N_parafusos,exp,esp]

            resultado = QWidget()
            resultado.setWindowTitle("Resultado - Chapa de Cabeça")
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
            layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos}"))
            layout.addWidget(QLabel(f"Altura da Chapa: {altura_chapa:.2f} mm"))
            layout.addWidget(QLabel(f"Largura da Chapa: {largura_chapa:.2f} mm"))
            layout.addWidget(QLabel(f"Espessura da Chapa: {exp:.2f} mm / {(exp / 25.4):.3f} pol"))
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

        self.input_momento = QLineEdit()
        self.form_layout.addRow("Momento (tf.m):", self.input_momento)

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

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

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



    def desenhar_no_autocad(self, dados_resultado):

        # Cria instância do AutoCAD
        acad = win32com.client.Dispatch("AutoCAD.Application")
        acad.Visible = True  # Garante que a janela fique visível

        # Aguarda 2 segundos
        time.sleep(2)

        acad = Autocad(create_if_not_exists=True)
        acad.prompt("Hello, Autocad from Python\n")
        print(acad.doc.Name)

        limpar_desenho(acad)

        [perfil_escolhido,parafuso,ver_parafuso,chapa,N_parafusos,exp,esp] = dados_resultado 

        pontos_hexagono = gerar_pontos_hexagono(parafuso.diametro_mm)

        # Chamando a função para desenhar a chapa 3D
        objetos_chapa = criar_chapa_3d(acad, chapa.df, exp)

        objetos_parafusos=[]
        for i in range(ver_parafuso.shape[0]):
            x_centro = ver_parafuso.iat[i, 1]
            y_centro = ver_parafuso.iat[i, 2]

            # Adicionar circunferência no ponto
            obj = acad.model.AddCircle(APoint(x_centro, y_centro,exp), parafuso.diametro_mm / 2)
            objetos_parafusos.append(obj)
            obj = acad.model.AddCircle(APoint(x_centro, y_centro,0), parafuso.diametro_mm / 2)
            objetos_parafusos.append(obj)
            # Transladar hexágono para o ponto atual
            hexagono_transladado = transladar_pontos(pontos_hexagono, x_centro, y_centro, exp)

            for j in range(len(hexagono_transladado) - 1):
                p1 = APoint(*hexagono_transladado[j])
                p2 = APoint(*hexagono_transladado[j + 1])
                obj = acad.model.AddLine(p1, p2)
                objetos_parafusos.append(obj)

        objetos_secao_perfil = desenhar_secao_perfil(acad, perfil_escolhido, (chapa.B / 2) - (perfil_escolhido.b_f / 2), posicao_y=20, altura_z=exp)
    

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

        escrever_descricao(acad,0,0,max(chapa.df["y (mm)"])+10 ,"Chapa","",perfil_escolhido.nome,esp)
