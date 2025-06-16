from front.base_form import ParametrosLigacaoBase, iniciar_autocad
import back.materials_constants as materials
from back.utils import registrar_marcha
from back.draw_autocad.draw_autocad_figures import *
from back.materials_constants import DIMENSOES_AÇO, DIMENSOES_PERFIS, DIMENSOES_PARAFUSO, DIMENSOES_SOLDA 

from back.domain.perfil import Perfil
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.solda import Solda

import math
#Importar bibliotecas do sistemas

from pyautocad import APoint 


class ParametrosChapaCabeca(ParametrosLigacaoBase):

    def executar_calculo(self):
        try:
            # Lê os valores dos esforços
            M = self.ler_momento_tonelada_metro(self.input_momento)
            V = self.ler_forca_tonelada(self.input_cortante)
            T = self.ler_forca_tonelada(self.input_tracao)

            # Verificação: todos os esforços são zero
            if all(x == 0 for x in [M, V, T]):
                registrar_marcha("\n Nenhum esforço foi informado. A ligação não foi solicitada.")
                raise ValueError("Nenhum esforço foi informado. A ligação não foi solicitada.")
                return

            # Dados que o usuário escolhe
            nome_perfil = self.combo_perfil.currentText()
            nome_aco_perfil = self.combo_aco_perfil.currentText()
            nome_aco = self.combo_aco.currentText()
            nome_parafuso = self.combo_parafuso.currentText()
            nome_solda = self.combo_solda.currentText()

            dimensoes_perfil = DIMENSOES_PERFIS[nome_perfil]
            dimensoes_aco_perfil = DIMENSOES_AÇO[nome_aco_perfil]
            dimensoes_aco      = DIMENSOES_AÇO[nome_aco]
            dimensoes_solda    = DIMENSOES_SOLDA[nome_solda]
            dimensoes_parafuso = DIMENSOES_PARAFUSO[nome_parafuso]



            aco_perfil = Aço(nome_aco_perfil,*dimensoes_aco_perfil)
            perfil = Perfil(nome_perfil,*dimensoes_perfil,aco_perfil)
            
            perfil.inercias()

            aco      = Aço(nome_aco,*dimensoes_aco)      
            solda    = Solda(nome_solda,*dimensoes_solda)    
            parafuso = Parafuso(nome_parafuso,*dimensoes_parafuso)

            #rosca = int(self.input_rosca.text())
            rosca = 1 if self.input_rosca.currentText() == "Sim" else False
            #planos = int(self.input_planos.text())
            #filete_duplo = True if self.combo_filete_duplo.currentText() == "Dupla" else False
            chapa_rigida = 1 if self.combo_chapa_rigida.currentText() == "Sim" else 0

            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=1)
            filete_duplo = True
            # Função que faz o dimensionamento
            S = dim_chapa_parafuso(M, V, T, perfil, materials.disposicoes_gerdau_chapa_cabeca, parafuso, materials.gamma)

            if isinstance(S[0], str):  # se for string, é um erro
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S[0])  # lança a string como erro

            # Variáveis utilizadas
            diam_pol = S[1].diametro_pol
            N_parafusos = len(S[4])
            altura_chapa = S[3].df["y (mm)"].max()
            largura_chapa = S[3].df["x (mm)"].max()
            chapa = S[3]
            ver_parafuso = S[4]

            #Calculo da espessura da chapa e da solda
            r_parafuso_total = resistencia_total(S[1],materials.gamma)
            #Considera os parafusos trabalhando plasticamente de forma que cada um receba a mesma carga
            s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, S[1] , S[0])
            s_p_t = solicitante_parafuso_tração(T,N_parafusos)
            s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
            
            espessura_placa = exp_placa(aco,chapa,chapa_rigida,ver_parafuso,S[1].diametro_mm,r_parafuso_total, (s_p_m + s_p_t), materials.gamma)

            if espessura_placa==["A ligação não aguenta a solicitação desejada."]:  # se for string, é um erro
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError(S[0])  # lança a string como erro

            espessura__solda = espessura_solda(M,V,T,solda,perfil,espessura_placa,filete_duplo,materials.gamma)


            C = criterio_cisalhamento_chapa(chapa,s_p_v,espessura_placa,ver_parafuso,S[1],aco,gamma)

            if C[0] == 0:
                raise ValueError(C[1])

            # propriedade com os dados do resultado para o desenho
            self.dados_resultado = [perfil,S[1],S[4],S[3],N_parafusos,espessura_placa,espessura_solda]

            layout, resultado = self.exposicao_resultado(diam_pol, N_parafusos, altura_chapa, largura_chapa, espessura_placa, espessura__solda)
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

    def __init__(self, titulo):
        super().__init__(titulo)

        # Campos principais
        self.combo_perfil = QComboBox()
        self.combo_perfil.addItems([k for k in DIMENSOES_PERFIS.keys()])
        self.form_layout.addRow("Perfil:", self.combo_perfil)

        self.combo_aco_perfil = QComboBox()
        self.combo_aco_perfil.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço do Perfil:", self.combo_aco_perfil)

        self.combo_aco = QComboBox()
        self.combo_aco.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço da Chapa:", self.combo_aco)

        self.input_momento = QLineEdit()
        self.form_layout.addRow("Momento (tf.m):", self.input_momento)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow("Força Cortante (tf):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (tf):", self.input_tracao)

        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in DIMENSOES_PARAFUSO.keys()])
        self.form_layout.addRow("Parafuso:", self.combo_parafuso)
        
        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in DIMENSOES_SOLDA.keys()])
        self.form_layout.addRow("Solda:", self.combo_solda)

        # Botão de cálculo
        self.botao_calcular = QPushButton("Calcular e Mostrar Resultado")
        self.botao_calcular.clicked.connect(self.executar_calculo)
        self.layout_principal.addWidget(self.botao_calcular)

        # Opções Avançadas
        self.input_rosca = QComboBox()
        self.input_rosca.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("O Corte do Parafuso passa na rosca ?", self.input_rosca)

        #self.input_planos = QLineEdit("1")
        #self.avancado_layout.addRow("Quantidade de planos de Corte no Parafuso:", self.input_planos)

        self.combo_chapa_rigida = QComboBox()
        self.combo_chapa_rigida.addItems(["Sim", "Não"])
        self.avancado_layout.addRow("Chapa Rígida:", self.combo_chapa_rigida)

        #self.combo_filete_duplo = QComboBox()
        #self.combo_filete_duplo.addItems(["Simples", "Dupla"])
        #self.combo_filete_duplo.setCurrentText("Dupla")  # define "Dupla" como padrão
        #self.avancado_layout.addRow("Solda Dupla:", self.combo_filete_duplo)

    def exposicao_resultado(self, diam_pol, N_parafusos, altura_chapa, largura_chapa, exp, esp):
        resultado = QWidget()
        resultado.setWindowTitle("Resultado - Chapa de Cabeça")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Diâmetro do Parafuso: {diam_pol} pol"))
        layout.addWidget(QLabel(f"Quantidade de Parafusos: {N_parafusos}"))
        layout.addWidget(QLabel(f"Altura da Chapa: {altura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Largura da Chapa: {largura_chapa:.2f} mm"))
        layout.addWidget(QLabel(f"Espessura da Chapa: {exp:.2f} mm / {(exp / 25.4):.3f} pol"))
        layout.addWidget(QLabel(f"Espessura do Filete de Solda: {esp:.2f} mm"))
        self.obs = "Solda colocada em todo contorno da viga com a chapa."
        #Adiciona o resultado no Layout
        resultado.setLayout(layout)
        return layout, resultado

    def desenhar_no_autocad(self, dados_resultado):

        acad = iniciar_autocad()

        limpar_desenho(acad)

        [perfil_escolhido,parafuso,ver_parafuso,chapa,N_parafusos,exp,esp] = dados_resultado 

        pontos_hexagono = gerar_pontos_hexagono(parafuso.diametro_mm)

        # Chamando a função para desenhar a chapa 3D
        objetos_chapa = criar_chapa_3d(acad, chapa.df, exp)

        # Criação dos objetos dos parafusos
        objetos_parafusos=[]

        #Rearranjar os parafusos para desenhar  
        rearranjar_parafusos(acad, ver_parafuso,objetos_parafusos, parafuso,pontos_hexagono, exp)
        #Desenhar a seção do perfil
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
