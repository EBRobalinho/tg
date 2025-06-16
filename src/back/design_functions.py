import numpy as np
import pandas as pd
from math import ceil
from back.norms import furo_padrao_pol, parametro_b, criterio_min_solda_filete
from back.domain.cantoneira import Cantoneira
from back.domain.materials import Aço
from back.domain.parafuso import Parafuso
from back.domain.chapa import Chapa
from logs import registrar_marcha



# Funções de cálculo do solicitante nos ligantes:

def solicitante_parafuso_tração(T,N_parafusos):  #N_parafusos é o número de parafusos que estão sendo solicitados devido aquela solicitação T na ligação
    return T/N_parafusos

def solicitante_parafuso_cisalhamento(V,N_parafusos):  #N_parafusos é o número de parafusos que estão sendo solicitados devido aquela solicitação V na ligação
    return V/N_parafusos  

def solicitante_total(T,V,N_parafusos):
    s_p_t = solicitante_parafuso_tração(T,N_parafusos)
    s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
    return np.sqrt(s_p_t**2 + s_p_v**2)

# Funções do cálculo de resistência dos ligantes (Parafusos)

def resistencia_parafuso_tração(parafuso,gamma):
    gamma_a2=gamma[0]
    #Cálculo da area bruta do parafuso
    F_t_Rd = 0.75 * parafuso.f_u * parafuso.A_g / gamma_a2 #item 6.3.3.1 da NBR 8800:2024
    registrar_marcha(f"Cálculo da resistência do parafuso considerando a área bruta é F_t_Rd ={0.75 * parafuso.f_u * parafuso.A_g / gamma_a2} N")
    return F_t_Rd/1000  #Para sair em kN

def resistencia_parafuso_cisalhamento(parafuso,gamma):
    gamma_a2=gamma[0]
    rosca=parafuso.rosca
    planos_de_corte=parafuso.planos_de_corte
    #Cálculo da area bruta do parafuso
    if rosca :
        F_v_Rd = 0.45 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2 #item 6.3.3.2 da NBR 8800:2024
        registrar_marcha(f"Cálculo da resistência do parafuso considerando o plano de corte na rosca é F_v_Rd ={0.45 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2} N")
    else:
        F_v_Rd = 0.56 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2
        registrar_marcha(f"Cálculo da resistência do parafuso considerando o plano de corte na rosca é F_v_Rd ={0.56 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2} N")
    return F_v_Rd/1000 #Para sair em kN

def resistencia_total(parafuso,gamma):
    r_p_t = resistencia_parafuso_tração(parafuso,gamma)
    r_p_c = resistencia_parafuso_cisalhamento(parafuso,gamma)
    return np.sqrt(r_p_t**2 + r_p_c**2)

#Soldas

def momento_inercia_soldas_perfil(perfil,filete_duplo):
    meia_altura=perfil.h/2 #mm
    largura_mesa=perfil.b_f

    if filete_duplo:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1

    Ix1 = qtd*(largura_mesa*0.7*(meia_altura**2)) 
    Ix2 = qtd*((largura_mesa-perfil.t_w)*0.7*(meia_altura-perfil.t_f)**2) 
    Ix3 = qtd*(0.7*(perfil.h - 2*perfil.t_f)**3)/12

    return Ix1 + Ix2 + Ix3 #mm^3*(Para 1mm de espessura)

def tensao_cisalhante_momento_filete(perfil,M,altura,filete_duplo):
    #A ideia é calcular a tensão de cisalhmento máxima advinda do momento que nem é feito no Livro do Pfeil:
    momento_inercia = momento_inercia_soldas_perfil(perfil,filete_duplo)
    return M*(altura*0.5)/momento_inercia         #kN/mm*(Para 1mm de espessura)

def tensao_cisalhante_cortante_filete(perfil,V,filete_duplo):
    if filete_duplo:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    #A ideia é calcular a tensão de cisalhmento máxima advinda do cortante que nem é feito no Livro do Pfeil (considera-se então que toda a cisalhante do cortante é resistida pela alma)
    return V/qtd/0.7/perfil.h_w       #kN/(mm*(Para 1mm de espessura))

def tensao_cisalhante_normal_filete(perfil,N,filete_duplo):
    if filete_duplo:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1

    comprimento=qtd*(2*perfil.b_f + perfil.h - 2*perfil.t_f - perfil.t_w)

    return N/comprimento/0.7        #kN/(mm*(Para 1mm de espessura))    

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

#Cálculo de espessura mínima de solda necessária:
    
def espessura_solda(M,V,T,solda,perfil,espessura_chapa,filete_duplo,gamma):
    registrar_marcha("Cálculo da espessura mínima de solda necessária segundo NBR 8800:2024")

    tal_r1 = solda.f_uw_mpa*0.6/gamma[1]     #Mpa    #Tabela 9, item 6.2.5.1 da NBR 8800:2024 (Relativa a tensão resistida pela solda)
    registrar_marcha(f"tal_r1 = {solda.f_uw_mpa} * 0.6 / {gamma[1]} = {tal_r1:.3f} MPa")
    tal_r2 = perfil.f_u*0.6/gamma[0]      #Letra b do item 6.5.5 da NBR 8800:2024 (relativa a ruptura do metal base)
    registrar_marcha(f"tal_r2 = {perfil.f_u} * 0.6 / {gamma[0]} = {tal_r2:.3f} MPa")

    tal_r = min(tal_r1, tal_r2)
    registrar_marcha(f"tal_r = min({tal_r1:.3f}, {tal_r2:.3f}) = {tal_r:.3f} MPa")

    tal_m = tensao_cisalhante_momento_filete(perfil, M, perfil.h_w*0.5, filete_duplo)
    tal_v = tensao_cisalhante_cortante_filete(perfil, V, filete_duplo)
    tal_n = tensao_cisalhante_normal_filete(perfil, T, filete_duplo)

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


# Funções para o cálculo do diâmetro do parafuso e da profundidade da linha neutra:

def y_linha_neutra(B: float, ver_parafuso: pd.DataFrame, diametro: float, k: int) -> float:  #Posição da linha neutra da seção transversal dada
    registrar_marcha("Cálculo da altura da linha neutra em função da variável guia k={k}")
    #Posição dos parafusos em y
    posição=np.unique(ver_parafuso["y (mm)"])

    N = len(ver_parafuso)  #Número total de parafusos
    n = (ver_parafuso["x (mm)"] == ver_parafuso["x (mm)"].iloc[0]).sum()  #número de parafusos por coluna
    n_p_c = N/n  #número de parafusos por camada

    #Somatório de todas as posições (em y) das barras de aço
    S=0
    for i in range(k,n,1):
        S = S + abs(posição[i])
    #Raiz positiva da equação do 2º grau que retorna as duas coordenadas possíveis para a posição da linha neutra
    y_ln = ( -(np.pi*n_p_c)*((diametro**2)*(n-k))/(4*B) + (np.sqrt((((np.pi*n_p_c*(n-k)))**2)*(diametro**4) + 8*B*(np.pi*n_p_c)*S*(diametro**2)  ) /(4*B) ) )
    registrar_marcha(
        f"y_ln = [-(pi * n_p_c * (d^2) * (n-k)) / (4*B) + sqrt(((pi * n_p_c * (n-k))^2 * d^4 + 8*B*pi*n_p_c*S*d^2) / (4*B))] = "
        f"[-({np.pi:.3f}) * {n_p_c:.3f} * ({diametro:.2f}^2) * ({n}-{k}) / (4*{B}) + "
        f"sqrt((({np.pi:.3f} * {n_p_c:.3f} * ({n}-{k}))^2 * {diametro:.2f}^4 + 8*{B}*{np.pi:.3f}*{n_p_c:.3f}*{S:.3f}*{diametro:.2f}^2) / (4*{B}))] = {y_ln:.3f} mm"
    )
    return y_ln

def w_inercia(B: float, ver_parafuso: pd.DataFrame, diametro: float, k: int) -> float:
    registrar_marcha("Cálculo do W de inércia (momento de inicio de plastificação)  em função da variável guia k={k}")
    #Posição dos parafusos em y
    posição=np.unique(ver_parafuso["y (mm)"])
    #Quantidade de parafusos em y
    n = len(posição)
    #Número de parafusos para cada y
    n_p_c = len(ver_parafuso)/n

    #Cálculo da posição da linha neutra
    y_ln=y_linha_neutra(B,ver_parafuso,diametro, k)

    #Cálculo do momento de inércia
    S=0
    for i in range(1,n+1,1):
        S = S + (abs(posição[i-1])-y_ln)**2
    i_s = B*(y_ln**3)/3 + np.pi*0.25*(diametro**2)*S*n_p_c

    #Cálculo do w de inércia
    w = (i_s)/(abs(max(posição)) - y_ln)
    registrar_marcha(
        f"w = Momento de Inércia/ (|max(y) - y_ln|) = {i_s:.3f} / (|{max(posição):.3f} - {y_ln:.3f}|) = {w:.3f} mm³"
    )
    return w

def solicitante_parafuso_momento(M: float, B: float, ver_parafuso: pd.DataFrame, parafuso: Parafuso, k: int) -> float:  #Cálculo da tração solicitante no parafuso mais externo
    A_s = parafuso.A_g
    w_secao = w_inercia(B, ver_parafuso, parafuso.d, k)
    return M * A_s / w_secao