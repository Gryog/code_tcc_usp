import abc
from typing import Dict, Any


class LLMClient(abc.ABC):
    """Interface abstrata para qualquer provedor de LLM (Gemini, OpenAI, Claude)."""

    @abc.abstractmethod
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """Deve retornar um dicionário Python derivado de um JSON válido."""
        pass
