from back.domain.materials import Aço

class Perfil:
    def __init__(self, Nome: str, espessura_base: float, base: float, altura: float, espessura_alma: float, B: float, a: float, e2: float, e1: float, qtd: int, aco: Aço):
        self.nome = Nome #referencia ao objeto de aço
        self.t_f = espessura_base # mm
        self.b_f = base # mm
        self.h = altura # mm   
        self.t_w  = espessura_alma #mm
        self.R_conc = 10 #mm
        self.h_w = self.h - 2*self.t_f - 2*self.R_conc
        self.f_y = aco.f_y  # MPa
        self.f_u = aco.f_u  # MPa
        self.material = aco

    def inercias(self):
        self.I_mesa = 2*((self.b_f*self.t_f**3)/12 + (self.b_f*self.t_f)*(((self.h - self.t_f)/2)**2))  #mm^4
        self.I_alma = (self.t_w*((self.h - 2*self.t_f)**3)/12)  #mm^4
        self.I_perfil = self.I_mesa + self.I_alma  #mm^4

