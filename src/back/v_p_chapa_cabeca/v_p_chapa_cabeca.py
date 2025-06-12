import pandas as pd
import numpy as np
from back.design_functions import (dist_min_borda_pol,registrar_marcha,
    registrar_marcha2,registrar_tabela,resistencia_parafuso_tração,resistencia_parafuso_cisalhamento,
    solicitante_parafuso_tração, solicitante_parafuso_cisalhamento,solicitante_parafuso_momento, 
    parametro_b,y_linha_neutra,
    )
from back.domain.chapa import ChapaCabeca, Chapa
from back.domain.parafuso import Parafuso
from back.domain.perfil import Perfil
from materials_constants import DIMENSOES_PERFIS


##### Da Disposição

#Obtém os valorea arbitrados das disposições contrutivas, conforme catálogo da Gerdau
def arranjo_chapa_parafusos(perfil: Perfil, parafuso: Parafuso) -> tuple[Chapa, pd.DataFrame]:
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

        disposicao = disposicao_parafusos(h, b, e2, e1, perfil.t_f, qtd)

        #B_gerdau = max(dados_chapa["B"],perfil.b_f + 25) #mm     Segundo Item 6.1.1 do manual da Gerdau ou valores arbitrados para o perfil segundo o Manual da Gerdau

        B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

        #B = max(B_norma,B_gerdau) 
        chapa = ChapaCabeca(B_norma,h,a)

        return (chapa,disposicao)

    raise ValueError("Perfil não encontrado no Catálogo da Gerdau.")  # nunca alcançado, mas necessário para tipagem

#Função relativa a disposição dos parafusos na chapa
def disposicao_parafusos(h: float, b: float, e2: float, e1: float, t_f: float, qtd: int) -> pd.DataFrame:
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


def dim_chapa_parafuso(M: float, V: float, T: float, perfil: Perfil, parafuso: Parafuso, gamma: list) -> list[str] | tuple[int,Parafuso,float,Chapa, pd.DataFrame] | None:  #Item 6.3.3.4 da NBR 8800:2024
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    k=0
    registrar_marcha("Dimensionamento da ligação que faz conexão da viga via chapa de cabeça com pilar \n")
    i = 0
    while i < len(parafuso.diametro_pol):
        d = parafuso.diametro_mm[i]
        parafuso.d = d
        registrar_marcha2(f"Interação {i} : cálculo com parafuso de diâmetro {d} pol")
        registrar_marcha(f" \n Interação {k} para linha neutra: ou seja, é estimado que a linha neutra esteja abaixo do parafuso n° {k+1} e no mínimo na altura do parafuso {k} de baixo para cima \n")

        #Arranjo da chapa e dos parafusos 
        [chapa,ver_parafuso] = arranjo_chapa_parafusos(perfil,parafuso)

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
            return (k,parafuso,y_ln,chapa,ver_parafuso) 
    return ["A ligação não aguenta a solicitação desejada, modifique as condições de contorno do problema, como por exemplo, aumentar o perfil..."]    

