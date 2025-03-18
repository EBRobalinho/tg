import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from main import *
from v_p_chapa_cabeca import *
from materiais import *

perfil_escolhido = W_610x125_0

chapa = chapa_para_perfil(perfil_escolhido)

disp_parafuso = disposicao_parafusos(perfil_escolhido)
ver_parafuso = disp_parafuso.df

M = 81000 #kN.mm 

V = 156 #kN

T = 0 #kN

B = chapa.B

parafuso = ASTM_A325

diametros = diametros_A325

rosca = 1

planos_de_corte =1

N = len(ver_parafuso)  #Número total de parafusos

n = (ver_parafuso["x (mm)"] == ver_parafuso["x (mm)"].iloc[0]).sum()  #número de parafusos por coluna

n_p_c = N/n  #número de parafusos por camada

S = curva_interacao(M,V,T,B,np.unique(ver_parafuso["y (mm)"]),parafuso,rosca,planos_de_corte,n,n_p_c,diametros,gamma_a2)

print(S)

from PIL import Image, ImageDraw
import pandas as pd

def criar_imagem_para_cada_diametro(chapa_df, disp_parafuso_df, S_df, nome_base="chapa_parafusos_diametro"):
    """
    Cria uma imagem da chapa com todos os parafusos tendo o mesmo diâmetro
    para cada diâmetro único encontrado no DataFrame S, incluindo a linha neutra.

    Args:
        chapa_df (pd.DataFrame): DataFrame com os vértices da chapa,
                                  colunas "y (mm)" e "x (mm)".
        disp_parafuso_df (pd.DataFrame): DataFrame com as coordenadas dos parafusos,
                                         colunas "y (mm)" e "x (mm)".
        S_df (pd.DataFrame): DataFrame com as informações de diâmetro (em polegadas)
                             na coluna 'diametro' e altura da linha neutra na coluna 'y_ln'.
        nome_base (str, opcional): Base do nome do arquivo para salvar as imagens.
                                   O diâmetro será adicionado ao nome.
                                   Padrão é "chapa_parafusos_diametro".
    """

    if chapa_df.empty or disp_parafuso_df.empty or S_df.empty:
        print("Um ou mais DataFrames estão vazios.")
        return

    # 1. Extrair vértices da chapa
    chapa_pontos = [(row["x (mm)"], row["y (mm)"]) for index, row in chapa_df.iterrows()]
    if not chapa_pontos:
        print("DataFrame da chapa não contém vértices.")
        return

    # 2. Extrair coordenadas dos parafusos
    parafusos_coords = [(row["x (mm)"], row["y (mm)"]) for index, row in disp_parafuso_df.iterrows()]
    i=0
    # 3. Iterar sobre cada diâmetro único em S
    for index, row in S_df.iterrows():
        diametro_pol_str = str(row['diametro'])
        diametro_mm = pol_to_mm(diametro_pol_str)
        y_ln = row['y_ln']

        if diametro_mm is None:
            print(f"Erro ao converter diâmetro '{diametro_pol_str}' para mm.")
            continue

        # 4. Definir escala e offset para a imagem
        escala = 5  # Ajuste conforme necessário para o tamanho da imagem
        offset_x = 50
        offset_y = 50

        # 5. Calcular limites para dimensionar a imagem
        all_x = [p[0] for p in chapa_pontos] + [p[0] for p in parafusos_coords]
        all_y = [p[1] for p in chapa_pontos] + [p[1] for p in parafusos_coords]

        if not all_x or not all_y:
            print("Não há coordenadas suficientes para calcular os limites da imagem.")
            continue

        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y)
        max_y = max(all_y)

        largura = int((max_x - min_x) * escala + 2 * offset_x)
        altura = int((max_y - min_y) * escala + 2 * offset_y)

        if largura <= 0 or altura <= 0:
            print("Dimensões da imagem inválidas.")
            continue

        # 6. Criar imagem
        img = Image.new('RGB', (largura, altura), 'white')
        draw = ImageDraw.Draw(img)

        # 7. Desenhar a chapa
        pontos_desenho_chapa = [(int((x - min_x) * escala + offset_x), int((max_y - y) * escala + offset_y)) for x, y in chapa_pontos]
        draw.polygon(pontos_desenho_chapa, outline='black', width=2)

        # 8. Desenhar todos os parafusos com o mesmo diâmetro
        raio = diametro_mm / 2 * escala
        for px, py in parafusos_coords:
            x_desenho = int((px - min_x) * escala + offset_x)
            y_desenho = int((max_y - py) * escala + offset_y)
            bbox = (x_desenho - raio, y_desenho - raio, x_desenho + raio, y_desenho + raio)
            draw.ellipse(bbox, outline='blue', width=2)
            # Adicionar diâmetro como texto (opcional)
            texto_x = x_desenho
            texto_y = y_desenho + raio + 5
            draw.text((texto_x, texto_y), f"{diametro_mm:.1f} mm", fill='black')

        # 9. Desenhar a linha neutra
        y_ln_desenho = int((max_y - y_ln) * escala + offset_y)
        draw.line([(0, y_ln_desenho), (largura, y_ln_desenho)], fill='red', width=2)

        # 10. Salvar a imagem com um nome que inclui o diâmetro
        nome_arquivo = f"{nome_base}_{i}.png"
        i = i+1
        try:
            img.save(nome_arquivo)
            print(f"Imagem salva como '{nome_arquivo}' (diâmetro: {diametro_pol_str} polegadas, linha neutra em y={y_ln})")
        except Exception as e:
            print(f"Erro ao salvar a imagem '{nome_arquivo}': {e}")

# Exemplo de uso (você precisará ter seus DataFrames 'chapa.df', 'disp_parafuso.df' e 'S'):
# Supondo que você já tenha esses DataFrames carregados:
# criar_imagem_para_cada_diametro(chapa.df, disp_parafuso.df, S)

criar_imagem_para_cada_diametro(chapa.df, disp_parafuso.df, S)