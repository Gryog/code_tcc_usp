from validator.validator import FastAPICodeValidator
import os
from client.geminiclient import GeminiClient
from config.rules import RULES_STANDARD
from config.config import settings
from tests.testes import *

def main():
    import sys

    # Determina o diretório alvo (padrão: atual)
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    print(f"🚀 Iniciando validação do projeto em: {target_dir}")
    print("---------------------------------------------------")

    # Inicializa o cliente LLM
    llm_client = GeminiClient(api_key=settings.GOOGLE_API_KEY)

    # Re-inicializa o validador para usar a classe atualizada
    validator = FastAPICodeValidator(llm_client=llm_client, rules=RULES_STANDARD)

    # Scan do projeto (Pode ser substituído por validator.validate(codigo_str) que o relatório funcionará igual)
    report = validator.validate_project(target_dir)
    #report = validator.validate(EXAMPLE_1_IDEAL)
    # Salva relatórios
    validator.save_report_json(report, "validation_report.json")
    validator.save_report_html(report, "validation_report.html")

    # Exibe relatório no console
    validator.print_report_console(report)


if __name__ == "__main__":
    main()
