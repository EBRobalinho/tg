import pandas as pd
from back.conversions import pol_to_mm
from back.domain.materials import Aço  # Importa a classe Aco do módulo aco.py


class Cantoneira:
    def __init__(self, b_pol: str , t_pol: str, aco):
        self.nome = f"L_{b_pol}x{t_pol}"  
        self.b_pol = (b_pol)  # b em polegadas
        self.t_pol = (t_pol)  # t em polegadas
        self.b_mm = pol_to_mm(b_pol)  # Convertido para mm
        self.t_mm = pol_to_mm(t_pol)  # Convertido para mm
        self.R_conc: float = 10 #mm 
        self.f_b: int      
        self.f_f: int 
        self.f_l: int 
        self.comprimento: int
        self.disp_parafusos: pd.DataFrame
        self.material: Aço = aco


    def vertices_chapa(self):

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
