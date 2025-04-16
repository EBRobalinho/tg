import pandas as pd
import numpy as np
from design_functions import * 

def arranjo_cantoneira_parafusos(Cantoneira, perfil, N_parafusos):
    # Define parâmetros com base no tipo de perfil
    nome = perfil.nome
    
    valor_w = int(nome.split('_')[1].replace('x', ''))

    if valor_w in [150, 200]:
        Cantoneira.f_b = 30   #Distância do furo a borda vertical da cantoneira
        Cantoneira.f_f = 60   #Distância do furo ao furo
        Cantoneira.f_l = 45
    else:
        Cantoneira.f_b = 40  #Distância do furo a borda vertical da cantoneira
        Cantoneira.f_f = 75   #Distância do furo ao furo
        Cantoneira.f_l = 45   #Distância do furo ao outro lado da cantoneira

    #self.f_b_lado = 30  #Distância do furo a borda horizontal da cantoneira
    b = Cantoneira.b_mm
    t = Cantoneira.t_mm
    r = Cantoneira.R_conc

    # Gera posições dos parafusos ao longo da altura da seção
    parafusos = []
    z = Cantoneira.f_b
    while len(parafusos) < N_parafusos :
        parafusos.append((Cantoneira.f_l, t, z))
        z += Cantoneira.f_f

    # Cria DataFrame com os pontos
    data = {
        "parafuso": list(range(1, len(parafusos) + 1)),
        "x (mm)": [p[0] for p in parafusos],
        "y (mm)": [p[1] for p in parafusos],
        "z (mm)": [p[2] for p in parafusos],
    }
    Cantoneira.disp_parafusos = pd.DataFrame(data)

    Cantoneira.comprimento = parafusos[-1][2] + Cantoneira.f_b  # em mm

#Resistência das peças para Esmagamento e rasgamento

def resistencia_rasgamento_esmagamento(corte,material,cantoneira,espessura,distancia,diametro,gamma): #Item 6.3.3.3 da NBR 8800:2024
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    resistencia1 = corte*2.4*material.f_u*espessura*diametro*N_parafusos/gamma   #Sair o resultado em N
    resistencia2 = 1.2*corte*material.f_u*espessura*distancia*N_parafusos/gamma   
    resistencia=min(resistencia1,resistencia2)
    return resistencia/1000 #Sair o resultado em kN

def resistencia_cisalhamento(corte,material,comprimento,cantoneira,espessura,diametro,gamma):   #Item 6.5.5 da NBR 8800:2024
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]

    N_parafusos =cantoneira.disp_parafusos.shape[0]

    resistencia1 = corte*0.6*material.f_y*comprimento*espessura/gamma_a1    #Escoamento da seção bruta
    resistencia2 = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2   #Ruptura da seção líquida

    resistencia=min(resistencia1,resistencia2)
    return resistencia/1000 #Sair o resultado em kN

def resistencia_block(corte,material,cantoneira,comprimento,espessura,diametro,gamma):  #Item 6.5.6 da NBR 8800:2024
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    A_gv = espessura*(cantoneira.comprimento - cantoneira.f_b)  #Area bruta da cantoneira sujeita a cisalhamento (O comprimento pode ser o espaçamento entre os parafusos ou )
    A_nv = espessura*(cantoneira.comprimento - cantoneira.f_b) - (N_parafusos-0.5)*(furo_padrao_pol(diametro))*espessura  #Area líquida da cantoneira sujeita a cisalhamento
    A_nt = (cantoneira.f_b - 0.5*(furo_padrao_pol(diametro)))*espessura
    C_ts=1  # Sé deixa de ser 1, quando a tensão na área líquida não for uniforme 
    resistencia = min(0.6*material.f_u*A_nv + C_ts*material.f_u*A_nt,0.6*material.f_y*A_gv + C_ts*material.f_u*A_nt)*corte/gamma   #Sair o resultado em N  

    return resistencia/1000 #Sair o resultado em kN

def dim_cant_parafuso(T,V,cantoneiras_dict,material,perfil,parafuso,N_parafusos,gamma):
    rosca=parafuso.rosca
    corte=parafuso.planos_de_corte
    gamma_a2=gamma[0]
    i=j=0
    while (i < len(cantoneiras_dict)-1) and (j < len(parafuso.diametros_disponiveis)):  
        cantoneira_escolhida = cantoneiras_dict[i]
        cantoneira_escolhida.material(material)

        arranjo_cantoneira_parafusos(cantoneira_escolhida, perfil, N_parafusos)

        cantoneira_escolhida.vertices_chapa(perfil)
        d = parafuso.diametros_disponiveis[j]
        parafuso.diametro(d)

        R1 = N_parafusos*resistencia_total(parafuso,gamma)

        R2 = resistencia_rasgamento_esmagamento(corte,cantoneira_escolhida,cantoneira_escolhida,cantoneira_escolhida.t_mm,cantoneira_escolhida.f_f - (furo_padrao_pol(parafuso.diametro_mm)),parafuso.diametro_mm,gamma_a2) #Da cantoneira f_f
        R3 = resistencia_rasgamento_esmagamento(corte,cantoneira_escolhida,cantoneira_escolhida,cantoneira_escolhida.t_mm,cantoneira_escolhida.f_b - 0.5*(furo_padrao_pol(parafuso.diametro_mm)),parafuso.diametro_mm,gamma_a2) #Da cantoneira f_b

        R4 = resistencia_rasgamento_esmagamento(1,perfil,cantoneira_escolhida,perfil.t_w,cantoneira_escolhida.f_f - (furo_padrao_pol(parafuso.diametro_mm)),parafuso.diametro_mm,gamma_a2) #Do Perfil f_f
        R5 = resistencia_rasgamento_esmagamento(1,perfil,cantoneira_escolhida,perfil.t_w,cantoneira_escolhida.b_mm + 10,parafuso.diametro_mm,gamma_a2) #Do Perfil f_b (10mm minimo de distância do furo ao borda do perfil)

        R6 = resistencia_cisalhamento(corte,cantoneira_escolhida,cantoneira_escolhida.comprimento,cantoneira_escolhida,cantoneira_escolhida.t_mm,parafuso.diametro_mm,gamma) #Da cantoneira
        R7 = resistencia_cisalhamento(1,perfil,perfil.h,cantoneira_escolhida,perfil.t_w,parafuso.diametro_mm,gamma) #Do perfil

        R8 = resistencia_block(corte,material,cantoneira_escolhida,cantoneira_escolhida.comprimento,cantoneira_escolhida.t_mm,parafuso.diametro_mm,gamma_a2) #Da cantoneira

        Esf_s_d  = np.sqrt(V**2 + T**2)
        reacoes = [R1, R2, R3, R4, R5, R6, R7, R8]
        f_list = [r - Esf_s_d for r in reacoes]

        dif_x = cantoneira_escolhida.disp_vertices_chapa["x (mm)"].max() - cantoneira_escolhida.disp_parafusos["x (mm)"].max()  #Para que obeceça-se a distância mínima pedida por norma entre o centro de furação e a borda da cantoneira
        dif_z = perfil.h_w - cantoneira_escolhida.disp_vertices_chapa["z (mm)"].max() # Para que a cantoneira escolhista esteja localizada entre as mesas do perfil

        if dif_x > dist_min_borda_pol(parafuso.diametro_pol) and dif_z > 0 and min(f_list) > 0:
            solucion = [cantoneira_escolhida,parafuso] 
            return solucion
        else:
            if j < len(parafuso.diametros_disponiveis)-1:
                j = j+1
            else:  
                j = 0
                i = i+1  
    return ["A ligação não aguenta a solicitação desejada."]


            



