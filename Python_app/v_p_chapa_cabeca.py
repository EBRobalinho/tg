import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from main import *

#Classe relativa as dimensões das chapas de cabeça (conforme catálogo da Gerdau)

class Chapa:
    def __init__(self, B, h, a):
        """Inicializa a classe com os valores B, h e a."""
        self.B = B #Largura da chapa em mm
        self.h = h #Altura da viga que vai na chapa
        self.a = a #distância do parafuso superior até borda da chapa
        self.df = self.vertices_chapa()
    
    def vertices_chapa(self):
        """Cria o DataFrame com os vértices e coordenadas."""
        data = {
            "vértice": [1, 2, 3, 4],
            "x (mm)": [0, self.B, self.B, 0],
            "y (mm)": [0, 0, 20 + self.h + 2 * self.a, 20 + self.h + 2 * self.a]
        }
        return pd.DataFrame(data)

    def mostrar_dataframe(self):
        """Retorna o DataFrame."""
        return self.df

def chapa_para_perfil(perfil):
    # Mapeamento dos nomes dos perfis para os valores de B e a
    mapeamento_chapas = {
        "W_150x13_0": {"B": 130, "a": 30},
        "W_150x18_0": {"B": 130, "a": 30},
        "W_150x24_0": {"B": 130, "a": 30},
        "W_200x15_0": {"B": 130, "a": 30},
        "W_200x19_3": {"B": 130, "a": 30},
        "W_200x22_5": {"B": 130, "a": 30},
        "W_200x26_6": {"B": 160, "a": 30},
        "W_200x31_3": {"B": 160, "a": 30},
        "W_250x17_9": {"B": 130, "a": 30},
        "W_250x22_3": {"B": 130, "a": 30},
        "W_250x25_3": {"B": 130, "a": 30},
        "W_250x28_4": {"B": 130, "a": 30},
        "W_250x32_7": {"B": 160, "a": 35},
        "W_250x38_5": {"B": 160, "a": 35},
        "W_250x44_8": {"B": 160, "a": 35},
        "W_310x21_0": {"B": 130, "a": 30},
        "W_310x23_8": {"B": 130, "a": 30},
        "W_310x28_3": {"B": 130, "a": 30},
        "W_310x32_7": {"B": 130, "a": 30},
        "W_310x38_7": {"B": 190, "a": 40},
        "W_310x44_5": {"B": 190, "a": 40},
        "W_310x52_0": {"B": 190, "a": 40},
        "W_360x32_9": {"B": 150, "a": 35},
        "W_360x39_0": {"B": 150, "a": 35},
        "W_360x44_6": {"B": 200, "a": 40},
        "W_300x51_0": {"B": 200, "a": 40},
        "W_360x58_0": {"B": 200, "a": 40},
        "W_360x64_0": {"B": 230, "a": 40},
        "W_360x72_0": {"B": 230, "a": 40},
        "W_300x79_0": {"B": 230, "a": 40},
        "W_410x38_8": {"B": 160, "a": 35},
        "W_410x46_1": {"B": 160, "a": 35},
        "W_410x53_0": {"B": 200, "a": 40},
        "W_410x60_0": {"B": 200, "a": 40},
        "W_430x67_0": {"B": 200, "a": 40},
        "W_410x75_0": {"B": 200, "a": 40},
        "W_410x85_0": {"B": 200, "a": 40},
        "W_460x52_0": {"B": 180, "a": 40},
        "W_460x60_0": {"B": 180, "a": 40},
        "W_460x68_0": {"B": 180, "a": 40},
        "W_460x74_0": {"B": 220, "a": 40},
        "W_460x82_0": {"B": 220, "a": 40},
        "W_460x89_0": {"B": 220, "a": 40},
        "W_460x97_0": {"B": 260, "a": 35},
        "W_460x106_0": {"B": 260, "a": 35},
        "W_530x66_0": {"B": 190, "a": 40},
        "W_530x74_0": {"B": 190, "a": 40},
        "W_530x85_0": {"B": 190, "a": 40},
        "W_530x72_0": {"B": 250, "a": 30},
        "W_530x82_0": {"B": 250, "a": 30},
        "W_530x92_0": {"B": 250, "a": 30},
        "W_530x101_0": {"B": 280, "a": 35},
        "W_530x109_0": {"B": 280, "a": 35},
        "W_610x101_0": {"B": 250, "a": 30},
        "W_610x113_0": {"B": 250, "a": 30},
        "W_610x125_0": {"B": 330, "a": 40},
        "W_610x140_0": {"B": 330, "a": 40},
        "W_610x155_0": {"B": 330, "a": 40},
        "W_610x174_0": {"B": 330, "a": 40},
    }

    nome_perfil = perfil.nome
    if nome_perfil in mapeamento_chapas:
        dados_chapa = mapeamento_chapas[nome_perfil]
        B = dados_chapa["B"]
        a = dados_chapa["a"]
        h = perfil.h  # Usando o atributo .h diretamente
        chapa = Chapa(B,h,a)
        return chapa
    else:
        print(f"Não há informações de chapa para o perfil '{nome_perfil}'.")
        return None

#Classe relativa a disposição dos parafusos (conforme catálogo da Gerdau)

class DisposicaoParafusos:
    def __init__(self, B, h, a, e2, e1, t_f, qtd):
        """Inicializa a classe com os valores fornecidos."""
        self.B = B
        self.h = h
        self.a = a
        self.e2 = e2
        self.e1 = e1
        self.t_f = t_f
        if qtd ==12: 
            self.df = self.disposicao_12()
        elif qtd ==6:
            self.df = self.disposicao_6()

    def disposicao_12(self):
        """Gera o DataFrame com as coordenadas dos parafusos."""
        # Definir as posições de x para as 4 posições diferentes
        x_positions = [self.e2, self.e2 + self.e1, self.B - self.e2 - self.e1, self.B - self.e2]
        
        # Para 3 camadas, vamos repetir as posições de x
        parafusos_x = x_positions * 3  # Repetir as 4 posições para as 3 camadas
        
        # Definir as posições de y
        y_positions = [
            20 + self.t_f + self.a,  # Primeira camada
            20 + self.h - self.t_f - self.a,  # Segunda camada
            20 + self.h + self.a,  # Terceira camada
        ]
        
        # Repetir cada camada (camada 1, camada 2, camada 3)
        parafusos_y = (
            [y_positions[0], y_positions[0]] * 2  # Repetir a 1ª camada
            + [y_positions[1], y_positions[1]] * 2  # Repetir a 2ª camada
            + [y_positions[2], y_positions[2]] * 2  # Repetir a 3ª camada
        )
        # Criar o DataFrame com as 12 posições
        data = {
            "parafuso": list(range(1, 13)),
            "x (mm)": parafusos_x,
            "y (mm)": parafusos_y
        }

        return pd.DataFrame(data)
    
    def disposicao_6(self):
            """Gera o DataFrame com as coordenadas dos parafusos."""
            # Definir as posições de x para as 4 posições diferentes
            x_positions = [self.e2, self.B - self.e2]
            
            # Para 3 camadas, vamos repetir as posições de x
            parafusos_x = x_positions * 3  # Repetir as 4 posições para as 3 camadas
            
            # Definir as posições de y
            y_positions = [
                20 + self.t_f + self.a,  # Primeira camada
                20 + self.h - self.t_f - self.a,  # Segunda camada
                20 + self.h + self.a,  # Terceira camada
            ]
            
            # Repetir cada camada (camada 1, camada 2, camada 3)
            parafusos_y = (
                [y_positions[0], y_positions[0]]   # Repetir a 1ª camada
                + [y_positions[1], y_positions[1]]   # Repetir a 2ª camada
                + [y_positions[2], y_positions[2]]   # Repetir a 3ª camada
            )
            # Criar o DataFrame com as 12 posições
            data = {
                "parafuso": list(range(1, 7)),
                "x (mm)": parafusos_x,
                "y (mm)": parafusos_y
            }

            return pd.DataFrame(data)
    
    def mostrar_dataframe(self):
        """Retorna o DataFrame com as posições dos parafusos."""
        return self.df
    
# Mapeamento dos perfis para e2, e1 e qtd
mapeamento_distancias = {
    "W_150x13_0": {"e2": 30, "e1": None, "qtd": 6},
    "W_150x18_0": {"e2": 30, "e1": None, "qtd": 6},
    "W_150x24_0": {"e2": 30, "e1": None, "qtd": 6},
    "W_200x15_0": {"e2": 30, "e1": None, "qtd": 6},
    "W_200x19_3": {"e2": 30, "e1": None, "qtd": 6},
    "W_200x22_5": {"e2": 30, "e1": None, "qtd": 6},
    "W_200x26_6": {"e2": 40, "e1": None, "qtd": 6},
    "W_200x31_3": {"e2": 40, "e1": None, "qtd": 6},
    "W_250x17_9": {"e2": 30, "e1": None, "qtd": 6},
    "W_250x22_3": {"e2": 30, "e1": None, "qtd": 6},
    "W_250x25_3": {"e2": 30, "e1": None, "qtd": 6},
    "W_250x28_4": {"e2": 30, "e1": None, "qtd": 6},
    "W_250x32_7": {"e2": 40, "e1": None, "qtd": 6},
    "W_250x38_5": {"e2": 40, "e1": None, "qtd": 6},
    "W_250x44_8": {"e2": 40, "e1": None, "qtd": 6},
    "W_310x21_0": {"e2": 30, "e1": None, "qtd": 6},
    "W_310x23_8": {"e2": 30, "e1": None, "qtd": 6},
    "W_310x28_3": {"e2": 30, "e1": None, "qtd": 6},
    "W_310x32_7": {"e2": 30, "e1": None, "qtd": 6},
    "W_310x38_7": {"e2": 45, "e1": None, "qtd": 6},
    "W_310x44_5": {"e2": 45, "e1": None, "qtd": 6},
    "W_310x52_0": {"e2": 45, "e1": None, "qtd": 6},
    "W_360x32_9": {"e2": 35, "e1": None, "qtd": 6},
    "W_360x39_0": {"e2": 35, "e1": None, "qtd": 6},
    "W_360x44_6": {"e2": 50, "e1": None, "qtd": 6},
    "W_300x51_0": {"e2": 50, "e1": None, "qtd": 6},
    "W_360x58_0": {"e2": 50, "e1": None, "qtd": 6},
    "W_360x64_0": {"e2": 60, "e1": None, "qtd": 6},
    "W_360x72_0": {"e2": 60, "e1": None, "qtd": 6},
    "W_300x79_0": {"e2": 60, "e1": None, "qtd": 6},
    "W_410x38_8": {"e2": 40, "e1": None, "qtd": 6},
    "W_410x46_1": {"e2": 40, "e1": None, "qtd": 6},
    "W_410x53_0": {"e2": 50, "e1": None, "qtd": 6},
    "W_410x60_0": {"e2": 50, "e1": None, "qtd": 6},
    "W_430x67_0": {"e2": 50, "e1": None, "qtd": 6},
    "W_410x75_0": {"e2": 50, "e1": None, "qtd": 6},
    "W_410x85_0": {"e2": 50, "e1": None, "qtd": 6},
    "W_460x52_0": {"e2": 45, "e1": None, "qtd": 6},
    "W_460x60_0": {"e2": 45, "e1": None, "qtd": 6},
    "W_460x68_0": {"e2": 45, "e1": None, "qtd": 6},
    "W_460x74_0": {"e2": 55, "e1": None, "qtd": 6},
    "W_460x82_0": {"e2": 5, "e1": None, "qtd": 6},
    "W_460x89_0": {"e2": 55, "e1": None, "qtd": 6},
    "W_460x97_0": {"e2": 35, "e1": 60, "qtd": 12},
    "W_460x106_0": {"e2": 35, "e1": 60, "qtd": 12},
    "W_530x66_0": {"e2": 45, "e1": None, "qtd": 6},
    "W_530x74_0": {"e2": 45, "e1": None, "qtd": 6},
    "W_530x85_0": {"e2": 45, "e1": None, "qtd": 6},
    "W_530x72_0": {"qtd": 12, "e2": 30, "e1": 60},
    "W_530x82_0": {"qtd": 12, "e2": 30, "e1": 60},
    "W_530x92_0": {"qtd": 12, "e2": 30, "e1": 60},
    "W_530x101_0": {"qtd": 12, "e2": 35, "e1": 70},
    "W_530x109_0": {"qtd": 12, "e2": 35, "e1": 70},
    "W_610x101_0": {"qtd": 12, "e1": 60, "e2": 30},
    "W_610x113_0": {"qtd": 12, "e1": 60, "e2": 30},
    "W_610x125_0": {"qtd": 12, "e1": 80, "e2": 40},
    "W_610x140_0": {"qtd": 12, "e1": 80, "e2": 40},
    "W_610x155_0": {"qtd": 12, "e1": 80, "e2": 40},
    "W_610x174_0": {"qtd": 12, "e1": 80, "e2": 40},
}

def disposicao_parafusos(perfil_viga):
    """
    Cria um objeto DisposicaoParafusos com base no objeto Perfil da viga.
    """
    nome_perfil_viga = perfil_viga.nome
    if nome_perfil_viga in mapeamento_distancias:
        distancias = mapeamento_distancias[nome_perfil_viga]
        e2 = distancias["e2"]
        e1 = distancias.get("e1")  # Usando .get() para lidar com casos onde e1 pode ser None
        qtd = distancias.get("qtd", 6) # Usando .get() para definir um valor padrão para qtd

        chapa = chapa_para_perfil(perfil_viga)

        if chapa:
            B_chapa = chapa.B
            h_chapa = chapa.h
            a_chapa = chapa.a
            t_f_viga = perfil_viga.t_f
            h_viga = perfil_viga.h

            disposicao = DisposicaoParafusos(B_chapa, h_viga, a_chapa, e2, e1, t_f_viga, qtd)
            return disposicao
        else:
            return None
    else:
        print(f"Não há informações de distâncias de borda para o perfil '{nome_perfil_viga}'.")
        return None

#Funções para o cálculo do diâmetro do parafuso e da linha neutra

def y_linha_neutra(B, posição , diametro , n, k):  #Posição da linha neutra da seção transversal dada
    #Somatório de todas as posições (em y) das barras de aço
    S=0
    for i in range(1,n-k+1,1):
        S = S + abs(posição[i-1])
    y_ln = ( -np.pi*((diametro**2)*(n-k))/(2*B) + (np.sqrt((np.pi**2)*(diametro**4)*(n-k) + 4*B*np.pi*S*(diametro**2)  ) /(2*B) ) )
    return y_ln

def m_inercia(B, posição , diametro , n, k):  #Cálculo do momento de inércia da seção 
    y_ln=y_linha_neutra(B, posição , diametro , n, k)
    S=0
    for i in range(1,n+1,1):
        S = S + (abs(posição[i-1])-y_ln)**2
    i_s = B*(y_ln**3)/3 + np.pi*0.25*(diametro**2)*S
    return i_s

def w_inercia(B, posição , diametro , n, k):
    i_s = m_inercia(B, posição , diametro , n, k)
    y_ln=y_linha_neutra(B, posição , diametro , n, k)
    w = (i_s)/(abs(max(posição)) - y_ln)
    return w

def solicitante_parafuso_tração(M,B, posição , parafuso , n, k):  #Cálculo da tração solicitante no parafuso mais externo
    A_s = parafuso.A_g
    w_secao=w_inercia(B, posição , parafuso.diametro_mm , n, k)
    return M*A_s/w_secao

def solicitante_parafuso_cisalhamento(V,n,n_p_c):
    N= n_p_c*n #Número total de parafusos na seção
    return V/N

def curva_interacao(M,V,T,B,posição,parafuso,rosca,planos_de_corte,n,n_p_c,diametros,gamma):  #Item 6.3.3.4 da NBR 8800:2024
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    i=0
    k=0
    solução = pd.DataFrame(columns=['k', 'diametro', 'y_ln'])
    while i<=len(diametros)-1:
        parafuso.diametro(diametros[i])  #Converte polegadas para mm
        #Resistentes do parafuso para tração e cisalhamento
        F_t_Rd=resistencia_parafuso_tração(parafuso,gamma)
        F_v_Rd=resistencia_parafuso_cisalhamento(parafuso,rosca,planos_de_corte,gamma)
        #Solicitantes no parafuso para tração e cisalhamento
        F_t_Sd=solicitante_parafuso_tração(M,B, posição, parafuso , n, k)
        F_v_Sd=solicitante_parafuso_cisalhamento(V,n,n_p_c)
        #Curva de interação
        curva=(((F_t_Sd + (T))/F_t_Rd)**2 + (F_v_Sd/F_v_Rd)**2)
        if curva > 1:
            if k<n:
                k=k+1
            else:
                k=0
                i=i+1
        else:
            y_ln = y_linha_neutra(B, posição , parafuso.diametro_mm , n, k)
            solução.loc[len(solução)] = [k,parafuso.diametro_pol,y_ln]
            break
            # Depois vou tirar essas outras soluções, porque acabam não sendo muito uteis
            #if k<n:
             #   k=k+1
            #else:
             #   k=0
              #  i=i+1
    return solução 

### Cálculo da espessura da chapa de cabeça

def parametro_b(diametro):
    """
    Retorna o valor de b conforme a tabela de referência.
    
    Parâmetros:
    valor (float): O valor do parâmetro b em polegadas.
    
    Retorna:
    int: O valor correspondente de b em mm.
    """
    if diametro <= 3/4:
        return 30
    elif diametro == 7/8:
        return 35
    else:
        return 40

def larg_trib(B, posição, diametro,b):

    # Encontrar o maior valor de y
    max_y = posição["y (mm)"].max()

    # Filtrar os parafusos que estão na camada com maior y
    parafusos_maior_y = posição[posição["y (mm)"] == max_y]

    # Calcular a diferença entre os valores máximos e mínimos de x nessa camada

    #Distância entre parafusos internos da camada
    eint = parafusos_maior_y["x (mm)"].max() - parafusos_maior_y["x (mm)"].min()
    #Distância entre parafusos externos da camada
    eext =  (B - eint)*0.5

    a=b #Facilidade construtiva

    pint=min(eint,3.5*b)

    pext = min(0.5*eint,1.75*b) + min(eext,1.75*b)

    #Se escolher o p maximo, o delta aumenta e o alfa diminui 

    return max(pext,pint)

def exp_placa(Aço, Secão, espessuras, rigida, posição, diametro, F_r_total,F_t_Sd,gamma_a1):

    a = Secão.a
    b = a

    B = Secão.B

    p = larg_trib(B, posição, diametro,b)

    delta = 1- ((diametro +  1.5)/p)      #1.5 mm é a folga minima exigida para os furo-padrão segundo a tabela 14 do item 6.3.6.1 da NBR 8800:2024 

    beta = ((a + 0.5*diametro)/(b - 0.5*diametro))*((F_r_total)/(F_t_Sd) - 1)

    if beta >=1:
        alfa=1
    else:
        alfa = min(1,((beta)/delta*(1-beta)))

    if rigida == 1:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma_a1/(Aço.f_u*p))

    else:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma_a1/(Aço.f_u*p*(1+delta*alfa)))

    maiores = [e for e in espessuras if e > t]  # Filtra apenas valores maiores que a espessura calculada

    return min(maiores) if maiores else None  # Retorna o menor dos maiores ou None se não houver

### Cálculo de espessura mínima de solda necessária

def esp_solda(aço,solda,comprimento_solda, M,V,T,filete_duplo,gamma_1,gamma_2):
    if filete_duplo == True:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    esp=10**(-5)
    #Solicitante vertical da solda:
    solicitante_vertical=V/(comprimento_solda*qtd)  # kN/mm
    #Solicitante horizontal da solda: (Do momento)
    I = qtd*(esp*comprimento_solda**3)/12 #mm^4
    sigma_h = M*comprimento_solda*0.5/I   #kN/mm^2
    solicitante_horizontal_m = sigma_h*esp # kN/mm
    #Solicitante horizontal da solda (Da tração)
    solicitante_horizontal_t = T/(qtd*comprimento_solda)  #kN/mm

    solicitante_total = np.sqrt( solicitante_vertical**2 + (solicitante_horizontal_m + solicitante_horizontal_t)**2 )  #kN/mm

    esp1=resistencia_solda_filete_cisalhamento_solda(solda,comprimento_solda, solicitante_total*comprimento_solda,filete_duplo,gamma_2)
    esp2=resistencia_solda_filete_tracao_base(aço,comprimento_solda, solicitante_total*comprimento_solda,filete_duplo,gamma_1)
    esp3=resistencia_solda_filete_cisalhamento_base(aço,comprimento_solda, solicitante_vertical*comprimento_solda,filete_duplo,gamma_1)
    esp = max(esp1,esp2,esp3)
    return esp