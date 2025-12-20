from ..LLMInterface import LLMInterface
from ..LLMEnums import OLLAMARolesEnums
from ..utils import ModelUtils

import requests
import logging


class Ollama(LLMInterface, ModelUtils):

    def __init__(self,
                 api_key: str, 
                 base_url: str = "http://localhost:11434",
                 default_input_max_characters: int = 1024,
                 default_generation_output_max_tokens: int = 1024,
                 default_generation_temperature: float = 0.1):
        
        ModelUtils.__init__(self)

        self.base_url = base_url.rstrip("/")
        self.enums = OLLAMARolesEnums
        
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_output_max_tokens = default_generation_output_max_tokens
        self.default_generation_temperature = default_generation_temperature
        
        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.logger = logging.getLogger(__name__)


    def generate_text(self,
                      prompt: str,
                      chat_history: list = None,
                      max_output_tokens: int = None,
                      temperature: float = None):
        
        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set for Ollama.")
            return None

        history = chat_history or []


        history = history + [self.construct_prompt(prompt, role=OLLAMARolesEnums.USER.value)]

        payload = {
            "model": self.generation_model_id,
            "messages": history,
            "options": {
                "temperature": temperature or 0.1, 
                "num_predict": max_output_tokens or self.default_generation_output_max_tokens
                },
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Ollama generation request failed: {e}")
            return None
        
        result = response.json()
        return result.get("message", {}).get("content", "").strip()


    def embed_text(self, text: str, document_type: str = None):
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set for Ollama.")
            return None
        
        payload = {
            "model": self.embedding_model_id,
            "input": text
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json=payload
            )

            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Ollama embedding request failed: {e}")
            return None

        result = response.json()
        return result.get("embeddings", [None])[0] if result.get("embeddings") else None


    def construct_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}

    def process_text(self, text: str):
        text = text.strip()
        if len(text) > self.default_input_max_characters:
            self.logger.warning("Input text too long. Truncating for Ollama.")
        return text[:self.default_input_max_characters]
