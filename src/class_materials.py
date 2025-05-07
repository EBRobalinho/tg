import pandas as pd
import math
import re
from fractions import Fraction
from design_functions import * 

# Definição das classes a serem utilizadas

class Chapa:
    def __init__(self, B, h, a):
        """Inicializa a classe com os valores B, h e a."""
        self.B = B #Largura da chapa em mm
        self.h = h #Altura da viga que vai na chapa
        self.a = a #distância do CENTRO dO parafuso superior até borda da chapa:  ITEM 6.3.5.2 NBR 8800:2024
        self.df = self.vertices_chapa()

    def material(self, aco):
        self.f_y = aco.f_y  # MPa
        self.f_u = aco.f_u  # MPa

    @property
    def espessuras_disponiveis(self):
        espessuras_pol = ["1/4","3/8","1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2"]  #Espessuras possíveis para chapas de aço    (máximo valor encontrado em chapa da Gerdau)
        return [pol_to_mm(x) for x in espessuras_pol]

class ChapaCabeca(Chapa):   #Subclasse utilizada para a ligação chapa-cabeça
    def vertices_chapa(self):
        """Cria o DataFrame com os vértices e coordenadas."""
        data = {
            "vértice": [1, 2, 3, 4,5],
            "x (mm)": [0, self.B, self.B, 0,0],
            "y (mm)": [0, 0, 20 + self.h + 2 * self.a, 20 + self.h + 2 * self.a,0]
        }
        return pd.DataFrame(data)

class ChapaExtremidade(Chapa):   #Subclasse utilizada para a ligação chapa-extremidade
    def vertices_chapa(self):
        """Cria o DataFrame com os vértices e coordenadas."""
        data = {
            "vértice": [1, 2, 3, 4,5],
            "x (mm)": [0, self.B, self.B, 0,0],
            "y (mm)": [0, 0, self.h ,self.h,0]
        }
        return pd.DataFrame(data)

class Aço:
    def __init__(self, nome, f_y, f_u, E, densidade):
        self.nome = nome # Nome do aço (ex: ASTM A36)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa
        self.E = E # GPa
        self.densidade = densidade  # kg/m³

class Parafuso:
    def __init__(self, nome,f_y, f_u):
        self.nome = nome # Nome do parafuso (ex: ASTM A325)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa

    def diametro(self, diametro):
        self.diametro_pol = diametro  # Armazena o valor original em polegadas
        self.diametro_mm = pol_to_mm(diametro)
        self.A_g = math.pi * (self.diametro_mm / 2) ** 2 # mm²

    def prop_geometricas(self,rosca,planos_de_corte):
        self.rosca = rosca
        self.planos_de_corte = planos_de_corte

    @property
    def diametros_disponiveis(self):
        if self.nome == 'ASTM A307':
            return ["1/2", "9/16", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8","1.1/2", "1.3/4", "2", "2.1/4", "2.1/2", "2.3/4", "3", "3.1/4","3.1/2", "3.3/4", "4" ]
        elif self.nome == 'ASTM A325':
            return ["1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]
        elif self.nome == "ASTM 490":   
            return ["1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]

class Solda:
    def __init__(self, nome, f_uw):
        self.nome = nome # Nome da solda (ex: E6010)
        self.f_uw_ksi = f_uw # ksi
        self.f_uw_mpa = f_uw * 6.89476 # MPa
        # Ver tabela relacionando tipo de metal com a solda Tabela 9 item 6.2.5.1 da NBR 8800:2024

class Perfil:
    def __init__(self, Nome, espessura_base, base, altura, espessura_alma):
        self.nome = Nome #referencia ao objeto de aço
        self.t_f = espessura_base # mm
        self.b_f = base # mm
        self.h = altura # mm   
        self.t_w  = espessura_alma #mm
        self.R_conc = 10 #mm
        self.h_w = self.h - 2*self.t_f - 2*self.R_conc

    def inercias(self):
        self.I_mesa = 2*((self.b_f*self.t_f**3)/12 + (self.b_f*self.t_f)*(((self.h - self.t_f)/2)**2))  #mm^4
        self.I_alma = (self.t_w*((self.h - 2*self.t_f)**3)/12)  #mm^4
        self.I_perfil = self.I_mesa + self.I_alma  #mm^4

    def material(self, aco):
        self.f_y = aco.f_y  # MPa
        self.f_u = aco.f_u  # MPa

class Cantoneira:
    def __init__(self, b_pol, t_pol):
        self.nome = f"L_" + b_pol+ "x" + t_pol  # Nome formatado
        self.b_pol = (b_pol)  # b em polegadas
        self.t_pol = (t_pol)  # t em polegadas
        self.b_mm = pol_to_mm(b_pol)  # Convertido para mm
        self.t_mm = pol_to_mm(t_pol)  # Convertido para mm
        self.R_conc = 10 #mm 
        self.f_b = None     
        self.f_f = None
        self.f_l = None
        self.comprimento = None
        self.disp_parafusos = None


    def material(self, aco):
        self.f_y = aco.f_y  # MPa
        self.f_u = aco.f_u  # MPa

    def vertices_chapa(self, perfil):

        b = self.b_mm
        t = self.t_mm
        r = self.R_conc

        # Define os 8 vértices da cantoneira em 3D (base z = 0)
        vertices = [
            (0, 0, 0),           # V1
            (b, 0, 0),           # V2
            (b, t, 0),           # V3
            (t + r, t, 0),       # V4
            (t, t + r, 0),       # V5
            (t, b, 0),           # V6
            (0, b, 0),           # V7
            (0, 0, 0),           # V8 (fecha a seção)
        ]

        # Extrude os mesmos pontos para o comprimento em z
        vertices_3d = vertices + [(x, y, self.comprimento) for (x, y, _) in vertices]

        # Cria DataFrame com vértices e coordenadas
        data = {
            "vértice": list(range(1, len(vertices_3d) + 1)),
            "x (mm)": [v[0] for v in vertices_3d],
            "y (mm)": [v[1] for v in vertices_3d],
            "z (mm)": [v[2] for v in vertices_3d],
        }

        self.disp_vertices_chapa = pd.DataFrame(data)
