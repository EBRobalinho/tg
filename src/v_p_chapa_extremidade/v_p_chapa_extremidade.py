import pandas as pd
import numpy as np
from design_functions import *
from class_materials import *
from v_p_chapa_cabeca.v_p_chapa_cabeca import parametro_b,espessura_solda,exp_placa


##### Da Disposição    

def disposicao_parafusos(t_f, b, c ,e2, e1, h_gerdau):
    x_positions = [e2, e2 + e1]

    parafusos_x = []
    parafusos_y = []

    z = b

    while (z+b < h_gerdau):
        # Para cada camada, adiciona dois parafusos (um em cada posição de x)
        parafusos_x.extend(x_positions)
        parafusos_y.extend([z, z])
        z += c

    data = {
        "parafuso": list(range(1, len(parafusos_x) + 1)),
        "x (mm)": parafusos_x,
        "y (mm)": parafusos_y
    }


    return pd.DataFrame(data)

#Obtém os valorea arbitrados das disposições contrutivas, conforme catálogo da Gerdau
def arranjo_chapa_parafusos(perfil,parafuso):
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    h_gerdau = perfil.h - 2*perfil.t_f   #Altura total do perfil Gerdau

    b = dist_min_borda_pol(parafuso.diametro_pol) #Distância vertical do parafuso mais em cima até a borda da placa 

    e1 = max(120,3*parafuso.diametro_mm)  #Distância horizontal entre parafusos (na minha linha, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    c  = max(75,3*parafuso.diametro_mm)  #Distância vertical entre parafusos (na minha coluna, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    e2 = max(40,dist_min_borda_pol(parafuso.diametro_pol)) #Distância horizontal entre parafuso-borda (na minha linha, segundo o manual da Gerdau) e item 6.3.11.1 da NBR 8800:2024

    disposicao = disposicao_parafusos(perfil.t_f, b,c, e2, e1, h_gerdau)

    N_parafusos = (disposicao.shape[0])/2

    B_gerdau = 200 #mm     Segundo Item 4.1.1 do manual da Gerdau

    B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

    B = max(B_norma,B_gerdau) 

    h_parafusos = max(disposicao["y (mm)"]) + e2

    h = h_gerdau

    chapa = ChapaExtremidade(B,h,b)

    return [chapa,disposicao,N_parafusos]

def resistencia_cisalhamento(corte,material,comprimento,N_parafusos,espessura,diametro,gamma):   #Item 6.5.5 da NBR 8800:2024
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]

    resistencia1 = corte*0.6*material.f_y*comprimento*espessura/gamma_a1    #Escoamento da seção bruta
    resistencia2 = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2   #Ruptura da seção líquida

    resistencia=min(resistencia1,resistencia2)
    return resistencia/1000 #Sair o resultado em kN


def dim_chapa_parafuso(V,T,perfil,parafuso,material,rigida,solda,filete_duplo,gamma):  #Item 6.3.3.4 da NBR 8800:2024
    #Tem de variar no espaço de busca os diâmetros
    for d in parafuso.diametros_disponiveis:

        #Atualiza o diâmetro de busca
        parafuso.diametro(d)  

        #Arranjo da chapa e dos parafusos 
        [chapa,ver_parafuso,N_parafusos] = arranjo_chapa_parafusos(perfil,parafuso)

        #Resistentes do parafuso para tração e cisalhamento
        r_p_t=resistencia_parafuso_tração(parafuso,gamma)
        r_p_v=resistencia_parafuso_cisalhamento(parafuso,gamma)
        r_parafuso_total = resistencia_total(parafuso,gamma)

        #Solicitantes no parafuso para tração e cisalhamento
        s_p_t = solicitante_parafuso_tração(T,N_parafusos)
        s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
        s_parafuso_total = solicitante_total(T,V,N_parafusos)

        #Curva de interação Item 6.3.3.4 da NBR 8800:2024
        curva=(((s_p_t)/r_p_t)**2 + (s_p_v/r_p_v)**2)

        if curva > 1:
            continue
        else:   
            #Cálculo da espessura da placa
            exp = exp_placa(material, chapa, rigida, ver_parafuso, parafuso.diametro_mm, r_parafuso_total,s_parafuso_total,gamma)

            #Teste e relação a escoamento da seção bruta e ruptura da seção líquida
            corte = 2 # Há 2 planos de corte na chapa
            N_parafusos_fileira =2 #Sempre serão só 2 parafusos em cada horizontal
            comprimento = chapa.df['x (mm)'].max()

            res_cisalhamento_chapa = resistencia_cisalhamento(corte,material,comprimento,N_parafusos_fileira,exp,parafuso.diametro_mm,gamma)
            if res_cisalhamento_chapa > s_p_v:
                break
            else:
                continue

    #Cálculo da solda:

    esp_solda = espessura_solda(0,V,T,solda,perfil,exp,filete_duplo,gamma)

    return [chapa,exp,parafuso,ver_parafuso,solda,esp_solda]



