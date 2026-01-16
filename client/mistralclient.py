import json
from typing import Dict, Any
from mistralai import Mistral
from .llmclient import LLMClient


class MistralClient(LLMClient):
    def __init__(self, api_key: str, model_name: str = "mistral-small-latest"):
        self.client = Mistral(api_key=api_key)
        self.model_name = model_name

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        try:
            chat_response = self.client.chat.complete(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                response_format={
                    "type": "json_object",
                },
                temperature=0.2,
            )

            response_content = chat_response.choices[0].message.content
            # Mistral's JSON mode ensures valid JSON, but we still parse it
            return json.loads(response_content)
        except Exception as e:
            raise RuntimeError(f"Falha na geração do Mistral: {str(e)}")
