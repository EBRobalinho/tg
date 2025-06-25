import os
import json
import sys
from typing import Dict, List, Any
from back.conversions import pol_to_mm
import shutil

def get_materials_dir() -> str:
    safe_dir = os.path.expanduser("~\\AppData\\Local\\STCAD\\materials")
    os.makedirs(safe_dir, exist_ok=True)

    nomes = ["acos.json", "parafusos.json", "soldas.json"]
    for nome in nomes:
        destino = os.path.join(safe_dir, nome)
        if not os.path.exists(destino):
            if getattr(sys, 'frozen', False):
                origem_base = os.path.join(getattr(sys, '_MEIPASS', ''), "data", "materials")
            else:
                origem_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "materials"))

            origem = os.path.join(origem_base, nome)
            if os.path.exists(origem):
                shutil.copy2(origem, destino)

    return safe_dir

MATERIALS_DIR = get_materials_dir()


def ensure_materials_dir():
    """Garante que o diretório de materiais existe"""
    if not os.path.exists(MATERIALS_DIR):
        os.makedirs(MATERIALS_DIR, exist_ok=True)

def load_materials_from_file(filename: str, default_data: Dict) -> Dict:
    """Carrega dados de materiais de um arquivo, criando com dados padrão se não existir"""
    ensure_materials_dir()
    filepath = os.path.join(MATERIALS_DIR, filename)
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Erro ao carregar {filename}, usando dados padrão")
            save_materials_to_file(filename, default_data)
            return default_data
    else:
        # Arquivo não existe, criar com dados padrão
        save_materials_to_file(filename, default_data)
        return default_data

def save_materials_to_file(filename: str, data: Dict):
    """Salva dados de materiais em um arquivo"""
    ensure_materials_dir()
    filepath = os.path.join(MATERIALS_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar {filename}: {e}")

def add_material(filename: str, nome: str, propriedades: List[Any]):
    """Adiciona um novo material ao arquivo"""
    data = load_materials_from_file(filename, {})
    data[nome] = propriedades
    save_materials_to_file(filename, data)

def remove_material(filename: str, nome: str):
    """Remove um material do arquivo"""
    data = load_materials_from_file(filename, {})
    if nome in data:
        del data[nome]
        save_materials_to_file(filename, data)

# Dados padrão para inicialização
DEFAULT_ACOS = {
    "ASTM_A36": [250, 400, 200, 7850],
    "MR250": [250, 400, 200, 7850],
    "AR350": [350, 450, 200, 7850],
    "AR350COR": [350, 485, 200, 7850],
    "AR415COR": [415, 520, 200, 7850],
    "ASTM_A572_GR50": [345, 450, 200, 7850]
}

DEFAULT_PARAFUSOS = {
    "ASTM A307": [None, 415, ["1/2", "9/16", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2", "2.1/4", "2.1/2", "2.3/4", "3", "3.1/4", "3.1/2", "3.3/4", "4"]],
    "ASTM A325": [635, 830, ["1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]],
    "ASTM A490": [895, 1040, ["1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]]
}

DEFAULT_SOLDAS = {
    "E60XX": [60],
    "E70XX": [70],
    "E80XX": [80],
    "E90XX": [90]
}

# Carregamento inicial dos materiais
DIMENSOES_AÇO = load_materials_from_file("acos.json", DEFAULT_ACOS)
DIMENSOES_PARAFUSO = load_materials_from_file("parafusos.json", DEFAULT_PARAFUSOS)
DIMENSOES_SOLDA = load_materials_from_file("soldas.json", DEFAULT_SOLDAS)

# Espessuras disponíveis
espessuras_pol = ["1/4", "1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]
espessuras_mm = [pol_to_mm(x) for x in espessuras_pol]
