from PySide6.QtWidgets import *
from front.base_form import ParametrosLigacaoBase
import materials

class ParametrosCantoneiraSolda(ParametrosLigacaoBase):
    def executar_calculo(self):
        try:
            from v_p_cantoneira_flex.v_p_cantoneira_flex_solda import dim_cant_solda

            V = float(self.input_cortante.text() or 0)
            T = float(self.input_tracao.text() or 0)
            perfil = getattr(materials, self.combo_perfil.currentText())
            perfil.inercias()
            aco_perfil = getattr(materials, self.combo_aco_perfil.currentText())
            perfil.material(aco_perfil)
            aco_cantoneira = getattr(materials, self.combo_aco_cantoneira.currentText())
            solda = getattr(materials, self.combo_solda.currentText())
            tipo_solda = True if self.combo_filete_duplo.currentText() == "Dupla" else False

            S = dim_cant_solda(T, V, materials.cantoneiras_dict, aco_cantoneira, perfil, solda, tipo_solda, materials.gamma)
            if isinstance(S[0], str):  # se for string, é um erro
                raise ValueError(S[0])  # lança a string como erro
 
            nome_cantoneira = S[0].nome
            comprimento = max(S[0].disp_vertices_chapa['z (mm)'])
            espessura_solda = S[1]

            resultado = QWidget()
            resultado.setWindowTitle("Resultado - Cantoneira Flexível (Solda)")
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Cantoneira Selecionada (Catálogo Gerdau): {nome_cantoneira}"))
            layout.addWidget(QLabel(f"Comprimento da Cantoneira : {comprimento:.2f} mm"))
            layout.addWidget(QLabel(f"Espessura da Solda: {espessura_solda:.2f} mm"))

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

        self.combo_aco_cantoneira = QComboBox()
        self.combo_aco_cantoneira.addItems([k for k in dir(materials) if isinstance(getattr(materials, k), materials.Aço)])
        self.form_layout.addRow("Aço da Cantoneira:", self.combo_aco_cantoneira)

        self.input_cortante = QLineEdit()
        self.form_layout.addRow("Força Cortante (kN):", self.input_cortante)

        self.input_tracao = QLineEdit()
        self.form_layout.addRow("Tração (kN):", self.input_tracao)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
