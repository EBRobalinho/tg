from fractions import Fraction
import re
from back.logs import registrar_marcha
#Conversão de Unidades

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
    

def ler_forca_tonelada(campo_input):
    texto = campo_input.text().strip().replace(",", ".")
    if not texto:
        return 0.0
    valor_tf = float(texto)
    valor_kn = valor_tf * 9.80665  # converte tf para kN
    registrar_marcha(f"Valor lido do input: {valor_tf} tf = {valor_kn:.2f} kN")
    return valor_kn

def ler_momento_tonelada_metro(campo_input):
    texto = campo_input.text().strip().replace(",", ".")
    if not texto:
        return 0.0
    valor_tf_m = float(texto)
    valor_kn_m = valor_tf_m * 9806.65  # converte tf·m para kN·mm
    registrar_marcha(f"Valor lido do input: {valor_tf_m} tf·m = {valor_kn_m:.2f} kN·m")
    return valor_kn_m