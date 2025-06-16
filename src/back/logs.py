import re

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

