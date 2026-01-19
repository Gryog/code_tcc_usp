import json
import os
from typing import Dict


def load_rules(file_path: str) -> Dict:
    """Carrega regras de validação de um arquivo JSON."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de regras não encontrado: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Carrega as regras padrão
try:
    # Tenta carregar do diretório atual ou relativo ao arquivo
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(base_dir, "rules_standard.json")
    RULES_STANDARD = load_rules(rules_path)
except Exception as e:
    print(f"⚠️ AVISO: Não foi possível carregar rules_standard.json: {e}")
    print("Usando regras vazias como fallback.")
    RULES_STANDARD = {"rules": {}}

# Carrega as regras relaxadas
try:
    # Tenta carregar do diretório atual ou relativo ao arquivo
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(base_dir, "rules_relaxed.json")
    RULES_RELAXED = load_rules(rules_path)
except Exception as e:
    print(f"⚠️ AVISO: Não foi possível carregar rules_relaxed.json: {e}")
    print("Usando regras vazias como fallback.")
    RULES_RELAXED = {"rules": {}}
