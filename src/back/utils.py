import numpy as np
import pandas as pd
from back.norms import furo_padrao_pol, parametro_b
from back.domain.cantoneira import Cantoneira
from back.domain.materials import Aço
from back.domain.chapa import Chapa
from logs import registrar_marcha



def resistencia_cisalhamento_chapa(corte,material,comprimento,N_parafusos,espessura,diametro,gamma):   #Item 6.5.5 da NBR 8800:2024
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]
    registrar_marcha("\nVerificação cisalhamento segundo Item 6.5.5 da NBR 8800:2024")
    
    resistencia1 = corte*0.6*material.f_y*comprimento*espessura/gamma_a1    #Escoamento da seção bruta
    registrar_marcha(f"Resistência do cisalhamento da chapa segundo o escoamento da seção bruta: resistencia_1 = {corte*0.6*material.f_y*comprimento*espessura/gamma_a1} N")
    
    resistencia2 = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2   #Ruptura da seção líquida
    registrar_marcha(f"Resistência do cisalhamento da chapa segundo a ruptura da seção líquida: resistencia_2 = {corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2} N")
    
    resistencia=min(resistencia1,resistencia2)
    registrar_marcha(f"Resistência do cisalhamento da chapa segundo o menor valor entre os dois: resistencia = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN


def criterio_cisalhamento_chapa(chapa,s_p_v,espessura_chapa,ver_parafuso,parafuso,material,gamma):
    #Teste e relação a escoamento da seção bruta e ruptura da seção líquida
    corte = parafuso.planos_de_corte # Há 1 plano de corte na chapa
    N_parafusos_coluna = (ver_parafuso["x (mm)"] == ver_parafuso["x (mm)"].iloc[0]).sum()
    comprimento = chapa.df['y (mm)'].max()

    res_cisalhamento_chapa = resistencia_cisalhamento_chapa(corte,material,comprimento,N_parafusos_coluna,espessura_chapa,parafuso.diametro_mm,gamma)
    if res_cisalhamento_chapa > s_p_v:
        registrar_marcha(f"Verificação: resistência ao cisalhamento {res_cisalhamento_chapa:.2f} kN > solicitante {s_p_v:.2f} kN.\nA chapa aguenta a solicitação para cisalhamento.")
        return [1,"A chapa aguenta a solicitação para cisalhamento."]
    else:
        registrar_marcha(f"Verificação: resistência ao cisalhamento {res_cisalhamento_chapa:.2f} kN <= solicitante {s_p_v:.2f} kN.\nA chapa não aguenta a solicitação desejada para cisalhamento.")
        return [0,"A chapa não aguenta a solicitação desejada para cisalhamento."]


#Resistência das peças para Esmagamento e rasgamento

def resistencia_rasgamento_esmagamento(corte: int, material: Aço, cantoneira: Cantoneira, espessura: float, distancia: float, diametro: float, gamma: float): #Item 6.3.3.3 da NBR 8800:2024
    registrar_marcha("\nCalculo relativo a resistência a rasgamento e esmagamento")
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    resistencia1 = corte*2.4*material.f_u*espessura*diametro*N_parafusos/gamma 
    registrar_marcha(f"\nResistencia 1 (Esmagamento): corte * 2.4 * material.f_u * espessura * diametro * N_parafusos / gamma = {corte} * 2.4 * {material.f_u} * {espessura} * {diametro} * {N_parafusos} / {gamma} = {resistencia1} N")  #Sair o resultado em N
    resistencia2 = 1.2*corte*material.f_u*espessura*distancia*N_parafusos/gamma  
    registrar_marcha(f"\nResistencia 2 (Rasgamento): 1.2 * corte * material.f_u * espessura * distancia * N_parafusos / gamma = 1.2 * {corte} * {material.f_u} * {espessura} * {distancia} * {N_parafusos} / {gamma} = {resistencia2} N")
    resistencia=min(resistencia1,resistencia2)

    registrar_marcha(f"Resistência minima = min({resistencia1},{resistencia2}) = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN

def resistencia_cisalhamento(corte: int, material: Aço, comprimento: float, cantoneira: Cantoneira, espessura: float, diametro: float, gamma: list) -> float:   #Item 6.5.5 da NBR 8800:2024
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]

    N_parafusos =cantoneira.disp_parafusos.shape[0]
    registrar_marcha("\nCalculo relativo a resistência a cisalhamento")
    resistencia1 = corte*0.6*material.f_y*comprimento*espessura/gamma_a1    #Escoamento da seção bruta
    registrar_marcha(f"\nResistencia 1 (Escoamento da seção bruta): corte * 0.6 * material.f_y * comprimento * espessura / gamma_a1 = {corte} * 0.6 * {material.f_y} * {comprimento} * {espessura} / {gamma_a1} = {resistencia1} N")
    resistencia2 = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2   #Ruptura da seção líquida
    registrar_marcha(f"\nResistencia 2 (Ruptura da seção líquida): corte * 0.6 * material.f_u * espessura * (comprimento - N_parafusos * (furo_padrao_pol(diametro))) / gamma_a2 = {corte} * 0.6 * {material.f_u} * {espessura} * ({comprimento} - {N_parafusos} * ({furo_padrao_pol(diametro)})) / {gamma_a2} = {resistencia2} N")

    resistencia=min(resistencia1,resistencia2)
    registrar_marcha(f"Resistência minima = min({resistencia1},{resistencia2}) = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN

def resistencia_block(corte: int, cantoneira: Cantoneira, espessura: float, diametro: float, gamma: float) -> float:  #Item 6.5.6 da NBR 8800:2024
    f_y = cantoneira.material.f_y
    f_u = cantoneira.material.f_u
    registrar_marcha("\nCalculo relativo a resistência a cisalhamento de bloco")
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    A_gv = espessura*(cantoneira.comprimento - cantoneira.f_b)  #Area bruta da cantoneira sujeita a cisalhamento (O comprimento pode ser o espaçamento entre os parafusos ou )
    A_nv = espessura*(cantoneira.comprimento - cantoneira.f_b) - (N_parafusos-0.5)*(furo_padrao_pol(diametro))*espessura  #Area líquida da cantoneira sujeita a cisalhamento
    A_nt = (cantoneira.f_b - 0.5*(furo_padrao_pol(diametro)))*espessura
    C_ts=1  # Sé deixa de ser 1, quando a tensão na área líquida não for uniforme 
    resistencia = min(0.6*f_u*A_nv + C_ts*f_u*A_nt,0.6*f_y*A_gv + C_ts*f_u*A_nt)*corte/gamma   #Sair o resultado em N  
    registrar_marcha(f"\nResistencia ao bloco de cisalhamento: min(0.6*f_u*A_nv + C_ts*f_u*A_nt,0.6*mf_y*A_gv + C_ts*f_u*A_nt)*corte/gamma = min(0.6*{f_u}*{A_nv} + {C_ts}*{f_u}*{A_nt}, 0.6*{f_y}*{A_gv} + {C_ts}*{f_u}*{A_nt})*{corte}/{gamma} = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN

#Cálculo da espessura da chapa de cabeça:

def larg_trib(posição: pd.DataFrame,b: float) -> float:

    registrar_marcha("Cálculo da largura tributária p para o efeito alavanca: item 6.3.5.2 da NBR 8800 \n")
    # Encontrar o maior valor de y
    max_y = posição["y (mm)"].max()

    # Filtrar os parafusos que estão na camada com maior y
    parafusos_maior_y = posição[posição["y (mm)"] == max_y]

    #Distância entre parafusos internos da camada (considerando a distância entre os dois primeiros parafusos)
    eint = abs(parafusos_maior_y["x (mm)"].iat[0] - parafusos_maior_y["x (mm)"].iat[1])
    registrar_marcha(f"Distância entre parafusos internos da camada = {eint} mm \n")

    #Distância entre parafusos externos da camada (Ou seja a distância de qualquer parafuso externo para sua borda na horizontal)
    eext =  parafusos_maior_y["x (mm)"].iat[0]
    registrar_marcha(f"Distância entre parafusos externos da camada = {eext} mm \n")

    pint = min(eint,3.5*b)
    registrar_marcha(f"p interno é o valor mínimo entre a distância entre parafusos internos da camada pint={min(eint,3.5*b)} mm \n")

    pext = min(0.5*eint,1.75*b) + min(eext,1.75*b)
    registrar_marcha(f"p externo é o valor mínimo entre a distância entre parafusos externos da camada pext={min(0.5*eint,1.75*b) + min(eext,1.75*b)} mm \n")

    #Se escolher o p minimo, aumenta o denominador, aumentando a espessura, segundo item 6.3.5.4 da NBR 8800;2024
    registrar_marcha(f"p é o menor entre pext e pint, ou seja, p={min(pext,pint)} mm \n")
    return min(pext,pint)


def exp_placa(Aço: Aço, Secão: Chapa, rigida: int, posição: pd.DataFrame, diametro: float, F_r_total: float, F_t_Sd: float, gamma: list) -> float | str | None:
    registrar_marcha(f"Cálculo da espessura mínima da chapa de cabeça, considerando o efeito alavanca a depender se a chapa é rígida={rigida}=1\n")
    a =Secão.a
    b = parametro_b(diametro) #Distância da face mais próxima da mesa até a linha de furação 

    #B = Secão.B

    p = larg_trib(posição,b)

    delta = 1- ((furo_padrao_pol(diametro))/p)      #Considerando a dimensão do furo na largura tributária como se fosse o furo padrão
    registrar_marcha(f"delta = 1 - (furo_padrao_pol(diametro)/p) = 1 - ({furo_padrao_pol(diametro)}/{p}) = {delta}")

    beta = ((a + 0.5*diametro)/(b - 0.5*diametro))*((F_r_total)/(F_t_Sd) - 1)
    registrar_marcha(f"beta = ((a + 0.5*diametro)/(b - 0.5*diametro)) * ((F_r_total/F_t_Sd) - 1) = (({a} + 0.5*{diametro})/({b} - 0.5*{diametro})) * (({F_r_total}/{F_t_Sd}) - 1) = {beta}")

    if beta >= 1:
        alfa = 1
        registrar_marcha(f"alfa = {alfa} (pois beta >= 1)")
    elif beta > 0 and beta < 1:
        alfa = min(1, (beta) / (delta * (1 - beta)))
        registrar_marcha(f"alfa = min(1, (beta)/(delta*(1-beta))) = min(1, ({beta})/({delta}*{1-beta})) = {alfa}")
    else:
        # Se beta <= 0, alfa é zero
        #Fisicamente o que isso significa é que b é menor do que meio diâmetro, não respeita as distâncias mínimas entre borda e furo
        alfa = 0
        registrar_marcha(f"alfa = {alfa} (pois beta <= 0)")
        registrar_marcha(f"A solicitação é maior do que a geometria da ligação aguenta, pois {diametro}>2*{b}.")
        return "A ligação não aguenta a solicitação desejada." 

    if rigida == 1:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p))*np.sqrt(1000)
        registrar_marcha(f"t = sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p)) * sqrt(1000) = sqrt(4*({b}-0.5*{diametro})*{F_t_Sd}*{gamma[0]}/({Aço.f_u}*{p})) * sqrt(1000) = {t} mm ")
    else:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p*(1+delta*alfa)))*np.sqrt(1000)
        registrar_marcha(f"t = sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p*(1+delta*alfa))) * sqrt(1000) = sqrt(4*({b}-0.5*{diametro})*{F_t_Sd}*{gamma[0]}/({Aço.f_u}*{p}*(1+{delta}*{alfa}))) * sqrt(1000) = {t} mm")

    maiores = [e for e in Secão.espessuras_disponiveis if e > t]  # Filtra apenas valores maiores que a espessura calculada

    if not maiores :
        return "A ligação não aguenta a solicitação desejada." 
    
    return min(maiores) if maiores else None  # Retorna o menor dos maiores ou None se não houver
