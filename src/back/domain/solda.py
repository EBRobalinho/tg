class Solda:
    def __init__(self, nome, f_uw):
        self.nome = nome # Nome da solda (ex: E6010)
        self.f_uw_ksi = f_uw # ksi
        self.f_uw_mpa = f_uw * 6.89476 # MPa
        # Ver tabela relacionando tipo de metal com a solda Tabela 9 item 6.2.5.1 da NBR 8800:2024

