import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from design_functions import * 
from materials import ASTM_A325, diametros_A325
from v_p_cantoneira_flex.v_p_cantoneira_flex import dim_cant_parafuso

def tensao_cisalhante_cortante_filete_cantoneira(cantoneira,V,filete_duplo):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    comprimento=cantoneira.comprimento #Quem resistente ao esforço cortante na solda é a componente vertical da solda

    return V/qtd/0.7/comprimento 

def tensao_cisalhante_normal_filete_cantoneira(cantoneira,V,filete_duplo):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    comprimento=2*cantoneira.b_mm #Quem resistente ao esforço cortante na solda é a componente vertical da solda (o valor é vezes 2 pq há dois braços de cantoneira soldados)

    return V/qtd/0.7/comprimento 


def dim_cant_solda(T,V,cantoneiras_dict,material,perfil,solda,filete_duplo,gamma):

    # A ideia é usar a cantoneira que o método parafusado usou, para depois usar as dimensões da cantoneira para dimensionar a ligação soldada
    N= np.floor((1+np.floor((perfil.h_w-2*30)/67.5))/2)  # Número médio de parafusos necessários
    parafuso = ASTM_A325
    parafuso.prop_geometricas(rosca = 1,planos_de_corte =2)
    diametros = diametros_A325
    S = dim_cant_parafuso(T,V,cantoneiras_dict,material,perfil,parafuso,N,gamma)
    if isinstance(S[0], str):  # se for string, é um erro
        return S  # lança a string como erro
    #Dimensionamento da solda:
    cantoneira_escolhida = S[0]
    #Pois há duas cantoneiras, logo a tensão sobre a qual a solda de cada uma está submetida advém de metade do valor dos esfoços solicitantes
    esf_V_cant = V/2
    esf_T_cant = T/2

    tal_r1 = solda.f_uw_mpa*0.6/gamma[1]     #Mpa    #Tabela 9, item 6.2.5.1 da NBR 8800:2024 (Relativa a tensão resistida pela solda)
    tal_r2 = cantoneira_escolhida.f_u*0.6/gamma[0]      #Letra b do item 6.5.5 da NBR 8800:2024 (relativa a ruptura do metal base)
    tal_r3 = perfil.f_u*0.6/gamma[0]

    tal_r = min(tal_r1,tal_r2,tal_r3)   #Menor resistência dos metais envolvidos na ligação

    tal_m=0
    tal_v = tensao_cisalhante_cortante_filete_cantoneira(cantoneira_escolhida,esf_V_cant,filete_duplo)
    tal_n = tensao_cisalhante_normal_filete_cantoneira(cantoneira_escolhida,esf_T_cant,filete_duplo)
    tal_s = np.sqrt((tal_m)**2 + (tal_v)**2 + (tal_n)**2)*1000   #Tensão solicitante em Mpa*mm    

    esp = tal_s/tal_r

    esp_metal_base = perfil.t_w
    esp_minima = criterio_min_solda_filete(esp_metal_base)

    esp_final = max(esp_minima,esp)

    return [cantoneira_escolhida,esp_final]