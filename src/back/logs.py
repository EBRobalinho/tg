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

def registrar_marcha_titulo(titulo: str):
    """Registra um título de seção na marcha de cálculo"""
    separador = "=" * len(titulo)
    MARCHA_LOG.append(f"\n{separador}\n")
    MARCHA_LOG.append(f"{titulo}\n")
    MARCHA_LOG.append(f"{separador}\n\n")

def registrar_marcha_subtitulo(subtitulo: str):
    """Registra um subtítulo na marcha de cálculo"""
    MARCHA_LOG.append(f"\n--- {subtitulo} ---\n")

def registrar_marcha_formula(descricao: str, formula: str, resultado: float, unidade: str = ""):
    """Registra uma fórmula matemática de forma estruturada"""
    MARCHA_LOG.append(f"\n🧮 {descricao}:\n")
    MARCHA_LOG.append(f"   {formula}\n")
    MARCHA_LOG.append(f"   = {resultado:.2f} {unidade}\n")

def registrar_marcha_verificacao(criterio: str, valor_calculado: float, valor_limite: float, passou: bool, unidade: str = ""):
    """Registra uma verificação normativa"""
    status = "✅ APROVADO" if passou else "❌ REPROVADO"
    comparacao = "≤" if passou else ">"
    MARCHA_LOG.append(f"\n🔍 Verificação: {criterio}\n")
    MARCHA_LOG.append(f"   {valor_calculado:.2f} {comparacao} {valor_limite:.2f} {unidade} - {status}\n")

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

