import json
from typing import Dict, Any
from openai import OpenAI
from .llmclient import LLMClient


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant designed to output JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty content")

            return json.loads(content)
        except Exception as e:
            raise RuntimeError(f"Falha na geração da OpenAI: {str(e)}")
