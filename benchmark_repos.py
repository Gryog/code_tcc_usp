import os
import json
import time
from typing import List, Dict, Any
from config.config import settings as SETTINGS
from validator.validator import FastAPICodeValidator
from client.geminiclient import GeminiClient
from client.mistralclient import MistralClient
from client.openaiclient import OpenAIClient
from config.rules import RULES_STANDARD
from reports.charts_generator import generate_charts_report
from reports.statistic_report_generator import analyze, generate_report
from extraction.repo_collector import RepoCollector
from extraction.teste_colletor import TesteRepoCollector

def run_repo_benchmark():
    """
    Executa benchmark em repositórios reais do GitHub.
    """
    print("🚀 Iniciando Benchmark de Repositórios Reais...")
    
    # 1. Configurar Repositórios Alvo
    repos = [
        "https://github.com/rednafi/fastapi-nano",
        "https://github.com/nsidnev/fastapi-realworld-example-app",
        #"https://github.com/tiangolo/full-stack-fastapi-template" # Muito grande/complexo para este teste rápido, descomentar se necessário
    ]
    
    # 2. Configurar Clientes LLM
    clients = []
    
    if SETTINGS.GOOGLE_API_KEY:
        clients.append({
            "name": "Gemini 2.5-flash",
            "client": GeminiClient(api_key=SETTINGS.GOOGLE_API_KEY, model_name="gemini-2.5-flash"),
            "file_suffix": "gemini"
        })
        
    if SETTINGS.MISTRAL_API_KEY:
        clients.append({
            "name": "Mistral Small",
            "client": MistralClient(api_key=SETTINGS.MISTRAL_API_KEY, model_name="mistral-small-latest"),
            "file_suffix": "mistral"
        })
        
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
    for repo_url in repos:
        collector = TesteRepoCollector(repo_url)
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
        endpoint_codes = { ep['id']: ep['code'] for ep in endpoints }
        
        # Iterar sobre Clientes para este Repositório
        for item in clients:
            llm_name = item["name"]
            client_instance = item["client"]
            suffix = item["file_suffix"]
            
            # Check if result already exists
            filename = f"repo_results_{suffix}_{collector.repo_name}.json"
            if os.path.exists(filename):
                print(f"  ⏭️  Skipping {llm_name} for {collector.repo_name} (Result exists: {filename})")
                results_summary.append({
                    "llm": f"{llm_name} ({collector.repo_name})",
                    "filename": filename,
                    "repo": collector.repo_name
                })
                continue
            
            print(f"  🤖 Validando {len(endpoints)} endpoints com {llm_name}...")
            start_time = time.time()
            
            # Validador
            validator = FastAPICodeValidator(llm_client=client_instance, rules=RULES_STANDARD)
            
            # Executa validação em batch nos endpoints extraídos
            try:
                report = validator.validate_batch(endpoint_codes)
                
                # Adiciona metadados extras aos resultados 
                # (validate_batch usa o ID como file_path, vamos enriquecer se precisar)
                for res in report.get("results", []):
                    ep_id = res.get("file_path")
                    # Encontra o endpoint original para pegar mais metadados se quiser
                    orig_ep = next((e for e in endpoints if e['id'] == ep_id), None)
                    if orig_ep:
                        res["metadata"] = {**res.get("metadata", {}), **orig_ep["metadata"]}
                        res["source_file"] = orig_ep["source"]

                # Metadados do Benchmark
                report["benchmark_metadata"] = {
                    "llm_name": llm_name,
                    "repo_name": collector.repo_name,
                    "repo_url": repo_url,
                    "total_time": round(time.time() - start_time, 2),
                    "total_endpoints": len(endpoints)
                }
                
                # Salvar resultado
                filename = f"repo_results_{suffix}_{collector.repo_name}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Concluído ({report['benchmark_metadata']['total_time']}s). Salvo: {filename}")
                
                results_summary.append({
                    "llm": f"{llm_name} ({collector.repo_name})",
                    "filename": filename,
                    "repo": collector.repo_name
                })
                
            except Exception as e:
                print(f"❌ Erro ao validar com {llm_name}: {e}")
        
        # Limpeza após todos os LLMs rodarem neste repo
        collector.cleanup()

    print("\n🏁 Benchmark de Repositórios Finalizado!")
    
    # Gera relatórios finais (Reaproveitando geradores existentes)
    # Nota: generate_charts_report pode precisar de ajuste se esperar estrutura exata do benchmark sintético,
    # mas vamos tentar usar. Para análise estatística funciona.
    
    print("\n📊 Gerando Relatórios Consolidados...")
    try:
        analyze(results_summary)
        generate_report(results_summary)
        generate_charts_report(file_pattern="repo_results_*.json", output_file="benchmark_repos_report.html")
    except Exception as e:
        print(f"⚠️ Erro na geração de relatório final: {e}")

if __name__ == "__main__":
    run_repo_benchmark()
