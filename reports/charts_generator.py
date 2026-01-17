import json
import glob
import statistics
from typing import List, Dict, Any

def generate_charts_report(file_pattern: str, output_file: str = "benchmark_final_report.html"):
    """
    Lê os arquivos de resultado do benchmark (padrão ou customizado)
    e gera um relatório HTML com tabelas comparativas e gráficos Chart.js.
    """
    
    # 1. Carregar Resultados
    result_files = glob.glob(file_pattern)
    print(f"🔍 Pattern '{file_pattern}' found files: {result_files}")
    if not result_files:
        print(f"❌ Nenhum arquivo de resultado encontrado ({file_pattern}). Rode o benchmark.py primeiro.")
        return

    data_by_llm = {}
    
    for file_path in result_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            llm_name = data.get("benchmark_metadata", {}).get("llm_name", "Unknown")
            # Caso o nome venha duplicado ou algo do tipo
            if llm_name in data_by_llm:
                llm_name = f"{llm_name} ({file_path})"
                
            data_by_llm[llm_name] = data
            print(f"📦 Carregado: {file_path} -> {llm_name}")
        except Exception as e:
            print(f"⚠️ Erro ao ler {file_path}: {e}")

    # 2. Processar Métricas
    stats = []
    
    for llm, report in data_by_llm.items():
        results = report.get("results", [])
        print(f"📊 Processando {llm}: {len(results)} resultados encontrados.")
        scores = [r.get("overall_score", r.get("score", 0)) for r in results]
        times = [
            r.get("response_time", r.get("_metadata", {}).get("response_time", 0))
            for r in results
        ]
        passed = sum(1 for r in results if r.get("overall_status") == "pass")
        warnings = sum(1 for r in results if r.get("overall_status") == "warning")
        failed = sum(1 for r in results if r.get("overall_status") == "fail")
        errors = sum(1 for r in results if "error" in r)
        
        # Acurácia (Simplificada: Score Médio vs Categoria Esperada)
        # Assumindo que o dataset sintético tem scores esperados.
        # Aqui vamos usar apenas a média geral para comparação.
        
        stats.append({
            "name": llm,
            "avg_score": round(statistics.mean(scores), 2) if scores else 0,
            "avg_time": round(statistics.mean(times), 2) if times else 0,
            "total_passed": passed,
            "total_warnings": warnings,
            "total_failed": failed,
            "total_errors": errors,
            "total": len(results),
            "raw_scores": scores,
            "raw_times": times
        })

    # 3. Gerar HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Benchmark LLM - Code Validator</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f8f9fa; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #2c3e50; }}
            .summary-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; }}
            .summary-table th, .summary-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            .summary-table th {{ background: #34495e; color: white; }}
            .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px; }}
            .chart-box {{ background: #fff; padding: 15px; border: 1px solid #eee; border-radius: 8px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #7f8c8d; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Relatório Comparativo de LLMs</h1>
            <p style="text-align:center">Comparação de performance na validação de código FastAPI</p>
            
            <!-- Tabela Estatística -->
            <h2>Estatísticas Gerais</h2>
            <table class="summary-table">
                <thead>
                    <tr>
                        <th>Modelo LLM</th>
                        <th>Score Médio</th>
                        <th>Tempo Médio (s)</th>
                        <th>Aprovados</th>
                        <th>Avisos</th>
                        <th>Reprovados</th>
                        <th>Erros API</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f"<tr><td>{s['name']}</td><td>{s['avg_score']}</td><td>{s['avg_time']}</td><td style='color:green'>{s['total_passed']}</td><td style='color:goldenrod'>{s['total_warnings']}</td><td style='color:orange'>{s['total_failed']}</td><td style='color:red'>{s['total_errors']}</td></tr>" for s in stats)}
                </tbody>
            </table>

            <!-- Gráficos -->
            <div class="charts-grid">
                <div class="chart-box">
                    <canvas id="scoreChart"></canvas>
                </div>
                <div class="chart-box">
                    <canvas id="timeChart"></canvas>
                </div>
                <div class="chart-box">
                    <canvas id="passRateChart"></canvas>
                </div>
                 <div class="chart-box">
                    <canvas id="errorChart"></canvas>
                </div>
            </div>

            <div class="footer">
                <p>Gerado automaticamente pelo Antigravity • {len(result_files)} datasets processados</p>
            </div>
        </div>

        <script>
            const models = {json.dumps([s['name'] for s in stats])};
            const scores = {json.dumps([s['avg_score'] for s in stats])};
            const times = {json.dumps([s['avg_time'] for s in stats])};
            const passed = {json.dumps([s['total_passed'] for s in stats])};
            const warnings = {json.dumps([s['total_warnings'] for s in stats])};
            const failed = {json.dumps([s['total_failed'] for s in stats])};
            const errors = {json.dumps([s['total_errors'] for s in stats])};

            // Gráfico de Scores
            new Chart(document.getElementById('scoreChart'), {{
                type: 'bar',
                data: {{
                    labels: models,
                    datasets: [{{
                        label: 'Score Médio (0-100)',
                        data: scores,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ title: {{ display: true, text: 'Qualidade Média da Avaliação (Score)' }} }},
                    scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
                }}
            }});

            // Gráfico de Tempo
            new Chart(document.getElementById('timeChart'), {{
                type: 'line',
                data: {{
                    labels: models,
                    datasets: [{{
                        label: 'Tempo Médio de Resposta (s)',
                        data: times,
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        borderColor: 'rgba(153, 102, 255, 1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ title: {{ display: true, text: 'Latência (Velocidade)' }} }},
                    scales: {{ y: {{ beginAtZero: true }} }}
                }}
            }});

            // Gráfico de Aprovação (Empilhado)
            new Chart(document.getElementById('passRateChart'), {{
                type: 'bar',
                data: {{
                    labels: models,
                    datasets: [
                        {{
                            label: 'Aprovados',
                            data: passed,
                            backgroundColor: '#2ecc71',
                        }},
                        {{
                            label: 'Avisos',
                            data: warnings,
                            backgroundColor: '#f39c12',
                        }},
                        {{
                            label: 'Reprovados',
                            data: failed,
                            backgroundColor: '#f1c40f',
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ title: {{ display: true, text: 'Consistência de Validação' }} }},
                    scales: {{ x: {{ stacked: true }}, y: {{ stacked: true }} }}
                }}
            }});
            
             // Gráfico de Erros
            new Chart(document.getElementById('errorChart'), {{
                type: 'doughnut',
                data: {{
                    labels: models,
                    datasets: [{{
                        label: 'Erros de API',
                        data: errors,
                        backgroundColor: ['#e74c3c', '#c0392b', '#922b21'],
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ title: {{ display: true, text: 'Erros de Execução' }} }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📊 Relatório Comparativo gerado com sucesso: {output_file}")

if __name__ == "__main__":
    generate_charts_report()
