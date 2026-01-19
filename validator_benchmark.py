import json
import glob
from dataclasses import dataclass
from typing import List, Set
from validator.validator import FastAPICodeValidator
from client.geminiclient import GeminiClient
from config.rules import RULES_STANDARD
from config.config import settings

@dataclass
class EvaluationMetrics:
    total_files: int = 0
    true_positives: int = 0  # Erro existia e foi achado
    false_positives: int = 0 # Erro não existia e foi achado (Alucinação)
    false_negatives: int = 0 # Erro existia e não foi achado
    
    @property
    def precision(self) -> float:
        if (self.true_positives + self.false_positives) == 0: return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        if (self.true_positives + self.false_negatives) == 0: return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        if (p + r) == 0: return 0.0
        return 2 * (p * r) / (p + r)

class ValidatorBenchmark:
    def __init__(self, validator: FastAPICodeValidator, manifest_path: str):
        self.validator = validator
        with open(manifest_path, 'r', encoding='utf-8') as f:
            self.manifest = json.load(f)

    def run(self):
        metrics = EvaluationMetrics()
        metrics.total_files = len(self.manifest)
        
        print(f"🚀 Iniciando Benchmark em {metrics.total_files} arquivos...")

        for case in self.manifest:
            # Check if file exists to perform the test
            if not glob.glob(case['file']) and not case['file'].startswith('/'): # straightforward check
                 # maybe it is absolute path?
                 pass

            try:
                with open(case['file'], 'r', encoding='utf-8') as f:
                    code_content = f.read()
            except FileNotFoundError:
                 print(f"❌ Arquivo não encontrado: {case['file']}")
                 continue

            # Executa a validação real
            result = self.validator.validate(code_content)
            
            # Extrai as categorias de erro detectadas pelo LLM
            detected_categories = {v['rule_category'] for v in result.get('violations', [])}
            expected_categories = set(case['expected_violations'])
            
            # Cálculo de Sets
            # TP: Estava no esperado E foi detectado
            tp_set = expected_categories.intersection(detected_categories)
            # FP: Foi detectado MAS NÃO estava no esperado (Alucinação)
            fp_set = detected_categories.difference(expected_categories)
            # FN: Estava no esperado MAS NÃO foi detectado
            fn_set = expected_categories.difference(detected_categories)

            metrics.true_positives += len(tp_set)
            metrics.false_positives += len(fp_set)
            metrics.false_negatives += len(fn_set)

            # Log detalhado de falhas
            if fp_set or fn_set:
                print(f"⚠️  Discrepância em {case['file']}:")
                if fp_set: print(f"   - Alucinações (FP): {fp_set}")
                if fn_set: print(f"   - Perdeu (FN): {fn_set}")

        self._print_report(metrics)

    def _print_report(self, m: EvaluationMetrics):
        print("\n" + "="*40)
        print("📊 RESULTADO DO BENCHMARK")
        print("="*40)
        print(f"Precision: {m.precision:.2%} (Confiabilidade dos alertas)")
        print(f"Recall:    {m.recall:.2%} (Capacidade de varredura)")
        print(f"F1-Score:  {m.f1_score:.2%} (Média Geral)")
        print("-" * 40)
        print(f"TP: {m.true_positives} | FP: {m.false_positives} | FN: {m.false_negatives}")

if __name__ == "__main__":
    # Exemplo de uso
    try:
        client = GeminiClient(api_key=settings.GOOGLE_API_KEY)
        validator = FastAPICodeValidator(client, RULES_STANDARD)
        # Ajuste o caminho do manifesto conforme necessário
        manifest_path = "benchmark/manifest.json" 
        
        # Só executa se o manifesto existir
        import os
        if os.path.exists(manifest_path):
            bench = ValidatorBenchmark(validator, manifest_path)
            bench.run()
        else:
            print(f"Manifesto não encontrado em {manifest_path}. Crie o arquivo para executar o benchmark.")
    except Exception as e:
        print(f"Erro ao executar benchmark: {e}")
