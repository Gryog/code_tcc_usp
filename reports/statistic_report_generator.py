# ============================================================================
# PARTE 3: ANÁLISE ESTATÍSTICA DOS RESULTADOS
# ============================================================================
import json
import statistics
from pathlib import Path
from typing import List, Dict, Any

class ResultsAnalyzer:
    """
    Analisa resultados de validação e gera estatísticas detalhadas.
    """
    
    def __init__(self, results: List[Dict[str, Any]]):
        """
        Args:
            results: Lista de resultados de validação
        """
        self.results = results
        self.stats = {}
    
    def analyze(self) -> Dict[str, Any]:
        """
        Executa análise completa dos resultados.
        
        Returns:
            Dicionário com todas as estatísticas
        """
        self.stats = {
            "geral": self._analyze_general(),
            "por_categoria": self._analyze_by_category(),
            "performance": self._analyze_performance(),
            "violacoes": self._analyze_violations(),
            "acuracia": self._calculate_accuracy(),
            "distribuicao_scores": self._score_distribution()
        }
        
        return self.stats
    
    def _analyze_general(self) -> Dict:
        """Estatísticas gerais."""
        scores = [
            r.get('overall_score', r.get('score', 0))
            for r in self.results
            if 'overall_score' in r or 'score' in r
        ]
        
        return {
            "total_exemplos": len(self.results),
            "score_medio": round(statistics.mean(scores), 2) if scores else 0,
            "score_mediano": round(statistics.median(scores), 2) if scores else 0,
            "desvio_padrao": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
            "score_minimo": min(scores) if scores else 0,
            "score_maximo": max(scores) if scores else 0
        }
    
    def _analyze_by_category(self) -> Dict:
        """Análise por categoria."""
        categories = {}
        
        for result in self.results:
            cat = result.get('expected_category', result.get('category'))
            if not cat and 'file_path' in result:
                # Tentativa de extrair do nome do arquivo [CATEGORY] ...
                import re
                match = re.search(r'\[(\w+)\]', result['file_path'])
                if match:
                    cat = match.group(1).lower()
            
            if not cat:
                cat = 'unknown'

            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result.get('overall_score', result.get('score', 0)))
        
        analysis = {}
        for cat, scores in categories.items():
            analysis[cat] = {
                "quantidade": len(scores),
                "score_medio": round(statistics.mean(scores), 2) if scores else 0,
                "score_min": min(scores) if scores else 0,
                "score_max": max(scores) if scores else 0
            }
        
        return analysis
    
    def _analyze_performance(self) -> Dict:
        """Análise de performance (tempo de resposta)."""
        times = [
            r.get('response_time', r.get('_metadata', {}).get('response_time', 0))
            for r in self.results
            if 'response_time' in r or '_metadata' in r
        ]
        times = [t for t in times if t > 0]  # Remove zeros
        
        return {
            "tempo_medio": round(statistics.mean(times), 2) if times else 0,
            "tempo_mediano": round(statistics.median(times), 2) if times else 0,
            "tempo_minimo": round(min(times), 2) if times else 0,
            "tempo_maximo": round(max(times), 2) if times else 0,
            "desvio_padrao": round(statistics.stdev(times), 2) if len(times) > 1 else 0
        }
    
    def _analyze_violations(self) -> Dict:
        """Análise de violações encontradas."""
        total_violations = sum(len(r.get('violations', [])) for r in self.results)
        
        status_count = {}
        for result in self.results:
            status = result.get('overall_status', result.get('status', 'unknown'))
            status_count[status] = status_count.get(status, 0) + 1
        
        return {
            "total_violacoes": total_violations,
            "media_por_exemplo": round(total_violations / len(self.results), 2) if self.results else 0,
            "por_status": status_count
        }
    
    def _calculate_accuracy(self) -> Dict:
        """Calcula acurácia comparando score esperado vs obtido."""
        correct = 0
        total = 0
        
        for result in self.results:
            if 'expected_score_min' in result and 'expected_score_max' in result:
                score = result.get('overall_score', result.get('score', 0))
                min_expected = result['expected_score_min']
                max_expected = result['expected_score_max']
                
                if min_expected <= score <= max_expected:
                    correct += 1
                total += 1
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return {
            "exemplos_com_expectativa": total,
            "predicoes_corretas": correct,
            "predicoes_incorretas": total - correct,
            "acuracia_percentual": round(accuracy, 2),
            "taxa_erro": round(100 - accuracy, 2)
        }
    
    def _score_distribution(self) -> Dict:
        """Distribuição de scores por faixas."""
        scores = [r.get('overall_score', r.get('score', 0)) for r in self.results]
        
        distribution = {
            "0-20": sum(1 for s in scores if 0 <= s < 20),
            "20-40": sum(1 for s in scores if 20 <= s < 40),
            "40-60": sum(1 for s in scores if 40 <= s < 60),
            "60-80": sum(1 for s in scores if 60 <= s < 80),
            "80-100": sum(1 for s in scores if 80 <= s <= 100)
        }
        
        return distribution
    
    def generate_report(self, save_path: str = None) -> str:
        """
        Gera relatório textual das estatísticas.
        
        Args:
            save_path: Se fornecido, salva relatório em arquivo
        
        Returns:
            String com relatório formatado
        """
        if not self.stats:
            self.analyze()
        
        report = []
        report.append("=" * 70)
        report.append("📊 RELATÓRIO ESTATÍSTICO DE VALIDAÇÃO")
        report.append("=" * 70)
        report.append("")
        
        # Geral
        report.append("📈 ESTATÍSTICAS GERAIS:")
        geral = self.stats['geral']
        report.append(f"  Total de exemplos: {geral['total_exemplos']}")
        report.append(f"  Score médio: {geral['score_medio']}/100")
        report.append(f"  Score mediano: {geral['score_mediano']}/100")
        report.append(f"  Desvio padrão: {geral['desvio_padrao']}")
        report.append(f"  Range: {geral['score_minimo']} - {geral['score_maximo']}")
        report.append("")
        
        # Por categoria
        report.append("📂 POR CATEGORIA:")
        for cat, data in self.stats['por_categoria'].items():
            report.append(f"  {cat.upper()}:")
            report.append(f"    Quantidade: {data['quantidade']}")
            report.append(f"    Score médio: {data['score_medio']}/100")
            report.append(f"    Range: {data['score_min']} - {data['score_max']}")
        report.append("")
        
        # Performance
        report.append("⏱️  PERFORMANCE:")
        perf = self.stats['performance']
        report.append(f"  Tempo médio: {perf['tempo_medio']}s")
        report.append(f"  Tempo mediano: {perf['tempo_mediano']}s")
        report.append(f"  Range: {perf['tempo_minimo']}s - {perf['tempo_maximo']}s")
        report.append("")
        
        # Violações
        report.append("⚠️  VIOLAÇÕES:")
        viol = self.stats['violacoes']
        report.append(f"  Total: {viol['total_violacoes']}")
        report.append(f"  Média por exemplo: {viol['media_por_exemplo']}")
        report.append("  Por status:")
        for status, count in viol['por_status'].items():
            report.append(f"    {status}: {count}")
        report.append("")
        
        # Acurácia
        report.append("🎯 ACURÁCIA:")
        acc = self.stats['acuracia']
        report.append(f"  Exemplos com expectativa: {acc['exemplos_com_expectativa']}")
        report.append(f"  Predições corretas: {acc['predicoes_corretas']}")
        report.append(f"  Predições incorretas: {acc['predicoes_incorretas']}")
        report.append(f"  Acurácia percentual: {acc['acuracia_percentual']}%")
        report.append(f"  Taxa de erro: {acc['taxa_erro']}%")
        report.append("")
        
        # Distribuição de scores
        report.append("📊 DISTRIBUIÇÃO DE SCORES:")
        dist = self.stats['distribuicao_scores']
        for faixa, count in dist.items():
            report.append(f"  {faixa}: {count}")
        report.append("")
        
        # Salvar relatório
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report))
        
        return '\n'.join(report)

def analyze(results_summary: List[Dict[str, Any]]) -> None:
    """
    Função auxiliar para analisar uma lista de sumários de benchmark.
    Carrega os arquivos JSON detalhados e executa o ResultsAnalyzer para cada um.
    """
    print("\n🔍 Executando Análise Estatística Detalhada...")
    
    for item in results_summary:
        llm_name = item.get("llm", "Unknown")
        filename = item.get("filename")
        if not filename:
            continue
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            results = data.get("results", [])
            analyzer = ResultsAnalyzer(results)
            stats = analyzer.analyze()
            
            # Opcional: Salvar stats de volta ou apenas imprimir
            print(f"  > Estatísticas calculadas para {llm_name}")
            
        except Exception as e:
            print(f"  ❌ Erro ao analisar {llm_name}: {e}")

def generate_report(results_summary: List[Dict[str, Any]]) -> None:
    """
    Gera relatórios textuais para todos os LLMs do benchmark.
    """
    print("\n📝 Gerando Relatórios Textuais...")
    
    full_report = []
    
    for item in results_summary:
        llm_name = item.get("llm", "Unknown")
        filename = item.get("filename")
        if not filename:
             continue
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get("results", [])
            analyzer = ResultsAnalyzer(results)
            
            # Gera nome do arquivo de relatório
            if "benchmark_results" in filename:
                report_filename = filename.replace("benchmark_results", "report_stats").replace(".json", ".txt")
            elif "repo_results" in filename:
                report_filename = filename.replace("repo_results", "report_stats").replace(".json", ".txt")
            else:
                report_filename = f"report_stats_{Path(filename).stem}.txt"
            
            report_content = analyzer.generate_report(save_path=report_filename)
            
            full_report.append(f"RELATÓRIO: {llm_name}\n{report_content}\n\n")
            print(f"✅ Relatório salvo: {report_filename}")
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório para {llm_name}: {e}")
            
    # Opcional: Salvar relatório unificado
    try:
        with open("benchmark_final_stats.txt", "w", encoding="utf-8") as f:
            f.write("".join(full_report))
        print("✅ Relatório unificado salvo: benchmark_final_stats.txt")
    except Exception as e:
        print(f"❌ Erro ao salvar relatório unificado: {e}")
