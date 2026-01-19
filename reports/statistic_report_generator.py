# ============================================================================
# PARTE 3: ANÁLISE ESTATÍSTICA DOS RESULTADOS
# ============================================================================
import os
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
            "recall": self._calculate_recall(),
            "status_metricas": self._calculate_status_metrics(),
            "keyword_metricas": self._calculate_keyword_metrics(),
            "distribuicao_scores": self._score_distribution(),
        }

        return self.stats

    def _analyze_general(self) -> Dict:
        """Estatísticas gerais."""
        scores = [
            r.get("overall_score", r.get("score", 0))
            for r in self.results
            if "overall_score" in r or "score" in r
        ]

        return {
            "total_exemplos": len(self.results),
            "score_medio": round(statistics.mean(scores), 2) if scores else 0,
            "score_mediano": round(statistics.median(scores), 2) if scores else 0,
            "desvio_padrao": round(statistics.stdev(scores), 2)
            if len(scores) > 1
            else 0,
            "score_minimo": min(scores) if scores else 0,
            "score_maximo": max(scores) if scores else 0,
        }

    def _analyze_by_category(self) -> Dict:
        """Análise por categoria."""
        categories = {}

        for result in self.results:
            cat = result.get("expected_category", result.get("category"))
            if not cat and "file_path" in result:
                # Tentativa de extrair do nome do arquivo [CATEGORY] ...
                import re

                match = re.search(r"\[(\w+)\]", result["file_path"])
                if match:
                    cat = match.group(1).lower()

            if not cat:
                cat = "unknown"

            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result.get("overall_score", result.get("score", 0)))

        analysis = {}
        for cat, scores in categories.items():
            analysis[cat] = {
                "quantidade": len(scores),
                "score_medio": round(statistics.mean(scores), 2) if scores else 0,
                "score_min": min(scores) if scores else 0,
                "score_max": max(scores) if scores else 0,
            }

        return analysis

    def _analyze_performance(self) -> Dict:
        """Análise de performance (tempo de resposta)."""
        times = [
            r.get("response_time", r.get("_metadata", {}).get("response_time", 0))
            for r in self.results
            if "response_time" in r or "_metadata" in r
        ]
        times = [t for t in times if t > 0]  # Remove zeros

        return {
            "tempo_medio": round(statistics.mean(times), 2) if times else 0,
            "tempo_mediano": round(statistics.median(times), 2) if times else 0,
            "tempo_minimo": round(min(times), 2) if times else 0,
            "tempo_maximo": round(max(times), 2) if times else 0,
            "desvio_padrao": round(statistics.stdev(times), 2) if len(times) > 1 else 0,
        }

    def _analyze_violations(self) -> Dict:
        """Análise de violações encontradas."""
        total_violations = sum(len(r.get("violations", [])) for r in self.results)

        status_count = {}
        for result in self.results:
            status = result.get("overall_status", result.get("status", "unknown"))
            status_count[status] = status_count.get(status, 0) + 1

        return {
            "total_violacoes": total_violations,
            "media_por_exemplo": round(total_violations / len(self.results), 2)
            if self.results
            else 0,
            "por_status": status_count,
        }

    def _calculate_accuracy(self) -> Dict:
        """Calcula acurácia comparando score esperado vs obtido."""
        correct = 0
        total = 0

        for result in self.results:
            if "expected_score_min" in result and "expected_score_max" in result:
                score = result.get("overall_score", result.get("score", 0))
                min_expected = result["expected_score_min"]
                max_expected = result["expected_score_max"]

                if min_expected <= score <= max_expected:
                    correct += 1
                total += 1

        accuracy = (correct / total * 100) if total > 0 else 0

        return {
            "exemplos_com_expectativa": total,
            "predicoes_corretas": correct,
            "predicoes_incorretas": total - correct,
            "acuracia_percentual": round(accuracy, 2),
            "taxa_erro": round(100 - accuracy, 2),
        }

    def _calculate_recall(self) -> Dict:
        """
        Calcula a métrica de Recall baseada em palavras-chave esperadas.
        Verifica se o LLM mencionou os termos chave na descrição das violações.
        """
        total_with_keywords = 0
        detected_count = 0

        for result in self.results:
            expected_keywords = result.get("expected_keywords")
            
            # Se não tiver keywords, tenta buscar no metadata ou raw (dependendo de onde o benchmark injetar)
            if not expected_keywords:
                expected_keywords = result.get("metadata", {}).get("expected_keywords")

            if not expected_keywords:
                continue

            total_with_keywords += 1
            
            # Coleta textos gerados pelo LLM
            llm_texts = []
            # Descrições das violações
            for v in result.get("violations", []):
                llm_texts.append(v.get("description", "").lower())
                llm_texts.append(v.get("suggestion", "").lower())
            
            # Resumo geral
            llm_texts.append(result.get("summary", "").lower())
            
            full_text = " ".join(llm_texts)
            
            # Verifica se PELO MENOS UMA keyword foi encontrada
            # (Critério flexível: se encontrou um dos problemas chave, já conta ponto)
            found = any(k.lower() in full_text for k in expected_keywords)
            
            if found:
                detected_count += 1

        recall_rate = (detected_count / total_with_keywords * 100) if total_with_keywords > 0 else 0

        return {
            "total_analisados": total_with_keywords,
            "detectados": detected_count,
            "nao_detectados": total_with_keywords - detected_count,
            "recall_rate": round(recall_rate, 2)
        }

    def _calculate_status_metrics(self) -> Dict:
        """Calcula métricas de classificação para o status (pass/warning/fail)."""
        labels = ("pass", "warning", "fail")
        confusion = {label: {l: 0 for l in labels} for label in labels}
        total = 0

        for result in self.results:
            expected = result.get("expected_status")
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
            per_label[label] = {
                "precision": round(precision * 100, 2),
                "recall": round(recall * 100, 2),
                "f1": round(f1 * 100, 2),
                "suporte": tp + fn,
            }
            correct += tp

        accuracy = (correct / total * 100) if total > 0 else 0
        labels_with_support = [label for label in labels if per_label[label]["suporte"] > 0]
        macro_precision = (
            sum(per_label[label]["precision"] for label in labels_with_support)
            / len(labels_with_support)
            if labels_with_support
            else 0
        )
        macro_recall = (
            sum(per_label[label]["recall"] for label in labels_with_support)
            / len(labels_with_support)
            if labels_with_support
            else 0
        )
        macro_f1 = (
            sum(per_label[label]["f1"] for label in labels_with_support)
            / len(labels_with_support)
            if labels_with_support
            else 0
        )

        weighted_precision = 0
        weighted_recall = 0
        weighted_f1 = 0
        for label in labels:
            support = per_label[label]["suporte"]
            if total > 0 and support > 0:
                weight = support / total
                weighted_precision += per_label[label]["precision"] * weight
                weighted_recall += per_label[label]["recall"] * weight
                weighted_f1 += per_label[label]["f1"] * weight

        return {
            "total_avaliados": total,
            "accuracy": round(accuracy, 2),
            "macro_avg": {
                "precision": round(macro_precision, 2),
                "recall": round(macro_recall, 2),
                "f1": round(macro_f1, 2),
            },
            "weighted_avg": {
                "precision": round(weighted_precision, 2),
                "recall": round(weighted_recall, 2),
                "f1": round(weighted_f1, 2),
            },
            "matriz_confusao": confusion,
            "por_status": per_label,
        }

    def _calculate_keyword_metrics(self) -> Dict:
        """Calcula precisão/recall/F1 para keywords esperadas nos testes sintéticos."""
        keyword_pool = set()
        total_expected_keywords = 0
        for result in self.results:
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
        total_results = len(self.results)

        for result in self.results:
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

            tp = len(expected_set & predicted_set)
            fp = len(predicted_set - expected_set)
            fn = len(expected_set - predicted_set)

            total_tp += tp
            total_fp += fp
            total_fn += fn

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        return {
            "total_exemplos": total_examples,
            "cobertura_percentual": round((total_examples / total_results) * 100, 2)
            if total_results > 0
            else 0,
            "media_keywords_por_exemplo": round(
                total_expected_keywords / total_examples, 2
            )
            if total_examples > 0
            else 0,
            "total_keywords_unicas": len(keyword_pool),
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1": round(f1 * 100, 2),
        }

    def _score_distribution(self) -> Dict:
        """Distribuição de scores por faixas."""
        scores = [r.get("overall_score", r.get("score", 0)) for r in self.results]

        distribution = {
            "0-20": sum(1 for s in scores if 0 <= s < 20),
            "20-40": sum(1 for s in scores if 20 <= s < 40),
            "40-60": sum(1 for s in scores if 40 <= s < 60),
            "60-80": sum(1 for s in scores if 60 <= s < 80),
            "80-100": sum(1 for s in scores if 80 <= s <= 100),
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
        geral = self.stats["geral"]
        report.append(f"  Total de exemplos: {geral['total_exemplos']}")
        report.append(f"  Score médio: {geral['score_medio']}/100")
        report.append(f"  Score mediano: {geral['score_mediano']}/100")
        report.append(f"  Desvio padrão: {geral['desvio_padrao']}")
        report.append(f"  Range: {geral['score_minimo']} - {geral['score_maximo']}")
        report.append("")

        # Por categoria
        report.append("📂 POR CATEGORIA:")
        for cat, data in self.stats["por_categoria"].items():
            report.append(f"  {cat.upper()}:")
            report.append(f"    Quantidade: {data['quantidade']}")
            report.append(f"    Score médio: {data['score_medio']}/100")
            report.append(f"    Range: {data['score_min']} - {data['score_max']}")
        report.append("")

        # Performance
        report.append("⏱️  PERFORMANCE:")
        perf = self.stats["performance"]
        report.append(f"  Tempo médio: {perf['tempo_medio']}s")
        report.append(f"  Tempo mediano: {perf['tempo_mediano']}s")
        report.append(f"  Range: {perf['tempo_minimo']}s - {perf['tempo_maximo']}s")
        report.append("")

        # Violações
        report.append("⚠️  VIOLAÇÕES:")
        viol = self.stats["violacoes"]
        report.append(f"  Total: {viol['total_violacoes']}")
        report.append(f"  Média por exemplo: {viol['media_por_exemplo']}")
        report.append("  Por status:")
        for status, count in viol["por_status"].items():
            report.append(f"    {status}: {count}")
        report.append("")

        # Acurácia
        report.append("🎯 ACURÁCIA:")
        acc = self.stats["acuracia"]
        report.append(f"  Exemplos com expectativa: {acc['exemplos_com_expectativa']}")
        report.append(f"  Predições corretas: {acc['predicoes_corretas']}")
        report.append(f"  Predições incorretas: {acc['predicoes_incorretas']}")
        report.append(f"  Acurácia percentual: {acc['acuracia_percentual']}%")
        report.append(f"  Taxa de erro: {acc['taxa_erro']}%")
        report.append("")

        # Recall
        report.append("🧠 RECALL (Detecção de palavras-chave):")
        rec = self.stats.get("recall", {})
        report.append(f"  Exemplos com keywords: {rec.get('total_analisados', 0)}")
        report.append(f"  Detectados: {rec.get('detectados', 0)}")
        report.append(f"  Recall Rate: {rec.get('recall_rate', 0)}%")
        report.append("")

        # Métricas de status
        report.append("✅ CLASSIFICAÇÃO POR STATUS (pass/warning/fail):")
        status_metrics = self.stats.get("status_metricas", {})
        total_status_examples = status_metrics.get("total_avaliados", 0)
        report.append(f"  Total avaliados: {total_status_examples}")
        report.append(f"  Accuracy: {status_metrics.get('accuracy', 0)}%")
        macro_avg = status_metrics.get("macro_avg", {})
        weighted_avg = status_metrics.get("weighted_avg", {})
        if total_status_examples > 0:
            report.append(
                f"  Macro Avg: Precision {macro_avg.get('precision', 0)}% | Recall {macro_avg.get('recall', 0)}% | F1 {macro_avg.get('f1', 0)}%"
            )
            report.append(
                f"  Weighted Avg: Precision {weighted_avg.get('precision', 0)}% | Recall {weighted_avg.get('recall', 0)}% | F1 {weighted_avg.get('f1', 0)}%"
            )
        else:
            report.append("  Macro Avg: Precision N/A | Recall N/A | F1 N/A")
            report.append("  Weighted Avg: Precision N/A | Recall N/A | F1 N/A")
        per_status = status_metrics.get("por_status", {})
        for status, data in per_status.items():
            report.append(
                f"  {status.upper()}: Precision {data['precision']}% | Recall {data['recall']}% | F1 {data['f1']}% | Suporte {data['suporte']}"
            )
        confusion = status_metrics.get("matriz_confusao", {})
        if confusion:
            report.append("  Matriz de Confusão (esperado -> predito):")
            for expected, predicted in confusion.items():
                row = ", ".join(f"{label}:{count}" for label, count in predicted.items())
                report.append(f"    {expected.upper()}: {row}")
        report.append("")

        # Métricas de keywords
        report.append("🔎 PRECISÃO/RECALL/F1 (Keywords):")
        keyword_metrics = self.stats.get("keyword_metricas", {})
        total_keyword_examples = keyword_metrics.get("total_exemplos", 0)
        report.append(f"  Total exemplos: {total_keyword_examples}")
        report.append(
            f"  Cobertura: {keyword_metrics.get('cobertura_percentual', 0)}% | Keywords únicas: {keyword_metrics.get('total_keywords_unicas', 0)} | Média keywords/exemplo: {keyword_metrics.get('media_keywords_por_exemplo', 0)}"
        )
        report.append(
            f"  TP: {keyword_metrics.get('tp', 0)} | FP: {keyword_metrics.get('fp', 0)} | FN: {keyword_metrics.get('fn', 0)}"
        )
        if total_keyword_examples > 0:
            report.append(
                f"  Precision: {keyword_metrics.get('precision', 0)}% | Recall: {keyword_metrics.get('recall', 0)}% | F1: {keyword_metrics.get('f1', 0)}%"
            )
        else:
            report.append("  Precision: N/A | Recall: N/A | F1: N/A")
        report.append("")

        # Distribuição de scores
        report.append("📊 DISTRIBUIÇÃO DE SCORES:")
        dist = self.stats["distribuicao_scores"]
        for faixa, count in dist.items():
            report.append(f"  {faixa}: {count}")
        report.append("")

        # Salvar relatório
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("\n".join(report))

        return "\n".join(report)


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
            with open(filename, "r", encoding="utf-8") as f:
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
    repo_report = []

    for item in results_summary:
        llm_name = item.get("llm", "Unknown")
        filename = item.get("filename")
        if not filename:
            continue

        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            results = data.get("results", [])
            analyzer = ResultsAnalyzer(results)

            # Gera nome do arquivo de relatório
            # Forçar salvamento na pasta 'results/'
            base_name = os.path.basename(filename)
            
            if "synthetic_results" in base_name:
                report_filename = os.path.join(
                    "results/sinteticos", 
                    base_name.replace("synthetic_results", "synthetic_report_stats").replace(".json", ".txt")
                )
            elif "repo_results" in base_name:
                report_filename = os.path.join(
                    "results/repositorios",
                    base_name.replace("repo_results", "repo_report_stats").replace(".json", ".txt")
                )
            else:
                report_filename = os.path.join(
                    "results",
                    f"report_stats_{Path(base_name).stem}.txt"
                )

            report_content = analyzer.generate_report(save_path=report_filename)

            report_block = f"RELATÓRIO: {llm_name}\n{report_content}\n\n"
            full_report.append(report_block)
            if filename.startswith("results/repositorios") or "repo_results" in filename:
                repo_report.append(report_block)
            print(f"✅ Relatório salvo: {report_filename}")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório para {llm_name}: {e}")

    # Opcional: Salvar relatório unificado
    try:
        with open("results/synthetic_final_stats.txt", "w", encoding="utf-8") as f:
            f.write("".join(full_report))
        print("✅ Relatório unificado salvo: results/synthetic_final_stats.txt")
    except Exception as e:
        print(f"❌ Erro ao salvar relatório unificado: {e}")

    if repo_report:
        try:
            with open("results/repo_final_stats.txt", "w", encoding="utf-8") as f:
                f.write("".join(repo_report))
            print("✅ Relatório unificado salvo: results/repo_final_stats.txt")
        except Exception as e:
            print(f"❌ Erro ao salvar relatório de repositórios: {e}")

