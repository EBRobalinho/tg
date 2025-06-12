import math
from back.design_functions import pol_to_mm

class Parafuso:
    def __init__(self, nome,f_y, f_u,diametro):
        self.nome = nome # Nome do parafuso (ex: ASTM A325)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa
        self.diametro_pol = diametro  # Armazena os valores possíveis de diâmetro em polgadas
        self.diametro_mm = [pol_to_mm(d) for d in diametro] #Armazena os valores convertidos para mm
        self.A_g = [math.pi * (d / 2) ** 2 for d in self.diametro_mm]  # mm²
        self.d : None|float = None #Diâmetro encontrado do dimensionamento do Parafuso


    def prop_geometricas(self,rosca,planos_de_corte):
        self.rosca = rosca
        self.planos_de_corte = planos_de_corte

