import os
import glob
from reports.statistic_report_generator import analyze, generate_report

def generate_final():
    print("📊 Generating Consolidated Report from saved results...")
    
    # Encontrar todos os arquivos de resultado de repositórios
    pattern = "repo_results_*.json"
    files = glob.glob(pattern)
    
    if not files:
        print("❌ No result files found.")
        return

    results_summary = []
    
    for filename in files:
        # Nome do arquivo ex: repo_results_gemini_fastapi-nano.json
        # Extrair info
        parts = filename.replace("repo_results_", "").replace(".json", "").split("_", 1)
        suffix = parts[0]
        repo_name = parts[1] if len(parts) > 1 else "unknown"
        
        # Mapear suffix para Nome LLM (aproximado)
        llm_name = {
            "gemini": "Gemini 2.5-flash",
            "mistral": "Mistral Small",
            "openai": "GPT-4.1-nano"
        }.get(suffix, suffix.capitalize())
        
        print(f"  found: {filename} (LLM: {llm_name}, Repo: {repo_name})")
        
        results_summary.append({
            "llm": f"{llm_name} ({repo_name})",
            "filename": filename,
            "repo": repo_name
        })
        
    # Gerar
    try:
        analyze(results_summary)
        generate_report(results_summary)
        print("✅ Reports generated successfully!")
        print("   - check benchmark_final_stats.txt")
        print("   - check benchmark_final_report.html")
    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_final()
