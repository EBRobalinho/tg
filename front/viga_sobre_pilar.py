from PySide6.QtWidgets import *
from pyautocad import Autocad, APoint 

from draw_autocad.draw_autocad_figures import *
from front.base_form import ParametrosLigacaoBase
from v_p_viga_sobre_pilar.v_p_viga_sobre_pilar import *
from v_p_chapa_cabeca.v_p_chapa_cabeca import parametro_b,espessura_solda

import materials
import math
import time
#Importar bibliotecas do sistemas
import win32com.client


class ParametrosVigaSobrePilar(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:

            M = self.ler_momento_tonelada_metro(self.input_momento)
            V = self.ler_forca_tonelada(self.input_cortante)
            T = self.ler_forca_tonelada(self.input_tracao)

            # Verificação: todos os esforços são zero
            if all(x == 0 for x in [M, V, T]):
                raise ValueError("Nenhum esforço foi informado. A ligação não foi solicitada.")

            perfil = getattr(materials, self.combo_perfil.currentText())
            perfil.inercias()

            aco_chapa = getattr(materials, self.combo_aco_chapa.currentText())
            aco_pilar = getattr(materials, self.combo_aco_pilar.currentText())
            perfil.material(aco_pilar)

            solda = getattr(materials, self.combo_solda.currentText())
            parafuso = getattr(materials, self.combo_parafuso.currentText())
            rosca = int(self.input_rosca.text())
            planos = int(self.input_planos.text())
            altura = int(self.input_altura_enrijecedor.text())
            filete_duplo = True if self.combo_filete_duplo.currentText() == "Dupla" else False
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=planos)
            enrijecedor = 1 if self.combo_enrijecedor.currentText() == "Sim" else 0

            S = dim_chapa_pilar(M, V, T, aco_chapa, enrijecedor,altura,perfil, parafuso, materials.gamma)

            if isinstance(S[0], str):  # se for string, é um erro
                raise ValueError(S[0])  # lança a string como erro

            diam_pol = S[1].diametro_pol
            N_parafusos = len(S[3])
            altura_chapa = S[2].df["y (mm)"].max()
            largura_chapa = S[2].df["x (mm)"].max()
            esp_chapa_mm = S[4]
            esp_chapa_pol = esp_chapa_mm / 25.4
            if enrijecedor ==1:
                esp_enrij_mm = S[5]

            esp = espessura_solda(M,T,V,solda,perfil,esp_chapa_mm,filete_duplo,materials.gamma)

            if enrijecedor ==1:
                self.dados_resultado = [S[1],perfil,S[2],S[3],N_parafusos,altura_chapa,largura_chapa,esp_chapa_mm,esp_enrij_mm,esp]
            else:
                self.dados_resultado = [S[1],perfil,S[2],S[3],N_parafusos,altura_chapa,largura_chapa,esp_chapa_mm,esp]     
                
                     
            resultado = QWidget()
            resultado.setWindowTitle("Resultado - Viga sobre Pilar")
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
            layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos}"))
            layout.addWidget(QLabel(f"Altura da Chapa: {altura_chapa:.2f} mm"))
            layout.addWidget(QLabel(f"Largura da Chapa: {largura_chapa:.2f} mm"))
            layout.addWidget(QLabel(f"Espessura da Chapa: {esp_chapa_pol * 25.4:.2f} mm / {esp_chapa_pol:.3f} pol"))
            if enrijecedor ==1:
                layout.addWidget(QLabel(f"Espessura do Enrijecedor: {esp_enrij_mm:.2f} mm / {esp_enrij_mm/25.4:.3f} pol"))
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
        
        self.combo_aco_pilar = QComboBox()
        self.combo_aco_pilar.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço do Pilar:", self.combo_aco_pilar)

        self.combo_aco_chapa = QComboBox()
        self.combo_aco_chapa.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço da Chapa:", self.combo_aco_chapa)

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

        self.combo_enrijecedor = QComboBox()
        self.combo_enrijecedor.addItems(["Sim", "Não"])
        self.form_layout.addRow("Enrijecedor (nas mesas do Pilar):", self.combo_enrijecedor)

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        # Opções Avançadas
        self.input_rosca = QLineEdit("1")
        self.avancado_layout.addRow("Rosca (1=sim, 0=não):", self.input_rosca)

        self.input_planos = QLineEdit("1")
        self.avancado_layout.addRow("Planos de Corte:", self.input_planos)

        self.combo_filete_duplo = QComboBox()
        self.combo_filete_duplo.addItems(["Simples", "Dupla"])
        self.combo_filete_duplo.setCurrentText("Dupla")  # define "Dupla" como padrão
        self.avancado_layout.addRow("Solda Dupla:", self.combo_filete_duplo)

        self.input_altura_enrijecedor = QLineEdit()
        self.input_altura_enrijecedor.setText("100")
        self.avancado_layout.addRow("Altura do Enrijecedor (mm):", self.input_altura_enrijecedor)   


    def desenhar_no_autocad(self, dados_resultado):

        enrijecedor = 1 if self.combo_enrijecedor.currentText() == "Sim" else 0

        if enrijecedor ==1:
            [parafuso,perfil_pilar,chapa,ver_parafuso,N_parafusos,altura_chapa,largura_chapa,esp_chapa_mm,esp_enrij_mm,esp] = dados_resultado
        else:
            [parafuso,perfil_pilar,chapa,ver_parafuso,N_parafusos,altura_chapa,largura_chapa,esp_chapa_mm,esp] = dados_resultado
 

        # Cria instância do AutoCAD
        acad = win32com.client.Dispatch("AutoCAD.Application")
        acad.Visible = True  # Garante que a janela fique visível

        # Aguarda 2 segundos
        time.sleep(2)

        acad = Autocad(create_if_not_exists=True)
        acad.prompt("Hello, Autocad from Python\n")
        print(acad.doc.Name)

        limpar_desenho(acad)

        pontos_hexagono = gerar_pontos_hexagono(parafuso.diametro_mm)

        # Chamando a função para desenhar a chapa 3D
        objetos_chapa = criar_chapa_3d(acad, chapa.df, esp_chapa_mm)

        objetos_parafusos=[]
        for i in range(ver_parafuso.shape[0]):
            x_centro = ver_parafuso.iat[i, 1]
            y_centro = ver_parafuso.iat[i, 2]

            # Adicionar circunferência no ponto
            obj = acad.model.AddCircle(APoint(x_centro, y_centro,esp_chapa_mm), parafuso.diametro_mm / 2)
            objetos_parafusos.append(obj)
            obj = acad.model.AddCircle(APoint(x_centro, y_centro,0), parafuso.diametro_mm / 2)
            objetos_parafusos.append(obj)
            # Transladar hexágono para o ponto atual
            hexagono_transladado = transladar_pontos(pontos_hexagono, x_centro, y_centro, esp_chapa_mm)

            for j in range(len(hexagono_transladado) - 1):
                p1 = APoint(*hexagono_transladado[j])
                p2 = APoint(*hexagono_transladado[j + 1])
                obj = acad.model.AddLine(p1, p2)
                objetos_parafusos.append(obj)

        base_perfil= min(ver_parafuso['y (mm)'])+ parametro_b(parafuso.diametro_mm)

        objetos_secao_perfil = desenhar_secao_perfil(acad, perfil_pilar, (chapa.B / 2) - (perfil_pilar.b_f / 2), posicao_y=base_perfil, altura_z=esp_chapa_mm)

        if enrijecedor == 1:
            desenhar_enrijecedores(acad, (0,0,esp_chapa_mm),base_perfil ,chapa, perfil_pilar, ver_parafuso, parafuso.diametro_mm, esp_enrij_mm)