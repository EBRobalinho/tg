from pyautocad import Autocad, APoint
from back.domain.perfil import Perfil
from back.domain.cantoneira import Cantoneira
from back.domain.chapa import Chapa
from back.domain.parafuso import Parafuso
from draw_utils import transladar_pontos, iniciar_autocad, limpar_desenho, gerar_pontos_hexagono
from norms import parametro_b
import math
import pandas as pd

# Função para criar chapa 3D com espessura

def desenhar_chapa(acad: Autocad, pontos: pd.DataFrame, exp: float) -> list:
    obj_chapa = []
    """
    Cria uma chapa em 3D considerando a espessura.

    Args:
        acad: Instância do Autocad
        pontos: DataFrame com coordenadas dos vértices (colunas x, y)
        exp: Espessura da chapa em mm
    """
    num_pontos = pontos.shape[0]

    # Criando vértices inferiores e superiores
    pontos_inferiores = [
        APoint(pontos.iat[i, 1], pontos.iat[i, 2], 0) for i in range(num_pontos)]
    pontos_superiores = [
        APoint(pontos.iat[i, 1], pontos.iat[i, 2], exp) for i in range(num_pontos)]

    # Desenhando linhas da base superior e da base inferior
    for i in range(num_pontos - 1):
        obj = acad.model.AddLine(pontos_superiores[i-1], pontos_superiores[i])
        obj_chapa.append(obj)
        obj = acad.model.AddLine(pontos_inferiores[i-1], pontos_inferiores[i])
        obj_chapa.append(obj)

    # Conectando as bases inferior e superior
    for i in range(num_pontos):
        obj = acad.model.AddLine(pontos_inferiores[i], pontos_superiores[i])
        obj_chapa.append(obj)

    return obj_chapa

def desenhar_secao_perfil(acad: Autocad, perfil: Perfil, posicao_x: float, posicao_y: float = 20, altura_z=None) -> list:
    """
    Desenha a seção transversal do perfil W com raios de concordância no topo da chapa 3D (plano XY).
    Retorna a lista dos objetos desenhados (linhas e arcos).
    """
    objetos = []

    x0 = posicao_x
    y0 = posicao_y
    z0 = altura_z if altura_z else 0
    R = perfil.R_conc

    # Pontos principais
    p1 = APoint(x0, y0, z0)
    p2 = APoint(x0 + perfil.b_f, y0, z0)
    p3 = APoint(x0 + perfil.b_f, y0 + perfil.t_f, z0)
    p4 = APoint(x0 + (perfil.b_f / 2) +
                (perfil.t_w / 2) + R, y0 + perfil.t_f, z0)
    p5 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) +
                R, y0 + perfil.t_f + R, z0)
    p6 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2),
                y0 + perfil.t_f + R, z0)
    p7 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2),
                y0 + perfil.t_f + perfil.h_w + R, z0)
    p8 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) +
                R, y0 + perfil.t_f + perfil.h_w + R, z0)
    p9 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) +
                R, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p10 = APoint(x0 + perfil.b_f, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p11 = APoint(x0 + perfil.b_f, y0 + 2*perfil.t_f + perfil.h_w + 2*R, z0)
    p12 = APoint(x0, y0 + 2*perfil.t_f + perfil.h_w + 2*R, z0)
    p13 = APoint(x0, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p14 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) -
                 R, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p15 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R,
                 y0 + perfil.t_f + perfil.h_w - R + 2*R, z0)
    p16 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2),
                 y0 + perfil.t_f + perfil.h_w - R + 2*R, z0)
    p17 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2),
                 y0 + perfil.t_f + R, z0)
    p18 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) -
                 R, y0 + perfil.t_f + R, z0)
    p19 = APoint(x0 + (perfil.b_f / 2) -
                 (perfil.t_w / 2) - R, y0 + perfil.t_f, z0)
    p20 = APoint(x0, y0 + perfil.t_f, z0)

    # Linhas retas
    linhas = [(p1, p2), (p2, p3), (p3, p4), (p6, p7), (p9, p10), (p10, p11), (p11, p12),
              (p12, p13), (p13, p14), (p16, p17), (p19, p20), (p20, p1)]

    for linha in linhas:
        obj = acad.model.AddLine(*linha)
        objetos.append(obj)

    # Arcos de concordância
    objetos.append(acad.model.AddArc(
        p5, R, math.radians(180), math.radians(270)))
    objetos.append(acad.model.AddArc(
        p8, R, math.radians(90), math.radians(180)))
    objetos.append(acad.model.AddArc(
        p15, R, math.radians(0), math.radians(90)))
    objetos.append(acad.model.AddArc(
        p18, R, math.radians(270), math.radians(360)))

    return objetos

def desenhar_s_cantoneira(acad: Autocad, cantoneira: Cantoneira, ver_chapa: pd.DataFrame):
    objetos = []
    # === Geometria da chapa ===
    df = ver_chapa
    R = cantoneira.R_conc
    n = len(df) // 2

    # Linhas da base (z = 0)
    for i in range(n - 1):
        if i != 3:
            p1 = APoint(df.at[i, "x (mm)"],
                        df.at[i, "y (mm)"], df.at[i, "z (mm)"])
            p2 = APoint(df.at[i + 1, "x (mm)"], df.at[i + 1,
                        "y (mm)"], df.at[i + 1, "z (mm)"])
            objetos.append(acad.model.AddLine(p1, p2))

    # Linhas do topo (z = comprimento)
    for i in range(n, 2 * n - 1):
        if i != 11:
            p1 = APoint(df.at[i, "x (mm)"],
                        df.at[i, "y (mm)"], df.at[i, "z (mm)"])
            p2 = APoint(df.at[i + 1, "x (mm)"], df.at[i + 1,
                        "y (mm)"], df.at[i + 1, "z (mm)"])
            objetos.append(acad.model.AddLine(p1, p2))

    # Linhas verticais ligando base ao topo
    for i in range(n):
        p1 = APoint(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
        p2 = APoint(df.at[i + n, "x (mm)"], df.at[i + n,
                    "y (mm)"], df.at[i + n, "z (mm)"])
        objetos.append(acad.model.AddLine(p1, p2))

    # Arcos de concordância verticais
    pares_concordancia = [(3, 4), (11, 12)]
    for i, j in pares_concordancia:
        p1 = APoint(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
        p2 = APoint(df.at[j, "x (mm)"], df.at[j, "y (mm)"], df.at[j, "z (mm)"])
        centro = APoint(df.at[i, "x (mm)"], df.at[j, "y (mm)"],
                        (df.at[j, "z (mm)"] + df.at[i, "z (mm)"]) / 2)
        objetos.append(acad.model.AddArc(centro, R, math.pi, 3 * math.pi / 2))

    return objetos

def desenhar_enrijecedores(acad: Autocad, origem: tuple, y_base_perfil: float, chapa: Chapa, perfil: Perfil, enj: float):
    ox, oy, oz = origem  # origem no plano XY
    y_topo_perfil = y_base_perfil + perfil.h
    y_topo_chapa = oy + chapa.h
    y_base_chapa = oy

    # Alturas verticais
    altura_sup = y_topo_chapa - y_topo_perfil
    altura_inf = y_base_perfil - y_base_chapa

    # Enrijecedor superior
    desenhar_retangulo(acad, ox + chapa.B/2, y_topo_perfil,
                       enj/2, altura_sup, oz)

    # Enrijecedor inferior
    desenhar_retangulo(acad, ox + chapa.B/2, y_base_chapa,
                       enj/2, altura_inf, oz)

def desenhar_retangulo(acad: Autocad, x0 : float, y0 : float, largura : float, altura : float, z0: float):
    p1 = APoint(x0, y0, z0)
    p2 = APoint(x0 + largura, y0, z0)
    p3 = APoint(x0 + largura, y0 + altura, z0)
    p4 = APoint(x0, y0 + altura, z0)
    p5 = APoint(x0 - largura, y0 + altura, z0)
    p6 = APoint(x0 - largura, y0, z0)

    acad.model.AddLine(p1, p2)
    acad.model.AddLine(p2, p3)
    acad.model.AddLine(p3, p4)
    acad.model.AddLine(p4, p5)
    acad.model.AddLine(p5, p6)
    acad.model.AddLine(p6, p1)

def rearranjar_parafusos(acad: Autocad, ver_parafuso: pd.DataFrame, objetos_parafusos: list,
                          parafuso: Parafuso, pontos_hexagono: list, esp_chapa_mm: int):
    # Rearranjar os parafusos para desenhar
    for i in range(ver_parafuso.shape[0]):
        x_centro = ver_parafuso.iat[i, 1]
        y_centro = ver_parafuso.iat[i, 2]

        # Adicionar circunferência no ponto
        obj = acad.model.AddCircle(
            APoint(x_centro, y_centro, esp_chapa_mm), parafuso.d / 2)
        objetos_parafusos.append(obj)
        obj = acad.model.AddCircle(
            APoint(x_centro, y_centro, 0), parafuso.d / 2)
        objetos_parafusos.append(obj)
        # Transladar hexágono para o ponto atual
        hexagono_transladado = transladar_pontos(
            pontos_hexagono, x_centro, y_centro, esp_chapa_mm)

        for j in range(len(hexagono_transladado) - 1):
            p1 = APoint(*hexagono_transladado[j])
            p2 = APoint(*hexagono_transladado[j + 1])
            obj = acad.model.AddLine(p1, p2)
            objetos_parafusos.append(obj)

def desenhar_viga_sobre_pilar(enrijecedor, dados_resultado: list):
        #Verifica se foi dimensionado com enrijecedor ou não
        if enrijecedor == 1:
            [parafuso,perfil_pilar,chapa,ver_parafuso,N_parafusos,altura_chapa,largura_chapa,esp_chapa_mm,esp_enrij_mm,esp] = dados_resultado
        else:
            [parafuso,perfil_pilar,chapa,ver_parafuso,N_parafusos,altura_chapa,largura_chapa,esp_chapa_mm,esp] = dados_resultado
            esp_enrij_mm = 0  # Define a default value when enrijecedor is not used

        acad = iniciar_autocad()

        limpar_desenho(acad)

        pontos_hexagono = gerar_pontos_hexagono(parafuso.d)

        # Chamando a função para desenhar a chapa 3D
        desenhar_chapa(acad, chapa.df, esp_chapa_mm)

        # Criação dos objetos dos parafusos
        objetos_parafusos=[]

        #Rearranjar os parafusos para desenhar  
        rearranjar_parafusos(acad, ver_parafuso,objetos_parafusos, parafuso,pontos_hexagono, esp_chapa_mm)

        #Cálculo da altura da base do perfil
        base_perfil= min(ver_parafuso['y (mm)'])+ parametro_b(parafuso.d)

        #Desenhar a seção do perfil
        desenhar_secao_perfil(acad, perfil_pilar, (chapa.B / 2) - (perfil_pilar.b_f / 2), posicao_y=base_perfil, altura_z=esp_chapa_mm)

        if enrijecedor == 1:
            desenhar_enrijecedores(acad, (0,0,esp_chapa_mm) ,base_perfil ,chapa, perfil_pilar, esp_enrij_mm)

def desenhar_parafuso_cantoneira(acad: Autocad,perfil: Perfil, cantoneira: Cantoneira, parafuso: Parafuso
                                 , ver_parafuso: pd.DataFrame, pontos_hexagono: list) -> list:

    #### Desenhar os parafusos do plano XY
    objetos_p2_cantoneira = []
    # === Parafusos e hexágonos ===
    for i in range(ver_parafuso.shape[0]):
        x_centro = ver_parafuso.iat[i, 2]
        y_centro = ver_parafuso.iat[i, 1]   #Muda a tabela considerando agora os parafusos do outro plano
        z_centro = ver_parafuso.iat[i, 3]

        # Face do hexágono em X
        obj1 = acad.model.AddCircle(APoint(z_centro, y_centro, -x_centro), parafuso.d / 2)
        obj1.Rotate3D(APoint(0, 0, 0), APoint(0, 1, 0), math.radians(-90))
        objetos_p2_cantoneira.append(obj1)

        # Face traseira em X
        obj2 = acad.model.AddCircle(APoint(z_centro, y_centro, 0), parafuso.d / 2)
        obj2.Rotate3D(APoint(0, 0, 0), APoint(0, 1, 0), math.radians(-90))
        objetos_p2_cantoneira.append(obj2)

        # Hexágono desenhado com linhas
        hexagono_transladado = transladar_pontos(pontos_hexagono, z_centro, y_centro, -y_centro)

        for j in range(len(hexagono_transladado) - 1):
            p1 = APoint(hexagono_transladado[j][0], hexagono_transladado[j][1], -cantoneira.t_mm)
            p2 = APoint(hexagono_transladado[j + 1][0], hexagono_transladado[j + 1][1], -cantoneira.t_mm)

            linha = acad.model.AddLine(p1, p2)
            linha.Rotate3D(APoint(0, 0, 0), APoint(0, 1, 0), math.radians(-90))
            objetos_p2_cantoneira.append(linha)

    return objetos_p2_cantoneira

def transladar_cantoneira(acad: Autocad,perfil: Perfil, cantoneira: Cantoneira, secao_cantoneira: list, secao_parafusos_cantoneira: list):
        #### Desenhar seção das cantoneiras

    # Vetor de translação (exemplo: mover 100 mm no eixo X)
    dx, dy, dz = 10, perfil.t_w/2, (perfil.h-cantoneira.comprimento)/2  # ajuste aqui conforme necessário

    # Aponta o vetor de deslocamento
    vetor = APoint(dx, dy, dz)

    # Aplica a translação a todos os objetos na lista
    for obj in secao_cantoneira:
        obj.Move(APoint(0,0,0),vetor) 
        obj.Mirror(APoint(1, 0, 0), APoint(0, 0, 0))
    for obj in secao_parafusos_cantoneira:
        obj.Move(APoint(0,0,0),vetor) 
        obj.Mirror(APoint(1, 0, 0), APoint(0, 0, 0))

def rotacionar_secao_perfil_cantoneira(acad: Autocad, perfil: Perfil):

    #### Desenhar seção do perfil

    objetos_secao_perfil = desenhar_secao_perfil(acad, perfil, posicao_x=-perfil.b_f/2, posicao_y=-perfil.h/2, altura_z=0)

    # Rotacionar apenas a seção do perfil:
    for obj in objetos_secao_perfil:
        obj.Rotate3D(APoint(0, 0, 0), APoint(1,0, 0), math.radians(90))
        obj.Rotate3D(APoint(0, 0, 0), APoint(0,0, 1), math.radians(90))

    # Vetor de translação (exemplo: mover 100 mm no eixo X)
    dx, dy, dz = 0,0,perfil.h/2  # ajuste aqui conforme necessário

    # Aponta o vetor de deslocamento
    vetor = APoint(dx, dy, dz)

    for obj in objetos_secao_perfil:
        obj.Move(APoint(0,0,0),vetor)

def desenhar_cantoneira_solda_parafuso(dados_resultado: list):
    [perfil_escolhido,parafuso,cantoneira_escolhida] = dados_resultado

    ver_parafuso = cantoneira_escolhida.disp_parafusos
    ver_chapa = cantoneira_escolhida.disp_vertices_chapa

    acad = iniciar_autocad()

    limpar_desenho(acad)

    pontos_hexagono = gerar_pontos_hexagono(parafuso.d)   

    objetos_s_cantoneira = desenhar_s_cantoneira(acad, cantoneira_escolhida, ver_chapa)

    #### Desenhar os parafusos do plano XY
    objetos_p2_cantoneira = desenhar_parafuso_cantoneira(acad,perfil_escolhido,cantoneira_escolhida,parafuso,ver_parafuso,pontos_hexagono)

    transladar_cantoneira(acad,perfil_escolhido,cantoneira_escolhida,objetos_s_cantoneira,objetos_p2_cantoneira)

    rotacionar_secao_perfil_cantoneira(acad, perfil_escolhido)
