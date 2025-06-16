import pandas as pd
import numpy as np
from math import floor
from back.design_functions import (registrar_marcha, 
resistencia_parafuso_tração,resistencia_parafuso_cisalhamento, 
solicitante_parafuso_tração, solicitante_parafuso_cisalhamento, parametro_b)
from back.norms import dist_min_borda_pol
from back.logs import registrar_marcha2, registrar_tabela
from back.domain.perfil import Perfil
from back.domain.parafuso import Parafuso
from back.domain.materials import Aço

from back.v_p_chapa_cabeca.v_p_chapa_cabeca import solicitante_parafuso_momento

from back.domain.chapa import ChapaExtremidade


##### Da Disposição

def disposicao_parafusos(t_f: float, b: float, b_linha: float, c: float, e2: float, e1: float, h: float):
    x_positions = [e2, e2 + e1]
    """
    Gera posições Y de parafusos linearmente espaçados entre as flanges da viga,
    respeitando distância mínima c entre eles.
    """
    parafusos_x = []
    parafusos_y = []

    # Altura onde se pode colocar parafusos entre as flanges
    altura_util = h - 2*t_f - 2*b_linha
    # Número de espaços mínimos possíveis (n espaçamentos => n+1 parafusos)
    n_espacos = floor(altura_util / c)
    n_parafusos = n_espacos + 1
    if n_espacos < 1:
        registrar_marcha("Não há espaço suficiente para colocar parafuso cujo diâmetro dimensione a ligação entre as flanges.")
        registrar_marcha(f"A distância disponível entre as flanges é de {altura_util} mm e a distância mínima entre os parafusos é de {c} mm.")
        raise ValueError("Não há espaço suficiente para colocar parafuso cujo diâmetro dimensione a ligação entre as flanges.")
        return 
    # Espaçamento real entre parafusos (maior ou igual a c)
    espac_real = altura_util / n_espacos
    # Primeira altura: da borda inferior até início da alma
    base_alma = b + b_linha 

    parafusos_x.extend(x_positions)
    parafusos_y.extend([b, b])

    parafusos_x.extend(x_positions)
    parafusos_y.extend([base_alma + t_f + b_linha, base_alma + t_f + b_linha])

    for i in range(1,n_parafusos-1):
        y = base_alma + t_f + b_linha + i * espac_real
        parafusos_x.extend(x_positions)
        parafusos_y.extend([y, y])

    parafusos_x.extend(x_positions)
    parafusos_y.extend([base_alma + h - b_linha - t_f,base_alma + h - b_linha - t_f])

    parafusos_x.extend(x_positions)
    parafusos_y.extend([base_alma + h + b_linha, base_alma + h + b_linha])

    data = {
        "parafuso": list(range(1, len(parafusos_x) + 1)),
        "x (mm)": parafusos_x,
        "y (mm)": parafusos_y
    }

    return pd.DataFrame(data)

#Comentar
def arranjo_chapa_parafusos(perfil: Perfil, parafuso: Parafuso, enrijecedor: int) -> tuple[ChapaExtremidade, pd.DataFrame, int, float, float]:
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    B_pilar = perfil.b_f #mm  

    h_pilar = perfil.h 
    
    b_linha = parametro_b(parafuso.d) # Distância Gerdau entre o centro do parafuso e face mais próxima da mesa do perfil

    b = dist_min_borda_pol(parafuso.d_pol) #Distância vertical do parafuso mais em cima até a borda da placa 

    e2 = max(40,b) #Distância horizontal entre parafuso-borda (na minha linha, segundo o manual da Gerdau) e item 6.3.11.1 da NBR 8800:2024

    e1 = max(120,3*parafuso.d,B_pilar - 2*e2)  #Distância horizontal entre parafusos (na minha linha, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    c  = 3*parafuso.d  #Distância vertical entre parafusos (na mesma coluna, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    disposicao = disposicao_parafusos(perfil.t_f, b,b_linha,c, e2, e1, h_pilar)

    N_parafusos = (disposicao.shape[0])

    B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

    B = max(B_norma,B_pilar) 

    y_inicio = min(disposicao['y (mm)']) + b_linha + perfil.t_f   #considerações a partir da distância recomendada pelo manual da Gerdau

    y_fim = max(disposicao['y (mm)']) - b_linha - perfil.t_f

    h_chapa = max(disposicao["y (mm)"]) + b

    chapa = ChapaExtremidade(B,h_chapa,b)

    return (chapa,disposicao,N_parafusos,y_inicio, y_fim)


def tensao_atuante(M : float, V: float, chapa: ChapaExtremidade) -> list[float]:
    W_chapa = (chapa.B*chapa.h**2)/6
    A_chapa = chapa.B*chapa.h
    
    sigma_topo = M/(W_chapa) - V/(A_chapa)  #Está submetida a compressão da flexão e da normal     

    sigma_base = -M/(W_chapa) - V/(A_chapa)  # Está submetida a tração da flexão e compressão da normal

    return [sigma_topo,sigma_base]        #kN/mm^2

def momento_atuante_intervalo(M: float, V: float, chapa: ChapaExtremidade, y1: float, y2: float, b: float) -> float:
    """
    Calcula o momento interno entre y1 e y2 na altura da chapa, 
    considerando a distribuição linear de tensões.

    Retorna momento em kN.mm
    """
    h = chapa.h

    # Calcula tensões nos extremos
    sigma_topo, sigma_base = tensao_atuante(M, V, chapa)

    # Coeficientes da função sigma(y) = a*y + b
    a = (sigma_topo - sigma_base) / h
    b0 = sigma_base

    # Integra sigma(y) * y de y1 a y2:
    # ∫(a*y + b0)*y dy = ∫a*y² + b0*y dy = (a/3)*(y2³ - y1³) + (b0/2)*(y2² - y1²)
    termo1 = (a / 3) * (y2**3 - y1**3)
    termo2 = (b0 / 2) * (y2**2 - y1**2)

    momento = b * (termo1 + termo2)  # b é a largura da chapa
    return momento  # kN.mm

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

def esp_chapa_roark(M: float, V: float, vinculacao: str, chapa: ChapaExtremidade, a: float, b: float) -> float:
    registrar_marcha("Cálculo da espessura da chapa:")
    tensoes=tensao_atuante(M,V,chapa)
    sigma = max(np.abs(tensoes))  #kN/mm^2
    fy = chapa.f_y*1000/(1000**2)   #kN/mm^2
    registrar_marcha(f"Tensão atuante na Chapa de {sigma} kN/mm^2 e f_y da chapa {fy} kN/mm^2")
    beta = chapa_beta_roark(vinculacao, a, b)
    registrar_marcha(f"Beta={beta}, conforme a vinculação do tipo {vinculacao} com a={a} e b={b}")
    t = b*np.sqrt(beta*sigma/(1.35*fy))       # mm
    registrar_marcha(f"Espessura dada por {t} = {b}*sqrt({beta}*{sigma}/(1.35*{fy})) mm")
    return t  # Retorna o menor dos maiores ou None se não houver

def dim_enrijecedores(M: float, V: float, chapa: ChapaExtremidade, y1: float, y2: float, largura_placa: float, altura: float = 100) -> float:  #Dimensionamento do enrijecedor, com altura default de 100 mm
    registrar_marcha(f"\nDimensionamento do enrijecedor com a altura de {altura} mm")
    fy = chapa.f_y*1000/(1000**2)   #kN/mm^2
    registrar_marcha(f"f_y da chapa {fy} kN/mm^2")
    Mch =  momento_atuante_intervalo(M, V, chapa, y1, y2,largura_placa) # y1 é de onde começa a ser calculado o momento até o y2 que é onde vai.
    registrar_marcha(f"Momento atuante na chapa onde será colocado o enrijecedor {abs(Mch)} kN*mm (Cálculo analítico realizado via integração da tensão por posição)")
    t = 6.6*np.abs(Mch)/((altura)**2)/(fy)
    registrar_marcha(f"Espessura do enrijecedor dada por {t} = 6.6*{abs(Mch)}/(({altura})**2)/({fy}) mm \n")
    return t  # Retorna o menor dos maiores ou None se não houver


def dim_chapa_pilar(M: float, V: float, T: float, aco_chapa: Aço, enrijecedor: int, altura: float, perfil_pilar: Perfil, parafuso: Parafuso, gamma: list) -> tuple[int,Parafuso, ChapaExtremidade, pd.DataFrame, float] | tuple[int,Parafuso, ChapaExtremidade, pd.DataFrame, float, float]|list[str]:
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    k=0
    registrar_marcha("Dimensionamento da ligação que faz conexão da viga sobre pilar \n")
    registrar_marcha("O dimensionamento dos enrijecedores será feito conforme metodologia de Roark Formulas for Stress and Strain 7° edition \n")
    i = 0
    while i < len(parafuso.diametro_mm):
        d = parafuso.diametro_mm[i]
        parafuso.d = d  # Atualiza o diâmetro do parafuso
        registrar_marcha2(f"Interação i={i} : cálculo com parafuso de diâmetro {d} pol")
        registrar_marcha(f"\nInteração k={k} para linha neutra: ou seja, é estimado que a linha neutra esteja abaixo do parafuso n° {k+1} e no mínimo na altura do parafuso {k} de baixo para cima \n")
        [chapa,ver_parafuso,N_parafusos,y_inicio, y_fim] = arranjo_chapa_parafusos(perfil_pilar,parafuso,enrijecedor)
        registrar_tabela("Vértices dos Parafusos", ver_parafuso)

        registrar_marcha(f"Vertices que limitam a alma colaborante da chapa: y_inicio = {y_inicio} mm e y_fim = {y_fim} mm")

        registrar_marcha(f"Número de parafusos calculados = {N_parafusos} \n")
        
        chapa.material(aco_chapa)
        registrar_tabela("Vértices da chapa", chapa.df)

        #Cálculo da espessura da chapa e do enrijecedor

        if enrijecedor == 0:

            #Cálculo da espessura solicitada pela área externa as mesas:
            vinculacao_externa="F"
            registrar_marcha(f"Caso: enrijecedor={enrijecedor}, para calcular a espessura da chapa externa \n")
            b_ext = chapa.B
            registrar_marcha(f"Espessura colaborante b_ext={chapa.B} mm")
            a_ext = y_inicio - perfil_pilar.t_f
            registrar_marcha(f"Espessura colaborante a_ext={y_inicio - perfil_pilar.t_f} mm")

            t_ext = esp_chapa_roark(M,V,vinculacao_externa,chapa,a_ext,b_ext)

            #Cálculo da espessura solicitada pela área interna as mesas:
            vinculacao_interna = "B"
            registrar_marcha(f"Caso: enrijecedor={enrijecedor}, para calcular a espessura da chapa interna \n")
            a_int = (chapa.B/2) - (perfil_pilar.t_w/2)
            registrar_marcha(f"Espessura colaborante a_int={(chapa.B/2) - (perfil_pilar.t_w/2)} mm")
            b_int = y_fim - y_inicio            
            registrar_marcha(f"Espessura colaborante b_int={y_fim - y_inicio}")

            t_int = esp_chapa_roark(M,V,vinculacao_interna,chapa,a_int,b_int)
            maiores_enj = [0,0,0]
        else:
            #Cálculo da espessura solicitada pela área externa as mesas:
            vinculacao_externa="E"
            registrar_marcha(f"Caso: enrijecedor={enrijecedor}, para calcular a espessura da chapa externa \n")
            b_ext = chapa.B/2
            registrar_marcha(f"Espessura colaborante b_ext={chapa.B} mm")
            a_ext = y_inicio - perfil_pilar.t_f
            registrar_marcha(f"Espessura colaborante a_ext={y_inicio - perfil_pilar.t_f} mm")

            t_ext = esp_chapa_roark(M,V,vinculacao_externa,chapa,a_ext,b_ext)

            esp_enj =dim_enrijecedores(M,V,chapa,0,a_ext,b_ext,altura)

            #Cálculo da espessura solicitada pela área interna as mesas:
            vinculacao_interna = "B"
            registrar_marcha(f"Caso: enrijecedor={enrijecedor}, para calcular a espessura da chapa interna \n")
            a_int = (chapa.B/2) - (perfil_pilar.t_w/2)
            registrar_marcha(f"Espessura colaborante a_int={(chapa.B/2) - (perfil_pilar.t_w/2)} mm")
            b_int = (perfil_pilar.h - 2*perfil_pilar.t_f)/2     
            registrar_marcha(f"Espessura colaborante b_int={(perfil_pilar.h - 2*perfil_pilar.t_f)/2}")       

            t_int = esp_chapa_roark(M,V,vinculacao_interna,chapa,a_int,b_int)   

            maiores_enj = [e for e in chapa.espessuras_disponiveis if e > esp_enj]  # Filtra apenas valores maiores que a espessura calculada para o enrijecedor
            registrar_marcha(f"\nEspessuras de chapa no mercado em pol para os enrijecedores que sejam maiores ou igual que o solicitado {maiores_enj}")
            if not maiores_enj :
                registrar_marcha(f"A espessura solicitada {esp_enj} é maior dos que as existentes no mercado")
                return ["A ligação não aguenta a solicitação desejada (A chapa requisitada é muito expessa)."] 

        t=max(t_ext,t_int)
        registrar_marcha(f"Calcula a maior espessura entre a chapa interna e externa {t}=max({t_ext},{t_int}) mm ")

        maiores_t = [e for e in chapa.espessuras_disponiveis if e > t]  # Filtra apenas valores maiores que a espessura calculada para a chapa
        if not maiores_t :
                registrar_marcha(f"A espessura solicitada {t} é maior dos que as existentes no mercado")
                return ["A ligação não aguenta a solicitação desejada (A chapa requisitada é muito expessa)."] 

        registrar_marcha("\nCálculo da resistência e solicitante de cada parafuso conforme NBR:8800, itens de 6.3.3 ")  
        #Resistentes do parafuso para tração e cisalhamento
        r_p_t=resistencia_parafuso_tração(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso individual a tração {r_p_t} KN")
        r_p_v=resistencia_parafuso_cisalhamento(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso individual a cisalhamento {r_p_v} KN")
        #Solicitantes no parafuso para tração e cisalhamento
        s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, parafuso , k)
        registrar_marcha(f"Resistência do parafuso individual a tração advinda do momento {s_p_m} KN")
        s_p_t = solicitante_parafuso_tração(V,N_parafusos)
        registrar_marcha(f"Resistência do parafuso individual a tração pura {s_p_t} KN")
        s_p_v = solicitante_parafuso_cisalhamento(T,N_parafusos)
        registrar_marcha(f"Resistência do parafuso individual a cisalhamento puro {s_p_v} KN")
        #Curva de interação (Sendo aplicada considerando que todos os parafusos estão solicitados conforme o parafuso mais solicitado)
        curva=(((s_p_t + s_p_m)/r_p_t)**2 + (s_p_v/r_p_v)**2)
        registrar_marcha(f"\nCalculo da circunferência de interação, conforme previsto em 6.3.3.4 da 8800:2024 {curva}=((({s_p_t} + {s_p_m})/{r_p_t})**2 + ({s_p_v}/{r_p_v})**2)")
        #Critério 6.3.3.4 da NBR 8800:2024
        if curva > 1:
            if k<(N_parafusos/2):
                k+=1
                registrar_marcha(f'\n{curva}>1 : Mudança da linha neutra entre os parafusos, para k={k}.')
                continue
            else:
                k=0
                i+=1
                registrar_marcha(f'\n{curva}> 1 e não há mais posições para linha neutra. Zera a linha neutra e calcula para o próximo diâmetro comercial.')
                continue
        else:
            return (k,parafuso,chapa,ver_parafuso,min(maiores_t),min(maiores_enj)) 
    return ["A ligação não aguenta a solicitação desejada."]







