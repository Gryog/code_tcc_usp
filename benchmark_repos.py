import os
import json
import time
from config.config import settings as SETTINGS
from validator.validator import FastAPICodeValidator
from client.geminiclient import GeminiClient
from client.mistralclient import MistralClient
from client.openaiclient import OpenAIClient
from config.rules import RULES_STANDARD, RULES_RELAXED  
from reports.charts_generator import generate_charts_report, generate_comparison_report
from reports.statistic_report_generator import analyze, generate_report
from extraction.repo_collector import RepoCollector
from validator.heuristics import ValidationHeuristics


def run_repo_benchmark(run_id=None, skip_reporting=False):
    """
    Executa benchmark em repositórios reais do GitHub.
    Args:
        run_id: Identificador opcional da execução.
        skip_reporting: Se True, não gera relatórios finais automaticamente.
    """
    run_msg = f" (Run {run_id})" if run_id is not None else ""
    print(f"🚀 Iniciando Benchmark de Repositórios Reais...{run_msg}")

    # 1. Configurar Repositórios Alvo
    repos = [
        "https://github.com/rednafi/fastapi-nano",
        "https://github.com/nsidnev/fastapi-realworld-example-app",
        "https://github.com/tiangolo/full-stack-fastapi-template"
    ]

    # 2. Configurar Clientes LLM
    clients = []

    if SETTINGS.GOOGLE_API_KEY:
        clients.append(
            {
                "name": "Gemini 2.5-flash",
                "client": GeminiClient(
                    api_key=SETTINGS.GOOGLE_API_KEY, model_name="gemini-2.5-flash"
                ),
                "file_suffix": "gemini",
            }
        )

    if SETTINGS.MISTRAL_API_KEY:
        clients.append(
            {
                "name": "Mistral Small",
                "client": MistralClient(
                    api_key=SETTINGS.MISTRAL_API_KEY, model_name="mistral-small-latest"
                ),
                "file_suffix": "mistral",
            }
        )

    # if SETTINGS.OPENAI_API_KEY:
    #     clients.append({
    #         "name": "GPT-4.1-nano",
    #         "client": OpenAIClient(api_key=SETTINGS.OPENAI_API_KEY, model_name="gpt-4.1-nano"),
    #         "file_suffix": "openai"
    #     })

    if not clients:
        print("❌ Nenhum cliente LLM configurado.")
        return

    results_summary = []

    # 3. Iterar sobre Repositórios
    # Garantir diretório de saída
    os.makedirs("results/repositorios", exist_ok=True)

    for repo_url in repos:
        collector = RepoCollector(repo_url)
        target_dir = collector.clone_repository()

        if not target_dir:
            continue

        print(f"\n📂 Analisando Repositório: {collector.repo_name}")

        # Extrair endpoints usando a nova lógica (parecido com RealWorldCollector)
        endpoints = collector.extract_endpoints()

        if not endpoints:
            print(f"⚠️ Nenhum endpoint encontrado em {collector.repo_name}.")
            collector.cleanup()
            continue

        # Prepara dicionário para validação em batch
        # Mapeia ID -> Código
        endpoint_codes = {ep["id"]: ep["code"] for ep in endpoints}

        # Iterar sobre Clientes para este Repositório
        for item in clients:
            llm_name = item["name"]
            client_instance = item["client"]
            suffix = item["file_suffix"]

            # Check if result already exists
            run_suffix = f"_run{run_id}" if run_id is not None else ""
            filename = f"results/repositorios/repo_results_{suffix}_{collector.repo_name}{run_suffix}.json"
            if os.path.exists(filename) and run_id is None:
                print(
                    f"  ⏭️  Skipping {llm_name} for {collector.repo_name} (Result exists: {filename})"
                )
                results_summary.append(
                    {
                        "llm": f"{llm_name} ({collector.repo_name})",
                        "filename": filename,
                        "repo": collector.repo_name,
                    }
                )
                continue

            print(f"  🤖 Validando {len(endpoints)} endpoints com {llm_name}...")
            start_time = time.time()

            # Validador
            validator = FastAPICodeValidator(
                llm_client=client_instance, rules=RULES_RELAXED
            )

            # Executa validação em batch nos endpoints extraídos
            try:
                report = validator.validate_batch(endpoint_codes, rate_limit_s=1.0)

                # Adiciona metadados extras aos resultados
                # (validate_batch usa o ID como file_path, vamos enriquecer se precisar)
                def derive_expected_status(violations):
                    severities = {v.get("severity", "").lower() for v in violations or []}
                    if "error" in severities:
                        return "fail"
                    if "warning" in severities:
                        return "warning"
                    return "pass"

                for res in report.get("results", []):
                    ep_id = res.get("file_path")
                    # Encontra o endpoint original para pegar mais metadados se quiser
                    orig_ep = next((e for e in endpoints if e["id"] == ep_id), None)
                    if orig_ep:
                        res["metadata"] = {
                            **res.get("metadata", {}),
                            **orig_ep["metadata"],
                        }
                        res["source_file"] = orig_ep["source"]
                        
                        # Injeta Snippet
                        if ep_id in endpoint_codes:
                            res["code_snippet"] = endpoint_codes[ep_id]
                            
                            # Injeta Heurísticas (Recall)
                            inferred_keywords = ValidationHeuristics.infer_expected_keywords(res["code_snippet"])
                            if inferred_keywords:
                                res["expected_keywords"] = inferred_keywords

                    if "expected_status" not in res:
                        res["expected_status"] = derive_expected_status(res.get("violations", []))
                        res["expected_status_source"] = "derived_from_violations"

                # Calcular uso total de tokens
                total_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                for res in report.get("results", []):
                    usage = res.get("_metadata", {}).get("token_usage", {})
                    # Adaptar chaves diferentes (Gemini vs Mistral/OpenAI) 
                    # Gemini: prompt_token_count, candidates_token_count, total_token_count
                    # Mistral/OpenAI: prompt_tokens, completion_tokens, total_tokens
                    
                    p_tokens = usage.get("prompt_tokens") or usage.get("prompt_token_count") or 0
                    c_tokens = usage.get("completion_tokens") or usage.get("candidates_token_count") or 0
                    t_tokens = usage.get("total_tokens") or usage.get("total_token_count") or 0
                    
                    total_tokens["prompt_tokens"] += p_tokens
                    total_tokens["completion_tokens"] += c_tokens
                    total_tokens["total_tokens"] += t_tokens

                # Metadados do Benchmark
                report["benchmark_metadata"] = {
                    "llm_name": llm_name,
                    "repo_name": collector.repo_name,
                    "repo_url": repo_url,
                    "total_time": round(time.time() - start_time, 2),
                    "total_endpoints": len(endpoints),
                    "skipped_files_count": len(collector.skipped_files),
                    "skipped_files": collector.skipped_files,
                    "token_usage": total_tokens
                }

                # Salvar resultado
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                print(
                    f"✅ Concluído ({report['benchmark_metadata']['total_time']}s). Salvo: {filename}"
                )

                results_summary.append(
                    {
                        "llm": f"{llm_name} ({collector.repo_name})",
                        "filename": filename,
                        "repo": collector.repo_name,
                    }
                )

            except Exception as e:
                print(f"❌ Erro ao validar com {llm_name}: {e}")

        # Limpeza após todos os LLMs rodarem neste repo
        collector.cleanup()

    print("\n🏁 Benchmark de Repositórios Finalizado!")
    
    if skip_reporting:
        print("⏩ Pulando geração de relatórios (skip_reporting=True)")
        return

    # Gera relatórios finais (Reaproveitando geradores existentes)
    # Nota: generate_charts_report pode precisar de ajuste se esperar estrutura exata do benchmark sintético,
    # mas vamos tentar usar. Para análise estatística funciona.

    print("\n📊 Gerando Relatórios Consolidados...")
    try:
        analyze(results_summary)
        generate_report(results_summary)
        generate_charts_report(
            file_pattern="results/repositorios/repo_results_*.json",
            output_file="results/benchmark_repos_report.html",
        )
        generate_comparison_report(
            file_pattern="results/repositorios/repo_results_*.json",
            output_file="results/benchmark_repos_comparison_report.html"
        )
    except Exception as e:
        print(f"⚠️ Erro na geração de relatório final: {e}")


if __name__ == "__main__":
    run_repo_benchmark()
