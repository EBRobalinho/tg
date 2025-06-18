from PySide6.QtWidgets import QComboBox, QLineEdit
from front.domain.box_ligacoes import Box_Ligacao
from back.logs import registrar_marcha
from back.materials_constants import DIMENSOES_PERFIS,DIMENSOES_AÇO, DIMENSOES_SOLDA, DIMENSOES_PARAFUSO
from back.conversions import CONVERSORES, UNIDADE_ESCOLHIDA

class Ligacao_Rigida(Box_Ligacao):
    def __init__(self):
        super().__init__("Ligação Rígida")
        self.combo_perfil : QComboBox
        self.combo_aco_perfil : QComboBox
        self.combo_aco : QComboBox
        self.input_momento : QLineEdit
        self.input_cortante : QLineEdit
        self.input_tracao : QLineEdit
        self.combo_parafuso : QComboBox
        self.combo_solda : QComboBox
        self.input_rosca : QComboBox
        
        uni_f, uni_m = CONVERSORES[UNIDADE_ESCOLHIDA]["rótulos"]

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
        self.form_layout.addRow(f"Momento ({uni_m}):", self.input_momento)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow(f"Força Cortante ({uni_f}):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow(f"Tração ({uni_f}):", self.input_tracao)

        self.combo_parafuso = QComboBox()
        self.combo_parafuso.addItems([k for k in DIMENSOES_PARAFUSO.keys()])
        self.form_layout.addRow("Parafuso:", self.combo_parafuso)
        
        self.combo_solda = QComboBox()
        self.combo_solda.addItems([k for k in DIMENSOES_SOLDA.keys()])
        self.form_layout.addRow("Solda:", self.combo_solda)


    def receber_input(self)-> list: 
        # Lê os valores dos esforços
        [M,V,T] = self.conversor_unidades(self.input_momento,self.input_cortante,self.input_tracao)

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
        rosca = 1 if self.input_rosca.currentText() == "Sim" else False
        dimensoes_perfil = DIMENSOES_PERFIS[nome_perfil]
        dimensoes_aco_perfil = DIMENSOES_AÇO[nome_aco_perfil]
        dimensoes_aco      = DIMENSOES_AÇO[nome_aco]
        dimensoes_solda    = DIMENSOES_SOLDA[nome_solda]
        dimensoes_parafuso = DIMENSOES_PARAFUSO[nome_parafuso]

        self.inputs = [M, V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca, nome_solda, dimensoes_solda]
        
        return self.inputs  # Retorna os dados recebidos para uso posterior
