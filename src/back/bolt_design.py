import numpy as np
from back.logs import registrar_marcha
import pandas as pd
from back.domain.parafuso import Parafuso


# Funções de cálculo do solicitante nos ligantes:

def solicitante_parafuso_tração(T,N_parafusos):  #N_parafusos é o número de parafusos que estão sendo solicitados devido aquela solicitação T na ligação
    return T/N_parafusos

def solicitante_parafuso_cisalhamento(V,N_parafusos):  #N_parafusos é o número de parafusos que estão sendo solicitados devido aquela solicitação V na ligação
    return V/N_parafusos  

def solicitante_parafuso_momento(M: float, B: float, ver_parafuso: pd.DataFrame, parafuso: Parafuso, k: int) -> float:  #Cálculo da tração solicitante no parafuso mais externo
    A_s = parafuso.A_g
    w_secao = w_inercia(B, ver_parafuso, parafuso.d, k)
    return M * A_s / w_secao

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

