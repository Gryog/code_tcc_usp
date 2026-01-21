import json
from google import genai
from google.genai import types
from typing import Dict, Any
from .llmclient import LLMClient


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_json(self, prompt: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    top_p=0.9,
                ),
            )
            usage_metadata = {}
            if response.usage_metadata:
                usage_metadata = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count,
                }

            return json.loads(response.text), usage_metadata
        except Exception as e:
            raise RuntimeError(f"Falha na geração do Gemini: {str(e)}")
