import pandas as pd
from back.bolt_design import (solicitante_parafuso_tração, resistencia_parafuso_tração,resistencia_parafuso_cisalhamento,resistencia_total,
solicitante_parafuso_cisalhamento,solicitante_total)             
from back.utils import exp_placa
from back.weld_design import espessura_solda
from back.logs import registrar_marcha, registrar_marcha2, registrar_tabela
from back.norms import dist_min_borda_pol
from back.domain.chapa import ChapaExtremidade
from back.domain.perfil import Perfil
from back.domain.parafuso import Parafuso
from back.domain.materials import Aço
from back.domain.solda import Solda


##### Da Disposição    

def disposicao_parafusos(t_f: float, b: float, c: float, e2: float, e1: float, h_gerdau: float) -> pd.DataFrame:
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
def arranjo_chapa_parafusos(perfil: Perfil, parafuso: Parafuso) -> tuple[ChapaExtremidade, pd.DataFrame,int]:
    # Mapeamento dos nomes dos perfis para os valores das distâncias dos arranjos nas chapas

    h_gerdau = perfil.h - 2*perfil.t_f   #Altura total do perfil Gerdau

    b = dist_min_borda_pol(parafuso.d_pol) #Distância vertical do parafuso mais em cima até a borda da placa 

    e1 = max(120,3*parafuso.d)  #Distância horizontal entre parafusos (na minha linha, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    c  = max(75,3*parafuso.d)  #Distância vertical entre parafusos (na minha coluna, segundo o manual da Gerdau), o critério vem do item 6.3.9 da NBR 8800:2024

    e2 = max(40,dist_min_borda_pol(parafuso.d_pol)) #Distância horizontal entre parafuso-borda (na minha linha, segundo o manual da Gerdau) e item 6.3.11.1 da NBR 8800:2024

    disposicao = disposicao_parafusos(perfil.t_f, b,c, e2, e1, h_gerdau)

    N_parafusos = int((disposicao.shape[0])/2)

    B_gerdau = 200 #mm     Segundo Item 4.1.1 do manual da Gerdau

    B_norma = max(disposicao["x (mm)"]) + e2 # Posição dos parafusos + a distância minima entre borda e furo da NBR

    B = max(B_norma,B_gerdau) 

    #h_parafusos = max(disposicao["y (mm)"]) + e2

    h = h_gerdau      

    chapa = ChapaExtremidade(B,h,b)

    return (chapa,disposicao,N_parafusos)


def dim_chapa_parafuso(V: float, T: float, perfil: Perfil, parafuso: Parafuso, material: Aço, rigida: int, solda: Solda, filete_duplo: int, gamma: list) -> list[str] | tuple[ChapaExtremidade, float, Parafuso, pd.DataFrame, Solda, float] | None:  #Item 6.3.3.4 da NBR 8800:2024
    #Tem de variar no espaço de busca os diâmetros
    registrar_marcha("Dimensionamento da ligação que faz conexão da viga via chapa de extremidade com pilar \n")

    for d in parafuso.diametro_mm:
        registrar_marcha2(f"Cálculo com parafuso de diâmetro {d} pol")
        #Atualiza o diâmetro de busca
        parafuso.d = d  

        #Arranjo da chapa e dos parafusos
        [chapa, ver_parafuso, N_parafusos] = arranjo_chapa_parafusos(perfil, parafuso)

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
                    esp_solda = espessura_solda(0,V,T,solda,perfil,exp,filete_duplo,gamma)
                    return (chapa,exp,parafuso,ver_parafuso,solda,esp_solda)
            break





