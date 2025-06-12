import numpy as np
import re
from fractions import Fraction
from back.domain.cantoneira import Cantoneira

# Salva um registro de marcha de cálculo como variável global

MARCHA_LOG = []

def registrar_marcha(msg: str):
    if isinstance(msg, (int, float)):
        texto = f"{msg:.2f}"
    elif isinstance(msg, str):
        # Substitui todos os números float nas strings por versões com 2 casas decimais
        texto = re.sub(
            r"(?<!\\w)(-?\d+\.\d+)",  # pega números negativos e decimais
            lambda m: f"{float(m.group()):.2f}",
            msg
        )
    else:
        texto = str(msg)

    MARCHA_LOG.append(texto + "\n")

def registrar_marcha2(msg):
    MARCHA_LOG.append(msg + "\n")    

def registrar_tabela(titulo, df):
    if df.empty:
        MARCHA_LOG.append(f"{titulo}: tabela vazia.\n")
        return

    MARCHA_LOG.append(f"\n{titulo}:\n")

    # Cabeçalho com coluna de índice
    colunas = ["#"] + df.columns.tolist()
    largura_colunas = 12  # espaço reservado para cada coluna
    linha_cabecalho = " | ".join(f"{col:<{largura_colunas}}" for col in colunas)
    MARCHA_LOG.append(linha_cabecalho + "\n")
    MARCHA_LOG.append("-" * len(linha_cabecalho) + "\n")

    # Linhas
    for idx, (_, linha) in enumerate(df.iterrows(), start=1):
        valores = [idx] + list(linha)
        linha_formatada = " | ".join(
            f"{valor:.2f}".rjust(largura_colunas) if isinstance(valor, (float, int)) else str(valor).ljust(largura_colunas)
            for valor in valores
        )
        MARCHA_LOG.append(linha_formatada + "\n")

def limpar_marcha():
    MARCHA_LOG.clear()
    # Limpa o log de marcha

#Conversão de Unidades

#Fazer uma função para converter a lista de pol para mm de chapa

def pol_to_mm(pol: int | str) -> float:
    if isinstance(pol, (int, float)):  # Se já for número, converte direto
        return pol * 25.4
    elif isinstance(pol, str):
        if '.' in pol:  # Se for formato misto (ex: "1.1/8")
            partes = re.split(r'\.', pol)  # Divide parte inteira e fração
            parte_inteira = int(partes[0])  # Parte inteira
            fracao = float(Fraction(partes[1]))  # Converte fração com Fraction
            return (parte_inteira + fracao) * 25.4  # Converte para mm
        else:  # Se for apenas uma fração (ex: "5/8")
            return float(Fraction(pol)) * 25.4  # Converte para mm

def mm_para_polegada(valor_mm):
    """
    Converte valor em milímetros para string em polegadas com notação fracionária.
    Ex: 28.575 mm → '1.1/8'
    """
    polegadas = valor_mm / 25.4
    parte_inteira = int(polegadas)
    fracao = Fraction(polegadas - parte_inteira).limit_denominator(64)

    if fracao.numerator == 0:
        return f"{parte_inteira}"
    elif parte_inteira == 0:
        return f"{fracao.numerator}/{fracao.denominator}"
    else:
        return f"{parte_inteira}.{fracao.numerator}/{fracao.denominator}"

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

def dist_min_borda_pol(diametro_pol):
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

# Funções de cálculo do solicitante nos ligantes:

def solicitante_parafuso_tração(T,N_parafusos):  #N_parafusos é o número de parafusos que estão sendo solicitados devido aquela solicitação T na ligação
    return T/N_parafusos

def solicitante_parafuso_cisalhamento(V,N_parafusos):  #N_parafusos é o número de parafusos que estão sendo solicitados devido aquela solicitação V na ligação
    return V/N_parafusos  

def solicitante_total(T,V,N_parafusos):
    s_p_t = solicitante_parafuso_tração(T,N_parafusos)
    s_p_v = solicitante_parafuso_cisalhamento(V,N_parafusos)
    return np.sqrt(s_p_t**2 + s_p_v**2)

# Funções do cálculo de resistência dos ligantes (Parafusos)

def resistencia_parafuso_tração(parafuso,gamma):
    gamma_a2=gamma[0]
    #Cálculo da area bruta do parafuso
    F_t_Rd = 0.75 * parafuso.f_u * parafuso.A_g / gamma_a2 #item 6.3.3.1 da NBR 8800:2024
    registrar_marcha(f"Cálculo da resistência do parafuso considerando a área bruta é F_t_Rd ={0.75 * parafuso.f_u * parafuso.A_g / gamma_a2} N")
    return F_t_Rd/1000  #Para sair em kN

def resistencia_parafuso_cisalhamento(parafuso,gamma):
    gamma_a2=gamma[0]
    rosca=parafuso.rosca
    planos_de_corte=parafuso.planos_de_corte
    #Cálculo da area bruta do parafuso
    if rosca :
        F_v_Rd = 0.45 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2 #item 6.3.3.2 da NBR 8800:2024
        registrar_marcha(f"Cálculo da resistência do parafuso considerando o plano de corte na rosca é F_v_Rd ={0.45 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2} N")
    else:
        F_v_Rd = 0.56 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2
        registrar_marcha(f"Cálculo da resistência do parafuso considerando o plano de corte na rosca é F_v_Rd ={0.56 *planos_de_corte* parafuso.f_u * parafuso.A_g / gamma_a2} N")
    return F_v_Rd/1000 #Para sair em kN

def resistencia_total(parafuso,gamma):
    r_p_t = resistencia_parafuso_tração(parafuso,gamma)
    r_p_c = resistencia_parafuso_cisalhamento(parafuso,gamma)
    return np.sqrt(r_p_t**2 + r_p_c**2)

#Soldas

def momento_inercia_soldas_perfil(perfil,filete_duplo):
    meia_altura=perfil.h/2 #mm
    largura_mesa=perfil.b_f

    if filete_duplo:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1

    Ix1 = qtd*(largura_mesa*0.7*(meia_altura**2)) 
    Ix2 = qtd*((largura_mesa-perfil.t_w)*0.7*(meia_altura-perfil.t_f)**2) 
    Ix3 = qtd*(0.7*(perfil.h - 2*perfil.t_f)**3)/12

    return Ix1 + Ix2 + Ix3 #mm^3*(Para 1mm de espessura)

def tensao_cisalhante_momento_filete(perfil,M,altura,filete_duplo):
    #A ideia é calcular a tensão de cisalhmento máxima advinda do momento que nem é feito no Livro do Pfeil:
    momento_inercia = momento_inercia_soldas_perfil(perfil,filete_duplo)
    return M*(altura*0.5)/momento_inercia         #kN/mm*(Para 1mm de espessura)

def tensao_cisalhante_cortante_filete(perfil,V,filete_duplo):
    if filete_duplo:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1
    #A ideia é calcular a tensão de cisalhmento máxima advinda do cortante que nem é feito no Livro do Pfeil (considera-se então que toda a cisalhante do cortante é resistida pela alma)
    return V/qtd/0.7/perfil.h_w       #kN/(mm*(Para 1mm de espessura))

def tensao_cisalhante_normal_filete(perfil,N,filete_duplo):
    if filete_duplo:  # Ou seja tem solda dos dois lados da chapa, fazendo a mesa ligação
        qtd=2
    else:
        qtd=1

    comprimento=qtd*(2*perfil.b_f + perfil.h - 2*perfil.t_f - perfil.t_w)

    return N/comprimento/0.7        #kN/(mm*(Para 1mm de espessura))    

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
    

def tensao_cisalhante_filete_cantoneira(cantoneira: Cantoneira, V: float) -> float:
    #Quem resistente ao esforço cortante na solda é a componente vertical + 2*horizontal da solda (o valor é vezes 2 pq há dois braços de cantoneira soldados)
    comprimento = cantoneira.comprimento + 2 * cantoneira.b_mm

    return V / comprimento  # kN/mm

def momento_polar_inercia(cantoneira: Cantoneira) -> float:
    registrar_marcha("Calculo do momento polar de inércia para uma solda filete de 1 mm")
    I_p = ( (8*((cantoneira.b_mm)**3)) + 6*(cantoneira.b_mm)*(cantoneira.comprimento) + (cantoneira.comprimento)**3 )/12  - ((cantoneira.b_mm**4)/(2*cantoneira.b_mm + cantoneira.comprimento)) #mm^3
    registrar_marcha(f"I_p = ( (8*({cantoneira.b_mm}**3)) + 6*{cantoneira.b_mm}*{cantoneira.comprimento} + {cantoneira.comprimento}**3 )/12  - (({cantoneira.b_mm}**4)/(2*{cantoneira.b_mm} + {cantoneira.comprimento})) = {I_p} mm^3")  
    return I_p #mm^4/mm

def centroide_solda(cantoneira: Cantoneira) -> float:
    registrar_marcha("Cálculo da excentricidade e borda da cantoneira que fica na viga") 
    e = (cantoneira.b_mm**2)/(2*cantoneira.b_mm + cantoneira.comprimento) #mm
    registrar_marcha(f"e = {e} = ({cantoneira.b_mm}**2)/(2*{cantoneira.b_mm} + {cantoneira.comprimento}) mm")
    return e


def torcao_momento(V: float, e: float) -> float:
    registrar_marcha("Cálculo do momento advindo da excentricidade da cortante na ligação") 
    M = V*e    #kN*mm
    registrar_marcha(f"Momento {M} = {V}*{e} kN")
    return M


def tensao_momento(V: float, cantoneira: Cantoneira) -> float:
    registrar_marcha("Cálculo da tensão advinda do momento de torção sobre a qual a solda da cantoneira está submetida") 
    I_p = momento_polar_inercia(cantoneira) #mm^3

    e = centroide_solda(cantoneira)

    M = torcao_momento(V,e) #kN*mm

    braco = np.sqrt((cantoneira.comprimento*0.5)**2 + (cantoneira.b_mm - e)**2) #mm

    tensao = M*braco/I_p  #kN/mm  = Mpa*m
    registrar_marcha(f"Tensão advinda do momento de torção {tensao} = {M}*np.sqrt(({cantoneira.comprimento}*0.5)**2 + ({cantoneira.b_mm - e})**2)/({I_p}) kN")
    return tensao
