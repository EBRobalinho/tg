# front/color_config.py

# Cores e estilos globais para a interface

COR_BARRA_SUPERIOR = "#e0e0e0"
COR_BARRA_HOVER = "#d0d0d0"
COR_BOTAO_FECHAR_HOVER = "#ff5c5c"
COR_TEXTO_FECHAR_HOVER = "white"

STYLE_BOTAO_MENU = f"""
QToolButton {{
    background-color: transparent;
    border: none;
    font-weight: bold;
    padding: 4px 10px;
}}
QToolButton::menu-indicator {{
    image: none;
}}
QToolButton:hover {{
    background-color: {COR_BARRA_HOVER};
}}
"""

STYLE_BOTAO_JANELA = f"""
QPushButton {{
    border: none;
    background-color: {COR_BARRA_SUPERIOR};
}}
QPushButton:hover {{
    background-color: {COR_BARRA_HOVER};
}}
"""

STYLE_BOTAO_FECHAR = f"""
QPushButton {{
    border: none;
    background-color: {COR_BARRA_SUPERIOR};
}}
QPushButton:hover {{
    background-color: {COR_BOTAO_FECHAR_HOVER};
    color: {COR_TEXTO_FECHAR_HOVER};
}}
"""


# Endereço dos Icones do Aplicativo:
        # Mapeamento de nomes para imagens
icones = {
    "Viga sobre Pilar (Rígida)": "imagem_ligacao/ligacao_viga_sob_pilar.png",
    "Chapa de Cabeça (Rígida)": "imagem_ligacao/ligacao_viga_chapa_de_cabeça_pilar.png",
    "Chapa de Extremidade (Flexível)": "imagem_ligacao/ligacao_viga_chapa_de_extremidade_pilar.png",
    "Cantoneira - Parafuso (Flexível)": "imagem_ligacao/ligacao_viga_cantoneira_parafusada_pilar.png",
    "Cantoneira - Solda (Flexível)": "imagem_ligacao/ligacao_viga_cantoneira_soldada_pilar.png",
    "Cantoneira - Parafuso/Solda (Flexível)": "imagem_ligacao/ligacao_viga_cantoneira_parafusada_soldada_pilar.png"
}  
 