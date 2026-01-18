import json
import glob
import statistics


def generate_charts_report(
    file_pattern: str, output_file: str = "benchmark_final_report.html"
):
    """
    Lê os arquivos de resultado do benchmark (padrão ou customizado)
    e gera um relatório HTML com tabelas comparativas e gráficos Chart.js.
    """

    report_context = "Dataset Sintético"
    if "repo_results" in file_pattern or "repos" in output_file:
        report_context = "Repositórios Reais"

    # 1. Carregar Resultados
    result_files = glob.glob(file_pattern)
    print(f"🔍 Pattern '{file_pattern}' found files: {result_files}")
    if not result_files:
        print(f"❌ Nenhum arquivo de resultado encontrado ({file_pattern}). Rode o benchmark.py primeiro.")
        return

    data_by_llm = {}

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
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

        stats.append(
            {
                "name": llm,
                "avg_score": round(statistics.mean(scores), 2) if scores else 0,
                "avg_time": round(statistics.mean(times), 2) if times else 0,
                "total_passed": passed,
                "total_warnings": warnings,
                "total_failed": failed,
                "total_errors": errors,
                "total": len(results),
                "raw_scores": scores,
                "raw_times": times,
            }
        )

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
            <p style="text-align:center">Comparação de performance na validação de código FastAPI • {report_context}</p>
            
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
                    {"".join(f"<tr><td>{s['name']}</td><td>{s['avg_score']}</td><td>{s['avg_time']}</td><td style='color:green'>{s['total_passed']}</td><td style='color:goldenrod'>{s['total_warnings']}</td><td style='color:orange'>{s['total_failed']}</td><td style='color:red'>{s['total_errors']}</td></tr>" for s in stats)}
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
            const models = {json.dumps([s["name"] for s in stats])};
            const scores = {json.dumps([s["avg_score"] for s in stats])};
            const times = {json.dumps([s["avg_time"] for s in stats])};
            const passed = {json.dumps([s["total_passed"] for s in stats])};
            const warnings = {json.dumps([s["total_warnings"] for s in stats])};
            const failed = {json.dumps([s["total_failed"] for s in stats])};
            const errors = {json.dumps([s["total_errors"] for s in stats])};

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

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"📊 Relatório Comparativo gerado com sucesso: {output_file}")


def generate_comparison_report(
    file_pattern: str, output_file: str = "benchmark_comparison_report.html"
):
    """
    Gera um relatório HTML detalhado comparando as respostas de cada LLM lado a lado para cada caso de teste.
    """
    result_files = glob.glob(file_pattern)
    if not result_files:
        print(f"❌ Nenhum arquivo encontrado para comparação ({file_pattern})")
        return

    # 1. Carregar dados
    data_by_llm = {}
    test_cases = {}  # Map: id -> {code: str, description: str, llm_results: {llm: result}}

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            llm_name = data.get("benchmark_metadata", {}).get("llm_name", "Unknown")
            data_by_llm[llm_name] = data
            
            for result in data.get("results", []):
                # Extrai ID do filename ou path
                # Ex: [EXCELLENT] EXC_001 -> id="EXC_001"
                file_id = result.get("file_path", "unknown")
                
                if file_id not in test_cases:
                    test_cases[file_id] = {
                        "id": file_id,
                        "code": result.get("code_snippet", ""), # Se não tiver snippet no result, vai ficar vazio por enquanto
                        "llm_results": {}
                    }
                
                # Se o codigo ainda estiver vazio, tenta preencher
                if not test_cases[file_id]["code"] and result.get("code_snippet"):
                    test_cases[file_id]["code"] = result.get("code_snippet")

                test_cases[file_id]["llm_results"][llm_name] = result

        except Exception as e:
            print(f"⚠️ Erro ao processar {file_path} para comparação: {e}")

    llm_names = list(data_by_llm.keys())

    # 2. Gerar HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Comparação Detalhada de LLMs</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f4f6f9; padding: 20px; }}
            .container {{ max-width: 95%; margin: 0 auto; }}
            .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
            .card-header {{ background: #34495e; color: white; padding: 15px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
            .card-content {{ padding: 20px; display: none; }}
            .comparison-grid {{ display: grid; grid-template-columns: 30% repeat({len(llm_names)}, 1fr); gap: 15px; }}
            .code-column {{ background: #272822; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; font-size: 0.85em; max-height: 500px; overflow-y: auto; }}
            .llm-column {{ border: 1px solid #ddd; border-radius: 5px; padding: 10px; background: #fff; }}
            .status-pass {{ color: green; font-weight: bold; }}
            .status-fail {{ color: red; font-weight: bold; }}
            .status-warning {{ color: orange; font-weight: bold; }}
            .violation-item {{ background: #fff3cd; padding: 5px; margin: 5px 0; border-left: 3px solid #ffc107; font-size: 0.9em; }}
            .violation-critical {{ background: #f8d7da; border-left: 3px solid #dc3545; }}
            .meta-info {{ font-size: 0.8em; color: #666; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        </style>
        <script>
            function toggleCard(id) {{
                var content = document.getElementById('content-' + id);
                if (content.style.display === 'block') {{
                    content.style.display = 'none';
                }} else {{
                    content.style.display = 'block';
                }}
            }}
            function expandAll() {{
                var contents = document.getElementsByClassName('card-content');
                for(var i=0; i<contents.length; i++) contents[i].style.display = 'block';
            }}
            function collapseAll() {{
                var contents = document.getElementsByClassName('card-content');
                for(var i=0; i<contents.length; i++) contents[i].style.display = 'none';
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Comparação Lado a Lado ({len(test_cases)} casos)</h1>
            <div style="margin-bottom: 20px;">
                <button onclick="expandAll()" style="padding: 10px; cursor: pointer;">Expandir Todos</button>
                <button onclick="collapseAll()" style="padding: 10px; cursor: pointer;">Recolher Todos</button>
            </div>
    """

    for case_id, case_data in sorted(test_cases.items()):
        # Tenta pegar descrição de algum resultado
        desc = "Sem descrição"
        for r in case_data["llm_results"].values():
            if r.get("metadata", {}).get("description"):
                desc = r.get("metadata", {}).get("description")
                break
        
        html += f"""
            <div class="card">
                <div class="card-header" onclick="toggleCard('{case_id}')">
                    <span><strong>{case_id}</strong>: {desc}</span>
                    <span>▼</span>
                </div>
                <div id="content-{case_id}" class="card-content">
                    <div class="comparison-grid">
                        <div class="code-column">{case_data['code'].replace('<', '&lt;').replace('>', '&gt;')}</div>
        """

        for llm in llm_names:
            res = case_data["llm_results"].get(llm)
            if not res:
                html += "<div class='llm-column'><em>N/A</em></div>"
                continue
            
            status_class = f"status-{res.get('overall_status', 'unknown')}"
            score = res.get('overall_score', res.get('score', 0))
            
            # Recall info
            recall_badges = ""
            expected_kws = res.get("expected_keywords") or res.get("metadata", {}).get("expected_keywords")
            if expected_kws:
                # Checa recall rapidinho aqui tbm para visualização
                full_text = (res.get("summary", "") + " " + " ".join([v.get("description","") for v in res.get("violations", [])])).lower()
                found_kws = [k for k in expected_kws if k.lower() in full_text]
                if found_kws:
                    recall_badges = f"<div style='margin-top:5px;'><span style='background:#d4edda; color:#155724; padding:2px 5px; border-radius:3px; font-size:0.8em'>✅ Recall: {', '.join(found_kws)}</span></div>"
                else:
                    recall_badges = f"<div style='margin-top:5px;'><span style='background:#f8d7da; color:#721c24; padding:2px 5px; border-radius:3px; font-size:0.8em'>❌ Missed: {', '.join(expected_kws)}</span></div>"

            html += f"""
                <div class="llm-column">
                    <div class="meta-info">
                        <strong>{llm}</strong><br>
                        Score: <strong>{score}</strong> | <span class="{status_class}">{res.get('overall_status')}</span>
                        <br>Tempo: {res.get('response_time', 0)}s
                        {recall_badges}
                    </div>
                    <div class="violations-list">
            """
            
            for v in res.get("violations", []):
                # Check critical
                is_crit = "critic" in v.get("category", "").lower() or "high" in v.get("severity", "").lower()
                cls = "violation-critical" if is_crit else "violation-item"
                html += f"<div class='{cls}'><strong>{v.get('category')}</strong>: {v.get('description')}</div>"
            
            if not res.get("violations"):
                html += "<div style='color:green; font-style:italic'>Nenhuma violação encontrada.</div>"

            html += """
                    </div>
                    <div style='margin-top:10px; font-size:0.85em; color:#555;'>
                        <strong>Resumo:</strong><br>
            """
            html += res.get("summary", "Sem resumo")[:300] + "..."
            html += """
                    </div>
                </div>
            """

        html += """
                    </div>
                </div>
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"📊 Relatório Detalhado gerado: {output_file}")


if __name__ == "__main__":
    generate_charts_report("benchmark_results_*.json")

