from PySide6.QtWidgets import *
from front.base_form import ParametrosLigacaoBase
import materials

class ParametrosVigaSobrePilar(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:
            from v_p_viga_sobre_pilar.v_p_viga_sobre_pilar import dim_chapa_pilar
            from v_p_chapa_cabeca.v_p_chapa_cabeca import espessura_solda

            M = float(self.input_momento.text() or 0)
            V = float(self.input_cortante.text() or 0)
            T = float(self.input_tracao.text() or 0)

            perfil = getattr(materials, self.combo_perfil.currentText())
            perfil.inercias()

            aco_chapa = getattr(materials, self.combo_aco_chapa.currentText())
            aco_pilar = getattr(materials, self.combo_aco_pilar.currentText())
            perfil.material(aco_pilar)

            solda = getattr(materials, self.combo_solda.currentText())
            parafuso = getattr(materials, self.combo_parafuso.currentText())
            rosca = int(self.input_rosca.text())
            planos = int(self.input_planos.text())
            filete_duplo = True if self.combo_filete_duplo.currentText() == "Dupla" else False
            parafuso.prop_geometricas(rosca=rosca, planos_de_corte=planos)
            enrijecedor = 1 if self.combo_enrijecedor.currentText() == "Sim" else 0

            S = dim_chapa_pilar(M, V, T, aco_chapa, enrijecedor, perfil, parafuso, materials.gamma)

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
        self.form_layout.addRow("Momento (kN.mm):", self.input_momento)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow("Força Cortante (kN):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (kN):", self.input_tracao)

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



