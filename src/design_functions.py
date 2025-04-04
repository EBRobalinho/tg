import pandas as pd
import numpy as np
import math
import re
from fractions import Fraction

#Conversão de Unidades

#Fazer uma função para converter a lista de pol para mm de chapa

def pol_to_mm(pol):
    if isinstance(pol, (int, float)):  # Se já for número, converte direto
        return pol * 25.4
    elif isinstance(pol, str):
        if '.' in pol:  # Se for formato misto (ex: "1.1/8")
            partes = re.split(r'\.', pol)  # Divide parte inteira e fração
            parte_inteira = int(partes[0])  # Parte inteira
            fracao = float(Fraction(partes[1]))  # Converte fração com Fraction
            return (parte_inteira + fracao) * 25.4  # Converte para mm
        else:  # Se for apenas uma fração (ex: "5/8")
            return float(Fraction(pol)) * 25.4  # Converte para mm

def mm_para_polegada(valor_mm):
    """
    Converte valor em milímetros para string em polegadas com notação fracionária.
    Ex: 28.575 mm → '1.1/8'
    """
    polegadas = valor_mm / 25.4
    parte_inteira = int(polegadas)
    fracao = Fraction(polegadas - parte_inteira).limit_denominator(64)

    if fracao.numerator == 0:
        return f"{parte_inteira}"
    elif parte_inteira == 0:
        return f"{fracao.numerator}/{fracao.denominator}"
    else:
        return f"{parte_inteira}.{fracao.numerator}/{fracao.denominator}"

# Diâmetro do furo padrão (considerações do diâmetro do furo-padrão) #Tabela 14 do item 6.3.6.2 da NBR 8800:2024

def furo_padrao_pol(diametro):
    """
    Retorna o diâmetro do furo padrão em polegadas,
    com base no diâmetro do parafuso em polegadas (Tabela 14).
    """
    if diametro == pol_to_mm("1/2"):
        return pol_to_mm("9/16")
    elif diametro == pol_to_mm("5/8"):
        return pol_to_mm("11/16")
    elif diametro == pol_to_mm("3/4"):
        return pol_to_mm("13/16")
    elif diametro == pol_to_mm("7/8"):
        return pol_to_mm("15/16")
    elif diametro == pol_to_mm("1"):
        return pol_to_mm("1.1/8")
    else:       
        return diametro + pol_to_mm(1/8) # Retorna a fórmula, pois depende do valor de 'db'

# Distância mínima da distância de um furo padrão a borda #Tabela 16 do item 6.3.11.1 da NBR 8800:2024

def dist_min_borda_pol(diametro_pol):
    """
    Retorna a distância mínima do centro do furo à borda (em mm),
    conforme a Tabela 16, dado o diâmetro do parafuso em polegadas.
    """
    tabela = {
        "1/2": 19,
        "5/8": 22,
        "3/4": 25,
        "7/8": 28,
        "1": 32,
        "1.1/8": 38,
        "1.1/4": 41,
    }

    if diametro_pol in tabela:
        return tabela[diametro_pol] #retorna a distância em mm
    else:
        db_mm = pol_to_mm(diametro_pol)
        return 1.25 * db_mm

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
    return F_t_Rd/1000  #Para sair em kN

def resistencia_parafuso_cisalhamento(parafuso,gamma):
    gamma_a2=gamma[0]
    rosca=parafuso.rosca
    planos_de_corte=parafuso.planos_de_corte
    #Cálculo da area bruta do parafuso
    if rosca == True:
        F_v_Rd = 0.45 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2 #item 6.3.3.2 da NBR 8800:2024
    else:
        F_v_Rd = 0.56 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2
    return F_v_Rd/1000 #Para sair em kN

def resistencia_total(parafuso,gamma):
    r_p_t = resistencia_parafuso_tração(parafuso,gamma)
    r_p_c = resistencia_parafuso_cisalhamento(parafuso,gamma)
    return np.sqrt(r_p_t**2 + r_p_c**2)

#Soldas

def momento_inercia_soldas_perfil(perfil,filete_duplo):
    meia_altura=perfil.h/2 #mm
    largura_mesa=perfil.b_f

    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1

    Ix1 = qtd*(largura_mesa*0.7*(meia_altura**2)) 
    Ix2 = qtd*((largura_mesa-perfil.t_w)*0.7*(meia_altura-perfil.t_f)**2) 
    Ix3 = qtd*(0.7*(perfil.h - 2*perfil.t_f)**3)/12

    return Ix1 + Ix2 + Ix3 #mm^3*(Para 1mm de espessura)

def tensao_cisalhante_momento_filete(perfil,M,altura,filete_duplo):
    #A ideia é calcular a tensão de cisalhmento máxima advinda do momento que nem é feito no Livro do Pfeil:
    I = momento_inercia_soldas_perfil(perfil,filete_duplo)
    return M*(altura*0.5)/I         #kN/mm*(Para 1mm de espessura)

def tensao_cisalhante_cortante_filete(perfil,V,filete_duplo):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    #A ideia é calcular a tensão de cisalhmento máxima advinda do cortante que nem é feito no Livro do Pfeil (considera-se então que toda a cisalhante do cortante é resistida pela alma)
    return V/qtd/0.7/perfil.h_w       #kN/(mm*(Para 1mm de espessura))

def tensao_cisalhante_normal_filete(perfil,N,filete_duplo):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1

    comprimento=qtd*(2*perfil.b_f + perfil.h - 2*perfil.t_f - perfil.t_w)

    return N/comprimento/0.7        #kN/(mm*(Para 1mm de espessura))    

def criterio_min_solda_filete(espessura_metal_base):  #Segundo item 6.2.6.2.1 da NBR 8800:2024

    if espessura_metal_base <= 6.3:
        return 3
    if espessura_metal_base <=12.5 and espessura_metal_base > 6.3:
        return 5
    if espessura_metal_base <=19 and espessura_metal_base > 12.5:
        return 6
    if espessura_metal_base > 19:
        return 8