import os
import json
from tests.testes_sinteticos import gerar_dataset_sintetico

# Manual mapping of test IDs to expected rule categories based on descriptions
# Rules: endpoint_structure, naming_conventions, type_hints, error_handling, input_validation
VIOLATION_MAPPING = {
    # Excellent - should have no violations
    "EXC": [], 
    
    # Good - minor issues or clean
    "GOOD": [],

    # Medium
    "MED_001": ["endpoint_structure"], # Endpoint sem response_model
    "MED_002": ["naming_conventions"], # Endpoint com nome inadequado e sem type hints completos
    "MED_003": ["error_handling"],     # Endpoint sem tratamento adequado de erros
    "MED_004": ["error_handling"],     # Tratamento de erro genérico
    "MED_005": ["type_hints"],         # Sem type hints nos parâmetros
    "MED_006": ["endpoint_structure"], # Blocking IO (approximate mapping)
    "MED_007": ["endpoint_structure"], # Retorna dicionário cru sem schema
    "MED_008": ["endpoint_structure"], # Não usa APIRouter
    "MED_009": ["endpoint_structure"], # Uso incorreto de status codes
    "MED_010": ["endpoint_structure"], # Lógica de negócio complexa
    "MED_011": ["naming_conventions"], # Nome de rota inconsistente
    "MED_012": ["input_validation"],   # Query param sem validação
    "MED_013": ["endpoint_structure"], # Falta injeção de dependência
    "MED_014": ["endpoint_structure"], # Usa variáveis globais
    "MED_015": ["endpoint_structure"], # Falta de docstring total

    # Poor
    "POOR_001": ["endpoint_structure"], # Endpoint mínimo sem boas práticas
    "POOR_002": ["input_validation", "error_handling"], # Sem validação e sem tratamento
    "POOR_003": ["naming_conventions", "endpoint_structure"], # Múltiplas violações
    "POOR_004": ["endpoint_structure"], # Retorno de HTML em rota API JSON
    "POOR_005": ["input_validation"],   # eval()
    "POOR_006": ["endpoint_structure"], # Rota sem verbo HTTP
    "POOR_007": ["error_handling"],     # Captura de exceção vazia
    "POOR_008": ["input_validation"],   # Dados sensíveis
    "POOR_009": ["endpoint_structure"], # Loop infinito
    "POOR_010": ["endpoint_structure"], # Modificação de argumentos padrão
}

def get_expected_violations(case_id):
    if case_id in VIOLATION_MAPPING:
        return VIOLATION_MAPPING[case_id]
    
    prefix = case_id.split('_')[0]
    if prefix in VIOLATION_MAPPING:
        return VIOLATION_MAPPING[prefix]
        
    return []

def main():
    print("🚀 Gerando dataset de benchmark...")
    
    # 1. Obter dados sintéticos
    dataset = gerar_dataset_sintetico()
    
    # 2. Preparar diretórios
    base_dir = "benchmark"
    cases_dir = os.path.join(base_dir, "cases")
    os.makedirs(cases_dir, exist_ok=True)
    
    manifest = []
    
    # 3. Gerar arquivos
    all_categories = ["excellent", "good", "medium", "poor"]
    
    for cat in all_categories:
        examples = dataset["categories"].get(cat, [])
        for example in examples:
            case_id = example["id"]
            code = example["code"].strip()
            
            # Salvar arquivo .py
            filename = f"{case_id}.py"
            filepath = os.path.join(cases_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
                
            # Adicionar ao manifesto
            expected = get_expected_violations(case_id)
            manifest.append({
                "file": filepath,
                "expected_violations": expected,
                "description": example["description"]
            })
            
    # 4. Salvar manifesto
    manifest_path = os.path.join(base_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)
        
    print(f"✅ {len(manifest)} casos gerados em {cases_dir}")
    print(f"✅ Manifesto salvo em {manifest_path}")

if __name__ == "__main__":
    main()
