from back.conversions import pol_to_mm
from math import radians, sin, cos, sqrt
from pyautocad import Autocad
import win32com.client
import time

#Inicia a instância do Autocad

def iniciar_autocad():
        # Força o AutoCAD a abrir, se necessário
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = True  # Garante que a janela fique visível

    # Aguarda um tempo para garantir que carregou
    time.sleep(2)

    # Conecta com a instância ativa e garante documento aberto
    acad = Autocad(create_if_not_exists=True)
    return acad

#Apagar o que estiver desenhado

def limpar_desenho(acad, max_tentativas=20, pausa=0.2):
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
                except Exception:
                    pass  # ignora falha ao deletar objeto individual

            acad.doc.Regen(1)
            print("✅ Desenho limpo com sucesso.")
            return  # sucesso, sai da função

        except Exception:
            print(f"⚠️ Tentativa {tentativa + 1} falhou... tentando novamente.")
            time.sleep(pausa)

    print("❌ Não foi possível limpar completamente o desenho após várias tentativas.")

#Calcula uma lista com os vértices do hexágono do parafuso

def gerar_pontos_hexagono(d: float)-> list:
    """
    Gera os pontos de um hexágono regular que representa a cabeça de um parafuso.

    Args:
        d (float): Diâmetro do parafuso em mm.

    Returns:
        list: Lista com as coordenadas (x, y) dos 7 vértices do hexágono (o último ponto é igual ao primeiro).
    """
    # Distância entre lados opostos
    distancia_lados_opostos = 1.5 * d + pol_to_mm("1/8")

    # Raio do hexágono (distância do centro até cada vértice)
    raio = distancia_lados_opostos / sqrt(3)

    pontos = []
    for i in range(6):
        angulo = radians(60 * i)
        x = raio * cos(angulo)
        y = raio * sin(angulo)
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

""" def escrever_descricao(acad, x, y, z, Ligante ,nome_cantoneira, nome_perfil, espessura_solda,obs=''):

    Escreve uma anotação técnica no plano YZ, deslocada 5 mm no eixo Y.
    O texto fica de lado (como se fosse uma vista lateral).

    texto = f"{Ligante} {nome_cantoneira} soldada no perfil {nome_perfil}, com solda do tipo filete de {espessura_solda} mm\n{obs}"

    # Posição inicial (no plano YZ → x constante)
    ponto_texto = APoint(x, y, z)

    # Cria o texto
    texto_obj = acad.model.AddText(texto, ponto_texto, 2.5)  # altura do texto

    # Rotaciona 90° para aparecer no plano YZ (em torno de Z)
    texto_obj.Rotate3D(APoint(0, 0, 0), APoint(1, 0, 0), radians(90))

    # Rotaciona 90° para aparecer no plano YZ (em torno de Z)
    texto_obj.Rotate3D(APoint(0, 0, 0), APoint(0, 0, 1), radians(90))

    ponto = texto_obj.InsertionPoint

    # Acessar x, y, z separadamente
    x = ponto[0]
    y = ponto[1]
    z = ponto[2]

    texto_obj.Move(APoint(x,y,z),APoint(z,y,x)) """