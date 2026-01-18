import os
import json
import time
from typing import Dict, List, Any
from config.config import settings as SETTINGS
from validator.validator import FastAPICodeValidator
from client.geminiclient import GeminiClient
from client.mistralclient import MistralClient
from client.openaiclient import OpenAIClient
from tests.testes_sinteticos import gerar_dataset_sintetico
from config.rules import RULES_STANDARD
from reports.charts_generator import generate_charts_report, generate_comparison_report
from reports.statistic_report_generator import analyze, generate_report

def run_benchmark():
    """
    Executa o benchmark completo comparando diferentes LLMs
    usando o dataset sintético de 50 exemplos.
    """
    print("🚀 Iniciando Benchmark de LLMs...")
    
    # 1. Carregar Dataset Sintético
    print("📦 Gerando dataset sintético...")
    dataset = gerar_dataset_sintetico()
    examples = dataset["categories"]
    
    # Preparar dicionário flat para o validate_batch
    # Estrutura: "Nome do Exemplo": "Código"
    batch_input = {}
    
    # Adiciona Excelentes
    for ex in examples["excellent"]:
        batch_input[f"[EXCELLENT] {ex['id']}"] = ex['code']
        
    # Adiciona Bons
    for ex in examples["good"]:
        batch_input[f"[GOOD] {ex['id']}"] = ex['code']
        
    # Adiciona Médios
    for ex in examples["medium"]:
        batch_input[f"[MEDIUM] {ex['id']}"] = ex['code']

    # Adiciona Ruins
    for ex in examples["poor"]:
        batch_input[f"[POOR] {ex['id']}"] = ex['code']
        
    print(f"📋 Total de casos de teste: {len(batch_input)}")
    
    # 2. Configurar Clientes
    clients = []
    
    # Gemini
    if SETTINGS.GOOGLE_API_KEY:
        clients.append({
            "name": "Gemini 2.5-flash",
            "client": GeminiClient(api_key=SETTINGS.GOOGLE_API_KEY, model_name="gemini-2.5-flash"),
            "file_suffix": "gemini"
        })
    else:
        print("⚠️ Gemini API Key não encontrada. Pulando...")

    # Mistral
    if SETTINGS.MISTRAL_API_KEY:
        clients.append({
            "name": "Mistral Small",
            "client": MistralClient(api_key=SETTINGS.MISTRAL_API_KEY, model_name="mistral-small-latest"),
            "file_suffix": "mistral"
        })
    else:
        print("⚠️ Mistral API Key não encontrada. Pulando...")
        
    # # OpenAI
    # if SETTINGS.OPENAI_API_KEY:
    #     clients.append({
    #         "name": "GPT-4.1-nano",
    #         "client": OpenAIClient(api_key=SETTINGS.OPENAI_API_KEY, model_name="gpt-4.1-nano"),
    #         "file_suffix": "openai"
    #     })
    # else:
    #     print("⚠️ OpenAI API Key não encontrada. Pulando...")

    if not clients:
        print("❌ Nenhum cliente LLM configurado. Abortando.")
        return

    # 3. Executar Validações
    results_summary = []

    for item in clients:
        llm_name = item["name"]
        client_instance = item["client"]
        suffix = item["file_suffix"]
        
        print(f"\n🤖 Executando validação com: {llm_name}...")
        start_time = time.time()
        
        # Instancia Validador com o cliente atual
        validator = FastAPICodeValidator(llm_client=client_instance, rules=RULES_STANDARD)
        
        # Executa Batch
        try:
            report = validator.validate_batch(batch_input, rate_limit_s=1.0)
            
            # RE-INJECT METADATA (Keywords)
            # Como o validator não retorna os metadados do input, precisamos mapear de volta
            # O validator retorna lista de resultados.
            # Precisamos iterar e encontrar o exemplo original pelo ID/File Path
            
            for result in report.get("results", []):
                file_id_tag = result.get("file_path", "") # Ex: [EXCELLENT] EXC_001
                # Tenta extrair ID "EXC_001"
                import re
                match = re.search(r" ([\w_]+)$", file_id_tag)
                if match:
                    ex_id = match.group(1)
                    # Busca nos exemplos originais
                    found_ex = None
                    for cat in examples:
                        for ex in examples[cat]:
                            if ex["id"] == ex_id:
                                found_ex = ex
                                break
                        if found_ex: break
                    
                    if found_ex:
                        result["expected_keywords"] = found_ex.get("expected_keywords", [])
                        result["expected_score_min"] = found_ex.get("expected_score_min")
                        result["expected_score_max"] = found_ex.get("expected_score_max")

                # INJECT CODE SNIPPET FROM INPUT
                if file_id_tag in batch_input:
                    result["code_snippet"] = batch_input[file_id_tag]

            # Adiciona metadados do benchmark ao relatório
            report["benchmark_metadata"] = {
                "llm_name": llm_name,
                "total_time": round(time.time() - start_time, 2),
                "dataset_version": dataset["metadata"]["version"]
            }
            
            # Salva resultado individual
            filename = f"benchmark_results_{suffix}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Concluído ({report['benchmark_metadata']['total_time']}s). Salvo em {filename}")
            
            results_summary.append({
                "llm": llm_name,
                "filename": filename,
                "stats": report["summary"]
            })
            
        except Exception as e:
            print(f"❌ Erro ao executar {llm_name}: {str(e)}")

    print("\n🏁 Benchmark Finalizado!")
    print(json.dumps(results_summary, indent=2, ensure_ascii=False))
    
    # Gera relatório com gráficos
    generate_charts_report(
            file_pattern="benchmark_results_*.json",
            output_file="benchmark_final_report.html",
        )

    # Gera relatório comparativo detalhado
    generate_comparison_report(
        file_pattern="benchmark_results_*.json",
        output_file="benchmark_comparison_report.html"
    )
    
    # Gera relatório estatístico
    analyze(results_summary)
    generate_report(results_summary)

if __name__ == "__main__":
    run_benchmark()
