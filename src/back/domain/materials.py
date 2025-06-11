class Aço:
    def __init__(self, nome, f_y, f_u, E, densidade):
        self.nome = nome # Nome do aço (ex: ASTM A36)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa
        self.E = E # GPa
        self.densidade = densidade  # kg/m³