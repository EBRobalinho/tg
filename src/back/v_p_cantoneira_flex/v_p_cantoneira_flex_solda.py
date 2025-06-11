import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from back.design_functions import * 
from back.v_p_cantoneira_flex.v_p_cantoneira_flex import dim_cant_parafuso

def tensao_cisalhante_filete_cantoneira(cantoneira,V):
    #Quem resistente ao esforço cortante na solda é a componente vertical + 2*horizontal da solda (o valor é vezes 2 pq há dois braços de cantoneira soldados)
    comprimento=cantoneira.comprimento + 2*cantoneira.b_mm 

    return V/comprimento #kN/mm

def momento_polar_inercia(cantoneira):
    registrar_marcha("Calculo do momento polar de inércia para uma solda filete de 1 mm")
    I_p = ( (8*((cantoneira.b_mm)**3)) + 6*(cantoneira.b_mm)*(cantoneira.comprimento) + (cantoneira.comprimento)**3 )/12  - ((cantoneira.b_mm**4)/(2*cantoneira.b_mm + cantoneira.comprimento)) #mm^3
    registrar_marcha(f"I_p = ( (8*({cantoneira.b_mm}**3)) + 6*{cantoneira.b_mm}*{cantoneira.comprimento} + {cantoneira.comprimento}**3 )/12  - (({cantoneira.b_mm}**4)/(2*{cantoneira.b_mm} + {cantoneira.comprimento})) = {I_p} mm^3")  
    return I_p #mm^4/mm

def centroide_solda(cantoneira):
    registrar_marcha(f"Cálculo da excentricidade e borda da cantoneira que fica na viga") 
    e = (cantoneira.b_mm**2)/(2*cantoneira.b_mm + cantoneira.comprimento) #mm
    registrar_marcha(f"e = {e} = ({cantoneira.b_mm}**2)/(2*{cantoneira.b_mm} + {cantoneira.comprimento}) mm")
    return e


def torcao_momento(V,e):
    registrar_marcha(f"Cálculo do momento advindo da excentricidade da cortante na ligação") 
    M = V*e    #kN*mm
    registrar_marcha(f"Momento {M} = {V}*{e} kN")
    return M


def tensao_momento(V,cantoneira):
    registrar_marcha(f"Cálculo da tensão advinda do momento de torção sobre a qual a solda da cantoneira está submetida") 
    I_p = momento_polar_inercia(cantoneira) #mm^3

    e = centroide_solda(cantoneira)

    M = torcao_momento(V,e) #kN*mm

    braco = np.sqrt((cantoneira.comprimento*0.5)**2 + (cantoneira.b_mm - e)**2) #mm

    tensao = M*braco/I_p  #kN/mm  = Mpa*m
    registrar_marcha(f"Tensão advinda do momento de torção {tensao} = {M}*np.sqrt(({cantoneira.comprimento}*0.5)**2 + ({cantoneira.b_mm - e})**2)/({I_p}) kN")
    return tensao

def dim_cant_solda(T,V,material,perfil,solda,gamma,parafuso):
    try:
        # A ideia é usar a cantoneira que o método parafusado usou, para depois usar as dimensões da cantoneira para dimensionar a ligação soldada
        registrar_marcha("\nDimensionamento de uma ligação flexível atraves de cantoneira soldada na alma da viga e na mesa do pilar")
        registrar_marcha("\nO dimensionamento da cantoneira será feito como se fosse uma ligação toda parafusada, sendo calculada a solda posteriormente")
        h_w = perfil.h_w  # altura útil

        # ⬇️ Aqui entra sua regra condicional
        if perfil.nome.startswith("W_150x"):
            margem = 2 * 25
            espacamento = 60
        else:
            margem = 2 * 30
            espacamento = 75

        n_p_min = 1
        n_p_max = max(int((h_w - margem) // espacamento), 2)
        
        N = n_p_max

        S = dim_cant_parafuso(T,V,material,perfil,parafuso,N,gamma)
        if isinstance(S[0], str):  # se for string, é um erro
            return S  # lança a string como erro
        registrar_marcha("\nDimensionamento da solda")
        #Dimensionamento da solda:
        cantoneira_escolhida = S[0]
        parafuso = S[1] #usado para a ligação com parafuso e solda
        #Pois há duas cantoneiras, logo a tensão sobre a qual a solda de cada uma está submetida advém de metade do valor dos esfoços solicitantes
        esf_V_cant = V/2
        esf_T_cant = T/2

        Esf_s_d  = np.sqrt(esf_V_cant**2 + esf_T_cant**2)

        tal_r1 = solda.f_uw_mpa*0.6/gamma[1]     #Mpa    #Tabela 9, item 6.2.5.1 da NBR 8800:2024 (Resistência da solda)
        registrar_marcha(f"\ntal_r1 (solda) = solda.f_uw*0.6/gamma[1] = {solda.f_uw_mpa}*0.6/{gamma[1]} = {tal_r1} MPa [Tabela 9, item 6.2.5.1 da NBR 8800:2024]")

        tal_r2 = cantoneira_escolhida.f_u*0.6/gamma[0]      #Letra b do item 6.5.5 da NBR 8800:2024 (Ruptura do metal base - cantoneira)
        registrar_marcha(f"\ntal_r2 (cantoneira) = cantoneira_escolhida.f_u*0.6/gamma[0] = {cantoneira_escolhida.f_u}*0.6/{gamma[0]} = {tal_r2} MPa [Letra b do item 6.5.5 da NBR 8800:2024]")

        tal_r3 = perfil.f_u*0.6/gamma[0]   #Ruptura do metal base - perfil
        registrar_marcha(f"\ntal_r3 (perfil) = perfil.f_u*0.6/gamma[0] = {perfil.f_u}*0.6/{gamma[0]} = {tal_r3} MPa [Letra b do item 6.5.5 da NBR 8800:2024]")

        tal_r = min(tal_r1, tal_r2, tal_r3)   #Menor resistência dos metais envolvidos na ligação
        registrar_marcha(f"\ntal_r = min({tal_r1}, {tal_r2}, {tal_r3}) = {tal_r} MPa (Menor resistência dos metais envolvidos na ligação)")       

        tal_m = tensao_momento(V,cantoneira_escolhida) #kN/mm = Mpa*m
        tal_v = tensao_cisalhante_filete_cantoneira(cantoneira_escolhida,Esf_s_d)  #kN/mm = Mpa*m

        tal_s = np.sqrt((tal_m)**2 + (tal_v)**2 )*1000   #Tensão solicitante em Mpa*mm    

        registrar_marcha(f"\ntal_r = min({tal_m}, {tal_v})*1000 = {tal_s} MPa*mm (Menor resistência dos metais envolvidos na ligação)")       

        esp_t = tal_s/tal_r #mm
        registrar_marcha(f"\nesp (espessura do filete (t) de solda) = tal_s / tal_r = {tal_s} / {tal_r} = {esp_t} mm (espessura necessária da solda para resistir à solicitação)")

        #Perna da solda 
        esp=esp_t*np.sqrt(2)
        registrar_marcha(f"\nesp (espessura da perna (b) de solda) = {esp}={esp_t}*np.sqrt(2) mm (espessura necessária da solda para resistir à solicitação)")

        esp_metal_base = perfil.t_w #mm
        esp_minima = criterio_min_solda_filete(esp_metal_base)
        registrar_marcha(f"espessura minima prevista em norma = {esp_minima}")

        esp_final = max(esp_minima,esp)
        registrar_marcha(f"esp_final = max({esp_minima}, {esp:.3f}) = {esp_final:.3f} mm (antes de arredondar)")

        esp_final = math.ceil(esp_final) #mm
        registrar_marcha(f"esp_final (arredondado para cima) = {esp_final} mm")

        return [cantoneira_escolhida,esp_final,parafuso]

    except IndexError:
        raise ValueError("A ligação não aguenta a solicitação desejada.")