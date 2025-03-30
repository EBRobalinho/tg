import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from main import *
from materiais import *

#Resistência das peças para Esmagamento e rasgamento

def resistencia_esmagamento(corte,material,cantoneira,espessura,diametro,gamma):
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    resistencia = corte*2.4*material.f_u*espessura*diametro*N_parafusos/gamma   #Sair o resultado em N

    return resistencia/1000 #Sair o resultado em kN

def resistencia_rasgamento_esmagamento(corte,material,cantoneira,espessura,distancia,gamma):
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    # A distância pode ser furo-borda ou furo-furo
    resistencia = 1.2*corte*material.f_u*espessura*distancia*N_parafusos/gamma   #Sair o resultado em N

    return resistencia/1000 #Sair o resultado em kN

def resistencia_cisalhamento_secao_bruta(corte,material,comprimento,espessura,gamma):

    resistencia = corte*0.6*material.f_y*comprimento*espessura/gamma   #Sair o resultado em N

    return resistencia/1000 #Sair o resultado em kN

def resistencia_cisalhamento_secao_liquida(corte,material,comprimento,cantoneira,espessura,diametro,gamma):            #Talvez seja necessário considerar recorte da viga
    # o 2 mm vem da folga de 1 mm de cada lado do parafuso, o 1.5 é recomendado pela norma
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    resistencia = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(diametro+2+1.5))/gamma   #Sair o resultado em N

    return resistencia/1000 #Sair o resultado em kN

def resistencia_block(corte,material,cantoneira,comprimento,espessura,diametro,gamma):   #Ver se precisa fazer o mesmo para block shear no perfil
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    A_gv = espessura*(cantoneira.comprimento - cantoneira.f_b)  #Area bruta da cantoneira sujeita a cisalhamento (O comprimento pode ser o espaçamento entre os parafusos ou )
    A_nv = espessura*(cantoneira.comprimento - cantoneira.f_b) - (N_parafusos-0.5)*(diametro+2+1.5)*espessura  #Area líquida da cantoneira sujeita a cisalhamento
    A_nt = (cantoneira.f_b - 0.5*(diametro+2+1.5))*espessura
    C_ts=1
    resistencia = min(0.6*material.f_u*A_nv + C_ts*material.f_u*A_nt,0.6*material.f_y*A_gv + C_ts*material.f_u*A_nt)*corte/gamma   #Sair o resultado em N  

    return resistencia/1000 #Sair o resultado em kN

def curva_interacao2(T,V,material,perfil,parafuso,diametros,N_parafusos,gamma):
    rosca=parafuso.rosca
    corte=parafuso.planos_de_corte
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]
    i=0
    j=0
    solucion = []
    while (i < len(cantoneiras_dict)-1) or (j < len(diametros)-1):  
        cantoneira_escolhida = cantoneiras_dict[i]
        cantoneira_escolhida.material(material)
        cantoneira_escolhida.disp(perfil, N_parafusos)

        parafuso.diametro(diametros[j])

        V_s_d = V
        T_s_d = T

        R1 = N_parafusos*resistencia_total(parafuso,gamma_a2)

        R2 = resistencia_esmagamento(corte,cantoneira_escolhida,cantoneira_escolhida,cantoneira_escolhida.t_mm,parafuso.diametro_mm,gamma_a2) #Da cantoneira
        R3 = resistencia_esmagamento(1,perfil,cantoneira_escolhida,perfil.t_w,parafuso.diametro_mm,gamma_a2)  # Do perfil

        R4 = resistencia_rasgamento_esmagamento(corte,cantoneira_escolhida,cantoneira_escolhida,cantoneira_escolhida.t_mm,cantoneira_escolhida.f_f - parafuso.diametro_mm -3.5,gamma_a2) #Da cantoneira f_f
        R5 = resistencia_rasgamento_esmagamento(corte,cantoneira_escolhida,cantoneira_escolhida,cantoneira_escolhida.t_mm,cantoneira_escolhida.f_b - 0.5*(parafuso.diametro_mm+3.5),gamma_a2) #Da cantoneira f_b
        R6 = resistencia_rasgamento_esmagamento(1,perfil,cantoneira_escolhida,perfil.t_w,cantoneira_escolhida.f_f - parafuso.diametro_mm -3.5,gamma_a2) #Do Perfil f_f
        R7 = resistencia_rasgamento_esmagamento(1,perfil,cantoneira_escolhida,perfil.t_w,cantoneira_escolhida.b_mm + 10,gamma_a2) #Do Perfil f_b (10mm minimo de distância do furo ao borda do perfil)

        R8 = resistencia_cisalhamento_secao_bruta(corte,cantoneira_escolhida,cantoneira_escolhida.comprimento,cantoneira_escolhida.t_mm,gamma_a1) #Da cantoneira
        R9 = resistencia_cisalhamento_secao_bruta(1,perfil,perfil.h,perfil.t_w,gamma_a1) #Do perfil

        R10 = resistencia_cisalhamento_secao_liquida(corte,cantoneira_escolhida,cantoneira_escolhida.comprimento,cantoneira_escolhida,cantoneira_escolhida.t_mm,parafuso.diametro_mm,gamma_a2) #Da cantoneira
        R11 = resistencia_cisalhamento_secao_liquida(1,perfil,perfil.h,cantoneira_escolhida,perfil.t_w,parafuso.diametro_mm,gamma_a2) #Do perfil

        R12 = resistencia_block(corte,material,cantoneira_escolhida,cantoneira_escolhida.comprimento,cantoneira_escolhida.t_mm,parafuso.diametro_mm,gamma_a2) #Da cantoneira


        Esf_s_d  = np.sqrt(V_s_d**2 + T_s_d**2)
        f1 = R1 - Esf_s_d
        f2 = R2 - Esf_s_d
        f3 = R3 - Esf_s_d
        f4 = R4 - Esf_s_d
        f5 = R5 - Esf_s_d
        f6 = R6 - Esf_s_d
        f7 = R7 - Esf_s_d
        f8 = R8 - Esf_s_d
        f9 = R9 - Esf_s_d
        f10 = R10 - Esf_s_d
        f11 = R11 - Esf_s_d
        f12 = R12 - Esf_s_d
        dif_x = cantoneira_escolhida.disp_vertices_chapa["x (mm)"].max() - cantoneira_escolhida.disp_parafusos["x (mm)"].max()
        dif_z = perfil.h_w - cantoneira_escolhida.disp_vertices_chapa["z (mm)"].max() 

        if dif_x > cantoneira_escolhida.f_b_lado and dif_z > 0 and Esf_s_d <= R1 and  f2 > 0 and f3 > 0 and f4 > 0 and f5 > 0 and f6 > 0 and f7 > 0 and f8 > 0 and f9 > 0 and f10 > 0 and f11 > 0 and f12 > 0 :#and f13 > 0:
            solucion.append([cantoneira_escolhida.nome,parafuso.diametro_pol,parafuso,cantoneira_escolhida,cantoneira_escolhida.disp_vertices_chapa,cantoneira_escolhida.disp_parafusos])   
            #(f1/R1)*100,(f2/R2)*100,(f3/R3)*100,(f4/R4)*100,(f5/R5)*100,(f6/R6)*100,(f7/R7)*100,(f8/R8)*100,(f9/R9)*100,(f10/R10)*100,(f11/R11)*100,(f12/R12)*100
            break
            if j < len(diametros)-1:
                j = j+1
            else:  
                j = 0
                i = i+1  
        else:
            if j < len(diametros)-1:
                j = j+1
            else:  
                j = 0
                i = i+1
    return solucion


            



