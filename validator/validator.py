from client import llmclient
import config.prompt
from schemas import schema
import json
import time
import os
from pydantic import ValidationError
from typing import Dict, Any


class FastAPICodeValidator:
    def __init__(self, llm_client: llmclient.LLMClient, rules: Dict):
        """
        Recebe o cliente LLM injetado. Não cria o cliente internamente.
        Isso torna a classe testável e agnóstica.
        """
        self.llm_client = llm_client
        self.rules = rules

    def _build_prompt(self, code: str) -> str:
        # Serializa as regras para o prompt
        rules_str = json.dumps(self.rules, indent=2, ensure_ascii=False)

        # Prompt Engineering estruturado
        return config.prompt.VALIDATION_PROMPT_TEMPLATE.format(
            rules_text=rules_str, code=code
        )

    def validate(self, code: str) -> Dict[str, Any]:
        """
        Valida um trecho de código (string).
        Mantido para retrocompatibilidade e uso simples.
        """
        prompt_text = self._build_prompt(code)
        start_time = time.time()

        try:
            # 1. Chama o LLM (que retorna um Dict cru)
            raw_result = self.llm_client.generate_json(prompt_text)

            # 2. Valida a estrutura com Pydantic (Garante integridade)
            validated_data = schema.ValidationResult(**raw_result)

            # 3. Adiciona metadados de execução
            result_dict = validated_data.model_dump()
            response_time = round(time.time() - start_time, 2)
            result_dict["_metadata"] = {
                "response_time": response_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            result_dict["response_time"] = response_time
            return result_dict

        except ValidationError as e:
            return {
                "error": "O modelo retornou um JSON com schema inválido",
                "details": str(e),
                "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
            }
        except Exception as e:
            return {
                "error": "Erro sistêmico na validação",
                "details": str(e),
                "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
            }

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Valida um arquivo específico."""
        if not os.path.exists(file_path):
            return {
                "error": f"Arquivo não encontrado: {file_path}",
                "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            result = self.validate(code)
            result["file_path"] = file_path
            return result
        except Exception as e:
            return {
                "error": f"Erro ao ler arquivo: {str(e)}",
                "file_path": file_path,
                "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
            }

    def validate_project(
        self, root_path: str, ignore_folders: list = None, target_patterns: list = None
    ) -> Dict[str, Any]:
        """
        Varre um diretório recursivamente e valida arquivos Python.
        Args:
            root_path: Caminho raiz do projeto.
            ignore_folders: Lista de pastas a ignorar (ex: ['.venv']).
            target_patterns: Lista de substrings para filtrar caminhos (ex: ['routes', 'api']).
                             Se fornecido, analise apenas arquivos cujo path completo contenha um dos patterns.
        """
        if ignore_folders is None:
            ignore_folders = [".venv", ".git", "__pycache__", "venv", "env"]

        results = []
        overall_stats = {"passed": 0, "failed": 0, "errors": 0}

        for root, dirs, files in os.walk(root_path):
            # Filtra diretórios ignorados
            dirs[:] = [d for d in dirs if d not in ignore_folders]

            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)

                    # Logica de filtro positivo (target_patterns)
                    if target_patterns:
                        # Normaliza separadores para garantir match
                        normalized_path = full_path.replace(os.sep, "/")
                        if not any(
                            pattern in normalized_path for pattern in target_patterns
                        ):
                            continue

                    print(f"🔍 Analisando: {full_path}...")
                    time.sleep(1.0)  # Rate limiting manual

                    file_result = self.validate_file(full_path)

                    # Atualiza estatísticas
                    if "error" in file_result:
                        overall_stats["errors"] += 1
                        error_detail = file_result.get("details", "Sem detalhes")
                        print(
                            f"   ❌ Erro: {file_result['error']} - Detalhes: {error_detail}"
                        )
                    elif file_result.get("overall_status") == "fail":
                        overall_stats["failed"] += 1
                        print(
                            f"   ⚠️  Issues found (Score: {file_result.get('overall_score')})"
                        )
                    else:
                        overall_stats["passed"] += 1
                        print(f"   ✅ OK (Score: {file_result.get('overall_score')})")

                    results.append(file_result)

        return {
            "summary": overall_stats,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def validate_batch(
        self, codes: Dict[str, str], rate_limit_s: float = 0.0
    ) -> Dict[str, Any]:
        """
        Valida múltiplos trechos de código fornecidos como um dicionário (nome -> código).
        Retorna um relatório consolidado.
        """
        results = []
        overall_stats = {"passed": 0, "failed": 0, "errors": 0}

        for name, code in codes.items():
            print(f"🔍 Analisando: {name}...")

            # Reutiliza logica de validação unica
            result = self.validate(code)
            result["file_path"] = name  # Usa o nome como "caminho"

            # Atualiza estatísticas
            if "error" in result:
                overall_stats["errors"] += 1
                error_detail = result.get("details", "Sem detalhes")
                print(f"   ❌ Erro: {result['error']} - Detalhes: {error_detail}")
            elif result.get("overall_status") == "fail":
                overall_stats["failed"] += 1
                print(f"   ⚠️  Issues found (Score: {result.get('overall_score')})")
            else:
                overall_stats["passed"] += 1
                print(f"   ✅ OK (Score: {result.get('overall_score')})")

            results.append(result)
            if rate_limit_s > 0:
                time.sleep(rate_limit_s)

        return {
            "summary": overall_stats,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

