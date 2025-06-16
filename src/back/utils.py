import numpy as np
import pandas as pd
from back.norms import furo_padrao_pol, parametro_b
from back.domain.cantoneira import Cantoneira
from back.domain.materials import Aço
from back.domain.chapa import Chapa, ChapaExtremidade
from back.norms import chapa_beta_roark
from back.logs import registrar_marcha



def resistencia_cisalhamento_chapa(corte,material,comprimento,N_parafusos,espessura,diametro,gamma):   #Item 6.5.5 da NBR 8800:2024
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]
    registrar_marcha("\nVerificação cisalhamento segundo Item 6.5.5 da NBR 8800:2024")
    
    resistencia1 = corte*0.6*material.f_y*comprimento*espessura/gamma_a1    #Escoamento da seção bruta
    registrar_marcha(f"Resistência do cisalhamento da chapa segundo o escoamento da seção bruta: resistencia_1 = {corte*0.6*material.f_y*comprimento*espessura/gamma_a1} N")
    
    resistencia2 = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2   #Ruptura da seção líquida
    registrar_marcha(f"Resistência do cisalhamento da chapa segundo a ruptura da seção líquida: resistencia_2 = {corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2} N")
    
    resistencia=min(resistencia1,resistencia2)
    registrar_marcha(f"Resistência do cisalhamento da chapa segundo o menor valor entre os dois: resistencia = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN


def criterio_cisalhamento_chapa(chapa,s_p_v,espessura_chapa,ver_parafuso,parafuso,material,gamma):
    #Teste e relação a escoamento da seção bruta e ruptura da seção líquida
    corte = parafuso.planos_de_corte # Há 1 plano de corte na chapa
    N_parafusos_coluna = (ver_parafuso["x (mm)"] == ver_parafuso["x (mm)"].iloc[0]).sum()
    comprimento = chapa.df['y (mm)'].max()

    res_cisalhamento_chapa = resistencia_cisalhamento_chapa(corte,material,comprimento,N_parafusos_coluna,espessura_chapa,parafuso.diametro_mm,gamma)
    if res_cisalhamento_chapa > s_p_v:
        registrar_marcha(f"Verificação: resistência ao cisalhamento {res_cisalhamento_chapa:.2f} kN > solicitante {s_p_v:.2f} kN.\nA chapa aguenta a solicitação para cisalhamento.")
        return [1,"A chapa aguenta a solicitação para cisalhamento."]
    else:
        registrar_marcha(f"Verificação: resistência ao cisalhamento {res_cisalhamento_chapa:.2f} kN <= solicitante {s_p_v:.2f} kN.\nA chapa não aguenta a solicitação desejada para cisalhamento.")
        return [0,"A chapa não aguenta a solicitação desejada para cisalhamento."]


#Resistência das peças para Esmagamento e rasgamento

def resistencia_rasgamento_esmagamento(corte: int, material: Aço, cantoneira: Cantoneira, espessura: float, distancia: float, diametro: float, gamma: float): #Item 6.3.3.3 da NBR 8800:2024
    registrar_marcha("\nCalculo relativo a resistência a rasgamento e esmagamento")
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    resistencia1 = corte*2.4*material.f_u*espessura*diametro*N_parafusos/gamma 
    registrar_marcha(f"\nResistencia 1 (Esmagamento): corte * 2.4 * material.f_u * espessura * diametro * N_parafusos / gamma = {corte} * 2.4 * {material.f_u} * {espessura} * {diametro} * {N_parafusos} / {gamma} = {resistencia1} N")  #Sair o resultado em N
    resistencia2 = 1.2*corte*material.f_u*espessura*distancia*N_parafusos/gamma  
    registrar_marcha(f"\nResistencia 2 (Rasgamento): 1.2 * corte * material.f_u * espessura * distancia * N_parafusos / gamma = 1.2 * {corte} * {material.f_u} * {espessura} * {distancia} * {N_parafusos} / {gamma} = {resistencia2} N")
    resistencia=min(resistencia1,resistencia2)

    registrar_marcha(f"Resistência minima = min({resistencia1},{resistencia2}) = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN

def resistencia_cisalhamento(corte: int, material: Aço, comprimento: float, cantoneira: Cantoneira, espessura: float, diametro: float, gamma: list) -> float:   #Item 6.5.5 da NBR 8800:2024
    gamma_a1=gamma[0]
    gamma_a2=gamma[0]

    N_parafusos =cantoneira.disp_parafusos.shape[0]
    registrar_marcha("\nCalculo relativo a resistência a cisalhamento")
    resistencia1 = corte*0.6*material.f_y*comprimento*espessura/gamma_a1    #Escoamento da seção bruta
    registrar_marcha(f"\nResistencia 1 (Escoamento da seção bruta): corte * 0.6 * material.f_y * comprimento * espessura / gamma_a1 = {corte} * 0.6 * {material.f_y} * {comprimento} * {espessura} / {gamma_a1} = {resistencia1} N")
    resistencia2 = corte*0.6*material.f_u*espessura*(comprimento-N_parafusos*(furo_padrao_pol(diametro)))/gamma_a2   #Ruptura da seção líquida
    registrar_marcha(f"\nResistencia 2 (Ruptura da seção líquida): corte * 0.6 * material.f_u * espessura * (comprimento - N_parafusos * (furo_padrao_pol(diametro))) / gamma_a2 = {corte} * 0.6 * {material.f_u} * {espessura} * ({comprimento} - {N_parafusos} * ({furo_padrao_pol(diametro)})) / {gamma_a2} = {resistencia2} N")

    resistencia=min(resistencia1,resistencia2)
    registrar_marcha(f"Resistência minima = min({resistencia1},{resistencia2}) = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN

def resistencia_block(corte: int, cantoneira: Cantoneira, espessura: float, diametro: float, gamma: float) -> float:  #Item 6.5.6 da NBR 8800:2024
    f_y = cantoneira.material.f_y
    f_u = cantoneira.material.f_u
    registrar_marcha("\nCalculo relativo a resistência a cisalhamento de bloco")
    N_parafusos =cantoneira.disp_parafusos.shape[0]
    A_gv = espessura*(cantoneira.comprimento - cantoneira.f_b)  #Area bruta da cantoneira sujeita a cisalhamento (O comprimento pode ser o espaçamento entre os parafusos ou )
    A_nv = espessura*(cantoneira.comprimento - cantoneira.f_b) - (N_parafusos-0.5)*(furo_padrao_pol(diametro))*espessura  #Area líquida da cantoneira sujeita a cisalhamento
    A_nt = (cantoneira.f_b - 0.5*(furo_padrao_pol(diametro)))*espessura
    C_ts=1  # Sé deixa de ser 1, quando a tensão na área líquida não for uniforme 
    resistencia = min(0.6*f_u*A_nv + C_ts*f_u*A_nt,0.6*f_y*A_gv + C_ts*f_u*A_nt)*corte/gamma   #Sair o resultado em N  
    registrar_marcha(f"\nResistencia ao bloco de cisalhamento: min(0.6*f_u*A_nv + C_ts*f_u*A_nt,0.6*mf_y*A_gv + C_ts*f_u*A_nt)*corte/gamma = min(0.6*{f_u}*{A_nv} + {C_ts}*{f_u}*{A_nt}, 0.6*{f_y}*{A_gv} + {C_ts}*{f_u}*{A_nt})*{corte}/{gamma} = {resistencia} N")
    return resistencia/1000 #Sair o resultado em kN

#Cálculo da espessura da chapa de cabeça:

def larg_trib(posição: pd.DataFrame,b: float) -> float:

    registrar_marcha("Cálculo da largura tributária p para o efeito alavanca: item 6.3.5.2 da NBR 8800 \n")
    # Encontrar o maior valor de y
    max_y = posição["y (mm)"].max()

    # Filtrar os parafusos que estão na camada com maior y
    parafusos_maior_y = posição[posição["y (mm)"] == max_y]

    #Distância entre parafusos internos da camada (considerando a distância entre os dois primeiros parafusos)
    eint = abs(parafusos_maior_y["x (mm)"].iat[0] - parafusos_maior_y["x (mm)"].iat[1])
    registrar_marcha(f"Distância entre parafusos internos da camada = {eint} mm \n")

    #Distância entre parafusos externos da camada (Ou seja a distância de qualquer parafuso externo para sua borda na horizontal)
    eext =  parafusos_maior_y["x (mm)"].iat[0]
    registrar_marcha(f"Distância entre parafusos externos da camada = {eext} mm \n")

    pint = min(eint,3.5*b)
    registrar_marcha(f"p interno é o valor mínimo entre a distância entre parafusos internos da camada pint={min(eint,3.5*b)} mm \n")

    pext = min(0.5*eint,1.75*b) + min(eext,1.75*b)
    registrar_marcha(f"p externo é o valor mínimo entre a distância entre parafusos externos da camada pext={min(0.5*eint,1.75*b) + min(eext,1.75*b)} mm \n")

    #Se escolher o p minimo, aumenta o denominador, aumentando a espessura, segundo item 6.3.5.4 da NBR 8800;2024
    registrar_marcha(f"p é o menor entre pext e pint, ou seja, p={min(pext,pint)} mm \n")
    return min(pext,pint)


def exp_placa(Aço: Aço, Secão: Chapa, rigida: int, posição: pd.DataFrame, diametro: float, F_r_total: float, F_t_Sd: float, gamma: list) -> float | str | None:
    registrar_marcha(f"Cálculo da espessura mínima da chapa de cabeça, considerando o efeito alavanca a depender se a chapa é rígida={rigida}=1\n")
    a =Secão.a
    b = parametro_b(diametro) #Distância da face mais próxima da mesa até a linha de furação 

    #B = Secão.B

    p = larg_trib(posição,b)

    delta = 1- ((furo_padrao_pol(diametro))/p)      #Considerando a dimensão do furo na largura tributária como se fosse o furo padrão
    registrar_marcha(f"delta = 1 - (furo_padrao_pol(diametro)/p) = 1 - ({furo_padrao_pol(diametro)}/{p}) = {delta}")

    beta = ((a + 0.5*diametro)/(b - 0.5*diametro))*((F_r_total)/(F_t_Sd) - 1)
    registrar_marcha(f"beta = ((a + 0.5*diametro)/(b - 0.5*diametro)) * ((F_r_total/F_t_Sd) - 1) = (({a} + 0.5*{diametro})/({b} - 0.5*{diametro})) * (({F_r_total}/{F_t_Sd}) - 1) = {beta}")

    if beta >= 1:
        alfa = 1
        registrar_marcha(f"alfa = {alfa} (pois beta >= 1)")
    elif beta > 0 and beta < 1:
        alfa = min(1, (beta) / (delta * (1 - beta)))
        registrar_marcha(f"alfa = min(1, (beta)/(delta*(1-beta))) = min(1, ({beta})/({delta}*{1-beta})) = {alfa}")
    else:
        # Se beta <= 0, alfa é zero
        #Fisicamente o que isso significa é que b é menor do que meio diâmetro, não respeita as distâncias mínimas entre borda e furo
        alfa = 0
        registrar_marcha(f"alfa = {alfa} (pois beta <= 0)")
        registrar_marcha(f"A solicitação é maior do que a geometria da ligação aguenta, pois {diametro}>2*{b}.")
        return "A ligação não aguenta a solicitação desejada." 

    if rigida == 1:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p))*np.sqrt(1000)
        registrar_marcha(f"t = sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p)) * sqrt(1000) = sqrt(4*({b}-0.5*{diametro})*{F_t_Sd}*{gamma[0]}/({Aço.f_u}*{p})) * sqrt(1000) = {t} mm ")
    else:
        t = np.sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p*(1+delta*alfa)))*np.sqrt(1000)
        registrar_marcha(f"t = sqrt(4*(b-0.5*diametro)*F_t_Sd*gamma[0]/(Aço.f_u*p*(1+delta*alfa))) * sqrt(1000) = sqrt(4*({b}-0.5*{diametro})*{F_t_Sd}*{gamma[0]}/({Aço.f_u}*{p}*(1+{delta}*{alfa}))) * sqrt(1000) = {t} mm")

    maiores = [e for e in Secão.espessuras_disponiveis if e > t]  # Filtra apenas valores maiores que a espessura calculada

    if not maiores :
        return "A ligação não aguenta a solicitação desejada." 
    
    return min(maiores) if maiores else None  # Retorna o menor dos maiores ou None se não houver


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

