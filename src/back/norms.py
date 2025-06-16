from back.conversions import pol_to_mm
import numpy as np
from back.logs import registrar_marcha

# Diâmetro do furo padrão (considerações do diâmetro do furo-padrão) #Tabela 14 do item 6.3.6.2 da NBR 8800:2024

def furo_padrao_pol(diametro: float) -> float:
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
        return diametro + pol_to_mm("1/8") # Retorna a fórmula, pois depende do valor de 'db'

# Distância mínima da distância de um furo padrão a borda #Tabela 16 do item 6.3.11.1 da NBR 8800:2024

def dist_min_borda_pol(diametro_pol: str) -> float:
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
    
    #Calcula a distância da face da mesa da viga a linha de furação (distância vertical entre a face da mesa e a linha de furação)
def parametro_b(diametro: float) -> float:  # Segundo Item 6.1.1 do manual da Gerdau

    if diametro <= pol_to_mm("3/4"):
        return 30
    elif diametro == pol_to_mm("7/8"):
        return 35
    else:
        return 40
    
def criterio_min_solda_filete(espessura_metal_base: float) -> float:  #Segundo item 6.2.6.2.1 da NBR 8800:2024

    registrar_marcha("Critério mínimo de espessura da solda segundo o item 6.2.6.2.1 da NBR 8800:2024")
    if espessura_metal_base <= 6.3:
        registrar_marcha("Espessura mínima de solda é 3 mm se a espessura do metal base for menor ou igual a 6.3 mm")
        return 3

    if espessura_metal_base <=12.5 and espessura_metal_base > 6.3:
        registrar_marcha("Espessura mínima de solda é 4 mm se a espessura do metal base for menor ou igual a 12.5 mm e maior que 6.3 mm")
        return 5

    if espessura_metal_base <=19 and espessura_metal_base > 12.5:
        registrar_marcha("Espessura mínima de solda é 5 mm se a espessura do metal base for menor ou igual a 19 mm e maior que 12.5 mm")
        return 6

    if espessura_metal_base > 19:
        registrar_marcha("Espessura mínima de solda é 6 mm se a espessura do metal base for maior que 19 mm")
        return 8
    raise ValueError("Espessura do metal base inválida.")  # nunca alcançado, mas necessário para tipagem

def chapa_beta_roark(vinculacao: str, a: float, b: float) -> float:       #Tabela do Roarks (formulas for stress and strain, 7º edição) Para dimensionamento de espessura de chapa 
  
    # A -> Engastada dos 4 lados
    # B -> Engastados 3 lados e 1 lado livre 
    # C -> Engastado 1 lado, o lado oposto é livre e os outros 2 lados apoiados 
    # D -> Apoiado nos 4 lados
    # E -> Engastados dois lados consecultivos e os outros dois lados são livres
    # F -> Engastado 1 lado, os outros 3 lados são livres
  
    tabela = {
        "A": ([1, 1.2, 1.4, 1.6, 1.8, 2], [0.31, 0.38, 0.44, 0.47, 0.49, 0.52]),
        "B": ([0.25, 0.5, 0.75, 1, 1.5, 2, 3], [0.02, 0.08, 0.17, 0.32, 0.73, 1.2, 2.1]),
        "C": ([0.5, 0.67, 1, 1.5, 2, 99], [0.36, 0.45, 0.67, 0.77, 0.79, 0.8]),  # 99 ≈ ∞
        "D": ([0.25, 0.5, 0.75, 1, 1.5, 2, 3], [0.05, 0.19, 0.39, 0.67, 1.28, 1.8, 2.5]),
        "E": ([1, 1.2, 1.4, 1.6, 1.8, 2, 3], [0.29, 0.38, 0.45, 0.52, 0.57, 0.61, 0.71]),
        "F": ([0.125, 0.25, 0.375, 0.5, 0.75, 1], [0.05, 0.19, 0.4, 0.63, 1.25, 1.8])
    }

    vinculacao = vinculacao.upper()

    ab = a / b
    x, y = tabela[vinculacao]

    # Se estiver fora do intervalo, limita ao mínimo ou máximo
    if ab <= x[0]:
        return y[0]
    elif ab >= x[-1]:
        return y[-1]

    # Interpola o valor de beta
    return float(np.interp(ab, x, y))