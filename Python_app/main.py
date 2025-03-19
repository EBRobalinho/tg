import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import re
from fractions import Fraction


# Definição das classes a serem utilizadas

class Aço:
    def __init__(self, nome, f_y, f_u, E, densidade):
        self.nome = nome # Nome do aço (ex: ASTM A36)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa
        self.E = E # GPa
        self.densidade = densidade  # kg/m³

class Parafuso:
    def __init__(self, nome,f_y, f_u):
        self.nome = nome # Nome do parafuso (ex: ASTM A325)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa

    def diametro(self, diametro):
        """
        Converte um diâmetro fornecido em polegadas para milímetros.
        
        Parâmetros:
        diametro (str, int ou float): O diâmetro em polegadas, podendo ser um número ou fração (ex: "1.1/8").
        
        Retorna:
        None: Atualiza os atributos `diametro_pol` e `diametro_mm`.
        """
        self.diametro_pol = diametro  # Armazena o valor original em polegadas

        if isinstance(diametro, (int, float)):  # Se já for número, converte direto
            self.diametro_mm = diametro * 25.4
        elif isinstance(diametro, str):
            if '.' in diametro:  # Se for formato misto (ex: "1.1/8")
                partes = re.split(r'\.', diametro)  # Divide parte inteira e fração
                parte_inteira = int(partes[0])  # Parte inteira
                fracao = float(Fraction(partes[1]))  # Converte fração com Fraction
                self.diametro_mm = (parte_inteira + fracao) * 25.4  # Converte para mm
            else:  # Se for apenas uma fração (ex: "5/8")
                self.diametro_mm = float(Fraction(diametro)) * 25.4  # Converte para mm


        self.A_g = math.pi * (self.diametro_mm / 2) ** 2 # mm²

class Solda:
    def __init__(self, nome, f_uw):
        self.nome = nome # Nome da solda (ex: E6010)
        self.f_uw_ksi = f_uw # ksi
        self.f_uw_mpa = f_uw * 6.89476 # MPa
        # Ver tabela relacionando tipo de metal com a solda Tabela 9 item 6.2.5.1 da NBR 8800:2024

class Perfil:
    def __init__(self, Nome, espessura_base, base, altura, espessura_alma):
        self.nome = Nome #referencia ao objeto de aço
        self.t_f = espessura_base # mm
        self.b_f = base # mm
        self.h = altura # mm   
        self.t_w  = espessura_alma #mm
        self.R_conc = 10 #mm
        self.h_w = self.h - 2*self.t_f - 2*self.R_conc
        # se precisar de mais propriedades ir colocando aos poucos
    def inercias(self):
        self.I_mesa = 2*((self.b_f*self.t_f**3)/12 + (self.b_f*self.t_f)*(((self.h - self.t_f)/2)**2))  #mm^4
        self.I_alma = (self.t_w*((self.h - 2*self.t_f)**3)/12)
        self.I_perfil = self.I_mesa + self.I_alma

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

# Funções do cálculo de resistência dos ligantes (Parafusos)

def resistencia_parafuso_tração(parafuso,gamma):
    #Cálculo da area bruta do parafuso
    F_t_Rd = 0.75 * parafuso.f_u * parafuso.A_g / gamma #item 6.3.3.1 da NBR 8800:2024
    return F_t_Rd/1000  #Para sair em kN

def resistencia_parafuso_cisalhamento(parafuso,rosca,planos_de_corte,gamma):
    #Cálculo da area bruta do parafuso
    if rosca == True:
        F_v_Rd = 0.45 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma #item 6.3.3.2 da NBR 8800:2024
    else:
        F_v_Rd = 0.56 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma
    return F_v_Rd/1000 #Para sair em kN

def resistencia_total(parafuso,rosca,planos_de_corte,gamma):
    r_p_t = resistencia_parafuso_tração(parafuso,gamma)
    r_p_c = resistencia_parafuso_cisalhamento(parafuso,rosca,planos_de_corte,gamma)
    return np.sqrt(r_p_t**2 + r_p_c**2)

#Soldas

def resistencia_solda_filete_cisalhamento_solda(solda,comprimento_solda, solicitante,filete_duplo,gamma_2):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    espessura = solicitante*gamma_2*np.sqrt(2)/(solda.f_uw_mpa*qtd*0.6)
    return espessura*1000 # Calcula a espessura minima de solda necessária para resistir aquela solicitação de cisalhamento (saindo em mm)

def resistencia_solda_filete_tracao_base(aço,comprimento_solda, solicitante,filete_duplo,gamma_1):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    espessura = solicitante*gamma_1/(aço.f_y*qtd)
    return espessura*1000  # Calcula a espessura minima de solda necessária para resistir aquela solicitação de tração (saindo em mm)

def resistencia_solda_filete_cisalhamento_base(aço,comprimento_solda, solicitante,filete_duplo,gamma_1):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    espessura = solicitante*gamma_1/(aço.f_y*qtd*0.6)
    return espessura*1000  # Calcula a espessura minima de solda necessária para resistir aquela solicitação de tração (saindo em mm)