import os
import glob
import json
from benchmark_repos import run_repo_benchmark
from benchmark_synthetic import run_benchmark
from reports.statistic_report_generator import ResultsAnalyzer

def consolidate_synthetic_results():
    print("\n📊 Consolidating Synthetic Results for Average Report...")
    syn_files = glob.glob("results/sinteticos/synthetic_results_*.json")
    
    merged_results = {} # {"Gemini 2.5-flash": [result1, result2, ...]}
    
    for fpath in syn_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                llm = data.get("benchmark_metadata", {}).get("llm_name", "Unknown")
                results = data.get("results", [])
                
                # Check if this is a "run" file (avoid double counting if we have other files)
                # But actually we want to aggregate everything found.
                if llm not in merged_results:
                    merged_results[llm] = []
                merged_results[llm].extend(results)
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            
    for llm, results in merged_results.items():
        print(f"\n📈 Averaged Stats for {llm} (Synthetic) - Total samples: {len(results)}")
        analyzer = ResultsAnalyzer(results)
        stats = analyzer.analyze()
        report_content = analyzer.generate_report()
        
        s_name = llm.replace(" ", "_").lower()
        save_path = f"results/sinteticos/AVERAGE_report_{s_name}.txt"
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"✅ Saved Average Report: {save_path}")

def consolidate_repo_results():
    print("\n📊 Consolidating Repo Results for Average Report...")
    repo_files = glob.glob("results/repositorios/repo_results_*.json")
    
    # Key: "LLM Name | Repo Name"
    merged_results = {} 
    
    for fpath in repo_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                llm = data.get("benchmark_metadata", {}).get("llm_name", "Unknown")
                repo = data.get("benchmark_metadata", {}).get("repo_name", "Unknown")
                key = f"{llm}___{repo}"
                
                results = data.get("results", [])
                if key not in merged_results:
                    merged_results[key] = []
                merged_results[key].extend(results)
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

    for key, results in merged_results.items():
        llm, repo = key.split("___")
        print(f"\n📈 Averaged Stats for {llm} on {repo} - Total samples: {len(results)}")
        analyzer = ResultsAnalyzer(results)
        stats = analyzer.analyze()
        report_content = analyzer.generate_report()
        
        s_name = f"{llm}_{repo}".replace(" ", "_").lower()
        save_path = f"results/repositorios/AVERAGE_report_{s_name}.txt"
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"✅ Saved Average Report: {save_path}")

def main():
    NUM_RUNS = 5
    print(f"🔄 Starting Batch Execution: {NUM_RUNS} runs.")

    for i in range(1, NUM_RUNS + 1):
        print(f"\n==========================================")
        print(f"🔁 EXECUTION RUN {i}/{NUM_RUNS}")
        print(f"==========================================")
        
        # 1. Synthetic
        try:
            run_benchmark(run_id=i, skip_reporting=True)
        except Exception as e:
            print(f"❌ Error in synthetic run {i}: {e}")
        
        # 2. Repos
        try:
            run_repo_benchmark(run_id=i, skip_reporting=True)
        except Exception as e:
            print(f"❌ Error in repo run {i}: {e}")

    print("\n✅ Batch Execution Completed.")
    
    # Consolidate
    consolidate_synthetic_results()
    consolidate_repo_results()

if __name__ == "__main__":
    main()
