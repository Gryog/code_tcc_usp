from client import llmclient
import prompt
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
        return prompt.VALIDATION_PROMPT_TEMPLATE.format(
            rules_text=rules_str,
            code=code
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
            result_dict['_metadata'] = {
                'response_time': round(time.time() - start_time, 2),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            return result_dict

        except ValidationError as e:
            return {"error": "O modelo retornou um JSON com schema inválido", "details": str(e), "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}}
        except Exception as e:
            return {"error": "Erro sistêmico na validação", "details": str(e), "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}}

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Valida um arquivo específico."""
        if not os.path.exists(file_path):
             return {"error": f"Arquivo não encontrado: {file_path}", "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = self.validate(code)
            result['file_path'] = file_path
            return result
        except Exception as e:
            return {"error": f"Erro ao ler arquivo: {str(e)}", "file_path": file_path, "_metadata": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}}

    def validate_project(self, root_path: str, ignore_folders: list = None) -> Dict[str, Any]:
        """
        Varre um diretório recursivamente e valida arquivos Python.
        """
        if ignore_folders is None:
            ignore_folders = ['.venv', '.git', '__pycache__', 'venv', 'env']

        results = []
        overall_stats = {"passed": 0, "failed": 0, "errors": 0}

        for root, dirs, files in os.walk(root_path):
            # Filtra diretórios ignorados
            dirs[:] = [d for d in dirs if d not in ignore_folders]

            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    print(f"🔍 Analisando: {full_path}...")
                    
                    file_result = self.validate_file(full_path)
                    
                    # Atualiza estatísticas
                    if "error" in file_result:
                        overall_stats["errors"] += 1
                        print(f"   ❌ Erro: {file_result['error']}")
                    elif file_result.get("overall_status") == "fail":
                        overall_stats["failed"] += 1
                        print(f"   ⚠️  Issues found (Score: {file_result.get('overall_score')})")
                    else:
                        overall_stats["passed"] += 1
                        print(f"   ✅ OK (Score: {file_result.get('overall_score')})")
                    
                    results.append(file_result)
        
        return {
            "summary": overall_stats,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def validate_batch(self, codes: Dict[str, str]) -> Dict[str, Any]:
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
            result['file_path'] = name # Usa o nome como "caminho"
            
            # Atualiza estatísticas
            if "error" in result:
                overall_stats["errors"] += 1
                error_detail = result.get('details', 'Sem detalhes')
                print(f"   ❌ Erro: {result['error']} - Detalhes: {error_detail}")
            elif result.get("overall_status") == "fail":
                overall_stats["failed"] += 1
                print(f"   ⚠️  Issues found (Score: {result.get('overall_score')})")
            else:
                overall_stats["passed"] += 1
                print(f"   ✅ OK (Score: {result.get('overall_score')})")
            
            results.append(result)
        
        return {
            "summary": overall_stats,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _normalize_report(self, report: Dict) -> Dict:
        """
        Normaliza o relatório para garantir formato padrão.
        Se receber um resultado único, envolve em uma estrutura de lista.
        """
        if "results" in report:
            return report
        
        # Constrói wrapper para resultado único
        is_error = "error" in report
        is_fail = report.get("overall_status") == "fail"
        
        summary = {
            "passed": 0 if (is_error or is_fail) else 1,
            "failed": 1 if (not is_error and is_fail) else 0,
            "errors": 1 if is_error else 0
        }
        
        return {
            "summary": summary,
            "results": [report],
            "timestamp": report.get("_metadata", {}).get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
        }

    def save_report_json(self, report: Dict, path: str):
        """Salva o relatório em JSON."""
        normalized = self._normalize_report(report)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(normalized, f, indent=2, ensure_ascii=False)
        print(f"💾 Relatório JSON salvo em: {path}")

    def save_report_html(self, report: Dict, path: str):
        """Gera um relatório HTML moderno e estilizado."""
        report = self._normalize_report(report)
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório de Auditoria FastAPI</title>
            <style>
                :root {{
                    --bg-color: #0f172a;
                    --text-color: #e2e8f0;
                    --card-bg: #1e293b;
                    --border-color: #334155;
                    --success: #22c55e;
                    --warning: #eab308;
                    --error: #ef4444;
                    --info: #3b82f6;
                }}
                body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; line-height: 1.5; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                h1 {{ font-size: 2rem; margin-bottom: 10px; background: linear-gradient(to right, #60a5fa, #a855f7); -webkit-background-clip: text; color: transparent; }}
                .header {{ margin-bottom: 30px; border-bottom: 1px solid var(--border-color); padding-bottom: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
                .stat-card {{ background: var(--card-bg); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); text-align: center; }}
                .stat-value {{ font-size: 2.5rem; font-weight: bold; display: block; }}
                .stat-label {{ font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
                .file-card {{ background: var(--card-bg); border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 15px; overflow: hidden; }}
                .file-header {{ padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; background: rgba(255,255,255,0.02); }}
                .file-header:hover {{ background: rgba(255,255,255,0.05); }}
                .file-name {{ font-weight: 600; font-family: monospace; }}
                .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }}
                .badge-pass {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
                .badge-fail {{ background: rgba(239, 68, 68, 0.2); color: var(--error); }}
                .file-content {{ padding: 0 20px 20px 20px; display: none; }}
                .file-card.open .file-content {{ display: block; }}
                .violation {{ margin-top: 15px; padding: 10px; border-left: 3px solid; background: rgba(0,0,0,0.2); border-radius: 0 4px 4px 0; }}
                .v-error {{ border-color: var(--error); }}
                .v-warning {{ border-color: var(--warning); }}
                .v-info {{ border-color: var(--info); }}
                .v-title {{ font-weight: bold; display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }}
                .v-suggestion {{ margin-top: 5px; font-size: 0.9rem; color: #94a3b8; font-style: italic; }}
                .footer {{ margin-top: 50px; text-align: center; color: #64748b; font-size: 0.8rem; }}
            </style>
            <script>
                function toggle(id) {{
                    document.getElementById(id).classList.toggle('open');
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Code Validator Report</h1>
                    <p>Gerado em: {report.get('timestamp')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <span class="stat-value" style="color: var(--success)">{report.get('summary', {}).get('passed', 0)}</span>
                        <span class="stat-label">Arquivos Aprovados</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value" style="color: var(--error)">{report.get('summary', {}).get('failed', 0)}</span>
                        <span class="stat-label">Arquivos Reprovados</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value" style="color: var(--warning)">{report.get('summary', {}).get('errors', 0)}</span>
                        <span class="stat-label">Erros de Leitura</span>
                    </div>
                </div>

                <h2>Detalhes da Análise</h2>
        """
        
        for i, file_res in enumerate(report.get('results', [])):
            card_id = f"file-{i}"
            score = file_res.get('overall_score', 0)
            status = file_res.get('overall_status', 'fail')
            badge_class = "badge-pass" if status == 'pass' else "badge-fail"
            
            html_content += f"""
            <div id="{card_id}" class="file-card">
                <div class="file-header" onclick="toggle('{card_id}')">
                    <span class="file-name">{file_res.get('file_path')}</span>
                    <div>
                        <span style="margin-right: 15px; color: #94a3b8;">Score: {score}/100</span>
                        <span class="badge {badge_class}">{status.upper()}</span>
                    </div>
                </div>
                <div class="file-content">
                    <p style="color: #cbd5e1; margin-top: 15px;"><em>{file_res.get('summary')}</em></p>
            """
            
            if "error" in file_res:
                 html_content += f"<div class='violation v-error'><strong>❌ Erro Fatal:</strong> {file_res['error']}</div>"
            
            for v in file_res.get('violations', []):
                sev = v.get('severity', 'error')
                icon = "🔴" if sev == 'error' else "🟡" if sev == 'warning' else "🔵"
                html_content += f"""
                    <div class="violation v-{sev}">
                        <div class="v-title">{icon} [{v['rule_category']}] {v['description']}</div>
                        <div class="v-suggestion">💡 Sugestão: {v['suggestion']}</div>
                    </div>
                """
                
            html_content += """
                </div>
            </div>
            """

        html_content += """
            <div class="footer">Gerado por Antigravity Code Validator</div>
            </div>
        </body>
        </html>
        """
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 Relatório HTML salvo em: {path}")

    def print_report_console(self, report: Dict):
        """Imprime o relatório no console usando Rich."""
        report = self._normalize_report(report)
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        console = Console()
        
        # Header
        console.print()
        console.print(Panel.fit("[bold cyan]🛡️  FastAPI Code Validator Relatório[/bold cyan]", border_style="cyan"))
        console.print(f"[dim]Data: {report.get('timestamp')}[/dim]\n")

        # Stat Summary
        summary = report.get("summary", {})
        grid_table = Table.grid(expand=True)
        grid_table.add_column(justify="center")
        grid_table.add_column(justify="center")
        grid_table.add_column(justify="center")
        
        grid_table.add_row(
            f"[green bold]{summary.get('passed', 0)}[/green bold] Aprovados",
            f"[red bold]{summary.get('failed', 0)}[/red bold] Reprovados",
            f"[yellow bold]{summary.get('errors', 0)}[/yellow bold] Erros",
        )
        console.print(Panel(grid_table, title="Resumo", border_style="grey50"))
        console.print()

        # Detalhes
        table = Table(title="Detalhamento por Arquivo", box=box.ROUNDED, header_style="bold magenta")
        table.add_column("Arquivo", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Violações", justify="right")

        for res in report.get("results", []):
            fname = res.get("file_path", "N/A").split("\\")[-1].split("/")[-1] # Simplifica nome
            score = res.get("overall_score", 0)
            status = res.get("overall_status", "fail")
            
            status_style = "[green]PASS[/green]" if status == "pass" else "[red]FAIL[/red]"
            if "error" in res: status_style = "[bold red]ERROR[/bold red]"
            
            violations_count = len(res.get("violations", []))
            v_style = "[dim]-[/dim]" if violations_count == 0 else f"[red]{violations_count}[/red]"

            table.add_row(fname, str(score), status_style, v_style)

        console.print(table)
        console.print("\n[dim]Para detalhes completos, verifique validation_report.html[/dim]\n")