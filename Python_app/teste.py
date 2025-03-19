import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from main import *
from v_p_chapa_cabeca import *
from materiais import *
import pyautocad


pontos_parafusos =pd.read_excel("posicao_gerdau.xlsx", sheet_name="parafusos")

pontos_chapa  =pd.read_excel("posicao_gerdau.xlsx", sheet_name="chapa")

B = pontos_chapa["x (mm)"].max() - pontos_chapa["x (mm)"].min() #em mm 

M = 30000 #kN.mm 

V = 103 #kN

T = 20 #kN

parafuso = ASTM_A325

diametros = diametros_A325

rosca = 1

planos_de_corte =1

N = len(pontos_parafusos)  #Número total de parafusos

n = (pontos_parafusos["x (mm)"] == pontos_parafusos["x (mm)"].iloc[0]).sum()  #número de parafusos por coluna

n_p_c = N/n  #número de parafusos por camada

S = curva_interacao(M,V,T,B,np.unique(pontos_parafusos["y (mm)"]),parafuso,rosca,planos_de_corte,n,n_p_c,diametros,gamma_a2)

print(S)

