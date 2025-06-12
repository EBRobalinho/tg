import math
import pandas as pd
import re
from fractions import Fraction  # Para lidar com frações em strings

#Fazer uma função para converter a lista de pol para mm de chapa

def pol_to_mm(pol: int | str) -> float:
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

def mm_para_polegada(valor_mm: float) -> str:
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



class Parafuso:
    def __init__(self, nome: str, f_y: float, f_u: float, diametro: list):
        self.nome = nome  # Nome do parafuso (ex: ASTM A325)
        self.f_y = f_y  # MPa
        self.f_u = f_u # MPa
        self.diametro_pol = diametro  # Armazena os valores possíveis de diâmetro em polgadas
        self.diametro_mm = [pol_to_mm(d) for d in diametro] #Armazena os valores convertidos para mm
        self.d : float #Diâmetro encontrado do dimensionamento do Parafuso
        self.d_pol: str = mm_para_polegada(self.d)
        self.A_g = math.pi * (self.d / 2) ** 2  # mm²


    def prop_geometricas(self, rosca: int, planos_de_corte: int):
        self.rosca = rosca
        self.planos_de_corte = planos_de_corte

