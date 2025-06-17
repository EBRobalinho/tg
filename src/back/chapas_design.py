import pandas as pd
import numpy as np
from back.bolt_design import (
    solicitante_parafuso_tração,
    resistencia_parafuso_tração,
    resistencia_parafuso_cisalhamento,
    resistencia_total,
    solicitante_parafuso_momento,
    y_linha_neutra,
    solicitante_parafuso_cisalhamento,
    solicitante_total
)
from back.logs import registrar_marcha, registrar_marcha2, registrar_tabela
from back.norms import dist_min_borda_pol, parametro_b
from back.domain.chapa import ChapaCabeca, ChapaExtremidade
from back.domain.parafuso import Parafuso
from back.domain.perfil import Perfil
from back.materials_constants import DIMENSOES_PERFIS
from back.utils import exp_placa, criterio_cisalhamento_chapa
from back.weld_design import espessura_solda
from back.domain.materials import Aço
from back.domain.solda import Solda
from math import floor
from back.utils import esp_chapa_roark, dim_enrijecedores
##### Da Disposição

#Obtém os valorea arbitrados das disposições contrutivas, conforme catálogo da Gerdau
def arranjo_chapa_cabeca_parafusos(perfil: Perfil, parafuso: Parafuso) -> tuple[ChapaCabeca, pd.DataFrame]:
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    nome_perfil = perfil.nome
    if nome_perfil in DIMENSOES_PERFIS:

        dados_chapa = DIMENSOES_PERFIS[nome_perfil]

        b = parametro_b(parafuso.d)  # Distância da face mais próxima da mesa até a linha de furação

        a = max(b, dist_min_borda_pol(parafuso.d_pol))  # Fato arbitrado pelo manual da Gerdau e item 6.3.11.1 da NBR 8800:2024

        h = perfil.h  # Altura total do perfil Gerdau

        e1 = max(dados_chapa.get("e1") or 0, 3 * parafuso.d)  # Distância horizontal entre parafusos (na minha linha), o critério vem do item 6.3.9 da NBR 8800:2024

        e2 = max(dados_chapa["e2"], dist_min_borda_pol(parafuso.d_pol))  # Distância horizontal entre parafuso-borda (na minha linha) e item 6.3.11.1 da NBR 8800:2024

        t_w = perfil.t_w

        if (e1 - t_w)*0.5 < dist_min_borda_pol(parafuso.d_pol):  #Verifica se a distância entre o furo e o perfil é maior que a distância mínima
            e1 = 2*dist_min_borda_pol(parafuso.d_pol) + t_w

        qtd = int(dados_chapa.get("qtd", 6))

        disposicao = disposicao_chapa_cabeca_parafusos(h, b, e2, e1, perfil.t_f, qtd)

        #B_gerdau = max(dados_chapa["B"],perfil.b_f + 25) #mm     Segundo Item 6.1.1 do manual da Gerdau ou valores arbitrados para o perfil segundo o Manual da Gerdau

        B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

        #B = max(B_norma,B_gerdau) 
        chapa = ChapaCabeca(B_norma,h,a)

        return (chapa,disposicao)

    raise ValueError("Perfil não encontrado no Catálogo da Gerdau.")  # nunca alcançado, mas necessário para tipagem

#Função relativa a disposição dos parafusos na chapa
def disposicao_chapa_cabeca_parafusos(h: float, b: float, e2: float, e1: float, t_f: float, qtd: int) -> pd.DataFrame:
    if qtd == 12:
        # Definir as posições de x para as 4 posições diferentes
        x_positions = [e2, e2 + e1, e2 + 2*e1 , e2 + 3*e1]
        
        # Para 3 camadas, vamos repetir as posições de x
        parafusos_x = x_positions * 3 
        
        # Definir as posições de y
        y_positions = [
            20 + t_f + b,  # Primeira camada
            20 + h - t_f - b,  # Segunda camada
            20 + h + b,  # Terceira camada
        ]
        
        # Repetir cada camada (camada 1, camada 2, camada 3)
        parafusos_y = (
            [y_positions[0], y_positions[0]] * 2  
            + [y_positions[1], y_positions[1]] * 2  
            + [y_positions[2], y_positions[2]] * 2  
        )
        # Criar o DataFrame com as 12 posições
        data = {
            "parafuso": list(range(1, 13)),
            "x (mm)": parafusos_x,
            "y (mm)": parafusos_y
        }

        return pd.DataFrame(data)
    elif qtd == 6:
        # Definir as posições de x para as 2 posições diferentes
        x_positions = [e2, e2 +e1]
        
        # Para 3 camadas, vamos repetir as posições de x
        parafusos_x = x_positions * 3 
        
        # Definir as posições de y
        y_positions = [
            20 + t_f + b,  # Primeira camada
            20 + h - t_f - b,  # Segunda camada
            20 + h + b,  # Terceira camada
        ]
        
        # Repetir cada camada (camada 1, camada 2, camada 3)
        parafusos_y = (
            [y_positions[0], y_positions[0]]   
            + [y_positions[1], y_positions[1]]  
            + [y_positions[2], y_positions[2]]   
        )
        # Criar o DataFrame com as 6 posições
        data = {
            "parafuso": list(range(1, 7)),
            "x (mm)": parafusos_x,
            "y (mm)": parafusos_y
        }
        return pd.DataFrame(data)
    raise ValueError("Perfil não disponível no Manual da Gerdau.")  # nunca alcançado, mas necessário para tipagem
    
#####  DO Dimensionamento


def dim_chapa_cabeca(M: float, V: float, T: float, perfil: Perfil, aco : Aço, chapa_rigida: int, parafuso: Parafuso, solda: Solda, gamma: list) -> list[str] | tuple[int,Parafuso,float,ChapaCabeca, pd.DataFrame, int, float]:  #Item 6.3.3.4 da NBR 8800:2024
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    k=0
    registrar_marcha("Dimensionamento da ligação que faz conexão da viga via chapa de cabeça com pilar \n")
    i = 0
    while i < len(parafuso.diametro_pol):
        d = parafuso.diametro_mm[i]
        parafuso.d = d
        parafuso.diam_pol()
        parafuso.area_bruta()
        registrar_marcha2(f"Interação {i} : cálculo com parafuso de diâmetro {d} pol")
        registrar_marcha(f" \n Interação {k} para linha neutra: ou seja, é estimado que a linha neutra esteja abaixo do parafuso n° {k+1} e no mínimo na altura do parafuso {k} de baixo para cima \n")

        #Arranjo da chapa e dos parafusos 
        [chapa,ver_parafuso] = arranjo_chapa_cabeca_parafusos(perfil,parafuso)

        registrar_tabela("Vértices da chapa", chapa.df)
        
        #Posição dos parafusos em y
        posição=np.unique(ver_parafuso["y (mm)"])
        registrar_tabela("Vértices dos Parafusos", ver_parafuso)

        #Número de parafusos na seção:
        N_parafusos = ver_parafuso.shape[0]
        registrar_marcha(f"Número de parafusos calculados = {N_parafusos} \n")

        #Resistentes do parafuso para tração e cisalhamento
        r_p_t=resistencia_parafuso_tração(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso a tração = {r_p_t} KN \n")

        r_p_v=resistencia_parafuso_cisalhamento(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso a cisalhamento = {r_p_v} KN \n")

        #Solicitantes no parafuso para tração e cisalhamento
        s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, parafuso , k)
        registrar_marcha(f"Solicitante de tração advinda do momento no parafuso = {s_p_m} KN \n")
        s_p_t = solicitante_parafuso_tração(T,N_parafusos)
        registrar_marcha(f"Solicitante de tração pura no parafuso = {s_p_t} KN \n")
        s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
        registrar_marcha(f"Solicitante de cisalhamento no parafuso = {s_p_v} KN \n")

        #Curva de interação (Sendo aplicada considerando que todos os parafusos estão solicitados conforme o parafuso mais solicitado)
        curva=(((s_p_t + s_p_m)/r_p_t)**2 + (s_p_v/r_p_v)**2)
        registrar_marcha(f"\nCalculo da circunferência de interação, conforme previsto em 6.3.3.4 da 8800:2024 {curva}=((({s_p_t} + {s_p_m})/{r_p_t})**2 + ({s_p_v}/{r_p_v})**2)")
        #Critério 6.3.3.4 da NBR 8800:2024
        if curva > 1:
            if k<len(posição):
                k+=1
                registrar_marcha(f'\n{curva}>1 : Mudança da linha neutra entre os parafusos, para k={k}.')
                continue
            else:
                k=0
                i+=1
                registrar_marcha(f'\n{curva}> 1 e não há mais posições para linha neutra. Zera a linha neutra e calcula para o próximo diâmetro comercial.')
                continue
        else:
            y_ln = y_linha_neutra(chapa.B,ver_parafuso, parafuso.d , k)

            
            #Calculo da espessura da chapa e da solda
            r_parafuso_total = resistencia_total(parafuso,gamma)
            #Considera os parafusos trabalhando plasticamente de forma que cada um receba a mesma carga
            s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, parafuso , k)
            s_p_t = solicitante_parafuso_tração(T,N_parafusos)
            s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)

            espessura_placa = exp_placa(aco,chapa,chapa_rigida,ver_parafuso,parafuso.d,r_parafuso_total, (s_p_m + s_p_t), gamma)

            if isinstance(espessura_placa, list) and espessura_placa == ["A ligação não aguenta a solicitação desejada."]:  # se for string, é um erro
                registrar_marcha("\n Resultado não foi encontrado!\n")
                raise ValueError("A ligação não aguenta a solicitação desejada.")  # lança a string como erro
            if isinstance(espessura_placa, float):
                espessura__solda = espessura_solda(M,V,T,solda,perfil,espessura_placa,gamma)
                C = criterio_cisalhamento_chapa(chapa,s_p_v,espessura_placa,ver_parafuso,parafuso,aco,gamma)
                if C[0] == 0:
                    raise ValueError(C[1])
                else:
                    return (k,parafuso,y_ln,chapa,ver_parafuso, espessura__solda, espessura_placa) 
    return ["A ligação não aguenta a solicitação desejada, modifique as condições de contorno do problema, como por exemplo, aumentar o perfil..."]    


def disposicao_chapa_extremidade_parafusos(t_f: float, b: float, c: float, e2: float, e1: float, h_gerdau: float) -> pd.DataFrame:
    x_positions = [e2, e2 + e1]

    parafusos_x = []
    parafusos_y = []

    z_i = b
    z_f = h_gerdau - b
    parafusos_x.extend(x_positions)
    parafusos_y.extend([z_i, z_i])
    parafusos_x.extend(x_positions)
    parafusos_y.extend([z_f, z_f])

    n_vertical = (h_gerdau - 2 * b)//c 

    for i in range(1, int(n_vertical)):
        y = b + i * (h_gerdau - 2 * b) / n_vertical
        parafusos_x.extend(x_positions)
        parafusos_y.extend([y, y])


    data = {
        "parafuso": list(range(1, len(parafusos_x) + 1)),
        "x (mm)": parafusos_x,
        "y (mm)": parafusos_y
    }


    return pd.DataFrame(data)

#Obtém os valorea arbitrados das disposições contrutivas, conforme catálogo da Gerdau
def arranjo_chapa_extremidade_parafusos(perfil: Perfil, parafuso: Parafuso) -> tuple[ChapaExtremidade, pd.DataFrame,int]:
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    h_gerdau = perfil.h - 2*perfil.t_f   #Altura total do perfil Gerdau

    b = dist_min_borda_pol(parafuso.d_pol) #Distância vertical do parafuso mais em cima até a borda da placa 

    e1 = max(120,3*parafuso.d)  #Distância horizontal entre parafusos (na minha linha, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    c  = max(75,3*parafuso.d)  #Distância vertical entre parafusos (na minha coluna, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    e2 = max(40,dist_min_borda_pol(parafuso.d_pol)) #Distância horizontal entre parafuso-borda (na minha linha, segundo o manual da Gerdau) e item 6.3.11.1 da NBR 8800:2024

    disposicao = disposicao_chapa_extremidade_parafusos(perfil.t_f, b,c, e2, e1, h_gerdau)

    N_parafusos = int((disposicao.shape[0])/2)

    B_gerdau = 200 #mm     Segundo Item 4.1.1 do manual da Gerdau

    B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

    B = max(B_norma,B_gerdau) 

    #h_parafusos = max(disposicao["y (mm)"]) + e2

    h = h_gerdau      

    chapa = ChapaExtremidade(B,h,b)

    return (chapa,disposicao,N_parafusos)


def dim_chapa_extremidade(V: float, T: float, perfil: Perfil, parafuso: Parafuso, material: Aço, rigida: int, solda: Solda, gamma: list) -> list[str] | tuple[ChapaExtremidade, float, Parafuso, pd.DataFrame, Solda, float] | None:  #Item 6.3.3.4 da NBR 8800:2024
    #Tem de variar no espaço de busca os diâmetros
    registrar_marcha("Dimensionamento da ligação que faz conexão da viga via chapa de extremidade com pilar \n")

    for d in parafuso.diametro_mm:
        registrar_marcha2(f"Cálculo com parafuso de diâmetro {d} pol")
        #Atualiza o diâmetro de busca
        parafuso.d = d  
        parafuso.diam_pol()
        parafuso.area_bruta()
        #Arranjo da chapa e dos parafusos
        [chapa, ver_parafuso, N_parafusos] = arranjo_chapa_extremidade_parafusos(perfil, parafuso)

        registrar_tabela("Vértices da chapa", chapa.df)
        registrar_tabela("Vértices dos Parafusos", ver_parafuso)

        N_parafusos = ver_parafuso.shape[0]
        registrar_marcha(f"Número de parafusos calculados = {N_parafusos} \n")

        #Resistentes do parafuso para tração e cisalhamento
        r_p_t=resistencia_parafuso_tração(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso a tração = {r_p_t} KN \n")

        r_p_v=resistencia_parafuso_cisalhamento(parafuso,gamma)
        registrar_marcha(f"Resistência do parafuso a cisalhamento = {r_p_v} KN \n")

        r_parafuso_total = resistencia_total(parafuso,gamma)

        #Solicitantes no parafuso para tração e cisalhamento
        s_p_t = solicitante_parafuso_tração(T,N_parafusos)
        registrar_marcha(f"Solicitante de tração pura no parafuso = {s_p_t} KN \n")

        s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
        registrar_marcha(f"Solicitante de cisalhamento no parafuso = {s_p_v} KN \n")
        
        s_parafuso_total = solicitante_total(T,V,N_parafusos)

        #Curva de interação Item 6.3.3.4 da NBR 8800:2024
        curva=(((s_p_t)/r_p_t)**2 + (s_p_v/r_p_v)**2)
        registrar_marcha(f"\nCalculo da circunferência de interação, conforme previsto em 6.3.3.4 da 8800:2024 {curva}=((({s_p_t})/{r_p_t})**2 + ({s_p_v}/{r_p_v})**2)")
        
        if (curva > 1) and d == max(parafuso.diametro_mm):
            return ["A ligação não aguenta a solicitação desejada, modifique as condições de contorno do problema, como por exemplo, aumentar o perfil..."] 
        if  (curva > 1):
            registrar_marcha(f'\n{curva}> 1, calcula para o próximo diâmetro comercial.')
        else:   
            #Cálculo da espessura da placa
            exp = exp_placa(material, chapa, rigida, ver_parafuso, d, r_parafuso_total,s_parafuso_total,gamma)
            if isinstance(exp, str):  # se for string, é um erro
                return [exp] # lança a string como erro
            else:
                if isinstance(exp, float):
                    if (exp - float(16))>=0: #Item 10.14.9.1 do livro de Dimensionamento de Elementos Estruturais e mistos Aço e concreto.
                        registrar_marcha(f'\n Como a espessura da placa foi {exp} > 16, a chapa não garante a flexibilidade da ligação.')
                        return ["A Chapa tem uma espessura maior que 16 mm o que não garante a flexibilidade da ligação."] 
                    #Cálculo da solda:
                    esp_solda = espessura_solda(0,V,T,solda,perfil,exp,gamma)

                    s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
                    C = criterio_cisalhamento_chapa(chapa,s_p_v,exp,ver_parafuso,parafuso,material,gamma)

                    if C[0] == 0:
                        raise ValueError(C[1])

                    return (chapa,exp,parafuso,ver_parafuso,solda,esp_solda)
            break


def disposicao_chapa_viga_pilar_parafusos(t_f: float, b: float, b_linha: float, c: float, e2: float, e1: float, h: float):
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
def arranjo_chapa_viga_pilar_parafusos(perfil: Perfil, parafuso: Parafuso, enrijecedor: int) -> tuple[ChapaExtremidade, pd.DataFrame, int, float, float]:
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    B_pilar = perfil.b_f #mm  

    h_pilar = perfil.h 
    
    b_linha = parametro_b(parafuso.d) # Distância Gerdau entre o centro do parafuso e face mais próxima da mesa do perfil

    b = dist_min_borda_pol(parafuso.d_pol) #Distância vertical do parafuso mais em cima até a borda da placa 

    e2 = max(40,b) #Distância horizontal entre parafuso-borda (na minha linha, segundo o manual da Gerdau) e item 6.3.11.1 da NBR 8800:2024

    e1 = max(120,3*parafuso.d,B_pilar - 2*e2)  #Distância horizontal entre parafusos (na minha linha, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    c  = 3*parafuso.d  #Distância vertical entre parafusos (na mesma coluna, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    disposicao = disposicao_chapa_viga_pilar_parafusos(perfil.t_f, b,b_linha,c, e2, e1, h_pilar)

    N_parafusos = (disposicao.shape[0])

    B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

    B = max(B_norma,B_pilar) 

    y_inicio = min(disposicao['y (mm)']) + b_linha + perfil.t_f   #considerações a partir da distância recomendada pelo manual da Gerdau

    y_fim = max(disposicao['y (mm)']) - b_linha - perfil.t_f

    h_chapa = max(disposicao["y (mm)"]) + b

    chapa = ChapaExtremidade(B,h_chapa,b)

    return (chapa,disposicao,N_parafusos,y_inicio, y_fim)

def dim_chapa_viga_pilar(M: float, V: float, T: float, aco_chapa: Aço, enrijecedor: int, altura: float, perfil_pilar: Perfil, parafuso: Parafuso, solda: Solda, gamma: list) -> tuple[int,Parafuso, ChapaExtremidade, pd.DataFrame, float, float,int]|list[str]:
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    k=0
    registrar_marcha("Dimensionamento da ligação que faz conexão da viga sobre pilar \n")
    registrar_marcha("O dimensionamento dos enrijecedores será feito conforme metodologia de Roark Formulas for Stress and Strain 7° edition \n")
    i = 0
    while i < len(parafuso.diametro_mm):
        d = parafuso.diametro_mm[i]
        parafuso.d = d  # Atualiza o diâmetro do parafuso
        parafuso.diam_pol()
        parafuso.area_bruta()
        registrar_marcha2(f"Interação i={i} : cálculo com parafuso de diâmetro {d} pol")
        registrar_marcha(f"\nInteração k={k} para linha neutra: ou seja, é estimado que a linha neutra esteja abaixo do parafuso n° {k+1} e no mínimo na altura do parafuso {k} de baixo para cima \n")
        [chapa,ver_parafuso,N_parafusos,y_inicio, y_fim] = arranjo_chapa_viga_pilar_parafusos(perfil_pilar,parafuso,enrijecedor)
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
            espessura_chapa = min(maiores_t)

            s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos) 

            C = criterio_cisalhamento_chapa(chapa,s_p_v,espessura_chapa,ver_parafuso,parafuso,aco_chapa,gamma)

            if C[0] == 0:
                raise ValueError(C[1])

            # Calculo da espessura da solda
            espessura__solda = espessura_solda(M,T,V,solda,perfil_pilar,espessura_chapa,gamma)
            print("chegouaqq")

            return (k,parafuso,chapa,ver_parafuso,espessura_chapa,min(maiores_enj),espessura__solda) 
        

    return ["A ligação não aguenta a solicitação desejada."]



