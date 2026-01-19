import json
import glob
import re
import statistics

def _calculate_status_metrics(results):
    labels = ("pass", "warning", "fail")
    confusion = {label: {l: 0 for l in labels} for label in labels}
    total = 0

    for result in results:
        expected = result.get("expected_status")
        if not expected:
            expected_category = result.get("expected_category")
            if expected_category:
                category = expected_category.lower()
                if category in ("excellent", "good"):
                    expected = "pass"
                elif category == "medium":
                    expected = "warning"
                elif category == "poor":
                    expected = "fail"
        if not expected:
            file_path = result.get("file_path", "")
            match = re.search(r"\[(\w+)\]", file_path)
            if match:
                category = match.group(1).lower()
                if category in ("excellent", "good"):
                    expected = "pass"
                elif category == "medium":
                    expected = "warning"
                elif category == "poor":
                    expected = "fail"
        predicted = result.get("overall_status")
        if expected not in labels or predicted not in labels:
            continue
        confusion[expected][predicted] += 1
        total += 1

    per_label = {}
    correct = 0
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in labels if other != label)
        fn = sum(confusion[label][other] for other in labels if other != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
        per_label[label] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
        correct += tp

    accuracy = (correct / total) if total > 0 else 0
    labels_with_support = [label for label in labels if per_label[label]["support"] > 0]
    macro_f1 = (
        sum(per_label[label]["f1"] for label in labels_with_support) / len(labels_with_support)
        if labels_with_support
        else 0
    )
    weighted_f1 = 0
    for label in labels:
        support = per_label[label]["support"]
        if total > 0 and support > 0:
            weighted_f1 += per_label[label]["f1"] * (support / total)

    return {
        "total": total,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "confusion": confusion,
    }


def _format_percent(value, enabled=True):
    if not enabled:
        return "N/A"
    return f"{round(value * 100, 2)}%"


def _calculate_keyword_metrics(results):
    keyword_pool = set()
    total_expected_keywords = 0
    for result in results:
        expected_keywords = result.get("expected_keywords") or result.get("metadata", {}).get(
            "expected_keywords"
        )
        if expected_keywords:
            keyword_pool.update(k.lower() for k in expected_keywords)
            total_expected_keywords += len(expected_keywords)

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_examples = 0
    total_results = len(results)

    for result in results:
        expected_keywords = result.get("expected_keywords") or result.get("metadata", {}).get(
            "expected_keywords"
        )
        if not expected_keywords:
            continue

        total_examples += 1
        expected_set = {k.lower() for k in expected_keywords}

        llm_texts = []
        for v in result.get("violations", []):
            llm_texts.append(v.get("description", "").lower())
            llm_texts.append(v.get("suggestion", "").lower())
        llm_texts.append(result.get("summary", "").lower())
        full_text = " ".join(llm_texts)

        predicted_set = {k for k in keyword_pool if k in full_text}

        total_tp += len(expected_set & predicted_set)
        total_fp += len(predicted_set - expected_set)
        total_fn += len(expected_set - predicted_set)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    return {
        "total_examples": total_examples,
        "coverage": (total_examples / total_results) if total_results > 0 else 0,
        "avg_keywords": (total_expected_keywords / total_examples) if total_examples > 0 else 0,
        "unique_keywords": len(keyword_pool),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

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

        status_metrics = _calculate_status_metrics(results)
        keyword_metrics = _calculate_keyword_metrics(results)

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
                "status_metrics": status_metrics,
                "keyword_metrics": keyword_metrics,
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
                        <th>Status Accuracy</th>
                        <th>Status Macro F1</th>
                        <th>Keyword F1</th>
                        <th>Keyword Cobertura</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(
                        f"<tr><td>{s['name']}</td><td>{s['avg_score']}</td><td>{s['avg_time']}</td>"
                        f"<td style='color:green'>{s['total_passed']}</td>"
                        f"<td style='color:goldenrod'>{s['total_warnings']}</td>"
                        f"<td style='color:orange'>{s['total_failed']}</td>"
                        f"<td style='color:red'>{s['total_errors']}</td>"
                        f"<td>{_format_percent(s['status_metrics']['accuracy'], s['status_metrics']['total'] > 0)}</td>"
                        f"<td>{_format_percent(s['status_metrics']['macro_f1'], s['status_metrics']['total'] > 0)}</td>"
                        f"<td>{_format_percent(s['keyword_metrics']['f1'], s['keyword_metrics']['total_examples'] > 0)}</td>"
                        f"<td>{_format_percent(s['keyword_metrics']['coverage'], s['keyword_metrics']['total_examples'] > 0)}</td></tr>"
                        for s in stats
                    )}
                </tbody>
            </table>

            <h2>Detalhes de Status e Keywords</h2>
            {"".join(
                f"<div class='chart-box' style='margin-bottom:20px;'>"
                f"<h3>{s['name']}</h3>"
                f"<p><strong>Status:</strong> Accuracy {_format_percent(s['status_metrics']['accuracy'], s['status_metrics']['total'] > 0)} | Macro F1 {_format_percent(s['status_metrics']['macro_f1'], s['status_metrics']['total'] > 0)} | Weighted F1 {_format_percent(s['status_metrics']['weighted_f1'], s['status_metrics']['total'] > 0)}</p>"
                f"<p><strong>Keywords:</strong> F1 {_format_percent(s['keyword_metrics']['f1'], s['keyword_metrics']['total_examples'] > 0)} | Cobertura {_format_percent(s['keyword_metrics']['coverage'], s['keyword_metrics']['total_examples'] > 0)} | Keywords únicas {s['keyword_metrics']['unique_keywords']} | Média keywords/exemplo {round(s['keyword_metrics']['avg_keywords'], 2)}</p>"
                f"</div>"
                for s in stats
            )}


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
                rule_cat = v.get("rule_category", v.get("category", "Geral"))
                is_crit = "critic" in rule_cat.lower() or "high" in v.get("severity", "").lower() or "error" in v.get("severity", "").lower()
                cls = "violation-critical" if is_crit else "violation-item"
                html += f"<div class='{cls}'><strong>{rule_cat}</strong>: {v.get('description')}</div>"
            
            if not res.get("violations"):
                html += "<div style='color:green; font-style:italic'>Nenhuma violação encontrada.</div>"

            html += """
                    </div>
                    <div style='margin-top:10px; font-size:0.85em; color:#555;'>
                        <strong>Resumo:</strong><br>
            """
            html += res.get("summary", "Sem resumo")[:500] + "..."
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

