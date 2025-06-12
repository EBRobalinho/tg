import pandas as pd
from back.design_functions import pol_to_mm


class Chapa:
    def __init__(self, B: float, h: float, a: float):
        """Inicializa a classe com os valores B, h e a."""
        self.B = B #Largura da chapa em mm
        self.h = h #Altura da viga que vai na chapa
        self.a = a #distância do CENTRO dO parafuso superior até borda da chapa:  ITEM 6.3.5.2 NBR 8800:2024

    def material(self, aco):
        self.f_y = aco.f_y  # MPa
        self.f_u = aco.f_u  # MPa

    @property
    def espessuras_disponiveis(self):
        espessuras_pol = ["1/4","3/8","1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2"]  #Espessuras possíveis para chapas de aço    (máximo valor encontrado em chapa da Gerdau)
        return [pol_to_mm(x) for x in espessuras_pol]

class ChapaCabeca(Chapa):   #Subclasse utilizada para a ligação chapa-cabeça
    def __init__(self, B: float, h: float, a: float):
        super().__init__(B, h, a)
        self.df = self.vertices_chapa()  # DataFrame com os vértices e coordenadas da chapa

    def vertices_chapa(self):
        """Cria o DataFrame com os vértices e coordenadas."""
        data = {
            "vértice": [1, 2, 3, 4,5],
            "x (mm)": [0, self.B, self.B, 0,0],
            "y (mm)": [0, 0, 20 + self.h + 2 * self.a, 20 + self.h + 2 * self.a,0]
        }
        return pd.DataFrame(data)

class ChapaExtremidade(Chapa):
    def __init__(self, B: float, h: float, a: float):
        super().__init__(B, h, a)
        self.df = self.vertices_chapa()  # DataFrame com os vértices e coordenadas da chapa

    #Subclasse utilizada para a ligação chapa-extremidade
    def vertices_chapa(self):
        """Cria o DataFrame com os vértices e coordenadas."""
        data = {
            "vértice": [1, 2, 3, 4,5],
            "x (mm)": [0, self.B, self.B, 0,0],
            "y (mm)": [0, 0, self.h ,self.h,0]
        }
        return pd.DataFrame(data)