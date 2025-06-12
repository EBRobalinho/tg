import math
from back.design_functions import pol_to_mm, mm_para_polegada

class Parafuso:
    def __init__(self, nome: str, f_y: float, f_u: float, diametro: list):
        self.nome = nome  # Nome do parafuso (ex: ASTM A325)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa
        self.diametro_pol = diametro  # Armazena os valores possíveis de diâmetro em polgadas
        self.diametro_mm = [pol_to_mm(d) for d in diametro] #Armazena os valores convertidos para mm
        self.d : float #Diâmetro encontrado do dimensionamento do Parafuso
        self.d_pol: str = mm_para_polegada(self.d)
        self.A_g = math.pi * (self.d / 2) ** 2  # mm²


    def prop_geometricas(self, rosca: int, planos_de_corte: int):
        self.rosca = rosca
        self.planos_de_corte = planos_de_corte

