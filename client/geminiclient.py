import json
from google import genai
from google.genai import types
from typing import Dict, Any
from .llmclient import LLMClient


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            raise RuntimeError(f"Falha na geração do Gemini: {str(e)}")
