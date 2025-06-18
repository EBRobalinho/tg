from PySide6.QtWidgets import QComboBox, QLineEdit
from front.domain.box_ligacoes import Box_Ligacao
from back.logs import registrar_marcha
from back.materials_constants import DIMENSOES_PERFIS
from back.materials_loader import DIMENSOES_AÇO, DIMENSOES_PARAFUSO
from back.conversions import CONVERSORES
from back import conversions

class Ligacao_Flexivel(Box_Ligacao):
    def __init__(self):
        super().__init__("Ligação Flexível")
        self.combo_perfil : QComboBox
        self.combo_aco_perfil : QComboBox
        self.combo_aco : QComboBox
        self.input_cortante : QLineEdit
        self.input_tracao : QLineEdit
        self.combo_parafuso : QComboBox
        self.combo_solda : QComboBox
        self.input_rosca : QComboBox
        self.combo_qtd_parafusos : QComboBox

        uni_f, uni_m = CONVERSORES[conversions.UNIDADE_ESCOLHIDA]["rótulos"]

        # Campos principais
        self.combo_perfil = QComboBox()
        self.combo_perfil.addItems([k for k in DIMENSOES_PERFIS.keys()])
        self.form_layout.addRow("Perfil:", self.combo_perfil)

        self.combo_aco_perfil = QComboBox()
        self.combo_aco_perfil.addItems([k for k in DIMENSOES_AÇO.keys()])
        self.form_layout.addRow("Aço do Perfil:", self.combo_aco_perfil)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow(f"Força Cortante ({uni_f}):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow(f"Tração ({uni_f}):", self.input_tracao)


    def receber_input(self)-> list: 
        # Lê os valores dos esforços
        cortante = self.input_cortante.text()
        tracao = self.input_tracao.text()
        [M,V,T] = self.conversor_unidades(0,cortante,tracao)

        # Verificação: todos os esforços são zero
        if all(x == 0 for x in [V, T]):
            registrar_marcha("\n Nenhum esforço foi informado. A ligação não foi solicitada.")

        nome_perfil = self.combo_perfil.currentText()
        nome_aco_perfil = self.combo_aco_perfil.currentText()
        nome_aco = self.combo_aco.currentText()
        nome_parafuso = self.combo_parafuso.currentText()

        rosca = 1 if self.input_rosca.currentText() == "Sim" else False
        # Obtém as dimensões dos perfis e materiais
        dimensoes_perfil = DIMENSOES_PERFIS[nome_perfil]
        dimensoes_aco_perfil = DIMENSOES_AÇO[nome_aco_perfil]
        dimensoes_aco      = DIMENSOES_AÇO[nome_aco]

        dimensoes_parafuso = DIMENSOES_PARAFUSO[nome_parafuso]

        self.inputs = [V, T, nome_perfil, dimensoes_perfil, nome_aco_perfil, dimensoes_aco_perfil,
            nome_aco, dimensoes_aco, nome_parafuso, dimensoes_parafuso, rosca]
        
        return self.inputs  # Retorna os dados recebidos para uso posterior

    
    #Permite que o usuário escolha a quantidade de parafusos a depender do perfil da viga
    def atualizar_opcoes_parafusos(self):
        nome_perfil = self.combo_perfil.currentText()
        dimensoes_perfil = DIMENSOES_PERFIS[nome_perfil]
        h= dimensoes_perfil["h"]
        t_f = dimensoes_perfil["t_f"]
        # Calcula a altura útil do perfil
        h_w = h - 2 * t_f
        try:
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

        except Exception:
            self.combo_qtd_parafusos.clear()
            self.combo_qtd_parafusos.addItem("1")
