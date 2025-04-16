from PySide6.QtWidgets import *
from front.base_form import ParametrosLigacaoBase
import materials

class ParametrosChapaExtremidade(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:
            from v_p_chapa_extremidade.v_p_chapa_extremidade import dim_chapa_parafuso
            from v_p_chapa_cabeca.v_p_chapa_cabeca import espessura_solda

            V = float(self.input_cortante.text() or 0)
            T = float(self.input_tracao.text() or 0)

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
        self.form_layout.addRow("Força Cortante (kN):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (kN):", self.input_tracao)

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

