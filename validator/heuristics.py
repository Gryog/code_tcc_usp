import re
from typing import List, Dict

class ValidationHeuristics:
    """
    Analisa estaticamente o código para inferir quais violações (palavras-chave)
    seriam esperadas de um validador LLM, baseando-se nas regras do projeto.
    """

    @staticmethod
    def infer_expected_keywords(code: str) -> List[str]:
        expected_keywords = []
        code_lower = code.lower()

        # 1. Regra: endpoint_structure (response_model)
        # Se tem @router/app.method mas não tem response_model
        if re.search(r"@(router|app)\.(get|post|put|delete|patch)\(", code):
            if "response_model" not in code:
                expected_keywords.extend(["response_model", "output schema", "return type"])

            # Regra: status_code explícito
            if "status_code" not in code:
                expected_keywords.extend(["status_code", "status explícito", "200", "201"])

            # Regra: tags
            if "tags=[" not in code and "tags =" not in code:
                expected_keywords.extend(["tags", "doc", "swagger", "organization"])

        # 2. Regra: error_handling
        # Se faz query no banco ou requests mas não tem try/except
        if ("db.query" in code or "requests." in code) and "try:" not in code:
            expected_keywords.extend(["try-except", "error handling", "tratamento de erro", "exception"])
        
        # Se usa HTTPException
        if "raise HTTPException" not in code and ("db." in code or "permission" in code_lower):
            # É apenas um 'warning' heurístico, pois pode ter handlers globais, mas vale notar
            pass 

        # 4. Regra: naming_conventions (Snake Case)
        # Busca definições de função em camelCase (ex: def getUserUser:)
        if re.search(r"def [a-z]+[A-Z]\w+\(", code):
             expected_keywords.extend(["snake_case", "naming convention", "pythonic"])

        # 5. Segurança (Extras)
        if "eval(" in code or "exec(" in code:
            expected_keywords.extend(["security", "eval", "code injection", "perigoso"])
        
        if "password" in code_lower and ("response_model" not in code):
            expected_keywords.extend(["sensitive", "password", "security", "leak"])
            
        return list(set(expected_keywords))
