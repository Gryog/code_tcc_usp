import abc
from typing import Dict, Any


class LLMClient(abc.ABC):
    """Interface abstrata para qualquer provedor de LLM (Gemini, OpenAI, Claude)."""

    @abc.abstractmethod
    def generate_json(self, prompt: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Deve retornar uma tupla:
        1. Um dicionário Python derivado de um JSON válido (conteúdo).
        2. Um dicionário com metadados de uso (tokens de entrada, saída, total).
        """
        pass
