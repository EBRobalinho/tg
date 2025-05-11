import math
import design_functions
from v_p_chapa_cabeca import *
from materials import *
from pyautocad import Autocad, APoint
import time

def limpar_desenho(acad, max_tentativas=100, pausa=0.2):
    """
    Tenta apagar todos os objetos do desenho atual no AutoCAD,
    com repetição controlada em caso de erro COM.
    """
    for tentativa in range(max_tentativas):
        try:
            objetos = list(acad.iter_objects())

            for obj in objetos:
                try:
                    obj.Delete()
                except:
                    pass  # ignora falha ao deletar objeto individual

            acad.doc.Regen(1)
            print("✅ Desenho limpo com sucesso.")
            return  # sucesso, sai da função

        except Exception as e:
            print(f"⚠️ Tentativa {tentativa + 1} falhou... tentando novamente.")
            time.sleep(pausa)

    print("❌ Não foi possível limpar completamente o desenho após várias tentativas.")

### Funções para o desenho da ligação Vigas-Pilar com chapa de cabeça ###

def gerar_pontos_hexagono(d):
    """
    Gera os pontos de um hexágono regular que representa a cabeça de um parafuso.

    Args:
        d (float): Diâmetro do parafuso em mm.

    Returns:
        list: Lista com as coordenadas (x, y) dos 7 vértices do hexágono (o último ponto é igual ao primeiro).
    """
    # Distância entre lados opostos
    distancia_lados_opostos = 1.5 * d + pol_to_mm(1/8)

    # Raio do hexágono (distância do centro até cada vértice)
    raio = distancia_lados_opostos / math.sqrt(3)

    pontos = []
    for i in range(6):
        angulo = math.radians(60 * i)
        x = raio * math.cos(angulo)
        y = raio * math.sin(angulo)
        pontos.append((x, y))

    # Fechar o hexágono, adicionando o primeiro ponto ao final da lista
    pontos.append(pontos[0])

    return pontos


def transladar_pontos(pontos, dx, dy, dz):
    """
    Translada uma lista de pontos por dx e dy.

    Args:
        pontos (list): Lista com coordenadas (x, y).
        dx (float): Deslocamento no eixo x.
        dy (float): Deslocamento no eixo y.

    Returns:
        list: Lista de pontos translados.
    """
    return [(x + dx, y + dy, dz) for x, y in pontos]

# Função para criar chapa 3D com espessura
def criar_chapa_3d(acad, pontos, exp):
    obj_chapa=[]
    """
    Cria uma chapa em 3D considerando a espessura.

    Args:
        acad: Instância do Autocad
        pontos: DataFrame com coordenadas dos vértices (colunas x, y)
        exp: Espessura da chapa em mm
    """
    num_pontos = pontos.shape[0]

    # Criando vértices inferiores e superiores
    pontos_inferiores = [APoint(pontos.iat[i, 1], pontos.iat[i, 2], 0) for i in range(num_pontos)]
    pontos_superiores = [APoint(p.x, p.y, exp) for p in pontos_inferiores]

    # Desenhando linhas da base inferior
    for i in range(num_pontos - 1):
        obj = acad.model.AddLine(pontos_inferiores[i], pontos_inferiores[i + 1])
        obj_chapa.append(obj)
    # Fechar a base inferior
    obj = acad.model.AddLine(pontos_inferiores[-1], pontos_inferiores[0])
    obj_chapa.append(obj)
    # Desenhando linhas da base superior
    for i in range(num_pontos - 1):
        obj = acad.model.AddLine(pontos_superiores[i], pontos_superiores[i + 1])
        obj_chapa.append(obj)
    # Fechar a base superior
    obj = acad.model.AddLine(pontos_superiores[-1], pontos_superiores[0])
    obj_chapa.append(obj)

    # Conectando as bases inferior e superior
    for i in range(num_pontos):
        obj = acad.model.AddLine(pontos_inferiores[i], pontos_superiores[i])
        obj_chapa.append(obj)

    return obj_chapa

def desenhar_secao_perfil(acad, perfil, posicao_x, posicao_y=20, altura_z=None):
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
    p4 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f, z0)
    p5 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f + R, z0)
    p6 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2), y0 + perfil.t_f + R, z0)
    p7 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2), y0 + perfil.t_f + perfil.h_w + R, z0)
    p8 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f + perfil.h_w + R, z0)
    p9 = APoint(x0 + (perfil.b_f / 2) + (perfil.t_w / 2) + R, y0 + perfil.t_f + perfil.h_w + 2*R , z0)
    p10 = APoint(x0 + perfil.b_f, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p11 = APoint(x0 + perfil.b_f, y0 + 2*perfil.t_f + perfil.h_w + 2*R, z0)
    p12 = APoint(x0, y0 + 2*perfil.t_f + perfil.h_w + 2*R, z0)
    p13 = APoint(x0, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p14 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f + perfil.h_w + 2*R, z0)
    p15 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f + perfil.h_w - R + 2*R, z0)
    p16 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2), y0 + perfil.t_f + perfil.h_w - R + 2*R, z0)
    p17 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2), y0 + perfil.t_f + R, z0)
    p18 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f + R, z0)
    p19 = APoint(x0 + (perfil.b_f / 2) - (perfil.t_w / 2) - R, y0 + perfil.t_f, z0)
    p20 = APoint(x0, y0 + perfil.t_f, z0)

    # Linhas retas
    linhas = [(p1, p2), (p2, p3), (p3, p4), (p6, p7), (p9, p10), (p10, p11), (p11, p12),
              (p12, p13), (p13, p14), (p16, p17), (p19, p20), (p20, p1)]

    for linha in linhas:
        obj = acad.model.AddLine(*linha)
        objetos.append(obj)

    # Arcos de concordância
    objetos.append(acad.model.AddArc(p5, R, math.radians(180), math.radians(270)))
    objetos.append(acad.model.AddArc(p8, R, math.radians(90), math.radians(180)))
    objetos.append(acad.model.AddArc(p15, R, math.radians(0), math.radians(90)))
    objetos.append(acad.model.AddArc(p18, R, math.radians(270), math.radians(360)))

    return objetos

def desenhar_s_cantoneira(acad, cantoneira, ver_chapa):
    objetos = []
    # === Geometria da chapa ===
    df = ver_chapa
    R = cantoneira.R_conc
    n = len(df) // 2

    # Linhas da base (z = 0)
    for i in range(n - 1):
        if i != 3:
            p1 = APoint(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
            p2 = APoint(df.at[i + 1, "x (mm)"], df.at[i + 1, "y (mm)"], df.at[i + 1, "z (mm)"])
            objetos.append(acad.model.AddLine(p1, p2))

    # Linhas do topo (z = comprimento)
    for i in range(n, 2 * n - 1):
        if i != 11:
            p1 = APoint(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
            p2 = APoint(df.at[i + 1, "x (mm)"], df.at[i + 1, "y (mm)"], df.at[i + 1, "z (mm)"])
            objetos.append(acad.model.AddLine(p1, p2))

    # Linhas verticais ligando base ao topo
    for i in range(n):
        p1 = APoint(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
        p2 = APoint(df.at[i + n, "x (mm)"], df.at[i + n, "y (mm)"], df.at[i + n, "z (mm)"])
        objetos.append(acad.model.AddLine(p1, p2))

    # Arcos de concordância verticais
    pares_concordancia = [(3, 4), (11, 12)]
    for i, j in pares_concordancia:
        p1 = APoint(df.at[i, "x (mm)"], df.at[i, "y (mm)"], df.at[i, "z (mm)"])
        p2 = APoint(df.at[j, "x (mm)"], df.at[j, "y (mm)"], df.at[j, "z (mm)"])
        centro = APoint(p1.x, p2.y, (p1.z + p2.z) / 2)
        objetos.append(acad.model.AddArc(centro, R, math.pi, 3 * math.pi / 2))

    return objetos

def escrever_descricao(acad, x, y, z, Ligante ,nome_cantoneira, nome_perfil, espessura_solda,obs=''):
    """
    Escreve uma anotação técnica no plano YZ, deslocada 5 mm no eixo Y.
    O texto fica de lado (como se fosse uma vista lateral).
    """
    texto = f"{Ligante} {nome_cantoneira} soldada no perfil {nome_perfil}, com solda do tipo filete de {espessura_solda} mm " + f'\n' + f"{obs}"

    # Posição inicial (no plano YZ → x constante)
    ponto_texto = APoint(x, y, z)

    # Cria o texto
    texto_obj = acad.model.AddText(texto, ponto_texto, 2.5)  # altura do texto

    # Rotaciona 90° para aparecer no plano YZ (em torno de Z)
    texto_obj.Rotate3D(APoint(0, 0, 0), APoint(1, 0, 0), math.radians(90))

    # Rotaciona 90° para aparecer no plano YZ (em torno de Z)
    texto_obj.Rotate3D(APoint(0, 0, 0), APoint(0, 0, 1), math.radians(90))

    ponto = texto_obj.InsertionPoint

    # Acessar x, y, z separadamente
    x = ponto[0]
    y = ponto[1]
    z = ponto[2]

    texto_obj.Move(APoint(x,y,z),APoint(z,y,x))

def desenhar_enrijecedores(acad, origem,y_base_perfil,chapa, perfil, ver_parafuso, diametro_parafuso, enj):
    ox, oy,oz = origem  # origem no plano XY
    y_topo_perfil = y_base_perfil + perfil.h
    y_topo_chapa = oy + chapa.h 
    y_base_chapa = oy

    # Alturas verticais
    altura_sup = y_topo_chapa - y_topo_perfil
    altura_inf = y_base_perfil - y_base_chapa
    comprimento_lat = (chapa.B / 2) - (perfil.t_w / 2)

    # Enrijecedor superior
    desenhar_retangulo(acad, ox + chapa.B/2, y_topo_perfil, enj/2, altura_sup,oz)

    # Enrijecedor inferior
    desenhar_retangulo(acad, ox + chapa.B/2, y_base_chapa, enj/2, altura_inf,oz)

def desenhar_retangulo(acad, x0, y0, largura, altura,z0):
    p1 = APoint(x0, y0,z0)
    p2 = APoint(x0 + largura, y0,z0)
    p3 = APoint(x0 + largura, y0 + altura,z0)
    p4 = APoint(x0, y0 + altura,z0)
    p5 = APoint(x0 - largura, y0 + altura,z0)
    p6 = APoint(x0 - largura, y0,z0)



    acad.model.AddLine(p1, p2)
    acad.model.AddLine(p2, p3)
    acad.model.AddLine(p3, p4)
    acad.model.AddLine(p4, p5)
    acad.model.AddLine(p5, p6)
    acad.model.AddLine(p6, p1)

def rearranjar_parafusos(acad, ver_parafuso,objetos_parafusos, parafuso,pontos_hexagono, esp_chapa_mm):
    #Rearranjar os parafusos para desenhar  
    for i in range(ver_parafuso.shape[0]):
        x_centro = ver_parafuso.iat[i, 1]
        y_centro = ver_parafuso.iat[i, 2]

        # Adicionar circunferência no ponto
        obj = acad.model.AddCircle(APoint(x_centro, y_centro,esp_chapa_mm), parafuso.diametro_mm / 2)
        objetos_parafusos.append(obj)
        obj = acad.model.AddCircle(APoint(x_centro, y_centro,0), parafuso.diametro_mm / 2)
        objetos_parafusos.append(obj)
        # Transladar hexágono para o ponto atual
        hexagono_transladado = transladar_pontos(pontos_hexagono, x_centro, y_centro, esp_chapa_mm)

        for j in range(len(hexagono_transladado) - 1):
            p1 = APoint(*hexagono_transladado[j])
            p2 = APoint(*hexagono_transladado[j + 1])
            obj = acad.model.AddLine(p1, p2)
            objetos_parafusos.append(obj)
