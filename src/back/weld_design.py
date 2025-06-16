import numpy as np
from back.logs import registrar_marcha
from back.domain.cantoneira import Cantoneira
from back.norms import criterio_min_solda_filete
from math import ceil
from back.domain.perfil import Perfil
from back.domain.solda import Solda

#Soldas

def momento_inercia_soldas_perfil(perfil: Perfil) -> float:
    meia_altura = perfil.h / 2  # mm
    largura_mesa = perfil.b_f
    qtd = 2
    Ix1 = qtd * (largura_mesa * 0.7 * (meia_altura ** 2))
    Ix2 = qtd * ((largura_mesa - perfil.t_w) * 0.7 * (meia_altura - perfil.t_f) ** 2)
    Ix3 = qtd * (0.7 * (perfil.h - 2 * perfil.t_f) ** 3) / 12

    return Ix1 + Ix2 + Ix3 #mm^3*(Para 1mm de espessura)

def tensao_cisalhante_momento_filete(perfil,M,altura):
    #A ideia é calcular a tensão de cisalhmento máxima advinda do momento que nem é feito no Livro do Pfeil:
    momento_inercia = momento_inercia_soldas_perfil(perfil)
    return M*(altura*0.5)/momento_inercia         #kN/mm*(Para 1mm de espessura)

def tensao_cisalhante_cortante_filete(perfil,V):
    # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
    qtd=2
    #A ideia é calcular a tensão de cisalhmento máxima advinda do cortante que nem é feito no Livro do Pfeil (considera-se então que toda a cisalhante do cortante é resistida pela alma)
    return V/qtd/0.7/perfil.h_w       #kN/(mm*(Para 1mm de espessura))

def tensao_cisalhante_normal_filete(perfil,N):
    # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
    qtd=2
    comprimento=qtd*(2*perfil.b_f + perfil.h - 2*perfil.t_f - perfil.t_w)

    return N/comprimento/0.7        #kN/(mm*(Para 1mm de espessura))    

    

def tensao_cisalhante_filete_cantoneira(cantoneira: Cantoneira, V: float) -> float:
    #Quem resistente ao esforço cortante na solda é a componente vertical + 2*horizontal da solda (o valor é vezes 2 pq há dois braços de cantoneira soldados)
    comprimento = cantoneira.comprimento + 2 * cantoneira.b_mm

    return V / comprimento  # kN/mm

def momento_polar_inercia(cantoneira: Cantoneira) -> float:
    registrar_marcha("Calculo do momento polar de inércia para uma solda filete de 1 mm")
    I_p = ( (8*((cantoneira.b_mm)**3)) + 6*(cantoneira.b_mm)*(cantoneira.comprimento) + (cantoneira.comprimento)**3 )/12  - ((cantoneira.b_mm**4)/(2*cantoneira.b_mm + cantoneira.comprimento)) #mm^3
    registrar_marcha(f"I_p = ( (8*({cantoneira.b_mm}**3)) + 6*{cantoneira.b_mm}*{cantoneira.comprimento} + {cantoneira.comprimento}**3 )/12  - (({cantoneira.b_mm}**4)/(2*{cantoneira.b_mm} + {cantoneira.comprimento})) = {I_p} mm^3")  
    return I_p #mm^4/mm

def centroide_solda(cantoneira: Cantoneira) -> float:
    registrar_marcha("Cálculo da excentricidade e borda da cantoneira que fica na viga") 
    e = (cantoneira.b_mm**2)/(2*cantoneira.b_mm + cantoneira.comprimento) #mm
    registrar_marcha(f"e = {e} = ({cantoneira.b_mm}**2)/(2*{cantoneira.b_mm} + {cantoneira.comprimento}) mm")
    return e


def torcao_momento(V: float, e: float) -> float:
    registrar_marcha("Cálculo do momento advindo da excentricidade da cortante na ligação") 
    M = V*e    #kN*mm
    registrar_marcha(f"Momento {M} = {V}*{e} kN")
    return M


def tensao_momento(V: float, cantoneira: Cantoneira) -> float:
    registrar_marcha("Cálculo da tensão advinda do momento de torção sobre a qual a solda da cantoneira está submetida") 
    I_p = momento_polar_inercia(cantoneira) #mm^3

    e = centroide_solda(cantoneira)

    M = torcao_momento(V,e) #kN*mm

    braco = np.sqrt((cantoneira.comprimento*0.5)**2 + (cantoneira.b_mm - e)**2) #mm

    tensao = M*braco/I_p  #kN/mm  = Mpa*m
    registrar_marcha(f"Tensão advinda do momento de torção {tensao} = {M}*np.sqrt(({cantoneira.comprimento}*0.5)**2 + ({cantoneira.b_mm - e})**2)/({I_p}) kN")
    return tensao


#Cálculo de espessura mínima de solda necessária:


def espessura_solda(M: float, V: float, T: float, solda: Solda, perfil: Perfil, espessura_chapa: float, gamma: list) -> int:
    registrar_marcha("Cálculo da espessura mínima de solda necessária segundo NBR 8800:2024")

    tal_r1 = solda.f_uw_mpa*0.6/gamma[1]     #Mpa    #Tabela 9, item 6.2.5.1 da NBR 8800:2024 (Relativa a tensão resistida pela solda)
    registrar_marcha(f"tal_r1 = {solda.f_uw_mpa} * 0.6 / {gamma[1]} = {tal_r1:.3f} MPa")
    tal_r2 = perfil.f_u*0.6/gamma[0]      #Letra b do item 6.5.5 da NBR 8800:2024 (relativa a ruptura do metal base)
    registrar_marcha(f"tal_r2 = {perfil.f_u} * 0.6 / {gamma[0]} = {tal_r2:.3f} MPa")

    tal_r = min(tal_r1, tal_r2)
    registrar_marcha(f"tal_r = min({tal_r1:.3f}, {tal_r2:.3f}) = {tal_r:.3f} MPa")

    tal_m = tensao_cisalhante_momento_filete(perfil, M, perfil.h_w*0.5)
    tal_v = tensao_cisalhante_cortante_filete(perfil, V)
    tal_n = tensao_cisalhante_normal_filete(perfil, T)

    tal_s = np.sqrt((tal_m)**2 + (tal_v)**2 + (tal_n)**2)*1000   #Tensão solicitante em Mpa*mm    
    registrar_marcha(f"tal_s = sqrt({tal_m:.3f}^2 + {tal_v:.3f}^2 + {tal_n:.3f}^2) * 1000 = {tal_s:.3f} MPa*mm")

    esp = tal_s / tal_r
    registrar_marcha(f"esp = {tal_s:.3f} / {tal_r:.3f} = {esp:.3f} mm")

    esp_metal_base = min(espessura_chapa, perfil.t_w)
    registrar_marcha(f"esp_metal_base = min({espessura_chapa}, {perfil.t_w}) = {esp_metal_base}")
    esp_minima = criterio_min_solda_filete(esp_metal_base)
    registrar_marcha(f"espessura minima prevista em norma = {esp_minima}")

    esp_final = max(esp_minima, esp)
    registrar_marcha(f"esp_final = max({esp_minima}, {esp:.3f}) = {esp_final:.3f} mm (antes de arredondar)")

    esp_final =ceil(esp_final) #mm
    registrar_marcha(f"esp_final (arredondado para cima) = {esp_final} mm")

    return esp_final