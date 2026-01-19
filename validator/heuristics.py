import re
from typing import List, Set, Dict, Tuple


class ValidationHeuristics:
    """
    Analisa estaticamente o código para inferir quais violações (palavras-chave)
    seriam esperadas de um validador LLM, baseando-se nas regras do projeto.
    """

    @staticmethod
    def infer_expected_keywords(code: str) -> List[str]:
        """
        Retorna lista de palavras-chave esperadas nas validações LLM
        baseado em heurísticas sobre o código.
        """
        expected_keywords: Set[str] = set()
        code_lower = code.lower()

        # Detecta se é um endpoint FastAPI
        is_endpoint = bool(re.search(r"@(router|app)\.(get|post|put|delete|patch)\(", code))
        
        if is_endpoint:
            # Extrai informações do decorator
            decorator_info = ValidationHeuristics._extract_decorator_info(code)
            http_method = decorator_info.get("method", "").upper()
            
            # 1. ENDPOINT_STRUCTURE
            expected_keywords.update(
                ValidationHeuristics._check_endpoint_structure(code, decorator_info)
            )
            
            # 2. HTTP_SEMANTICS
            expected_keywords.update(
                ValidationHeuristics._check_http_semantics(code, decorator_info, http_method)
            )
            
            # 3. INPUT_VALIDATION_AND_OPENAPI
            expected_keywords.update(
                ValidationHeuristics._check_input_validation(code)
            )

        # 4. NAMING_CONVENTIONS
        expected_keywords.update(
            ValidationHeuristics._check_naming_conventions(code)
        )
        
        # 5. TYPE_HINTS
        expected_keywords.update(
            ValidationHeuristics._check_type_hints(code)
        )
        
        # 6. ERROR_HANDLING
        expected_keywords.update(
            ValidationHeuristics._check_error_handling(code, code_lower)
        )

        return sorted(list(expected_keywords))

    @staticmethod
    def _extract_decorator_info(code: str) -> Dict[str, str]:
        """Extrai informações do decorator do endpoint."""
        info = {}
        
        # Extrai método HTTP
        method_match = re.search(r"@(?:router|app)\.(get|post|put|delete|patch)\(", code)
        if method_match:
            info["method"] = method_match.group(1)
        
        # Extrai status_code se presente
        status_match = re.search(r"status_code\s*=\s*(\d+)", code)
        if status_match:
            info["status_code"] = status_match.group(1)
        
        # Verifica response_model
        info["has_response_model"] = "response_model" in code
        
        # Verifica tags
        info["has_tags"] = bool(re.search(r"tags\s*=\s*\[", code))
        
        return info

    @staticmethod
    def _check_endpoint_structure(code: str, decorator_info: Dict[str, str]) -> Set[str]:
        """Valida estrutura básica do endpoint."""
        keywords = set()
        
        # Docstring
        func_match = re.search(r"def\s+\w+\([^)]*\).*?:", code, re.DOTALL)
        if func_match:
            func_end = func_match.end()
            next_lines = code[func_end:func_end+200]
            if '"""' not in next_lines and "'''" not in next_lines:
                keywords.update(["docstring", "documentation", "description"])
        
        # response_model (exceto para 204, Response, streaming)
        if not decorator_info.get("has_response_model"):
            status = decorator_info.get("status_code", "")
            if status != "204" and "Response" not in code and "StreamingResponse" not in code and "FileResponse" not in code:
                keywords.update(["response_model", "output schema", "pydantic model"])
        
        # status_code explícito
        if "status_code" not in decorator_info:
            keywords.update(["status_code", "explicit status", "http status"])
        
        # tags
        if not decorator_info.get("has_tags"):
            keywords.update(["tags", "endpoint organization", "openapi tags"])
        
        return keywords

    @staticmethod
    def _check_http_semantics(code: str, decorator_info: Dict[str, str], method: str) -> Set[str]:
        """Valida semântica HTTP."""
        keywords = set()
        status = decorator_info.get("status_code", "")
        
        # POST deve usar 201 se cria recurso
        if method == "POST" and "db.add" in code and status not in ["201", "202"]:
            keywords.update(["201 created", "status code semantics", "resource creation"])
        
        # DELETE sem body deve usar 204
        if method == "DELETE" and "return" in code:
            return_match = re.search(r"return\s+(\w+|\{)", code)
            if return_match and return_match.group(1) not in ["None", "Response"]:
                if status != "204":
                    keywords.update(["204 no content", "delete response", "empty body"])
        
        # Status 204 não deve retornar corpo
        if status == "204":
            if re.search(r"return\s+\w+(?!None|Response\()", code):
                keywords.update(["204 no body", "empty response", "no content"])
        
        # Status 201 deve retornar representação do recurso
        if status == "201":
            if "return None" in code or not re.search(r"return\s+\w+", code):
                keywords.update(["201 response body", "resource representation", "created resource"])
        
        # PUT/PATCH devem retornar representação ou 204
        if method in ["PUT", "PATCH"]:
            if status not in ["200", "204"] and status:
                keywords.update(["update semantics", "put/patch response", "resource representation"])
        
        # Async jobs devem usar 202
        if "background_tasks" in code.lower() or "celery" in code.lower():
            if status != "202":
                keywords.update(["202 accepted", "async processing", "background task"])
        
        return keywords

    @staticmethod
    def _check_input_validation(code: str) -> Set[str]:
        """Valida validação de entrada e documentação OpenAPI."""
        keywords = set()
        
        # Body requests devem usar Pydantic models
        if re.search(r"def\s+\w+\([^)]*:\s*dict", code):
            keywords.update(["pydantic model", "request body", "input validation"])
        
        # Path parameters com constraints devem usar Path()
        path_params = re.findall(r"{\w+}", code)
        if path_params and "Path(" not in code:
            # Verifica se há tipos como int, UUID que sugerem validação
            if re.search(r":\s*(int|UUID|uuid)", code):
                keywords.update(["Path()", "path validation", "parameter constraints"])
        
        # Query parameters com paginação/filtros devem usar Query()
        if re.search(r"(skip|limit|page|filter|search)\s*:\s*\w+\s*=", code):
            if "Query(" not in code:
                keywords.update(["Query()", "query validation", "parameter documentation"])
        
        # Modelos sem Field quando precisam constraints
        if "class " in code and "BaseModel" in code:
            if "str" in code or "int" in code:
                if "Field(" not in code and not re.search(r"(min_length|max_length|ge|le|gt|lt)", code):
                    keywords.update(["Field()", "model constraints", "validation rules"])
        
        # Uso incorreto de Body() para dependências
        if re.search(r"Body\(\).*(?:BackgroundTasks|Session|Depends)", code):
            keywords.update(["incorrect Body()", "dependency injection", "background tasks"])
        
        return keywords

    @staticmethod
    def _check_naming_conventions(code: str) -> Set[str]:
        """Valida convenções de nomenclatura."""
        keywords = set()
        
        # Funções em camelCase (deveria ser snake_case)
        if re.search(r"def [a-z]+[A-Z]\w+\(", code):
            keywords.update(["snake_case", "function naming", "python conventions"])
        
        # Funções sem verbo de ação
        func_names = re.findall(r"def (\w+)\(", code)
        action_verbs = ["get", "post", "create", "update", "delete", "list", "fetch", "retrieve"]
        for name in func_names:
            if not any(name.startswith(verb) for verb in action_verbs):
                if not name.startswith("_"):  # Ignora métodos privados
                    keywords.update(["action verb", "function naming", "descriptive names"])
                    break
        
        # Classes não em PascalCase
        if re.search(r"class [a-z_]+\w*(?:\(|:)", code):
            keywords.update(["PascalCase", "class naming", "python conventions"])
        
        # Variáveis em camelCase
        if re.search(r"\b[a-z]+[A-Z]\w+\s*=", code):
            keywords.update(["variable naming", "snake_case", "python style"])
        
        return keywords

    @staticmethod
    def _check_type_hints(code: str) -> Set[str]:
        """Valida uso de type hints."""
        keywords = set()
        
        # Funções sem type hints nos parâmetros
        func_pattern = r"def \w+\(([^)]+)\)"
        for match in re.finditer(func_pattern, code):
            params = match.group(1)
            if params and params.strip() not in ["self", "cls"]:
                # Verifica se tem parâmetros sem type hint (exceto self/cls)
                if re.search(r"\w+\s*(?:,|=|\))", params) and ":" not in params:
                    keywords.update(["type hints", "parameter types", "type annotations"])
                    break
        
        # Funções sem return type annotation
        if re.search(r"def \w+\([^)]*\)\s*:", code):
            if not re.search(r"def \w+\([^)]*\)\s*->", code):
                keywords.update(["return type", "type annotation", "function signature"])
        
        # Uso de dict genérico ao invés de BaseModel
        if re.search(r":\s*dict(?:\s|,|\)|=)", code):
            keywords.update(["BaseModel", "typed dict", "specific types"])
        
        # Falta de Optional para valores None
        if re.search(r"=\s*None", code) and "Optional[" not in code and "| None" not in code:
            keywords.update(["Optional", "nullable types", "type hints"])
        
        return keywords

    @staticmethod
    def _check_error_handling(code: str, code_lower: str) -> Set[str]:
        """Valida tratamento de erros."""
        keywords = set()
        
        # Operações de banco sem try-except
        db_operations = ["db.query", "db.add", "db.commit", "db.delete", "db.execute"]
        has_db_op = any(op in code for op in db_operations)
        
        if has_db_op and "try:" not in code:
            keywords.update(["try-except", "error handling", "exception handling"])
        
        # Requisições HTTP sem try-except
        if ("requests." in code or "httpx." in code) and "try:" not in code:
            keywords.update(["try-except", "network error", "request handling"])
        
        # Operações de arquivo sem tratamento
        if ("open(" in code or "file." in code) and "try:" not in code:
            keywords.update(["file handling", "io errors", "exception handling"])
        
        # Uso apropriado de HTTPException
        if has_db_op or "permission" in code_lower or "auth" in code_lower:
            if "raise HTTPException" not in code:
                keywords.update(["HTTPException", "http errors", "status codes"])
        
        # Status codes incorretos em exceções
        exception_matches = re.finditer(r"HTTPException\([^)]*status_code\s*=\s*(\d+)", code)
        for match in exception_matches:
            status = match.group(1)
            if status not in ["400", "401", "403", "404", "422", "500", "503"]:
                keywords.update(["correct status codes", "http semantics", "error codes"])
        
        return keywords