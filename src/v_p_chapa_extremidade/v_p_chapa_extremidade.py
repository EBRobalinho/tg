import pandas as pd
import numpy as np
from design_functions import *
from v_p_chapa_cabeca.v_p_chapa_cabeca import parametro_b,espessura_solda,exp_placa


##### Da Disposição

##Classe relativa as dimensões das chapas de cabeça (conforme catálogo da Gerdau)
class Chapa:
    def __init__(self, B, h, a):
        """Inicializa a classe com os valores B, h e a."""
        self.B = B #Largura da chapa em mm
        self.h = h #Altura da viga que vai na chapa
        self.a = a #distância do CENTRO dO parafuso superior até borda da chapa:  ITEM 6.3.5.2 NBR 8800:2024
        self.df = self.vertices_chapa()
    
    def vertices_chapa(self):
        """Cria o DataFrame com os vértices e coordenadas."""
        data = {
            "vértice": [1, 2, 3, 4,5],
            "x (mm)": [0, self.B, self.B, 0,0],
            "y (mm)": [0, 0, self.h ,self.h,0]
        }
        return pd.DataFrame(data)
    

def disposicao_parafusos(t_f, b, c ,e2, e1, h_gerdau):
    x_positions = [e2, e2 + e1]

    parafusos_x = []
    parafusos_y = []

    z = b

    while (z+b < h_gerdau):
        # Para cada camada, adiciona dois parafusos (um em cada posição de x)
        parafusos_x.extend(x_positions)
        parafusos_y.extend([z, z])
        z += c

    data = {
        "parafuso": list(range(1, len(parafusos_x) + 1)),
        "x (mm)": parafusos_x,
        "y (mm)": parafusos_y
    }


    return pd.DataFrame(data)

#Obtém os valorea arbitrados das disposições contrutivas, conforme catálogo da Gerdau
def arranjo_chapa_parafusos(perfil,parafuso):
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    h_gerdau = perfil.h - 2*perfil.t_f   #Altura total do perfil Gerdau

    b = dist_min_borda_pol(parafuso.diametro_pol) #Distância vertical do parafuso mais em cima até a borda da placa 

    e1 = max(120,3*parafuso.diametro_mm)  #Distância horizontal entre parafusos (na minha linha, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    c  = max(75,3*parafuso.diametro_mm)  #Distância vertical entre parafusos (na minha coluna, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    e2 = max(40,dist_min_borda_pol(parafuso.diametro_pol)) #Distância horizontal entre parafuso-borda (na minha linha, segundo o manual da Gerdau) e item 6.3.11.1 da NBR 8800:2024

    disposicao = disposicao_parafusos(perfil.t_f, b,c, e2, e1, h_gerdau)

    N_parafusos = (disposicao.shape[0])/2

    B_gerdau = 200 #mm     Segundo Item 4.1.1 do manual da Gerdau

    B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

    B = max(B_norma,B_gerdau) 



    h_parafusos = max(disposicao["y (mm)"]) + e2

    h = h_gerdau

    chapa = Chapa(B,h,b)

    return [chapa,disposicao,N_parafusos]

def resistencia_cisalhamento(corte,material,comprimento,N_parafusos,espessura,diametro,gamma):   #Item 6.5.5 da NBR 8800:2024
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]

    resistencia1 = corte*0.6*material.f_y*comprimento*espessura/gamma_a1    #Escoamento da seção bruta
    resistencia2 = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2   #Ruptura da seção líquida

    resistencia=min(resistencia1,resistencia2)
    return resistencia/1000 #Sair o resultado em kN


def dim_chapa_parafuso(V,T,perfil,parafuso,diametros,material,espessuras,rigida,solda,filete_duplo,gamma):  #Item 6.3.3.4 da NBR 8800:2024
    gamma_a2=gamma[0]
    #Sobre a posição do corte na rosca e a quantidade de planos de corte no parafuso
    rosca=parafuso.rosca
    planos_de_corte=parafuso.planos_de_corte
    #Tem de variar no espaço de busca os diâmetros e o parâmetro k
    i=0
    solução = pd.DataFrame(columns=['Chapa','Parafuso','Disposição Parafusos',"Solda"])

    while i<=len(diametros)-1:

        parafuso.diametro(diametros[i])  

        #Arranjo da chapa e dos parafusos 
        [chapa,ver_parafuso,N_parafusos] = arranjo_chapa_parafusos(perfil,parafuso)

        #Resistentes do parafuso para tração e cisalhamento
        F_t_Rd=resistencia_parafuso_tração(parafuso,gamma_a2)
        F_v_Rd=resistencia_parafuso_cisalhamento(parafuso,rosca,planos_de_corte,gamma_a2)

        #Solicitantes no parafuso para tração e cisalhamento
        esf_V_parafuso = V/N_parafusos
        esf_T_parafuso = T/N_parafusos
        esf_s_parafuso = np.sqrt(esf_V_parafuso**2 + esf_T_parafuso**2)
        #Curva de interação Item 6.3.3.4 da NBR 8800:2024
        curva=(((esf_T_parafuso)/F_t_Rd)**2 + (esf_V_parafuso/F_v_Rd)**2)
        if curva > 1:
            i = i + 1
        else:   
            F_r_total = resistencia_total(parafuso,gamma_a2)
            #Cálculo da espessura da placa
            exp = exp_placa(material, chapa, espessuras, rigida, ver_parafuso, parafuso.diametro_mm, F_r_total,esf_s_parafuso,gamma[0])
            #Teste e relação a escoamento da seção bruta e ruptura da seção líquida
            corte = 2 # Há 2 planos de corte na chapa
            N_parafusos_fileira =2 #Sempre serão só 2 parafusos em cada horizontal
            comprimento = chapa.df['x (mm)'].max()
            res_cisalhamento_chapa = resistencia_cisalhamento(corte,material,comprimento,N_parafusos_fileira,exp,parafuso.diametro_mm,gamma)
            if res_cisalhamento_chapa > esf_V_parafuso:
                break
            else:
                i = i + 1

    #Cálculo da solda:

    esp_solda = espessura_solda(0,V,T,solda,perfil,exp,filete_duplo,gamma)

    return [chapa,exp,parafuso,ver_parafuso,solda,esp_solda]



