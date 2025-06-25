import ezdxf
from ezdxf.math import Vec3
from back.domain.perfil import Perfil
from back.domain.cantoneira import Cantoneira
from back.domain.chapa import Chapa
from back.domain.parafuso import Parafuso
from back.norms import parametro_b
import math
import pandas as pd
import tempfile
import os

def criar_documento_dxf():
    """Cria um novo documento DXF e retorna o documento e o modelspace"""
    doc = ezdxf.new("AC1032")  # Versão compatível com a maioria dos CADs
    msp = doc.modelspace()
    return doc, msp

def salvar_e_abrir_dxf(doc, nome_arquivo="ligacao_estrutural.dxf"):
    """Salva o arquivo DXF em um local temporário e abre"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf", prefix=nome_arquivo.replace(".dxf", "_")) as tmp:
        caminho = tmp.name
    
    doc.saveas(caminho)
    os.startfile(caminho)  # Abre com o programa padrão para DXF
    return caminho

def salvar_dxf_com_dialogo(doc, nome_arquivo="ligacao_estrutural.dxf"):
    """Salva o arquivo DXF usando diálogo 'Salvar Como'"""
    from PySide6.QtWidgets import QFileDialog, QApplication
    
    # Garantir que existe uma instância QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Abrir diálogo "Salvar Como"
    caminho, _ = QFileDialog.getSaveFileName(
        None,
        "Salvar Desenho DXF",
        nome_arquivo,
        "Arquivos DXF (*.dxf);;Todos os arquivos (*.*)"
    )
    
    if caminho:  # Se o usuário não cancelou
        # Garantir que tem extensão .dxf
        if not caminho.lower().endswith('.dxf'):
            caminho += '.dxf'
        
        doc.saveas(caminho)
        return caminho
    else:
        return None  # Usuário cancelou

def salvar_dxf_direto(doc, caminho_arquivo):
    """Salva o arquivo DXF diretamente no caminho especificado"""
    doc.saveas(caminho_arquivo)
    return caminho_arquivo

def desenhar_chapa(msp, pontos: pd.DataFrame, exp: float) -> list:
    """
    Cria uma chapa em 3D considerando a espessura usando ezdxf.

    Args:
        msp: Modelspace do ezdxf
        pontos: DataFrame com coordenadas dos vértices (colunas x, y)
        exp: Espessura da chapa em mm
    """
    entidades = []
    num_pontos = pontos.shape[0]

    # Criando vértices inferiores e superiores
    pontos_inferiores = [
        Vec3(pontos.iat[i, 1], pontos.iat[i, 2], 0) for i in range(num_pontos)
    ]
    pontos_superiores = [
        Vec3(pontos.iat[i, 1], pontos.iat[i, 2], exp) for i in range(num_pontos)
    ]

    # Desenhando linhas da base superior e da base inferior
    for i in range(num_pontos):
        # Base superior
        line = msp.add_line(pontos_superiores[i-1], pontos_superiores[i])
        entidades.append(line)
        # Base inferior
        line = msp.add_line(pontos_inferiores[i-1], pontos_inferiores[i])
        entidades.append(line)

    # Conectando as bases inferior e superior
    for i in range(num_pontos):
        line = msp.add_line(pontos_inferiores[i], pontos_superiores[i])
        entidades.append(line)

    return entidades

def desenhar_secao_perfil(msp, perfil: Perfil, posicao_x: float, posicao_y: float = 20, altura_z=None) -> list:
    """
    Desenha a seção transversal do perfil W com raios de concordância usando ezdxf.
    """
    entidades = []

    x0 = posicao_x
    y0 = posicao_y
    z0 = altura_z if altura_z else 0
    R = perfil.R_conc

    # Pontos principais
    p1 = Vec3(x0, y0, z0)
    p2 = Vec3(x0 + perfil.b_f, y0, z0)
    p3 = Vec3(x0 + perfil.b_f, y0 + perfil.t_f, z0)
    p4 = Vec3(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f, z0)
    p5 = Vec3(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f + R, z0)
    p6 = Vec3(x0 + (perfil.b_f / 2) + (perfil.t_w / 2), y0 + perfil.t_f + R, z0)
    p7 = Vec3(x0 + (perfil.b_f / 2) + (perfil.t_w / 2), y0 + perfil.t_f + perfil.h_w + R, z0)
    p8 = Vec3(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f + perfil.h_w + R, z0)
    p9 = Vec3(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p10 = Vec3(x0 + perfil.b_f, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p11 = Vec3(x0 + perfil.b_f, y0 + 2*perfil.t_f + perfil.h_w + 2*R, z0)
    p12 = Vec3(x0, y0 + 2*perfil.t_f + perfil.h_w + 2*R, z0)
    p13 = Vec3(x0, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p14 = Vec3(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p15 = Vec3(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f + perfil.h_w - R + 2*R, z0)
    p16 = Vec3(x0 + (perfil.b_f / 2) - (perfil.t_w / 2), y0 + perfil.t_f + perfil.h_w - R + 2*R, z0)
    p17 = Vec3(x0 + (perfil.b_f / 2) - (perfil.t_w / 2), y0 + perfil.t_f + R, z0)
    p18 = Vec3(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f + R, z0)
    p19 = Vec3(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f, z0)
    p20 = Vec3(x0, y0 + perfil.t_f, z0)

    # Linhas retas
    linhas = [(p1, p2), (p2, p3), (p3, p4), (p6, p7), (p9, p10), (p10, p11), (p11, p12),
              (p12, p13), (p13, p14), (p16, p17), (p19, p20), (p20, p1)]

    for inicio, fim in linhas:
        line = msp.add_line(inicio, fim)
        entidades.append(line)

    # Arcos de concordância
    # Para ezdxf, os arcos são criados de forma diferente
    arc1 = msp.add_arc(center=p5, radius=R, start_angle=180, end_angle=270)
    entidades.append(arc1)
    
    arc2 = msp.add_arc(center=p8, radius=R, start_angle=90, end_angle=180)
    entidades.append(arc2)
    
    arc3 = msp.add_arc(center=p15, radius=R, start_angle=0, end_angle=90)
    entidades.append(arc3)
    
    arc4 = msp.add_arc(center=p18, radius=R, start_angle=270, end_angle=360)
    entidades.append(arc4)

    return entidades

def desenhar_s_cantoneira(msp, cantoneira: Cantoneira, ver_chapa: pd.DataFrame):
    """Desenha a seção da cantoneira usando ezdxf"""
    entidades = []
    df = ver_chapa
    R = cantoneira.R_conc
    n = len(df) // 2

    # Linhas da base (z = 0)
    for i in range(n - 1):
        if i != 3:
            p1 = Vec3(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
            p2 = Vec3(df.at[i + 1, "x (mm)"], df.at[i + 1, "y (mm)"], df.at[i + 1, "z (mm)"])
            line = msp.add_line(p1, p2)
            entidades.append(line)

    # Linhas do topo (z = comprimento)
    for i in range(n, 2 * n - 1):
        if i != 11:
            p1 = Vec3(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
            p2 = Vec3(df.at[i + 1, "x (mm)"], df.at[i + 1, "y (mm)"], df.at[i + 1, "z (mm)"])
            line = msp.add_line(p1, p2)
            entidades.append(line)

    # Linhas verticais ligando base ao topo
    for i in range(n):
        p1 = Vec3(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
        p2 = Vec3(df.at[i + n, "x (mm)"], df.at[i + n, "y (mm)"], df.at[i + n, "z (mm)"])
        line = msp.add_line(p1, p2)
        entidades.append(line)

    # Arcos de concordância
    pares_concordancia = [(3, 4), (11, 12)]
    for i, j in pares_concordancia:
        p1 = Vec3(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
        p2 = Vec3(df.at[j, "x (mm)"], df.at[j, "y (mm)"], df.at[j, "z (mm)"])
        centro = Vec3(df.at[i, "x (mm)"], df.at[j, "y (mm)"], (df.at[j, "z (mm)"] + df.at[i, "z (mm)"]) / 2)
        
        # No ezdxf, criar arco com centro, raio e ângulos
        arc = msp.add_arc(center=centro, radius=R, start_angle=180, end_angle=270)
        entidades.append(arc)

    return entidades

def desenhar_enrijecedores(msp, origem: tuple, y_base_perfil: float, chapa: Chapa, perfil: Perfil, enj: float):
    """Desenha enrijecedores usando ezdxf"""
    ox, oy, oz = origem
    y_topo_perfil = y_base_perfil + perfil.h
    y_topo_chapa = oy + chapa.h
    y_base_chapa = oy

    # Alturas verticais
    altura_sup = y_topo_chapa - y_topo_perfil
    altura_inf = y_base_perfil - y_base_chapa

    # Enrijecedor superior
    desenhar_retangulo(msp, ox + chapa.B/2, y_topo_perfil, enj/2, altura_sup, oz)

    # Enrijecedor inferior
    desenhar_retangulo(msp, ox + chapa.B/2, y_base_chapa, enj/2, altura_inf, oz)

def desenhar_retangulo(msp, x0: float, y0: float, largura: float, altura: float, z0: float):
    """Desenha um retângulo usando ezdxf"""
    p1 = Vec3(x0, y0, z0)
    p2 = Vec3(x0 + largura, y0, z0)
    p3 = Vec3(x0 + largura, y0 + altura, z0)
    p4 = Vec3(x0, y0 + altura, z0)
    p5 = Vec3(x0 - largura, y0 + altura, z0)
    p6 = Vec3(x0 - largura, y0, z0)

    msp.add_line(p1, p2)
    msp.add_line(p2, p3)
    msp.add_line(p3, p4)
    msp.add_line(p4, p5)
    msp.add_line(p5, p6)
    msp.add_line(p6, p1)

def gerar_pontos_hexagono(d: float) -> list:
    """
    Gera os pontos de um hexágono regular que representa a cabeça de um parafuso.
    Adaptado para usar com ezdxf.
    """
    from math import sqrt, cos, sin, radians
    
    # Distância entre lados opostos (convertendo pol para mm se necessário)
    distancia_lados_opostos = 1.5 * d + 3.175  # 1/8 pol = 3.175 mm

    # Raio do hexágono
    raio = distancia_lados_opostos / sqrt(3)

    pontos = []
    for i in range(6):
        angulo = radians(60 * i)
        x = raio * cos(angulo)
        y = raio * sin(angulo)
        pontos.append((x, y))

    # Fechar o hexágono
    pontos.append(pontos[0])
    return pontos

def transladar_pontos(pontos, dx, dy, dz):
    """Translada uma lista de pontos"""
    return [(x + dx, y + dy, dz) for x, y in pontos]

def rearranjar_parafusos(msp, ver_parafuso: pd.DataFrame, parafuso: Parafuso, pontos_hexagono: list, esp_chapa_mm: int):
    """Desenha parafusos e hexágonos usando ezdxf"""
    entidades = []
    
    for i in range(ver_parafuso.shape[0]):
        x_centro = ver_parafuso.iat[i, 1]
        y_centro = ver_parafuso.iat[i, 2]

        # Adicionar circunferências
        circle1 = msp.add_circle(Vec3(x_centro, y_centro, esp_chapa_mm), parafuso.d / 2)
        entidades.append(circle1)
        
        circle2 = msp.add_circle(Vec3(x_centro, y_centro, 0), parafuso.d / 2)
        entidades.append(circle2)
        
        # Desenhar hexágono
        hexagono_transladado = transladar_pontos(pontos_hexagono, x_centro, y_centro, esp_chapa_mm)
        
        for j in range(len(hexagono_transladado) - 1):
            p1 = Vec3(*hexagono_transladado[j])
            p2 = Vec3(*hexagono_transladado[j + 1])
            line = msp.add_line(p1, p2)
            entidades.append(line)
    
    return entidades

def desenhar_parafuso_cantoneira_generico(msp, perfil: Perfil, cantoneira: Cantoneira, parafuso: Parafuso, 
                                        ver_parafuso: pd.DataFrame, pontos_hexagono: list, plano: str = "XY") -> list:
    """
    Desenha parafusos e hexágonos em cantoneira usando ezdxf, tanto no plano XY quanto XZ.
    """
    entidades = []
    
    for i in range(ver_parafuso.shape[0]):
        if plano == "XY":
            x_centro = ver_parafuso.iat[i, 2]
            y_centro = ver_parafuso.iat[i, 1]
            z_centro = ver_parafuso.iat[i, 3]
            circle_centers = [Vec3(z_centro, y_centro, 0), Vec3(z_centro, y_centro, -x_centro)]
            hex_trans = (z_centro, y_centro, -y_centro)
        elif plano == "XZ":
            x_centro = ver_parafuso.iat[i, 1]
            y_centro = ver_parafuso.iat[i, 2]
            z_centro = ver_parafuso.iat[i, 3]
            circle_centers = [Vec3(x_centro, z_centro, -y_centro), Vec3(x_centro, z_centro, 0)]
            hex_trans = (x_centro, z_centro, y_centro)
        else:
            raise ValueError("plano deve ser 'XY' ou 'XZ'")

        # Desenhar círculos
        for center in circle_centers:
            circle = msp.add_circle(center, parafuso.d / 2)
            entidades.append(circle)

        # Desenhar hexágono
        hexagono_transladado = transladar_pontos(pontos_hexagono, *hex_trans)
        for j in range(len(hexagono_transladado) - 1):
            p1 = Vec3(hexagono_transladado[j][0], hexagono_transladado[j][1], -cantoneira.t_mm)
            p2 = Vec3(hexagono_transladado[j + 1][0], hexagono_transladado[j + 1][1], -cantoneira.t_mm)
            line = msp.add_line(p1, p2)
            entidades.append(line)
    
    return entidades

def aplicar_transformacoes_3d(entidades: list, rotacao_x=0, rotacao_y=0, rotacao_z=0, translacao=(0, 0, 0)):
    """
    Aplica transformações 3D às entidades (rotação e translação).
    No ezdxf, as transformações são aplicadas usando matrizes de transformação.
    """
    from ezdxf.math import Matrix44
    
    # Criar matriz de transformação
    m = Matrix44.chain(
        Matrix44.x_rotate(math.radians(rotacao_x)),
        Matrix44.y_rotate(math.radians(rotacao_y)), 
        Matrix44.z_rotate(math.radians(rotacao_z)),
        Matrix44.translate(*translacao)
    )
    
    # Aplicar transformação a todas as entidades
    for entidade in entidades:
        entidade.transform(m)

def desenhar_chapa_generica_dxf(dados_resultado: list, tipo: str = "extremidade"):
    """
    Desenha uma chapa genérica (extremidade ou cabeca) com perfil e parafusos usando ezdxf.
    """
    if tipo == "extremidade":
        [perfil_escolhido, parafuso, ver_parafuso, chapa, exp] = dados_resultado
        posicao_y = -perfil_escolhido.t_f
    elif tipo == "cabeca":
        [perfil_escolhido, parafuso, ver_parafuso, chapa, exp] = dados_resultado
        posicao_y = 20
    else:
        raise ValueError("tipo deve ser 'extremidade' ou 'cabeca'")

    doc, msp = criar_documento_dxf()
    pontos_hexagono = gerar_pontos_hexagono(parafuso.d)

    # Desenhar chapa 3D
    entidades_chapa = desenhar_chapa(msp, chapa.df, exp)

    # Desenhar seção do perfil
    entidades_perfil = desenhar_secao_perfil(
        msp, perfil_escolhido,
        (chapa.B / 2) - (perfil_escolhido.b_f / 2),
        posicao_y=posicao_y,
        altura_z=exp
    )

    # Desenhar parafusos
    entidades_parafusos = rearranjar_parafusos(msp, ver_parafuso, parafuso, pontos_hexagono, exp)

    # Aplicar rotações
    todas_entidades = entidades_chapa + entidades_perfil + entidades_parafusos
    aplicar_transformacoes_3d(todas_entidades, rotacao_x=90, rotacao_z=90, 
                            translacao=(0, -perfil_escolhido.b_f / 2, 0))    # Salvar usando diálogo
    caminho = salvar_dxf_com_dialogo(doc, f"chapa_{tipo}.dxf")
    return caminho

def desenhar_viga_sobre_pilar_dxf(enrijecedor, dados_resultado: list):
    """Desenha ligação viga sobre pilar usando ezdxf"""
    if enrijecedor == 1:
        [parafuso, perfil_pilar, chapa, ver_parafuso, N_parafusos, altura_chapa, largura_chapa, esp_chapa_mm, esp_enrij_mm, esp] = dados_resultado
    else:
        [parafuso, perfil_pilar, chapa, ver_parafuso, N_parafusos, altura_chapa, largura_chapa, esp_chapa_mm, esp] = dados_resultado
        esp_enrij_mm = 0

    doc, msp = criar_documento_dxf()
    pontos_hexagono = gerar_pontos_hexagono(parafuso.d)

    # Desenhar chapa 3D
    desenhar_chapa(msp, chapa.df, esp_chapa_mm)

    # Desenhar parafusos
    rearranjar_parafusos(msp, ver_parafuso, parafuso, pontos_hexagono, esp_chapa_mm)

    # Calcular posição do perfil
    base_perfil = min(ver_parafuso['y (mm)']) + parametro_b(parafuso.d)    # Desenhar seção do perfil
    desenhar_secao_perfil(msp, perfil_pilar, (chapa.B / 2) - (perfil_pilar.b_f / 2), 
                         posicao_y=base_perfil, altura_z=esp_chapa_mm)

    if enrijecedor == 1:
        desenhar_enrijecedores(msp, (0, 0, esp_chapa_mm), base_perfil, chapa, perfil_pilar, esp_enrij_mm)

    # Salvar usando diálogo
    caminho = salvar_dxf_com_dialogo(doc, "viga_sobre_pilar.dxf")
    return caminho

def desenhar_cantoneira_dxf(dados_resultado: list, tipo: str = "parafuso"):
    """
    Desenha uma cantoneira com perfil usando ezdxf, e opcionalmente com parafusos.
    """
    doc, msp = criar_documento_dxf()
    
    # Extrair dados dependendo do tipo
    if tipo == "solda":
        [perfil_escolhido, cantoneira_escolhida] = dados_resultado
        parafuso = None
    else:  # "parafuso" ou "solda_parafuso"
        [perfil_escolhido, parafuso, cantoneira_escolhida] = dados_resultado
    
    ver_chapa = cantoneira_escolhida.disp_vertices_chapa
    
    # Desenhar a seção da cantoneira
    entidades_cantoneira = desenhar_s_cantoneira(msp, cantoneira_escolhida, ver_chapa)
    
    # Desenhar parafusos conforme necessário
    entidades_parafusos = []
    
    if parafuso:
        ver_parafuso = cantoneira_escolhida.disp_parafusos
        pontos_hexagono = gerar_pontos_hexagono(parafuso.d)
        
        # Parafusos no plano XY (presentes em todos os casos exceto "solda")
        entidades_parafusos.extend(
            desenhar_parafuso_cantoneira_generico(
                msp, perfil_escolhido, cantoneira_escolhida, parafuso, 
                ver_parafuso, pontos_hexagono, "XY"
            )
        )

        # Parafusos no plano XZ (apenas no tipo "parafuso")
        if tipo == "parafuso":
            entidades_parafusos.extend(
                desenhar_parafuso_cantoneira_generico(
                    msp, perfil_escolhido, cantoneira_escolhida, parafuso, 
                    ver_parafuso, pontos_hexagono, "XZ"
                )
            )
    
    # Desenhar seção do perfil
    entidades_perfil = desenhar_secao_perfil(msp, perfil_escolhido, 
                                           -perfil_escolhido.b_f/2, 
                                           -perfil_escolhido.h/2, 0)
      # Aplicar transformações (equivalente às rotações do AutoCAD)
    
    # Transformações para simular as rotações e translações do código original
    aplicar_transformacoes_3d(entidades_perfil, rotacao_x=90, rotacao_z=90, 
                            translacao=(0, 0, perfil_escolhido.h/2))
      # Aplicar translações específicas das cantoneiras e parafusos
    dx, dy, dz = 10, perfil_escolhido.t_w/2, (perfil_escolhido.h - cantoneira_escolhida.comprimento)/2
    aplicar_transformacoes_3d(entidades_cantoneira + entidades_parafusos, 
                            translacao=(dx, dy, dz))

    # Salvar usando diálogo
    caminho = salvar_dxf_com_dialogo(doc, f"cantoneira_{tipo}.dxf")
    return caminho
