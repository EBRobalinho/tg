import pandas as pd
import numpy as np
from design_functions import *
from class_materials import *

##### Da Disposição

#Obtém os valorea arbitrados das disposições contrutivas, conforme catálogo da Gerdau
def arranjo_chapa_parafusos(perfil,disposicoes_gerdau,parafuso):
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    nome_perfil = perfil.nome
    if nome_perfil in disposicoes_gerdau:

        dados_chapa = disposicoes_gerdau[nome_perfil]

        b = parametro_b(parafuso.diametro_mm) #Distância da face mais próxima da mesa até a linha de furação 

        a=max(b,dist_min_borda_pol(parafuso.diametro_pol)) #Fato arbitrado pelo manual da Gerdau e item 6.3.11.1 da NBR 8800:2024

        h = perfil.h  #Altura total do perfil Gerdau

        e1 = max(dados_chapa.get("e1") or 0, 3 * parafuso.diametro_mm) #Distância horizontal entre parafusos (na minha linha), o critério vem do item 6.3.9 da NBR 8800:2024

        e2 = max(dados_chapa["e2"],dist_min_borda_pol(parafuso.diametro_pol)) #Distância horizontal entre parafuso-borda (na minha linha) e item 6.3.11.1 da NBR 8800:2024

        qtd = dados_chapa.get("qtd", 6) 

        disposicao = disposicao_parafusos(h, b, e2, e1, perfil.t_f, qtd)

        B_gerdau = max(dados_chapa["B"],perfil.b_f + 25) #mm     Segundo Item 6.1.1 do manual da Gerdau

        B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

        B = max(B_norma,B_gerdau) 

        chapa = ChapaCabeca(B,h,a)
        
 
        return [chapa,disposicao]

#Calcula a distância da face da mesa da viga a linha de furação
def parametro_b(diametro):  # Segundo Item 6.1.1 do manual da Gerdau
    
    if diametro <= pol_to_mm(3/4):
        return 30
    elif diametro == pol_to_mm(7/8):
        return 35
    else:
        return 40

#Função relativa a disposição dos parafusos na chapa
def disposicao_parafusos(h, b, e2, e1, t_f, qtd):
    if qtd ==12: 
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
    elif qtd ==6:
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
    
#####  DO Dimensionamento

# Funções para o cálculo do diâmetro do parafuso e da profundidade da linha neutra:

def y_linha_neutra(B,ver_parafuso,diametro, k):  #Posição da linha neutra da seção transversal dada

    #Posição dos parafusos em y
    posição=coluna_parafusos(ver_parafuso)

    N = len(ver_parafuso)  #Número total de parafusos
    n = (ver_parafuso["x (mm)"] == ver_parafuso["x (mm)"].iloc[0]).sum()  #número de parafusos por coluna
    n_p_c = N/n  #número de parafusos por camada

    #Somatório de todas as posições (em y) das barras de aço
    S=0
    for i in range(k,n,1):
        S = S + abs(posição[i])
    #Raiz positiva da equação do 2º grau que retorna as duas coordenadas possíveis para a posição da linha neutra
    y_ln = ( -(np.pi*n_p_c)*((diametro**2)*(n-k))/(4*B) + (np.sqrt((((np.pi*n_p_c*(n-k)))**2)*(diametro**4) + 8*B*(np.pi*n_p_c)*S*(diametro**2)  ) /(4*B) ) )
    return y_ln

def w_inercia(B,ver_parafuso,diametro, k):

    #Posição dos parafusos em y
    posição=coluna_parafusos(ver_parafuso)
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

    return w

def solicitante_parafuso_momento(M,B, ver_parafuso , parafuso , k):  #Cálculo da tração solicitante no parafuso mais externo
    A_s = parafuso.A_g
    w_secao=w_inercia(B, ver_parafuso, parafuso.diametro_mm , k)
    return M*A_s/w_secao

def coluna_parafusos(ver_parafuso): #Considera a posição de apenas uma coluna de parafusos
    return np.unique(ver_parafuso["y (mm)"])

def dim_chapa_parafuso(M,V,T,perfil,disposicoes_gerdau_chapa_cabeca,parafuso,gamma):  #Item 6.3.3.4 da NBR 8800:2024
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    k=0
    solução = pd.DataFrame(columns=['k', 'diametro', 'y_ln'])

    for d in parafuso.diametros_disponiveis:

        parafuso.diametro(d)  

        #Arranjo da chapa e dos parafusos 
        [chapa,ver_parafuso] = arranjo_chapa_parafusos(perfil,disposicoes_gerdau_chapa_cabeca,parafuso)

        #Posição dos parafusos em y
        posição=coluna_parafusos(ver_parafuso)
        #Número de parafusos na seção:
        N_parafusos = ver_parafuso.shape[0]

        #Resistentes do parafuso para tração e cisalhamento
        r_p_t=resistencia_parafuso_tração(parafuso,gamma)
        r_p_v=resistencia_parafuso_cisalhamento(parafuso,gamma)

        #Solicitantes no parafuso para tração e cisalhamento
        s_p_m =solicitante_parafuso_momento(M,chapa.B,ver_parafuso, parafuso , k)
        s_p_t = solicitante_parafuso_tração(T,N_parafusos)
        s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)

        #Curva de interação (Sendo aplicada considerando que todos os parafusos estão solicitados conforme o parafuso mais solicitado)
        curva=(((s_p_t + s_p_m)/r_p_t)**2 + (s_p_v/r_p_v)**2)
        #Critério 6.3.3.4 da NBR 8800:2024
        if curva > 1:
            if k<len(posição):
                k=k+1
            else:
                k=0
                continue
        else:
            y_ln = y_linha_neutra(chapa.B,ver_parafuso, parafuso.diametro_mm , k)
            return [k,parafuso,y_ln,chapa,ver_parafuso] 

#Cálculo da espessura da chapa de cabeça:

def larg_trib(posição,b):

    # Encontrar o maior valor de y
    max_y = posição["y (mm)"].max()

    # Filtrar os parafusos que estão na camada com maior y
    parafusos_maior_y = posição[posição["y (mm)"] == max_y]

    #Distância entre parafusos internos da camada (considerando a distância entre os dois primeiros parafusos)
    eint = abs(parafusos_maior_y["x (mm)"].iat[0] - parafusos_maior_y["x (mm)"].iat[1])

    #Distância entre parafusos externos da camada (Ou seja a distância de qualquer parafuso externo para sua borda na horizontal)
    eext =  parafusos_maior_y["x (mm)"].iat[0]

    pint = min(eint,3.5*b)

    pext = min(0.5*eint,1.75*b) + min(eext,1.75*b)

    #Se escolher o p minimo, aumenta o denominador, aumentando a espessura, segundo item 6.3.5.4 da NBR 8800;2024

    return min(pext,pint)

def exp_placa(Aço, Secão, rigida, posição, diametro, F_r_total,F_t_Sd,gamma):

    a =Secão.a
    b = parametro_b(diametro) #Distância da face mais próxima da mesa até a linha de furação 

    B = Secão.B

    p = larg_trib(posição,b)

    delta = 1- ((furo_padrao_pol(diametro))/p)      #Considerando a dimensão do furo na largura tributária como se fosse o furo padrão

    beta = ((a + 0.5*diametro)/(b - 0.5*diametro))*((F_r_total)/(F_t_Sd) - 1)

    if beta >=1:
        alfa=1
    elif beta>0 and beta<1:
        alfa = min(1,((beta)/delta*(1-beta)))

    if rigida == 1:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p))*np.sqrt(1000)

    else:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p*(1+delta*alfa)))*np.sqrt(1000)

    maiores = [e for e in Secão.espessuras_disponiveis if e > t]  # Filtra apenas valores maiores que a espessura calculada

    return min(maiores) if maiores else None  # Retorna o menor dos maiores ou None se não houver

#Cálculo de espessura mínima de solda necessária:
    
def espessura_solda(M,V,T,solda,perfil,espessura_chapa,filete_duplo,gamma):

    tal_r1 = solda.f_uw_mpa*0.6/gamma[1]     #Mpa    #Tabela 9, item 6.2.5.1 da NBR 8800:2024 (Relativa a tensão resistida pela solda)
    tal_r2 = perfil.f_u*0.6/gamma[0]      #Letra b do item 6.5.5 da NBR 8800:2024 (relativa a ruptura do metal base)

    tal_r = min(tal_r1,tal_r2)
    tal_m = tensao_cisalhante_momento_filete(perfil,M,perfil.h_w*0.5,filete_duplo)
    tal_v = tensao_cisalhante_cortante_filete(perfil,V,filete_duplo)
    tal_n = tensao_cisalhante_normal_filete(perfil,T,filete_duplo)
    tal_s = np.sqrt((tal_m)**2 + (tal_v)**2 + (tal_n)**2)*1000   #Tensão solicitante em Mpa*mm    

    esp = tal_s/tal_r

    esp_metal_base = min(espessura_chapa, perfil.t_w)
    esp_minima = criterio_min_solda_filete(esp_metal_base)

    esp_final = max(esp_minima,esp)

    return esp_final


