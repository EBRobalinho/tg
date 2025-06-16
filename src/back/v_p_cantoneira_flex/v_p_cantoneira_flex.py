import pandas as pd
from back.materials_constants import DIMENSOES_CANTONEIRAS
import numpy as np
from back.design_functions import (resistencia_parafuso_tração,
                                   resistencia_parafuso_cisalhamento,solicitante_parafuso_tração,
                                   solicitante_parafuso_cisalhamento,
                                    resistencia_total, resistencia_rasgamento_esmagamento,
                                    resistencia_cisalhamento, resistencia_block
                                   )
from back.norms import (dist_min_borda_pol, furo_padrao_pol, pol_to_mm)
from back.logs import registrar_marcha, registrar_marcha2, registrar_tabela
from back.domain import cantoneira
from back.domain.parafuso import Parafuso
from back.domain.perfil import Perfil
from back.domain.cantoneira import Cantoneira
from back.domain.materials import Aço


def arranjo_cantoneira_parafusos(Cantoneira : Cantoneira, perfil : Perfil, N_parafusos : int) -> list|None:
    # Define parâmetros com base no tipo de perfil
    nome = perfil.nome
    
    valor_w = int(nome.split('_')[1].replace('x', '_').split('_')[0])

    if valor_w in [150, 200]:
        Cantoneira.f_b = 25   #Distância do furo a borda vertical da cantoneira
        Cantoneira.f_f = 60   #Distância do furo ao furo
        Cantoneira.f_l = 45
    else:
        Cantoneira.f_b = 40  #Distância do furo a borda vertical da cantoneira
        Cantoneira.f_f = 75   #Distância do furo ao furo
        Cantoneira.f_l = 45   #Distância do furo ao outro lado da cantoneira (dobra da cantoneira)

    registrar_marcha("\nConsiderações da AISC Steel construction manual, sobre a ligação ser flexível.")

    if Cantoneira.f_l > pol_to_mm(3):
        registrar_marcha(f"\nA distância  do furo a dobra da cantoneira {Cantoneira.f_l} é maior do que 3 polegadas, a ligação não é flexível e precisa ser considerada a excentricidade.")
        return ["Não há arranjo viável para a ligação ser flexível."]

    registrar_marcha(f"A distância  do furo a dobra da cantoneira {Cantoneira.f_l} é menor do que 3 polegadas, a ligação é flexível e não precisa ser considerada a excentricidade.")

    em_mm= pol_to_mm("5/8")

    if Cantoneira.t_mm  > em_mm:
        registrar_marcha(f"\nComo a espessura da cantoneira {Cantoneira.t_mm} mm é maior do que 5/8 polegadas = {em_mm} mm, a ligação não é flexível.")
        return ["Não há arranjo viável para a ligação ser flexível."]

    registrar_marcha(f"\nComo a espessura da cantoneira {Cantoneira.t_mm} mm é menor do que 5/8 polegadas = {em_mm} mm, a ligação é flexível.")

    #self.f_b_lado = 30  #Distância do furo a borda horizontal da cantoneira
    t = Cantoneira.t_mm

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

def dim_cant_parafuso(T : float, V : float, material_cantoneira : Aço, perfil : Perfil, parafuso : Parafuso, N_parafusos : int, gamma: list) -> tuple[Cantoneira, Parafuso] | list[str]:
    corte=parafuso.planos_de_corte
    registrar_marcha("Dimensionamento da ligação que faz conexão da viga via cantoneira aparafusada no pilar e na viga\n") 
    gamma_a2=gamma[1]
    i=j=0
    while (i < len(DIMENSOES_CANTONEIRAS)-1) and (j < len(parafuso.diametro_pol)):  
        nome_cantoneira = DIMENSOES_CANTONEIRAS[i]
        cantoneira_escolhida = cantoneira.Cantoneira(*DIMENSOES_CANTONEIRAS[i][nome_cantoneira],material_cantoneira)
        criteiro_flexivel = arranjo_cantoneira_parafusos(cantoneira_escolhida, perfil, N_parafusos)

        if criteiro_flexivel == ["Não há arranjo viável para a ligação ser flexível."]:
                return ["A ligação não aguenta a solicitação desejada."]

        registrar_tabela("Vértices dos parafusos de uma aba da cantoneira", cantoneira_escolhida.disp_parafusos)

        cantoneira_escolhida.vertices_chapa()
        d = parafuso.diametro_mm[j]
        parafuso.d = d
        d_pol = parafuso.diametro_pol[j]

        registrar_marcha2(f"Interação {j} : cálculo com parafuso de diâmetro {d} pol")
        registrar_marcha2(f"\nInteração {i} para a cantoneira {cantoneira_escolhida.nome}\n")

        R1 = N_parafusos*resistencia_total(parafuso,gamma)

        d_furo_padrao = furo_padrao_pol(d)
        R2 = resistencia_rasgamento_esmagamento(corte,cantoneira_escolhida.material,cantoneira_escolhida,cantoneira_escolhida.t_mm,cantoneira_escolhida.f_f - (d_furo_padrao),d,gamma_a2) #Da cantoneira f_f
        R3 = resistencia_rasgamento_esmagamento(corte,cantoneira_escolhida.material,cantoneira_escolhida,cantoneira_escolhida.t_mm,cantoneira_escolhida.f_b - 0.5*(d_furo_padrao),d,gamma_a2) #Da cantoneira f_b

        R4 = resistencia_rasgamento_esmagamento(1,perfil.material,cantoneira_escolhida,perfil.t_w,cantoneira_escolhida.f_f - (d_furo_padrao),d,gamma_a2) #Do Perfil f_f
        R5 = resistencia_rasgamento_esmagamento(1,perfil.material,cantoneira_escolhida,perfil.t_w,cantoneira_escolhida.b_mm + 10,d,gamma_a2) #Do Perfil f_b (10mm minimo de distância do furo ao borda do perfil)

        R6 = resistencia_cisalhamento(corte,cantoneira_escolhida.material,cantoneira_escolhida.comprimento,cantoneira_escolhida,cantoneira_escolhida.t_mm,d,gamma) #Da cantoneira
        R7 = resistencia_cisalhamento(1,perfil.material,perfil.h,cantoneira_escolhida,perfil.t_w,d,gamma) #Do perfil

        R8 = resistencia_block(corte,cantoneira_escolhida,cantoneira_escolhida.t_mm,d,gamma_a2) #Da cantoneira

        Esf_s_d  = np.sqrt(V**2 + T**2)
        registrar_marcha(f"O esforço solicitante de cálculo é dado por: np.sqrt(V**2 + T**2) = {Esf_s_d} kN")
        reacoes = [R1, R2, R3, R4, R5, R6, R7, R8]
        f_list = [r - Esf_s_d for r in reacoes]

        dif_x = cantoneira_escolhida.disp_vertices_chapa["x (mm)"].max() - cantoneira_escolhida.disp_parafusos["x (mm)"].max()  #Para que obeceça-se a distância mínima pedida por norma entre o centro de furação e a borda da cantoneira
        dif_z = perfil.h_w - cantoneira_escolhida.disp_vertices_chapa["z (mm)"].max() # Para que a cantoneira escolhista esteja localizada entre as mesas do perfil

        #Resistentes do parafuso para tração e cisalhamento
        r_p_t=resistencia_parafuso_tração(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso a tração = {r_p_t} KN \n")

        r_p_v=resistencia_parafuso_cisalhamento(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso a cisalhamento = {r_p_v} KN \n")

        #Solicitantes no parafuso para tração e cisalhamento
        s_p_t = solicitante_parafuso_tração(T,2*N_parafusos)
        registrar_marcha(f"Solicitante de tração pura no parafuso = {s_p_t} KN \n")
        s_p_v = solicitante_parafuso_cisalhamento(V,2*N_parafusos)
        registrar_marcha(f"Solicitante de cisalhamento no parafuso = {s_p_v} KN \n")


        registrar_marcha(
            f"{perfil.h_w} - {cantoneira_escolhida.disp_vertices_chapa['z (mm)'].max()} = {dif_z} mm "
            "(distância vertical entre a mesa superior do perfil e o topo da cantoneira, deve ser positiva para encaixe correto)"
        )

        registrar_marcha(
            f"{cantoneira_escolhida.disp_vertices_chapa['x (mm)'].max()} - {cantoneira_escolhida.disp_parafusos['x (mm)'].max()} = {dif_x} mm "
            f"(distância da borda da cantoneira ao centro do furo mais próximo, deve ser maior que o mínimo normativo = {dist_min_borda_pol(parafuso.d_pol)}, caso esteja negativo significa que o parafuso não está dentro da cantoneira.)"
        )

        registrar_marcha(f"f_list = {[f'{r} - {Esf_s_d} = {r - Esf_s_d}' for r in reacoes]} (cada valor deve ser > 0 para atender todas as condições da norma)")

        #Curva de interação (Sendo aplicada considerando que todos os parafusos estão solicitados conforme o parafuso mais solicitado)
        curva=(((s_p_t)/r_p_t)**2 + (s_p_v/r_p_v)**2)
        registrar_marcha(f"\nCalculo da circunferência de interação, conforme previsto em 6.3.3.4 da 8800:2024 {curva}=((({s_p_t})/{r_p_t})**2 + ({s_p_v}/{r_p_v})**2)")

        if dif_x > dist_min_borda_pol(d_pol) and dif_z > 0 and min(f_list) > 0 and curva <=1:
            registrar_marcha(f'\n{curva}<=1 : Solução encontrada.')
            solucion = [cantoneira_escolhida,parafuso] 
            return solucion
        else:
            if dif_x<0:
                j = 0
                i = i+1  
            else:
                if j < len(parafuso.diametro_mm)-1:
                    j = j+1
                else:  
                    j = 0
                    i = i+1  
    return ["A ligação não aguenta a solicitação desejada."]


            



