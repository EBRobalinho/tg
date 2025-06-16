import numpy as np
from math import ceil
from back.norms import criterio_min_solda_filete
from back.logs import registrar_marcha
from back.cantoneira_flex import dim_cant_parafuso
from back.domain.materials import Aço
from back.domain.perfil import Perfil
from back.domain.solda import Solda
from back.domain.parafuso import Parafuso
from back.domain.cantoneira import Cantoneira
from back.weld_design import tensao_momento, tensao_cisalhante_filete_cantoneira

def dim_cant_solda(T: float, V: float, material: Aço, perfil: Perfil, solda: Solda, gamma: list, parafuso: Parafuso) -> list[str] | tuple[Cantoneira, int, Parafuso] | None:
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

        n_p_max = max(int((h_w - margem) // espacamento), 2)
        
        N = n_p_max

        S = dim_cant_parafuso(T,V,material,perfil,parafuso,N,gamma)
        # Se for uma lista e todos os itens forem strings, é erro
        if isinstance(S, list) and all(isinstance(x, str) for x in S):
            return S
        elif isinstance(S, tuple) and isinstance(S[0], Cantoneira) and isinstance(S[1], Parafuso):
            cantoneira_escolhida = S[0]
            parafuso = S[1]
            registrar_marcha("\nDimensionamento da solda")
            #Dimensionamento da solda:
            #Pois há duas cantoneiras, logo a tensão sobre a qual a solda de cada uma está submetida advém de metade do valor dos esfoços solicitantes
            esf_V_cant = V/2
            esf_T_cant = T/2

            Esf_s_d  = np.sqrt(esf_V_cant**2 + esf_T_cant**2)

            tal_r1 = solda.f_uw_mpa*0.6/gamma[1]     #Mpa    #Tabela 9, item 6.2.5.1 da NBR 8800:2024 (Resistência da solda)
            registrar_marcha(f"\ntal_r1 (solda) = solda.f_uw*0.6/gamma[1] = {solda.f_uw_mpa}*0.6/{gamma[1]} = {tal_r1} MPa [Tabela 9, item 6.2.5.1 da NBR 8800:2024]")

            tal_r2 = cantoneira_escolhida.material.f_u*0.6/gamma[0]      #Letra b do item 6.5.5 da NBR 8800:2024 (Ruptura do metal base - cantoneira)
            registrar_marcha(f"\ntal_r2 (cantoneira) = cantoneira_escolhida.f_u*0.6/gamma[0] = {cantoneira_escolhida.material.f_u}*0.6/{gamma[0]} = {tal_r2} MPa [Letra b do item 6.5.5 da NBR 8800:2024]")

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

            esp_final = ceil(esp_final) #mm
            registrar_marcha(f"esp_final (arredondado para cima) = {esp_final} mm")

            return (cantoneira_escolhida,esp_final,parafuso)

    except IndexError:
        raise ValueError("A ligação não aguenta a solicitação desejada.")