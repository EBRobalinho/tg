import pandas as pd
import numpy as np
from math import isclose
from design_functions import *
from class_materials import *
from v_p_chapa_cabeca.v_p_chapa_cabeca import parametro_b,solicitante_parafuso_momento

##### Da Disposição

def disposicao_parafusos(t_f, b,b_linha,c ,e2, e1, h):
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
    n_espacos = math.floor(altura_util / c)
    n_parafusos = n_espacos + 1

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
def arranjo_chapa_parafusos(perfil,parafuso,enrijecedor):
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    B_pilar = perfil.b_f #mm  

    h_pilar = perfil.h 
    
    b_linha = parametro_b(parafuso.diametro_mm) # Distância Gerdau entre o centro do parafuso e face mais próxima da mesa do perfil

    b = dist_min_borda_pol(parafuso.diametro_pol) #Distância vertical do parafuso mais em cima até a borda da placa 

    e2 = max(40,dist_min_borda_pol(parafuso.diametro_pol)) #Distância horizontal entre parafuso-borda (na minha linha, segundo o manual da Gerdau) e item 6.3.11.1 da NBR 8800:2024

    e1 = max(120,3*parafuso.diametro_mm,B_pilar - 2*e2)  #Distância horizontal entre parafusos (na minha linha, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    c  = 3*parafuso.diametro_mm  #Distância vertical entre parafusos (na minha coluna, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    disposicao = disposicao_parafusos(perfil.t_f, b,b_linha,c, e2, e1, h_pilar)

    N_parafusos = (disposicao.shape[0])

    B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

    B = max(B_norma,B_pilar) 

    y_inicio = min(disposicao['y (mm)']) + b_linha + perfil.t_f   #considerações a partir da distância recomendada pelo manual da Gerdau

    y_fim = max(disposicao['y (mm)']) - b_linha - perfil.t_f

    h_chapa = max(disposicao["y (mm)"]) + b

    chapa = ChapaExtremidade(B,h_chapa,b)


    return [chapa,disposicao,N_parafusos,y_inicio, y_fim]


def tensao_atuante(M,V,chapa):
    W_chapa = (chapa.B*chapa.h**2)/6
    A_chapa = chapa.B*chapa.h
    
    sigma_topo = M/(W_chapa) - V/(A_chapa)  #Está submetida a compressão da flexão e da normal     

    sigma_base = -M/(W_chapa) - V/(A_chapa)  # Está submetida a tração da flexão e compressão da normal

    return [sigma_topo,sigma_base]        #kN/mm^2

def momento_atuante_intervalo(M, V, chapa, y1, y2,b):
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

def esp_chapa_roark(M,V,vinculacao,chapa,a,b):
    tensoes=tensao_atuante(M,V,chapa)
    sigma = max(np.abs(tensoes))  #kN/mm^2
    fy = chapa.f_y*1000/(1000**2)   #kN/mm^2

    beta = chapa_beta_roark(vinculacao, a, b)

    t = b*np.sqrt(beta*sigma/(1.35*fy))       # mm

    return t  # Retorna o menor dos maiores ou None se não houver

def dim_enrijecedores(M,V,chapa,y1,y2,largura_placa,altura = 100):  #Dimensionamento do enrijecedor, com altura default de 100 mm
    fy = chapa.f_y*1000/(1000**2)   #kN/mm^2
    Mch =  momento_atuante_intervalo(M, V, chapa, y1, y2,largura_placa) # y1 é de onde começa a ser calculado o momento até o y2 que é onde vai.

    t = 6.6*np.abs(Mch)/((altura)**2)/(fy)

    return t  # Retorna o menor dos maiores ou None se não houver


def dim_chapa_pilar(M,V,T,aco_chapa,enrijecedor,perfil_pilar,parafuso,gamma):
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    k=0

    i = 0
    while i < len(parafuso.diametros_disponiveis):
        d = parafuso.diametros_disponiveis[i]
        parafuso.diametro(d) 

        [chapa,ver_parafuso,N_parafusos,y_inicio, y_fim] = arranjo_chapa_parafusos(perfil_pilar,parafuso,enrijecedor)

        chapa.material(aco_chapa)

        #Cálculo da espessura da chapa e do enrijecedor
        if enrijecedor == 0:
            #Cálculo da espessura solicitada pela área externa as mesas:
            vinculacao_externa="F"

            b_ext = chapa.B
            a_ext = y_inicio - perfil_pilar.t_f

            t_ext = esp_chapa_roark(M,V,vinculacao_externa,chapa,a_ext,b_ext)

            #Cálculo da espessura solicitada pela área interna as mesas:
            vinculacao_interna = "B"

            a_int = (chapa.B/2) - (perfil_pilar.t_w/2)
            b_int = y_fim - y_inicio            

            t_int = esp_chapa_roark(M,V,vinculacao_interna,chapa,a_int,b_int)
        else:
            #Cálculo da espessura solicitada pela área externa as mesas:
            vinculacao_externa="E"

            b_ext = chapa.B/2
            a_ext = y_inicio - perfil_pilar.t_f

            t_ext = esp_chapa_roark(M,V,vinculacao_externa,chapa,a_ext,b_ext)

            esp_enj =dim_enrijecedores(M,V,chapa,0,a_ext,b_ext)

            #Cálculo da espessura solicitada pela área interna as mesas:
            vinculacao_interna = "B"

            a_int = (chapa.B/2) - (perfil_pilar.t_w/2)
            b_int = (perfil_pilar.h - 2*perfil_pilar.t_f)/2            

            t_int = esp_chapa_roark(M,V,vinculacao_interna,chapa,a_int,b_int)   

        #Critério de parada caso não haja chapa ou enrijecedor para essa configuração:
        t=max(t_ext,t_int)
        maiores_t = [e for e in chapa.espessuras_disponiveis if e > t]  # Filtra apenas valores maiores que a espessura calculada para a chapa
        if not maiores_t :
                return ["A ligação não aguenta a solicitação desejada (A chapa requisitada é muito expessa), Aumente o perfil"] 

        if enrijecedor == 1:
            maiores_enj = [e for e in chapa.espessuras_disponiveis if e > esp_enj]  # Filtra apenas valores maiores que a espessura calculada para o enrijecedor
            if min(maiores_enj) > perfil_pilar.t_f:
                return ["A ligação não aguenta a solicitação desejada (O enrijecedor requisitado é muito expesso), Aumente o perfil"]  

        #Resistentes do parafuso para tração e cisalhamento
        r_p_t=resistencia_parafuso_tração(parafuso,gamma)
        r_p_v=resistencia_parafuso_cisalhamento(parafuso,gamma)

        #Solicitantes no parafuso para tração e cisalhamento
        s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, parafuso , k)
        s_p_t = solicitante_parafuso_tração(V,N_parafusos)
        s_p_v = solicitante_parafuso_cisalhamento(T,N_parafusos)

        #Curva de interação (Sendo aplicada considerando que todos os parafusos estão solicitados conforme o parafuso mais solicitado)
        curva=(((s_p_t + s_p_m)/r_p_t)**2 + (s_p_v/r_p_v)**2)
        #Critério 6.3.3.4 da NBR 8800:2024
        if curva > 1:
            if k<(N_parafusos/2):
                k+=1
                continue
            else:
                k=0
                i+=1
                continue
        else:
            if enrijecedor == 0:
                return [k,parafuso,chapa,ver_parafuso,min(maiores_t)] 
            else:                  
                return [k,parafuso,chapa,ver_parafuso,min(maiores_t),min(maiores_enj)] 








